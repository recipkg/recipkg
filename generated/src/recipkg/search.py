"""Explicit discovery of public recipe repositories through GitHub topics."""

from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .package import RecipeError


MAX_SEARCH_BYTES = 4 * 1024 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A GitHub token must never follow a redirect to another host.
        return None


def search_packages(query: str = "", limit: int = 20) -> tuple[list[dict[str, str]], bool]:
    """Return tagged repository candidates, not validated or installed recipes."""
    if not 1 <= limit <= 100:
        raise RecipeError("Search limit must be between 1 and 100")
    if len(query) > 200 or any(ord(char) < 32 for char in query):
        raise RecipeError("Search text must be at most 200 characters without control characters")
    # Treat user words as text, so qualifiers cannot replace the topic filter.
    terms = " ".join(json.dumps(word, ensure_ascii=False) for word in query.split())
    search_query = f"topic:recipkg is:public {terms}".strip()
    if len(search_query) > 256:
        raise RecipeError("Search query is too long; use fewer keywords")
    parameters = urlencode({"q": search_query, "per_page": limit})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "recipkg/0.1"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/search/repositories?{parameters}", headers=headers)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=15) as response:
            data = response.read(MAX_SEARCH_BYTES + 1)
    except HTTPError as exc:
        exc.close()
        if exc.code in (403, 429):
            reason = "rate limit or access restriction; retry later or use GH_TOKEN"
        elif exc.code == 401:
            reason = "authentication failed; check GH_TOKEN or GITHUB_TOKEN"
        else:
            reason = f"HTTP {exc.code}"
        raise RecipeError(f"GitHub search failed: {reason}") from exc
    except (OSError, URLError, ValueError) as exc:
        raise RecipeError(f"Cannot search GitHub: {exc}") from exc
    if len(data) > MAX_SEARCH_BYTES:
        raise RecipeError("GitHub search response exceeds the size limit")
    try:
        payload = json.loads(data)
        if (not isinstance(payload, dict) or not isinstance(payload.get("items"), list)
                or not isinstance(payload.get("incomplete_results"), bool)
                or len(payload["items"]) > limit):
            raise ValueError("unexpected result structure")
        results = []
        for item in payload["items"]:
            name = item["full_name"]
            url = item["html_url"]
            description = item.get("description") or ""
            branch = item["default_branch"]
            if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name)
                    or url != f"https://github.com/{name}"
                    or not isinstance(branch, str) or not branch
                    or not isinstance(description, str) or not isinstance(item["topics"], list)
                    or "recipkg" not in item["topics"]
                    or item.get("private", False)):
                raise ValueError("unexpected repository metadata")
            results.append({"repository": name, "url": url, "description": description,
                            "default_branch": branch})
        return results, payload["incomplete_results"]
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise RecipeError("Invalid GitHub search response") from exc
