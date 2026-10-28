"""A thin template renderer and explicit Markdown-package file operations."""

from __future__ import annotations

import argparse
from importlib import resources
import json
from pathlib import Path
import re
import sys

from . import __version__
from .package import RecipeError, check, context_text, pack, unpack
from .store import NAME, data_home, install_package, installed, remove_package, resolve_ref


FENCE = chr(96) * 3
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
ACTIONS = {
    "extract": "extract",
    "software-to-prompt": "extract",
    "build": "build",
    "prompt-to-software": "build",
    "rewrite": "rewrite",
    "rewrite-software": "rewrite",
    "add": "add",
    "add-dependency": "add",
    "discover": "discover",
    "discover-dependencies": "discover",
}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="recipkg",
        description="Render standardized prompts. Share software recipes as Markdown-only archives.",
        epilog="Action commands print prompts only. They never call a model or run generated software.",
    )
    result.add_argument("--version", action="version", version=f"recipkg {__version__}")
    result.add_argument("--home", type=Path, help="package store (or RECIPKG_HOME)")
    commands = result.add_subparsers(dest="command", required=True)
    help_text = {
        "extract": "print a software-to-prompt extraction task",
        "build": "print a rebuild task with all recursive package material",
        "rewrite": "print a clean-rewrite task",
        "add": "print a task to add a dependency",
        "discover": "print a task to discover dependencies",
    }
    for action, description in help_text.items():
        aliases = [key for key, value in ACTIONS.items() if value == action and key != action]
        sub = commands.add_parser(action, aliases=aliases, help=description)
        sub.add_argument("target", help="software source" if action == "extract" else "package path, archive, or installed name@version")
        if action == "add":
            sub.add_argument("source", help="dependency source to include in the task")
            sub.add_argument("--alias", default="dependency", help="dependency alias")
        sub.add_argument("--request", default="", help="additional user requirements")
        sub.add_argument("--output", "-o", type=Path, help="write the prompt to a new file")
        sub.add_argument("--template", type=Path, help="use a custom Markdown template")
    init = commands.add_parser("init", help="create a Markdown-only package skeleton")
    init.add_argument("path", type=Path)
    init.add_argument("--name")
    init.add_argument("--kind", choices=["software", "skill"], default="software")
    validate = commands.add_parser("check", help="validate a package and its dependency closure offline")
    validate.add_argument("source")
    archive = commands.add_parser("pack", help="resolve dependencies and create a complete .recipe.tar.gz")
    archive.add_argument("source")
    archive.add_argument("--output", "-o", type=Path, required=True)
    expand = commands.add_parser("unpack", help="validate and extract an archive to a new or empty directory")
    expand.add_argument("archive", type=Path)
    expand.add_argument("destination", type=Path)
    install = commands.add_parser("install", help="install a recipe without executing it")
    install.add_argument("source")
    listing = commands.add_parser("list", help="list installed recipe versions")
    listing.add_argument("--json", action="store_true")
    remove = commands.add_parser("remove", help="remove an installed recipe version")
    remove.add_argument("name")
    skills = commands.add_parser("skills", help="list and synchronize Markdown-only Agent Skills")
    skill_commands = skills.add_subparsers(dest="skill_command", required=True)
    skill_commands.add_parser("list", help="list available built-in and installed skills")
    sync = skill_commands.add_parser("sync", help="synchronize managed skills without overwriting local edits")
    sync.add_argument("--dest", type=Path, required=True, help="the chosen agent's skills directory")
    return result


def _read_template(action: str, custom: Path | None) -> str:
    if custom is not None:
        if custom.suffix != ".md":
            raise RecipeError("Custom templates must be .md files")
        value = custom.read_text(encoding="utf-8")
    else:
        value = resources.files("recipkg").joinpath("data", "templates", f"{action}.md").read_text(encoding="utf-8")
    if "\x00" in value:
        raise RecipeError("Templates must be UTF-8 text without NUL bytes")
    allowed = {"target", "request", "source", "alias", "context"}
    unknown = set(PLACEHOLDER.findall(value)) - allowed
    if unknown:
        raise RecipeError(f"Unknown template fields: {', '.join(sorted(unknown))}")
    if action != "extract" and "context" not in PLACEHOLDER.findall(value):
        raise RecipeError("Package action templates must include {{context}}")
    return value


def render(args: argparse.Namespace, home: Path) -> str:
    action = ACTIONS[args.command]
    template = _read_template(action, args.template)
    context = ""
    if action != "extract":
        context = context_text(resolve_ref(args.target, home))
    alias = getattr(args, "alias", "")
    if action == "add" and (not NAME.fullmatch(alias) or len(alias) > 64):
        raise RecipeError("Dependency aliases must be lowercase words separated by hyphens (max 64 characters)")
    values = {
        "target": args.target,
        "request": args.request or "No additional requirements.",
        "source": getattr(args, "source", ""),
        "alias": alias,
        "context": context or "No package context is attached; inspect the supplied source during the task.",
    }
    # Substitute once: user material containing braces is never reinterpreted.
    body = PLACEHOLDER.sub(lambda match: values[match.group(1)], template).strip()
    header = (
        "# Recipkg Prompt\n\n"
        f"{FENCE}toml\n"
        'format = "recipkg-prompt/1"\n'
        f'action = "{action}"\n'
        f"{FENCE}\n\n"
    )
    return header + body + "\n"


