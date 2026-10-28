# Hello 软件配方

一个可由任意适合目标环境的编程语言实现的小型命令行程序。

```toml
format = "recipkg/1"

[package]
name = "hello"
version = "0.1.0"
kind = "software"
description = "读取一个可选名字，输出确定的英文问候语。"
entry = "BUILD_PROMPT.md"

[dependencies.greeting]
source = "../greeting"
```

根配方只规定命令行行为；问候语生成和名字规范化分别由递归依赖规定。
