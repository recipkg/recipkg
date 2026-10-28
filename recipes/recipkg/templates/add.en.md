## Task: add a recipe dependency

Verify and integrate the following dependency into the software recipe.

- Recipe: {{target}}
- Dependency source: {{source}}
- Alias: {{alias}}
- Additional requirements: {{request}}

{{context}}

### Procedure

1. Read the root and recursive recipes. Define the capability this dependency supplies and the interface expected by its callers.
2. Verify that the source contains a valid Recipkg recipe. Source-only projects, isolated prompts, reference documents, and runtime services are not packaged recipe dependencies.
3. Record attribution, licensing, version, and compatibility evidence. Use relative local sources, HTTPS recipe archives, or Git sources pinned to a full 40-character commit with the correct recipe subdirectory.
4. Explain the alias's role, scope, integration contract, and acceptance checks in `BUILD_PROMPT.md`. Reusable quality/design/performance rules must not be confused with runtime libraries or applied beyond their declared scope.
5. Add the dependency table inside the existing single TOML manifest fence. Recursively collect required recipes; report missing dependencies, cycles, conflicts, and external prerequisites.
6. Repackage to resolve remote materials and refresh integrity records, then check the archive and complete build prompt. Local checks and prompt rendering remain offline. Preserve existing inputs and do not execute dependency content.

### Configuration example

Use the requested alias and real source. Put this table in the manifest's existing TOML fence:

```toml
[dependencies.helper]
source = "../helper"
```

### Deliverable

Deliver the updated recipe, complete dependency material, and observable integration checks. Distinguish verified compatibility from proposals or unknowns. A GitHub repository distributing the recipe must carry the `recipkg` topic; discovery is not validation or trust. The CLI that printed this task has not itself modified any manifest or installed a dependency.

### Repository convention

GitHub recipe repositories must carry the `recipkg` topic. Generated source lives in separate repositories, checked out as pinned Git submodules at `generated/<source-repository-name>/`. The `generated/` directory is only a container; source is never recipe payload. Reuse shared project skill repositories as pinned submodules rather than copying them. `recipkg search [keywords]` finds candidates, not validated packages.
