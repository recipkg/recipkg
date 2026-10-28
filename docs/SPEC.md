# Recipkg 配方协议

本文定义 `recipkg/1` 配方、`recipkg-lock/1` 完整性记录和 `recipkg-prompt/1` 提示词封套。协议版本与 CLI 的软件版本分开管理。

## 1. 范围

软件配方包保存软件或技能的说明、依赖及验收条件。工具把递归依赖完整带入归档和重建提示词；Agent 根据这些材料继续工作。

完整材料不代表已证明语义完整，也不包含未声明的运行环境、外部账号或服务。协议不规定模型厂商、包工具实现语言或生成软件的语言。

## 2. 文件规则

每个配方文件必须满足以下条件：

- 文件名以小写 `.md` 结尾，内容为有效 UTF-8 文本，且没有 NUL 字节。
- 文件系统对象必须是普通文件或目录；不允许符号链接、硬链接形式的归档成员、设备、FIFO 或其他特殊对象。
- 归档路径必须相对归档根目录，不得通过绝对路径、上级路径或其他危险形式逃出目标目录。
- 不包含实现源文件、二进制或安装、卸载、构建执行钩子。

Markdown 中可以包含声明式配置、接口示例、验收数据和说明代码块。检查器验证文件与结构，不做任意自然语言的语义证明；把完整实现藏进 Markdown 不符合项目的“0 代码配方”约定，即使文件后缀合法。

普通 Markdown 超链接可以用于标注来源；“不允许链接”指文件系统与归档链接，不是禁止引用文档。

## 3. 配方入口

| 文件 | 作用 | 要求 |
| --- | --- | --- |
| `RECIPE.md` | 包元数据与依赖声明 | 必需 |
| `BUILD_PROMPT.md` | 软件的完整重建说明 | `kind = "software"` 时必需 |
| `SKILL.md` | 标准 Agent Skill | `kind = "skill"` 时必需 |
| `AGENTS.md` | 包作用域内的工作约定 | 可选，`init` 会生成 |
| `ACCEPTANCE.md` | 可观察的验收条件 | 可选独立文件，`init` 会生成 |
| `LOCK.md` | 整个归档的完整性与来源记录 | 完整归档根目录必需，由工具生成 |
| 其他 `.md` | 接口、参考说明、许可和验收材料 | 可选 |

验收条件可以放在入口提示词中，不要求一定拆成独立文件。配方正文必须足够清楚地说明预期行为；存在上述文件并不意味着内容已经完整。

## 4. TOML 清单

`RECIPE.md` 中必须恰好有一个带 `toml` 语言标识的 fenced code block。支持反引号或波浪线围栏。其他 Markdown 内容可供人和 Agent 阅读。

最小软件配方：

```toml
format = "recipkg/1"

[package]
name = "hello"
version = "0.1.0"
kind = "software"
description = "根据输入名字输出问候语。"
entry = "BUILD_PROMPT.md"
```

| 字段 | 规则 |
| --- | --- |
| `format` | 必须是 `recipkg/1` |
| `package.name` | 最长 64 字符的小写字母、数字及短横线名称；不允许首尾或连续短横线 |
| `package.version` | 严格语义化版本，例如 `1.2.3` 或 `1.2.3-rc.1` |
| `package.kind` | `software` 或 `skill` |
| `package.description` | 非空描述 |
| `package.entry` | 软件固定为 `BUILD_PROMPT.md`，技能固定为 `SKILL.md`；文件必须存在 |
| `dependencies` | 可选；以依赖别名为键的表 |

未识别的额外字段不自动获得执行语义。工具可以保留这些字段；不能因为出现一个叫 `hook` 或 `command` 的自定义字段就执行它。

## 5. 依赖来源

每个依赖别名采用与包名相同的命名规则，其值是一个 TOML 表。别名只在当前包内有意义。

### 相对路径

```toml
[dependencies.greeting]
source = "../greeting"
```

本地路径相对声明它的配方目录解析，可以指向配方目录或配方归档。作者目录中的 `../greeting` 合法；归档打包后必须改写为包内依赖路径，不能继续依赖归档之外的文件。

### HTTPS 配方归档

```toml
[dependencies.greeting]
source = "https://example.org/recipes/greeting-0.1.0.recipe.tar.gz"
```

