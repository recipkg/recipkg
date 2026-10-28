"""The Recipkg/1 Markdown package protocol and deterministic archive operations.

Only pack() may acquire network sources. check(), load_recipe(), unpack(), and
context_text() are local operations. Archives are read and validated completely
before anything is written to an extraction target.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
from datetime import date, datetime, time
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import tempfile
import tomllib
from typing import Any
import unicodedata

from .sources import SourceError, checkout_git, download_archive, validate_https


MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_FILES = 4096
MAX_PACKAGES = 256
MAX_DEPENDENCY_DEPTH = 32
MAX_PATH_DEPTH = 128
MAX_TAR_BYTES = MAX_TOTAL_BYTES + MAX_FILES * 2048 + 1024 * 1024

_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_WINDOWS_DEVICE = re.compile(r"(?:con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])\Z", re.IGNORECASE)
_SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z"
)


class RecipeError(ValueError):
    """A recipe is incomplete, invalid, unsafe, or inconsistent."""


@dataclass(frozen=True)
class Recipe:
    root: Path
    name: str
    version: str
    kind: str
    description: str
    entry: str
    manifest: dict[str, Any]


@dataclass
class _Source:
    root: Path
    files: dict[str, bytes]
    identity: str
    directory: Path | None = None
    archive: bool = False
    require_lock: bool = False
    local_boundary: Path | None = None


def _safe_path(name: str, *, directory: bool = False) -> str:
    if not isinstance(name, str) or not name or "\\" in name:
        raise RecipeError(f"unsafe package path: {name!r}")
    if directory and name.endswith("/"):
        name = name[:-1]
    parts = name.split("/")
    try:
        encoded_length = len(name.encode("utf-8"))
        component_lengths = [len(part.encode("utf-8")) for part in parts]
    except UnicodeError as exc:
        raise RecipeError("package paths must be valid UTF-8") from exc
    if (not name or name.startswith("/") or len(parts) > MAX_PATH_DEPTH
            or any(p in ("", ".", "..") for p in parts)
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or any(c in '<>:"|?*' for c in name) or encoded_length > 4096
            or any(p.endswith((".", " ")) or _WINDOWS_DEVICE.fullmatch(p.split(".")[0]) for p in parts)
            or any(length > 255 for length in component_lengths)):
        raise RecipeError(f"unsafe package path: {name!r}")
    return name


def _markdown_bytes(name: str, data: bytes) -> None:
    _safe_path(name)
    if not name.endswith(".md"):
        raise RecipeError(f"package payload must be Markdown (.md): {name}")
    if len(data) > MAX_FILE_BYTES:
        raise RecipeError(f"file exceeds the {MAX_FILE_BYTES}-byte limit: {name}")
    if b"\0" in data:
        raise RecipeError(f"NUL bytes are not allowed in Markdown: {name}")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecipeError(f"file is not UTF-8 Markdown: {name}") from exc


def _file_limits(files: dict[str, bytes]) -> None:
    if len(files) > MAX_FILES:
        raise RecipeError(f"package exceeds the {MAX_FILES}-file limit")
    if sum(map(len, files.values())) > MAX_TOTAL_BYTES:
        raise RecipeError(f"package exceeds the {MAX_TOTAL_BYTES}-byte payload limit")
    names = set(files)
    portable_paths: dict[str, str] = {}
    for name in names:
        parts = name.split("/")
        if any("/".join(parts[:i]) in names for i in range(1, len(parts))):
            raise RecipeError(f"package file is also used as a directory: {name}")
        for i in range(1, len(parts) + 1):
            prefix = "/".join(parts[:i])
            folded = unicodedata.normalize("NFC", prefix).casefold()
            previous = portable_paths.setdefault(folded, prefix)
            if previous != prefix:
                raise RecipeError(f"package paths collide on a case-insensitive filesystem: {previous}, {prefix}")


def _read_directory(root: Path) -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise RecipeError(f"recipe source must be a directory or recipe archive: {root}")
    files: dict[str, bytes] = {}
    total = 0
    members = 0

    def walk(folder: Path, prefix: str = "") -> None:
        nonlocal total, members
        try:
            entries = sorted(os.scandir(folder), key=lambda item: item.name)
        except OSError as exc:
            raise RecipeError(f"cannot read recipe directory: {exc}") from exc
        for item in entries:
            if item.name == ".git":
                continue
            members += 1
            if members > MAX_FILES * 2:
                raise RecipeError("recipe directory exceeds the member count limit")
            name = prefix + item.name
            _safe_path(name)
            try:
                info = item.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    walk(Path(item.path), name + "/")
                elif stat.S_ISREG(info.st_mode):
                    if info.st_nlink != 1:
                        raise RecipeError(f"hard-linked files are not allowed: {name}")
                    if not name.endswith(".md"):
                        raise RecipeError(f"package payload must be Markdown (.md): {name}")
                    if info.st_size > MAX_FILE_BYTES:
                        raise RecipeError(f"file exceeds the size limit: {name}")
                    with open(item.path, "rb") as stream:
                        data = stream.read(MAX_FILE_BYTES + 1)
                    _markdown_bytes(name, data)
                    total += len(data)
                    files[name] = data
                    if len(files) > MAX_FILES or total > MAX_TOTAL_BYTES:
                        raise RecipeError("recipe directory exceeds package limits")
                else:
                    raise RecipeError(f"links and special files are not allowed: {name}")
            except OSError as exc:
                raise RecipeError(f"cannot read package file {name}: {exc}") from exc

    walk(root)
    _file_limits(files)
    return files


def _archive_files(data: bytes) -> dict[str, bytes]:
    if len(data) > MAX_ARCHIVE_BYTES:
        raise RecipeError("compressed recipe archive exceeds its size limit")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as zipped:
            unpacked = zipped.read(MAX_TAR_BYTES + 1)
        if len(unpacked) > MAX_TAR_BYTES:
            raise RecipeError("uncompressed archive exceeds its size limit")
        files: dict[str, bytes] = {}
        members: set[str] = set()
        directories: set[str] = set()
        total = 0
        with tarfile.open(fileobj=io.BytesIO(unpacked), mode="r:") as archive:
            for member in archive:
                if len(members) >= MAX_FILES * 2:
                    raise RecipeError("archive exceeds the member count limit")
                if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
                    raise RecipeError(f"archive links and special members are forbidden: {member.name}")
                if any(key.startswith("GNU.sparse") for key in member.pax_headers):
                    raise RecipeError("sparse archive members are forbidden")
                name = _safe_path(member.name, directory=member.isdir())
                if name in members:
                    raise RecipeError(f"duplicate archive member: {name}")
                members.add(name)
                if member.isdir():
                    directories.add(name)
                    continue
                if member.size < 0 or member.size > MAX_FILE_BYTES:
                    raise RecipeError(f"archive file exceeds the size limit: {name}")
                stream = archive.extractfile(member)
                if stream is None:
                    raise RecipeError(f"cannot read archive file: {name}")
                content = stream.read(MAX_FILE_BYTES + 1)
                if len(content) != member.size:
                    raise RecipeError(f"truncated archive file: {name}")
                _markdown_bytes(name, content)
                files[name] = content
                total += len(content)
                if len(files) > MAX_FILES or total > MAX_TOTAL_BYTES:
                    raise RecipeError("archive exceeds package limits")
        _file_limits(files)
        for directory in directories:
            parts = directory.split("/")
            if any("/".join(parts[:i]) in files for i in range(1, len(parts) + 1)):
                raise RecipeError(f"archive file conflicts with a directory: {directory}")
        return files
    except (OSError, EOFError, tarfile.TarError) as exc:
        raise RecipeError(f"invalid recipe tar.gz archive: {exc}") from exc


def _toml_document(content: bytes, filename: str) -> tuple[dict[str, Any], str, int, int]:
    text = content.decode("utf-8")
    found: list[tuple[int, int]] = []
    opened: tuple[str, int, str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)[\r\n]*$", line)
        if match:
            fence, info = match.group(1), match.group(2).strip()
            if opened is None:
                opened = (fence[0], len(fence), info, offset + len(line))
            elif fence[0] == opened[0] and len(fence) >= opened[1] and not info:
                if opened[2] == "toml":
                    found.append((opened[3], offset))
                opened = None
        offset += len(line)
    if opened is not None and opened[2] == "toml":
        raise RecipeError(f"unclosed TOML fence in {filename}")
    if len(found) != 1:
        raise RecipeError(f"{filename} must contain exactly one fenced toml block")
    start, end = found[0]
    try:
        parsed = tomllib.loads(text[start:end])
    except tomllib.TOMLDecodeError as exc:
        raise RecipeError(f"invalid TOML in {filename}: {exc}") from exc
    return parsed, text, start, end


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecipeError(f"{field} must be a non-empty string")
    return value


def _recipe(source: _Source) -> Recipe:
    if "RECIPE.md" not in source.files:
        raise RecipeError(f"no RECIPE.md found at recipe root: {source.root}")
    manifest, _, _, _ = _toml_document(source.files["RECIPE.md"], "RECIPE.md")
    if manifest.get("format") != "recipkg/1":
        raise RecipeError("RECIPE.md format must be 'recipkg/1'")
    metadata = manifest.get("package")
    if not isinstance(metadata, dict):
        raise RecipeError("RECIPE.md requires a [package] table")
    name = _string(metadata.get("name"), "package.name")
    if len(name) > 64 or not _SLUG.fullmatch(name):
        raise RecipeError("package.name must be a lowercase slug of at most 64 characters")
    version = _string(metadata.get("version"), "package.version")
    if not _SEMVER.fullmatch(version):
        raise RecipeError("package.version must be a semantic version, such as 1.0.0")
    kind = metadata.get("kind")
    if kind not in ("software", "skill"):
        raise RecipeError("package.kind must be 'software' or 'skill'")
    description = _string(metadata.get("description"), "package.description")
    entry = metadata.get("entry")
    expected_entry = "BUILD_PROMPT.md" if kind == "software" else "SKILL.md"
    if entry != expected_entry:
        raise RecipeError(f"{kind} packages require entry = '{expected_entry}'")
    if entry not in source.files:
        raise RecipeError(f"package entry does not exist: {entry}")
    if kind == "skill":
        from .skills import _validate_skill_bytes
        skill_name, _ = _validate_skill_bytes(source.files[entry], str(source.root / entry))
        if skill_name != name:
            raise RecipeError("SKILL.md name must match package.name")
    dependencies = manifest.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise RecipeError("dependencies must be a TOML table")
    for alias, dependency in dependencies.items():
        if len(alias) > 64 or not _SLUG.fullmatch(alias) or not isinstance(dependency, dict):
            raise RecipeError(f"dependency aliases must be lowercase slugs with table values: {alias}")
        if ("source" in dependency) == ("git" in dependency):
            raise RecipeError(f"dependency {alias} requires exactly one of source or git")
        if "source" in dependency:
            value = _string(dependency["source"], f"dependencies.{alias}.source")
            if "rev" in dependency or "subdir" in dependency:
                raise RecipeError(f"dependency {alias}: rev/subdir require git")
            if "://" in value:
                try:
                    validate_https(value)
                except SourceError as exc:
                    raise RecipeError(str(exc)) from exc
            elif (Path(value).is_absolute() or "\\" in value or ":" in value.split("/")[0]
                  or any(ord(c) < 32 for c in value)):
                raise RecipeError(f"dependency {alias} source must be a relative path or HTTPS URL")
        else:
            try:
                validate_https(dependency["git"])
            except SourceError as exc:
                raise RecipeError(str(exc)) from exc
            revision = dependency.get("rev")
            if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
                raise RecipeError(f"git dependency {alias} requires a full 40-character commit rev")
            if "subdir" in dependency and not isinstance(dependency["subdir"], str):
                raise RecipeError(f"git dependency {alias} subdir must be a string")
            if dependency.get("subdir"):
                _safe_path(dependency["subdir"])
    return Recipe(source.root, name, version, kind, description, entry, manifest)


def _toml_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return repr(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(_toml_value(key) + " = " + _toml_value(value[key])
                                   for key in sorted(value)) + " }"
    raise RecipeError(f"unsupported TOML value: {type(value).__name__}")


def _dump_toml(manifest: dict[str, Any]) -> str:
    return "".join(f"{_toml_value(key)} = {_toml_value(manifest[key])}\n" for key in sorted(manifest))


def _rewrite_manifest(content: bytes, manifest: dict[str, Any]) -> bytes:
    _, text, start, end = _toml_document(content, "RECIPE.md")
    return (text[:start] + _dump_toml(manifest) + text[end:]).encode("utf-8")


def _verify_lock(files: dict[str, bytes], *, required: bool = False) -> None:
    if "LOCK.md" not in files:
        if required:
            raise RecipeError("a recipe archive must contain LOCK.md")
        return
    lock, _, _, _ = _toml_document(files["LOCK.md"], "LOCK.md")
    if lock.get("format") != "recipkg-lock/1" or not isinstance(lock.get("files"), dict):
        raise RecipeError("LOCK.md requires format='recipkg-lock/1' and a files table")
    expected = {name: hashlib.sha256(data).hexdigest()
                for name, data in files.items() if name != "LOCK.md"}
    recorded = lock["files"]
    if set(recorded) != set(expected):
        missing = sorted(set(expected) - set(recorded))
        extra = sorted(set(recorded) - set(expected))
        raise RecipeError(f"LOCK.md file index mismatch (unlisted={missing}, missing={extra})")
    for name, digest in expected.items():
        if recorded[name] != digest:
            raise RecipeError(f"LOCK.md SHA256 integrity mismatch: {name}")
    if not isinstance(lock.get("packages"), list) or not lock["packages"]:
        raise RecipeError("LOCK.md requires a non-empty packages array")
    seen: set[str] = set()
    for record in lock["packages"]:
        if not isinstance(record, dict):
            raise RecipeError("LOCK.md packages entries must be tables")
        path = record.get("path")
        if not isinstance(path, str) or path in seen:
            raise RecipeError("LOCK.md package paths must be unique strings")
        seen.add(path)
        recipe_path = "RECIPE.md" if path == "." else _safe_path(path) + "/RECIPE.md"
        if recipe_path not in files:
            raise RecipeError(f"LOCK.md points to a missing recipe: {path}")
        package_manifest, _, _, _ = _toml_document(files[recipe_path], recipe_path)
        for field in ("name", "version"):
            if record.get(field) != package_manifest.get("package", {}).get(field):
                raise RecipeError(f"LOCK.md package {field} mismatch: {path}")
        _string(record.get("source"), "LOCK.md package source")
        if "rev" in record and not re.fullmatch(r"[0-9a-fA-F]{40}", str(record["rev"])):
            raise RecipeError("LOCK.md git revisions must be full 40-character commits")
    if "." not in seen:
        raise RecipeError("LOCK.md must record the root package")


class _Resolver:
    def __init__(self, allow_network: bool = False):
        self.allow_network = allow_network
        self.cache: dict[str, _Source] = {}
        self.total_loaded = 0
        self.packages = 0
        self.temp = tempfile.TemporaryDirectory(prefix="recipkg-sources-")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.temp.cleanup()

    def _remember(self, source: _Source) -> _Source:
        self.total_loaded += sum(map(len, source.files.values()))
        if self.total_loaded > MAX_TOTAL_BYTES:
            raise RecipeError("combined dependency sources exceed the payload size limit")
        self.cache[source.identity] = source
        return source

    def local(self, value: str | Path, boundary: Path | None = None) -> _Source:
        path = Path(value).expanduser()
        if path.is_symlink():
            raise RecipeError(f"recipe source may not be a symbolic link: {path}")
        path = path.resolve()
        if boundary is not None and not path.is_relative_to(boundary.resolve()):
            raise RecipeError("a Git recipe's relative dependency escapes its checkout")
        identity = "local:" + str(path)
        if identity in self.cache:
            cached = self.cache[identity]
            return _Source(cached.root, cached.files, cached.identity, cached.directory,
                           cached.archive, cached.require_lock, boundary)
        if path.is_dir():
            source = _Source(path, _read_directory(path), identity, path)
        elif path.is_file():
            if not path.name.endswith(".recipe.tar.gz"):
                raise RecipeError("recipe archive filenames must end in .recipe.tar.gz")
            try:
                with path.open("rb") as stream:
                    raw = stream.read(MAX_ARCHIVE_BYTES + 1)
            except OSError as exc:
                raise RecipeError(f"cannot read recipe archive: {exc}") from exc
            source = _Source(path, _archive_files(raw), identity, archive=True, require_lock=True)
        else:
            raise RecipeError(f"recipe source does not exist: {path}")
        self._remember(source)
        source.local_boundary = boundary
        return source

    def remote(self, url: str) -> _Source:
        if not self.allow_network:
            raise RecipeError("remote dependency requires explicit pack/install; context and check never use the network")
        identity = "url:" + url
        if identity not in self.cache:
            try:
                data = download_archive(url, MAX_ARCHIVE_BYTES)
            except SourceError as exc:
                raise RecipeError(str(exc)) from exc
            source = _Source(Path("remote.recipe.tar.gz"), _archive_files(data), identity, archive=True, require_lock=True)
            self._remember(source)
        return self.cache[identity]

    def load(self, value: str | Path) -> _Source:
        if isinstance(value, str) and "://" in value:
            return self.remote(value)
        return self.local(value)

    def dependency(self, parent: _Source, alias: str, dependency: dict[str, Any]) -> _Source:
        if "git" in dependency:
            if parent.archive:
                raise RecipeError(f"archive dependency {alias} must be vendored under .deps/{alias}")
            if not self.allow_network:
                raise RecipeError("git dependency requires explicit pack/install; context and check never use the network")
            identity = "git:" + dependency["git"] + "@" + dependency["rev"].lower() + "/" + dependency.get("subdir", "")
            if identity not in self.cache:
                destination = Path(self.temp.name) / hashlib.sha256(identity.encode()).hexdigest()
                try:
                    root = checkout_git(dependency["git"], dependency["rev"], dependency.get("subdir", ""), destination)
                except SourceError as exc:
                    raise RecipeError(str(exc)) from exc
                if not root.resolve().is_relative_to(destination.resolve()):
                    raise RecipeError("Git recipe path escapes its checkout")
                self._remember(_Source(root, _read_directory(root), identity, root,
                                       local_boundary=destination.resolve()))
            return self.cache[identity]
        value = dependency["source"]
        internal = f".deps/{alias}"
        if value == internal:
            prefix = value + "/"
            files = {name[len(prefix):]: data for name, data in parent.files.items() if name.startswith(prefix)}
            if not files:
                raise RecipeError(f"missing vendored dependency: {internal}")
            return _Source(parent.root / internal, files, parent.identity + "/" + internal,
                           parent.directory / internal if parent.directory else None, parent.archive,
                           local_boundary=parent.local_boundary)
        if parent.archive:
            raise RecipeError(f"archive dependency {alias} must use source = '{internal}'")
        if "://" in value:
            return self.remote(value)
        if parent.directory is None:
            raise RecipeError(f"local dependency has no source directory: {alias}")
        return self.local(parent.directory / value, parent.local_boundary)

    def walk(self, source: _Source, stack: tuple[str, ...] = (), path: str = ".",
             provenance: dict[str, str] | None = None,
             saved: dict[str, dict[str, str]] | None = None) -> tuple[Recipe, dict[str, bytes], list[dict[str, str]]]:
        if source.identity in stack:
            raise RecipeError("dependency cycle: " + " -> ".join(stack + (source.identity,)))
        if len(stack) >= MAX_DEPENDENCY_DEPTH:
            raise RecipeError("dependency nesting exceeds its depth limit")
        self.packages += 1
        if self.packages > MAX_PACKAGES:
            raise RecipeError("dependency tree exceeds its package count limit")
        _verify_lock(source.files, required=source.require_lock)
        own_lock = None
        if "LOCK.md" in source.files:
            own_lock, _, _, _ = _toml_document(source.files["LOCK.md"], "LOCK.md")
            if saved is None:
                saved = {item["path"]: item for item in own_lock["packages"]}
        recipe = _recipe(source)
        dependencies = recipe.manifest.get("dependencies", {})
        owned = {name: data for name, data in source.files.items()
                 if not name.startswith(".deps/") and name != "LOCK.md"}
        for name in source.files:
            if name.startswith(".deps/"):
                parts = name.split("/")
                if len(parts) < 3 or parts[1] not in dependencies or dependencies[parts[1]].get("source") != f".deps/{parts[1]}":
                    raise RecipeError(f"unmanaged or stale vendored dependency file: {name}")
        if saved and "." in saved and (provenance is None or provenance.get("source", "").startswith(".deps/")):
            provenance = saved["."]
        record = {"path": path, "name": recipe.name, "version": recipe.version,
                  "source": "." if provenance is None else provenance.get("source", provenance.get("git", "."))}
        if provenance:
            for key in ("rev", "subdir"):
                if key in provenance:
                    record[key] = provenance[key]
        records = [record]
        manifest = copy.deepcopy(recipe.manifest)
        for alias in sorted(dependencies):
            dependency = dependencies[alias]
            child = self.dependency(source, alias, dependency)
            child_path = f".deps/{alias}" if path == "." else path + f"/.deps/{alias}"
            child_saved = None
            child_prefix = f".deps/{alias}"
            if saved and dependency.get("source") == child_prefix:
                child_saved = {("." if key == child_prefix else key[len(child_prefix) + 1:]): value
                               for key, value in saved.items()
                               if key == child_prefix or key.startswith(child_prefix + "/")}
            _, child_files, child_records = self.walk(child, stack + (source.identity,), child_path,
                                                      dependency, child_saved)
            for name, content in child_files.items():
                owned[f".deps/{alias}/{name}"] = content
            records.extend(child_records)
            rewritten = manifest["dependencies"][alias]
            for key in ("git", "rev", "subdir"):
                rewritten.pop(key, None)
            rewritten["source"] = f".deps/{alias}"
            _file_limits(owned)
        owned["RECIPE.md"] = _rewrite_manifest(owned["RECIPE.md"], manifest)
        for name, content in owned.items():
            _markdown_bytes(name, content)
        _file_limits(owned)
        if own_lock is not None:
            actual_paths = {("." if item["path"] == path else
                             item["path"] if path == "." else item["path"][len(path) + 1:])
                            for item in records}
            if {item["path"] for item in own_lock["packages"]} != actual_paths:
                raise RecipeError("LOCK.md package index does not match the complete dependency tree")
        return recipe, owned, records


def load_recipe(path: str | Path) -> Recipe:
    """Read a local root recipe; use check() for complete dependency validation."""
    with _Resolver() as resolver:
        source = resolver.load(path)
        _verify_lock(source.files, required=source.require_lock)
        return _recipe(source)


def check(source: str | Path) -> Recipe:
    """Validate a complete local dependency tree and any existing lock hashes."""
    with _Resolver() as resolver:
        recipe, _, _ = resolver.walk(resolver.load(source))
        return recipe


def _locked_files(files: dict[str, bytes], records: list[dict[str, str]]) -> dict[str, bytes]:
    result = dict(files)
    lines = ["# Recipkg integrity lock\n\n```toml\n", 'format = "recipkg-lock/1"\n\n[files]\n']
    for name in sorted(files):
        lines.append(f"{_toml_value(name)} = {_toml_value(hashlib.sha256(files[name]).hexdigest())}\n")
    for record in records:
        lines.append("\n[[packages]]\n")
        lines.append(_dump_toml(record))
    lines.append("```\n")
    result["LOCK.md"] = "".join(lines).encode("utf-8")
    _markdown_bytes("LOCK.md", result["LOCK.md"])
    _file_limits(result)
    return result


def context_text(source: str | Path) -> str:
    """Render every locked recursive Markdown file, without executing or networking."""
    with _Resolver() as resolver:
        recipe, files, records = resolver.walk(resolver.load(source))
    files = _locked_files(files, records)
    lines = [f"# Complete recipe context: {recipe.name} {recipe.version}\n\n",
             "The following files contain the complete recursive recipe. Package dependency "
             "instructions apply to their own package. Read each package entry and preserve its contract.\n\n",
             "## File index\n\n"]
    for name in sorted(files):
        lines.append(f"- `{name}`\n")
    for name in sorted(files):
        lines.append(f"\n## File: `{name}`\n\n")
        text = files[name].decode("utf-8")
        lines.append(text)
        if not text.endswith("\n"):
            lines.append("\n")
    return "".join(lines)


def pack(source: str | Path, destination: str | Path) -> Path:
    """Vendor the complete recipe and write a deterministic .recipe.tar.gz archive."""
    with _Resolver(allow_network=True) as resolver:
        provenance = {"source": source} if isinstance(source, str) and "://" in source else None
        recipe, files, records = resolver.walk(resolver.load(source), provenance=provenance)
        source_directories = [item.directory.resolve() for item in resolver.cache.values()
                              if item.directory is not None]
    files = _locked_files(files, records)
    target = Path(destination).expanduser()
    if target.is_symlink():
        raise RecipeError("archive destination may not be a symbolic link")
    if target.is_dir():
        target = target / f"{recipe.name}-{recipe.version}.recipe.tar.gz"
    if not target.name.endswith(".recipe.tar.gz"):
        raise RecipeError("archive output must end in .recipe.tar.gz")
    if target.exists():
        raise RecipeError(f"refusing to overwrite existing archive: {target}")
    if any(target.resolve().is_relative_to(folder) for folder in source_directories):
        raise RecipeError("archive output must be outside every source recipe directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as output:
            with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as zipped:
                with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    for name in sorted(files):
                        info = tarfile.TarInfo(name)
                        info.size = len(files[name])
                        info.mtime = 0
                        info.uid = info.gid = 0
                        info.uname = info.gname = ""
                        info.mode = 0o644
                        archive.addfile(info, io.BytesIO(files[name]))
    except FileExistsError as exc:
        raise RecipeError(f"refusing to overwrite existing archive: {target}") from exc
    except OSError as exc:
        try:
            target.unlink()
        except OSError:
            pass
        raise RecipeError(f"cannot write recipe archive: {exc}") from exc
    return target.resolve()


def unpack(archive: str | Path, destination: str | Path) -> Path:
    """Safely extract a validated archive into a nonexistent or empty directory."""
    with _Resolver() as resolver:
        source = resolver.load(archive)
        if not source.archive:
            raise RecipeError("unpack requires a .recipe.tar.gz archive")
        resolver.walk(source)
        files = source.files
    target = Path(destination).expanduser()
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise RecipeError("unpack destination must be a normal empty directory")
    if target.exists() and any(target.iterdir()):
        raise RecipeError(f"refusing to unpack into a non-empty directory: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".recipkg-unpack-", dir=target.parent))
    try:
        for name in sorted(files):
            output = staging.joinpath(*PurePosixPath(name).parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(files[name])
        if target.is_symlink() or (target.exists() and (not target.is_dir() or any(target.iterdir()))):
            raise RecipeError("unpack destination changed while preparing extraction")
        os.replace(staging, target)
    except (OSError, RecipeError) as exc:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)
        if isinstance(exc, RecipeError):
            raise
        raise RecipeError(f"cannot unpack recipe archive: {exc}") from exc
    return target.resolve()
