---
description: "US-007 整体验收与交接任务"
---

# Tasks: US-007 整体验收与交接

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、US-001～US-006 的 spec/plan/tasks/validation、
宪章 1.0.0 与四份 0.2 文档。

**Prerequisites**: US-001～US-006 已完成的本地/受控证据；生产 Pages 与 US-006 调度已启用；
用户已确认 Demo-002 可接受 POC-003 受控证据，且 US-007 可带未运行项进入验收但不判定整包通过。

**Status**: 任务于 2026-11-14 生成；当前 22 项。T001–T022 已执行；2026-11-14 补验生产
environment/部署失败、MIME/缓存基础头、真实 403 和 macOS runner；结论仍为有条件验收/交接，
剩余子项见 `validation/residual-gaps.md`，不判定整包通过。

**Tests**: 验收以只读检查和受控复验为主；不执行 `skills/` 内脚本，不写生产内容，不把未运行项
计为通过。

**Organization**: 五个用户故事对应 spec.md 的五条验收切片；同文件任务串行，`[P]` 不授权多 Agent。

## Format: `[ID] [P?] [Story] Description`

- 每项使用 `- [ ] Txxx [P?] [USx?] 描述 + 文件路径`。
- Setup/Foundational/Polish 不加故事标签；User Story 阶段必须带 `[US1]`～`[US5]`。
- 证据文件写入 `specs/007-overall-acceptance/validation/`。

## Phase 1: Setup — 基线与矩阵骨架

- [X] T001 [P] 记录验收前置状态：分支/HEAD、Node/npm、生产 Pages revision、最新部署 run、
  US-006 调度状态、POC-002/003 可用性；写入 `specs/007-overall-acceptance/validation/preflight.md`。
- [X] T002 [P] 在 `specs/007-overall-acceptance/validation/acceptance-matrix.md` 建立
  AC-001～AC-015、Demo-001～003、US-001～006 矩阵骨架；状态只允许“通过/受控通过/未运行/失败”。

## Phase 2: Foundational — 证据索引

- [X] T003 汇总现有 validation、POC 运行 ID、生产页面和测试入口，形成可追溯索引并补入
  `acceptance-matrix.md` 的证据列；不改变既有验收结论。

## Phase 3: User Story 1 — 维护到公开取用（Priority: P1）

**Goal**: 手动/命令维护、检索、详情、复制、原件和 ZIP 下载完整可用。

**Independent Test**: 在隔离副本完成一次手动新增/替换和一次 CLI preview/add，再从公开站点或
本地 dist 走完整取用链路。

- [X] T004 [US1] 在隔离副本执行手动单文件/目录新增、替换、下架，核对 slug、旧附件清理、
  站内字段保留和失败批次旧站保留；记录到 `validation/demo-001.md`。（AC-001/AC-005/AC-006）
- [X] T005 [US1] 按 README 执行 `skill-cli` preview/add/import/replace/status，核对零写入、
  目标路径提交、JSON/退出码和冲突；记录命令与结果到 `validation/demo-001.md`。
  （AC-007/AC-011）
- [X] T006 [US1] 从生产站点或本地 dist 检查检索、详情、复制和下载；下载原件/ZIP 后逐路径、
  逐字节核对，记录到 `validation/demo-001.md` 与 `validation/fidelity.md`。
  （AC-002/AC-004/AC-005）
- [X] T007 [US1] 更新 `acceptance-matrix.md` 的 Demo-001 和对应 AC 状态；失败/未运行项必须
  保留原因，不得计为通过。 （AC-001～AC-008）

## Phase 4: User Story 2 — 上游升级到单一新版（Priority: P1）

**Goal**: 用 POC-003 受控证据验证来源更新、单版本、许可基线和无变化；记录生产调度现实。

**Independent Test**: 复核 branch/release/pinned、v1→v2、许可变化阻断、无变化和同次发布运行。

- [X] T008 [US2] 复核 `specs/006-source-auto-update/validation/` 的 POC-003、许可基线、T020 和
  `us6-workflow` 证据；在 `validation/demo-002.md` 标注“受控通过”，不写成生产自动更新。
  （AC-009/AC-010/AC-011）
- [X] T009 [US2] 读取生产 catalog 和 `Maintain site` 运行：确认 `source_tracking` 当前为
  `null`、2026-11-14 延迟 schedule run `43533439066` 为 sync success/build-deploy skipped；
  记录“配置已启用、实际来源未配置、准点未承诺”。（AC-011/AC-014）
- [X] T010 [US2] 更新 `acceptance-matrix.md` 的 Demo-002 和 AC-009/AC-010 状态；明确受控证据与
  生产自动更新的区别。 （AC-009/AC-011）

## Phase 5: User Story 3 — 失败、冲突到恢复（Priority: P1）

**Goal**: 404/限流/非法候选/许可/冲突/构建/部署失败失败关闭，状态可查、可重跑、可恢复。

