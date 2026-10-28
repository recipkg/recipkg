# Changelog

## Unreleased

- Added `skills project add/list/update` for complete project-owned skills pinned as Git submodules; scripts and resources remain outside Markdown recipe archives.
- Added explicit GitHub discovery with `recipkg search`; recipe repositories must carry the `recipkg` topic.
- Added public `test-feedback` and `rewrite-to-recipkg` skills with English and Simplified Chinese documentation.
- Added English prompt templates (now the default) and `--lang en|zh-CN`; recipe and custom-template bytes remain unchanged.
- Made recipes the primary repository input and pinned the separate `recipkg/cli-source` repository at `generated/cli-source/`.
- Split all eleven project skills into independent canonical repositories, referenced by pinned submodules and reused during migration.

## 0.1.0 — Initial version

- Added five prompt-only actions: `extract`, `build`, `rewrite`, `add`, and `discover`.
- Defined the `recipkg/1` recipe format: UTF-8 Markdown payloads, a TOML manifest in `RECIPE.md`, and `.recipe.tar.gz` archives.
- Added recursive dependency packaging, file integrity metadata, explicit package operations, and managed skill synchronization.
- Included five standard Agent Skills and a three-level `hello` example.
- Added a complete Markdown recipe for reconstructing Recipkg itself without its implementation source.
- Documented the difference between complete reconstruction materials and a verified software implementation.
