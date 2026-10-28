## 任务：软件到提示词

把下列软件提炼为可以独立交给另一个 Agent 的软件配方。

- 目标：{{target}}
- 用户补充要求：{{request}}

{{context}}

### 工作步骤

1. 阅读可获得的源码、文档、界面和测试，记录本次观察的版本或提交。区分已经验证的行为、推断和未知项；无法访问的内容不要补写成事实。
2. 描述用户目标、输入输出、公开接口、数据格式、状态变化、错误处理、边界条件和运行环境。保存重要的行为与约束，不要求复刻内部实现。
3. 识别直接依赖。区分需要重建的配方依赖、仅供参考的上游资料和实际运行所需的外部工具或服务。依赖声明必须指向具体配方；原始源码仓库先提炼为配方。
4. 编写 `RECIPE.md` 和 `BUILD_PROMPT.md`。`RECIPE.md` 使用唯一的 fenced `toml` 配置块；其余说明使用 Markdown。按需要补充 `ACCEPTANCE.md`、参考说明和 `AGENTS.md`。
5. 对重建所需的每个配方依赖重复上述提炼，直到叶子依赖完整。遇到缺失资料、循环依赖或无法重建的服务，明确列出阻塞原因。
6. 写出可观察的验收条件，覆盖正常行为、失败行为与边界输入；保留来源和许可说明。

### 最小配方格式

创建 `RECIPE.md` 与 `BUILD_PROMPT.md`。将下面唯一的 TOML 配置块放入 `RECIPE.md`，替换示例名称与描述；`BUILD_PROMPT.md` 保存完整重建说明。

```toml
format = "recipkg/1"

[package]
name = "example-software"
version = "0.1.0"
kind = "software"
description = "说明软件用途和主要行为"
entry = "BUILD_PROMPT.md"
```

包名仅用小写字母、数字和短横线，最长 64 字符；版本使用语义化版本。技能包使用 `kind = "skill"`、`entry = "SKILL.md"`，并保留标准 SKILL.md 的 YAML `name`、`description` 文件头。工具环境可用时，可先运行 `recipkg init <directory> --name <name> --kind software` 创建骨架。

本地配方依赖声明示例：

```toml
[dependencies.helper]
source = "../helper"
```

将依赖表放在同一 TOML 块内，不要为每个依赖新建配置块。

### 交付与验收

- 交付可阅读的软件配方及递归依赖；所有包文件必须是 UTF-8 `.md`。
- 不把实现源码、二进制、链接或执行钩子藏进配方。必要的接口约定和测试样例可以用 Markdown 表达。
- 未完成的依赖和不确定行为必须显式列出，不能声称配方已经完整。
- 配方应让未读过原始软件的 Agent 理解“做什么、依赖什么、怎样判断做对了”。
