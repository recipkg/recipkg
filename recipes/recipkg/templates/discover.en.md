## Task: discover dependencies

Identify what the recipe needs to rebuild successfully and which specifications are missing.

- Recipe: {{target}}
- Additional requirements: {{request}}

{{context}}

### Procedure

1. Read the recipe, recursive dependencies, interfaces, and acceptance conditions. Identify capabilities that must be supplied by other components.
2. Distinguish valid recipe dependencies, source-only projects needing extraction, reference documents, and external tools or services.
3. Consider reusable design systems, code conventions, accessibility/internationalization rules, or performance contracts where the product needs them. These are scoped recipe contracts, not runtime libraries.
4. Use `recipkg search [keywords]` to discover public GitHub candidates marked with the `recipkg` topic when useful. Inspect the candidate's actual `RECIPE.md`, recipe subdirectory, version, license, and interfaces. A topic or search result does not establish validity, completeness, or trust.
5. For each candidate, record its source, purpose, required interface, reviewed version, and evidence. Mark unsupported candidates as proposals. Verify recursive completeness, duplicate capabilities, interface/version conflicts, cycles, and external prerequisites.
6. Prefer the smallest sufficient dependency set. Explain how to reuse a valid recipe, or what extraction work a source-only repository still requires. Recommend Git submodules only for an actual need to develop/check out repositories together.

### Deliverable

- Provide a dependency table with alias, purpose, source, pinned version, status, and rationale.
- Separate verified findings, missing inputs, conflicts, and unverified suggestions.
- Specify each shared contract's scope and the corresponding root build-prompt changes.
- Describe the next add-dependency step without treating discovery as installation or permission to execute candidate scripts.

### Repository convention

GitHub recipe repositories must carry the `recipkg` topic. Generated source lives in separate repositories, checked out as pinned Git submodules at `generated/<source-repository-name>/`. The `generated/` directory is only a container; source is never recipe payload. Reuse shared project skill repositories as pinned submodules rather than copying them. `recipkg search [keywords]` finds candidates, not validated packages.
