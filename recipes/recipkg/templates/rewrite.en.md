## Task: rewrite software

Update the existing recipe for the requested changes, then produce a new implementation.

- Current recipe: {{target}}
- Rewrite requirements: {{request}}

{{context}}

### Procedure

1. Read the complete recursive recipe. Map each request to behavior that must remain, change, or be added; expose conflicting or unspecified requirements.
2. Update requirements, interfaces, dependencies, and acceptance conditions before implementation. Preserve unrelated behavior and explain compatibility effects.
3. Treat the old implementation as optional observation material. Rebuild from the updated complete recipe; do not rely on undocumented behavior as a hidden input. For a source-only starting point, extract and validate the recipe first.
4. Generate the replacement in a separate output directory and preserve the old implementation and unique recovery material.
5. Retain useful visual identity, module boundaries, and performance properties unless the request changes them. Update corresponding acceptance conditions; do not replace a distinctive product with a generic AI page template.
6. Run the updated acceptance checks and compare public behavior before and after. Separate intended changes, regressions, and unverified cases. Compare performance using the same environment and workload.
7. A GitHub repository publishing the recipe must have the `recipkg` topic. Preserve existing topics when adding it, and verify the published files and topic when publication is in scope.

### Deliverable

- Deliver the updated Markdown-only recipe, new implementation, and behavior-change record.
- Explain dependency and acceptance changes; update the version and regenerate lock information by repackaging.
- Do not remove tests, ignore failures, or silently change dependencies to declare success.
- If no rewrite goal is supplied, inspect recipe completeness and establish the intended outcome without expanding the product arbitrarily.

### Repository convention

GitHub recipe repositories must carry the `recipkg` topic. Generated source belongs under `generated/`, with no extra implementation-name directory; when independently versioned, use this directory itself as a pinned source submodule; it is never recipe payload. `recipkg search [keywords]` finds candidates, not validated packages.
