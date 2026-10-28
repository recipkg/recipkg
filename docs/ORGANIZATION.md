# 项目与组织命名

## 推荐命名

| 对象 | 建议 |
| --- | --- |
| 项目 | Recipkg |
| 中文名 | 构方 |
| 包类型 | 软件配方包 / Recipe Package |
| GitHub 组织显示名 | Recipkg · 构方 |
| 首选组织标识 | `recipkg` |
| 备选显示名与标识 | Recipkg Project / `recipkg-project` |
| 建议主仓库 | `recipkg/recipkg` |

Recipkg 由 recipe 与 pkg 组合：管理软件的“配方包”。名称同时容纳软件重建提示词和 Agent 技能，不限定模型提供方或目标编程语言。

组织已创建，标识为 `recipkg`；主仓库位于 `recipkg/recipkg`。

## 初期仓库结构

主仓库保存配方、协议和示例，通过固定提交的子模块引用独立的 CLI 源码仓库与技能仓库。核心内容包括：

- `recipes/recipkg/`：产品合同、协议、公开技能和中英文提示词。
- `generated/cli-source/`：独立仓库 `recipkg/cli-source` 的固定提交子模块，保存可替换 CLI 源码、打包配置和测试。
- `docs/SPEC.md`：配方与归档协议。
- `examples/`：可以递归打包的纯 Markdown 配方。
- `generated/cli-source/tests/`：CLI 行为与包完整性的验证。

项目和主仓库保持原名 `recipkg`，不追加 `-recipkg`。发布配方的 GitHub 仓库必须有 `recipkg` topic；源码仓库若需独立管理，名称使用全小写、连字符，在 `generated/` 容器下用同名子目录作为固定提交子模块。所有项目技能也各自独立成仓库，用子模块引用相同上游。

有明确需求后再建立独立的配方集合或文档站。第一版使用本地目录、HTTPS 配方归档和固定提交的 Git 仓库作为来源，不要求中央注册表。

## 对外介绍

中文：

> Recipkg（构方）是一个管理软件重建提示词和 Agent 技能的小型包工具。它用纯 Markdown 配方保存需求、TOML 依赖配置和验收条件，递归收齐依赖，再把完整材料交给你选择的 Agent。

English:

> Recipkg manages software reconstruction recipes and Agent Skills. It bundles Markdown instructions, TOML dependency metadata, and acceptance criteria into a complete recursive package for the agent you choose.
