# Acceptance criteria for magpie-context-folding 0.5.0

These are reconstruction requirements. Run checks against the rebuilt implementation in an isolated environment and record commands, environment, outputs and result. Existing source-repository test records below are evidence about that source snapshot only; they do not count as tests of a reconstruction.

## 1. Annotation parsing and projection

- A valid whole-line begin/end pair in assistant text is preserved on first observation with the default one-request delay, then becomes a reversible `[[cf:v2:<hash>]]` reference at the next progressing request boundary when all eligibility and savings checks pass.
- An identical retry does not advance the delay. `delay_requests = 0` allows immediate projection after a complete marked region is observed.
- Correctly nested ranges produce parent/child archive structure. Unmarked text, conclusions outside ranges, orphan ends, unclosed ranges, crossing/malformed pairs and mismatched labels follow the stated preservation rules; no uncertain text disappears.
- Pairing across assistant ordinary-text messages preserves message structure and does not consume tool calls/results. A new user message prevents an unfinished assistant range from crossing the boundary.
- Tool arguments/results, images and signed reasoning fields remain unchanged. Source reads that cannot be verified as one supported text source remain unchanged. Test Python and JavaScript/TypeScript strings/templates that resemble annotations to ensure conservative filtering retains ambiguous input.
- A repeated identical body at a new occurrence receives its own delay. A changed body yields a distinct content identity. Prefix collisions are reported or disambiguated, never silently misread.

## 2. Durability, scope and recovery

- Force archive-write, capacity, state-conflict, missing-shell and request-savings failures. In every case the outgoing request retains the original text and no dangling reference is emitted.
- Recover a folded body through the Magpie CLI with the same archive directory and scope supplied to the request. Verify byte-exact UTF-8 restoration, including CRLF, Unicode and the protocol's final-newline handling.
- Ordinary bounded `read` returns the current layer, reports usable paging metadata, leaves folding state unchanged and does not expose more than its documented limit. Follow `nextOffset` using UTF-16 code units in the Magpie CLI and Unicode code points in `ctxf`; test that the two offset conventions are not conflated.
- `read --restore` returns the complete exact original and persistently protects the selected nested subtree and ancestors. Reject incompatible partial range/offset/limit options rather than claiming a full restore.
- `list`, `meta` and `grep` locate nested archive content without implicitly restoring it. `paste` refuses an existing destination. `forget` does not delete data that remains referenced. Archived instructions are returned as inert text and are never executed.
- Two independent session scopes cannot read one another's archive references. The Python archive and Magpie archive do not interoperate.

## 3. Host request integration and guidance

- For every supported host protocol, guidance is inserted in the true system-instruction field, preserving existing host content, tools, model/stream settings and tool choice. Repeated projection replaces the plugin's own guidance instead of accumulating copies, including after host merge/CRLF normalization.
- When a reference is present, recovery guidance identifies a usable CLI command, state directory and current scope. Without a callable authorized shell tool, the hook leaves the request unchanged.
- Unsupported or ambiguous instruction-field shapes fail closed without damaging the input.
- Verify the plugin through the target Magpie hook runtime as well as unit-level tests. A mocked hook test alone is not host integration evidence.

## 4. Standalone `ctxf`

- `cat text | ctxf` and `ctxf fold` output exactly the transformed text on stdout and no status wrapper or extra newline; diagnostics are on stderr. JSON mode returns the documented text and reference metadata.
- Explicit folding is immediate and independent of request delay settings. Invalid, incomplete or unmarked ranges are retained according to the parser contract.
- Querying the generated Python archive returns the expected view and original data using the same `--state`/`CTXF_STATE` and scope. For an archived body longer than 1200 code points, ordinary `ctxf read HASH` and `ctxf read HASH --raw` return the same bounded current-layer text and report `nextOffset=1200` on stderr; `read --json` exposes the structured paging fields. Follow explicit pages to recover the complete view; do not silently treat `--raw` as a full original export. Verify Unicode-code-point paging separately from Magpie's UTF-16 paging. See `COVERAGE.md` for the pinned README conflict.
- Confirm the standalone Python command cannot accidentally read or overwrite the Magpie backend's archive.

## 5. Configuration, migration and packaging

- Test default/global/project/plugin-option precedence and project search termination at the Git root. Confirm the documented 64 MiB capacity default and 256 estimated-token savings default; a zero delay enables immediate consideration.
- Old unsupported configuration produces an actionable migration error and is not silently mapped. Legacy archive reads required by the documented compatibility contract remain possible without reviving retired automation or MCP.
- Install the npm package and Python package in clean locations. Verify the CLI executable, plugin hook resource, docs and licenses are present and no install hook is needed to generate runtime code. Test the minimum versions actually claimed in package metadata.
- Verify paste does not overwrite, invalid paths fail safely, and a failed build or archive operation leaves no partial output presented as valid.

## 6. Evidence already recorded for the source snapshot

The source's 2026-10-28 README and validation documents describe the intended 0.5.0 behavior. They record historical local test results and selected CI/container/host smoke runs for their respective commits. The final source commit inspected for this recipe is `b0837a72d62a88bfff301de5dbd76b276d24eca1`; some evidence documents explicitly describe earlier commits and must not be relabeled as tests of that final commit.

Earlier session records report that the final source's local `npm run check` passed 254 tests, `test:controller` passed 13 tests, and `test:harbor` passed 34 tests. A local isolated CLI-hook smoke restored a 60-line Unicode body exactly and checked scope isolation. These are reported source-validation results, not reruns performed while writing this recipe. They do not prove installation of npm 0.5.0 or successful activation in the user's live Magpie gateway.

The source's Harbor documentation distinguishes deterministic component/Docker smoke checks from real model A/B tests. Real model quality, latency, token and billing comparisons remain unverified unless rebuilt acceptance work runs them with a specified model endpoint, dataset, environment and budget. Do not report scripted oracle checks as model capability scores.

## 7. Unknowns and reporting

Record the actual supported OS/architectures, minimum Magpie version, package installation paths, exact edge behavior where documentation is incomplete, and any differences in the reconstructed implementation. Python >=3.10 is established by the pinned package metadata; verify any claimed minimum-version runtime support separately. No benchmark budget is specified. Product UI checks are not applicable, but CLI help, errors and documentation must be readable.

Mark every acceptance item pass, fail or unverified with reproducible evidence. Structural Recipkg validation or successful prompt rendering proves only that the recipe is packaged correctly; it does not prove the software has been reconstructed or that external host integration works.
