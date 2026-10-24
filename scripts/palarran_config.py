#!/usr/bin/env python3
"""Strict public preferences and skill-package selection; no credentials or execution."""
import json
from pathlib import Path

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


def selected(bundle, packages):
    """Retain public support files, but expose only reviewed selected skills."""
    if packages is None:
        return bundle  # Legacy API callers retain their original scope.
    catalog = json.loads(bundle["skills/catalog.json"])
    rows = catalog["skills"] if isinstance(catalog, dict) else catalog
    from package_plugin import PACKAGES
    allowed = {key.removeprefix("palarran-"): set(value["skills"]) for key, value in PACKAGES.items()}
    if "all" in packages:
        if packages != ["all"]:
            raise ValueError("all cannot be mixed with individual packages")
        names = {row["skill"] for row in rows}
    else:
        normalized = [p.removeprefix("palarran-") for p in packages]
        if any(p not in allowed for p in normalized):
            raise ValueError("Unknown skill package")
        names = set().union(*(allowed[p] for p in normalized))
    names.add("palarran-setup")
    return {name: raw for name, raw in bundle.items() if not name.startswith("skills/") or len(Path(name).parts) < 3 or Path(name).parts[1] in names}
