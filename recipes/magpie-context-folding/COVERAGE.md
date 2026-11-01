# Coverage and evidence

## Snapshot and scope

Recipe source: `LIghtJUNction/magpie-context-folding` at `b0837a72d62a88bfff301de5dbd76b276d24eca1`. Plugin version: 0.5.0. Independent Python distribution: `context-folding` 0.1.0. Audit date: 2026-11-01.

The local upstream checkout contains later commits and uncommitted work. It was not modified or used as the tested snapshot. Source observations below used files exported with `git archive` from the exact pinned commit, with isolated temporary SQLite state.

## Observed requirements and conflicts

- Annotation parsing, nested snapshots, hashing, request delay, query layers, restore, host guidance and fail-closed behavior: recorded in `BUILD_PROMPT.md`, bundled `PROTOCOL.md` and `ACCEPTANCE.md`. These are reconstruction requirements, not a reconstruction pass.
- `context-folding/pyproject.toml` establishes Python >=3.10, `tomli>=2.0.1` on Python <3.11, and standalone version 0.1.0. Optional Tree-sitter prerequisites and build backend are recorded in `BUILD_PROMPT.md`. Minimum-version execution was not tested.
- The pinned standalone README says ordinary read has a JSON envelope, a 4000-character default, and raw read follows all pages. Its CLI source (`context-folding/python/context_folding/cli.py`, `main`'s `CTXF_QUERY_ACTIONS` branch) instead defaults `ctxf read` to plain text, limit 1200, and handles `--raw` in the same bounded query branch. `PROTOCOL.md` agrees with that CLI branch. Do not apply the older executable's separate `_raw_read` branch to `ctxf`.
- Isolated observation on Python 3.14.8: fold a whole-line HTML annotation containing 150 numbered lines of Unicode text (`Evidence Unicode 汉字 🐦 %04d\n`), using `ctxf fold --json`, temporary `--state` and scope `audit`; query its returned ID with `ctxf read ID`, `ctxf read ID --raw` and `ctxf read ID --json`. All exited 0. Both plain variants returned exactly 1200 code points, were equal, and reported `nextOffset=1200` on stderr. JSON returned `nextOffset: 1200` and a larger `totalChars`. This resolves this narrow conflict only; it is not full upstream regression or rebuilt-software evidence.
- Scope is a local namespace, not authentication. Archive/file/process permissions remain the host's responsibility. Separate scopes do not authorize one another's data; isolation checks must not be advertised as an authentication system.

## Dependency review

The public `recipkg/standard-library` README was retrieved on 2026-11-01. Its catalog contains no context-folding component recipe. Agent framework candidates are not required to implement this plugin; generic design recipes are not a substitute for the folding protocol. No unrelated dependency was introduced. Magpie, Python/SQLite, Node/Bun, optional parser packages and build tools remain explicitly documented external prerequisites. This is a catalog relevance check, not an audit of every listed recipe.

## Structural verification

Use the reference CLI from the Recipkg repository root, with output paths under a temporary directory:

```sh
export PYTHONPATH="$PWD/generated/cli-source/src"
work=$(mktemp -d)
python3 -m recipkg check recipes/magpie-context-folding
python3 -m recipkg pack recipes/magpie-context-folding -o "$work/magpie.recipe.tar.gz"
python3 -m recipkg check "$work/magpie.recipe.tar.gz"
python3 -m recipkg build "$work/magpie.recipe.tar.gz" --lang en --output "$work/build.en.md"
python3 -m recipkg build "$work/magpie.recipe.tar.gz" --lang zh-CN --output "$work/build.zh-CN.md"
```

Structural results are recorded in `docs/PROGRESS.md` of the containing Recipkg repository. The recipe remains Markdown-only; protocol and license are part of the complete build context.

## Not verified / remaining reconstruction work

- Independent reconstruction of either component and every rebuilt acceptance item.
- Complete Magpie host integration, real-session activation, npm 0.5.0 availability and clean npm/Python package installation.
- Full source regression at the pinned commit, all parser/concurrency/lifecycle/error branches, minimum runtime versions and supported OS/architectures.
- The source also exposes SDK bridges, JSON Lines transport, host adapters, annotation-editing and lifecycle APIs. Their complete contracts are not extracted here. This recipe covers the stated plugin and basic standalone folding/query workflows, not a complete replacement for every shipped source feature. Do not label the whole upstream project fully extracted or fully reconstructable.
- Complete standalone RPC schemas, all flag edge cases and exact host-hook schemas remain extraction gaps. A rebuilding agent must report them rather than silently invent compatibility or require external source as an undeclared build dependency.
- Historical 254/13/34 test counts in `ACCEPTANCE.md` are inherited session reports, not independently reproduced evidence from this audit.
- Model quality, tokenizer measurements, cost/latency benefit, and replacement of host compaction remain unverified.
