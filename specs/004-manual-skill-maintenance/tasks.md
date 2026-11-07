---
description: "US-004 管理员手动维护的实施任务"
---

# Tasks: US-004 管理员手动维护

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[research.md](research.md)、[data-model.md](data-model.md)、
[manual-maintenance 契约](contracts/manual-maintenance.md)、[quickstart.md](quickstart.md)。日期：2026-11-07。

**Prerequisites**: [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0，
以及 US-003 已交付的发布链与 validation 证据。

**Status**: 任务于 2026-11-07 生成；当前 17 项。T001–T017 已完成（本地/受控；生产未启用）。
证据入口：T001 [validation/preflight.md](validation/preflight.md)，T002/T005/T008
`tests/integration/manual-maintenance.test.js`，T003/T006/T009 `README.md`，T004
[validation/manual-add.md](validation/manual-add.md)，T007 [validation/manual-failures.md](validation/manual-failures.md)，
T010 [validation/manual-replace-remove-recovery.md](validation/manual-replace-remove-recovery.md)，
T011–T013 `tests/unit/site-entry.test.js` 与 [validation/admin-entry.md](validation/admin-entry.md)，
T014 [validation/manual-quality.md](validation/manual-quality.md)，T015 `README.md`/`AGENTS.md`，
T016 [validation/manual-poc.md](validation/manual-poc.md)，T017
[validation/manual-final-review.md](validation/manual-final-review.md)。分支
`codex/us-004-manual-maintenance`（从 US-003 分支堆叠，未合并 main）。生产 Pages 未切换；
手动发布验收只在隔离副本与受控仓库（POC-002）授权范围内进行。

**Tests**: 宪章 IX 要求先建立能识别错误行为的验证。新增站点入口静态测试与手动维护集成测试；
复用 US-003 的构建/发布链，不重复实现发布校验器。

**Organization**: 四个用户故事对应 [spec.md](spec.md) 的内部切片。同文件任务必须串行；
`[P]` 不授权多 Agent。

## Format: [ID] [P?] [Story] Description

- 每项严格使用 `- [ ] Txxx [P?] [USx?] 描述 + 文件路径`。
- `[P]` 只表示不同文件、无未完成依赖时可并行；同一文件任务不得并行。
- Setup/Polish 不加故事标签；User Story 阶段必须加 `[US1]`～`[US4]`。
- 路径相对项目根；`dist/` 是生成目录，不手改、不提交。

## Phase 1: Setup — 基线与验证落点

**Purpose**: 固定当前分支、构建/测试基线和生产状态，为后续故事提供可复现记录。

- [X] T001 [P] 在 `specs/004-manual-skill-maintenance/validation/preflight.md` 记录：分支与 HEAD、
  Node/npm 实际版本与锁定版本、现有测试数量、首页页脚现状、生产 Pages 仍为 `legacy`、
  POC-002 可用性与本轮授权边界；不读取或打印凭证。（NFR-006；AC-006）

**Checkpoint**: 基线可复现；尚未修改页面或文档。

## Phase 2: User Story 1 — 通过 GitHub 后台上传并发布 Skill（Priority: P1）MVP

**Goal**: 合法单文件/目录型 Skill 与站内记录经手动提交后完成校验、构建和发布；访客可见。

**Independent Test**: 隔离副本新增单文件与目录型 Skill，构建后索引/详情/下载正确；仅改元数据
不改写原件字节。

### Tests for User Story 1

- [X] T002 [US1] 在 `tests/integration/manual-maintenance.test.js` 建立手动维护集成契约：
  使用隔离项目新增单文件与目录型 Skill（含 `catalog` 记录），调用现有构建并断言索引/详情/
  原件下载/目录 ZIP；仅修改站内元数据时原件字节不变；重复构建同一内容稳定。
  （FR-005、NFR-001；AC-006）

### Implementation / Validation for User Story 1

- [X] T003 [US1] 在 `README.md` 增加“手动维护（GitHub 后台）”章节：单文件/目录上传步骤、必填
  记录字段、提交到默认分支后的校验/构建/发布结果、成功与未发布状态的区分；不写未验证命令。
  （FR-005、NFR-006；AC-006）
- [X] T004 [US1] 在隔离副本执行新增流程（单文件与目录型各一次），记录命令、构建结果、
  `contentRevision`、索引/详情/下载检查和未运行项到
  `specs/004-manual-skill-maintenance/validation/manual-add.md`。
  （FR-005、NFR-006；AC-006）

**Checkpoint**: 合法手动新增可独立验证；尚未覆盖失败、替换和下架。

## Phase 3: User Story 2 — 非法输入整批阻止且旧站保留（Priority: P1）

**Goal**: 任一非法条目使整批失败，不部署；旧站与旧产物保持，诊断可定位。

**Independent Test**: 隔离副本提交缺字段、缺附件、越界路径或凭证批次，确认构建失败且旧 `dist/`
文件集合与摘要不变。

### Tests for User Story 2

- [X] T005 [US2] 在 `tests/integration/manual-maintenance.test.js` 增加失败用例：缺必填字段、
  缺失附件、越界路径、伪造凭证文件（运行时构造或占位符）全部失败关闭；诊断只含位置/规则，
  不回显值；失败前后旧 `dist/` 不变。（FR-005、FR-007、FR-009；AC-006、AC-008、AC-011）

### Implementation / Validation for User Story 2

- [X] T006 [US2] 在 `README.md` 补充失败处理：字段/附件/路径/凭证错误的定位方式、整批阻止和
  旧站保留、重新提交要求；示例只使用占位凭证。（FR-005、FR-007；AC-006、AC-008）
- [X] T007 [US2] 在隔离副本执行失败批次（至少缺字段、缺附件、凭证文件各一次），记录退出码、
  诊断码、旧产物不变证据与未运行项到
  `specs/004-manual-skill-maintenance/validation/manual-failures.md`。
  （FR-005、FR-009；AC-006、AC-011）

**Checkpoint**: 失败阻止与旧站保留可独立验证。

## Phase 4: User Story 3 — 显式替换、下架与受控恢复（Priority: P2）

**Goal**: 替换保持单版本并清理旧附件；下架移除索引/详情/下载；恢复通过受控历史重建。

**Independent Test**: 隔离副本替换同 slug、删除附件后重建；下架后检查产物消失；`git revert`
后 `contentRevision` 回到基线且 slug/旧链接保持。

### Tests for User Story 3

- [X] T008 [US3] 在 `tests/integration/manual-maintenance.test.js` 增加替换/下架/恢复用例：
  替换后单版本且旧附件不残留；删除原件与记录后索引/详情/ZIP 消失；受控 revert 重建后
  `contentRevision` 与基线一致、slug 不变。（FR-005、FR-009；AC-006、AC-011）

### Implementation / Validation for User Story 3

- [X] T009 [US3] 在 `README.md` 补充显式替换、下架和受控恢复步骤，说明单版本、旧附件清理、
  不处理未纳管文件、不 force push。（FR-005、FR-009；AC-006、AC-011）
- [X] T010 [US3] 在隔离副本执行替换/下架/恢复，记录命令、产物差异、`contentRevision` 和未运行项到
  `specs/004-manual-skill-maintenance/validation/manual-replace-remove-recovery.md`。
  （FR-005、FR-009；AC-006、AC-011）

**Checkpoint**: 替换、下架与恢复可独立验证。

## Phase 5: User Story 4 — 可见但低权重的管理入口（Priority: P2）

**Goal**: 页脚提供指向受信任仓库的管理外链；无站内登录/上传入口；入口不改变只读能力。

**Independent Test**: 静态断言入口 href/rel、无表单/文件输入；构建后首页包含该入口。

### Tests for User Story 4

- [X] T011 [P] [US4] 在 `tests/unit/site-entry.test.js` 建立入口契约：页脚“管理”链接指向
  `https://github.com/chengxuan2002-droid/skill-gallery`、`target="_blank"`、`rel="noopener"`；
  首页无登录表单、`<input type="file">` 或上传按钮。（FR-007、FR-010；AC-008）

### Implementation / Validation for User Story 4

- [X] T012 [US4] 修改 `index.html` 与 `assets/style.css`：页脚增加低权重“管理”外链，
  不改变主视觉、搜索/详情行为或运行时依赖。（FR-007、FR-010；AC-008）
- [X] T013 [US4] 运行入口测试与隔离构建，记录链接、构建后首页包含情况、未运行项到
  `specs/004-manual-skill-maintenance/validation/admin-entry.md`。
  （FR-007、FR-010；AC-008）

**Checkpoint**: 四个故事均可独立验证。

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 全量检查、受控发布验收、文档状态和最终复核。

- [X] T014 [P] 运行 `npm test`、`npm run lint`、`npm run format:check`、`npm run security`；
  只修复本故事引入的问题；记录实际命令、退出码、测试数量、扫描结果和未运行项到
  `specs/004-manual-skill-maintenance/validation/manual-quality.md`。
  （NFR-003、NFR-006；AC-008）
- [X] T015 [P] 定向更新 `README.md`、`AGENTS.md` 中本故事已实现并验证的入口、手动维护流程、
  受控结果和未完成项；US-005～US-007 仍标规划；不写未验证命令或线上成功。
  （NFR-006；AC-006）
- [X] T016 在受控临时仓库 POC-002 执行等价手动提交（新增、非法批次、替换、下架），确认
  校验/构建/发布与失败保留；记录运行 URL、目标 SHA、`contentRevision` 和未运行项到
  `specs/004-manual-skill-maintenance/validation/manual-poc.md`；生产 Pages 未切换。
  （FR-005、FR-009；AC-006、AC-011）
- [X] T017 对照 `spec.md`、`contracts/` 和 `validation/` 做最终差异复核：未改内容 schema、
  搜索/详情前端、发布权限或生产 Pages；失败项和未运行项单独列出；更新 tasks/plan 状态，
  记录到 `specs/004-manual-skill-maintenance/validation/manual-final-review.md`。
  （FR-005、FR-007、FR-009；AC-006、AC-008、AC-011）

## Dependencies & Execution Order

```text
T001 ──┬─ US1: T002 → T003 → T004
       ├─ US2: T005 → T006 → T007（T005 依赖 T002 的测试夹具）
       ├─ US3: T008 → T009 → T010（T008 依赖 T002 的测试夹具）
       └─ US4: T011 → T012 → T013
                    │
        T014, T015 ─┴→ T016 → T017
```

- T001 无依赖；US1 是 MVP，完成后再进入 US2/US3。
- `tests/integration/manual-maintenance.test.js` 由 T002/T005/T008 串行修改；`site-entry.test.js`
  独立，可与 US1～US3 并行。
- T014/T015 可并行；T016 依赖实现与文档完成；T017 最后执行。

### User Story Dependencies

- **US1**: 仅依赖 Setup；交付合法新增与发布说明。
- **US2**: 依赖 US1 的测试夹具与 README 章节；独立验证失败保留。
- **US3**: 依赖 US1 的测试夹具与 README 章节；独立验证替换/下架/恢复。
- **US4**: 与 US1～US3 独立；只改页面入口与样式。

### Within Each User Story

- 先写测试并确认真实失败，再实现/执行验证；已由 US-003 覆盖的行为直接复验，不伪造失败。
- 同一文件只能串行修改；不同文件可并行。
- 真实生产发布未授权；受控仓库步骤单独记录，未授权时写未运行。

## Parallel Examples

### Setup

T001 可立即执行。

### User Stories

US1 与 US4 可在 T001 后并行；US2/US3 共用同一集成测试文件，必须在 T002 之后串行追加。
T003/T006/T009 都修改 `README.md`，需串行。

### Polish

T014（检查）与 T015（文档）为不同文件，可并行；T016/T017 串行收尾。

## Implementation Strategy

### MVP First

先完成 T001～T004：手动新增、README 说明与隔离证据；不声称失败/替换/下架或生产发布已完成。

### Incremental Delivery

Setup → US1 新增 → US2 失败保留 → US3 替换/下架/恢复 → US4 管理入口 → 全量检查/受控验收/最终复核。
每个故事在隔离副本验证；受控仓库步骤单独授权、单独报告。

## Notes

- 不执行 `skills/` 中任何脚本/测试，不安装其依赖；手动维护说明不得指引执行第三方内容。
- 不新增 npm 依赖；不改内容 schema、搜索/详情前端或 US-003 发布链。
- 生产 Pages 源、environment、分支保护和线上切换不在任务默认授权内；T016 使用受控仓库，
  未获授权时必须记录未运行。
- 提交按逻辑组拆分，仅暂存本故事文件；推送、合并 main 和生产发布需单独明确授权。
