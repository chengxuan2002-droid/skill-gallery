---
description: "US-006 来源定期检查与自动替换的实施任务"
---

# Tasks: US-006 来源定期检查与自动替换

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[research.md](research.md)、[data-model.md](data-model.md)、
[source-sync 契约](contracts/source-sync.md)、[workflow 契约](contracts/workflow-sync.md)、[quickstart.md](quickstart.md)。
日期：2026-11-12。

**Prerequisites**: [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0，
US-003 发布链、US-004 手动维护规则与 US-005 CLI 候选/工作副本基线。

**Status**: 任务于 2026-11-12 生成；当前 30 项。T001–T030 已完成本地/受控验证和生产启用。
tasks 勾选不代表 US-007 整体验收通过。
证据入口：`validation/preflight.md`、`us6-check.md`、`us6-apply.md`、`us6-conflict.md`、`us6-status.md`、
`us6-workflow.md`、`us6-quality.md`、`us6-poc.md`、`us6-license.md`、`us6-final-review.md`、`us6-quickstart.md`。

**Tests**: 宪章 IX 要求先建立能识别错误行为的验证。默认测试使用注入来源读取器、临时 Git 仓库和
临时裸远端，不访问真实 GitHub、不执行上游脚本、不推送真实远端。

**Organization**: 规格中的 User Story 1～5 是本故事内部验收切片，对应 `[US1]`～`[US5]`；
同一文件任务必须串行，`[P]` 不授权多 Agent。

## Format: `[ID] [P?] [Story] Description`

- 每项严格使用 `- [ ] Txxx [P?] [USx?] 描述 + 文件路径`。
- `[P]` 只表示不同文件、无未完成依赖时可并行；同一文件任务不得并行。
- Setup/Foundational/Polish 不加故事标签；User Story 阶段必须带 `[US1]`～`[US5]`。
- 路径相对项目根；`dist/` 是生成目录，不手改、不提交。

## Phase 1: Setup — 基线与实施前核实

- [X] T001 [P] 在 `specs/006-source-auto-update/validation/preflight.md` 记录：分支与 HEAD、
  Node/npm 实际值与锁定版本、`gh`/Git 可用性（不读取 token）、当前 `npm test` 基线、`maintain.yml`
  状态、POC-002/POC-003 授权与边界。（NFR-006；AC-011）
- [X] T002 [P] 用 Context7 复核 GitHub Actions `schedule`/`workflow_dispatch`/`permissions`/checkout
  行为与 GitHub REST Release/Tree/Blob 当前语义；把结论与版本依据追加到
  `specs/006-source-auto-update/validation/preflight.md`，不执行真实来源写入。（FR-008；AC-009）

## Phase 2: Foundational — 共享读取、候选与报告骨架

**⚠️ CRITICAL**: 本阶段完成前，各用户故事无法独立验证。

- [X] T003 [P] 在 `tests/unit/github-source.test.js` 建立来源读取契约：结构化 `owner/repository`、
  POSIX `path`、branch/release/pinned 解析到不可变 40 位 SHA、Release 缺失为 unavailable、
  truncated/子模块/符号链接/越界路径拒绝、500 文件/20 MiB/主文档 1 MiB 限制、
  `mode`/可执行位保留、稳定错误码与诊断脱敏。（FR-008、NFR-001、NFR-003；AC-009、AC-012）
- [X] T004 [P] 在 `tests/unit/source-sync-state.test.js` 建立状态与报告契约：
  `unconfigured/paused/unsupported`、`unchanged/candidate/updated/failed/conflict/policy_blocked`、
  `commit_status`/`content_status`/`deploy_status` 分离、退出码 `0/2/4/5/6`、无变化不伪造提交、
  报告字段封闭。（FR-008、FR-009；AC-010、AC-011）
- [X] T005 [P] 在 `tests/support/source-sync-fixture.js` 建立夹具：临时项目与 catalog、
  临时裸远端、注入来源读取器、两修订候选（增删文件/二进制/许可）、失败与冲突注入；
  只写系统临时目录并在结束时清理。（FR-008、NFR-003；AC-009）
- [X] T006 实现 `scripts/lib/github-source.js`：从 `scripts/lib/skill-cli/source-github.js` 提取
  来源校验、修订解析、完整树/blob 读取、mode 保留、大小/文件数限制、来源子树许可发现、
  超时/重试与稳定错误码；把原入口改为薄兼容出口并保持 US-005 import 行为。
  （FR-008、NFR-001、NFR-003；AC-009、AC-012）
- [X] T007 实现 `scripts/lib/source-sync-report.js` 与 `scripts/sync-skills.js` 骨架：
  `--slug`、`--apply`、`--push`、`--json`、`--report`、`--summary`、`--help`；单行 JSON、
  stderr 脱敏、报告写入与退出码；不接受 URL/token/文件内容参数。
  （FR-009、NFR-003；AC-011、AC-012）
- [X] T008 实现 `scripts/lib/source-sync.js` 的候选与摘要：把来源文件转换为目标记录相对的候选，
  复用 `snapshotSkill`/`computeDigest`/`catalog-schema`/`validateSkillInput`/`scanSecrets`；
  候选只作为数据读取，不执行脚本、不安装依赖。（FR-008、NFR-001；AC-009、AC-012）

**Checkpoint**: 共享读取、候选、报告骨架可用；尚未写工作区或推送。

## Phase 3: User Story 1 — 定期检查与无变化判定（Priority: P1）

**Goal**: 启用来源后可检查固定修订、比较内容摘要、输出真实状态；无变化不写 Git。

**Independent Test**: 用注入来源执行 check，覆盖无变化、候选、幂等、404/403/429/超时/截断和
pinned/Release 不可用；工作区无写入、无提交。

- [X] T009 [US1] 在 `tests/integration/source-sync-check.test.js` 建立检查契约：check 模式零写入；
  相同摘要为 `unchanged`；内容变化为 `candidate`；重复检查幂等；单个来源失败不影响其他来源；
  报告包含真实 `checked_at` 与 `resolved_revision`。（FR-008、FR-009；AC-009、AC-010）
- [X] T010 [US1] 实现 `scripts/lib/source-sync.js` 的检查链路：按 `enabled` 与可选 `--slug`
  选择来源，标记 unconfigured/paused/unsupported；解析修订、读取完整树、校验候选、比较
  `last_synced_digest` 与当前内容摘要，输出逐项状态；不写工作区、不提交。
  （FR-008、FR-009；AC-009、AC-010）
- [X] T011 [US1] 在隔离临时仓库按 quickstart 第 2 节执行检查，记录命令、退出码、JSON 状态、
  检查时间、来源修订与未运行项到 `specs/006-source-auto-update/validation/us6-check.md`。
  （FR-008；AC-009）

**Checkpoint**: US1 可独立演示；无变化检查不产生 Git 提交。

## Phase 4: User Story 2 — 单版本完整替换（Priority: P1）

**Goal**: 候选通过完整校验后整体替换当前内容，删除上游已删除文件，保留 slug 与站内元数据。

**Independent Test**: 两个受控修订，v2 新增文件并删除 v1 附件；apply 后逐路径/逐字节核对当前内容、
catalog、提交清单与索引，确认只有一个版本。

- [X] T012 [US2] 在 `tests/integration/source-sync-apply.test.js` 建立 apply 契约：v2 增删文件、
  声明版本不变但正文/附件变化、单文件與目录互换、站内 display_name/tags/notes/usage 保留、
  只生成一个批次提交且不含无关文件、旧附件消失、重复 apply 幂等。
  （FR-008、NFR-001；AC-009）
- [X] T013 [US2] 实现 `scripts/lib/source-sync.js` 的应用链路并扩展
  `scripts/lib/skill-cli/workspace.js`：首次基线规则（无摘要时同内容可建基线，否则 conflict）、
  当前摘要偏离时 conflict、删除旧路径、写候选与 `catalog/<slug>.json`、仅更新
  `last_synced_revision`/`last_synced_digest`/`synced_at`、批次提交、非 force 推送。
  （FR-008、NFR-004；AC-009、AC-010）
- [X] T014 [US2] 在临时裸远端执行一次完整替换，记录 `git show --stat`、文件清单/字节核对、
  站内字段保留与未运行项到 `specs/006-source-auto-update/validation/us6-apply.md`。
  （FR-008、NFR-001；AC-009）

**Checkpoint**: US2 可独立演示；当前树只保留一个版本。

## Phase 5: User Story 3 — 许可、本地修改与冲突保护（Priority: P1）

**Goal**: 许可缺失/变化、本地修改、远端基线前进和非法候选失败关闭，保留当前版本。

**Independent Test**: 分别注入许可缺失/变化、本地摘要偏离、并发基线变化、越界/链接/子模块/
超大候选与单来源失败，确认当前内容与站点不变。

- [X] T015 [US3] 在 `tests/integration/source-sync-conflict.test.js` 与
  `tests/unit/github-source.test.js` 建立失败矩阵：来源子树许可缺失/路径变化/
  字节变化为 `policy_blocked`；本地内容偏离 `last_synced_digest` 为 `conflict`；远端前进或推送
  被拒绝为 `conflict`；非法候选为 `failed`；一个来源失败不阻断其他来源。
  （FR-008、NFR-003；AC-010、AC-012）
- [X] T016 [US3] 实现 `scripts/lib/source-sync.js` 与 `scripts/lib/github-source.js` 的许可策略、
  冲突检测和失败关闭：仅认来源子树许可；任何阻断不写入目标文件；诊断只含稳定码与位置。
  （FR-008、NFR-003；AC-010、AC-012）
- [X] T017 [US3] 在隔离环境执行失败矩阵，记录逐项状态、当前内容保留、诊断脱敏与未运行项到
  `specs/006-source-auto-update/validation/us6-conflict.md`。（FR-008；AC-010）

**Checkpoint**: US3 可独立演示；失败不删除或覆盖当前版本。

## Phase 6: User Story 4 — 状态记录、重跑与恢复（Priority: P2）

**Goal**: 运行记录区分检查、提交、构建与部署；部署失败保留旧站，可按同一提交重跑。

**Independent Test**: 模拟无变化、有更新、构建失败、部署失败、并发过期和恢复提交，核对运行
报告、重跑幂等、旧站保留与历史未改写。

- [X] T018 [P] [US4] 在 `tests/unit/source-sync-report.test.js` 建立报告/摘要契约：逐来源状态、
  检查时间、修订、摘要、许可状态、`commit_status`/`content_status`/`deploy_status` 分离、
  `updated` 必须有提交 SHA、`unchanged` 不得伪造提交、摘要不含敏感上下文。
  （FR-009；AC-011）
- [X] T019 [US4] 完成 `scripts/lib/source-sync-report.js` 与 `scripts/sync-skills.js` 的报告输出：
  封闭 JSON、脱敏 Markdown 摘要、运行标识/触发方式/提交状态，并为 build/deploy 摘要提供
  同一 `commit_status` 与目标 SHA 输入。（FR-009；AC-011）
- [X] T020 [US4] 在受控 POC 模拟部署失败、同提交重跑和受控 revert 恢复，记录“提交成功、部署
  失败”、旧站保留、未新增内容提交与 slug/历史保持到
  `specs/006-source-auto-update/validation/us6-status.md`。（FR-009；AC-011）
  **结果**：部署失败/旧站保留、同提交重跑、受控 revert 恢复均已完成，见 `validation/us6-status.md`。

**Checkpoint**: US4 可独立演示；状态不把提交成功写成部署成功。

## Phase 7: User Story 5 — 每日调度与运维说明（Priority: P2）

**Goal**: 每日 03:17 Asia/Shanghai 与手动触发共用同一代码路径；README 说明配置、状态、失败与恢复。

**Independent Test**: 在受控仓库验证手动/计划同一代码路径、时区、开关、无变化运行和失败重跑；
从干净 checkout 按 README 完成一次来源查看、失败处理和恢复演练。

- [X] T021 [P] [US5] 在 `tests/integration/publish/publish-sync-workflow.test.js` 建立工作流
  结构与安全断言：`schedule` cron 为 UTC `17 19 * * *`、`workflow_dispatch` 输入 `sync/slug`、
  `sync` 仅在 schedule/manual sync 时运行、仅 `sync` 拥有 `contents: write`、build/deploy 最小
  权限、checkout 使用 sync 提交、deploy 使用 build 的 target SHA、无第二条发布 workflow、
  `persist-credentials: false`、`GH_TOKEN` 只在 sync 步骤。（FR-007、FR-009；AC-008、AC-011）
- [X] T022 [US5] 扩展 `.github/workflows/maintain.yml`：新增 `sync` job、schedule、dispatch 输入、
  `changed`/`commit_sha`/`commit_status` 输出、30 分钟超时、同次运行 build/deploy 衔接与脱敏摘要；
  build/deploy 保持只读/最小权限。（FR-008、FR-009；AC-011、AC-014）
- [X] T023 [P] [US5] 更新 `README.md` 与 `AGENTS.md` 的 US-006 运维章节/状态：来源配置、启停、
  状态查看、许可/本地冲突、失败重跑、受控恢复、03:17 Asia/Shanghai 时区与未授权边界；示例只用
  占位凭证，不写未验证的生产成功。（FR-009、NFR-003；AC-008、AC-011）
- [X] T024 [US5] 在受控仓库手动触发 `sync=true/slug=...` 与 `sync=false`，验证与计划运行同一
  代码路径、无变化跳过 build/deploy、手动重发当前快照；记录运行 URL 与未运行项到
  `specs/006-source-auto-update/validation/us6-workflow.md`。（FR-008、FR-009；AC-011）

**Checkpoint**: US5 可独立演示；生产调度已于 2026-11-13 启用（T030）。

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T025 [P] 运行 `npm test`、`npm run lint`、`npm run format:check`、`npm run security`，
  记录退出码、测试数量、扫描结果与未运行项到
  `specs/006-source-auto-update/validation/us6-quality.md`。（NFR-003、NFR-004；AC-008）
- [X] T026 执行 POC-003：在受控公开 GitHub 源仓库验证 branch/release/pinned、两修订增删文件、
  二进制、许可、真实 404/403 与注入的截断/链接夹具；记录 run URL、提交 SHA、逐来源状态、
  旧附件删除与未运行项到 `specs/006-source-auto-update/validation/us6-poc.md`。
  （FR-008；AC-009、AC-010、AC-012）
- [X] T027 复核 `spec.md`、`contracts/` 与全部 `validation/`：未改公开搜索/详情、内容 schema
  或生产调度；失败项与未运行项单独列出；更新 tasks/plan 状态并记录到
  `specs/006-source-auto-update/validation/us6-final-review.md`。（FR-008、FR-009；AC-011）
- [X] T028 在干净副本按 [quickstart.md](quickstart.md) 复核命令、退出码、报告字段和失败路径，
  记录结果与偏差到 `specs/006-source-auto-update/validation/us6-quickstart.md`。
  （NFR-006；AC-011）
- [X] T029 持久化 `source_tracking.last_synced_license`（路径 + sha256）：扩展 schema、检查与 apply
  链路；补单文件/目录许可缺失、路径变化和字节变化测试；记录到
  `specs/006-source-auto-update/validation/us6-license.md`。（FR-008；AC-010、AC-012）
- [X] T030 合并 PR #6 并启用生产 `main` 调度；验证 push run 43421560371 的 build/deploy 与手动
  sync run 43421951464 的无变化路径，记录到 `validation/us6-workflow.md`；2026-11-14 首次 03:17 窗口
  轮询至 05:10 CST 前未出现，08:19 CST 出现延迟 schedule run 43533439066，下一窗口为 2026-11-15 03:17。
  （FR-008、FR-009；AC-011）

## Dependencies & Execution Order

```text
T001, T002 ── T003, T004, T005 ── T006 ── T007 ── T008
                                                     │
                    ┌────────────────────────────────┤
                    ├─ US1: T009 ── T010 ── T011
                    ├─ US2: T012 ── T013 ── T014（依赖 T008）
                    ├─ US3: T015 ── T016 ── T017（依赖 T010/T013）
                    ├─ US4: T018 ── T019 ── T020（依赖 T007）
                    └─ US5: T021 ── T022 ── T024（依赖 T019/T020）
                                  T023 可与 T021/T022 并行
                                                     │
                                  T025, T026 ────────┴─ T027 ── T028
```

- T001/T002 为不同文件，可并行；T003/T004/T005 为不同文件，可并行。
- T006 依赖 T003；T007 依赖 T004；T008 依赖 T003/T005；T006 与 T007/T008 可部分并行但不改同一文件。
- US1 是 MVP；US2/US3 依赖 T008；US3 依赖 US1/US2 的状态与候选行为。
- US4 依赖 T007 的报告骨架；US5 依赖 T019/T020 的状态字段。
- `README.md` 只由 T023 修改；`scripts/lib/source-sync.js` 由 T008/T010/T013/T016 串行修改；
  `.github/workflows/maintain.yml` 只由 T022 修改。
- POC-003（T026）在实现与默认测试通过后执行；生产调度启用不在此任务内。

### Within Each User Story

- 先写测试并确认真实失败，再实现；已由 US-003/US-005 覆盖的行为直接复用，不伪造失败。
- 同一文件只能串行修改；不同文件可并行。
- 真实远端写入只在 T020/T024/T026 的受控仓库执行；默认测试使用注入来源与临时裸远端。

## Parallel Examples

### Foundational

T003（来源读取测试）、T004（状态/报告测试）、T005（夹具）为不同文件，可并行；T006 在 T003 后，
T007 在 T004 后，T008 在 T003/T005 后。

### User Stories

US1 完成后，US2 与 US4 的不同文件测试可并行；US3 依赖 US2 的 apply 链路；US5 的 T021 与 T023
为不同文件，可并行，T022 在 T021 后。

## Implementation Strategy

### MVP First

先完成 T001～T011：共享读取、check 链路、无变化/候选与失败隔离。此时可演示“检查但不写入”，
不声称自动替换、调度或生产启用完成。

### Incremental Delivery

Setup → Foundational → US1 检查 → US2 完整替换 → US3 许可/冲突 → US4 状态/重跑 → US5 调度/文档
→ 全量检查 → POC-003 → 最终复核/quickstart。每步在隔离环境验证并独立提交；真实远端和调度启用
分别授权、分别报告。

## Notes

- 不执行 `skills/` 中任何脚本或测试，不安装其依赖；来源内容只作为数据处理。
- 不新增 npm 依赖；Git/`gh` 为文档化前置命令；不改公开搜索/详情/schema。
- 生产 `main` 的每日调度已启用；实际定时触发仍需观察，POC-003 不替代生产调度或发布验收。
- 凭证只在 `sync` job 的受限步骤使用；报告、摘要、日志和 README 不出现 token、响应正文或原始异常。
