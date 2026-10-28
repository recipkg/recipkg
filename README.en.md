# Recipkg

<img src="assets/recipkg-mark.svg" width="96" alt="Recipkg logo">

**Give the agent a recipe for the software.** Recipkg manages software reconstruction prompts, recursive dependencies, and Agent Skills. Recipe packages contain UTF-8 Markdown files only.

[中文](README.md) · [Format specification](docs/SPEC.en.md) · [Project philosophy](docs/PHILOSOPHY.md)

The project's vision is to preserve enough intent for future AI systems to reconstruct software. The current CLI has a narrower, explicit role: its five primary actions render standardized prompts. It does not call a model, execute generated software, or guarantee reconstruction from an incomplete description.

## Install

Python 3.11 or newer is required. The runtime uses the Python standard library; Git dependencies require the system Git executable.

Clone with `git clone https://github.com/recipkg/recipkg.git`. Recipes, specifications, and public skills are the primary input; the replaceable CLI source lives in `generated/`.

From this checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install ./generated
recipkg --help
```

For a user-global command, run `uv tool install ./generated`. You can also install a distributed wheel. These instructions do not assume that the project has been published to a public package registry.

## Try the recursive example

The example contains three Markdown-only recipes: `hello` depends on `greeting`, which depends on `text-rules`.

```sh
recipkg check examples/hello
recipkg pack examples/hello -o hello-0.1.0.recipe.tar.gz
recipkg build hello-0.1.0.recipe.tar.gz --output hello-build.md
```

Give `hello-build.md` to your chosen agent. The prompt includes the root recipe and the full recursive dependency material, then asks the agent to implement and verify the software in a separate output directory. `--output` refuses to overwrite an existing file.

## Reconstruct Recipkg itself

`recipes/recipkg/` describes this tool, including its CLI contract, package format, acceptance criteria, English/Chinese templates, and three bundled skills.

```sh
recipkg pack recipes/recipkg -o recipkg-0.1.0.recipe.tar.gz
recipkg build recipkg-0.1.0.recipe.tar.gz --output recipkg-build.md
```

Give the resulting prompt to an agent to request a new implementation. This repository's first reference CLI uses Python; the recipe permits other implementation languages. A reconstruction still needs to pass actual acceptance checks.

## Five prompt actions

| Command | Task described by the generated prompt |
| --- | --- |
| `recipkg extract <software>` | Inspect existing software and write a complete recipe |
| `recipkg build <package>` | Implement and verify software from a recipe and its dependencies |
| `recipkg rewrite <package> --request "requirements"` | Update the recipe, then generate a fresh implementation |
| `recipkg add <package> <source> --alias <name>` | Verify and integrate a dependency into the recipe |
| `recipkg discover <package>` | Identify dependencies, missing specifications, and external requirements |

All five accept `--request`, `--output` / `-o`, and `--template`. By default stdout contains only the prompt; diagnostics go to stderr. `add` does not modify the manifest, and `extract` does not fetch or inspect the target itself.

Except for `extract`, targets can be local recipe directories, archives, or installed `name@version` references. An unversioned name is accepted only when exactly one version is installed. Use `pack` or `install` first when dependencies need fetching.

Prompts carry a `recipkg-prompt/1` marker and an action name. Custom Markdown templates accept `{{target}}`, `{{request}}`, `{{source}}`, `{{alias}}`, and `{{context}}`. Package action templates must include `{{context}}` to preserve the dependency material.

## Recipe format

`recipkg init my-app --name my-app` creates `RECIPE.md`, `BUILD_PROMPT.md`, `ACCEPTANCE.md`, and `AGENTS.md`. The manifest is the single TOML code fence inside `RECIPE.md`:

```toml
format = "recipkg/1"

[package]
name = "my-app"
version = "0.1.0"
kind = "software"
description = "The software's purpose and observable behavior"
entry = "BUILD_PROMPT.md"

