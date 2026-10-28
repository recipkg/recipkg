---
name: update-recipkg-in-project
description: Add or update Recipkg in a host project using the Recipkg Git submodule as the canonical source, then synchronize its migration skill into the project's agent skill directory without losing local work.
---

# 在项目中安装或更新 Recipkg 技能

## 目标与默认设计

Recipkg 的独立 Git 仓库是唯一真相源。宿主项目通过 Git 子模块固定 Recipkg commit，并从子模块运行 CLI；CLI 把 `migrate-to-recipkg` 同步到宿主项目的 agent skills 目录。不要把整份 Recipkg 或同一技能手工复制到宿主仓库长期维护，也不要直接编辑 CLI 生成的 managed copy。

默认路径：`tools/recipkg`。用户项目如已有约定路径则沿用；多个仓库中的同步目标按项目现行 Agent 规则决定（例如 `.agents/skills` 或 `.claude/skills`），不可默认覆盖已有同名技能。

## 工作流程

1. 检查宿主项目 `AGENTS.md`、`git status --short --branch`、`.gitmodules`、`git submodule status --recursive`、CLI 版本、Recipkg 目录和目标技能目录。确认是否已有未提交工作、嵌套 Git repo、同名 skill、损坏/未初始化子模块或自定义安装路径。
2. 若 `tools/recipkg` 已是正确子模块，不重复 add；检查 remote URL 是 canonical `https://github.com/recipkg/recipkg.git`（或用户规定的官方 SSH URL），并核验当前 pin 和工作树。若同路径存在普通目录或另一 Git 项目，不删除/覆盖；先提出保留与迁移计划。
3. 若子模块缺失且目标路径空闲，运行：

   ```sh
   git submodule add https://github.com/recipkg/recipkg.git tools/recipkg
   git submodule update --init --recursive
   ```

   加入后检查 `.gitmodules`、gitlink commit、子模块 branch policy 和当前 CLI 版本。项目必须 pin commit；即使配置追踪 branch，也要审查并显式提交父仓库指针变动。

4. 运行 `tools/recipkg/.venv/bin/recipkg --help` 或在可用的本地开发安装方式下确认 CLI 入口。先读 `--help` 和该版本文档，不猜 CLI 子命令、参数或输出路径。Recipkg 当前用 `skills sync` 管理可同步技能时，按其帮助显示的参数同步到宿主项目的目标目录；先预览目标和现有同名文件。项目公开安装入口只需同步 `migrate-to-recipkg`。
5. 验证同步后的 skill 与固定子模块内的 `src/recipkg/data/skills/migrate-to-recipkg/SKILL.md` 完全一致；managed copy 加入 `.gitignore` 还是提交到宿主仓库，遵循宿主项目策略。若提交生成副本，要标注它由哪个 submodule commit 同步，禁止人工编辑。
6. 需要自定义说明时，写在独立的项目说明或用户管理区，不在 managed 文件内追加，以免下次 sync 丢失。上游修改先在 Recipkg 仓库完成，再升级子模块 pin 和同步副本。
7. 提交前审查父仓库 `git diff -- .gitmodules`、gitlink diff、目标 skill 内容、ignore 和未提交文件；运行本地相关检查。只 commit 授权范围内的 `.gitmodules`、gitlink 和 managed skill 路径，不替用户提交其余变更。

## 更新到新 Recipkg 版本

更新前读出当前子模块 commit、远端默认分支/tag、父仓库 dirty 状态。用 fetch 只获取新信息，不 reset。选择用户指定版本；未指定时可列出候选版本并按仓库发布节奏建议一个。切换子模块到目标 commit 后，先看该版本变化与 CLI help，再执行 sync。最后审查同步 diff，父仓库必须显式提交 gitlink 更新；不要把子模块 detached HEAD 误报为损坏（子模块通常在固定提交上）。

```sh
git -C tools/recipkg fetch --tags origin
git -C tools/recipkg status --short --branch
# 经核对后选择一个确切 tag/commit，再 checkout；不要盲目跟随浮动分支。
git -C tools/recipkg checkout <reviewed-tag-or-commit>
git submodule status --recursive
```

CLI 参数或安装方法可能随版本变化，先以该子模块 commit 内的 `--help` 和 README 为准。升级 Recipkg 和同步技能是一个变更单元；确认工作树 clean/可控后再做。

## 同步和 GitHub Actions

- 本机同步优先使用 submodule 内 CLI，从唯一真相源生成目标 skill。
- workflow 要 checkout Recipkg 子模块时配置 recursive checkout；若子模块仓库为私有，默认 `GITHUB_TOKEN` 只有当前仓库权限，需单独配置限权的 GitHub App token 或 read-only deploy credential。不要把个人 PAT 写进 workflow，也不要把凭据暴露给 fork PR。
- hosted runner 的工作目录通常不包含开发者的本地虚拟环境；workflow 要通过可信、可复现的安装方式准备运行时/CLI，不能硬编码某台机器的 `.venv`。
- 除用户明确要求搭建/更新 workflow 外，不修改 CI。普通同步、更新工作不触发远程 workflow。

## 限制与例外

- 子模块适合需要独立 Git 历史、固定版本、由上游维护的代码/技能源。普通 Python/npm 等项目依赖仍使用对应 package manager。
- 同一个 repo 中不需要嵌套的项目级专用 skill 可以本地直接维护；只有 Recipkg 可复用的共通内容才回到 Recipkg 上游。
- 用户的本地修改、未提交文件或自定义路径优先保护。发现同名文件不一致、未知 CLI 参数或子模块 dirty 时，停止相关覆盖/更新，先向用户说明准确路径和冲突内容。

## 验收

- `git submodule status --recursive` 显示预期 Recipkg commit；`.gitmodules` 指向 canonical source。
- 子模块 CLI 版本和参数已确认；同步 skill 可读取，名称和 frontmatter 有效。
- managed skill 内容来自固定 commit，没有手工漂移；宿主自定义说明保存在独立位置。
- 父仓库 diff 只包含约定的 submodule metadata/gitlink/skill 更新和说明。
- 本地检查结果与未运行的 CI、registry 发布、正式部署分别报告。
