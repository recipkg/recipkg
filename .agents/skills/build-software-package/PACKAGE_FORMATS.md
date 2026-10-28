# 软件包格式与生态教程

本清单按“用户拿到什么、从哪里安装”分类。选择前先确认项目是库、CLI、服务、桌面/移动应用、插件还是操作系统镜像；同一个项目可以需要多个交付格式。下列命令是入口，具体参数、签名要求和当前 registry 规则须按官方文档核对。

## 语言生态

| 生态 | 常见交付物与配置 | 构建/验收/发布路径 | 官方资料 |
| --- | --- | --- | --- |
| Python | `pyproject.toml`、sdist `.tar.gz`、wheel `.whl`；纯 Python 通常一份 wheel，原生扩展需平台 wheel | `python -m build` → `twine check dist/*` → 在干净环境安装并导入/运行 → PyPI Trusted Publishing 或授权上传。通常同时发布 sdist 与 wheel | [PyPA 打包教程](https://packaging.python.org/en/latest/tutorials/packaging-projects/)、[格式说明](https://packaging.python.org/en/latest/discussions/package-formats/)、[Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/) |
| JavaScript / TypeScript | `package.json`、npm tarball `.tgz`；CLI 可配 `bin`，库明确入口与导出 | `npm pack --dry-run` 审包 → 项目测试/构建 → `npm publish` 或 GitHub Packages；确认 `files`、`exports`、许可证和 lockfile | [npm package.json](https://docs.npmjs.com/cli/configuring-npm/package-json/)、[npm publish](https://docs.npmjs.com/cli/v10/commands/npm-publish/) |
| Rust | `Cargo.toml`、crate `.crate`、可执行文件 | `cargo package`/`cargo publish --dry-run` → 安装包并运行测试 → 用户明确授权后 `cargo publish`；crate 版本不可覆盖 | [Cargo 发布 crate](https://doc.rust-lang.org/cargo/reference/publishing.html) |
| Go | `go.mod`；模块通常由带语义版本的 Git tag 提供，不是上传一个中心二进制包 | `go test ./...`、`go vet ./...` → tag `vX.Y.Z` → `go list -m` 验证；CLI 另做 OS/架构二进制并附到 Release | [Go Modules 发布](https://go.dev/doc/modules/publishing) |
| JVM (Java/Kotlin/Scala) | JAR、WAR、Maven/Gradle metadata；库与可执行应用的依赖打包不同 | Maven/Gradle 构建和测试 → 验证 POM/metadata、sources/javadoc 与签名 → Maven Central 或私有 Maven registry | [Maven Central](https://central.sonatype.org/)、[Gradle 发布插件](https://docs.gradle.org/current/userguide/publishing_maven.html) |
| .NET | NuGet `.nupkg`、符号包 `.snupkg`、独立/框架依赖应用 | `dotnet pack` → 检查 package metadata → 用临时 feed 或本地源安装验包 → NuGet Gallery / GitHub Packages | [NuGet 创建与发布](https://learn.microsoft.com/en-us/nuget/quickstart/create-and-publish-a-package-using-the-dotnet-cli) |
| Ruby | RubyGem `.gem`、`gemspec` | `gem build` → `gem install --local` 和测试 → RubyGems.org；先核对 gem 文件清单及声明的 Ruby 版本 | [创建 gem](https://guides.rubygems.org/creating_gem/)、[发布 gem](https://guides.rubygems.org/publishing/) |
| PHP | Composer package (`composer.json`)；源代码通常通过带版本的 VCS tag 安装 | `composer validate` → 在干净项目中 `composer require` 验证 → Packagist 或私有 Composer registry；不要手填与 Git tag 冲突的 version | [Composer 库](https://getcomposer.org/doc/02-libraries.md) |
| Swift / Apple 平台 | Swift Package (`Package.swift` + Git tag)、`.xcframework.zip`、`.pkg`、`.dmg`、`.ipa` | `swift test`/build → 校验部署目标、架构与签名 → Swift Package Registry、Apple Developer 分发或 Release；应用签名须保护私钥 | [Swift Package Manager](https://www.swift.org/documentation/package-manager/)、[Apple 分发](https://developer.apple.com/distribute/) |
| Dart / Flutter | Dart package、Flutter 桌面/移动/网页构建产物 | `dart pub publish --dry-run` 和测试 → `dart pub publish`；Flutter 应用按各目标商店的签名与版本规范打包 | [Dart pub 发布](https://dart.dev/tools/pub/publishing)、[Flutter 部署](https://docs.flutter.dev/deployment) |
| R | source package `.tar.gz`/Windows `.zip` | `R CMD build` → `R CMD check` → 按 CRAN/Bioconductor 的政策提交；优先使用其当前官方提交指南 | [R Packages 书](https://r-pkgs.org/)、[CRAN](https://cran.r-project.org/) |
| Julia | Julia package + `Project.toml`、版本 tag、registry entry | `Pkg.test()` → 检查依赖兼容范围 → 依 Julia 注册表流程申请/更新；可额外构建应用二进制 | [Julia Pkg 文档](https://pkgdocs.julialang.org/) |
| Elixir / Erlang | Hex package `.tar`、`mix.exs` | `mix test` → `mix hex.build`/dry-run → Hex.pm；核对文档、许可证、Elixir/OTP 版本 | [Hex 发布任务](https://hexdocs.pm/hex/Mix.Tasks.Hex.Publish.html) |
| Haskell | Cabal source tarball、Hackage package | `cabal sdist` → `cabal check`/测试 → Hackage；检查 `.cabal` 的依赖上下限与 license | [Hackage](https://hackage.haskell.org/)、[Cabal 用户指南](https://cabal.readthedocs.io/) |
| OCaml | opam package description + source archive | `dune build`/`dune runtest` → opam lint/build → 提交 opam repository PR 或私有 opam repo | [opam 打包](https://opam.ocaml.org/doc/Packaging.html) |
| Perl | CPAN distribution archive (`.tar.gz`)、`META.*` | `perl Makefile.PL`/`Build.PL`、`make test` → 生成发行档并验证元数据 → CPAN；现代项目常用 Dist::Zilla | [CPAN](https://www.cpan.org/modules/00modlist.long.html)、[Dist::Zilla](https://dzil.org/) |
| Lua | LuaRocks rockspec、source rock 或 binary rock | `luarocks lint`/`luarocks pack` → 本地安装测试 → LuaRocks.org 或私有 server | [LuaRocks](https://luarocks.org/) |
| C / C++ / Fortran | source archive、共享/静态库、CMake package config、Conan/vcpkg 包 | CMake/Ninja/Make 构建和 CTest → ABI/架构验证 → CPack 系统包、Conan/vcpkg registry、系统仓库或 Release | [CMake 安装与打包教程](https://cmake.org/cmake/help/latest/guide/tutorial/Packaging%20and%20Installing%20Applications.html)、[CPack](https://cmake.org/cmake/help/latest/module/CPack.html) |
| Zig / 其他编译型语言 | 可复现源码包与 OS/架构二进制；是否有中心 registry 取决于生态 | 在声明的 toolchain 下构建 → 每个目标运行 smoke test → 校验和/签名后发布 Release 或对应系统仓库 | 使用语言项目当前的官方发布说明；不要凭旧教程发明一个 registry 流程 |

## 操作系统与桌面应用

| 目标 | 常见格式与入口 | 最低教程路径 | 官方资料 |
| --- | --- | --- | --- |
| Debian/Ubuntu | `.deb` 与 source package；`debian/` 目录、control/rules/changelog | 选 native 或 quilt source package → `dpkg-buildpackage`/`debuild` → `lintian` 与隔离安装测试 → 按目标发行版仓库规则上传 | [Debian Maintainers 指南](https://www.debian.org/doc/manuals/debmake-doc/index.en.html) |
| Fedora/RHEL/openSUSE | RPM `.rpm`、source RPM、`.spec` | 明确 build/runtime dependencies → `rpmbuild`/mock/OBS → 安装与升级测试 → Fedora Copr/OBS/发行版仓库 | [RPM spec 文档](https://rpm.org/docs/latest/manual/spec.html) |
| Arch Linux | `PKGBUILD` → `.pkg.tar.zst`；AUR 是构建脚本仓库，不是二进制镜像仓库 | `makepkg` → `namcap` 和干净容器安装测试 → AUR 提交或自有仓库；版本源与校验和固定 | [Arch 创建软件包](https://wiki.archlinux.org/title/Creating_packages) |
| Alpine Linux | `APKBUILD` → `.apk` | `abuild checksum`/`abuild -r` → Alpine 环境安装测试 → 自有 APK repository 或相应维护流程 | [Alpine 打包](https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package) |
| Nix / NixOS | Nix expression/flake、derivation、binary cache；渠道包括 nixpkgs 或私有 flake | 固定源码与输入 hash → `nix build`、`nix flake check` → 在隔离 store 验证 → 按 nixpkgs 贡献要求提交或发布 flake/cache | [Nix 手册](https://nixos.org/manual/nix/stable/)、[Nixpkgs 贡献指南](https://nixos.org/manual/nixpkgs/stable/) |
| GNU Guix | Scheme package definition、source/binary substitute | `guix build`/`guix lint` → sandbox 构建 → Guix package 提交或自有 channel/substitute | [Guix 手册](https://guix.gnu.org/manual/en/html_node/) |
| Gentoo | ebuild + Manifest，通常由源码构建 | `pkgcheck`/`ebuild` 本地检查 → overlay 安装与升级验证 → Gentoo tree PR 或 overlay | [Gentoo ebuild 文档](https://devmanual.gentoo.org/ebuild-writing/) |
| FreeBSD / BSD | Ports Makefile + distinfo，或 `.pkg` 二进制 package | `portlint`/poudriere 构建 → jail 安装/升级验证 → ports 提交或自有 pkg repository | [FreeBSD Porter's Handbook](https://docs.freebsd.org/en/books/porters-handbook/)、[pkg](https://docs.freebsd.org/en/books/handbook/ports/) |
| macOS | `.app`、`.pkg`、`.dmg`、Homebrew formula/cask、MacPorts Portfile | 区分源码安装与已编译 bottle/签名应用 → Intel/Apple Silicon 验收 → notarization/商店或 Homebrew/MacPorts | [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)、[MacPorts Guide](https://guide.macports.org/) |
| Windows | MSI、MSIX、EXE installer、portable ZIP、winget/Chocolatey/Scoop manifests | 明确每用户/系统安装、升级/卸载、签名和最低 Windows 版本 → 在干净 VM 安装验证 → Release 或所选分发源；installer 可由 WiX、Inno Setup、NSIS 等生成 | [MSIX 概览](https://learn.microsoft.com/en-us/windows/msix/overview)、[WinGet manifest](https://learn.microsoft.com/en-us/windows/package-manager/package/manifest)、[WiX](https://wixtoolset.org/docs/) |
| Linux 桌面通用 | Flatpak、Snap、AppImage | 明确沙箱权限与 runtime → 构建 → 安装、桌面入口、升级和卸载测试 → Flathub/Snap Store/Release | [Flatpak 首个构建](https://docs.flatpak.org/en/latest/first-build.html)、[Snapcraft](https://snapcraft.io/docs/create-a-new-snap/)、[AppImage 指南](https://docs.appimage.org/packaging-guide/overview.html) |

## 移动应用、容器、插件与基础设施

| 类型 | 格式/发布路径 | 需要特别验收的内容 | 官方资料 |
| --- | --- | --- | --- |
| Android | AAB 用于商店分发；APK 可直装/供部分渠道分发 | applicationId、versionCode、签名、arm64/x86 等 ABI、升级覆盖、权限；keystore 放 GitHub Environment secret 或安全签名服务 | [Android 发布准备](https://developer.android.com/studio/publish/preparing)、[AAB 与 APK](https://developer.android.com/guide/app-bundle/faq) |
| iOS/iPadOS | `.ipa`/App Store Connect/TestFlight | Bundle ID、证书/profile、最低系统、设备安装和 TestFlight；私钥不进入 Git | [Apple 分发](https://developer.apple.com/distribute/) |
| OCI 容器 | Docker/Podman image、OCI manifest/index；Dockerfile/Containerfile | 固定基础镜像与依赖、非 root、扫描、SBOM；测试启动/健康接口；按目标构建 `linux/amd64`、`linux/arm64` 等并推 GHCR/Docker Hub | [OCI Image Spec](https://github.com/opencontainers/image-spec)、[Docker GitHub Actions](https://docs.docker.com/build/ci/github-actions/)、[多平台构建](https://docs.docker.com/build/ci/github-actions/multi-platform/) |
| Kubernetes | Helm chart `.tgz`/OCI、Kustomize manifests | `helm lint`/template、安装升级/回滚验证、默认资源和权限；发布 OCI chart 或 chart repository | [Helm Charts](https://helm.sh/docs/topics/charts/) |
| Terraform | Provider platform zip + checksums/signature；module 通常用 Git tag/registry | `terraform fmt -check`, validate, provider acceptance tests、OS/CPU 矩阵；遵循 registry 的 namespace/version/签名布局 | [Terraform provider protocol](https://developer.hashicorp.com/terraform/plugin/which-plugin-protocol)、[Registry 发布](https://developer.hashicorp.com/terraform/registry/providers/publishing) |
| WebAssembly / WASI | `.wasm` module/component、WASI application；可发布到语言 registry、OCI artifact 或应用 Release | 固定 target/ABI/runtime → 编译并验证 import/export 与 capability → 在目标 runtime smoke test → 发布 module 和对应 host/install 说明 | [WASI 文档](https://wasi.dev/)、[WebAssembly component model](https://component-model.bytecodealliance.org/) |
| Serverless / Edge Function | AWS Lambda ZIP 或 OCI image、Azure Functions deployment package、Cloudflare Workers bundle | 区分平台打包器、runtime ABI、handler、依赖与大小限制 → 本地 emulator/dev test → 上传目标 account/stage；凭据、region 和回滚版本分开管理 | [AWS Lambda 部署包](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-package.html)、[Azure Functions 部署](https://learn.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies)、[Cloudflare Workers](https://developers.cloudflare.com/workers/wrangler/) |
| VS Code/IDE 扩展 | VSIX、Marketplace plugin archive | host/runtime compatibility、安装/启用/卸载；先本地安装包测试，再发 Marketplace | [VS Code 扩展发布](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) |
| 浏览器扩展 | Chrome/Firefox/Edge store upload archive | manifest version、权限最小化、签名/审核、干净 profile 安装与升级；渠道流程不同 | [Chrome Web Store 发布](https://developer.chrome.com/docs/webstore/publish) |
| 游戏/内容扩展 | Unity package/UPM、Unreal plugin/plugin archive、Godot Asset Library、游戏专属 mod archive | 核对宿主引擎和游戏版本、license、依赖、资源路径与脚本权限 → clean project 导入验证 → 对应 marketplace、mod portal 或 GitHub Release；不要把引擎缓存与临时构建塞进包 | [Unity package](https://docs.unity3d.com/Manual/Packages.html)、[Unreal 插件](https://dev.epicgames.com/documentation/en-us/unreal-engine/plugins-in-unreal-engine)、[Godot 插件](https://docs.godotengine.org/en/stable/tutorials/plugins/editor/making_plugins.html) |
| GitHub Action | `action.yml` + JavaScript/composite/Docker action、语义化 tags/Marketplace | 测试不同事件、最小 token 权限、不可变 SHA 使用说明、fork PR 无秘密 | [创建和发布 Actions](https://docs.github.com/en/actions/how-tos/create-and-publish-actions) |
| 虚拟机/系统镜像 | ISO、OVA/OVF、QCOW2、VHD/VHDX、cloud image、设备/固件镜像 | 先确认启动固件、磁盘布局、架构、分区、引导链、校验/签名和目标平台；镜像通常很大，放 Release/object storage，不进普通 Git 历史 | [Packer 文档](https://developer.hashicorp.com/packer/docs) |
| 固件/嵌入式设备 | `.bin`、`.hex`、UF2、bootloader/OTA bundle、板卡专用 package | 先确认 MCU/板卡、flash layout、bootloader、签名/防回滚和供电恢复方式；在模拟器和目标硬件分别验证烧录、升级及恢复，然后经厂商 OTA 或 Release 分发 | 使用芯片/板卡厂商当前固件工具链和安全启动文档；不同硬件的格式和烧录流程不可互换 |

## 每个选中格式都要给出的教程

无论格式是否列在上表，都用同一份交付模板补齐：

1. **用途与用户**：这是库、安装器、二进制、镜像还是源码包；终端用户在哪里取得它。
2. **布局与清单**：必需 manifest/recipe、metadata、license、依赖和最终包含文件；列出排除的缓存与开发材料。
3. **本地构建**：前置工具与版本、从干净 checkout 开始的命令、输出目录和可复现输入。
4. **本地验包**：列出包内容；在隔离环境安装、启动、升级/卸载，验证目标 OS/架构；库包做导入/API smoke test。
5. **分发**：registry/store/release 上传入口、标签或版本、签名、校验和、权限和用户安装命令。
6. **CI**：对应 build/test/release workflow；凭据放哪里、job 权限和触发条件。
7. **回滚与故障处理**：如何撤下 pre-release、停发错误版本、修复失败 workflow；对不可覆盖的 registry version 写明处理限制。

对于新出现或小众格式，先找到其维护方的规范和当前发布指南；没有可靠官方资料时明确说明来源质量与未知项，不把相似格式的流程当成事实。
