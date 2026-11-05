---
description: "US-002 检索、详情、分享与视觉改版的实施任务"
---

# Tasks: US-002 检索、详情、分享与视觉改版

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[research.md](research.md)、[data-model.md](data-model.md)、
[search-ui 契约](contracts/search-ui.md)、[detail-share 契约](contracts/detail-share.md)、[quickstart.md](quickstart.md)。日期：2026-11-05。

**Prerequisites**: [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0，
以及四份 0.2 文档：[调研](../../docs/IndustryResearch.md)、[需求](../../docs/DemandAnalysis.md)、
[技术方案](../../docs/TechnicalSolution.md)、[编程规范](../../docs/AiProgrammingGuide.md)。

**Status**: 任务于 2026-11-05 生成；当前分支 `codex/us-002-search-detail-share`，尚未实施。
本功能只覆盖 US-002；不改变 US-001 已验收的复制、下载、旧链接、T041 macOS 缺口或生产发布状态。

**Tests**: spec 的 Independent Test、Acceptance Scenarios 与 US002-SC-01～06 要求验证；宪章 IX 要求先建立
能识别错误行为的验证。因此包含搜索核心契约、分享地址/内容标识、构建资产、浏览器可访问性和性能任务。
测试夹具只作数据，不执行收录 Skill 的脚本或测试，不安装其依赖。

**Organization**: 三个用户故事对应 [spec.md](spec.md) 的内部切片，不占用上游其他 US 编号。
每个故事可在共享基础完成后独立验证；同文件任务必须串行，不由 `[P]` 自动授权多 Agent。

## Format: [ID] [P?] [Story] Description

- 每项严格使用 `- [ ] Txxx [P?] [USx?] 描述 + 文件路径`。
- `[P]` 只表示不同文件、无未完成依赖时可并行；同一文件任务不得并行。
- Setup/Foundational/Polish 不加故事标签；User Story 阶段必须加 `[US1]`/`[US2]`/`[US3]`。
- 路径相对项目根；`dist/` 是生成目录，不手改、不提交。

## Phase 1: Setup — 夹具与测试输入

**Purpose**: 在实现前固定可重复的检索输入和规模负载，避免用正式四项数据代替验收。

- [X] T001 [P] 在 `tests/fixtures/search/fixed-skills.json` 创建固定检索样例：包含中英文名称/简介/用法、
  标签、平台、来源、作者、缺失元数据、代码/表格/中文路径、同分 slug；不写入正式 catalog 或 `skills/`。
  （FR-002、FR-003；AC-003、AC-004）
- [X] T002 [P] 在 `tests/support/search-fixture.js` 创建临时项目构建器：
  `createSearchFixtureProject` 生成 1,000 项、总正文 10 MiB 的 catalog/skills/最小 assets
  （含 `assets/app-search.js` 与现有前端模块）；
  `createDetailFixtureProject` 生成信息齐全和作者/版本缺失的可构建详情样例；
  `buildFixturePreview` 调用 `scripts/lib/build-site.js` 在系统临时目录生成 dist 并返回预览路径；
  另提供 50 条固定中英查询集。只写系统临时目录，不写工作区 `dist/`、不读取私人路径或凭证。
  （FR-003、NFR-002；AC-004、AC-015）

**Checkpoint**: 固定查询集和规模负载可复现；尚未修改站点行为。

## Phase 2: Foundational — 构建与测试前置

**Purpose**: 让新前端模块进入公开构建和快照身份，同时保持 US-001 的索引/详情契约不变。

- [X] T003 [P] 在 `tests/integration/search-assets.test.js` 先写失败契约：构建产物必须包含
  `assets/app-search.js`；修改该资产必须改变 `contentRevision`；索引/详情仍为 `schemaVersion=1`。
  （FR-004、FR-011；AC-014 本地部分）
- [X] T004 [P] 在 `scripts/lib/build-outputs.js` 的 `copyWebAssets` 增加 `assets/app-search.js`；
  缺失或非普通文件使整批构建失败，不跳过该资产。
  （FR-011、NFR-003；AC-014 本地部分）
- [X] T005 [P] 在 `scripts/lib/build-inputs.js` 的 `contentRevision` 资产清单增加 `assets/app-search.js`；
  不改变 `POLICY_VERSION` 的业务含义或索引 schema。
  （FR-011、NFR-006；AC-014 本地部分）
- [X] T006 [P] 更新以下测试夹具的临时 `assets/`，创建 `assets/app-search.js` 并保持 `index.html`
  脚本顺序可构建：`tests/integration/build-contract.test.js`、`tests/integration/build-recovery.test.js`、
  `tests/integration/distribution.test.js`、`tests/support/invalid-batch-project.js`。
  （FR-011；AC-014 本地部分）

**Checkpoint**: 新资产已被构建和快照身份覆盖，现有构建失败保留/恢复测试可继续运行。

## Phase 3: User Story 1 — 快速找到并筛选 Skill（Priority: P1）MVP

**Goal**: 访客可用精准/模糊模式、标签/平台/来源/作者组合筛选和排序找到 Skill，并通过地址恢复条件。

**Independent Test**: 只用 `tests/fixtures/search/fixed-skills.json` 和隔离临时项目，
验证固定查询集、模式切换、同维 OR/跨维 AND、排序、URL 恢复及空/加载/错误状态；
不依赖正式四项、生产站点、上传或自动更新。

### Tests for User Story 1

- [X] T007 [P] [US1] 在 `tests/unit/search-core.test.js` 先写失败契约：规范化（NFC/小写/空白折叠）、
  精准连续片段/双引号短语、模糊英文拼写容错、中文连续子串、名称优先排序、同分 slug、
  同维 OR/跨维 AND、缺失筛选值不匹配、URL 解析/构建往返、非法 mode/sort 回退、空 Hash 等价 `#/`。
  （FR-002；AC-003、AC-015）

### Implementation for User Story 1

- [X] T008 [US1] 实现 `assets/app-search.js` 纯模块（无 DOM）：`normalizeText`、`parseListHash`、
  `buildListHash`、`createSearchEngine`、`searchSkills`、`buildFilterOptions`、`buildDetailShareUrl`、
  `buildListShareUrl`；`mode` 仅 `fuzzy|exact` 且缺省 `fuzzy`，`sort` 仅 `auto|name|updated` 且缺省 `auto`，
  筛选数组去重，URL 参数白名单，复用 MiniSearch 6.3.0 的 `boost`/`prefix`/`fuzzy`。
  （FR-002、FR-004；NFR-002；AC-003、AC-005）
- [X] T009 [P] [US1] 在 `index.html` 于 `assets/app.js` 之前加载 `assets/app-search.js`，
  保留现有 `#app`、`#skill-count`、主题切换和 `/skill-gallery/` 相对路径。
  （FR-010；AC-013）
- [X] T010 [P] [US1] 改造 `assets/app.js`：加载索引后只构建一次搜索引擎；从列表 Hash 读取
  query/mode/tags/platforms/sourceTypes/authors/sort；筛选/排序复用一次搜索结果；
  列表状态用 `history.replaceState` 更新地址；进入详情前把列表 Hash 存入 `sessionStorage`；
  详情地址保持 `#/skill/<slug>`；不把查询写入公开详情身份。
  （FR-002、FR-004；AC-003、AC-005）
- [X] T011 [P] [US1] 改造 `assets/app-views.js`：搜索框、精准/模糊真实按钮、标签/平台/来源/作者
  checkbox、带标签的排序 select、命中数、当前条件、单项/全部清除、复制列表链接按钮、结果卡片
  （名称、一句话用途、标签、平台、版本、更新时间；版本缺失显示“未声明版本”、更新时间缺失显示“未提供”）
  和 loading/ready/empty_library/empty_results/load_failed 状态；结果计数使用
  `aria-live="polite"`，输入变化不丢焦点。
  （FR-002、FR-010；AC-003、AC-013）
- [X] T012 [US1] 使用 T002 的 `buildFixturePreview` 生成隔离 dist/预览，运行
  `tests/unit/search-core.test.js`、`tests/integration/search-assets.test.js` 和固定查询集验证；
  在 `specs/002-search-detail-share-redesign/validation/us2-search.md` 记录命令、退出码、
  查询/模式/筛选/排序/URL 恢复结果及未运行项；不依赖工作区 `dist/`。
  （FR-002、FR-004；AC-003、AC-005、AC-015）

**Checkpoint**: US1 可独立演示检索与筛选；复制/下载/详情尚未重新验收。

## Phase 4: User Story 2 — 完整理解并稳定分享（Priority: P1）

**Goal**: 访客看到完整、分区且缺失状态诚实的详情，并能复制稳定详情/列表地址；US-001 的取用能力不回退。

**Independent Test**: 用信息齐全和作者/版本缺失的隔离样例，检查详情分区、版本/内容标识、
旧链接、分享复制成功/失败及未知 slug；不依赖上传、自动更新或生产发布。

### Tests for User Story 2

- [X] T013 [P] [US2] 在 `tests/unit/share-link.test.js` 先写失败契约：详情地址为
  当前文档目录 + `#/skill/<slug>`；列表地址包含查询/模式/筛选/排序且无凭证；
  `contentIdentity` 在声明版本缺失时返回 `digest` 前 12 位，声明版本存在时不把版本当内容身份。
  （FR-003、FR-004；AC-004、AC-005）

### Implementation for User Story 2

- [X] T014 [US2] 改造 `assets/app-actions.js`：使用 `app-search.js` 的详情/列表地址构建器，
  接上 T011 的“复制列表链接”按钮和详情分享按钮；复制成功仅在真实写入后提示，失败显示可手动复制值；
  保留原文复制、单文件/目录包/附件下载的响应/大小/摘要校验和
  `raw_unavailable`/`copy_failed`/`download_failed` 状态。
  （FR-004；AC-005、AC-012）
- [X] T015 [US2] 改造 `assets/app-detail.js`：首屏按名称、简介、版本/内容标识、作者、来源、
  下载/复制/分享入口排列；其下分区展示 `description`（功能简介）、`usage`（适用场景与使用方法）、
  `notes`（备注）、原文、附件和来源元数据；
  `declared_version` 存在时显示版本，否则显示 `digest` 前 12 位内容标识；
  `author`/`homepage_url`/`repository_url`/`license`/`updated_at` 缺失显示“未提供”；
  `body_html` 只作已清理 HTML 使用，外链仅安全协议，未知 slug/加载失败/快照不一致有明确状态。
  （FR-003、FR-010；AC-004、AC-012）
- [ ] T016 [US2] 使用 T002 的 `createDetailFixtureProject`/`buildFixturePreview` 生成隔离详情 dist 和预览；
  执行四个旧 `#/skill/<slug>` 链接、刷新、同 slug 更新、信息齐全/缺失详情、复制详情/列表地址、
  剪贴板拒绝、未知 slug、原文复制和原件/ZIP/附件下载回归；在
  `specs/002-search-detail-share-redesign/validation/us2-detail.md` 记录实际结果和未运行项；
  不依赖工作区 `dist/`。
  （FR-003、FR-004；AC-004、AC-005、AC-012，US-001 AC-002 回归）

**Checkpoint**: US2 可独立演示完整详情和稳定分享，US-001 取用能力不回退。

## Phase 5: User Story 3 — 多种设备与主题下无障碍使用（Priority: P2）

**Goal**: 360/768/1440px、明暗主题、纯键盘和减少动效偏好下完成主要流程，正文外无溢出。

**Independent Test**: 在三种宽度、两种主题、纯键盘和当前稳定 Chromium/Firefox/WebKit 中完成
搜索、筛选、详情、下载、分享；记录焦点、对比度、溢出、浏览器版本及未运行项。

### Implementation for User Story 3

- [ ] T017 [P] [US3] 改造 `assets/style.css`：桌面筛选/结果分栏、移动端折叠筛选/单列卡片、
  明暗主题、焦点样式、正文对比 ≥4.5:1、减少动效媒体查询、代码块内部横向滚动、
  正文外无横向溢出；不使用粒子背景、自动播放视频或大面积霓虹。
  （FR-010、NFR-005；AC-013）
- [ ] T018 [P] [US3] 补全 `assets/app-views.js` 和 `assets/app-detail.js` 的可访问语义：
  真实 button/checkbox/select/link、可见标签、移动筛选 `aria-expanded`/`aria-controls`、
  结果计数和动作状态 `aria-live`、焦点保持/返回、错误状态可恢复。
  （FR-010、NFR-005；AC-013）
- [ ] T019 [P] [US3] 改造 `assets/app.js` 主题与焦点：优先读取已保存主题，无保存值时跟随
  `prefers-color-scheme`；切换后持久化；路由切换后把焦点放到主标题或返回控件，
  不改变详情/列表地址契约。
  （FR-010、NFR-005；AC-013）
- [ ] T020 [US3] 使用 T002 的 `buildFixturePreview` 生成隔离 dist 和预览，用浏览器完成
  360/768/1440、明暗主题、纯键盘和减少动效验证；记录 Chromium/Firefox/WebKit 版本、焦点路径、
  对比度、溢出和截图/操作记录到
  `specs/002-search-detail-share-redesign/validation/us2-accessibility.md`；未运行浏览器不得写成通过；
  不依赖工作区 `dist/`。
  （FR-010、NFR-005；AC-013）

**Checkpoint**: 三个故事均可在本地独立演示；进入跨场景回归与性能收口。

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 完成全量检查、性能证据、US-001 回归和范围复核，不新增业务能力。

- [ ] T021 [P] 运行 `npm run lint`、`npm run format:check`、`npm test`、`npm run security`
  （secrets/code/deps），只修复本故事引入的失败；记录实际命令、退出码、测试数量、扫描结果和未运行项。
  不得为通过而格式化原件或无关文件，也不得把工具缺失/AUDIT_UNAVAILABLE 当通过。
  （NFR-003、NFR-006；AC-012、AC-014 工程支撑）
- [ ] T022 [P] 使用 T002 的 `createSearchFixtureProject`/`buildFixturePreview` 生成隔离的
  1,000 项/10 MiB dist 和预览，在真实浏览器执行 50 次固定中英查询；记录查询到结果可见的 p95、
  设备、浏览器、查询集；候选通过线 200ms，排除网络；证据写入
  `specs/002-search-detail-share-redesign/validation/us2-performance.md`；不依赖工作区 `dist/`。
  （NFR-002；AC-015）
- [ ] T023 在隔离副本运行 `npm run build` 和 `npm run preview`（或使用 T002 的隔离构建辅助），
  核对 `dist/assets/app-search.js` 存在、`/skill-gallery/` 子路径、四个旧详情链接、刷新和当前单版本；
  记录到 `validation/us2-build.md`，不写工作区 `dist/` 或根 `assets/search-index.json`、不提交 `dist/`。
  （FR-004、FR-011；AC-005、AC-014 本地部分）
- [ ] T024 在 T023 的隔离构建上回归 US-001：原文复制、单文件/目录包/附件下载、旧链接、
  当前单版本和失败反馈；记录到 `validation/us2-regression.md`，不以 US-002 结果宣称生产发布。
  （FR-004；AC-002、AC-005 回归）
- [ ] T025 只定向更新 `README.md`、`AGENTS.md` 中本故事已实现并验证的命令、浏览器/性能证据、
  搜索/筛选/分享行为和未完成项；上传、自动更新、生产发布仍标规划，不写假命令。
  （NFR-006；AC-014 工程支撑）
- [ ] T026 对照 `specs/002-search-detail-share-redesign/validation/` 与 T001 做最终差异复核：
  六原件/catalog/根 `assets/search-index.json` 未改写、无凭证/额外依赖/全仓格式化、无 schema 变更、
  四旧链接与单版本保持、无新增管理员后台/访客登录/站内写入、若保留管理外链则低权重且使用安全协议、
  T041 macOS 缺口仍记录、未合并 main/未发布；更新 tasks/plan 状态并列出未运行项与剩余风险。
  （FR-004、FR-011；NFR-003、NFR-006；AC-005、AC-012、AC-014 本地部分）

## Dependencies & Execution Order

### Phase Dependencies

```text
T001,T002 ─┬─ T003 ─┬─ T004 ─┐
           │        └─ T005 ─┼─ T006
           └──────────────────┘

Phase 2 完成
  └─ T007 → T008 → {T009, T010, T011} → T012 (US1 gate)

T012 → T013 → {T014, T015} → T016 (US2 gate)

T016 → {T017, T018, T019} → T020 (US3 gate)

T020 → {T021, T022}
       └─ T023 → T024 → T025
T020 + T021..T025 → T026 (final gate)
```

T002 的隔离项目/构建辅助供 T012、T016、T020、T022 使用；这些任务不依赖 T023 或工作区 `dist/`。
T023 是一次独立的四项隔离构建，T024 在它之上回归；T022 的 1,000 项负载不读取正式四项。

### User Story Dependencies

- **US1**: 只依赖 Phase 2 的构建/测试前置，是 MVP；不依赖 US2/US3。
- **US2**: 复用 US1 的地址构建器和详情入口，可独立验证详情/分享；列表分享回归在 T016 覆盖。
- **US3**: 依赖 US1/US2 的 DOM 结构；独立验证可访问性与响应式，不改变检索/详情契约。

### Within Each User Story

- 先写测试并确认真实失败，再实现；已由共享层覆盖的行为直接复验，不伪造失败。
- 搜索核心先于列表集成；详情/分享先于视觉/可访问改造。
- 同一文件（`assets/app-views.js`、`assets/app-detail.js`、`assets/app.js`、`assets/style.css`）
  只能串行修改；不同文件可并行，但由单一执行者控制。

## Parallel Examples

### User Story 1

T009（index.html）、T010（app.js）、T011（app-views.js）在 T008 完成后可并行；T012 等三者完成。

### User Story 2

T014（app-actions.js）和 T015（app-detail.js）在 T013 后可并行；T016 等两者完成。

### User Story 3

T017（style.css）、T018（app-views/app-detail）、T019（app.js）在 US2 后可并行；
T020 等三者完成。T022 的性能浏览器与 T023 的构建预览使用不同工作副本或串行，避免共享 dist。

## Implementation Strategy

### MVP First

先完成 Phase 1～3（T001～T012），只交付可独立验证的检索/筛选/URL 列表；不把详情、视觉或性能
声称为完成。通过 US1 固定查询集后再进入 US2。

### Incremental Delivery

US1 检索 → US2 详情/分享 → US3 响应式/可访问 → Polish 性能/回归/文档。
每一步在隔离副本验证，前一步通过后再继续；不自动推送、合并 main 或发布。

## Notes

- 不执行 `skills/` 中任何脚本/测试，不安装其依赖；搜索夹具只作数据。
- `contentRevision` 纳入 `assets/app-search.js` 后，构建身份变化是预期行为；
  不得为保持旧 revision 而遗漏资产。
- 详情中的 `usage` 映射“适用场景与使用方法”，`notes` 映射备注；不新增 catalog 字段或迁移。
- 性能 p95 必须在浏览器中测结果可见时间；Node 微基准和四项数据不能替代 AC-015。
- T012/T016/T020/T022/T023 的 dist/预览来自隔离临时项目；不覆盖或清理工作区 `dist/`。
- T021 必须执行 `npm run security`；工具缺失、网络失败或 `AUDIT_UNAVAILABLE` 不能算通过。
- T041 macOS、生产 Pages MIME/缓存/直接资源安全和 Q-004 调度保持原状态；不因本故事勾选而关闭。
- 提交按逻辑组拆分，仅暂存本故事文件；推送、合并 main 和生产发布需单独明确授权。
