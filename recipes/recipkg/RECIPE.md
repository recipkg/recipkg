# Recipkg 自举配方

这份配方描述 Recipkg 自身。它保存公开行为、格式约定、五主动作的中英文模板和三个公开技能，供 Agent 在没有原实现源码的情况下重新实现工具。

```toml
format = "recipkg/1"

[package]
name = "recipkg"
version = "0.1.1"
kind = "software"
description = "管理纯 Markdown 软件配方、递归依赖和 Agent 技能的提示词生成 CLI。"
entry = "BUILD_PROMPT.md"

[dependencies.quality]
source = "../software-quality"
```

`quality` 是可复用的软件设计、代码品味和性能约束配方。目标环境需要命令行、文件系统、UTF-8、TOML、SHA-256、gzip/tar，以及获取固定 Git 提交的能力；实际实现可以选择提供这些能力的语言和库。Python 是当前参考实现的选择，不是重建目标的强制语言。
