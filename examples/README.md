# 递归配方示例

这个示例只有 UTF-8 Markdown 文件，未包含任何语言的实现。

| 配方 | 职责 | 直接依赖 |
| --- | --- | --- |
| `hello` | 一个输出问候语的命令行软件 | `greeting` |
| `greeting` | 根据名字生成问候语 | `text-rules` |
| `text-rules` | 规范化名字中的空白 | 无 |

在仓库根目录执行：

```sh
recipkg check examples/hello
recipkg pack examples/hello -o hello-0.1.0.recipe.tar.gz
recipkg build hello-0.1.0.recipe.tar.gz --output hello-build.md
```

最后一个命令生成完整重建提示词。将 `hello-build.md` 交给一个能读写文件和运行检查的 Agent，由它选择实现语言、生成软件并逐项验收。

示例预期的递归层次为 `hello`、`.deps/greeting`、`.deps/greeting/.deps/text-rules`。归档独立于原始三个示例目录；复制归档后仍然包含每一层重建说明。
