# US-001 技术研究与决策

日期：2026-11-01。依据 [spec](spec.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0 及四份 0.2 主文档。
本阶段仅阅读代码、分派只读研究、查询 Context7 和官方资料；未安装项目依赖、运行收录脚本或执行 PoC。
以下是实施候选已收敛的设计，库的组合效果仍须在实施阶段验证，不能据此宣称验收通过。

## R-01：原件、记录与派生产物分离

- **Decision**：保留现有 skills 原件路径，以 catalog/<slug>.json 显式列出收录项。文件先读取为 Buffer 快照，原件副本、摘要和 ZIP 使用同一份字节；仅派生文本参与解析、搜索和展示。
- **Rationale**：现有 build-index 手写 YAML，markdownToText 会移除代码围栏内容；app 又用有损 content 重建导出。换索引格式而不分离下载源不能解决问题。显式 catalog 还可避免递归扫描误收录未跟踪 office2md。
- **Alternatives considered**：继续从 search-index 迁移正文会丢失内容；统一重写为目录 SKILL.md 会破坏原路径；把图库字段写回 frontmatter 会污染第三方原件，均不采用。
- **追溯**：DEC-002、DEC-003、DEC-009；FR-001、FR-004、FR-011。

## R-02：YAML 与元数据边界

- **Decision**：采用 yaml 2.9.1，使用 Document API 仅读取 frontmatter。处理 BOM、LF/CRLF 和准确的首尾分隔行；没有 frontmatter 时允许由完整图库记录提供显示名称和简介。存在但非法的 YAML 不能被记录覆写掩盖。
- **Rationale**：成熟解析器支持折叠、多行、嵌套与未知扩展。使用 YAML 1.2 core schema、严格解析、字符串键、重复键检查，不注册自定义 tag；检查 errors，并限制别名展开 maxAliasCount=100。只提取约定字段，未知字段依靠原始字节保留，不将整棵扩展对象传播到页面。
- **Alternatives considered**：不继续 split(':')；不使用把标量全部转字符串的 failsafe；不另引 gray-matter，因为首段边界识别和 YAML 解析已经足够。不得调用 stringify 重建原件。
- **来源**：[精确版本 options](https://github.com/eemeli/yaml/blob/v2.9.1/docs/03_options.md)、[Document API](https://github.com/eemeli/yaml/blob/v2.9.1/docs/04_documents.md)、[包元信息](https://registry.npmjs.org/yaml/2.9.1)；已用 Context7 library → docs 查证。

## R-03：安全展示与本地引用

- **Decision**：构建端采用 marked 18.1.2 渲染，再用 sanitize-html 2.18.1 严格清理。对清理后的 a[href]/img[src] 再做引用收集与映射；沿用 sanitize-html 的解析与 transformTags，不再增加 HTML parser。
- **Rationale**：渲染与清理分开；真实 Markdown、引用式链接及允许展示的 HTML 链接均可处理，代码围栏、行内代码、注释及已移除活动标签不会误判附件。目录内每个 Markdown 文件均校验引用，详情只展示主文档。
- **边界**：仅 http/https 外链，不发网络请求；本文锚点按 [C-04](contracts/static-site.md#heading-anchors) 生成受控标题 ID/别名并定位，保留技能 Hash。相对路径仅解码一次，去 query/fragment 后按所在 Markdown 目录解析，只能命中该 Skill 文件清单。缺失或越界的真实本地引用是整次构建的致命错误，沿用已确认澄清 A。
- **交付安全**：原始 HTML/SVG 附件不直接作为网页或 iframe 打开。附件原字节以无活动扩展名的 .bin 资源分发，通过 fetch → application/octet-stream Blob → 原名下载；仅对实际被图片引用的已准入栅格资源另生成媒体副本。SVG 图片位置提供附件下载入口。manifest 保留原路径映射，ZIP 内路径不变。
- **Alternatives considered**：不在浏览器运行未锁版本 marked CDN；不把 Markdown 直接塞 innerHTML；不通过正则扫描代码中的“链接”；不直接公开活动 HTML/SVG 原路径。浏览器 download 属性单独不足以充当安全边界。
- **来源**：[Marked 官方文档](https://marked.js.org/using_pro)、[sanitize-html 官方 README](https://github.com/apostrophecms/apostrophe/blob/main/packages/sanitize-html/README.md)、[marked 元信息](https://registry.npmjs.org/marked/18.1.2)、[sanitize-html 元信息](https://registry.npmjs.org/sanitize-html/2.18.1)；已通过 Context7 查证并核对官方仓库。清理器保留 decodeEntities=true，禁止脚本、事件、style、iframe、data/blob/javascript URL。

## R-04：完整目录包与文件准入

- **Decision**：采用 yazl 3.3.1 生成 ZIP，yauzl 3.4.0 仅用于独立解包验收。目录包保留原目录根、相对路径、空目录、许可和二进制字节；单文件直接下载原名 .md。
- **Rationale**：使用已验证的 Buffer 快照打包，等待流完成才能认定成功。文件清单和解包逐文件字节是保真证据；ZIP 压缩容器的整体 hash 不作为跨环境保真条件。
- **规则**：普通文件权限规范为 0644，有任意执行位的文件为 0755，不继承特殊权限；固定安全 mtime、排序条目以减少无意义差异。拒绝链接、设备、越界路径及大小写/NFC 碰撞。仅明确排除系统噪声；安全点文件需逐路径准入，凭证禁止项不能放行。详见 [C-01/C-02](contracts/content-pipeline.md)。
- **Alternatives considered**：不手写 ZIP、不调用收录的打包脚本、不按文本处理二进制、不按扩展名筛掉普通附件。Node 内建能力没有直接提供本项目需要的 ZIP 写入接口。
- **来源**：[yazl 官方仓库](https://github.com/thejoshwolfe/yazl)、[yazl 精确版本](https://registry.npmjs.org/yazl/3.3.1)、[yauzl 官方仓库](https://github.com/thejoshwolfe/yauzl)、[yauzl 精确版本](https://registry.npmjs.org/yauzl/3.4.0)；已通过 Context7 查询 yazl，并核对注册信息。

## R-05：整批失败与本地输出替换

- **Decision**：全部验证、构建和输出自检在同父目录 staging 完成；再将 dist 改名为私有 backup、将 staging 改名为 dist。提交前失败恢复 backup，启动按 [C-03 协议](contracts/content-pipeline.md#local-recovery) 处理可验证中断；遗留锁须人工确认原进程退出后解除，并发构建拒绝。promoted 记录为本地提交点；之后清理失败保留有效新输出并报告 cleanup_status=pending，临时 backup 不作历史版本入口。
- **Rationale**：不能在既有 dist 内边生成边覆盖，也不能跳过坏条目后成功。Node rename 不可直接替换非空目录，因此必须明确补偿恢复，而不是宣称目录替换天然原子。
- **限制**：两次 rename 存在短暂间隙，不承诺断电/进程强杀时连续可访问。恢复失败保留 backup 并脱敏报告恢复位置；不能删除唯一可用副本。本轮是本地构建事务，不是生产发布事务。
- **Alternatives considered**：不直接 rm -rf dist 后重建；不为本故事引入永久多版本目录、指针服务或数据库；生产 artifact 的切换和缓存一致性由 US-003 继续验收。
- **来源**：[Node fs.rename](https://nodejs.org/api/fs.html#fsrenameoldpath-newpath-callback)；已通过 Context7 library → docs 查证。

## R-06：运行时、依赖锁定与测试范围

**Decision**：继续 CommonJS 构建入口；marked 用动态 import，不做全库 ESM 迁移。以当前 Node 26.3.0 为本地实施基线，实施时记录到运行时版本文件，package 声明 Node >=26.3.0 <27；Linux 兼容验证同版本。CI/生产版本由 US-003 再固定，不称本次已验证兼容。

| 精确版本 | 用途 | 官方声明的 Node 边界 |
|---|---|---|
| yaml 2.9.1 | frontmatter 读取 | >=14.6 |
| marked 18.1.2 | 构建端 Markdown | >=20；ESM |
| sanitize-html 2.18.1 | 构建端清理 | >=22.12.0 |
| yazl 3.3.1 | ZIP 写入 | 未声明 engines；需 PoC |
| minisearch 6.3.0 | 保持原搜索行为，改为本地静态分发 | 未声明 engines；不升级检索算法 |
| yauzl 3.4.0 | 开发期独立 ZIP 验证 | >=12 |

- **Rationale**：锁定直接依赖精确版本与 package-lock，不用 latest 作为项目依赖。sanitize-html README 与 engines 有差异时以精确版本包元数据为准。仅 MiniSearch 进入浏览器，构建端解析器不进入页面。
- **测试选择**：Node 内建 node:test 覆盖受信任 tests/unit 与 tests/integration 的显式文件集合；不做默认全仓测试发现，以免运行 skills 内收录的测试。浏览器本轮保留人工/已有工具验收，不新增 E2E 框架，符合上游将专用 E2E 包选择留给 US-002 的边界。
- **Alternatives considered**：研究了 Playwright 1.64.1 的本地 webServer、下载和权限测试能力，但本轮不新增该依赖；也不增加单元测试框架、前端框架或构建器。
- **来源**：[Node test runner](https://nodejs.org/api/test.html)、[MiniSearch 6.3.0](https://registry.npmjs.org/minisearch/6.3.0)、[Playwright webServer](https://playwright.dev/docs/test-webserver)、[下载测试](https://playwright.dev/docs/downloads)、[Playwright 元信息](https://registry.npmjs.org/@playwright/test/1.64.1)。Node 与 Playwright 均已先经 Context7 解析库再查文档。

## R-07：本轮收敛与后续验证

- **Decision**：需求歧义已经收敛，不遗留待业务决定的阻塞问题；Phase 1 可以据此建模与定义契约。
- **Rationale**：尚未执行的 PoC 是实施门禁，不是已经获得的兼容证明。先复现旧导出缺失，再验证复杂 YAML、清理、相对引用、二进制 ZIP 和失败恢复，通过后才能扩展实现。
- **实施必验**：四项原件逐字节、标准字段样例、点路径准入、大小写/编码边界、活动内容不执行、输出白名单、两个干净副本与故障注入。浏览器验证原名下载和剪贴板拒绝；macOS/Linux 验证 ZIP 与回滚行为。
- **分析后细化（2026-11-02；依据 2026-11-01 分析）**：A1 的固定 SECRET-01～04/占位边界、U1 的私有事务/提交点/恢复矩阵、I1 的受控标题与 Hash 保留已定向落实到契约和任务；沿用现有依赖与研究事实，不表示这些新用例已经实测。
- **留给后续**：生产 .bin 响应头/直接访问行为及跨发布缓存一致性是 US-003 的发布门禁，本轮仅证明本地等价子路径，不宣称线上安全或已部署。若后续实际响应不能保证非活动交付，必须改用安全的编码载体后再发布，不能仅依赖 download 属性。Q-004 与自动更新适配仍由后续故事处理。
