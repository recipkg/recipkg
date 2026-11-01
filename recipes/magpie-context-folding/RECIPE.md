# Magpie Context Folding

```toml
format = "recipkg/1"

[package]
name = "magpie-context-folding"
version = "0.5.0"
kind = "software"
description = "Reversible, annotation-driven context folding for Magpie with local archive recovery and a standalone text-folding core."
entry = "BUILD_PROMPT.md"
```

## Source and license

Observed source: `https://github.com/LIghtJUNction/magpie-context-folding`, commit `b0837a72d62a88bfff301de5dbd76b276d24eca1`, package version 0.5.0, inspected 2026-10-28. The source project is licensed under MIT; preserve attribution to LIghtJUNction and the license terms when rebuilding or redistributing.

The source checkout is observation material only. It is not a build dependency or part of this recipe. This recipe records the two separately installed products documented by the source: the Magpie TypeScript plugin and the independent Python `ctxf` text-processing package. Their archives and state are not interchangeable.

## Evidence boundaries

The 0.5.0 README and protocol documents define the intended public contract. The source repository records local regression, component and selected host/container smoke evidence. These records do not establish successful independent reconstruction, npm availability of 0.5.0, real-model quality or cost improvements, or deployment into a user's live Magpie session. See `ACCEPTANCE.md` and `COVERAGE.md` for distinctions between documented requirements, historical test reports, this recipe's isolated source observations, and unverified claims. `PROTOCOL.md` bundles the detailed protocol; `LICENSE.md` preserves the upstream MIT license. The standalone Python package is `context-folding` 0.1.0, not plugin version 0.5.0.
