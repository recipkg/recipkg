# 分发教程：源码包、GitHub Release、registry 与镜像

## 先区分交付渠道

- **本地构建产物**：给开发者验证，不代表公开发布。
- **GitHub Actions artifact**：用于 workflow/job 间传递或短期下载；按保留期管理。
- **GitHub Release 附件**：面向版本用户的二进制、安装包、校验和、SBOM 和发行说明。
- **语言 registry**：PyPI、npm、crates.io、Maven Central、NuGet、RubyGems 等；用户可按包名和版本安装。
- **操作系统仓库/商店**：需要遵循发行版、Homebrew、Microsoft Store、App Store 或 Google Play 的元数据、签名和审核规则。
- **OCI registry**：发布可运行的容器镜像和多平台 manifest；镜像标签可变，部署需优先固定 digest。

选用多个渠道时，明确哪个是主渠道、哪些制品通过同一个版本产生，以及每个渠道的安装指令。

## 简单版本发布

适合暂时不需要语言 registry 或应用商店的 CLI/桌面工具：

1. 确认版本号、支持平台/架构、变更摘要和 Git working tree；Release 对应一个已验证提交。
2. 在本机执行项目的测试和构建命令，生成版本化附件，命名包含项目、版本、OS、架构和格式。
3. 对每个附件生成 SHA-256 校验文件；有签名策略时用受保护密钥签名并发布公钥/验证说明。
4. 在 GitHub 创建版本 tag 和 draft Release，附上安装步骤、兼容范围、校验和、breaking changes 与已知问题。
5. 安装 Release 附件到干净环境；验收后由用户决定是否正式 publish。

`.zip`/`.tar.gz` 源码归档、可执行二进制、MSI/DMG/AppImage 等文件分别说明作用。GitHub 自动生成的源码快照不能替代项目编译的发行包。

## GitHub Release 自动化

先询问触发方式，选一种：

- **tag 驱动**：推送 `vX.Y.Z` 后构建矩阵、打校验和，再创建 draft/正式 Release。
- **Release 驱动**：用户先建 draft 或发布 Release，workflow 对应 tag 构建并上传附件。
- **手动 workflow_dispatch**：选择 tag 和预发布选项，适合需要人工审核的维护流程。

不要让 tag 驱动 workflow 同时等待同一个 Release 事件再次触发，避免重复构建/创建。发布附件前校验 tag 指向的提交、版本 metadata 和 artifact 命名。GitHub 文档：[管理 Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)、[Release API](https://docs.github.com/en/rest/releases/releases)。

## Python 与 PyPI

1. 维护 `pyproject.toml` 的名称、版本、依赖、入口点和文件清单。
2. 本地运行 `python -m build`、`twine check dist/*`，再在干净环境从 wheel 安装；需要源码安装者同时发布 sdist。
3. 对新项目先用 TestPyPI，正式项目优先配置 PyPI Trusted Publisher（OIDC）和 GitHub Environment，而非长期 token。
4. workflow 的发布 job 给 `id-token: write`，测试 job 保持 `contents: read`；只有 tag/release job 能 publish。

## npm 与其他语言 registry

- npm：检查 `package.json` 的 `files`、入口、exports、bin、license、engines；先 `npm pack --dry-run`，测试 tarball 安装，再决定 `npm publish` 的 public/access/tag。
- Rust/crates.io：`cargo package`/`cargo publish --dry-run`，检查 manifest、README、license 和包内文件；正式 publish 可能不可覆盖，发布动作要单独确认。
- Go：module 版本由 Git tag 发布；CLI 二进制可另附到 GitHub Release。不要把 Go module 版本说成 registry 上传。
- Maven Central、NuGet、RubyGems、Packagist 等：按其官方指南配置坐标、metadata、签名、OIDC/API 凭据和 registry。不可把一种 registry 的认证/版本流程复制到另一种。

每个 registry 的正式上传都是公开或对特定读者可见的外部写入。先 dry-run、核对包清单和目标账号，然后遵循用户明确授权的范围。

## OCI 容器镜像

1. 检查 `Dockerfile`/`Containerfile` 是否多阶段构建、固定合理的基础镜像、设置非 root 用户、只复制 runtime files，并使用 `.dockerignore` 排除 `.git`、依赖缓存、测试报告、密钥和本地 `.env`。
2. 本地验证镜像能启动、健康检查通过、端口/volume/权限符合 README；记录体积和 SBOM/扫描结果（如果用户选择）。
3. 询问 registry（GHCR、Docker Hub 或其他）、公开/私有、架构（如 `linux/amd64`、`linux/arm64`）、tag 规则和是否推送。
4. GitHub Actions 用 Buildx 做多平台构建；在 PR 上 build/test 但不登录、不 push；只在受信任的 tag/release 推送。
5. GHCR 使用最小 `packages: write` 和适当的 `contents: read`；Docker Hub 凭据放 GitHub Secrets。镜像消费者建议固定 digest；`latest` 只能作为额外便利标签。

多平台 workflow 示例应依据 Docker 官方当前文档配置 Buildx、必要时的 QEMU、平台矩阵和 manifest；不要假定所有 CPU 架构都能在同一个 runner 原生构建。参考：[Docker GitHub Actions](https://docs.docker.com/build/ci/github-actions/)、[多平台策略](https://docs.docker.com/build/building/multi-platform/)。

## 大型文件与发布附件

用户需要下载的大型二进制、安装包或系统镜像放 GitHub Release、专用对象存储或 registry；不要放 Git 普通 blob。必要时才用 Git LFS，并先核对配额、协作者下载方式和归档行为。检查 GitHub 当前单文件、仓库大小与 LFS 限制，不将数字永久写死在教程里。
