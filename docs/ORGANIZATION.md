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

先把 CLI、协议、内置技能和示例放在同一个仓库中，避免在格式尚未稳定时维护多个重复版本。核心内容包括：

- `src/recipkg/`：包工具实现及内置提示词、技能。
- `docs/SPEC.md`：配方与归档协议。
- `examples/`：可以递归打包的纯 Markdown 配方。
- `tests/`：CLI 行为与包完整性的验证。

有明确需求后再建立独立的配方集合或文档站。第一版使用本地目录、HTTPS 配方归档和固定提交的 Git 仓库作为来源，不要求中央注册表。

## 对外介绍

中文：

> Recipkg（构方）是一个管理软件重建提示词和 Agent 技能的小型包工具。它用纯 Markdown 配方保存需求、TOML 依赖配置和验收条件，递归收齐依赖，再把完整材料交给你选择的 Agent。

English:

> Recipkg manages software reconstruction recipes and Agent Skills. It bundles Markdown instructions, TOML dependency metadata, and acceptance criteria into a complete recursive package for the agent you choose.