[dependencies.greeting]
source = "../greeting"
```

Describe behavior, interfaces, constraints, and environment requirements in the entry document. Define observable acceptance criteria in `ACCEPTANCE.md`. A generated scaffold still needs substantive specifications before it can support reconstruction.

Dependencies may use relative paths, HTTPS recipe archives, or Git repositories pinned to full 40-character commit hashes. A Git `subdir` selects a recipe directory. A source-only repository or ordinary prompt document must first be converted into a Recipkg recipe. A dependency does not need to be a Git submodule: `recipkg pack` collects its recursive Markdown content from the pinned source and records it in the lock file. The root build prompt must still state each dependency alias's role, scope, and acceptance contract. See the [format specification](docs/SPEC.md).

For example, a recipe in the same workspace can depend on the shared quality recipe:

```toml
[dependencies.quality]
source = "../software-quality"
```

For an independent repository, use `git`, a reviewed full commit hash in `rev`, and `subdir`. Then describe in the root `BUILD_PROMPT.md` where the `quality` contract applies and how to verify it. `recipkg pack` vendors the dependency under `.deps/quality/`, so consumers receive the full Markdown context. Use a Git submodule only when developers need both repositories checked out together.

## Search for recipes

GitHub repositories publishing Recipkg recipes must have the `recipkg` topic. Preserve other topics when adding it:

```sh
gh repo edit owner/repo --add-topic recipkg
recipkg search
recipkg search "quality" --limit 10
recipkg search "quality" --json
```

`search` explicitly queries public GitHub repositories using `topic:recipkg`. Optional `GH_TOKEN` or `GITHUB_TOKEN` authentication can increase the request allowance. Keywords are literal text; `--limit` accepts 1–100, default 20. JSON output is an array containing `repository`, `url`, `description`, and `default_branch`; diagnostics and incomplete-result warnings go to stderr. A topic is neither package validation nor an endorsement: inspect the actual `RECIPE.md`, recipe subdirectory, license, and version before pinning a reviewed full commit. Search does not download implementations, install recipes, or execute content. Empty results succeed; network failures are explicit errors.

## Languages

All five prompt actions default to English; use `--lang zh-CN` for Simplified Chinese or `--lang en` explicitly:

```sh
recipkg build recipes/recipkg --lang en
recipkg build recipes/recipkg --lang zh-CN
```

Language selection changes the task template only. Root and dependency recipes, user requirements, and custom templates remain verbatim; locked materials are never automatically translated. CLI help, diagnostics, and protocol identifiers use English. Public skills provide English entry points and Chinese translations. Read the [English specification](docs/SPEC.en.md) for the package contract.

## Package operations

```sh
recipkg init my-app --name my-app
recipkg check my-app
recipkg pack my-app -o my-app-0.1.0.recipe.tar.gz
recipkg unpack my-app-0.1.0.recipe.tar.gz unpacked-app
recipkg install my-app-0.1.0.recipe.tar.gz
recipkg list
recipkg build my-app@0.1.0 --output my-app-build.md
recipkg remove my-app@0.1.0
```

`pack` recursively copies dependencies under `.deps/<alias>/`, rewrites their sources to archive-local paths, and generates a root `LOCK.md` containing SHA-256 file digests and source records. The archive no longer depends on the original local directories. Missing dependencies, cycles, invalid files, and integrity mismatches produce errors rather than silently incomplete context.

The default store is `$XDG_DATA_HOME/recipkg`, falling back to `~/.local/share/recipkg`. Override it with `RECIPKG_HOME` or a global `--home <directory>` before the subcommand, for example `recipkg --home ./store list`. Installation stores and validates recipes without executing their instructions.

## Skills

Three public skills ship with the CLI, with English entry points and `SKILL.zh-CN.md` translations:

| Skill | Purpose |
| --- | --- |
| `migrate-to-recipkg` | Observe software and extract a complete recursive recipe |
| `rewrite-to-recipkg` | Observe, specify, establish a recipe repository, rebuild, and verify |
| `test-feedback` | Run target-user end-to-end tasks and synthesize requirements from real tests and related issues |

Development skills for building packages, managing Git repositories, and updating Recipkg are project-level tools under `.agents/skills/` and are not shipped by the CLI.

```sh
recipkg skills list
recipkg skills sync --dest /path/to/your-agent/skills
```

Synchronization includes built-in skills, installed skill packages, and skills embedded in installed packages as `skills/<name>/SKILL.md`. Choose a directory supported by your agent. Only managed files are synchronized; repeated runs are idempotent, and local edits or conflicting files are not overwritten.

Create a skill recipe with `recipkg init my-skill --name my-skill --kind skill`. Its manifest uses `kind = "skill"` and `entry = "SKILL.md"`. Standard YAML `name` and `description` frontmatter remains in `SKILL.md`; TOML configures the package, not the skill format.

## What “zero code” means

Every archive payload file is UTF-8 Markdown with a `.md` suffix. Recipe packages do not carry implementation source files, binaries, filesystem links, or executable hooks. The manager and generated software can contain code. The package protocol is independent of their implementation language or model provider.

Markdown may contain declarative configuration, interface descriptions, and input/output examples. File validation cannot prove that arbitrary natural-language content is sufficient for reconstruction, or that code has not been disguised as prose.

## Development

```sh
RECIPKG_RECIPE_ROOT="$PWD" PYTHONPATH=generated/src python3 -m unittest discover -s generated/tests -v
```

Read [AGENTS.md](AGENTS.md) before contributing. Keep the format specification, examples, and observable CLI behavior aligned.

## License

[MIT](LICENSE). Copyright © 2026 LIghtJUNction.