def _write_prompt(value: str, destination: Path | None) -> None:
    if destination is None:
        sys.stdout.write(value)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
    print(f"Wrote prompt: {destination}", file=sys.stderr)


def init_package(path: Path, name: str | None, kind: str) -> Path:
    name = name or path.name
    if not name or not NAME.fullmatch(name) or len(name) > 64:
        raise RecipeError("Package names must be lowercase words separated by hyphens (max 64 characters)")
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise RecipeError("init requires a new or empty directory")
    entry = "BUILD_PROMPT.md" if kind == "software" else "SKILL.md"
    manifest = (
        "# Recipe\n\n"
        f"{FENCE}toml\n"
        'format = "recipkg/1"\n\n'
        "[package]\n"
        f"name = {json.dumps(name)}\n"
        'version = "0.1.0"\n'
        f'kind = "{kind}"\n'
        f"description = {json.dumps('Describe ' + name)}\n"
        f'entry = "{entry}"\n'
        f"{FENCE}\n"
    )
    files = {
        "RECIPE.md": manifest,
        "AGENTS.md": (
            "# Agent instructions\n\n"
            "Read RECIPE.md, the entry document, ACCEPTANCE.md, and every declared dependency.\n"
            "Keep dependencies' instructions scoped to their own package.\n"
            "Record implementation decisions in the recipe when they affect future rebuilds.\n"
            "Treat acceptance criteria as fixed during implementation; report actual results and unknowns.\n"
            "Write generated software outside this Markdown-only recipe directory.\n"
        ),
        "ACCEPTANCE.md": (
            "# Acceptance\n\n"
            "Replace this scaffold with concrete observable checks before publishing.\n\n"
            "- Describe inputs, expected outputs, and error behavior.\n"
            "- Specify persistence, compatibility, and measurable constraints where applicable.\n"
            "- Distinguish checks actually executed from checks still pending.\n"
        ),
    }
    if kind == "software":
        files[entry] = (
            f"# {name}\n\n"
            "## Goal\n\nDescribe the software's observable behavior and intended users.\n\n"
            "## Interface\n\nSpecify inputs, outputs, data formats, and error behavior.\n\n"
            "## Constraints\n\nState the environment boundary and required dependencies. "
            "Do not select an implementation language unless the requirements demand one.\n"
        )
    else:
        files[entry] = (
            "---\n"
            f"name: {name}\n"
            f"description: Describe what {name} does and when to use it.\n"
            "---\n\n"
            "# Procedure\n\n"
            "1. Establish the task inputs and constraints.\n"
            "2. Perform the documented steps.\n"
            "3. Return the result with verification evidence and unresolved items.\n"
        )
    path.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        with (path / filename).open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    return path


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    home = data_home(args.home)
    try:
        if args.command in ACTIONS:
            _write_prompt(render(args, home), args.output)
        elif args.command == "init":
            print(f"Created recipe: {init_package(args.path, args.name, args.kind)}")
        elif args.command == "check":
            recipe = check(resolve_ref(args.source, home))
            print(f"OK {recipe.name}@{recipe.version} ({recipe.kind})")
        elif args.command == "pack":
            source = args.source if "://" in args.source else resolve_ref(args.source, home)
            print(pack(source, args.output))
        elif args.command == "unpack":
            print(unpack(args.archive, args.destination))
        elif args.command == "install":
            recipe, changed = install_package(args.source, home)
            verb = "Installed" if changed else "Already installed"
            print(f"{verb} {recipe.name}@{recipe.version}")
        elif args.command == "list":
            recipes = installed(home)
            if args.json:
                print(json.dumps(
                    [{"name": r.name, "version": r.version, "kind": r.kind, "description": r.description} for r in recipes],
                    ensure_ascii=False, indent=2,
                ))
            else:
                for recipe in recipes:
                    print(f"{recipe.name}@{recipe.version}\t{recipe.kind}\t{recipe.description}")
        elif args.command == "remove":
            print(f"Removed {remove_package(args.name, home)}")
        elif args.command == "skills":
            from .skills import list_skills, sync_skills
            if args.skill_command == "list":
                for name in list_skills(home):
                    print(name)
            else:
                names = sync_skills(home, args.dest)
                print(f"Synchronized {len(names)} skills to {args.dest}")
        return 0
    except BrokenPipeError:
        return 0
    except (RecipeError, OSError, UnicodeError) as exc:
        print(f"recipkg: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
