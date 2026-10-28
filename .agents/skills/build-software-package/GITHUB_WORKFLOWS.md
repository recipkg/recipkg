# GitHub Actions：CI、测试、Release 与镜像

## 工作流规划

把任务分开定义，避免一个高权限 workflow 既运行不可信 PR 代码又能发布：

| 文件建议 | 触发器 | 工作 | 权限 |
| --- | --- | --- | --- |
| `.github/workflows/ci.yml` | `pull_request`、主分支 `push` | lint、格式、类型检查、构建、静态验证 | 通常 `contents: read` |
| `.github/workflows/tests.yml` | PR、主分支 push、可选 schedule | 单元/集成/端到端测试，按 OS/runtime 矩阵，覆盖率报告 | 通常 `contents: read`；artifact 所需权限另算 |
| `.github/workflows/release.yml` | 受保护版本 tag、`release: published` 或手动 | 构建发行物、签名/校验、Release draft/附件 | 单独 job 使用最小 `contents: write` |
| `.github/workflows/container.yml` | PR 只 build/test；版本 tag 才 push | OCI 镜像、多架构 manifest、SBOM/attestation | 只给发布 job `packages: write` 等必要权限 |

如果用户只要一个轻量 workflow，可合并 CI 与 tests job；Release 和 registry push 仍需独立的权限边界。配置工作流和运行远端 Actions 是两项不同的工作。

## Workflow 生成步骤

1. 从项目清单和锁文件确定语言 runtime、包管理器、安装依赖、lint/build/test 命令和支持矩阵；不要猜脚本名。
2. 用官方文档核对当前 runner、action 和 marketplace/release 版本。在写入 YAML 时优先将第三方 action pin 到已核验的完整 40 位 commit SHA，并附注释标明对应 release；只写移动 tag 时说明安全取舍。
3. 明确 `permissions`，优先 workflow/job 级最小权限；设置 `timeout-minutes`、并发取消策略、缓存 key 和 artifact retention。
4. 测试 fork PR：PR 工作流不应读取 secrets，不应写 registry 或仓库。不要为访问秘密而使用 `pull_request_target` 执行未审查的 PR 代码。
5. 按用户选择生成文件；本地校验 YAML、命令和引用的 action。用户没要求时不触发远程 CI。

GitHub 推荐 workflow 由 `.github/workflows/*.yml` 描述；见[工作流概念](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows)、[语法](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)、[CI 指南](https://docs.github.com/en/actions/get-started/continuous-integration)和[安全使用](https://docs.github.com/en/actions/reference/security/secure-use)。

## CI 与测试模板

以下是结构模板，尖括号内容必须按项目替换；新增 action 前先核实来源和 SHA。

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  check:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest]
        runtime: ["<supported-version>"]
    runs-on: ${{ matrix.os }}
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<verified-40-character-sha> # include the matching release in a comment
      - name: Set up runtime
        run: <install-or-select-runtime>
      - name: Install locked dependencies
        run: <package-manager-install-from-lockfile>
      - name: Lint and type check
        run: <project-check-command>
      - name: Build
        run: <project-build-command>
      - name: Test
        run: <project-test-command>
```

按用户确认把 `matrix` 扩展到实际支持的 OS、解释器/runtime、CPU 架构和最低/最高依赖版本。矩阵不是越大越好；写明每项覆盖的兼容承诺。测试报告 artifact 不应包含凭据、私有 fixture 或客户数据。

## GitHub Release 模板要点

- 仅对正式 tag/release job 赋予写权限，使用 environment approval、protected tag 或 release environment。
- 构建各 OS/CPU 的制品并命名可辨认；打包后做清单检查、安装/启动 smoke test、SHA-256、签名/SBOM（如果项目承诺）。
- 自动 Release 使用可信 action 或受限的 GitHub CLI/API；引用 action 时遵守上面的 SHA 核验规则。
- 选 tag-driven 或 release-driven 一个流程；检查 draft/pre-release、Release notes、资产附件和重跑幂等性。
- 不在 PR 触发器中发布，不把 tag 名直接当未验证的 shell 输入。

## OCI 发布 workflow 要点

PR job 只构建和测试；tag/release job 登录所选 registry，再发布版本 tag、源提交 SHA 和（若用户要）`latest`。GHCR 通过 `GITHUB_TOKEN` 时只授予必要的 `packages: write`。多架构构建按 Docker 官方 Buildx/manifest 指南配置；本机 smoke test、远端推送和部署分别报告。

## 私有 Git 子模块

如果项目用了私有子模块，checkout 必须启用 `submodules: recursive`（或指定路径）。GitHub 的 `GITHUB_TOKEN` 默认只在当前仓库范围内；跨仓库读取私有 Recipkg 子模块需要用户配置限权的 GitHub App installation token 或专用只读凭据。不要把个人 PAT 写进工作流，也不要让来自 fork 的 PR 接触该凭据。参考 [actions/checkout](https://github.com/actions/checkout#usage) 的私有仓库说明。