**Independent Test**: 复核 POC-002/003 的失败矩阵、部署失败、同提交重跑和受控 revert。

- [X] T011 [US3] 复核来源 404、非法候选、许可变化、本地冲突和并发过期的测试/POC 证据；
  记录逐项状态与当前版本保留，写入 `validation/demo-003.md`。（AC-010/AC-012）
- [X] T012 [US3] 复核部署失败/旧站保留、同提交重跑、受控 revert 的 run ID 和内容 revision；
  明确真实 403/限流未运行，不伪造远程结果。 （AC-011）
- [X] T013 [US3] 更新 `acceptance-matrix.md` 的 Demo-003 和 AC-010/AC-011/AC-012 状态。
  （AC-010～AC-012）

## Phase 6: User Story 4 — 固定地址、旧链接与浏览器可达（Priority: P2）

**Goal**: 固定站点、子路径资源、旧 hash 链接和核心可访问性保持。

**Independent Test**: 读取生产首页/索引/详情/原件/ZIP、旧 `#/skill/<slug>` 和 `/skill-gallery/`
资源；复核既有浏览器证据并标注未运行设备。

- [X] T014 [US4] 检查生产首页、索引、详情、原件和 ZIP 的 200/内容/路径；检查旧详情和列表链接；
  记录到 `validation/fixed-address.md`。（AC-005/AC-014）
- [X] T015 [US4] 复核 US-002 的 360/768/1440、明暗主题、键盘和减少动效证据；Safari/移动实机
  未运行单独列出。 （AC-013/AC-015）
- [X] T016 [US4] 复核原件/附件/二进制/许可/相对路径和 ZIP 清单，记录到 `validation/fidelity.md`。
  （AC-001/AC-002/AC-004）

## Phase 7: User Story 5 — 交接与未运行项（Priority: P2）

**Goal**: 交接材料可执行、状态真实、未运行项可追溯、恢复路径明确。

**Independent Test**: 从干净 checkout 按 README 执行可行命令；核对矩阵、未运行项和恢复说明。

- [X] T017 [US5] 在 `validation/security.md` 复核凭证、路径/URL、上游脚本执行和公开产物白名单；
  重新运行 `npm run security`，记录结果。 （AC-008/AC-012）
- [X] T018 [US5] 在 `validation/residual-gaps.md` 逐项列出 T041 macOS、US-005 真实 `gh api`/`--wait`、
  生产 environment 审批、生产部署失败注入、MIME/缓存、真实 403/限流；每项写影响和补验方式。
  （AC-001～AC-015）
- [X] T019 [US5] 按 README 在干净副本复核 preview/发布/状态/恢复命令与退出码；记录偏差到
  `validation/handoff.md`。 （AC-007/AC-011）
- [X] T020 [US5] 更新 README/AGENTS 的 US-007 状态、已验收/未运行项和恢复入口；不宣称整包完成。
  （AC-011/AC-014）

## Phase 8: Polish & Final Review

- [X] T021 [P] 运行 `npm run check`、`npm run security` 和必要的工作流静态检查；记录实际命令、
  数量、退出码和未运行项。 （NFR-003/NFR-006）
- [X] T022 对照 `spec.md`、`plan.md`、`acceptance-matrix.md` 和全部 validation 做最终复核；
  更新 tasks/plan 状态，写 `validation/final-review.md`；未运行项不得计入通过。
  （AC-001～AC-015）

## Dependencies & Execution Order

```text
T001/T002 → T003
   ├─ US1: T004 → T005 → T006 → T007
   ├─ US2: T008 → T009 → T010（依赖 T003）
   ├─ US3: T011 → T012 → T013（依赖 T003）
   ├─ US4: T014/T015/T016（可并行）
   └─ US5: T017/T018/T019 → T020
T021/T022 最后执行；T022 依赖全部 US 证据。
```

- T001/T002 不同文件，可并行；T003 依赖两者。
- US1 是 Demo-001 主链路；US2/US3 复用既有 POC 证据；US4 可并行读取生产页面证据。
- `README.md`、`AGENTS.md` 只由 T020 修改；矩阵只由 T003/T007/T010/T013 串行修改。
- 生产只读；受控写入只在 T004/T005/T008 的隔离/POC 环境执行。

## Parallel Examples

- US4 的 T014（固定地址）、T015（浏览器证据）、T016（保真）为不同文件，可并行。
- US5 的 T017（安全）与 T018（残留缺口）为不同文件，可并行；T019/T020 串行。

## Notes

- Demo-002 使用 POC-003 受控证据是用户明确确认的口径；报告必须写“受控通过”，不能写成生产
  自动更新已发生。
- US-007 可以有意保留未运行项并完成交接；若未运行项影响关键 AC，最终结论必须是“有条件/未完成”，
  不能写成整包通过。
- 不执行收录 Skill 的脚本、测试或依赖；不打印凭证；不修改生产内容。
