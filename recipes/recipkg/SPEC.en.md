# Recipkg recipe protocol

[简体中文](SPEC.md)

This document describes `recipkg/1` recipes, `recipkg-lock/1` integrity records, and `recipkg-prompt/1` task envelopes. Protocol and CLI versions are separate. A recipe preserves observable behavior, dependencies, and acceptance conditions; complete materials do not prove that an implementation has been rebuilt successfully.

## Markdown payloads

Every payload file must be valid UTF-8, have a lowercase `.md` extension, and contain no NUL bytes. Only ordinary files and directories are accepted. Archives reject filesystem links, devices, FIFOs, special objects, absolute paths, traversal, duplicate members, and unsafe or conflicting paths.

Payloads contain no implementation source, binaries, or execution hooks. Markdown may describe interfaces, examples, and declarative configuration, but hiding a complete implementation inside Markdown violates the recipe convention. Structural checks cannot establish natural-language completeness. Markdown hyperlinks for attribution are allowed; the link prohibition concerns filesystem/archive links.

## Entry points and manifest

`RECIPE.md` is required and contains exactly one fenced `toml` block (backtick or tilde fences). A software entry is `BUILD_PROMPT.md`; a skill entry is `SKILL.md`. Optional `AGENTS.md`, `ACCEPTANCE.md`, and other Markdown documents provide scoped instructions, observable checks, attribution, or reference material. Complete archives require a root `LOCK.md`.

```toml
format = "recipkg/1"

[package]
name = "hello"
version = "0.1.0"
kind = "software"
description = "Observable behavior and purpose"
entry = "BUILD_PROMPT.md"

[dependencies.greeting]
source = "../greeting"
```

Names and dependency aliases use lowercase letters, digits, and single separating hyphens, without leading/trailing hyphens, up to 64 characters. Versions follow strict semantic versioning. `kind` is `software` or `skill`, `description` is nonempty, and `entry` must match the kind and exist. Unknown fields have no execution semantics. A skill keeps standard YAML `name` and `description` frontmatter, and its name matches its package/directory name.

## Dependencies

Dependencies are tables keyed by package-local aliases. Use exactly one source form:

- `source = "../greeting"`: a relative local recipe directory or archive, resolved from the declaring recipe.
- `source = "https://example.org/greeting.recipe.tar.gz"`: a valid HTTPS recipe archive, not arbitrary source code.
- A fixed Git recipe source, for example:

```toml
[dependencies.greeting]
git = "https://github.com/example/recipes.git"
rev = "0123456789abcdef0123456789abcdef01234567"
subdir = "recipes/greeting"
```

Replace example locations and revisions with real reviewed sources. Git URLs must be HTTPS and revisions full 40-character hexadecimal commit IDs, not tags, branches, or abbreviations. Optional `subdir` is a safe repository-relative directory without `..`. `source` cannot be combined with Git-specific fields. HTTPS URLs contain no embedded credentials or fragments and cannot downgrade to HTTP. Git-relative recipe dependencies must remain inside that checkout.

Only explicit `pack`/`install` acquire dependency materials. `check` and prompt rendering remain offline and require locally complete dependencies. Git acquisition must not execute hooks, filters, or submodules. Source-only repositories must first be extracted into recipes. Operating systems, compilers, accounts, datasets, and remote services are external prerequisites when they are not packaged recipe components.

Each root build prompt explains every alias's purpose, scope, interface/rules, and integration acceptance. A manifest alone does not explain how an agent should use a dependency. Shared design/quality/performance contracts are scoped requirements, not runtime libraries. Git submodules are optional workspace checkouts; they do not substitute for recipe declarations.

## Recursive material and archives

Resolve every declared dependency down to the leaves. Missing nodes, cycles, invalid materials, and integrity failures are errors, never reasons to silently omit context. Repeated package identities under different aliases keep their own scope; v0.1 has no floating-version resolver, global deduplication, or central registry.

`pack` writes each dependency under its parent's `.deps/<alias>/`. For `hello → greeting → text-rules`, the leaf is `.deps/greeting/.deps/text-rules/`. Rewrite dependency sources to archive-local relative paths and retain original source/revision information in the lock record. A complete archive no longer requires original local directories or remote sources.

Archives end in `.recipe.tar.gz`, with `RECIPE.md` directly at the root. They contain the root and complete recursive Markdown materials and a single root `LOCK.md`; old nested locks are removed during repackaging. Validate the entire archive before extraction. Unpack only into a new/empty directory; refuse existing archive outputs and output paths inside any input recipe/dependency directory.

