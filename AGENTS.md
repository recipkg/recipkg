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
- Keep package operations explicit: `init`, `check`, `pack`, `unpack`, `install`, `list`, `remove`, and `skills`.
- Synchronize only managed skills; preserve user edits and refuse conflicting overwrites.

## Development

- Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
- Exercise a packaged wheel outside this checkout before release.
- Use black-box tests for observable behavior, especially archive integrity and complete dependency context.
- Keep README commands executable and the protocol in `docs/SPEC.md` aligned with actual behavior.
- Do not commit generated distributions, caches, tokens, user data, or temporary build output.
