"""Synchronize Markdown skills without overwriting unowned or edited files."""

from __future__ import annotations

import hashlib
from importlib import resources
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import tomllib

from .package import RecipeError, check


STATE_NAME = ".recipkg-skills.toml"
STATE_FORMAT = "recipkg-skills/1"
_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _text(data: bytes, label: str) -> str:
    try:
        value = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecipeError(f"Skill file is not UTF-8: {label}") from exc
    if "\0" in value:
        raise RecipeError(f"Skill file contains a NUL byte: {label}")
    return value


def _metadata_scalar(value: str, field: str) -> str:
    value = value.strip()
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError) as exc:
            raise RecipeError(f"Invalid quoted skill {field}; use a plain or JSON-quoted string") from exc
        if not isinstance(parsed, str):
            raise RecipeError(f"Skill {field} must be a string")
        return parsed
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise RecipeError(f"Unterminated skill {field}")
        return value[1:-1].replace("''", "'")
    value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
    if value.lower() in {"null", "true", "false"} or value == "~":
        raise RecipeError(f"Skill {field} must be a nonempty string")
    return value


def _validate_skill_bytes(data: bytes, label: str) -> tuple[str, str]:
    """Read the two required scalar fields, retaining the original YAML verbatim."""
    value = _text(data, label).replace("\r\n", "\n")
    lines = value.splitlines()
    if not lines or lines[0] != "---":
        raise RecipeError(f"Missing YAML frontmatter in {label}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise RecipeError(f"Unterminated YAML frontmatter in {label}") from exc
    fields: dict[str, str] = {}
    i = 1
    while i < end:
        match = re.fullmatch(r"(name|description):[ \t]*(.*)", lines[i])
        if match:
            key, raw = match.groups()
            if key in fields:
                raise RecipeError(f"Duplicate skill {key} in {label}")
            if raw.strip() in {"|", "|-", "|+", ">", ">-", ">+"}:
                body: list[str] = []
                i += 1
                while i < end and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                    body.append(lines[i].strip())
                    i += 1
                fields[key] = (" " if raw.strip().startswith(">") else "\n").join(body).strip()
                continue
            fields[key] = _metadata_scalar(raw, key)
        i += 1
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name or len(name) > 64 or not _NAME.fullmatch(name):
        raise RecipeError(f"Invalid or missing skill name in {label}")
    if not description.strip() or len(description) > 1024:
        raise RecipeError(f"Invalid or missing skill description in {label}")
    return name, description


def validate_skill(path: Path) -> tuple[str, str]:
    """Validate SKILL.md's required metadata and return its name and description.

    Plain, JSON-quoted, single-quoted, and block scalar metadata are supported.
    Other frontmatter fields and the Markdown body are preserved unchanged.
    """
    path = Path(path)
    if path.is_dir():
        path = path / "SKILL.md"
    _reject_symlink_path(path)
    try:
        return _validate_skill_bytes(path.read_bytes(), str(path))
    except OSError as exc:
        raise RecipeError(f"Cannot read skill: {path}: {exc}") from exc


def _reject_symlink_path(path: Path) -> None:
    path = path.absolute()
    for ancestor in [*reversed(path.parents), path]:
        if ancestor.is_symlink():
            raise RecipeError(f"Refusing a symbolic link in skill path: {ancestor}")


def _read_tree(root, prefix: str = "") -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        relative = f"{prefix}{child.name}"
        if isinstance(child, Path) and child.is_symlink():
            raise RecipeError(f"Skill contains a symbolic link: {relative}")
        if child.is_dir():
            result.update(_read_tree(child, relative + "/"))
        elif child.is_file():
            if not child.name.endswith(".md"):
                raise RecipeError(f"Skill payload must contain only Markdown: {relative}")
            data = child.read_bytes()
            _text(data, relative)
            result[relative] = data
        else:
            raise RecipeError(f"Skill contains an unsupported file: {relative}")
    return result


def _collect_skills(home: Path) -> dict[str, dict[str, bytes]]:
    desired: dict[str, dict[str, bytes]] = {}

    def add(expected_name: str, files: dict[str, bytes], label: str) -> None:
        if "SKILL.md" not in files:
            raise RecipeError(f"Missing SKILL.md in {label}")
        name, _description = _validate_skill_bytes(files["SKILL.md"], label)
        if name != expected_name:
            raise RecipeError(f"Skill name {name!r} does not match {expected_name!r}: {label}")
        if name in desired and desired[name] != files:
            raise RecipeError(
                f"Conflicting skill {name!r}; remove the unwanted installed version or rename the skill"
            )
        desired[name] = files

    builtin = resources.files("recipkg").joinpath("data", "skills")
    for directory in sorted(builtin.iterdir(), key=lambda item: item.name):
        if directory.is_dir():
            add(directory.name, _read_tree(directory), f"builtin/{directory.name}")

    packages = Path(home) / "packages"
    _reject_symlink_path(packages)
    if packages.exists():
        if not packages.is_dir():
            raise RecipeError(f"Package store is not a directory: {packages}")
        for name in sorted(packages.iterdir()):
            if name.is_symlink():
                raise RecipeError(f"Package store contains a symbolic link: {name}")
            if not name.is_dir():
                continue
            for version in sorted(name.iterdir()):
                if version.is_symlink():
                    raise RecipeError(f"Package store contains a symbolic link: {version}")
                if not version.is_dir():
                    continue
                recipe = check(version)
                if recipe.kind == "skill":
                    files = _read_tree(version)
                    # Container metadata is not part of the Agent Skill payload.
                    # Removing it also lets identical skill versions deduplicate.
                    files.pop("RECIPE.md", None)
                    files.pop("LOCK.md", None)
                    add(recipe.name, files, str(version))
                embedded = version / "skills"
                if embedded.exists():
                    _reject_symlink_path(embedded)
                    if not embedded.is_dir():
                        raise RecipeError(f"Embedded skills path is not a directory: {embedded}")
                    for directory in sorted(embedded.iterdir()):
                        if not directory.is_dir() or directory.is_symlink():
                            raise RecipeError(f"Expected an embedded skill directory: {directory}")
                        add(directory.name, _read_tree(directory), str(directory))
    return desired


def list_skills(home: Path) -> list[str]:
    """List the desired skills without writing any files."""
    return sorted(_collect_skills(Path(home)))


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_state(path: Path) -> dict[str, str]:
    if path.is_symlink():
        raise RecipeError(f"Refusing a symbolic skill state file: {path}")
    if not path.exists():
        return {}
    try:
        state = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise RecipeError(f"Cannot read skill ownership state: {path}") from exc
    if state.get("format") != STATE_FORMAT or not isinstance(state.get("files"), dict):
        raise RecipeError(f"Invalid skill ownership state: {path}")
    files = state["files"]
    for relative, digest in files.items():
        parts = PurePosixPath(relative).parts
        if (
            not isinstance(relative, str)
            or "\\" in relative
            or len(parts) < 2
            or relative.startswith("/")
            or any(part in {".", "..", ""} for part in relative.split("/"))
            or not _NAME.fullmatch(parts[0])
            or len(parts[0]) > 64
            or not relative.endswith(".md")
            or not isinstance(digest, str)
            or not _HASH.fullmatch(digest)
        ):
            raise RecipeError(f"Unsafe path or checksum in skill ownership state: {relative!r}")
    return files


def _existing_tree(root: Path) -> tuple[dict[str, bytes], set[str]]:
    if root.is_symlink():
        raise RecipeError(f"Refusing a symbolic skill directory: {root}")
    if not root.exists():
        return {}, set()
    if not root.is_dir():
        raise RecipeError(f"Skill target is not a directory: {root}")
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    for entry in root.rglob("*"):
        relative = entry.relative_to(root).as_posix()
        if entry.is_symlink():
            raise RecipeError(f"Skill target contains a symbolic link: {entry}")
        if entry.is_dir():
            directories.add(relative)
        elif entry.is_file():
            files[relative] = entry.read_bytes()
        else:
            raise RecipeError(f"Skill target contains an unsupported file: {entry}")
    return files, directories


def sync_skills(home: Path, destination: Path) -> list[str]:
    """Apply the desired skill set after validating every existing managed file."""
    desired = _collect_skills(Path(home))
    destination = Path(destination).absolute()
    _reject_symlink_path(destination)
    if destination.exists() and not destination.is_dir():
        raise RecipeError(f"Skill destination is not a directory: {destination}")
    state_path = destination / STATE_NAME
    previous = _read_state(state_path)
    desired_hashes = {
        f"{name}/{relative}": _hash(data)
        for name, files in sorted(desired.items())
        for relative, data in sorted(files.items())
    }
    old_names = {relative.split("/", 1)[0] for relative in previous}
    affected = sorted(old_names | set(desired))
    current: dict[str, dict[str, bytes]] = {}

    for name in affected:
        root = destination / name
        files, directories = _existing_tree(root)
        current[name] = files
        owned = {
            relative.split("/", 1)[1]: digest
            for relative, digest in previous.items()
            if relative.startswith(name + "/")
        }
        if root.exists() and not owned:
            raise RecipeError(f"Refusing to overwrite unowned skill: {name}")
        extra = set(files) - set(owned)
        expected_directories = {
            str(parent)
            for relative in owned
            for parent in PurePosixPath(relative).parents
            if str(parent) != "."
        }
        extra_directories = directories - expected_directories
        if extra or extra_directories:
            raise RecipeError(f"Skill {name!r} contains user-added files or directories; preserve or move them before syncing")
        edited = [relative for relative, data in files.items() if _hash(data) != owned[relative]]
        if edited:
            raise RecipeError(f"Skill {name!r} has user edits in {edited[0]!r}; refusing to overwrite")

    if previous == desired_hashes and all(current.get(name, {}) == files for name, files in desired.items()):
        return sorted(desired)

    destination.parent.mkdir(parents=True, exist_ok=True)
    state_text = f'format = "{STATE_FORMAT}"\n\n[files]\n'
    state_text += "".join(
        f"{json.dumps(relative, ensure_ascii=False)} = {json.dumps(digest)}\n"
        for relative, digest in sorted(desired_hashes.items())
    )
    with tempfile.TemporaryDirectory(prefix=".recipkg-sync-", dir=destination.parent) as temporary:
        staging = Path(temporary)
        for name, files in desired.items():
            for relative, data in files.items():
                target = staging / "new" / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        new_state = staging / "state.toml"
        new_state.write_text(state_text, encoding="utf-8")
        destination.mkdir(parents=True, exist_ok=True)
        backups: list[str] = []
        written: list[str] = []
        try:
            for name in affected:
                target = destination / name
                if target.exists():
                    backup = staging / "backup" / name
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    target.rename(backup)
                    backups.append(name)
                if name in desired:
                    (staging / "new" / name).rename(target)
                    written.append(name)
            new_state.replace(state_path)
        except OSError as exc:
            for name in reversed(written):
                shutil.rmtree(destination / name)
            for name in reversed(backups):
                (staging / "backup" / name).rename(destination / name)
            raise RecipeError(f"Could not synchronize skills: {exc}") from exc
    return sorted(desired)
