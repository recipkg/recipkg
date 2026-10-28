# Recipkg reference CLI

This directory contains the replaceable Python reference implementation of [Recipkg](https://github.com/recipkg/recipkg). Requirements, recipe specifications, public skill sources, and examples are maintained in the parent recipe repository. This code is a replaceable implementation of that contract.

Python 3.11+ is required; runtime dependencies are standard-library modules only. Git is needed to fetch pinned Git recipe sources.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install .
recipkg --help
recipkg search --limit 10
recipkg extract /path/to/software --lang en
recipkg extract /path/to/software --lang zh-CN
recipkg skills list
```

The five action commands print prompts, without calling a model or executing software. `search` explicitly queries public GitHub repositories with the `recipkg` topic; candidates still need recipe validation. Prompt language changes the task template, never the original recipe material. Public skills include English and Simplified Chinese instructions.

## Local verification

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

For integration acceptance against the canonical recipe, set `RECIPKG_RECIPE_ROOT` to its checkout. Without that checkout, the recipe-resource integration test is explicitly skipped; the remaining tests are self-contained and offline.

```sh
RECIPKG_RECIPE_ROOT=/path/to/recipkg PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Do not hand-maintain competing template/skill requirements here: update `recipes/recipkg/` in the canonical repository, then refresh the packaged `src/recipkg/data/` resources. See the [English guide](https://github.com/recipkg/recipkg/blob/main/README.en.md) and [specification](https://github.com/recipkg/recipkg/blob/main/docs/SPEC.en.md).

## 中文

这是 Recipkg 的可替换 Python 参考实现，放在主仓库的 `generated/` 目录。需求、规范、公开技能和示例以 [主仓库](https://github.com/recipkg/recipkg) 为准。修改配方后同步打包资源，并在本机运行测试；测试通过不等于独立重建或所有平台验收通过。
