# 标准化的软件项目布局

标准化是让人知道文件在哪里、如何构建测试和发布；不是所有语言都长得一样。先识别生态与包边界，再选最贴切的常见约定。

## 通用单包项目

```text
project/
├── README.md
├── LICENSE
├── CHANGELOG.md              # 采用时由实际发布历史维护
├── CONTRIBUTING.md           # 有外部贡献流程时
├── SECURITY.md               # 项目接受漏洞报告时
├── .gitignore
├── .editorconfig              # 团队需要统一格式时
├── <manifest-and-lockfile>
├── src/                       # 源码（按语言惯例，可选）
├── tests/                     # 或生态指定目录
├── docs/                      # 用户文档，不重复 README
├── examples/                  # 可运行、维护的示例
├── scripts/                   # 项目维护脚本
├── .github/
│   ├── workflows/
│   └── ISSUE_TEMPLATE/        # 维护者确实使用时
└── build-output/              # 本地生成，不进 Git
```

LICENSE 类型由项目 owner 决定；不能为了“标准布局”擅自加许可证。README 至少要与实际构建和安装方式一致。

## 生态惯例示例

| 生态 | 常见骨架 | 注意 |
| --- | --- | --- |
| Python | `pyproject.toml`, `src/<package>/`, `tests/`, `docs/` | 使用 src layout 时确保测试安装真实包，不只从仓库根目录隐式导入 |
| Node/TypeScript | `package.json`, lockfile, `src/`, `test/` 或 `tests/`, `tsconfig.json` | `node_modules`, `.next`, `dist`, cache 不入 Git；检查 `files` 和 exports 确认发布包内容 |
| Rust | `Cargo.toml`, `Cargo.lock`（应用常提交；库看生态约定）, `src/`, `tests/`, `examples/` | workspace root 和每个 crate 职责清楚 |
| Go | `go.mod`, package dirs, `cmd/<binary>/`（多个 CLI）, `internal/`, `pkg/`（只在确有公开 API 时） | 避免无理由建 `pkg/`；module path 与仓库 URL一致 |
| JVM | `src/main`, `src/test`, `pom.xml`/`build.gradle`, parent/workspace config | 多模块各有独立责任，版本与发布 metadata 清楚 |
| .NET | `src/`, `tests/`, `.sln`, `.csproj`, `Directory.Build.*`（多项目时） | 区分应用与可独立发布的 libraries |
| Ruby | `lib/<gem>/`, `test/`/`spec/`, `.gemspec`, `Gemfile` | gemspec 文件清单与发布内容一致 |
| PHP | `src/`, `tests/`, `composer.json` | namespace/autoload 与目录保持一致 |
| C/C++ | `CMakeLists.txt`, `include/`, `src/`, `tests/`, `cmake/`, `examples/` | 明确 public headers、ABI 与 install/export rules |
| Web app | `src/`, `public/`, e2e/tests, lockfile, build config | 上传用户维护的 source/assets；把编译输出、浏览器缓存和录屏排除 |
| Monorepo | `apps/`, `packages/`, workspace root manifest/lockfile, `docs/` | 每个成员的发布边界、依赖方向、CI 路径过滤和独立 README 明确 |

## 前端专门规则

- `.gitignore` 至少处理 node modules、framework build output、test reports、coverage、cache、local env、logs；以实际框架生成规则为准。
- 用 package manager lockfile 重现依赖；不要提交 `node_modules`、包管理器 cache、`.next/cache` 或浏览器自动下载缓存。
- 公开源代码通常不用 Git LFS。检查高分辨率原图、视频、录屏、音频、地图/3D 模型和 `.map` source map；压缩/转换到 web 所需版本并把授权源资产放在合适位置。
- 客户端构建变量会进入浏览器 bundle；不把秘密当作前端环境变量。用 `NEXT_PUBLIC_` 等前缀的值预期对用户可见。
- 生成 API client、静态网站、storybook 或 coverage：确认它是必要源码、发布 Pages 输出、还是可重建工件。只把应分发的产物放 artifact/Release/部署存储。
- `.npmignore`、`package.json#files` 和 workspace 设置可能覆盖/改变默认包清单；执行 dry-run 并检查 tarball 清单。

## 单一真相源与子模块

同一规范、技能、源代码或配置不要在多个仓库里手工维护多个副本。若它需要独立版本、被多个项目引用并由上游维护，优先用 Git 子模块 pin 到已审阅的 commit；父仓库只记录 commit 指针，升级时显式审查并提交指针更新。参见 [Git 子模块参考](https://git-scm.com/docs/gitsubmodules)。

若只是语言库依赖，使用该生态 registry 和 lockfile；子模块不会自动提供版本兼容约束、安全更新或依赖解析。
