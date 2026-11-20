# Project progress / 项目进度

## 2026-11-20：文档与技能引用核对（本地）

这次核对只覆盖 Recipkg 主仓库的 Markdown 链接、固定子模块引用和 CLI 单元测试；**不代表重新发布、重建所有配方，也不代表所有平台的端到端验收**。为避免覆盖其他工作，保留已有 `.pi/` 未跟踪目录及全部子模块内容，不更新锁定版本。

- **源码边界：** 主仓库基线 `a76ae4a1580aa1918e30483acb6299d6d654b378`（检查时与 `origin/main` 一致）；CLI 源码子模块固定 `709ab44231000a31bae9b26fe05a017d4408fe20`。这两个提交分别是主仓库和 CLI 的复现入口，不以日期代替提交固定。
- **技能结构：** `git ls-files -s` 实际列出 13 个 `160000` gitlink，其中 `.agents/skills/` 9 个、`recipes/recipkg/skills/` 3 个，另一个为 `generated/cli-source/`；与 [技能仓库目录](SKILLS.md) 的 12 个项目技能一致。CLI `skills list` 实际只显示三个公开内置技能：`migrate-to-recipkg`、`rewrite-to-recipkg`、`test-feedback`，不能把其他九个开发技能宣称为 CLI 内置。
- **本地回归：** Linux / Python 3.14.10，使用仓库固定 CLI 源码执行 `RECIPKG_RECIPE_ROOT="$PWD" PYTHONPATH=generated/cli-source/src python3 -m unittest discover -s generated/cli-source/tests -q`；58 项通过，零失败。未触发远程 CI 或 CodeQL。
- **文档核对：** 扫描 Git 跟踪的所有 `.md` 文件中相对路径的内联 Markdown 链接，未发现缺失的目标文件；同时对照 `README.md`、`README.en.md` 的技能计数及开发命令。该扫描不证明外部 URL 可达、标题锚点有效或配方在语义上足够完整。
- **未完成范围：** 本次没有执行 wheel 的隔离安装测试、跨平台原生验证、所有远端技能 HEAD 的兼容性检查或发布动作。2026-11-01 条目是当时证据快照，其 `11` 个技能数量和 Python 版本不应当作当前值。

### Reproduction / 复现

```sh
git ls-files -s | grep '^160000 '
PYTHONPATH=generated/cli-source/src python3 -m recipkg skills list
RECIPKG_RECIPE_ROOT="$PWD" PYTHONPATH=generated/cli-source/src python3 -m unittest discover -s generated/cli-source/tests -q
```

**Claim–evidence review:** 本轮仅支持“12 个技能 gitlink 已记录、CLI 内置三个技能、现有 58 项本地测试通过、已检查的相对链接可解析”；不支持“12 个技能已全部运行验收”“wheel 已重新发布”“跨平台通过”或“完整语义复现”。后续改动应先固定上游源码及精确消费端，再补对应真实验证和提交回执。

## 2026-11-01：恢复进度与收尾

### 已确认的项目状态

- 盘点起点：主仓库 `e0a004465101eacf145977810b6bdff5fe22f0bc`，CLI 源码 `f6f5983d558937677c712fea291c65b376487568`。两者均与各自远端 main 一致。唯一既有未跟踪项目材料是 `recipes/magpie-context-folding/`；本轮未覆盖或删除它。
- 五个提示词动作、递归归档与完整性检查、离线渲染、显式 GitHub 搜索、双语模板、托管技能同步、固定提交的项目技能子模块均已实现。基线完整测试为 57 项通过，而非待开发事项。
- 11 个项目技能及独立 CLI 源码均以固定子模块引用。主配方和 CLI 内三个公开技能的提交相同；本轮没有更新技能上游或无关子模块。
- `CHANGELOG.md` 的 Unreleased 表示未发布变更，不代表功能未实现。本轮不进行正式版本发布、公共包发布或部署。

### 本轮完成

- 修复自举配方 `SPEC.md`、`SPEC.en.md` 漏掉的 `skills project list/add/update` 合同：固定提交、暂存而不提交、忽略路径提前拒绝、默认分支缺失处理、继承 Git 环境隔离及失败现场保留。公开规范与包内规范仅保留必要的目录链接差异。
- 修复配方 CLI/验收仍要求 `recipkg 0.1.0` 的过期说明，统一为已存在的 0.1.1；同步中英 README 的自举归档文件名。示例软件和 `init` 的 0.1.0 版本不受影响。
- 在独立 CLI 源码仓库加入规范及版本一致性回归测试。补齐规范前该测试两种语言均失败；修复后通过。没有更改 CLI 运行逻辑或运行依赖。
- 完成 Magpie 配方的结构收尾：加入详细 `PROTOCOL.md`、原始 MIT `LICENSE.md` 和覆盖记录 `COVERAGE.md`；补齐独立包版本、最低 Python 版本和外部前提；通过隔离源码观察裁决 `ctxf read --raw` 的 README 冲突。
- 更正 `ORGANIZATION.md` 中标准库尚未建立的过期说法；中英 README 均提供本进度入口。

