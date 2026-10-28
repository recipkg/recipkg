---
name: build-software-package
description: Plan and implement reproducible software packages, distribution channels, container images, GitHub Releases, CI and test workflows, and a project-specific README. Ask for the desired scope in one compact interview before changing the repository.
---

# 构建、打包与分发软件

## 先问用户：一次收齐范围

先读取现有对话、README、项目清单和 CI 配置；已知答案不重复问。把尚缺的选择合并成一轮问题发给用户。任务类型、生态、平台和分发渠道都允许多选；最后提供自由描述。不要先创建文件或发布产物，再补问关键目标。

1. **这次要做什么？** 可多选：初始化标准项目布局、构建软件包、生成安装包/系统包、构建 OCI 容器镜像、创建 GitHub Release、搭建 CI、搭建独立测试工作流、写发布说明、向注册表/应用商店分发、只给出教程和计划。
2. **目标软件与生态是什么？** 选择语言、框架和包格式；例如 Python/wheel+sdist、npm、Rust/crate、Go module/CLI、JVM、.NET/NuGet、RubyGem、Composer、C/C++、Swift/Dart、R/Julia、Linux 系统包、Windows/macOS/Android/iOS 应用、容器、插件或其他。可以多选，也可选“按源码仓库建议”。
3. **要支持哪些目标？** OS、CPU 架构、最低系统/运行时版本、浏览器、容器平台或应用商店。镜像一词要确认是 Docker/OCI 容器镜像、虚拟机/磁盘/ISO 镜像，还是 Android/桌面应用安装镜像。
4. **要分发到哪里？** 可多选：GitHub Release 附件、GitHub Packages/GHCR、PyPI、npm、crates.io、Maven Central、NuGet、RubyGems、Packagist、Linux 仓库、Homebrew、Microsoft Store、Apple App Store、Google Play、扩展市场、私有 registry 或其他。
5. **自动化范围是什么？** CI 触发分支/PR/标签；要运行的 lint、类型检查、构建、测试、覆盖率、矩阵、签名、SBOM、制品保留期；Release 是手动、打 tag 后自动，还是只生成工作流。
6. **发布权限到哪一步？** 只写配置/教程，还是授权发布到某个明确的 registry/release？需要哪些现成凭据、GitHub Environment 或签名密钥？不能索取或写入仓库中的明文秘密。
7. **README 要面向谁、使用什么语言？** 说明目标用户、软件要解决的问题、最重要的使用场景、安装方式、演示材料、项目特点、需要保留的品牌语气。可自由描述，不必套统一模板。

## 执行

1. 先检查项目的 `AGENTS.md`、Git 状态、分支、包管理器、锁文件、源码入口、现有脚本、测试和 `.github/workflows/`。保留已有未提交改动；不通过清理、重置或覆盖来“整理”仓库。
2. 从 `PACKAGE_FORMATS.md` 为所选生态挑选制品和目标 registry。未列出的格式，先查维护方当前规范，写出同样完整的本地构建、验包、安装验证、发布与 GitHub Actions 路径，再继续。
3. 使用适合项目的布局，不搬动用户源码来迎合模板。仓库布局和发布包布局分别判断；只把运行时必需文件放进最终制品，并在上传前预览包清单。
4. 根据 `DISTRIBUTION.md` 分清本地构建、GitHub Release 附件、语言 registry、系统仓库、应用商店和 OCI registry。版本来源、标签、校验和、签名、架构矩阵与安装方法要一致。
5. 用户选择 CI 时，按 `GITHUB_WORKFLOWS.md` 生成适合项目的工作流。CI、测试、Release、registry 发布和容器推送分开控制权限；只配置工作流不等于已运行或已发布。
6. 用户选择初始化或更新 README 时，依照 `README_DESIGN.md` 读取实际项目行为，并研究同类项目 README 的信息组织。借鉴章节顺序和表达方式，不复制文案、截图或未经验证的徽章；内容围绕当前项目定制。
7. 按用户选择执行本地构建、测试、包内容检查、安装/启动验收。写明运行命令、环境、产物和失败项。用户只要求配置时，不触发远程 CI、不创建 tag、不上传 registry、不发 Release。
8. 检查 Git diff、工作流权限和包清单；指出需要用户在 registry 或 GitHub 设置页配置的凭据、可信发布者、签名证书或应用商店资料。

## 安全边界

- 发布到公开 registry、应用商店、GHCR 或创建真实 Release 前，确认用户明确指定了目标、版本和发布动作。配置工作流的要求本身不代表允许立即发布。
- Actions 只申请所需的 `permissions`；PR 检查一般使用只读令牌。第三方 Actions 使用时查官方仓库当前版本和完整提交 SHA，并检查来源。
- 不把 token、证书、keystore、`.env`、签名密码或私有 registry 凭据写进源码、日志或公开工件。
- 不把依赖目录、缓存、编译缓存、测试报告、未压缩媒体或数据库文件打进源码包；查看最终包清单后再发布。
- GitHub Release 可以承载用户下载的二进制；registry 包、Release 附件和容器镜像是不同交付物，不能仅以“上传成功”表示安装有效。

## 参考

- [软件包格式与生态清单](PACKAGE_FORMATS.md)
- [分发教程](DISTRIBUTION_GUIDE.md)
- [GitHub Actions 工作流指南](GITHUB_WORKFLOWS.md)
- [定制 README](README_DESIGN.md)
