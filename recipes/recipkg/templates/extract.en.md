## Task: extract a software recipe

Describe the following software as a self-contained recipe another agent can use to rebuild it.

- Target: {{target}}
- Additional requirements: {{request}}

{{context}}

### Procedure

1. Inspect the available source, documentation, interfaces, and tests. Record the observed version or commit. Separate verified behavior, inference, and unknowns; do not invent inaccessible details.
2. Describe users, goals, inputs, outputs, public interfaces, formats, state changes, failures, boundary cases, and environment constraints. Preserve behavior without requiring the original internal architecture.
3. For visual products, inspect the actual hierarchy, typography, density, color roles, interaction feedback, empty/error/loading states, narrow layouts, and accessibility. Preserve a coherent product identity rather than applying a generic dashboard template. For CLI/API products, describe clear output, naming, errors, and documentation.
4. Identify performance-sensitive workflows, target devices, realistic workloads, and known budgets. Record measurement methods and real baselines when available. Mark unsupported numbers as unconfirmed instead of inventing targets or results.
5. Distinguish recipe dependencies, reusable design/engineering contracts, reference material, and external tools or services. Every dependency source must contain a valid recipe; source-only repositories need extraction first.
6. Write `RECIPE.md`, `BUILD_PROMPT.md`, and observable acceptance conditions, optionally in additional Markdown files. Explain each dependency alias's role, scope, interface, and integration checks in the root build prompt.
7. Repeat extraction for every required dependency down to the leaves. Report missing materials, cycles, and external prerequisites explicitly.
8. Define success, failure, boundary, design-quality, and evidence-based performance checks. Preserve attribution and licensing. A GitHub repository publishing recipes must have the `recipkg` topic so it can be found with `recipkg search`; a topic alone does not validate its contents.

### Minimal recipe

Put exactly one TOML manifest fence in `RECIPE.md`. Keep the full behavioral contract in `BUILD_PROMPT.md`.

```toml
format = "recipkg/1"

[package]
name = "example-software"
version = "0.1.0"
kind = "software"
description = "Purpose and observable behavior"
entry = "BUILD_PROMPT.md"
```

Names use lowercase letters, digits, and single hyphens, up to 64 characters; versions follow semantic versioning. Skill recipes use `kind = "skill"`, `entry = "SKILL.md"`, and standard YAML `name` and `description` frontmatter. When available, `recipkg init <directory> --name <name>` creates a scaffold that still needs a real specification.

Add dependency tables inside the same manifest fence, for example:

```toml
[dependencies.helper]
source = "../helper"
```

### Deliverable

- Deliver UTF-8 Markdown recipes with complete recursive dependencies and reproducible acceptance conditions.
- Keep implementation source, binaries, filesystem links, and execution hooks out of recipe payloads. Declarative configuration and interface examples are allowed.
- State missing or inferred behavior and unverified visual/performance claims. Complete materials do not prove a successful reconstruction.

### Repository convention

GitHub recipe repositories must carry the `recipkg` topic. Generated source lives in separate repositories, checked out as pinned Git submodules at `generated/<source-repository-name>/`. The `generated/` directory is only a container; source is never recipe payload. Reuse shared project skill repositories as pinned submodules rather than copying them. `recipkg search [keywords]` finds candidates, not validated packages.
