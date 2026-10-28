# Project skill repositories / 项目技能仓库

All eleven skills have their own canonical GitHub repositories. This project records reviewed commits as Git submodules; migrated projects reuse the same repositories, normally under `.agents/skills/<skill-name>/`. Public CLI skills and development skills remain separate roles, not separate copies of a skill.

| Skill | Canonical repository | Checkout in this project |
| --- | --- | --- |
| `add-dependency` | [recipkg/add-dependency](https://github.com/recipkg/add-dependency) | `.agents/skills/add-dependency/` |
| `build-software-package` | [recipkg/build-software-package](https://github.com/recipkg/build-software-package) | `.agents/skills/build-software-package/` |
| `discover-dependencies` | [recipkg/discover-dependencies](https://github.com/recipkg/discover-dependencies) | `.agents/skills/discover-dependencies/` |
| `manage-git-repository` | [recipkg/manage-git-repository](https://github.com/recipkg/manage-git-repository) | `.agents/skills/manage-git-repository/` |
| `migrate-to-recipkg` | [recipkg/migrate-to-recipkg](https://github.com/recipkg/migrate-to-recipkg) | `recipes/recipkg/skills/migrate-to-recipkg/` |
| `prompt-to-software` | [recipkg/prompt-to-software](https://github.com/recipkg/prompt-to-software) | `.agents/skills/prompt-to-software/` |
| `rewrite-software` | [recipkg/rewrite-software](https://github.com/recipkg/rewrite-software) | `.agents/skills/rewrite-software/` |
| `rewrite-to-recipkg` | [recipkg/rewrite-to-recipkg](https://github.com/recipkg/rewrite-to-recipkg) | `recipes/recipkg/skills/rewrite-to-recipkg/` |
| `software-to-prompt` | [recipkg/software-to-prompt](https://github.com/recipkg/software-to-prompt) | `.agents/skills/software-to-prompt/` |
| `test-feedback` | [recipkg/test-feedback](https://github.com/recipkg/test-feedback) | `recipes/recipkg/skills/test-feedback/` |
| `update-recipkg-in-project` | [recipkg/update-recipkg-in-project](https://github.com/recipkg/update-recipkg-in-project) | `.agents/skills/update-recipkg-in-project/` |

Initialize a checkout with `git submodule update --init --recursive`, or clone with `git clone --recurse-submodules https://github.com/recipkg/recipkg.git`. Review local work and upstream changes before updating a skill commit, then explicitly commit the parent gitlink. Never force-reset edited submodules.

The CLI source is also separate: [recipkg/cli-source](https://github.com/recipkg/cli-source), pinned at `generated/cli-source/`. Its bundled skill directories are submodules of the same three public skill repositories. `generated/` is only a container, not a flat source tree.

项目技能每个一个仓库，主仓库只记录固定提交。迁移到其他项目时引用相同仓库，不复制正文、不创建项目后缀的技能副本。源码也是独立仓库，通过 `generated/cli-source/` 子模块接入；以 Git 树中的 `160000` 确认真子模块。

`recipkg skills sync` still provides managed Markdown copies for non-Git destinations. It does not create a Git submodule and is not the default project integration workflow. Root `RECIPE.md` and `LOCK.md` are recipe container metadata, omitted from synchronized skill payloads for every source kind. README, license, translations, and workflow resources remain available.
