---
name: rewrite-to-recipkg
description: Observe existing software, extract its reconstruction contract, establish a Recipkg recipe repository, and rewrite the package from the complete recipe with real acceptance evidence. Use for source-to-recipe rewrites and rebuilding software under the Recipkg format.
---

# Rewrite software through a Recipkg recipe

[简体中文](SKILL.zh-CN.md)

Complete the requested path: observe → specify → establish the recipe repository → rebuild → verify. Producing a prompt or archive alone is not a completed rewrite.

## Establish the target

Read the request, project instructions, Git status, and existing recipes. Identify source/product version, public behavior to preserve, requested changes, target users/platforms, language/locales, output location, and layout. Reuse established choices; ask only about consequential gaps. Preserve unrelated work and existing implementations.

Update a valid existing recipe rather than creating competing specifications. For source-only software, use `recipkg extract <source>` as a checklist and actually inspect authorized software, documentation, tests, and interfaces. Record evidence and unknowns; do not claim unobserved behavior is preserved.

## Establish the recipe repository before implementation

Follow the selected or existing layout: a separate recipe workspace can keep a reviewed source commit as a `source/` submodule and recipes under `recipes/<name>/`; same-repository projects can retain that recipe directory beside source. Observation checkouts are not recipe dependencies. Do not create a self-submodule for Recipkg itself.

Complete `RECIPE.md`, `BUILD_PROMPT.md`, `ACCEPTANCE.md`, and scoped `AGENTS.md`. The manifest has one TOML fence with `recipkg/1`, valid identity/kind/entry, and real recursive recipe dependencies. Preserve attribution/licensing. Payloads contain UTF-8 `.md` only; implementation, binaries, logs, screenshots, and hooks belong outside them.

Specify goals, behavior, I/O, interfaces, errors/recovery, environment, design identity, localization, quality/performance constraints, and acceptance. State each dependency alias's purpose, scope, integration contract, and checks. `recipkg search [keywords]` finds candidates; inspect recipes and pin reviewed commits instead of trusting topics.

GitHub repositories publishing recipes must carry the `recipkg` topic. Preserve existing topics. When publishing is authorized, use `gh repo edit <owner/repo> --add-topic recipkg` or equivalent tooling and read back the result. For local-only work, prepare the repository and record publication as outstanding without publishing on your own.

Run `recipkg check`, `recipkg pack` outside the source directory, and `recipkg check <archive>`. Render `recipkg build <archive> --lang en` or `--lang zh-CN` and verify complete root/dependency materials. Resolve missing contracts and dependencies rather than shortening context.

## Rewrite from the contract

Use the updated complete recipe as the product input. Generate replacement software and tests in a separate implementation/output directory under the chosen language/platform constraints. Old source may explain observations but must not supply undocumented requirements or be copied into the Markdown package.

Preserve unchanged behavior. Implement leaves before integration, retain useful product identity, provide clear user paths and required English documentation. Do not replace design with generic UI templates or weaken acceptance to fit implementation.

Run declared success, failure, boundary, and integration checks. Exercise meaningful end-to-end paths for different target users; verify final data/artifacts, persistence, guidance, and recovery where applicable. Compare public behavior using comparable inputs/environments. Separate local tests, live acceptance, performance measurements, and unverified platforms. Feed new observations into candidate requirements rather than silently changing the original contract.

## Deliverable

Provide recipe repository/path, observed source version, complete archive/build prompt, runnable replacement, operating instructions, and real acceptance results. State changed behavior, compatibility, evidence gaps, and pending publication. Update changed package versions and regenerate integrity metadata by repackaging. Completion requires an existing implementation and actual requested acceptance; retain failures and blockers honestly.

## Generated source layout

Treat recipes as the primary input. Place generated implementation source under `generated/`, with no extra implementation-name directory; when independently versioned, use this directory itself as a pinned source submodule of the recipe repository. Keep observation checkouts separate. Create remotes and push only within existing publication authorization; otherwise complete local work and record its unpublished state.

Keep the original project and primary repository name; do not append `-recipkg`. Independently managed source repositories use lowercase, hyphenated names.
