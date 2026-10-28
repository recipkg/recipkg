"""Explicit, bounded acquisition of remote recipe sources (standard library only)."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class SourceError(ValueError):
    """A remote source could not be acquired safely."""


def validate_https(url: str) -> str:
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        raise SourceError("source URL must be an HTTPS URL")
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.fragment):
            raise SourceError("source URL must use HTTPS, without credentials or a fragment")
        _ = parsed.port
    except ValueError as exc:
        raise SourceError(f"invalid source URL: {exc}") from exc
    return url


class _HTTPSRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_archive(url: str, limit: int) -> bytes:
    validate_https(url)
    request = Request(url, headers={"User-Agent": "recipkg/0.1"})
    try:
        with build_opener(_HTTPSRedirect()).open(request, timeout=30) as response:
            validate_https(response.geturl())
            data = response.read(limit + 1)
    except (OSError, URLError, ValueError) as exc:
        raise SourceError(f"cannot download recipe archive: {exc}") from exc
    if len(data) > limit:
        raise SourceError("download exceeds the compressed archive size limit")
    return data


def checkout_git(url: str, revision: str, subdir: str, destination: Path) -> Path:
    """Fetch exactly one commit; never run hooks, submodules, or user filters."""
    validate_https(url)
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        raise SourceError("git dependencies require a full 40-character commit in rev")
    if not isinstance(subdir, str):
        raise SourceError("git subdir must be a string")
    parts = PurePosixPath(subdir).parts if subdir else ()
    if ("\\" in subdir or subdir.startswith("/") or any(p in (".", "..") for p in subdir.split("/"))
            or any(":" in p for p in parts)) and subdir:
        raise SourceError("git subdir must be a relative path without '..'")
    if not shutil.which("git"):
        raise SourceError("Git sources require the git executable")
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull})
    command = ["git", "-c", f"core.hooksPath={os.devnull}", "-c", "protocol.allow=never",
               "-c", "protocol.https.allow=always", "-c", "http.followRedirects=false",
               "-c", "submodule.recurse=false"]

    def run(*arguments: str) -> str:
        try:
            result = subprocess.run(command + list(arguments), env=env, check=True,
                                    capture_output=True, text=True, timeout=45)
        except FileNotFoundError as exc:
            raise SourceError("Git sources require the git executable") from exc
        except subprocess.TimeoutExpired as exc:
            raise SourceError("git source operation timed out") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "git failed").strip()[-2000:]
            raise SourceError(f"cannot fetch git dependency: {detail}") from exc
        return result.stdout.strip()

    run("init", "--quiet", str(destination))
    run("-C", str(destination), "fetch", "--quiet", "--depth=1", "--no-tags", url, revision)
    actual = run("-C", str(destination), "rev-parse", "FETCH_HEAD")
    if actual.lower() != revision.lower():
        raise SourceError("git fetched a different commit than the pinned rev")
    run("-C", str(destination), "checkout", "--quiet", "--detach", revision)
    root = destination
    for part in parts:
        root = root / part
        if root.is_symlink():
            raise SourceError("git subdir may not traverse a symbolic link")
    if not root.is_dir():
        raise SourceError("git subdir does not exist")
    return root
