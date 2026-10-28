"""Discovery boundaries and CLI output without depending on a live GitHub search."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from unittest import mock
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from recipkg.cli import main
from recipkg.package import RecipeError
from recipkg.search import search_packages


class SearchTests(unittest.TestCase):
    def payload(self, *, incomplete=False):
        return {"incomplete_results": incomplete, "items": [{
            "full_name": "example/recipes", "html_url": "https://github.com/example/recipes",
            "description": "Portable recipes", "default_branch": "main", "topics": ["recipkg"],
            "private": False,
        }]}

    def response(self, opener, payload):
        opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()

    @mock.patch("recipkg.search.build_opener")
    def test_search_is_scoped_and_has_no_installation_side_effect(self, opener):
        self.response(opener, self.payload())
        with mock.patch.dict("os.environ", {"GH_TOKEN": "", "GITHUB_TOKEN": ""}):
            results, incomplete = search_packages("storage topic:other OR tools", limit=5)
        request = opener.return_value.open.call_args.args[0]
        query = parse_qs(urlsplit(request.full_url).query)
        self.assertEqual(query["q"], ['topic:recipkg is:public "storage" "topic:other" "OR" "tools"'])
        self.assertEqual(query["per_page"], ["5"])
        self.assertEqual(results[0]["repository"], "example/recipes")
        self.assertNotIn("Authorization", request.headers)
        self.assertFalse(incomplete)

    @mock.patch("recipkg.search.build_opener")
    def test_json_and_incomplete_warning_do_not_mix(self, opener):
        self.response(opener, self.payload(incomplete=True))
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(main(["search", "--json"]), 0)
        self.assertEqual(json.loads(output.getvalue())[0]["url"], "https://github.com/example/recipes")
        self.assertIn("incomplete", errors.getvalue())
        self.assertIn("verify RECIPE.md", errors.getvalue())

    @mock.patch("recipkg.search.build_opener")
    def test_invalid_query_and_limit_fail_before_network(self, opener):
        for query, limit in (("ok", 0), ("ok", 101), ("bad\ninput", 5), ("x" * 201, 5)):
            with self.subTest(query=query, limit=limit), self.assertRaises(RecipeError):
                search_packages(query, limit)
        opener.assert_not_called()

    @mock.patch("recipkg.search.build_opener")
    def test_empty_results_are_success(self, opener):
        self.response(opener, {"incomplete_results": False, "items": []})
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(main(["search", "--json"]), 0)
        self.assertEqual(json.loads(output.getvalue()), [])

    @mock.patch("recipkg.search.build_opener")
    def test_rejects_malformed_unmarked_and_oversized_results(self, opener):
        invalid = self.payload()
        invalid["items"][0]["topics"] = []
        for payload in (None, {"items": []}, invalid):
            self.response(opener, payload)
            with self.subTest(payload=payload), self.assertRaises(RecipeError):
                search_packages()
        with mock.patch("recipkg.search.MAX_SEARCH_BYTES", 8):
            self.response(opener, self.payload())
            with self.assertRaises(RecipeError):
                search_packages()

    @mock.patch("recipkg.search.build_opener")
    def test_network_and_rate_limit_errors_produce_no_partial_json(self, opener):
        for error in (URLError("offline"), HTTPError("https://api.github.com/search/repositories", 429, "rate limited", {}, None)):
            opener.return_value.open.side_effect = error
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(main(["search", "--json"]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertNotIn("Traceback", errors.getvalue())

    @mock.patch("recipkg.search.build_opener")
    def test_optional_token_stays_in_request_headers_and_redirects_are_disabled(self, opener):
        self.response(opener, self.payload())
        with mock.patch.dict("os.environ", {"GH_TOKEN": "test-token"}):
            search_packages()
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer test-token")
        self.assertNotIn("test-token", request.full_url)
        handler = opener.call_args.args[0]
        self.assertIsNone(handler.redirect_request(request, None, 302, "redirect", {}, "https://other.example"))


if __name__ == "__main__":
    unittest.main()
