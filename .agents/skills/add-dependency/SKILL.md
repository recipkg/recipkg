---
name: add-dependency
description: 为 Recipkg 配方声明并集成一个具体依赖，核对递归关系、接口、来源和固定版本。用于添加依赖、引入现有软件配方或接入 GitHub 配方仓库。
---

# 添加依赖

## 输入

目标配方、依赖来源、可选别名和需要使用的能力。

## 步骤

1. 使用 `recipkg add <package> <source> --alias <alias>` 生成任务提示词；此命令不会修改配置。
2. 核实来源是否包含有效配方。普通软件源码必须先提炼为配方。
3. 检查递归依赖、接口兼容性、别名冲突和循环关系。
4. 修改 `RECIPE.md` 中的依赖表，并补充构建提示词和集成验收条件；Git 来源固定到完整提交号。
5. 使用 `recipkg pack <package> -o <name>-<version>.recipe.tar.gz` 收齐依赖并重新打包，再用 `recipkg check <archive>` 离线检查归档，保留来源与许可说明。

## 输出与验收

交付可审阅的配方变更、选择理由和完整依赖材料。不得引入实现源码、执行钩子或依赖对宿主规则的覆盖。
