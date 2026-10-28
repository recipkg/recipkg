"""Black-box tests for complete recipes, deterministic archives, and safe extraction."""

from __future__ import annotations

import gzip
import hashlib
import io
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import tomllib
import unittest
from unittest import mock

from recipkg.package import RecipeError, check, context_text, load_recipe, pack, unpack


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def recipe(self, name="example", dependencies="", extra="", marker=None):
        folder = self.root / name
        folder.mkdir()
        (folder / "RECIPE.md").write_text(
            '# Recipe\n\nHuman description retained.\n\n```toml\nformat = "recipkg/1"\n'
            f'[package]\nname = "{name}"\nversion = "1.0.0"\nkind = "software"\n'
            'description = "Example recipe"\nentry = "BUILD_PROMPT.md"\n'
            + dependencies + extra + '\n```\n\nTrailing human guidance.\n', encoding="utf-8")
        (folder / "BUILD_PROMPT.md").write_text(marker or f"# Build {name}\n", encoding="utf-8")
        (folder / "AGENTS.md").write_text("# Agent rules\nRead the contract.\n", encoding="utf-8")
        return folder

    def archive(self, name, entries):
        target = self.root / (name + ".recipe.tar.gz")
        with tarfile.open(target, "w:gz") as archive:
            for filename, data, kind in entries:
                member = tarfile.TarInfo(filename)
                member.type = kind
                if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                    member.linkname = "../../outside"
                if kind == tarfile.REGTYPE:
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
                else:
                    archive.addfile(member)
        return target

    def contents(self, archive):
        with tarfile.open(archive, "r:gz") as opened:
            return {member.name: opened.extractfile(member).read()
                    for member in opened if member.isfile()}

    def test_recursive_context_and_self_contained_archive(self):
        leaf = self.recipe("leaf", marker="DEEP-DEPENDENCY-REQUIREMENT\n")
        middle = self.recipe("middle", '[dependencies.leaf]\nsource = "../leaf"\n')
        root = self.recipe("app", '[dependencies.middle]\nsource = "../middle"\n')
        local_context = context_text(root)
        self.assertIn("DEEP-DEPENDENCY-REQUIREMENT", local_context)
        self.assertIn(".deps/middle/.deps/leaf/BUILD_PROMPT.md", local_context)
        output = pack(root, self.root)
        files = self.contents(output)
        self.assertIn(".deps/middle/.deps/leaf/BUILD_PROMPT.md", files)
        self.assertTrue(all(name.endswith(".md") for name in files))
        import shutil
        shutil.rmtree(leaf)
        shutil.rmtree(middle)
        shutil.rmtree(root)
        self.assertEqual(check(output).name, "app")
        extracted = unpack(output, self.root / "restored")
        self.assertIn("DEEP-DEPENDENCY-REQUIREMENT", context_text(extracted))
        self.assertEqual(load_recipe(extracted).manifest["dependencies"]["middle"]["source"], ".deps/middle")

    def test_deterministic_archives_and_repacking_preserve_provenance(self):
        self.recipe("dep")
        source = self.recipe("app", '[dependencies.helper]\nsource = "../dep"\n')
        first = pack(source, self.root / "first.recipe.tar.gz")
        second = pack(source, self.root / "second.recipe.tar.gz")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with tarfile.open(first) as opened:
            self.assertEqual(opened.getnames(), sorted(opened.getnames()))
            for member in opened:
                self.assertEqual((member.mtime, member.uid, member.gid), (0, 0, 0))
        repacked = pack(first, self.root / "third.recipe.tar.gz")
        self.assertEqual(first.read_bytes(), repacked.read_bytes())

    def test_manifest_rewrite_preserves_unknown_toml_fields_and_prose(self):
        source = self.recipe(extra='\n[metadata]\nemoji = "😀"\nday = 2026-10-28\nvalues = [1, true, "x"]\n')
        archive = pack(source, self.root)
        extracted = unpack(archive, self.root / "extracted")
        recipe = load_recipe(extracted)
        self.assertEqual(recipe.manifest["metadata"]["emoji"], "😀")
        self.assertEqual(recipe.manifest["metadata"]["values"], [1, True, "x"])
        self.assertEqual(str(recipe.manifest["metadata"]["day"]), "2026-10-28")
        text = (extracted / "RECIPE.md").read_text()
        self.assertIn("Human description retained.", text)
        self.assertIn("Trailing human guidance.", text)

    def test_lock_covers_every_file_and_package(self):
        self.recipe("dep")
        source = self.recipe("app", '[dependencies.dep]\nsource = "../dep"\n')
        files = self.contents(pack(source, self.root))
        lock = tomllib.loads(files["LOCK.md"].decode().split("```toml\n", 1)[1].split("```", 1)[0])
        self.assertEqual(set(lock["files"]), set(files) - {"LOCK.md"})
        self.assertEqual({p["path"] for p in lock["packages"]}, {".", ".deps/dep"})
        for name, digest in lock["files"].items():
            self.assertEqual(digest, hashlib.sha256(files[name]).hexdigest())

    def test_integrity_failure_writes_nothing(self):
        files = self.contents(pack(self.recipe(), self.root))
        files["BUILD_PROMPT.md"] = b"changed\n"
        corrupt = self.archive("corrupt", [(name, value, tarfile.REGTYPE) for name, value in files.items()])
        target = self.root / "not-created"
        with self.assertRaisesRegex(RecipeError, "integrity mismatch"):
            unpack(corrupt, target)
        self.assertFalse(target.exists())
        target.mkdir()
        with self.assertRaises(RecipeError):
            unpack(corrupt, target)
        self.assertEqual(list(target.iterdir()), [])

    def test_malicious_archives_are_rejected_before_writing(self):
        cases = [
            [("../escape.md", b"x", tarfile.REGTYPE)],
            [("/absolute.md", b"x", tarfile.REGTYPE)],
            [("C:/windows.md", b"x", tarfile.REGTYPE)],
            [("back\\slash.md", b"x", tarfile.REGTYPE)],
            [("link.md", b"", tarfile.SYMTYPE)],
            [("hard.md", b"", tarfile.LNKTYPE)],
            [("pipe.md", b"", tarfile.FIFOTYPE)],
            [("twice.md", b"1", tarfile.REGTYPE), ("twice.md", b"2", tarfile.REGTYPE)],
            [("program.py", b"print('bad')", tarfile.REGTYPE)],
            [("invalid.md", b"\xff", tarfile.REGTYPE)],
            [("nul.md", b"a\0b", tarfile.REGTYPE)],
            [("file.md", b"x", tarfile.REGTYPE), ("file.md/child.md", b"x", tarfile.REGTYPE)],
        ]
        for number, entries in enumerate(cases):
            with self.subTest(number=number):
                archive = self.archive(f"bad-{number}", entries)
                target = self.root / f"bad-target-{number}"
                with self.assertRaises(RecipeError):
                    unpack(archive, target)
                self.assertFalse(target.exists())

    def test_directory_payload_rejects_links_and_non_markdown(self):
        source = self.recipe()
        code = source / "main.py"
        code.write_text("print('never run')")
        with self.assertRaisesRegex(RecipeError, "Markdown"):
            check(source)
        code.unlink()
        link = source / "linked.md"
        link.symlink_to(source / "BUILD_PROMPT.md")
        with self.assertRaisesRegex(RecipeError, "links"):
            check(source)
        link.unlink()
        import os
        os.link(source / "BUILD_PROMPT.md", link)
        with self.assertRaisesRegex(RecipeError, "hard-linked"):
            check(source)

    def test_git_metadata_is_ignored_but_other_hidden_payload_is_checked(self):
        source = self.recipe()
        git = source / ".git"
        git.mkdir()
        (git / "index").write_bytes(b"\0binary")
        self.assertEqual(check(source).name, "example")
        (source / ".env").write_text("SECRET=not-an-allowed-payload")
        with self.assertRaises(RecipeError):
            check(source)

    def test_missing_and_cyclic_dependencies_fail_explicitly(self):
        source = self.recipe("app", '[dependencies.missing]\nsource = "../missing"\n')
        with self.assertRaisesRegex(RecipeError, "does not exist"):
            context_text(source)
        (self.root / "missing").mkdir()
        with self.assertRaisesRegex(RecipeError, "RECIPE.md"):
            check(source)
        (self.root / "missing").rmdir()
        self.recipe("missing", '[dependencies.app]\nsource = "../app"\n')
        with self.assertRaisesRegex(RecipeError, "dependency cycle"):
            pack(source, self.root / "cycle.recipe.tar.gz")

    def test_check_and_context_never_fetch_remote_dependencies(self):
        source = self.recipe("remote", '[dependencies.dep]\nsource = "https://example.org/dep.recipe.tar.gz"\n')
        with mock.patch("recipkg.package.download_archive") as download:
            for operation in (check, context_text):
                with self.assertRaisesRegex(RecipeError, "never use the network"):
                    operation(source)
            download.assert_not_called()

    def test_pack_downloads_and_vendors_an_explicit_archive_dependency(self):
        dependency = pack(self.recipe("dependency", marker="REMOTE-REQUIREMENT\n"), self.root)
        source = self.recipe("remote", '[dependencies.dep]\nsource = "https://example.org/dep.recipe.tar.gz"\n')
        with mock.patch("recipkg.package.download_archive", return_value=dependency.read_bytes()) as download:
            result = pack(source, self.root)
            download.assert_called_once()
        self.assertIn("REMOTE-REQUIREMENT", context_text(result))

    def test_git_source_requires_pin_and_preserves_pin_in_lock(self):
        dependency = self.recipe("dependency")
        revision = "a" * 40
        source = self.recipe("remote", '[dependencies.dep]\ngit = "https://example.org/repo.git"\n'
                             f'rev = "{revision}"\nsubdir = "recipes/dep"\n')
        def acquire(url, rev, subdir, destination):
            target = destination / subdir
            shutil.copytree(dependency, target)
            return target

        with mock.patch("recipkg.package.checkout_git", side_effect=acquire) as checkout:
            with self.assertRaisesRegex(RecipeError, "never use the network"):
                context_text(source)
            checkout.assert_not_called()
            result = pack(source, self.root)
            checkout.assert_called_once()
        text = self.contents(result)["LOCK.md"].decode()
        self.assertIn(revision, text)
        self.assertIn("https://example.org/repo.git", text)
        repacked = pack(result, self.root / "repacked.recipe.tar.gz")
        self.assertEqual(result.read_bytes(), repacked.read_bytes())

    def test_git_relative_dependencies_stay_within_checkout(self):
        private = self.recipe("private", marker="PRIVATE-LOCAL-RECIPE\n")
        dependency = self.recipe("git-package", '[dependencies.other]\nsource = "../shared"\n')
        source = self.recipe("remote", '[dependencies.dep]\ngit = "https://example.org/repo.git"\n'
                             f'rev = "{"b" * 40}"\nsubdir = "packages/app"\n')

        def acquire_safe(url, rev, subdir, destination):
            target = destination / subdir
            shutil.copytree(dependency, target)
            shutil.copytree(private, destination / "packages/shared")
            return target

        with mock.patch("recipkg.package.checkout_git", side_effect=acquire_safe):
            result = pack(source, self.root / "safe.recipe.tar.gz")
        self.assertIn("PRIVATE-LOCAL-RECIPE", context_text(result))

        def acquire_escaping(url, rev, subdir, destination):
            target = destination / subdir
            shutil.copytree(dependency, target)
            manifest = target / "RECIPE.md"
            manifest.write_text(manifest.read_text().replace("../shared", os.path.relpath(private, target)))
            return target

        with mock.patch("recipkg.package.checkout_git", side_effect=acquire_escaping):
            with self.assertRaisesRegex(RecipeError, "escapes its checkout"):
                pack(source, self.root / "unsafe.recipe.tar.gz")
        self.assertFalse((self.root / "unsafe.recipe.tar.gz").exists())

    def test_pack_output_cannot_contaminate_any_source_recipe(self):
        dependency = self.recipe("dep")
        source = self.recipe("app", '[dependencies.dep]\nsource = "../dep"\n')
        for directory in (source, dependency):
            with self.subTest(directory=directory):
                with self.assertRaisesRegex(RecipeError, "outside every source"):
                    pack(source, directory)
                self.assertEqual(check(directory).kind, "software")

    def test_skill_entry_metadata_is_required_and_matches_package_name(self):
        source = self.recipe("skill-package")
        manifest = source / "RECIPE.md"
        manifest.write_text(manifest.read_text().replace('kind = "software"', 'kind = "skill"')
                            .replace('entry = "BUILD_PROMPT.md"', 'entry = "SKILL.md"'))
        skill = source / "SKILL.md"
        skill.write_text("# Missing metadata\n")
        with self.assertRaisesRegex(RecipeError, "frontmatter"):
            check(source)
        skill.write_text("---\nname: other-name\ndescription: A useful skill.\n---\n# Instructions\n")
        with self.assertRaisesRegex(RecipeError, "match package.name"):
            check(source)
        skill.write_text("---\nname: skill-package\ndescription: A useful skill.\n---\n# Instructions\n")
        self.assertEqual(check(source).kind, "skill")

    def test_portable_paths_and_slugs(self):
        source = self.recipe("double--dash")
        with self.assertRaisesRegex(RecipeError, "slug"):
            check(source)
        for number, names in enumerate((
            ["nested/file:stream.md"], ["NUL.md"], ["A.md", "a.md"],
            ["Upper/one.md", "upper/two.md"],
        )):
            archive = self.archive(f"portable-{number}", [(name, b"x", tarfile.REGTYPE) for name in names])
            with self.assertRaises(RecipeError):
                unpack(archive, self.root / f"portable-target-{number}")

    def test_archive_requires_lock_and_cannot_escape_to_local_dependencies(self):
        source = self.recipe()
        entries = [(item.name, item.read_bytes(), tarfile.REGTYPE) for item in source.iterdir()]
        raw = self.archive("unlocked", entries)
        with self.assertRaisesRegex(RecipeError, "LOCK.md"):
            check(raw)

    def test_refuses_existing_output_and_nonempty_extraction(self):
        source = self.recipe()
        archive = pack(source, self.root)
        before = archive.read_bytes()
        with self.assertRaisesRegex(RecipeError, "overwrite"):
            pack(source, archive)
        self.assertEqual(archive.read_bytes(), before)
        destination = self.root / "occupied"
        destination.mkdir()
        important = destination / "personal.txt"
        important.write_text("keep me")
        with self.assertRaisesRegex(RecipeError, "non-empty"):
            unpack(archive, destination)
        self.assertEqual(important.read_text(), "keep me")
        empty = self.root / "empty"
        empty.mkdir()
        self.assertEqual(unpack(archive, empty), empty)

    def test_directory_entries_are_accepted(self):
        files = self.contents(pack(self.recipe(), self.root))
        entries = [("ordinary/", b"", tarfile.DIRTYPE)]
        entries.extend((name, value, tarfile.REGTYPE) for name, value in files.items())
        archive = self.archive("directories", entries)
        self.assertEqual(check(archive).name, "example")

    def test_file_size_and_dependency_depth_limits(self):
        source = self.recipe()
        (source / "large.md").write_text("x" * 8192)
        with mock.patch("recipkg.package.MAX_FILE_BYTES", 4096):
            with self.assertRaisesRegex(RecipeError, "size limit"):
                check(source)
        (source / "large.md").unlink()
        dependent = self.recipe("parent", '[dependencies.dep]\nsource = "../example"\n')
        with mock.patch("recipkg.package.MAX_DEPENDENCY_DEPTH", 1):
            with self.assertRaisesRegex(RecipeError, "depth limit"):
                check(dependent)

    def test_invalid_semver_and_multiple_manifest_blocks(self):
        source = self.recipe()
        recipe_path = source / "RECIPE.md"
        original = recipe_path.read_text()
        recipe_path.write_text(original.replace('version = "1.0.0"', 'version = "1.0"'))
        with self.assertRaisesRegex(RecipeError, "semantic version"):
            check(source)
        recipe_path.write_text(original + '\n```toml\nextra = true\n```\n')
        with self.assertRaisesRegex(RecipeError, "exactly one"):
            check(source)


if __name__ == "__main__":
    unittest.main()
