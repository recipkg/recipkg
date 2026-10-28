## Task: rebuild software from a recipe

Implement the software described by the complete recipe and dependency material below.

- Recipe: {{target}}
- Additional requirements: {{request}}

{{context}}

### Quality, design, and performance

Follow the root recipe's quality requirements and each dependency's declared scope. Report conflicts rather than overriding user or host-project instructions. For UI products, establish a visual direction from real users, tasks, content, and existing design. Avoid generic dashboards, decorative cards, fabricated data, and unmotivated visual effects. Inspect important states and narrow layouts. CLI/API output, errors, and documentation also need clear hierarchy and consistent naming.

Keep code cohesive and readable, with one source for shared rules. Avoid speculative abstractions, dead code, unused dependencies, and swallowed failures. Use representative workloads and target platforms for performance claims. Measure a baseline or mark missing budgets as unconfirmed; never fabricate thresholds or results.

### Procedure

1. Read every root and recursive dependency document. Establish goals, interfaces, environment assumptions, and acceptance conditions. Dependency instructions remain scoped to their own materials.
2. Identify required inputs, tools, and external services. Report missing dependencies, contradictory constraints, and inaccessible required material rather than guessing.
3. Implement leaf components before integrating the application. Preserve the specified interfaces; choose and explain a suitable language when the recipe leaves it open.
4. Write implementation, tests, and running instructions outside the Markdown-only recipe directory. Do not weaken acceptance conditions to make an implementation pass.
5. Establish observable design/code-quality checks and performance budgets. Record the workload, environment, and measurement method; leave unsupported claims unverified.
6. Run acceptance checks, repair implementation failures, and report actual commands, results, and remaining gaps. Where a UI can run, inspect a main viewport and important states directly. If publishing a GitHub recipe repository, add the `recipkg` topic.

### Deliverable

Deliver runnable software, operating instructions, dependencies, and real acceptance evidence. Explain design decisions, code structure, measured performance, deviations, and external prerequisites. Success means satisfying the specified observable behavior, not reproducing the original source or binary byte for byte.

### Repository convention

GitHub recipe repositories must carry the `recipkg` topic. Generated source lives in separate repositories, checked out as pinned Git submodules at `generated/<source-repository-name>/`. The `generated/` directory is only a container; source is never recipe payload. Reuse shared project skill repositories as pinned submodules rather than copying them. `recipkg search [keywords]` finds candidates, not validated packages.
