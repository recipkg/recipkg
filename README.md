# Recipkg · 构方

<img src="assets/recipkg-mark.svg" width="96" alt="Recipkg logo">

**把软件的配方交给 Agent。** Recipkg 管理软件重建提示词、递归依赖和 Agent 技能；软件配方包只包含 UTF-8 Markdown 文件。

[English](README.en.md) · [包格式](docs/SPEC.md) · [设计理念](docs/PHILOSOPHY.md) · [组织命名](docs/ORGANIZATION.md)

> 别写软件了，写提示词吧，未来的人工智能会完整重建它！

这是项目愿景。当前 CLI 的五个主要动作只生成标准化提示词，由你选择的 Agent 完成分析、实现与验收。CLI 不调用模型，不执行生成的软件，也不保证任意软件都能从有限说明中完整重建。

## 安装

需要 Python 3.11 或更新版本。运行时仅依赖 Python 标准库；解析 Git 依赖时需要系统 Git。

克隆本仓库：`git clone https://github.com/recipkg/recipkg.git`。配方、规范和技能是主要输入，生成的 CLI 源码位于`generated/`。

在本仓库目录执行：

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install ./generated
recipkg --help
```

希望直接作为用户全局命令使用时，可运行 `uv tool install ./generated`；命令会安装到用户工具目录。也可以从分发的 wheel 安装。项目尚未承诺已经发布到公共包注册表。

## 先跑一个递归示例

示例的依赖关系是 `hello` 依赖 `greeting`，而 `greeting` 依赖 `text-rules`。三层都是纯 Markdown 配方，没有附带实现源码。

```sh
recipkg check examples/hello
recipkg pack examples/hello -o hello-0.1.0.recipe.tar.gz
recipkg build hello-0.1.0.recipe.tar.gz --output hello-build.md
```

把生成的 `hello-build.md` 交给 Agent。它包含根配方和全部递归依赖的原文，要求 Agent 在独立目录生成实现并执行验收。输出文件已经存在时，`--output` 会拒绝覆盖。

## 重建 Recipkg 自身

`recipes/recipkg/` 是本工具自己的软件配方，包含完整 CLI 行为、包规范、验收条件、中英双语模板和三个内置技能。可以把它作为第一个正式配方包：

```sh
recipkg pack recipes/recipkg -o recipkg-0.1.0.recipe.tar.gz
recipkg build recipkg-0.1.0.recipe.tar.gz --output recipkg-build.md
```

把 `recipkg-build.md` 交给 Agent，即可要求它依据这些材料重建工具。本仓库首版 CLI 使用 Python；配方允许重建者选择其他实现语言。是否满足规格仍须通过实际验收确认。

## 五个主要动作

| 命令 | 输出的提示词要求 Agent 做什么 |
| --- | --- |
| `recipkg extract <software>` | 软件到提示词：观察软件并提炼完整配方 |
| `recipkg build <package>` | 提示词到软件：根据配方和递归依赖生成并验证实现 |
| `recipkg rewrite <package> --request "新要求"` | 先更新配方，再重新实现软件 |
| `recipkg add <package> <source> --alias <name>` | 核实并添加依赖，更新接口和集成验收 |
| `recipkg discover <package>` | 发现依赖、缺失说明和外部运行前提 |

五个命令都支持 `--request "补充要求"`、`--output <new-file.md>` 和 `--template <template.md>`。默认标准输出只有提示词，诊断写入标准错误。`add` 本身不会修改 `RECIPE.md`；`extract` 本身不会下载或阅读给定软件。

除 `extract` 外，`<package>` 可以是本地配方目录、已打包归档，或已安装的 `name@version`。只安装一个版本时也可用 `name`；多个版本不会猜选。需要远程依赖时，先使用 `pack` 或 `install` 收齐材料。

每份提示词都带有 `recipkg-prompt/1` 标识和动作名。自定义模板支持 `{{target}}`、`{{request}}`、`{{source}}`、`{{alias}}`、`{{context}}`；包动作模板必须包含 `{{context}}`，以保留完整依赖材料。

## 配方长什么样

运行 `recipkg init my-app --name my-app` 创建包含 `RECIPE.md`、`BUILD_PROMPT.md`、`ACCEPTANCE.md` 和 `AGENTS.md` 的骨架。把下面唯一的 TOML 块放在 `RECIPE.md` 中：

```toml
format = "recipkg/1"

[package]
name = "my-app"
version = "0.1.0"
kind = "software"
description = "这个软件的用途及主要行为"
entry = "BUILD_PROMPT.md"

