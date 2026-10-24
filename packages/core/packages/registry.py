"""Pure ten-package metadata validation with explicit optional path checks."""

import copy
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

MAX_CATALOG_BYTES = 1024 * 1024
PUBLIC_TITLES = {
    "core": "Core", "memory": "Memory", "product": "Product", "design": "Design",
    "code": "Code", "machine-learning": "Machine Learning", "docs": "Docs",
    "science": "Science", "validation": "Validation", "infrastructure": "Infrastructure",
}
PUBLIC_IDS = tuple(PUBLIC_TITLES)
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
SKILL_NAME = re.compile(r"palarran-[a-z][a-z0-9-]{0,119}\Z")


class RegistryError(ValueError):
    """Fixed safe validation code, never untrusted source content."""


def _object(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise RegistryError("invalid_fields")


def _text(value, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise RegistryError("invalid_text")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise RegistryError("invalid_text") from None


def _id(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise RegistryError("invalid_identifier")


def _relative(value):
    if (not isinstance(value, str) or not value or len(value) > 1024
            or "\\" in value or any(part in ("", ".", "..") for part in value.split("/"))
            or PurePosixPath(value).is_absolute() or PurePosixPath(value).as_posix() != value):
        raise RegistryError("invalid_path")
    return PurePosixPath(value).parts


def validate(value):
    """Validate declarations only; missing future canonical files are allowed."""
    _object(value, {"version", "packages"})
    if type(value["version"]) is not int or value["version"] != 1:
        raise RegistryError("unsupported_version")
    packages = value["packages"]
    if not isinstance(packages, list) or len(packages) != len(PUBLIC_IDS):
        raise RegistryError("invalid_package_inventory")
    by_id, owners, paths, legacy_paths = {}, {}, set(), set()
    total_skills = 0
    for package in packages:
        _object(package, {"id", "title", "description", "requires", "capabilities", "skills"})
        package_id = package["id"]
        _id(package_id)
        if package_id not in PUBLIC_TITLES:
            raise RegistryError("unknown_package")
        if package_id in by_id:
            raise RegistryError("duplicate_package")
        if package["title"] != PUBLIC_TITLES[package_id]:
            raise RegistryError("invalid_title")
        _text(package["description"])
        dependencies = package["requires"]
        if not isinstance(dependencies, list) or len(dependencies) > len(PUBLIC_IDS):
            raise RegistryError("invalid_dependencies")
        for dependency in dependencies:
            _id(dependency)
            if dependency not in PUBLIC_TITLES:
                raise RegistryError("unknown_dependency")
            if dependency == package_id:
                raise RegistryError("dependency_cycle")
        if len(set(dependencies)) != len(dependencies):
            raise RegistryError("duplicate_dependency")
        if (package_id == "core" and dependencies) or (package_id != "core" and "core" not in dependencies):
            raise RegistryError("invalid_core_dependency")
        capabilities = package["capabilities"]
        if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 32:
            raise RegistryError("invalid_capabilities")
        capability_ids = set()
        for capability in capabilities:
            _object(capability, {"id", "status", "description"})
            _id(capability["id"])
            if capability["id"] in capability_ids:
                raise RegistryError("duplicate_capability")
            if capability["status"] not in ("implemented", "planned"):
                raise RegistryError("invalid_capability_status")
            _text(capability["description"])
            capability_ids.add(capability["id"])
        skills = package["skills"]
        if not isinstance(skills, list) or len(skills) > 100:
            raise RegistryError("invalid_skills")
        total_skills += len(skills)
        if total_skills > 1000:
            raise RegistryError("invalid_skills")
        for skill in skills:
            _object(skill, {"name", "path", "legacy_path"})
            name = skill["name"]
            if not isinstance(name, str) or not SKILL_NAME.fullmatch(name):
                raise RegistryError("invalid_skill_name")
            if name in owners:
                raise RegistryError("duplicate_skill_owner")
            parts = _relative(skill["path"])
            legacy = _relative(skill["legacy_path"])
            if (len(parts) != 6 or parts[0] != "packages" or parts[1] != package_id
                    or parts[2] not in capability_ids or parts[3:] != ("skills", name, "SKILL.md")
                    or legacy != ("skills", name, "SKILL.md")):
                raise RegistryError("invalid_skill_path")
            if skill["path"] in paths or skill["legacy_path"] in legacy_paths:
                raise RegistryError("duplicate_skill_path")
            owners[name] = package_id
            paths.add(skill["path"])
            legacy_paths.add(skill["legacy_path"])
        by_id[package_id] = package
    if set(by_id) != set(PUBLIC_IDS):
        raise RegistryError("invalid_package_inventory")
    visited, active = set(), set()

    def visit(package_id):
        if package_id in active:
            raise RegistryError("dependency_cycle")
        if package_id in visited:
            return
        active.add(package_id)
        for dependency in by_id[package_id]["requires"]:
            visit(dependency)
        active.remove(package_id)
        visited.add(package_id)

    for package_id in PUBLIC_IDS:
        visit(package_id)
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise RegistryError("invalid_json") from None
    if len(encoded) > MAX_CATALOG_BYTES:
        raise RegistryError("catalog_too_large")
    return copy.deepcopy(value)


def _no_symlinks(path):
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise RegistryError("symlink_path")


def _absolute(path):
    try:
        return Path(os.path.abspath(os.path.expanduser(os.fspath(path))))
    except (TypeError, ValueError, OSError):
        raise RegistryError("invalid_path") from None


class Registry:
    def __init__(self, value):
        self._catalog = validate(value)
        self._packages = {package["id"]: package for package in self._catalog["packages"]}

    @property
    def catalog(self):
        return copy.deepcopy(self._catalog)

    @classmethod
    def load(cls, path):
        path = _absolute(path)
        _no_symlinks(path)
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                raise RegistryError("invalid_catalog_file")
            with path.open("rb") as stream:
                raw = stream.read(MAX_CATALOG_BYTES + 1)
            if len(raw) > MAX_CATALOG_BYTES:
                raise RegistryError("catalog_too_large")
        except OSError:
            raise RegistryError("invalid_catalog_file") from None

        def pairs(entries):
            result = {}
            for key, item in entries:
                if key in result:
                    raise RegistryError("duplicate_key")
                result[key] = item
            return result

        def constant(_):
            raise RegistryError("nonfinite_value")

        def integer(text):
            if len(text) > 20:
                raise RegistryError("invalid_number")
            return int(text)

        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                               parse_constant=constant, parse_int=integer)
        except (UnicodeError, json.JSONDecodeError, RecursionError):
            raise RegistryError("invalid_json") from None
        return cls(value)

    def resolve(self, selected):
        if not isinstance(selected, list) or not selected or len(selected) > len(PUBLIC_IDS):
            raise RegistryError("invalid_selection")
        for package_id in selected:
            if not isinstance(package_id, str) or package_id not in self._packages:
                raise RegistryError("unknown_package")
        if len(set(selected)) != len(selected):
            raise RegistryError("duplicate_selection")
        closure = set()

        def include(package_id):
            if package_id in closure:
                return
            closure.add(package_id)
            for dependency in self._packages[package_id]["requires"]:
                include(dependency)

        for package_id in selected:
            include(package_id)
        ordered, done = [], set()

        def order(package_id):
            if package_id in done:
                return
            for dependency in sorted(self._packages[package_id]["requires"], key=PUBLIC_IDS.index):
                order(dependency)
            done.add(package_id)
            ordered.append(package_id)

        for package_id in PUBLIC_IDS:
            if package_id in closure:
                order(package_id)
        skills = [copy.deepcopy(skill) for package_id in ordered
                  for skill in sorted(self._packages[package_id]["skills"], key=lambda item: item["name"])]
        return {"packages": ordered, "skills": skills}

    def check_paths(self, root, selected=None):
        """Explicitly verify modular files; never fall back to legacy paths."""
        root = _absolute(root)
        _no_symlinks(root)
        if not root.is_dir():
            raise RegistryError("invalid_root")
        resolved = self.resolve(list(PUBLIC_IDS) if selected is None else selected)
        checked = []
        for skill in resolved["skills"]:
            path = root.joinpath(*PurePosixPath(skill["path"]).parts)
            _no_symlinks(path)
            try:
                if not stat.S_ISREG(path.stat().st_mode):
                    raise RegistryError("missing_skill_path")
            except OSError:
                raise RegistryError("missing_skill_path") from None
            checked.append(skill["path"])
        return checked
