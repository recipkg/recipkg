"""Ownership and path invariants for skill synchronization."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from recipkg.package import RecipeError
from recipkg.skills import list_skills, sync_skills, validate_skill


class SkillSynchronizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="recipkg-skills-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "store"
        self.destination = self.root / "skills"

    def installed_skill(self, name: str = "custom-task", version: str = "0.1.0", body: str = "Do the task.") -> Path:
        root = self.home / "packages" / name / version
        root.mkdir(parents=True)
        (root / "RECIPE.md").write_text(
            '# Recipe\n\n```toml\nformat = "recipkg/1"\n\n[package]\n'
            f'name = "{name}"\nversion = "{version}"\nkind = "skill"\n'
            'description = "A custom task"\nentry = "SKILL.md"\n```\n',
            encoding="utf-8",
        )
        (root / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Perform a custom task.\n---\n\n{body}\n",
            encoding="utf-8",
        )
        return root

    def test_listing_does_not_create_a_store(self) -> None:
        names = list_skills(self.home)
        self.assertEqual(names, ["migrate-to-recipkg", "rewrite-to-recipkg", "test-feedback"])
        self.assertFalse(self.home.exists())

    def test_required_metadata_accepts_a_folded_description(self) -> None:
        skill = self.root / "SKILL.md"
        skill.write_text(
            "---\nname: sample-task\ndescription: >-\n  Perform one task\n  and report the result.\n---\n\n# Steps\n",
            encoding="utf-8",
        )
        name, description = validate_skill(skill)
        self.assertEqual(name, "sample-task")
        self.assertEqual(description, "Perform one task and report the result.")
        skill.write_text("---\nname: sample-task\n---\n", encoding="utf-8")
        with self.assertRaises(RecipeError):
            validate_skill(skill)

    def test_sync_refuses_a_preexisting_unowned_skill(self) -> None:
        target = self.destination / "migrate-to-recipkg"
        target.mkdir(parents=True)
        document = target / "SKILL.md"
        original = b"# My existing migrate-to-recipkg skill\n"
        document.write_bytes(original)
        with self.assertRaises(RecipeError):
            sync_skills(self.home, self.destination)
        self.assertEqual(document.read_bytes(), original)
        self.assertFalse((self.destination / ".recipkg-skills.toml").exists())

    def test_sync_rejects_a_symlink_destination(self) -> None:
        actual = self.root / "unrelated"
        actual.mkdir()
        self.destination.symlink_to(actual, target_is_directory=True)
        with self.assertRaises(RecipeError):
            sync_skills(self.home, self.destination)
        self.assertEqual(list(actual.iterdir()), [])

    def test_tampered_ownership_cannot_escape_the_destination(self) -> None:
        self.destination.mkdir()
        outside = self.root / "outside" / "SKILL.md"
        outside.parent.mkdir()
        outside.write_text("Preserve this file.\n", encoding="utf-8")
        (self.destination / ".recipkg-skills.toml").write_text(
            'format = "recipkg-skills/1"\n[files]\n'
            '"../outside/SKILL.md" = "' + "0" * 64 + '"\n',
            encoding="utf-8",
        )
        with self.assertRaises(RecipeError):
            sync_skills(self.home, self.destination)
        self.assertEqual(outside.read_text(encoding="utf-8"), "Preserve this file.\n")

    def test_uninstalled_skill_is_removed_only_if_unchanged(self) -> None:
        package = self.installed_skill()
        sync_skills(self.home, self.destination)
        document = self.destination / "custom-task" / "SKILL.md"
        original = document.read_bytes()
        shutil.rmtree(package)
        document.write_bytes(original + b"\nUser customization.\n")
        with self.assertRaises(RecipeError):
            sync_skills(self.home, self.destination)
        self.assertTrue(document.exists())
        document.write_bytes(original)
        sync_skills(self.home, self.destination)
        self.assertFalse(document.parent.exists())
        self.assertTrue((self.destination / "migrate-to-recipkg" / "SKILL.md").exists())

    def test_identical_skill_versions_deduplicate_but_different_bodies_conflict(self) -> None:
        self.installed_skill(version="0.1.0")
        second = self.installed_skill(version="0.2.0")
        names = sync_skills(self.home, self.destination)
        self.assertEqual(names.count("custom-task"), 1)
        target = self.destination / "custom-task" / "SKILL.md"
        original = target.read_bytes()
        document = second / "SKILL.md"
        document.write_text(document.read_text(encoding="utf-8") + "\nDifferent task.\n", encoding="utf-8")
        with self.assertRaises(RecipeError):
            sync_skills(self.home, self.destination)
        self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
