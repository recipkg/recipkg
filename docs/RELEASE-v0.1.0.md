# Recipkg v0.1.0

Released: 2026-10-28.

## Included

- Five template-based actions: extract, build, rewrite, add, discover.
- Complete recursive Markdown context; no model provider or generated-language requirement.
- Recipkg/1 recipe, lock, and prompt-envelope specifications.
- Markdown-only deterministic .recipe.tar.gz archives with integrity checking.
- Explicit package initialization, validation, packaging, extraction, installation, listing, and removal.
- Five standard Agent Skills and managed synchronization that preserves user edits.
- A three-level hello example and a recipe describing Recipkg itself.

## Verification performed

- Python 3.12.14 on Linux: all 40 unittest cases passed.
- Built the wheel and installed it without runtime dependencies into a separate virtual environment.
- Invoked the installed CLI outside the repository.
- Validated and packaged both examples/hello and recipes/recipkg.
- Generated complete build prompts from both archives.
- Installed the hello archive and rendered it by its installed name and version.
- Synchronized all five bundled skills twice to verify the installed-wheel resources and idempotence.
- Tests cover moved/deleted original recipe directories, recursive material completeness, archive traversal and link rejection, content tampering, missing/cyclic dependencies, version ambiguity, and skill-edit conflicts.
- Network-source tests use mocks. They test the HTTPS/Git acquisition boundary, pinned commits, and error handling; this release record does not claim a live-network end-to-end test in the restricted build environment.

## Distribution

- recipkg-0.1.0-py3-none-any.whl: the reference CLI, requiring Python 3.11+.
- recipkg-0.1.0.recipe.tar.gz: the Markdown-only recipe for rebuilding this tool in a suitable language.
- hello-0.1.0.recipe.tar.gz: a complete three-level example.
- recipkg-rebuild.md and hello-build.md: prompts rendered by the installed CLI.
- Source snapshot and checksums are included in the release backup.

The self-description recipe was checked and rendered. A second Agent has not been tasked with independently reproducing the entire CLI as part of this release.

## Use

Install the wheel with pip or install this source repository. Run recipkg --help.
The five action commands print tasks for an Agent. They do not themselves execute the software development work described by those tasks.
