#!/usr/bin/env python3
"""Strict public preferences and skill-package selection; no credentials or execution."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import json
from pathlib import Path
import sys

for _parent in Path(__file__).resolve().parents:
    if (_parent / "scripts/palarran_paths.py").is_file():
        sys.path.insert(0, str(_parent / "scripts"))
        break
from palarran_paths import repository_root, source_path

ROOT = repository_root(__file__)

LOCALES = ("en", "ru", "sr-Latn")
FIELDS = ("skills", "code", "docs")


def read(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Configuration symlinks are not supported")
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > 65536:
        raise ValueError("Invalid configuration file")
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate configuration key")
            value[key] = item
        return value
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    validate(value)
    return value


def validate(value):
    if not isinstance(value, dict) or value.get("version", 1) != 1:
        raise ValueError("Unsupported configuration version")
    if "packages" in value:
        packages = value["packages"]
        if not isinstance(packages, list) or not packages or any(not isinstance(p, str) for p in packages) or len(set(packages)) != len(packages):
            raise ValueError("Select distinct packages")
    languages = value.get("languages", {})
    if not isinstance(languages, dict) or any(k not in FIELDS or v not in LOCALES for k, v in languages.items()):
        raise ValueError("Unsupported language preference")
    return value


def resolve(target, packages=None, languages=None, home=None):
    global_value = read(Path(home or Path.home()) / ".palarran/config.json")
    local = read(Path(target) / ".palarran/config.json")
    merged = dict(global_value, **local)
    merged["version"] = 1
    merged["languages"] = dict(global_value.get("languages", {}), **local.get("languages", {}), **(languages or {}))
    if packages is not None:
        merged["packages"] = list(packages)
    validate(merged)
    return merged


def selected(bundle, packages, *, legacy_receipt=False, recorded_packages=None):
    """Filter discovery skills without widening recorded legacy selections."""
    if packages is None and recorded_packages is None:
        return bundle
    if packages is None:
        packages = ["all"]
    if not isinstance(packages, list) or not packages or len(set(packages)) != len(packages):
        raise ValueError("Select distinct packages")
    from package_plugin import LEGACY_PACKAGES, PUBLIC_GROUPS, registry_type
    if "all" in packages and packages != ["all"]:
        raise ValueError("all cannot be mixed with individual packages")
    if "packages/catalog.json" in bundle:
        catalog = registry_type()(json.loads(bundle["packages/catalog.json"]))
        if recorded_packages is not None:
            if (not isinstance(recorded_packages, list) or not recorded_packages
                    or any(not isinstance(item, str) for item in recorded_packages)
                    or len(set(recorded_packages)) != len(recorded_packages)):
                raise ValueError("Invalid recorded package selection")
            resolved = catalog.resolve(recorded_packages)
            if set(resolved["packages"]) != set(recorded_packages):
                raise ValueError("Package dependency change requires explicit scope review")
            records = resolved["skills"]
            if any(item["legacy_path"] not in bundle for item in records):
                raise ValueError("Recorded package skills are missing from the public bundle")
            names = {item["name"] for item in records}
        elif legacy_receipt and packages != ["all"]:
            # Existing receipts retain their exact old skill scope. Mapping an old
            # backend selection to all of Code would silently add frontend skills.
            allowed = {key.removeprefix("palarran-"): set(value["skills"])
                       for key, value in LEGACY_PACKAGES.items()}
            normalized = [p.removeprefix("palarran-") for p in packages]
            if any(p not in allowed for p in normalized): raise ValueError("Unknown recorded package")
            names = set().union(*(allowed[p] for p in normalized))
            names.add("palarran-setup")
        else:
            choices = list(PUBLIC_GROUPS) if packages == ["all"] else packages
            records = catalog.resolve(choices)["skills"]
            if any(item["legacy_path"] not in bundle for item in records):
                raise ValueError("Selected package skills are missing from the public bundle")
            names = {item["name"] for item in records}
    else:
        # Only pre-catalog fixtures/releases retain the former package interface.
        catalog = json.loads(bundle["skills/catalog.json"])
        rows = catalog["skills"] if isinstance(catalog, dict) else catalog
        allowed = {key.removeprefix("palarran-"): set(value["skills"])
                   for key, value in LEGACY_PACKAGES.items()}
        normalized = [p.removeprefix("palarran-") for p in packages]
        if packages == ["all"]: names = {row["skill"] for row in rows}
        elif any(p not in allowed for p in normalized): raise ValueError("Unknown skill package")
        else: names = set().union(*(allowed[p] for p in normalized))
        names.add("palarran-setup")
    return {name: raw for name, raw in bundle.items()
            if not name.startswith("skills/") or len(Path(name).parts) < 3
            or Path(name).parts[1] in names}


def recorded_selection(receipt, prior_catalog=None):
    """Recover an immutable package scope; caller verifies prior bytes' ownership hash."""
    from package_plugin import PUBLIC_GROUPS, registry_type
    recorded = receipt.get("resolved_packages")
    if recorded is not None:
        if (not isinstance(recorded, list) or not recorded
                or any(type(item) is not str or item not in PUBLIC_GROUPS for item in recorded)
                or len(set(recorded)) != len(recorded)):
            raise ValueError("Invalid recorded package selection")
        return list(recorded)
    preferences = receipt.get("preferences")
    choices = preferences.get("packages") if isinstance(preferences, dict) else None
    if receipt.get("package_selection_version", 1) == 1 and choices not in (None, ["all"]):
        return None  # Preserve the explicit pre-registry skill selection adapter.
    if prior_catalog is None:
        if receipt.get("package_selection_version", 1) == 1 and choices is None:
            return None  # Pre-catalog fixture releases retain their legacy behavior.
        raise ValueError("Original package selection requires a verified prior catalog")
    if len(prior_catalog) > 1024 * 1024:
        raise ValueError("Prior package catalog exceeds its byte bound")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError("Duplicate prior catalog field")
            result[key] = value
        return result
    value = json.loads(prior_catalog, object_pairs_hook=unique)
    if type(value) is not dict or type(value.get("packages")) is not list:
        raise ValueError("Invalid prior package catalog")
    ids = [item.get("id") if isinstance(item, dict) else None for item in value["packages"]]
    if any(type(item) is not str for item in ids):
        raise ValueError("Invalid prior package identifiers")
    # Explicit compatibility for the immediately preceding ten-package catalog.
    # The synthetic row validates its old neighbors but never joins the old scope.
    if len(ids) == 10 and set(ids) == set(PUBLIC_GROUPS) - {"security"}:
        for package in value['packages']:
            dependencies=package.get('requires')
            if (not isinstance(dependencies,list)
                    or any(type(item) is not str or item not in ids for item in dependencies)):
                raise ValueError("Prior catalog references an undeclared dependency")
        value["packages"].append({"id": "security", "title": "Security",
            "description": "Compatibility validation placeholder, never selected.", "requires": ["core"],
            "capabilities": [{"id": "compatibility", "status": "planned", "description": "No execution."}], "skills": []})
    catalog = registry_type()(value)
    return catalog.resolve(ids if choices in (None, ["all"]) else choices)["packages"]