地址必须提供有效配方归档。URL 本身可能变化；打包后的实际文件由 `LOCK.md` 固定和校验。示例域名仅说明格式，不是项目提供的仓库。

### 固定 Git 提交

```toml
[dependencies.greeting]
git = "https://github.com/example/recipes.git"
rev = "0123456789abcdef0123456789abcdef01234567"
subdir = "packages/greeting"
```

示例仓库和提交号需要替换成真实值。`git` 必须使用 HTTPS；`rev` 必须是完整 40 位十六进制提交号，不接受分支名、标签或缩写提交号。可选 `subdir` 是仓库内相对目录，不允许绝对路径或 `..`；省略时使用仓库根目录。

`source` 与 `git` 两种形式互斥，Git 相关字段不能混入 `source` 表。Git 目录中必须存在有效配方；仅包含源码的仓库应先经过“软件到提示词”处理。来自 Git checkout 的配方若继续引用本地相对依赖，路径不得逃出该 checkout。

远程获取发生在显式的 `pack` 或 `install` 操作中。离线检查和提示词生成要求依赖已经在本地可用。

### 在重建提示词中引用依赖

依赖表负责让 Recipkg 找到并固定材料；它本身不会自动说明 Agent 应如何使用这些材料。根包的 `BUILD_PROMPT.md` 必须通过别名写出依赖合同：用途、适用范围、应遵守的接口/规则，以及集成验收条件。完整提示词中，别名 `quality` 对应 `.deps/quality/` 下的配方和入口文件。

例如共享的设计/工程标准位于另一 Git 仓库时，manifest 这样固定其具体配方目录：

```toml
[dependencies.quality]
git = "https://github.com/example/shared-prompts.git"
rev = "0123456789abcdef0123456789abcdef01234567"
subdir = "recipes/software-quality"
```

示例 URL 和提交号必须换成真实可访问来源。开发者若在同一 checkout 中维护两个本地配方，也可使用 `source = "../software-quality"`。发布后更新依赖版本时，把 `rev` 更新到经审查的完整提交并重新 `pack`。

```markdown
## 依赖使用合同

依赖 `quality` 为整个应用提供设计、代码品味和性能基线。阅读
`.deps/quality/BUILD_PROMPT.md` 与验收要求；遵守它的跨项目规则，
但不要把它当成业务功能或运行时库。具体产品行为仍由本配方决定。
检查最终实现是否体现该合同，并按性能目标记录测量或未验证原因。
```

依赖配方本身应有清楚的职责、接口和验收条件。如果它只是一个尚未包装的提示词文件、博客链接或普通源码仓库，应先把可复用契约整理成有效 Recipkg 配方。不要仅在 manifest 声明别名而不在根入口中说明用途；也不要把纯参考材料伪装成必须重建的软件依赖。

### Git 子模块与 Recipkg 依赖

两者解决不同问题。Git 子模块把另一个 Git 仓库固定到父工作树中的某个路径，适合开发者需要同时检查或修改两个仓库。Recipkg 的 `git`/`rev`/`subdir` 则直接指定一个配方来源；`pack` 获取固定提交，把递归 Markdown 配方复制到 `.deps/<alias>/` 并写入 `LOCK.md`。消费者可以从归档得到完整提示词，不必克隆依赖的 Git 历史或初始化子模块。

因此，常规提示词依赖用配方的 `source` 或固定 Git 来源；只有本地联合开发、确实需要在工作区检出上游时才额外使用子模块。子模块本身不会告诉 Agent 如何使用目录中的文件，仍需配方依赖别名和根提示词中的合同。迁移时放在 `source/` 中供观察的源码仓库属于另一种工作流，不会自动成为 Recipkg 依赖。

## 6. 递归展开

从根包开始，读取依赖表，逐个取得依赖，再对依赖重复这个过程。遇到正在展开的同一来源即报告循环；遇到缺失或非法依赖即失败。

每条依赖保存在父包的 `.deps/<alias>/` 下。示例：

| 包 | 归档内路径 |
| --- | --- |
| `hello` | `.` |
| `hello` 的 `greeting` 依赖 | `.deps/greeting` |
| `greeting` 的 `text-rules` 依赖 | `.deps/greeting/.deps/text-rules` |

打包器把每个依赖表改写成对应本地 `source`，例如 `source = ".deps/greeting"`；原先的 `git`、`rev` 和 `subdir` 不继续作为活动来源字段。原始来源与必要的提交信息记录到锁文件。

