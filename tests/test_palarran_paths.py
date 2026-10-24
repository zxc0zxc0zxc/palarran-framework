"""Offline fixtures for explicit, bounded package-source path resolution."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.palarran_paths import MAX_MANIFEST_BYTES, source_path, source_resolver


class SourcePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "library"
        self.root.mkdir()

    def file(self, relative, content="inert source"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def manifest(self, moves):
        return self.file("packages/layout.json", json.dumps({"version": 1, "moves": moves}))

    def test_legacy_fixture_without_manifest_has_no_search_or_writes(self):
        legacy = self.file("docs/plan.md")
        self.file("elsewhere/missing.md")
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        self.assertEqual(source_path(self.root, "docs/plan.md", required=True), legacy)
        self.assertEqual(source_path(self.root, "missing.md"), self.root / "missing.md")
        self.assertFalse((self.root / "packages").exists())
        self.assertEqual(before, sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*")))

    def test_longest_directory_and_exact_file_prefixes(self):
        self.manifest({"docs": "packages/core/docs", "docs/ml": "packages/ml/docs",
                       "docs/ml/plan.md": "packages/ml/spec.md"})
        self.assertEqual(source_path(self.root, "docs/other.md"), self.root / "packages/core/docs/other.md")
        self.assertEqual(source_path(self.root, "docs/ml/data/card.md"), self.root / "packages/ml/docs/data/card.md")
        self.assertEqual(source_path(self.root, "docs/ml/plan.md"), self.root / "packages/ml/spec.md")
        self.assertEqual(source_path(self.root, "docs/ml"), self.root / "packages/ml/docs")

    def test_prefixes_match_only_at_segment_boundaries_and_rebase_once(self):
        self.manifest({"docs/ml": "packages/ml/docs", "packages/ml": "should-not-recurse"})
        self.assertEqual(source_path(self.root, "docs/ml-extra/plan.md"), self.root / "docs/ml-extra/plan.md")
        self.assertEqual(source_path(self.root, "docs/ml/plan.md"), self.root / "packages/ml/docs/plan.md")

    def test_mapped_missing_never_falls_back_to_existing_legacy_source(self):
        legacy = self.file("docs/plan.md")
        self.manifest({"docs": "packages/core/docs"})
        self.assertTrue(legacy.exists())
        self.assertEqual(source_path(self.root, "docs/plan.md"), self.root / "packages/core/docs/plan.md")
        with self.assertRaises(FileNotFoundError):
            source_path(self.root, "docs/plan.md", required=True)

    def test_unmapped_paths_and_empty_manifest_keep_strict_root_relative_lookup(self):
        legacy = self.file("docs/caf\u00e9.md")
        self.manifest({})
        self.assertEqual(source_path(self.root, "docs/caf\u00e9.md", required=True), legacy)
        self.manifest({"skills": "packages/core/skills"})
        self.assertEqual(source_path(self.root, "docs/caf\u00e9.md", required=True), legacy)

    def test_required_accepts_regular_files_and_directories_not_missing_paths(self):
        self.manifest({"docs": "packages/core/docs"})
        source = self.file("packages/core/docs/plan.md")
        self.assertEqual(source_path(self.root, "docs", required=True), source.parent)
        self.assertEqual(source_path(self.root, "docs/plan.md", required=True), source)
        with self.assertRaises(FileNotFoundError):
            source_path(self.root, "docs/missing.md", required=True)
        with self.assertRaises(ValueError):
            source_path(self.root, "docs", required=1)

    def test_invalid_relative_references_rejected_before_path_normalization(self):
        values = ("", "/absolute", "../secret", "a/../secret", "./docs", "a/./b",
                  "a//b", "a/", "a\\b", "https://example.invalid/a", "s3:bucket",
                  "C:drive", "a\x00b", "a\nb", "a\x7fb", "\ud800", Path("docs"), None)
        for value in values:
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                source_path(self.root, value)

    def test_malformed_duplicate_and_unknown_manifest_schema_fail_closed(self):
        invalid = ("not JSON", "[]", "null", '{}',
                   '{"version":1,"moves":{},"extra":0}',
                   '{"version":true,"moves":{}}', '{"version":2,"moves":{}}',
                   '{"version":1,"moves":[]}',
                   '{"version":1,"version":1,"moves":{}}',
                   '{"version":1,"moves":{"docs":"one","docs":"two"}}',
                   '{"version":NaN,"moves":{}}', '{"version":Infinity,"moves":{}}',
                   '{"version":1e999,"moves":{}}',
                   '{"version":1,"moves":{"docs":{"path":"bad","path":"also-bad"}}}')
        for raw in invalid:
            with self.subTest(raw=raw):
                self.file("packages/layout.json", raw)
                with self.assertRaises(ValueError):
                    source_path(self.root, "docs/plan.md")

    def test_all_mapping_keys_and_targets_are_validated_even_when_unmatched(self):
        for bad in ("", "../escape", "/absolute", "a\\b", "a//b", "./a", "a/..", "https:bad"):
            for moves in ({bad: "canonical"}, {"unrelated": bad}):
                with self.subTest(moves=moves):
                    self.manifest(moves)
                    with self.assertRaises(ValueError):
                        source_path(self.root, "docs/plan.md")
        self.manifest({"unrelated": 3})
        with self.assertRaises(ValueError):
            source_path(self.root, "docs/plan.md")

    def test_manifest_byte_bound_and_utf8(self):
        raw = '{"version":1,"moves":{}}'
        self.file("packages/layout.json", raw + " " * (MAX_MANIFEST_BYTES - len(raw)))
        self.assertEqual(source_path(self.root, "docs"), self.root / "docs")
        self.file("packages/layout.json", raw + " " * (MAX_MANIFEST_BYTES + 1 - len(raw)))
        with self.assertRaises(ValueError):
            source_path(self.root, "docs")
        (self.root / "packages/layout.json").write_bytes(b"\xff")
        with self.assertRaises(ValueError):
            source_path(self.root, "docs")

    def test_symlinked_roots_and_manifest_components_are_rejected(self):
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            source_path(alias, "docs")
        outside = self.root.parent / "outside"
        outside.mkdir()
        (self.root / "packages").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            source_path(self.root, "docs")
        (self.root / "packages").unlink()
        self.file("manifest.json", '{"version":1,"moves":{}}')
        (self.root / "packages").mkdir()
        (self.root / "packages/layout.json").symlink_to(self.root / "manifest.json")
        with self.assertRaises(ValueError):
            source_path(self.root, "docs")

    def test_mapped_unmapped_and_dangling_symlinks_never_escape(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        self.manifest({"docs": "packages/core/docs"})
        (self.root / "packages/core").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            source_path(self.root, "docs/plan.md")
        (self.root / "packages/core").unlink()
        (self.root / "unmapped").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            source_path(self.root, "unmapped/plan.md")
        self.manifest({"unrelated": "dangling"})
        (self.root / "dangling").symlink_to(outside / "missing")
        with self.assertRaises(ValueError):
            source_path(self.root, "docs/plan.md")

    def test_internal_symlinks_and_non_directory_ancestors_are_not_accepted(self):
        self.file("actual/plan.md")
        (self.root / "alias").symlink_to(self.root / "actual", target_is_directory=True)
        with self.assertRaises(ValueError):
            source_path(self.root, "alias/plan.md")
        self.file("not-directory")
        with self.assertRaises(ValueError):
            source_path(self.root, "not-directory/plan.md")

    def test_special_files_and_nonregular_manifests_are_rejected_without_reading(self):
        os.mkfifo(self.root / "pipe")
        with self.assertRaises(ValueError):
            source_path(self.root, "pipe")
        (self.root / "packages/layout.json").mkdir(parents=True)
        with self.assertRaises(ValueError):
            source_path(self.root, "docs")

    def test_resolution_reads_only_the_manifest_not_the_selected_source(self):
        self.manifest({"legacy.py": "packages/core/source.py"})
        target = self.file("packages/core/source.py", "raise RuntimeError('must not execute')")
        with patch("scripts.palarran_paths.os.open", wraps=os.open) as opened:
            self.assertEqual(source_path(self.root, "legacy.py", required=True), target)
        self.assertEqual([Path(call.args[0]) for call in opened.call_args_list], [self.root / "packages/layout.json"])


    def test_operation_resolver_reads_one_map_and_next_operation_refreshes(self):
        self.manifest({"legacy.py": "packages/core/first.py"})
        first = self.file("packages/core/first.py")
        second = self.file("packages/core/second.py")
        with patch("scripts.palarran_paths.os.open", wraps=os.open) as opened:
            resolve = source_resolver(self.root)
            for _ in range(20):
                self.assertEqual(resolve("legacy.py", required=True), first)
            self.assertEqual(len(opened.call_args_list), 1)
        self.manifest({"legacy.py": "packages/core/second.py"})
        self.assertEqual(source_resolver(self.root)("legacy.py", required=True), second)

    def test_operation_resolver_rechecks_target_symlinks_after_snapshot(self):
        self.manifest({"legacy.py": "packages/core/source.py"})
        target = self.file("packages/core/source.py")
        resolve = source_resolver(self.root)
        self.assertEqual(resolve("legacy.py"), target)
        target.unlink()
        target.symlink_to(self.file("outside.py"))
        with self.assertRaises(ValueError):
            resolve("legacy.py", required=True)


if __name__ == "__main__":
    unittest.main()
