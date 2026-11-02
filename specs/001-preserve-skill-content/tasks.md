---
description: "US-001 原件保真、图库模型、旧库迁移与完整取用的实施任务"
---

# Tasks: US-001 原件保真、图库模型、旧库迁移与完整取用

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[research.md](research.md)、[data-model.md](data-model.md)、[内容契约](contracts/content-pipeline.md)、[静态契约](contracts/static-site.md)、[quickstart.md](quickstart.md)。日期：2026-11-01。

**Prerequisites**: [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0，以及四份 0.2 文档：[调研](../../docs/IndustryResearch.md)、[需求](../../docs/DemandAnalysis.md)、[技术方案](../../docs/TechnicalSolution.md)、[编程规范](../../docs/AiProgrammingGuide.md)。

**Status**: 任务生成于 2026-11-01，2026-11-02 根据分析定向细化 A1/U1/I1；生成阶段未执行实现；2026-11-02 用户另行授权本地工程初始化和逐步提交，实际进度见复选框及工程补充；不迁移、不开展业务实现、不发布。功能标识为 001-preserve-skill-content，当前实际 Git 分支为 main；没有自动创建分支。

**Tests**: spec 的 Independent Test、Acceptance Scenarios、US001-SC-01～07 明确要求验证；宪章 IX 要求先建立识别错误行为的验证。因此包含契约、保真、故障注入和浏览器任务。新增行为先记录合理失败，再实现并复验；已由共享层覆盖的行为直接复验，不伪造失败，不复制生产转换算法当期望值。

**Organization**: 唯一上游故事为 US-001；下面三个故事标签是 spec 内部切片，不能误读成上游 US-002 或 US-003。

| 标签 | spec 切片 | 优先级 | 对应实体与契约 |
|---|---|---|---|
| [US1] | US-001.A 保留既有收藏并分离图库信息 | P1 | CatalogRecord、MigrationBaseline、DerivedSkill；C-01、C-02 读取子集、C-03、C-04 基本查阅 |
| [US2] | US-001.B 完整查阅、复制和下载 | P1 | SkillOriginal、PublicFile、DerivedSkill；C-03 分发、C-04 取用 |
| [US3] | US-001.C 非法内容不破坏已有收藏 | P1 | Diagnostic、BuildManifest、失败/恢复状态；C-01～C-04 的本地失败与安全部分 |

## Format: [ID] [P?] [Story] Description

- 每项严格使用按真实证据更新的复选框、连续 T 编号、可选 [P]、故事阶段必需的 [US1]/[US2]/[US3] 和具体文件路径。
- **[P]** 只表示在该组共同前置条件完成后、不同写入文件之间可并行；不自动授权启动多 Agent。文件相同的任务必须串行。
- 路径相对项目根；validation 路径均指本功能下的本地验收证据，不能进入 dist。
- 每项括号保留 FR/NFR、DEC、AC 追溯；所有任务均归上游 US-001。不创建 M-05～M-07 或 C-05～C-07。

## Phase 1: Setup — 环境、基线和受信任测试入口

**Purpose**: 在任何源码修改前冻结输入证据，建立能安全运行后续验证的最小工程入口。

- [x] T001 检查 AGENTS.md、git 状态及实际源码；在 specs/001-preserve-skill-content/validation/preflight.md 记录用户已有改动与未跟踪资产保护范围，在 specs/001-preserve-skill-content/validation/migration-baseline.json 固定 spec 表中四 slug、六源文件的路径/大小/SHA-256/执行位及 office2md 未纳管状态；原件只读，不能用旧 assets/search-index.json 生成基线。（FR-011、NFR-001；DEC-009；AC-001）
- [x] T002 创建 package.json、package-lock.json、.node-version 并定向补充 .gitignore（仅 node_modules/、dist/、.dist.lock/、.dist.transaction.json、.dist.transaction.tmp-*、.dist.stage-*/、.dist.backup-*/ 等本轮生成路径）：本地 Node 26.3.0、engines >=26.3.0 <27，精确锁定 yaml 2.9.1、marked 18.1.2、sanitize-html 2.18.1、yazl 3.3.1、minisearch 6.3.0，yauzl 3.4.0 仅开发依赖；保留 CommonJS、marked 动态 import；test 仅显式运行 tests/unit/*.test.js 与 tests/integration/*.test.js，不做全仓发现，不安装 Skill 依赖；build/preview 脚本待相应入口实现后接入。（FR-004、NFR-003、NFR-006；DEC-003、DEC-005；AC-002、AC-012）
- [x] T003 在 tests/support/fixtures.js 建立最小临时项目、摘要和清理辅助，在 tests/fixtures/common/ 放标准单文件与目录型纯数据样例，包含折叠字段、未知嵌套字段、中文/空格路径、代码/表格、许可、空文件/目录及二进制；夹具不得自动纳入正式 catalog，所有凭证样例用明显假值，收录脚本/测试仅作数据。（FR-001、FR-004、NFR-003；DEC-002、DEC-005；AC-001、AC-002、AC-012）

**Checkpoint**: 原件基线已冻结，站点依赖与测试入口可复现；尚未开始任何正式入库或发布。

## Phase 2: Foundational — 所有故事的前置保护

**Purpose**: 公共解析、诊断、文件准入、快照能力。安全检查不是等到 US3 才添加的可选补丁。

**Gate**: T004 先复现旧损失；T005/T006 依赖 PoC 通过后再进入生产实现。T007/T009 的新行为检查应先失败；T008/T010 使其通过。全部完成才能进入故事实现。

- [x] T004 在 tests/integration/export-regression.test.js 对隔离的现有 scripts/build-index.js 与 assets/app.js 真实构建/取用行为建立完整原文断言，记录代码围栏/版本丢失的失败于 specs/001-preserve-skill-content/validation/regression.md；后续对同一源字节改验新 raw 出口，不把纯文本重建算法复制成测试期望，不运行正式目录中的旧构建。（FR-004、NFR-001；DEC-002；AC-002）
- [x] T005 [P] 在 tests/unit/yaml-poc.test.js 验证已锁 yaml 的 Document 读取：BOM、LF/CRLF、>-、嵌套/未知字段、标准字段、正文分隔线、重复/非字符串键、非法/未闭合元数据、自定义 tag 和别名上限 maxAliasCount=100；证明仅读取派生文本、不 stringify 原件，记录 PoC 结果到 specs/001-preserve-skill-content/validation/yaml-poc.md。（FR-001、NFR-001；DEC-003；AC-001、AC-002）
- [x] T006 [P] 在 tests/unit/render-archive-poc.test.js 用锁定 marked/sanitize-html/yazl/yauzl 验证代码/表格保留、活动内容清理、真实链接与代码伪链接区分、中文/重复/空标题别名与受控 ID 在最终清理后保留、原件伪造 id/name 不被采信、二进制与空目录 ZIP、流完成及解包路径/字节/执行位；记录 specs/001-preserve-skill-content/validation/render-archive-poc.md，不执行样例脚本，不新增 HTML parser 或 E2E 框架。（FR-004、NFR-001、NFR-003；DEC-002、DEC-005；AC-002、AC-012）
- [ ] T007 [P] 在 tests/unit/input-boundaries.test.js 与 tests/unit/diagnostics.test.js 先写 C-01 保护契约：根/逐级链接检查、所有权、绝对/越界/歧义路径、大小写/NFC 碰撞、硬性凭证禁止项、系统噪声排除、精确点文件准入、C-01 的 SECRET-01～04 固定判定/占位边界与脱敏；每条规则有命中/不命中/合法占位样例，SECRET-02 覆盖 19/20 字符；覆盖“每 Skill 最多 500 普通文件，总原始字节不超过 20 MiB，主文档不超过 1 MiB（均含边界）”的等于与超出，不接受跳过坏项仍成功。（FR-001、FR-011、NFR-003；DEC-003、DEC-005；AC-001、AC-012）
- [ ] T008 在 scripts/lib/validate.js 实现 T005/T007 对应公共 frontmatter 读取、文件准入与脱敏诊断，严格按 C-01 拒绝链接/越界并实现 policyVersion=1 的 SECRET-01～04，不执行环境展开或远端验证、不添加跳过开关；占位例外不得越过路径禁止项，不按扩展名漏普通附件；主文档满足“主文档必须是非空、合法 UTF-8”，无 YAML 可由完整记录供值但非法 YAML 不能被覆写；Diagnostic 采用“code、slug（可空）、path（项目/Skill 相对位置）、line/column（可选）、message、severity=error”，只输出安全位置/类型，不原样打印 parser 片段；完成后复验 T005/T007。（FR-001、FR-011、NFR-003；DEC-003、DEC-005；AC-001、AC-012）
- [ ] T009 在 tests/unit/content-snapshot.test.js 先写 C-02 快照/digest 契约，证明路径、附件增删、字节、执行位、空目录变化影响身份，mtime/当前日期/Git HEAD 不影响；验证文件/记录清单在读取前后变化会失败，单文件不拥有邻接文件，Buffer 不受解析/打包改写。（FR-001、NFR-001、NFR-006；DEC-002、DEC-009；AC-002、AC-012）
- [ ] T010 在 scripts/lib/content-store.js 复用 M-01 实现只读受控快照：content_path 为“项目相对 POSIX 路径；仅 skills/<slug>.md 或 skills/<slug>/SKILL.md；路径保持现状”，kind 为“根据 content_path 推导 single_file 或 directory，不重复手工配置”，root_name 为“单文件为原文件名；目录为原目录名，作为 ZIP 根”；FileEntry 保持“path 为未经重命名的相对 POSIX 路径；bytes 为内部 Buffer；size 为原始字节数”和“sha256 为 64 位小写十六进制；executable 为布尔”，并遵守“Buffer 不序列化进入搜索索引”，空目录不当空文件；按数据模型固定 JSON 数组、UTF-8 路径排序及 SHA-256 算 digest，同一路径不能归两记录；复验 T009，不实现写入/远程替换。（FR-001、NFR-001、NFR-006；DEC-002、DEC-009；AC-001、AC-002）

**Checkpoint**: PoC、只读边界与快照测试通过，原件未变。C-03 的实际构建与事务仍由 US1 实现并在 US3 做深入故障验收。

## Phase 3: User Story 1 — 保留既有收藏并分离图库信息（P1，首个可审阅增量）

**Goal**: 四项原件不变、图库信息独立、恰好四项本地基本列表/详情与旧链接可用。

**Independent Test**: 隔离迁移四项，逐一比对六源文件及四 slug；另用标准字段样例生成独立测试库；改站内标签/备注不改原件，未知字段不编造，四旧链接在 /skill-gallery/ 可查阅。无需 US2 的复制按钮或 US3 的全部故障矩阵。

### Tests for User Story 1 — 先写新行为检查

- [ ] T011 [P] [US1] 在 tests/unit/catalog-contract.test.js 先覆盖 data-model.md 全部 CatalogRecord 必填/可空/枚举与优先级、非法日期/URL、未知顶层键、已知原件类型错误不可覆写，以及标准 name/description 原件可配独立记录的 C-01 正反例；补充不编造作者/版本/日期、保留中文显示名和原始扩展字段的断言。（FR-001、NFR-001；DEC-003、DEC-009；AC-001、AC-002）
- [ ] T012 [P] [US1] 在 tests/integration/migration.test.js 先覆盖四固定路径迁移、--dry-run 零写入、--write 全部合法才新增、一致 noop/差异冲突、写入中途失败只回收本次新文件、office2md 不入库不变、原件/已有记录不覆盖与标准样例不成为正式第五项。（FR-001、FR-011、NFR-001；DEC-009；AC-001、AC-002）
- [ ] T013 [P] [US1] 在 tests/integration/build-contract.test.js、tests/integration/preview.test.js 先定义 C-03/C-04 基本契约：索引/详情/raw/ZIP/manifest 同快照、输出白名单、缺主文档/重复 slug/缺本地附件整批失败保留旧输出、成功完整替换、首次失败无残缺 dist、第二次 rename 失败回滚，以及仅 dist 的 /skill-gallery/ 预览；可使用独立样例库，不依赖四记录已落盘。（FR-011、NFR-001、NFR-003、NFR-006；DEC-002、DEC-005、DEC-009；AC-001、AC-012、AC-014 本地部分）

### Implementation for User Story 1

- [ ] T014 [US1] 在 scripts/lib/validate.js 实现 CatalogRecord schema：schemaVersion“必需整数，固定 1”；slug/display_name/description/content_path 均“必需非空字符串”，slug 另满足“1～64 位小写 ASCII 字母、数字、单连字符分段；文件名必须一致”；tags/platforms/allowed_dot_paths 为“字符串数组，缺省 []”，allowed_dot_paths 遵守“本次细化的安全点文件精确路径准入，不可越过凭证禁止项”；author/homepage_url/repository_url/declared_version/source_type/usage/notes/license 均“可选 string 或 null”；created_at/updated_at 为“可选 YYYY-MM-DD 或 null”；source_tracking 为“null 或上游定义的对象”，其对象满足“GitHub provider、非空定位字段、branch/release/pinned 策略、布尔开关、可空同步结果”，只校验不请求同步；拒绝未知顶层字段及重复 slug/所有权。（FR-001、NFR-003；DEC-003；AC-001、AC-002）
- [ ] T015 [US1] 在 scripts/lib/validate.js 实现记录合并与 field_sources：站内 slug/显示名/简介/分类/用法/备注由 catalog 控制；可选字段 catalog 显式值（含 null）优先，未出现再取约定原件字段；declared_version 为显式值→version→metadata.version→null，遵守“不要求 SemVer，不是 digest”及“存在的已知版本字段必须为非空字符串；不自动把数字转字符串”；skill_name 取原件 name、缺失 null，不强制等于 slug；field_sources“值为 catalog、frontmatter、frontmatter.metadata 或 missing”；URL“仅接受无账号密码的 http/https 绝对 URL；空字符串和非法日期报错，不按 null 吞掉”，日期“缺失不补当前日期”；复验 T011。（FR-001、NFR-001；DEC-003、DEC-009；AC-001、AC-002）
- [ ] T016 [US1] 在 scripts/migrate-catalog.js 实现仅四固定路径的一次性本地迁移，默认 --dry-run、与 --write 互斥、0 成功/1 失败；先验证全部候选再落盘，一致 noop、冲突/中断保护既有记录，不从有损索引取值、不修改原件；状态遵循 discovered → validated → records_prepared → verified，错误 failed；复验 T012，不实现任意路径导入或上传 CLI。（FR-001、FR-011、NFR-001；DEC-009；AC-001、AC-002）
- [ ] T017 [P] [US1] 在 T016 通过后只生成 catalog/superpower-systematic-debugging.json、catalog/code-review-assistant.json、catalog/refactoring-workflow.json、catalog/handoff-codex.json，保留既有显示与站内信息、原 content_path 和 slug，source_tracking 全部 null；核对 T001 六文件基线零变化，不伪造可选信息/许可；本任务不读写构建模块，可与仅使用夹具的 T018 并行。（FR-001、FR-011、NFR-001；DEC-003、DEC-009；AC-001、AC-002）
- [ ] T018 [P] [US1] 在 scripts/lib/build-site.js 使用已验证快照实现 C-03 投影：安全 body_html 与检索 content_text 分离，所有 Markdown 附件的真实引用统一走 M-01 边界、缺本地附件使整批失败，外链/代码伪链接不误判；按 C-04 标题策略先移除源 id/name、再生成顺序标题 ID 和唯一别名，映射本文片段并保留最终受控 ID，未知片段不作为缺文件；生成原字节 .bin、经格式签名检查的栅格媒体、原目录根 ZIP（含空目录/许可、0644/0755、固定安全 mtime、等待流完成），保留 PublicFile 的“原 path、size、sha256、executable、download_name、url，可选 media_url；空目录不提供文件 URL”；内部 URL 遵守“所有公开 URL 为站点根相对地址，不以 / 开头、不含 .. 或敏感参数”；本任务只用夹具，不依赖 T017。（FR-004、FR-011、NFR-001、NFR-003；DEC-002、DEC-005；AC-002、AC-012）
- [ ] T019 [US1] 在 scripts/lib/build-site.js 接 T018 生成完整 schemaVersion=1 的 search-index/details/manifest：索引含“schemaVersion、contentRevision、skills”，详情按 C-04 完整字段及来源，下载区分“单文件为主文档资源，目录为 ZIP；另给 download_name、download_sha256、download_size”；contentRevision 使用排序的受控输入、构建/策略、网页、依赖锁和运行时标识，排除私人路径/日期/Git 状态/未纳管内容；manifest 记录路径/size/sha256 并遵守“不包含自身 hash，避免自引用；所有其他输出必须在产物清单内”，自检所有 URL/产物和同修订，拒绝越过输出白名单。（FR-004、FR-011、NFR-001、NFR-003、NFR-006；DEC-002、DEC-005、DEC-009；AC-002、AC-012、AC-014 本地部分）
- [ ] T020 [US1] 在 scripts/lib/build-site.js 将 T019 接入 C-03 的 .dist.lock/owner.json、.dist.transaction.json 与按 run_id 派生的 stage/backup；互斥取得锁后校验归属并逐行实施恢复表，依 prepared/promoting/promoted 记录完成 dist→backup→新 dist；遵循“idle → validating → snapshot_ready → staging → verified → promoting → ready”，失败 failed、补偿失败 recovery_required；切换前复核文件/清单/catalog 变化，错误 E_SOURCE_CHANGED；只清理本次拥有的候选/锁/backup，promoted 记录写入前失败回滚、之后清理失败返回 built/cleanup_status=pending 并保留记录，不回滚已提交结果；清理完成为 complete，不建立旧版入口；通过 T013 的失败保留检查，不宣称两次 rename 无间隙原子或已生产发布。（FR-011、NFR-001、NFR-003；DEC-002、DEC-009；AC-012、AC-014 本地部分）
- [ ] T021 [US1] 改造 scripts/build-index.js 为 T020 的完整构建入口，并在 package.json 接入 npm run build；公开产物只写 dist，必要私有控制路径按 C-03，保留根 assets/search-index.json 为旧基线；提交成功 0/built 并报告 cleanup_status=complete 或 pending；提交前校验/构建/恢复失败 1/脱敏诊断，禁止部分跳过成功；复制 .nojekyll、明确网页资产及固定 MiniSearch/许可，不能复制全仓；先在临时项目验证命令，真实四项闭环由 T024 执行。（FR-004、FR-011、NFR-003、NFR-006；DEC-002、DEC-009；AC-001、AC-012、AC-014 本地部分）
- [ ] T022 [P] [US1] 在 index.html、assets/app.js 最小适配新索引对象与安全详情，display_name 映射既有 name，维持基本列表/搜索、四旧 Hash 身份、加载/未找到反馈和“未提供”显示；仅清理后的 body_html 可插 HTML，其他公开字段按文本/安全属性处理；移除浏览器 marked CDN、改固定本地 MiniSearch，本文锚点点击仅定位当前正文的受控标题并阻止覆盖技能 Hash，不重写界面或搜索算法；共同前置 T021 完成后可与 T023 并行。（FR-001、FR-011、NFR-003；DEC-003、DEC-005、DEC-009；AC-001、AC-005 链接部分、AC-012）
- [ ] T023 [P] [US1] 在 scripts/preview.js 实现 localhost:8000 的只读 dist 预览，在 package.json 接入 npm run preview；仅映射 /skill-gallery/，拒绝目录外读取/路径穿越/链接、禁止目录列表，明确网页 MIME 与 .bin application/octet-stream，不做 HTML 嗅探；复验 T013 的 tests/integration/preview.test.js，不提供管理写入或生产服务。（FR-011、NFR-003、NFR-006；DEC-005、DEC-009；AC-005、AC-012、AC-014 本地部分）
- [ ] T024 [US1] 在隔离项目运行迁移/构建和 US1 相关测试，用 T023 预览四旧链接及独立标准样例，检查备注/标签只改 catalog、四唯一条目/六原件零差异、office2md 未动未收录、重复生成无伪日期；在 specs/001-preserve-skill-content/validation/us1-migration.md 记录实际命令/退出码/摘要与本地查阅证据，确认 T004 新 raw 回归通过。（FR-001、FR-011、NFR-001、NFR-006；DEC-002、DEC-003、DEC-009；AC-001、AC-002、AC-005；US001-SC-01、US001-SC-05）

**Checkpoint**: US1 独立验收通过，可提供带基本护栏的本地迁移/查阅演示。US2 的完整交互、US3 深入失败验收尚未完成，不能宣称整个 US-001 完成或上线。

## Phase 4: User Story 2 — 完整查阅、复制和下载（P1）

**Goal**: 访客能安全取得完整原文、原名单文件和完整目录包，保留分享链接并如实反馈操作失败。

**Independent Test**: 仅使用一单文件和一目录样例构建并预览，核对原文复制与下载/解包字节；旧 Hash/子路径刷新可达，剪贴板拒绝与文件不可用均不误报成功。不依赖正式四项迁移数据，也不增加写入入口。

### Tests for User Story 2

- [ ] T025 [P] [US2] 在 tests/integration/distribution.test.js 对 C-03/C-04 原件资源建立独立单文件/目录夹具验收：完整 frontmatter/版本/扩展/代码/中文，原名、空目录、许可、二进制、文件清单、逐字节摘要及规范执行位；核对所有 PublicFile/ZIP URL 与 hash、不混入跨 Skill 文件，验证 content_text/body_html 不能充当原件来源，不强求 ZIP 容器整体字节相等。（FR-004、NFR-001；DEC-002、DEC-005；AC-002）
- [ ] T026 [P] [US2] 在 specs/001-preserve-skill-content/validation/us2-browser.md 建立并用现有可信浏览器工具/人工执行前置失败场景：查看/复制原文、原名文件/ZIP/附件下载、剪贴板拒绝、404/摘要不符、未知 slug/不支持 schema、迟到响应/跨修订阻断、中文/重复标题跳转及未知片段、点击后技能 Hash 不变、同 slug 第二快照旧链接和子路径刷新；记录浏览器版本及失败原因，和 T025 使用独立临时输出，不新增 E2E 框架。（FR-004、FR-011、NFR-003；DEC-002、DEC-005、DEC-009；AC-002、AC-005、AC-012）

### Implementation for User Story 2

- [ ] T027 [US2] 在 assets/app.js、assets/style.css 增加必要原文文本区和完整原文复制：raw_url 响应/大小/SHA-256 正确后严格 UTF-8 解码，遵守「主文档“查看原文/复制”从 raw_url 读取完整 UTF-8 文本，不能从 body_html/content_text 还原」，保留 BOM/换行、不得 trim 或经 textarea 重建；等待剪贴板成功才提示，拒绝则保留手工复制区；只改本操作所需样式。（FR-004、NFR-001、NFR-003；DEC-002、DEC-005；AC-002、AC-005）
- [ ] T028 [US2] 在 assets/app.js 接通原名单文件、完整 ZIP、附件下载和相对附件点击：验证响应/大小/摘要后以 application/octet-stream Blob 按 download_name 发起，安全回收句柄；HTML/SVG/脚本不导航为活动页面、不执行，安全栅格图片用 media_url，其他图保留 alt 与下载入口；不能保存 404 页或把“已发起下载”说成已安装。（FR-004、NFR-001、NFR-003；DEC-002、DEC-005；AC-002、AC-005、AC-012）
- [ ] T029 [US2] 在 assets/app.js 完成安全分享链接与状态一致性，回归 T022 的本文锚点处理且不增加标题分享路由：站点基址取当前文档目录并忽略 Hash、内部路径正确编码；复制链接等待真实成功；校验 schemaVersion/contentRevision、detail.slug/digest 和资源摘要，忽略过期异步响应；明确区分 loading、ready、not_found、load_failed、snapshot_mismatch、raw_unavailable、copy_failed、download_failed，提供刷新/重试/手动复制，不给旧数组或坏 JSON 空库假象，不冒充生产缓存策略已验证。（FR-004、FR-011、NFR-003、NFR-006；DEC-005、DEC-009；AC-005、AC-012、AC-014 本地部分）
- [ ] T030 [US2] 执行 tests/integration/distribution.test.js 及 T026 全部浏览器步骤，在 specs/001-preserve-skill-content/validation/us2-browser.md 记录真实下载/解包摘要、四旧链接直接访问/刷新/复制及同 slug 手工快照、两个操作失败零误报、基本列表搜索回归；代码/表格/相对附件正常，证据未覆盖项明确标未运行，不把模拟内容变更当自动升级交付。（FR-004、FR-011、NFR-001、NFR-006；DEC-002、DEC-005、DEC-009；AC-002、AC-005、AC-012；US001-SC-02、US001-SC-03）

**Checkpoint**: US2 可用独立夹具证明完整查阅取用。整个功能还需 US3 和最终跨场景验收。

## Phase 5: User Story 3 — 非法内容不破坏已有收藏（P1）

**Goal**: 对已实现的共享保护做完整负例、故障与无副作用验收，按测试证据修正剩余缺口；不另造一套校验器。

**Independent Test**: 用隔离合法库先生成可用输出，再注入规定非法输入、文件/路径攻击与构建故障，检查整次失败、原件/旧输出零变化、秘密零回显、内容零执行；不需要正式四项、后台、远程凭证或上线。

### Tests for User Story 3

- [ ] T031 [P] [US3] 在 tests/integration/invalid-batch.test.js 使用 tests/fixtures/invalid-batch/ 覆盖缺/空主文档、必填空值、类型/未知字段/版本错误、重复 slug/来源、坏 YAML、缺本地附件（含 Markdown 附件内及被排除资源的引用）、全部容量边界；对每类断言非零退出、可修正诊断和原件/旧 dist 摘要零变化，外链/片段/代码伪链接不误伤。（FR-001、FR-011、NFR-003；DEC-003、DEC-005；AC-001、AC-012；US001-SC-04、US001-SC-07）
- [ ] T032 [P] [US3] 在 tests/unit/path-attacks.test.js 使用 tests/fixtures/path-attacks/ 验证原文件/引用/URL 各边界：单次解码、编码分隔和二次编码、目录内合法 ../、越界/盘符/NUL/反斜杠、符号/硬链接及非普通文件、NFC/大小写冲突、点路径逐文件准入/不存在项、模板例外不能放过凭证；确认越界文件没有被读入，不通过改原件路径规避失败。（FR-001、FR-011、NFR-003；DEC-005、DEC-009；AC-012）
- [ ] T033 [P] [US3] 在 tests/integration/build-failures.test.js 对 ZIP 写流/产物校验失败、源文件/清单/catalog 中途变化、promotion 第二次 rename 失败、状态记录写失败、补偿恢复失败、prepared/promoting/promoted 中断恢复表各行、并发/遗留锁/损坏或归属不明记录、提交后清理失败注入故障；验证提交前可捕获失败下旧 dist 原路径/字节不变、首次未提交失败无半成品、唯一可用 backup 不被删、恢复失败明确 E_RECOVERY_REQUIRED、未知临时文件不清理；提交后清理失败则 0/built、cleanup_status=pending 且新 dist 保持有效，不把它判为提交前构建失败。（FR-011、NFR-001、NFR-003、NFR-006；DEC-002、DEC-009；AC-012、AC-014 本地部分）
- [ ] T034 [P] [US3] 在 tests/integration/untrusted-content.test.js 使用 tests/fixtures/untrusted/ 验证脚本/事件/表单/iframe/object/危险 URL 与 DOM 遮蔽清理、普通字段安全插入、原始 HTML/SVG 非活动分发、媒体签名、SECRET-01～04 的正反/占位/误报阻断与诊断脱敏（仅测试内拼接明显 FAKE 材料，不在报告回显），受控标题 ID/片段不允许跳转全页面任意节点、输出白名单，以及脚本/Agent 配置/Skill 自带 tests 只当数据；用受控哨兵确认无执行/安装/敏感值回显，不引入真实密钥。（FR-004、FR-011、NFR-003；DEC-002、DEC-005；AC-012；US001-SC-04）

### Implementation and Closure for User Story 3

- [ ] T035 [US3] 依据 T031/T032 在 scripts/lib/validate.js、scripts/lib/content-store.js 校齐全入口的 C-01/C-02 保护：所有 Markdown 引用只查已验证清单，缺本地附件 E_REFERENCE_MISSING 整批失败、越界 E_PATH，不按引用扩大范围；凭证判定只按 C-01 的 SECRET-01～04 与 policyVersion，误报保留原件/旧输出并暂停，不临时放行；落实 E_SCHEMA/E_YAML/E_UTF8/E_DUPLICATE/E_MAIN_MISSING/E_LINK_FILE/E_DOT_PATH_REVIEW/E_SECRET/E_LIMIT 的类型化脱敏诊断；复用已有正确逻辑，只修复测试证实的缺口，不吞异常继续构建。（FR-001、FR-011、NFR-003；DEC-003、DEC-005；AC-001、AC-012；US001-SC-04、US001-SC-07）
- [ ] T036 [US3] 依据 T033 在 scripts/lib/build-site.js 校齐事务恢复与输入复核：E_SOURCE_CHANGED/E_BUSY/E_BUILD/E_RECOVERY_REQUIRED 明确分流，按 C-03 固定记录字段、派生路径、归属和恢复矩阵检查，不覆盖活动构建、不自动抢遗留锁、不按超时清锁、不删除唯一可用 backup；提交前失败恢复旧输出，promoted 后清理失败保留新有效 dist 并报告 cleanup_status=pending；损坏/不匹配记录不猜测，启动恢复未结束旧事务则 1/E_RECOVERY_REQUIRED、不覆盖记录或开始新事务；中断/补偿失败给真实恢复位置及步骤而不谎报原位置可用；只修测试缺口并复用 T020，不增加永久版本目录或生产发布流程。（FR-011、NFR-001、NFR-003；DEC-002、DEC-009；AC-012、AC-014 本地部分）
- [ ] T037 [US3] 依据 T034 校齐 scripts/lib/build-site.js、scripts/preview.js、assets/app.js 的预览/附件安全链路：按 C-04 固定标签/属性和 URL 白名单，只有清理 body_html 入 HTML、标题按 C-04 先去源 id/name 再分配 ID/别名，最终仅保留匹配的标题 ID，本文片段定位不改变技能 Hash，未知片段无 href 并明示；栅格签名准入/活动附件下载与 .bin 明确 MIME、dist 外不可读；正确实现不重复重构，不把本地安全结果冒充 Pages MIME 已验证。（FR-004、FR-011、NFR-003；DEC-005、DEC-009；AC-012）
- [ ] T038 [US3] 运行 T031～T034 全部负例及真实浏览器恶意展示/取用检查，在 specs/001-preserve-skill-content/validation/us3-failures.md 逐类记录诊断、原件/旧输出摘要、恢复路径、哨兵与回显检查；所有规定非法输入均阻止整批生成，合法点资源/脚本仍保真交付，旧可用库可继续查阅；明确中断时两次 rename 的间隙限制。（FR-001、FR-004、FR-011、NFR-001、NFR-003；DEC-002、DEC-003、DEC-005、DEC-009；AC-001、AC-002、AC-012；US001-SC-04、US001-SC-07）

**Checkpoint**: 三个切片的本地功能均完成，安全与故障保护有真实证据；进入跨切片复现与交付复核。

## Phase 6: Polish & Cross-Cutting Concerns — 复现与证据收口

**Purpose**: 完成计划要求的真实命令说明、干净副本/平台验证和本轮范围复核，不增加新业务。

- [ ] T039 [P] 在 tests/integration/reproducibility.test.js 从两个干净且同实现版本的临时副本构建，比较 contentRevision/slug/digest/原件/附件/解包清单及单版本输出；重复相同输入无伪版本/时间，第二快照删附件后无旧文件遗留；不依赖私人路径/凭证/未纳管目录，不要求 ZIP 容器 hash 跨环境相同。（FR-011、NFR-001、NFR-006；DEC-002、DEC-009；AC-002、AC-014 本地部分；US001-SC-06）
- [ ] T040 [P] 仅更新 README.md、AGENTS.md 中本轮已实现并验证的依赖、原件/catalog、限额、迁移/测试/构建/dist 子路径预览与 C-03 遗留锁人工核对/保留事务后重跑的恢复步骤（不新增强制 CLI），说明固定凭证规则/占位边界与标题锚点；明确本地 built 及提交后 cleanup_status=pending、原件非执行、生产 MIME/缓存后续门禁；上传 CLI、GitHub 后台/自动更新/发布仍按现状标规划，不写已可用假命令，不改四份 0.2 主文档的业务范围。（FR-011、NFR-003、NFR-006；DEC-002、DEC-005、DEC-009；AC-012、AC-014 本地部分）
- [ ] T041 在 specs/001-preserve-skill-content/validation/platform.md 记录同 Node 基线的 macOS 与 Linux ZIP 路径/0644-0755/二进制及 rename/回滚/中断恢复实测；缺环境或未通过必须记未运行/失败并保留此项未完成，不能用单平台结果声称跨平台通过，也不为验证擅自执行远程写入或部署。（FR-004、FR-011、NFR-001、NFR-006；DEC-002、DEC-009；AC-002、AC-012）
- [ ] T042 完整执行 specs/001-preserve-skill-content/quickstart.md 的适用步骤，在 specs/001-preserve-skill-content/validation/acceptance.md 汇总 npm ci/npm test/迁移/构建/预览的实际命令和退出码、Node/浏览器/平台版本、四项/下载/解包/失败保护证据；逐项判定 US001-SC-01～07，未运行或未达标不勾通过，不能以语法或任务勾选替代验收。（FR-001、FR-004、FR-011、NFR-001、NFR-003、NFR-006；DEC-002、DEC-003、DEC-005、DEC-009；AC-001、AC-002、AC-005、AC-012、AC-014 本地部分）
- [ ] T043 对照 T001 与 specs/001-preserve-skill-content/validation/acceptance.md 复核最终差异：六原件/office2md/无关用户改动未动、无凭证/额外依赖/全仓格式化、只定向改动计划内文件、旧根索引未被新构建改写；明确四旧链接和当前单版本成立、Git 历史未清除、站点未发布，列出生产 Pages MIME/直接资源安全/缓存/授权恢复及 Q-004 后续门禁；不创建提交、PR 或部署。（FR-011、NFR-001、NFR-003、NFR-006；DEC-005、DEC-009；AC-001、AC-005、AC-012、AC-014 本地部分）

## Dependencies & Execution Order

### Phase Dependencies

~~~text
T001 → T002 → T003 → T004
                       ├─ T005 ─┐
                       ├─ T006 ─┼→ T008 → T009 → T010
                       └─ T007 ─┘

Phase 2 完成
  ├─ T011 ─┐
  ├─ T012 ─┼→ T014 → T015 → T016 ─┬─ T017 ─────────────────────────┐
  └─ T013 ─┘                     └─ T018 → T019 → T020 → T021      │
                                                       ├─ T022 ──┼→ T024 (US1 gate)
                                                       └─ T023 ──┘

T024 → {T025, T026} → T027 → T028 → T029 → T030 (US2 gate)
T030 → {T031, T032, T033, T034} → T035 → T036 → T037 → T038 (US3 gate)
T038 → {T039, T040} → T041 → T042 → T043
~~~

图示是安全默认串行顺序；花括号/分叉内为可并行组，汇合需等待全部依赖完成。
T018 也需要 T013/T015/T010，T017 与 T018 的并行只在 T016 完成后开放；T024 等待 T017/T022/T023。

### User Story Dependencies

- **US1** 依赖共享基础；迁移、生成和基本查阅构成首个可审阅增量。
- **US2** 复用 US1 内的规范化/构建/只读前端运行时（T014/T015/T018～T023），不依赖四正式记录 T017 或迁移结论 T024 的业务数据。独立验证用自己的样例；默认在 T024 后执行以减少同文件冲突。
- **US3** 的负例定义可在 Phase 2 后用夹具先准备；其完整故障验收依赖已实现的 M-03/预览及必要 M-04。运行时相同而非业务数据依赖，不需要 US1 四项或 US2 的业务样例。涉及 scripts/lib/build-site.js、assets/app.js 等共用文件的修复串行。
- **Polish** 等三个切片通过。跨平台未验证或最终成功标准未满足，不得把整个功能标完成。

### Within Each User Story

先新增行为/契约验证，再实现模型与规则、生成/接口、页面集成，最后独立验收。测试红灯必须说明断言和原因，不能把环境损坏当功能缺陷证明。共享层正确实现直接复用；US3 不要求为了“有修改”重复重构已达标代码。

## Parallel Examples

### User Story 1

Phase 2 完成后，T011（catalog-contract.test.js）、T012（migration.test.js）、T013（build-contract.test.js/preview.test.js）只写各自测试文件，可同时建立新行为断言。T016 完成后，T017 写四 catalog，T018 仅用夹具写 build-site.js，可并行。T021 完成后，T022 写 index/app，T023 写 preview/package，可并行；包脚本此前由 T021 的修改必须先落定。

### User Story 2

运行时就绪后，T025 写 distribution.test.js，T026 在独立输出副本验证并记录 us2-browser.md，可并行。T027/T028/T029 均写 assets/app.js，必须串行。

### User Story 3

运行时就绪后，T031～T034 写不同测试文件/各自专属夹具（故障均注入临时副本），可并行；T035/T036/T037 的共用生产文件修改必须按依赖串行。浏览器/临时服务使用不同工作副本或串行，不共享同一 dist 故障现场。

其他可并行组：T004 后的 T005/T006/T007；最终阶段的 T039/T040。共享夹具辅助由 T003 先完成并在这些并行组中只读；若需要修改共享辅助或同一报告，先拆开调度，不因 [P] 强行并行。

## Implementation Strategy

### MVP First

先完成 T001～T024（Setup/Foundational + US1），验收四项原件/独立记录/基本查阅与旧链接，作为首个本地可审阅增量。基础失败护栏仍是必需前提；该增量不等于完整 US-001。整个上游故事的最小闭环需要 US1 + US2 + US3 和最终复现验收，不自动部署演示。

### Incremental Delivery

US1 迁移查阅 → US2 完整原文与下载 → US3 全失败矩阵 → 跨副本/平台和 quickstart 收口。每步均在隔离环境验证，前一增量通过后再继续。用户当前只授权任务生成；未来实施应另行调用 $speckit-implement，生产发布仍属于后续故事。

### Scope and Acceptance Boundaries

- AC-001/AC-002：完成本故事规定的迁移、输入和完整取用验收；关联 US001-SC-01/02/05。
- AC-005：旧链接、同 slug 手工快照、复制/下载反馈；不交付上传或自动升级；关联 US001-SC-03。
- AC-012：本地读取、渲染、打包与故障保护；不覆盖管理授权或远程同步入口；关联 US001-SC-04/07。
- AC-014：仅本地 /skill-gallery/ 和同快照/可复现支撑；不宣称完成线上构建部署；关联 US001-SC-06。
- 本轮不做全面视觉/检索改版、管理员上传、自动来源检查、Actions、生产发布、线上 MIME/缓存验证或 Q-004 调度决策。GitHub 后台、首版 GitHub 自动更新、单一当前版与保留 Git 历史的已确认边界保持。

## Notes

## 工程基线补充（2026-11-02）

用户现已授权执行 project-bootstrap 本地工程基线；此前“仅任务生成”的表述描述历史阶段，不限制本轮已授权工程工作。
保持所有原业务编号与验收范围；不实现 US-001 的功能、CI 或发布。T002/T003 的业务依赖与标准数据夹具仍须后续完成。

- [x] T044 创建根 package.json/package-lock.json/.node-version 与工程忽略项，精确锁定开发工具，并在隔离副本验证 npm ci。（NFR-003/NFR-006；DEC-005/009；AC-012/014 工程支撑）
- [x] T045 添加 eslint.config.mjs、Prettier/EditorConfig 和 tests/unit/bootstrap.test.js、tests/integration/bootstrap.test.js，验证受信任测试发现与规范门禁拒绝行为。（NFR-003/NFR-006；DEC-005；AC-012 工程支撑）
- [x] T046 添加 scripts/check-project.js、scripts/setup-security-tools.js 及 config 下固定工具/规则配置，用真实扫描器验证脱敏、失败传播和范围；不实现 C-01 的业务校验器。（NFR-003/NFR-006；DEC-005；AC-012 工程支撑）
- [x] T047 定向更新 README.md/AGENTS.md 的真实工程入口，记录 validation/bootstrap.md 的检查结果、拒绝样例、原件核对与未运行项。（NFR-001/NFR-003/NFR-006；DEC-009；AC-001/012/014 工程支撑）

以下原任务数量为生成阶段统计；工程补充后共 47 项，原 43 项及其依赖不重排。

任务合计 43 项：Setup 3、Foundational 7、US1 14、US2 6、US3 8、Polish 5；18 项标注 [P]。
这些数量只描述任务拆分，不表示已完成。生成阶段检查格式、连续编号、标签、文件路径、依赖和验收映射；业务通过证据在未来实施时填入 validation。
不要执行收录 Skill 的脚本/测试，不做全仓 npm 安装或测试发现，不执行 git add .、reset、clean、force push 或自动提交。原件/有损索引/安全展示不能混作同一数据源。

## 提前建设 CI 与基础可用性监测（2026-11-02）

用户单独授权的工程增量；不实现 US-001 业务功能、生产发布或来源更新 Q-004。

- [x] T048 同步 docs/TechnicalSolution.md、docs/AiProgrammingGuide.md 和当前 plan/tasks，明确提前检查 CI 与基础监测边界、错误处理和验收，提交本步。（FR-011、NFR-003/004/006；DEC-001/008/009；AC-014 工程支撑）
- [x] T049 在 tests/integration/site-monitor.test.js 用本地 HTTP 服务先验证成功与失败、重试/超时、索引及脱敏，再实现 scripts/check-site.js、package.json 的 monitor:site。（FR-011、NFR-003/004；DEC-008/009；AC-014 可用性支撑）
- [x] T050 创建 .github/workflows/quality.yml 与 site-monitor.yml，固定 Action SHA/工具版本、只读权限、无发布/写回；实际静态校验及本地命令验证后提交，远程运行另记。（NFR-003/004/006；DEC-001/008；AC-014 工程支撑）
- [x] T051 在 validation/ci-monitor.md 记录现站四资源、完整检查和原件保护，定向更新 README/AGENTS，明确定时启用、通知和远程未验证状态并提交。（FR-011、NFR-003/004/006；DEC-009；AC-014 支撑）

补充后共 51 项，原业务任务编号不变；复选框不替代远程执行证据。