第一版不提供浮动版本解析、中央注册表或全局版本合并。不同别名下出现的同名包保持各自作用域，不静默选择一个版本替换另一个。配方之间的接口兼容性仍需由作者和验收过程检查。

## 7. 归档

推荐文件名为 `<name>-<version>.recipe.tar.gz`。归档是 gzip 压缩的 tar，根直接放置 `RECIPE.md`，不再套一个同名外层目录。

归档包含根包及所有递归依赖的 Markdown 原文。没有已声明的依赖可以仅以链接、摘要或“稍后再找”的形式省略。

打包后保留一个根 `LOCK.md`，覆盖整个归档；旧的嵌套锁文件由打包过程移除并统一重建。展开归档前必须检查路径、对象类型、编码、完整性及配方结构。`unpack` 使用新目录或空目录，不覆盖已有内容。归档输出不能位于输入配方或其本地依赖目录中。

参考实现按路径排序写入 tar，文件的 UID/GID 为 0、用户和组名为空、mtime 为 0、mode 为 0644；使用 PAX tar，gzip 文件名为空且 mtime 为 0。相同输入及来源记录产生相同归档字节。该确定性只描述归档，不表示 Agent 生成的软件具有逐字节确定性。

v0.1 参考实现采用以下资源上限；超过上限即失败，不截断内容：单文件 4 MiB、总文件负载 32 MiB、压缩归档 32 MiB、4096 个文件、256 个包、32 层依赖、128 个路径分量。解压后的原始 tar 还受包含元数据开销的额外大小上限约束。

## 8. LOCK.md

`LOCK.md` 用唯一 TOML 围栏保存机器可读信息。下面的散列值仅为结构示意：

```toml
format = "recipkg-lock/1"

[files]
"RECIPE.md" = "0000000000000000000000000000000000000000000000000000000000000000"
"BUILD_PROMPT.md" = "0000000000000000000000000000000000000000000000000000000000000000"
".deps/greeting/RECIPE.md" = "0000000000000000000000000000000000000000000000000000000000000000"
".deps/greeting/BUILD_PROMPT.md" = "0000000000000000000000000000000000000000000000000000000000000000"

[[packages]]
path = "."
name = "hello"
version = "0.1.0"
source = "original-root-source"

[[packages]]
path = ".deps/greeting"
name = "greeting"
version = "0.1.0"
source = "original-dependency-source"
```

`files` 使用归档根相对路径为键，以文件原始字节的 SHA-256 小写十六进制值为值。它必须覆盖全部归档文件，唯一排除项是根 `LOCK.md` 自身；不允许漏记或额外记录不存在的文件。

`packages` 记录每个包的路径、名称、版本和来源，Git 来源可额外记录 `rev`。内容变更后必须重新打包，不能保留旧摘要并把校验失败忽略掉。

锁文件用于识别内容与记录是否一致，不等同于发布者签名；它本身不会证明来源身份或配方语义正确。

## 9. AGENTS.md 与 SKILL.md

