"""Explicit package installation, with no build hooks or model calls."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile

from .package import Recipe, RecipeError, check, load_recipe, pack, unpack


NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def data_home(override: str | Path | None = None) -> Path:
    if override is not None:
        return Path(override).expanduser().absolute()
    if os.environ.get("RECIPKG_HOME"):
        return Path(os.environ["RECIPKG_HOME"]).expanduser().absolute()
    base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return (base / "recipkg").expanduser().absolute()


def _safe_child(home: Path, path: Path) -> Path:
    base = home / "packages"
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError as exc:
        raise RecipeError("Installed package path escapes the package store") from exc
    current = path
    while current != base and current != current.parent:
        if current.is_symlink():
            raise RecipeError(f"Symlink in package store: {current}")
        current = current.parent
    if base.is_symlink():
        raise RecipeError("The packages directory must not be a symlink")
    return path


def installed(home: Path) -> list[Recipe]:
    base = home / "packages"
    if not base.exists():
        return []
    _safe_child(home, base)
    result = []
    for name in sorted(base.iterdir()):
        if not name.is_dir() or name.is_symlink():
            raise RecipeError(f"Unexpected entry in package store: {name.name}")
        for version in sorted(name.iterdir()):
            _safe_child(home, version)
            if not version.is_dir():
                raise RecipeError(f"Unexpected entry in package store: {version}")
            recipe = load_recipe(version)
            if recipe.name != name.name or recipe.version != version.name:
                raise RecipeError(f"Package identity does not match store path: {version}")
            result.append(recipe)
    return result


def resolve_ref(value: str | Path, home: Path) -> Path:
    local = Path(value).expanduser()
    if local.exists() or local.is_symlink():
        return local.absolute()
    text = str(value)
    if "://" in text:
        raise RecipeError("Remote packages must be fetched with pack or install before rendering a prompt")
    name, sep, version = text.partition("@")
    if not NAME.fullmatch(name) or len(name) > 64:
        raise RecipeError(f"Package path does not exist: {text}")
    choices = [r for r in installed(home) if r.name == name and (not sep or r.version == version)]
    if not choices:
        raise RecipeError(f"Package not found: {text}; use a directory/archive or install it first")
    if len(choices) > 1:
        versions = ", ".join(f"{r.name}@{r.version}" for r in choices)
        raise RecipeError(f"Ambiguous installed package {name}: choose {versions}")
    return choices[0].root


def _payload_hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RecipeError(f"Symlink in package: {path}")
        if path.is_file() and path.name != "LOCK.md":
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def install_package(source: str | Path, home: Path) -> tuple[Recipe, bool]:
    home.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".install-", dir=home) as temp:
        work = Path(temp)
        archive = pack(source, work / "package.recipe.tar.gz")
        root = unpack(archive, work / "unpacked")
        recipe = check(root)
        dest = _safe_child(home, home / "packages" / recipe.name / recipe.version)
        if dest.exists():
            existing = check(dest)
            if _payload_hashes(dest) != _payload_hashes(root):
                raise RecipeError(
                    f"{recipe.name}@{recipe.version} is already installed with different content; "
                    "change the version or remove the existing package explicitly"
                )
            return existing, False
        dest.parent.mkdir(parents=True, exist_ok=True)
        root.rename(dest)
        return load_recipe(dest), True


def remove_package(value: str, home: Path) -> str:
    if "/" in value or "\\" in value or not NAME.fullmatch(value.partition("@")[0]):
        raise RecipeError("remove accepts an installed name or name@version, never a filesystem path")
    name, sep, version = value.partition("@")
    choices = [r for r in installed(home) if r.name == name and (not sep or r.version == version)]
    if not choices:
        raise RecipeError(f"Installed package not found: {value}")
    if len(choices) > 1:
        raise RecipeError(f"Multiple installed versions of {name}; specify name@version")
    recipe = choices[0]
    path = _safe_child(home, recipe.root)
    shutil.rmtree(path)
    if not any(path.parent.iterdir()):
        path.parent.rmdir()
    return f"{recipe.name}@{recipe.version}"