### 本地验证结果

环境：Linux，Python 3.14.8。检查使用临时状态，不调用模型、不重跑远程 CI。

- 完整回归：58 项，零失败、零跳过。
- `examples/hello`、`recipes/recipkg`、`recipes/magpie-context-folding`：目录检查、打包、归档检查、解包后检查全部通过。各自归档含 8、41、8 个 Markdown 文件（含锁文件）。连续打包字节相同；归档仅含普通 Markdown 文件/目录；英、中两种构建提示词逐文件包含全部非锁文件的原文，包括递归质量配方、协议、技能与许可证。
- 隔离 wheel：从临时源码副本构建 `recipkg-0.1.1-py3-none-any.whl`，在临时虚拟环境安装；离开 checkout、清除 PYTHONPATH 后，版本、三个内置技能、五动作和中英 extract 均通过。wheel SHA-256：`d835fb47644f43ede50e214ede588f5a3ec338bc1f2399e965b75515d223ef56`。本轮源码改动仅涉及测试，不改变 wheel 运行内容；未发布该制品。
- Magpie 固定源码的隔离观察：150 行 Unicode 正文折叠后，普通 `ctxf read` 与 `--raw` 均输出 1200 个码点，并在 stderr 报 `nextOffset=1200`；JSON 分页字段一致。不是完整 Magpie 回归，也不是独立重建证据。

### 可重复验证

从主仓库根运行：

```sh
RECIPKG_RECIPE_ROOT="$PWD" PYTHONPATH=generated/cli-source/src python3 -m unittest discover -s generated/cli-source/tests -v
export PYTHONPATH="$PWD/generated/cli-source/src"
work=$(mktemp -d)
for recipe in examples/hello recipes/recipkg recipes/magpie-context-folding; do
  name=$(basename "$recipe")
  python3 -m recipkg check "$recipe"
  python3 -m recipkg pack "$recipe" -o "$work/$name.recipe.tar.gz"
  python3 -m recipkg pack "$recipe" -o "$work/$name.again.recipe.tar.gz"
  cmp "$work/$name.recipe.tar.gz" "$work/$name.again.recipe.tar.gz"
  python3 -m recipkg check "$work/$name.recipe.tar.gz"
  python3 -m recipkg unpack "$work/$name.recipe.tar.gz" "$work/$name-unpacked"
  python3 -m recipkg check "$work/$name-unpacked"
  python3 -m recipkg build "$work/$name.recipe.tar.gz" --lang en --output "$work/$name.en.md"
  python3 -m recipkg build "$work/$name.recipe.tar.gz" --lang zh-CN --output "$work/$name.zh-CN.md"
done
git diff --check
git -C generated/cli-source diff --check
git submodule status --recursive
```

### 提交、推送与未验证边界

交付顺序为 CLI 测试提交先推送，再由主仓库提交新 gitlink、规范、文档与 Magpie 材料。本条目所属提交及其 CLI gitlink 是交付版本；用下面的只读命令核对，而不将本地修改当作已经上线：

```sh
git log -1 --oneline
git ls-remote origin refs/heads/main
git -C generated/cli-source log -1 --oneline
git -C generated/cli-source ls-remote origin refs/heads/main
git ls-tree HEAD generated/cli-source
```

没有正式发布或部署。Magpie 配方仍有明确的提取/验证缺口：完整 SDK/RPC、适配器、注释编辑与生命周期 API 合同未全部提炼；两组件未独立重建，真实宿主、最低版本、多平台、npm 可用性和模型成本/质量收益未验证。详见该配方 `COVERAGE.md`。这些不作为本轮结构收尾的通过声明。标准库其他配方的完整提取和重建不在本轮范围。`.pi/` 是本地目标运行状态，不属于提交材料。

## English summary

The baseline already implemented the five prompt actions, recursive packages, offline rendering, explicit search, bilingual templates and pinned project skills (57 passing tests). This closeout fixes missing project-skill clauses in both bundled specifications and stale 0.1.0 version examples, adds a specification/version consistency regression, and organizes the existing Magpie recipe without claiming complete extraction or reconstruction.

Final local evidence: 58 passing tests with no skips; deterministic Markdown-only archives for hello, Recipkg and Magpie; complete payload inclusion in both prompt languages; unpack/check round trips; an installed 0.1.1 wheel exercised outside the checkout. A narrow pinned-source experiment resolves the conflicting `ctxf read --raw` documentation. All relevant commands and exact source identities are above.

Source changes are committed upstream first and the parent tracks that fixed CLI commit. Remote hashes must match the delivery commits; this is source synchronization, not release or deployment. Complete Magpie SDK/RPC/adapter extraction, independent reconstruction, live host validation and model-benefit measurements remain explicitly unverified, not silently waived.