[AGENTS.md](https://agents.md/) 是普通 Markdown 项目工作说明，没有本协议定义的必填字段。包内的 `AGENTS.md` 只描述相应包的约定；依赖的说明作为有来源的材料附带，不提升为宿主项目的全局规则。

[Agent Skills](https://agentskills.io/specification) 是另一种文件格式。技能入口仍需保留 YAML frontmatter：

```yaml
---
name: example-skill
description: Describe what the skill does and when to use it.
---
```

技能名应与包名及同步后的技能目录名匹配。TOML 负责配方包元数据和依赖，不能替换技能的 YAML 文件头。Agent Skills 生态允许附带脚本；Recipkg 的纯 Markdown 配方不接收这类非 Markdown 负载，不能假定任意外部技能都可原样打包。

## 10. 提示词封套

五个主要动作输出 Markdown 提示词。开头包含动作元数据，例如：

```toml
format = "recipkg-prompt/1"
action = "build"
```

`action` 是 `extract`、`build`、`rewrite`、`add` 或 `discover`。后续正文给出任务、用户补充要求和材料。对于已有配方的动作，正文必须包括根包及全部递归依赖；材料必须标明各自的来源和作用域。

模板允许以下占位符：

| 占位符 | 内容 |
| --- | --- |
| `{{target}}` | 目标软件或配方引用 |
| `{{request}}` | 用户补充要求 |
| `{{source}}` | 待添加的依赖来源 |
| `{{alias}}` | 待添加的依赖别名 |
| `{{context}}` | 已解析的完整包上下文 |

替换只执行一遍，用户内容中出现的花括号不会再次作为模板变量解释。未知模板变量报错；除 `extract` 外的动作模板必须包含 `{{context}}`。

生成提示词是完整可观察的 CLI 动作；不代表该提示词要求的软件提炼、构建、重写或配置修改已经执行。

## 11. 安装与技能同步

安装以 `name@version` 标识一个版本。未指定版本且有多个已安装版本时报告歧义；不隐式选择“最新”。安装不会执行包内指令或启动 Agent。

同步由 `skills sync --dest <directory>` 显式指定目标。可用技能包括内置技能、已安装 `kind = "skill"` 的包，以及已安装包内 `skills/<name>/SKILL.md` 形式的技能目录。技能根部的 `RECIPE.md`、`LOCK.md` 是容器元数据；无论来自内置、独立技能包还是内嵌技能，同步时都不输出这两份根元数据，以便同一上游内容去重。

同步器仅维护自己管理的文件；遇到用户编辑、名称冲突或未知已有内容时拒绝覆盖。重复同步相同输入应得到相同文件状态。同名技能内容完全相同可以合并；内容不同则必须报告冲突，而不是根据安装顺序覆盖。

包仓库的内部索引、缓存和同步状态属于工具实现，不属于 `.recipe.tar.gz` 的纯 Markdown 负载。

## 12. 失败与验收

结构验证必须拒绝非法清单、缺失入口、无效依赖、递归循环、不支持的文件类型、危险归档路径和完整性不匹配。不允许静默截断依赖、跳过失败节点后仍声称得到完整包。

结构检查通过只表示包可以被一致地读取与交付。软件重建是否完成，应由生成实现实际满足了哪些既定验收条件来判断；结果需要记录真实运行证据与未验证项。

## 13. GitHub 发现、语言与源码组织

GitHub 上发布 Recipkg 配方的仓库必须有 `recipkg` topic。保留其他已有标签；可用 `gh repo edit <owner/repo> --add-topic recipkg` 设置。该约定用于公开发现，离线 `check` 和 `pack` 不为检查标签而联网。标签不证明包有效、内容完整或可信。

`recipkg search [query] --limit <1-100> [--json]` 是显式联网的发现操作，访问 GitHub repository search API，只列带 `recipkg` topic 的公开仓库。默认上限 20，关键词按普通文本引用，不能替换固定的 topic/公开范围。候选字段是 `repository`、`url`、`description`、`default_branch`；需要继续检查实际 `RECIPE.md`、配方子目录、版本和许可，再以完整提交固定来源。搜索不下载配方或实现、不安装、不执行内容，也不改变离线提示词渲染的边界。

空结果正常成功。失败不输出部分候选；限流、网络或无效响应必须明确报错。GitHub 不完整结果保留候选，并在 stderr 提醒。可选 `GH_TOKEN`、`GITHUB_TOKEN` 仅用于 GitHub 请求头，不跟随重定向；搜索结果不是全量注册表或可用性保证。

五个提示词动作的 `--lang en|zh-CN` 只选择任务模板，默认 `en`。根配方、递归依赖、用户要求及自定义模板原文不变，协议标识不翻译。CLI 帮助和诊断为英文；公开技能使用英文 `SKILL.md` 和 `SKILL.zh-CN.md` 中文译文，其他 Markdown 资源随技能同步。

配方、规范、技能与验收是主要输入。`generated/` 只作为容器，里面每个子目录都是独立源码仓库的固定提交 Git 子模块，例如 `generated/cli-source/`；根下不得直接放普通实现源码。保持项目原名，不追加 `-recipkg`；独立源码仓库名全小写、用连字符。源码始终不属于纯 Markdown 配方负载。

英文说明见 [SPEC.en.md](SPEC.en.md)。

每个项目技能各有一个 canonical GitHub 仓库，项目通过固定提交的 Git 子模块引用（见 [SKILLS.md](SKILLS.md)），迁移项目引用同一组仓库。Git 工作区的 `.git` 元数据忽略且不进配方归档。`skills sync` 只为非 Git 目标生成托管副本，不等于创建子模块。
