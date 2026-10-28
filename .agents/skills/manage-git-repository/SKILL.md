---
name: manage-git-repository
description: Organize and maintain Git projects, choose a clear source/package layout, control repository growth, and handle submodules safely. Inspect repository state before proposing or applying changes.
---

# Git 仓库管理

## 工作方式

1. 阅读仓库级 `AGENTS.md` 和相关项目说明；执行 `git status --short --branch`、`git submodule status`，检查分支、远端、未提交/未跟踪内容和现有子模块。
2. 先说清楚用户要管理的是源码仓库、monorepo、发布包还是部署产物；沿用有用的现行布局，不为套模板大规模移动文件。
3. 若用户要求整理，先给出基于路径、文件类型和 Git 历史的具体改动，再在授权范围内实施；不覆盖未提交文件，不重置、不清理未知文件，不改 unrelated submodule。
4. 检查 `.gitignore`、`.dockerignore`、`.npmignore`/`files`、包构建配置和 CI artifact；确保生成文件没有误进 Git，也不会缺失运行必需文件。
5. 处理大文件时确认是否是源码、测试 fixture、可下载生成物、依赖缓存、模型、媒体或用户数据。优先阻止新增长文件进入历史，并决定合适存储；已提交的大文件需要单独评估迁移历史的影响，不能直接删工作树文件或重写远端历史。
6. 复查 Git diff、文件布局、子模块 pin、包清单和 ignore 规则；用户要求验证时在本机验证，不等待 CI。不要把本地检查说成远端发布或部署。

## 必须保护的仓库健康

- 不随手上传二进制、数据集、视频/图片原片、模型、依赖目录、缓存、build/dist 输出、覆盖率报告、日志、虚拟环境、密钥或本地数据库。
- 前端项目尤其检查 `node_modules/`、`.next/`、`dist/`、`build/`、`.turbo/`、Vite/Webpack cache、Playwright browser cache、source map、录屏/截图和大型静态媒体。依赖用 lockfile 表达，不提交 vendor/cache，除非项目明确必须 vendoring。
- 上传前查看大文件：`git ls-files`、`git status --short`、`du`/`find`，并查看待提交对象。GitHub 的单文件限制和仓库建议会变化；从官方文档实时核对，不能把历史阈值写成永久规则。
- release 二进制、大型镜像放 Release/OCI registry/对象存储；需要在 Git 中做版本管理的大型二进制才评估 Git LFS，并核对配额和下载体验。
- 依赖锁文件是否提交取决于生态与应用类型：应用通常提交锁文件；可复用库按语言生态惯例处理。不要笼统删除所有 lockfile。
- 子模块是独立 Git 仓库的固定 commit 引用。需同步来源时优先 git submodule；普通应用依赖优先使用官方包管理器，不能把所有第三方依赖改成子模块。
- 每个 repo/package 有明确 owner、默认分支、许可证、README、版本来源、构建/测试入口；避免多个目录同时维护同一份真相。

## 快速检查命令

先只读执行，按仓库大小调整范围：

```sh
git status --short --branch
git remote -v
git submodule status --recursive
git ls-files
git ls-files | sort | uniq -d
```

对待提交内容查看大文件和敏感配置时避免打印 secret 值；可仅输出路径、大小、匹配类型。提交前看 `git diff --check`、`git diff --stat` 和 `git diff --cached --stat`。任何历史清理需另行评估 clone、tag、fork、release 与协作者影响。

## 参考

- [标准项目布局](PROJECT_LAYOUTS.md)
- [GitHub 文件大小与大文件策略](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [Git LFS 说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)
- [GitHub 仓库限制](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)
- [Git 子模块](https://git-scm.com/docs/git-submodule)