[dependencies.greeting]
source = "../greeting"
```

在 `BUILD_PROMPT.md` 中写明行为、接口、环境和约束，在 `ACCEPTANCE.md` 中写出可观察的验收条件。声明了依赖后，其来源必须实际包含有效配方。`init` 生成的是待完善的骨架，不是已经证明可重建的软件规格。

依赖支持相对路径、HTTPS 配方归档，或固定到完整 40 位提交号的 Git 仓库。Git 仓库可以用 `subdir` 指定配方目录；只有源码或普通提示词的仓库需要先整理成 Recipkg 配方。普通依赖不要求做成 Git 子模块：`recipkg pack` 会按固定来源收集递归 Markdown 内容并写入锁文件；构建提示词仍需明确写出每个依赖别名的职责、适用范围和验收方式。详见[包格式](docs/SPEC.md)。

例如在同一工作区复用本仓库的质量配方，可在应用的 `RECIPE.md` 中声明：

```toml
[dependencies.quality]
source = "../software-quality"
```

如果质量配方在独立 Git 仓库，把 `source` 换为 `git`、完整 `rev` 和 `subdir`。然后在应用的 `BUILD_PROMPT.md` 写清 `quality` 约束应用到哪些部分、依赖只提供什么规则，以及如何验收。运行 `recipkg pack <app-recipe> -o <name>-<version>.recipe.tar.gz` 后，依赖会固定在 `.deps/quality/`；生成提示词包含它的完整 Markdown 内容。子模块适合需要同时开发/检出两个源码仓库的工作区，不是让 Agent 获得提示词依赖的必需条件。

## 搜索其他配方

发布 Recipkg 配方的 GitHub 仓库必须添加 `recipkg` topic。保留已有标签，可使用：

```sh
gh repo edit owner/repo --add-topic recipkg
recipkg search
recipkg search "quality" --limit 10
recipkg search "quality" --json
```

`search` 显式访问 GitHub 的公开仓库搜索，按 `topic:recipkg` 筛选，可用 `GH_TOKEN` 或 `GITHUB_TOKEN` 提高请求额度。关键词按普通文本处理；`--limit` 为 1–100，默认 20。JSON 输出是候选数组，含 `repository`、`url`、`description`、`default_branch`；诊断与不完整结果警告写到 stderr。标签不是有效性或信任证明：必须查看实际 `RECIPE.md`、配方子目录、许可证和版本，再用完整提交固定依赖。搜索不会下载实现、安装包或运行内容；没有结果也正常成功，网络失败明确报错。

## 语言

五个提示词动作默认使用英文模板，`--lang zh-CN` 选择简体中文，`--lang en` 显式选择英文，例如：

```sh
recipkg build recipes/recipkg --lang en
recipkg build recipes/recipkg --lang zh-CN
```

语言选项只选择任务模板；根配方、递归依赖、用户要求和自定义模板的原文保持不变，不自动翻译或改写锁定材料。CLI 帮助、诊断和协议标识使用英文。内置公开技能提供中英说明；英文用户可从 [English guide](README.en.md) 和 [English specification](docs/SPEC.en.md) 开始。

## 包操作

```sh
recipkg init my-app --name my-app
recipkg check my-app
recipkg pack my-app -o my-app-0.1.0.recipe.tar.gz
recipkg unpack my-app-0.1.0.recipe.tar.gz unpacked-app
recipkg install my-app-0.1.0.recipe.tar.gz
recipkg list
recipkg build my-app@0.1.0 --output my-app-build.md
recipkg remove my-app@0.1.0
```

`pack` 递归收集依赖到 `.deps/<alias>/`，将每层来源改写为归档内路径，并生成根 `LOCK.md`。锁文件记录文件 SHA-256 与包来源；归档不再依赖原来的本地目录。缺失依赖、循环、非法文件或完整性不匹配都会报错，不静默省略上下文。

默认安装位置是 `$XDG_DATA_HOME/recipkg`，未设置时使用 `~/.local/share/recipkg`。可以通过 `RECIPKG_HOME` 或放在子命令之前的 `--home <directory>` 改写，例如 `recipkg --home ./store list`。安装只保存和校验配方，不运行包内指令。

## 同步技能

内置并可同步安装的公开技能有三个，默认入口为英文，每个目录另有 `SKILL.zh-CN.md` 中文说明：

| 技能 | 作用 |
| --- | --- |
| `migrate-to-recipkg` | 观察现有软件，整理完整配方与依赖 |
| `rewrite-to-recipkg` | 观察、提取配方、建立规范仓库，再按配方重写并验收 |
| `test-feedback` | 模拟目标用户实际走端到端路径，结合本项目和相关项目的 issue 合成需求 |

本仓库开发使用的构建、仓库管理和更新技能位于 `.agents/skills/`，属于项目级工具，不随 CLI 发布。

```sh
recipkg skills list
recipkg skills sync --dest /path/to/your-agent/skills
```

同步包括内置技能、已安装的技能包，以及已安装包中 `skills/<name>/SKILL.md` 形式的内嵌技能。使用你所选 Agent 支持的技能目录；不同 Agent 的目录发现规则由各自实现决定。Recipkg 只管理自己同步的文件，重复同步保持一致，遇到用户修改或冲突会拒绝覆盖。

创建技能配方用 `recipkg init my-skill --name my-skill --kind skill`。`RECIPE.md` 中使用 `kind = "skill"` 和 `entry = "SKILL.md"`；`SKILL.md` 仍保留 Agent Skills 标准的 YAML `name`、`description` 文件头。TOML 只负责包配置。

## 0 代码的范围

`.recipe.tar.gz` 的每个文件必须是 UTF-8 `.md`。包内不含实现源文件、二进制、文件系统链接或执行钩子。工具本身和 Agent 生成的软件可以由代码实现；包协议不绑定实现语言或模型厂商。Markdown 允许配置块、接口说明和输入输出样例，文件检查不会自动证明提示词在语义上足够完整。

## 开发

```sh
RECIPKG_RECIPE_ROOT="$PWD" PYTHONPATH=generated/src python3 -m unittest discover -s generated/tests -v
```

贡献前请阅读 [AGENTS.md](AGENTS.md)。格式变更应同步更新规范、示例和 CLI 的行为验证。

## 许可证

[MIT](LICENSE) · Copyright © 2026 LIghtJUNction.