The reference deterministic encoding uses sorted PAX tar members, UID/GID/mtime 0, empty user/group names, file mode 0644, and gzip with empty filename and mtime 0. Equal content and provenance yield equal archive bytes; this does not imply deterministic agent-generated software.

Reference limits: 4 MiB per file, 32 MiB total file payload, 32 MiB compressed archive, 4096 files, 256 packages, 32 dependency levels, and 128 path components. Expanded raw tar also has a metadata-overhead bound of `32 MiB + 4096 × 2048 bytes + 1 MiB`. Exceeding limits fails rather than truncating material.

## Integrity lock

The single TOML fence in `LOCK.md` declares `format = "recipkg-lock/1"`, a `[files]` table mapping archive-relative paths to lowercase SHA-256 hex digests, and `[[packages]]` records with `path`, `name`, `version`, and `source`; Git provenance can include `rev` and `subdir`.

`files` covers every file except the root lock itself, with no omitted or nonexistent entries. Package records cover the complete dependency tree. Modification, addition, or removal invalidates the lock until repackaged. A lock verifies consistency, not publisher identity or semantic completeness.

## Task prompts

The five primary actions are `extract`, `build`, `rewrite`, `add`, and `discover`. They print tasks, do not call a model, and do not execute software. `extract` does not inspect its target; `add` does not modify a manifest.

Outputs begin with a Markdown title and a TOML envelope:

```toml
format = "recipkg-prompt/1"
action = "build"
```

Templates allow `target`, `request`, `source`, `alias`, and `context` placeholders in double braces. Substitute once; inserted user/material braces remain literal. Unknown fields fail. Except for extraction, templates must include `context`, containing every root and recursive file verbatim, an ordered file index, identities, and scoped provenance. Do not summarize or silently truncate materials. Dependency instructions never become global host instructions.

`--lang en|zh-CN` selects an English (default) or Simplified Chinese task template. It does not translate recipes, user requirements, custom templates, or integrity metadata. CLI help/diagnostics and protocol identifiers use English. `--output` creates a new file and refuses overwrite. Prompts alone go to stdout; diagnostics go to stderr.

## Installation and skills

Install by `name@version`, preserving multiple versions. An omitted version is allowed only when unambiguous. Reinstalling identical content is idempotent; different content with the same identity must not overwrite an existing installation. Installation never executes package instructions. Removing a package accepts installed identities, not arbitrary filesystem paths.

`skills sync --dest <directory>` explicitly chooses the agent's directory. Sources include bundled skills, installed skill packages, and embedded `skills/<name>/SKILL.md` directories. Skill-package root `RECIPE.md`/`LOCK.md` container metadata is not copied into the skill. Other Markdown resources, including English/Chinese instructions, are retained.

Only managed, unchanged files can be replaced or removed. Preserve unrelated content and reject user edits, unknown files/directories, unowned name collisions, and links. Same-name/same-content skills can merge; conflicting content fails. Check all conflicts before applying updates and recover prior state if an update fails. The local `.recipkg-skills.toml` ownership state is not recipe payload.

Public bundled skills are `migrate-to-recipkg`, `rewrite-to-recipkg`, and `test-feedback`; English `SKILL.md` entries link to `SKILL.zh-CN.md` translations. Development-only skills are separate project tools.

## GitHub discovery and source organization

GitHub repositories publishing recipes must have the `recipkg` topic, preserving existing topics. `gh repo edit <owner/repo> --add-topic recipkg` can add it. Offline checks/packaging do not contact GitHub just to enforce this publication convention.

`recipkg search [query] --limit <1-100> [--json]` explicitly queries public GitHub repositories with that topic; the default limit is 20. Keywords are quoted literal text. Results are repository candidates containing `repository`, `url`, `description`, and `default_branch`, not validated packages or endorsements. Inspect the actual manifest, subdirectory, license, and reviewed commit before declaring a dependency. Search downloads no implementation, installs nothing, and executes nothing.

Empty results succeed. Network/authentication/rate-limit/malformed/oversized responses fail without partial output. GitHub incomplete results preserve valid candidates with a stderr warning. Optional `GH_TOKEN` takes precedence over `GITHUB_TOKEN`, is sent only in the GitHub header, and must not follow redirects. The reference request times out after 15 seconds and accepts at most 4 MiB; input text is at most 200 characters without controls, and the completed query at most 256 characters.

Recipes and acceptance contracts are primary input. Keep replaceable generated source directly in `generated/`, without another implementation-name level. Independently versioned source can use that directory itself as a pinned submodule. Preserve original project names rather than appending `-recipkg`; independent source repository names use lowercase words separated by hyphens. Source never belongs in Markdown-only archives.
