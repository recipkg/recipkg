# Recipkg 0.1 CLI 行为契约

## 通用规则

命令入口为 `recipkg`。`--help` 显示帮助并退出 0；`--version` 输出 `recipkg 0.1.0` 并退出 0。成功退出 0，参数、输入、文件或验证错误退出 2，并向 stderr 输出可理解的原因。向已关闭的管道输出不应产生用户可见堆栈。

全局 `--home <directory>` 放在子命令前。安装仓库路径优先级为：`--home`、`RECIPKG_HOME`、`$XDG_DATA_HOME/recipkg`、`~/.local/share/recipkg`。不需要注册账号或模型凭据。

配方引用先匹配存在的本地路径；否则匹配已安装的 `name@version`。省略版本时，只有一个候选才可使用；零个或多个候选都报错。提示词生成和 `check` 不直接接收待下载的远程引用，应提示先 `pack` 或 `install`。

## 五个提示词动作

| 标准命令 | 同义命令 | 位置参数 |
| --- | --- | --- |
| `extract` | `software-to-prompt` | `<target>` |
| `build` | `prompt-to-software` | `<package>` |
| `rewrite` | `rewrite-software` | `<package>` |
| `add` | `add-dependency` | `<package> <source>` |
| `discover` | `discover-dependencies` | `<package>` |

每个动作接受 `--request <text>`、`--output <file>`（简写 `-o`）与 `--template <file.md>`。`add` 还接受 `--alias <name>`，默认 `dependency`，别名使用协议的名称规则。

没有 `--output` 时 stdout 只有生成的 Markdown 提示词。有输出路径时，创建其父目录并写入新文件；如果文件已存在就报错，不覆盖。成功写入的提示可到 stderr，stdout 不混入状态文字。

默认模板为本包 `templates/` 中对应动作的原文。自定义模板必须是有效 UTF-8 `.md` 且无 NUL，只允许 `target`、`request`、`source`、`alias`、`context` 五个双花括号占位符。空白可以出现在占位符内部。除 `extract` 外必须包含 `context`；未知变量失败。只替换一遍，插入文本中的花括号保持字面内容。

没有补充要求时使用 `No additional requirements.`。`extract` 没有包上下文，使用 `No package context is attached; inspect the supplied source during the task.`。其他动作的 `context` 包含完整递归材料。

输出先写标题 `# Recipkg Prompt`，然后是唯一用于封套的 TOML 块，其中 `format = "recipkg-prompt/1"`、`action` 为标准动作名，再写替换后的模板正文，结尾一个换行。模板正文或材料中的其他 TOML 块不属于封套元数据。

上下文需要有根包身份、按路径排序的文件索引，以及标有相对路径的每个文件原文；包含已经展开的依赖与根锁文件。具体标题文字无需逐字节照抄，但不得丢失材料或把依赖说明提升为全局指令。

`extract` 不下载、不读取目标源码，只生成提炼任务。`add` 不修改清单、锁文件或已安装内容，只生成添加依赖任务。所有动作均不调用模型、不执行生成软件，默认不修改输入。

## 配方操作

| 命令 | 参数与行为 |
| --- | --- |
| `init <path>` | `--name <name>` 默认取目录名；`--kind software\|skill` 默认 software。要求新目录或空目录，拒绝链接。创建版本 0.1.0 的有效骨架。 |
| `check <source>` | 离线验证根包、递归依赖、格式和可用锁信息；不下载远程材料。 |
| `pack <source> -o <archive.recipe.tar.gz>` | `--output` 与 `-o` 同义且必填。收齐递归依赖、校验并生成独立归档。输出不得覆盖已有文件或位于源包及其依赖内。 |
| `unpack <archive> <destination>` | 先完整校验，再解包到新目录或空目录，不覆盖已有内容。 |
| `install <source>` | 接收本地配方、归档或 HTTPS 配方归档；必要时获取声明的远程依赖，校验后安装。 |
| `list` | 按稳定顺序列出已安装版本的名称、版本、类型和描述。 |
| `list --json` | 输出对象数组，每项含 `name`、`version`、`kind`、`description`。 |
| `remove <name[@version]>` | 只删除明确解析到的已安装版本，不接收任意文件系统路径。多个版本时必须指定版本。 |

`init` 创建 `RECIPE.md`、`AGENTS.md`、`ACCEPTANCE.md` 及相应入口：软件用 `BUILD_PROMPT.md`，技能用 `SKILL.md`。内容必须提醒作者继续完善行为与验收，不能把骨架描述为已验证产品。

安装内容以 `<home>/packages/<name>/<version>/` 保存。同一身份与内容重复安装保持不变；同一身份却内容不同报错，要求调整版本或显式移除旧版本。不把原始来源记录变化单独当作软件内容变化。安装失败不能破坏已有版本。

HTTPS 来源必须无内嵌账号密码和 fragment，不能降级到 HTTP。Git 依赖遵守 `SPEC.md` 的固定提交规则；不得执行 hooks、子模块或用户自定义过滤器。外部 Git 不可用或来源不可访问时清楚报错，不静默跳过依赖。

## 技能

| 命令 | 行为 |
| --- | --- |
| `skills list` | 按名称稳定排序列出全部可同步技能。 |
| `skills sync --dest <directory>` | 必须显式指定目标，检查冲突后同步托管技能。 |

技能来源有三种：本工具内置的 `migrate-to-recipkg`、已安装 `kind = "skill"` 配方、已安装包中的 `skills/<name>/SKILL.md`。开发辅助技能属于源码仓库的 `.agents/skills/`，不随 CLI 安装或同步。独立技能包同步时移除根 `RECIPE.md` 与根 `LOCK.md` 容器元数据，其余纯 Markdown 材料保留。内嵌技能目录的名称须与其 YAML `name` 一致。

同名同内容可以合并；同名不同内容失败。技能的 `name` 和 `description` 必须是有效 YAML 字符串，保留原始文件。支持普通、单引号、双引号及常用块标量写法；名字遵守协议名称规则，描述非空且最长 1024 字符。

同步状态可使用目标目录下的 `.recipkg-skills.toml`，标识 `recipkg-skills/1`，通过 `[files]` 记录 `<skill>/<path.md>` 的 SHA-256。它是工具的本地托管状态，不属于纯 Markdown 配方负载。

执行前检查所有将涉及的文件。用户修改了托管文件、在托管技能中新增未知文件或目录、同名目录不属于本工具时，拒绝覆盖并保留现场。无关技能与文件不受影响。重复同步相同输入保持一致。已移除技能可以在下一次同步清理其仍未被用户修改的托管内容；文件更新中失败时恢复先前状态。

## 资源与分发

安装后的工具必须自带五个模板与唯一内置技能 `migrate-to-recipkg`，离开源码 checkout 仍能运行。包格式、提示词格式与生成软件语言没有绑定。各命令帮助应解释“输出提示词”和“执行任务”的区别。
