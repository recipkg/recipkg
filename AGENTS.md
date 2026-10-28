# Working on Recipkg

Recipkg is a small, language-independent prompt-package tool. Its primary action commands render Markdown prompts from templates. They never call a model or execute generated software.

## Product rules

- Keep the v0.1 CLI deterministic and small; use Python 3.11+ and the standard library at runtime.
- Keep the package format independent of the CLI implementation language, model provider, and generated software language.
- Recipe archives end in `.recipe.tar.gz`. Every payload file is UTF-8 Markdown with a `.md` suffix. No links, binaries, implementation source files, or installation hooks.
- Put the TOML package manifest in one fenced `toml` block in `RECIPE.md`. Machine-readable lock metadata also lives in Markdown.
- Preserve all recursive dependency prompts in a complete archive and in the build prompt. Fail on missing dependencies, cycles, invalid archives, or integrity mismatches; never silently omit context.
- Standard `SKILL.md` files retain YAML `name` and `description` frontmatter. Bundled project skills are not personal ChatGPT skill installations.
- The five primary actions are `extract`, `build`, `rewrite`, `add`, and `discover`. Their stdout is only the requested prompt; diagnostic output goes to stderr.
- Keep package operations explicit: `init`, `check`, `pack`, `unpack`, `install`, `list`, `remove`, `search`, and `skills`. Only explicit `search` retrieves repository discovery metadata; prompt rendering and `check` remain offline.
- GitHub repositories publishing Recipkg recipes must carry the `recipkg` topic. A topic marks a discovery candidate, not a validated package.
- Keep English and Simplified Chinese prompt templates and public skill documentation aligned. Preserve recipe bytes when selecting a prompt language.
- Every project skill has its own canonical `recipkg/<skill-name>` repository, consumed here and in migrated projects as a pinned Git submodule. Edit upstream first, then explicitly update consumer pins; never replace this with copied skill files. See `docs/SKILLS.md`.
- Synchronize only managed skills for non-Git destinations; preserve user edits and refuse conflicting overwrites.

## Development

- The canonical product lives in `recipes/recipkg/`; templates there define the product; each skill has an independent canonical GitHub repository, referenced here by a fixed submodule commit. `generated/` contains source submodules, not flat source files. The CLI implementation is the independent `recipkg/cli-source` repository, pinned at `generated/cli-source/`. Keep the project name `recipkg`; do not append `-recipkg`. Source repository names, when needed, use lowercase words separated by hyphens. Each generated source repository must occupy its own child directory as a gitlink with mode `160000`; never flatten it into the container.
- Run `RECIPKG_RECIPE_ROOT="$PWD" PYTHONPATH=generated/cli-source/src python3 -m unittest discover -s generated/cli-source/tests -v`.
- Exercise a packaged wheel outside this checkout before release.
- Use black-box tests for observable behavior, especially archive integrity and complete dependency context.
- Keep README commands executable and the protocol in `docs/SPEC.md` aligned with actual behavior.
- Do not commit generated distributions, caches, tokens, user data, or temporary build output.
