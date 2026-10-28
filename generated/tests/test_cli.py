"""Black-box v0.1 acceptance tests; every test uses a private offline workspace."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
BUILTIN_SKILLS = {
    "migrate-to-recipkg",
    "rewrite-to-recipkg",
    "test-feedback",
}


def snapshot(directory: Path) -> dict[str, bytes]:
    if not directory.exists():
        return {}
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


class CLIAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="recipkg-cli-test-")
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.home = self.work / "store"
        self.environment = os.environ.copy()
        self.environment["PYTHONPATH"] = str(REPOSITORY / "src")
        self.environment["PYTHONDONTWRITEBYTECODE"] = "1"

    def cli(self, *arguments: object, success: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-m", "recipkg", "--home", str(self.home), *map(str, arguments)],
            cwd=self.work,
            env=self.environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("Traceback (most recent call last)", result.stderr)
            self.assertTrue(result.stderr.strip(), "Errors should be explained on stderr")
        return result

    def recipe(
        self,
        name: str,
        *,
        marker: str = "ROOT_BEHAVIOR_9c42",
        version: str = "0.1.0",
        dependencies: dict[str, str] | None = None,
        directory: str | None = None,
        kind: str = "software",
    ) -> Path:
        root = self.work / (directory or name)
        root.mkdir()
        entry = "SKILL.md" if kind == "skill" else "BUILD_PROMPT.md"
        manifest = (
            '# Recipe\n\n```toml\nformat = "recipkg/1"\n\n[package]\n'
            f'name = {json.dumps(name)}\nversion = {json.dumps(version)}\n'
            f'kind = {json.dumps(kind)}\ndescription = "An offline test recipe"\n'
            f'entry = {json.dumps(entry)}\n'
        )
        for alias, source in (dependencies or {}).items():
            manifest += f'\n[dependencies.{alias}]\nsource = {json.dumps(source)}\n'
        (root / "RECIPE.md").write_text(manifest + "```\n", encoding="utf-8")
        if kind == "skill":
            body = (
                f"---\nname: {name}\ndescription: Perform the offline acceptance task.\n---\n\n"
                f"# Task\n\n{marker}\n"
            )
        else:
            body = f"# Required behavior\n\n{marker}\n"
        (root / entry).write_text(body, encoding="utf-8")
        (root / "AGENTS.md").write_text(
            "# Agent instructions\n\nPreserve the declared behavior and report actual checks.\n",
            encoding="utf-8",
        )
        (root / "ACCEPTANCE.md").write_text(
            f"# Acceptance\n\nVerify {marker}.\n", encoding="utf-8"
        )
        return root

    def assert_prompt(self, output: str) -> None:
        self.assertTrue(output.lstrip().startswith("#"), output[:300])
        self.assertNotIn("{{", output)
        self.assertNotIn("}}", output)
        self.assertGreater(len(output), 150)

    def test_init_produces_a_markdown_only_recipe(self) -> None:
        target = self.work / "new-recipe"
        self.cli("init", target, "--name", "new-recipe")
        for name in ("RECIPE.md", "BUILD_PROMPT.md", "AGENTS.md", "ACCEPTANCE.md"):
            self.assertTrue((target / name).is_file(), name)
        self.assertTrue(all(path.suffix == ".md" for path in target.rglob("*") if path.is_file()))
        text = (target / "RECIPE.md").read_text(encoding="utf-8")
        blocks = re.findall(r"(?m)^```toml\s*\n(.*?)^```\s*$", text, re.DOTALL)
        self.assertEqual(len(blocks), 1)
        manifest = tomllib.loads(blocks[0])
        self.assertEqual(manifest["format"], "recipkg/1")
        self.assertEqual(manifest["package"]["name"], "new-recipe")
        self.cli("check", target)

    def test_five_primary_actions_print_prompts_without_modifying_inputs(self) -> None:
        package = self.recipe("demo")
        before = snapshot(self.work)
        request = "保留中文要求：重启后数据仍存在。"
        commands = [
            ("extract", "https://example.invalid/source-repository", "--request", request),
            ("build", package, "--request", request),
            ("rewrite", package, "--request", request),
            ("add", package, "https://example.invalid/dependency", "--alias", "storage", "--request", request),
            ("discover", package, "--request", request),
        ]
        prompts: list[str] = []
        for command in commands:
            with self.subTest(action=command[0]):
                result = self.cli(*command)
                self.assert_prompt(result.stdout)
                self.assertIn(request, result.stdout)
                prompts.append(result.stdout)
        self.assertEqual(len(set(prompts)), 5)
        self.assertEqual(snapshot(self.work), before)

    def test_build_includes_every_level_of_dependency_context(self) -> None:
        self.recipe("leaf", marker="LEAF_RULE_b8cd")
        self.recipe("middle", marker="MIDDLE_RULE_22fe", dependencies={"leaf": "../leaf"})
        root = self.recipe("app", marker="APPLICATION_RULE_b976", dependencies={"middle": "../middle"})
        result = self.cli("build", root)
        for marker in ("LEAF_RULE_b8cd", "MIDDLE_RULE_22fe", "APPLICATION_RULE_b976"):
            self.assertIn(marker, result.stdout)
        self.assert_prompt(result.stdout)

    def test_output_file_matches_stdout_and_refuses_an_existing_file(self) -> None:
        package = self.recipe("demo")
        expected = self.cli("build", package).stdout
        output = self.work / "task.md"
        result = self.cli("build", package, "--output", output)
        self.assertEqual(result.stdout, "")
        self.assertEqual(output.read_text(encoding="utf-8"), expected)
        self.cli("build", package, "--output", output, success=False)
        self.assertEqual(output.read_text(encoding="utf-8"), expected)

    def test_prompt_languages_keep_recipe_and_user_material_verbatim(self) -> None:
        package = self.recipe("multilingual", marker="原始配方必须完整保留 ORIGINAL_CONTRACT")
        before = snapshot(package)
        request = "Keep literal {{context}} and 中文要求."
        for action in ("extract", "build", "rewrite", "add", "discover"):
            arguments = (action, package, "../other") if action == "add" else (action, package)
            english = self.cli(*arguments, "--request", request).stdout
            chinese = self.cli(*arguments, "--request", request, "--lang", "zh-CN").stdout
            with self.subTest(action=action):
                self.assertIn("## Task:", english)
                self.assertIn("## 任务：", chinese)
                self.assertNotEqual(english, chinese)
                for output in (english, chinese):
                    self.assertIn(request, output)
                    self.assertIn(f'action = "{action}"', output)
                    if action != "extract":
                        self.assertIn("原始配方必须完整保留 ORIGINAL_CONTRACT", output)
        self.assertEqual(snapshot(package), before)
        self.assertEqual(self.cli("build", package, "--lang", "fr", success=False).stdout, "")

    def test_custom_template_is_not_replaced_by_language_selection(self) -> None:
        package = self.recipe("custom-language")
        template = self.work / "custom.md"
        template.write_text("# Mon modèle\n\n{{context}}\n", encoding="utf-8")
        english = self.cli("build", package, "--template", template, "--lang", "en").stdout
        chinese = self.cli("build", package, "--template", template, "--lang", "zh-CN").stdout
        self.assertEqual(english, chinese)
        self.assertIn("Mon modèle", english)

    def test_self_recipe_carries_all_languages_skills_and_quality_contract(self) -> None:
        recipe_root = Path(os.environ.get("RECIPKG_RECIPE_ROOT", str(REPOSITORY.parent)))
        recipe = recipe_root / "recipes/recipkg"
        if not recipe.is_dir():
            self.skipTest("Set RECIPKG_RECIPE_ROOT to the canonical recipe checkout for integration acceptance")
        archive = self.work / "recipkg.recipe.tar.gz"
        self.cli("pack", recipe, "-o", archive)
        self.cli("check", archive)
        with tarfile.open(archive, "r:gz") as packed:
            files = {item.name: packed.extractfile(item).read() for item in packed if item.isfile()}
        for source in (REPOSITORY / "src/recipkg/data").rglob("*.md"):
            relative = source.relative_to(REPOSITORY / "src/recipkg/data").as_posix()
            self.assertEqual(files[relative], source.read_bytes(), relative)
        self.assertIn(".deps/quality/BUILD_PROMPT.md", files)
        self.cli("install", archive)
        self.assertEqual(set(self.cli("skills", "list").stdout.splitlines()), BUILTIN_SKILLS)
        destination = self.work / "self-skills"
        self.cli("skills", "sync", "--dest", destination)
        for source in (REPOSITORY / "src/recipkg/data/skills").rglob("*.md"):
            relative = source.relative_to(REPOSITORY / "src/recipkg/data/skills")
            self.assertEqual((destination / relative).read_bytes(), source.read_bytes())

    def test_archive_install_build_and_unpack_work_without_original_sources(self) -> None:
        leaf = self.recipe("leaf", marker="PORTABLE_LEAF_74dd")
        middle = self.recipe("middle", marker="PORTABLE_MIDDLE_128a", dependencies={"leaf": "../leaf"})
        app = self.recipe("demo", marker="PORTABLE_APP_263c", dependencies={"middle": "../middle"})
        archive = self.work / "demo-0.1.0.recipe.tar.gz"
        self.cli("pack", app, "-o", archive)
        self.cli("check", archive)
        with tarfile.open(archive, "r:gz") as packed:
            files = [member for member in packed.getmembers() if member.isfile()]
            self.assertTrue(any(Path(member.name).name == "LOCK.md" for member in files))
            for member in files:
                self.assertTrue(member.name.endswith(".md"), member.name)
                content = packed.extractfile(member)
                self.assertIsNotNone(content)
                content.read().decode("utf-8")
        for source in (app, middle, leaf):
            shutil.rmtree(source)
        self.cli("install", archive)
        self.assertIn("demo", self.cli("list").stdout)
        prompt = self.cli("build", "demo@0.1.0").stdout
        for marker in ("PORTABLE_LEAF_74dd", "PORTABLE_MIDDLE_128a", "PORTABLE_APP_263c"):
            self.assertIn(marker, prompt)
        by_name = self.cli("build", "demo").stdout
        for marker in ("PORTABLE_LEAF_74dd", "PORTABLE_MIDDLE_128a", "PORTABLE_APP_263c"):
            self.assertIn(marker, by_name)
        destination = self.work / "unpacked"
        self.cli("unpack", archive, destination)
        roots = [path.parent for path in destination.rglob("RECIPE.md")]
        self.assertTrue(roots)
        largest = max((self.cli("build", root).stdout for root in roots), key=len)
        self.assertIn("PORTABLE_APP_263c", largest)
        self.assertIn("PORTABLE_LEAF_74dd", largest)

    def test_same_version_install_is_idempotent_but_different_content_is_refused(self) -> None:
        package = self.recipe("stable", marker="ORIGINAL_PROMISE_0a8e")
        self.cli("install", package)
        installed = snapshot(self.home)
        self.cli("install", package)
        self.assertEqual(snapshot(self.home), installed)
        (package / "BUILD_PROMPT.md").write_text("# Changed\n\nALTERED_PROMISE_9fb1\n", encoding="utf-8")
        self.cli("install", package, success=False)
        self.assertEqual(snapshot(self.home), installed)
        prompt = self.cli("build", "stable@0.1.0").stdout
        self.assertIn("ORIGINAL_PROMISE_0a8e", prompt)
        self.assertNotIn("ALTERED_PROMISE_9fb1", prompt)

    def test_multiple_versions_require_an_explicit_reference(self) -> None:
        first = self.recipe("versioned", version="0.1.0", marker="FIRST_VERSION_778d", directory="v1")
        second = self.recipe("versioned", version="0.2.0", marker="SECOND_VERSION_676c", directory="v2")
        self.cli("install", first)
        self.cli("install", second)
        result = self.cli("build", "versioned", success=False)
        self.assertEqual(result.stdout, "")
        self.assertIn("FIRST_VERSION_778d", self.cli("build", "versioned@0.1.0").stdout)
        self.assertIn("SECOND_VERSION_676c", self.cli("build", "versioned@0.2.0").stdout)

    def test_remove_preserves_other_installed_packages(self) -> None:
        first = self.recipe("first")
        second = self.recipe("second", marker="KEEP_SECOND_1acd")
        self.cli("install", first)
        self.cli("install", second)
        self.cli("remove", "first")
        self.cli("build", "first@0.1.0", success=False)
        self.assertIn("KEEP_SECOND_1acd", self.cli("build", "second").stdout)

    def test_skill_sync_is_idempotent_and_preserves_user_edits(self) -> None:
        destination = self.work / "agent-skills"
        manual = destination / "manual-skill" / "SKILL.md"
        manual.parent.mkdir(parents=True)
        manual.write_text(
            "---\nname: manual-skill\ndescription: User-maintained skill.\n---\n\nKeep me.\n",
            encoding="utf-8",
        )
        self.cli("skills", "sync", "--dest", destination)
        for name in BUILTIN_SKILLS:
            path = destination / name / "SKILL.md"
            self.assertTrue(path.is_file(), name)
            self.assertIn(f"name: {name}", path.read_text(encoding="utf-8"))
        first_sync = snapshot(destination)
        self.cli("skills", "sync", "--dest", destination)
        self.assertEqual(snapshot(destination), first_sync)
        edited = destination / "migrate-to-recipkg" / "SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nUser-owned customization.\n", encoding="utf-8")
        before_conflict = snapshot(destination)
        self.cli("skills", "sync", "--dest", destination, success=False)
        self.assertEqual(snapshot(destination), before_conflict)
        self.assertIn("Keep me.", manual.read_text(encoding="utf-8"))

    def test_installed_skill_can_be_synced_alongside_builtins(self) -> None:
        package = self.recipe("custom-workflow", kind="skill", marker="CUSTOM_SKILL_bf6c")
        self.cli("install", package)
        destination = self.work / "agent-skills"
        self.cli("skills", "sync", "--dest", destination)
        installed = destination / "custom-workflow" / "SKILL.md"
        self.assertTrue(installed.is_file())
        self.assertIn("CUSTOM_SKILL_bf6c", installed.read_text(encoding="utf-8"))
        self.assertIn("custom-workflow", self.cli("skills", "list").stdout)

    def test_missing_dependency_does_not_emit_an_incomplete_prompt(self) -> None:
        package = self.recipe("broken", dependencies={"missing": "../does-not-exist"})
        result = self.cli("build", package, success=False)
        self.assertEqual(result.stdout, "")

    def test_build_does_not_fetch_unresolved_remote_dependencies(self) -> None:
        package = self.recipe(
            "offline",
            dependencies={"remote": "https://example.invalid/dependency.recipe.tar.gz"},
        )
        result = self.cli("build", package, success=False)
        self.assertEqual(result.stdout, "")
        self.assertTrue(any(word in result.stderr.lower() for word in ("pack", "offline", "network", "remote")))


if __name__ == "__main__":
    unittest.main()
