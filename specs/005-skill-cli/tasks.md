---
description: "US-005 Agent 命令维护的实施任务"
---

# Tasks: US-005 Agent 命令维护

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[research.md](research.md)、[data-model.md](data-model.md)、
[skill-cli 契约](contracts/skill-cli.md)、[quickstart.md](quickstart.md)。日期：2026-11-08。

**Prerequisites**: [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0，
US-003 发布链与 US-004 手动维护规则。

**Status**: 任务于 2026-11-08 生成；当前 23 项。T001–T014 已完成（T001 见
[validation/preflight.md](validation/preflight.md)，T002–T010 见
`tests/unit/skill-cli-args.test.js`、`tests/integration/skill-cli-{add,replace}.test.js`、
`tests/support/skill-cli-fixture.js`、`scripts/lib/skill-cli/` 与
[validation/us5-add.md](validation/us5-add.md)、[validation/us5-replace.md](validation/us5-replace.md)，
T011–T013 见 `tests/integration/skill-cli-import.test.js`、
`scripts/lib/skill-cli/source-github.js` 与 [validation/us5-import.md](validation/us5-import.md)，
T014 见 `tests/unit/skill-cli-status.test.js`）；T015–T023 未开始。分支
`codex/us-005-skill-cli`（从 US-004 分支堆叠，未合并 main）。生产 Pages 未启用；真实远端写入与
POC-002 操作需单独授权。

**Tests**: 宪章 IX 要求先建立能识别错误行为的验证。新增参数/退出码/JSON 单元测试与临时裸仓库
集成测试；来源与状态查询可注入，默认测试不访问网络、不推真实远端。

**Organization**: 五个用户故事对应 [spec.md](spec.md) 的内部切片。同文件任务必须串行；`[P]` 不授权多 Agent。

## Format: [ID] [P?] [Story] Description

- 每项严格使用 `- [ ] Txxx [P?] [USx?] 描述 + 文件路径`。
- `[P]` 只表示不同文件、无未完成依赖时可并行；同一文件任务不得并行。
- Setup/Foundational/Polish 不加故事标签；User Story 阶段必须加 `[US1]`～`[US5]`。
- 路径相对项目根；`dist/` 是生成目录，不手改、不提交。

## Phase 1: Setup — 基线与前置

- [X] T001 [P] 在 `specs/005-skill-cli/validation/preflight.md` 记录：分支与 HEAD、Node/npm 实际与
  锁定版本、Git/gh 可用性与登录状态（不读取 token）、现有测试数量、生产 Pages 状态、POC-002
  可用性与授权边界。（NFR-006；AC-007）

## Phase 2: Foundational — 命令骨架与测试夹具

**⚠️ CRITICAL**: 本阶段完成前，各用户故事无法独立验证。

- [X] T002 [P] 在 `tests/unit/skill-cli-args.test.js` 建立参数/退出码契约：命令互斥、必填、非法
  slug/SHA、`--wait` 仅用于 publish、JSON 单行与脱敏、退出码 `0/2/3/4/5/6/7/8` 映射。
  （FR-006、FR-007；AC-007、AC-008）
- [X] T003 [P] 在 `tests/support/skill-cli-fixture.js` 建立测试夹具：临时项目、临时裸远端、基线
  提交、候选 Skill/元数据、来源读取与运行查询注入；只写系统临时目录，测试结束清理。
  （FR-006；AC-007）
- [X] T004 实现 `scripts/skill-cli.js` 与 `scripts/lib/skill-cli/args.js`、`output.js`：命令分发、
  参数校验、单行 JSON、脱敏与退出码；复验 T002。（FR-006、FR-007；AC-007）

**Checkpoint**: 命令骨架与夹具可测试；尚未执行发布。

## Phase 3: User Story 1 — 校验预览与新增（Priority: P1）MVP

- [X] T005 [US1] 在 `tests/integration/skill-cli-add.test.js` 建立预览/新增契约：预览零写入；
  合法单文件/目录发布只暂存目标文件；相同内容 noop；JSON 字段与状态正确。
  （FR-006、FR-009；AC-007、AC-011）
- [X] T006 [US1] 实现 `scripts/lib/skill-cli/candidate.js`、`workspace.js`、`publish.js`：候选校验、
  隔离工作副本、基于远端基线暂存、提交与状态输出；复验 T005。
  （FR-006、FR-009；AC-007、AC-011）
- [X] T007 [US1] 在隔离项目与临时裸远端执行预览/新增，记录命令、退出码、JSON、提交与未运行项到
  `specs/005-skill-cli/validation/us5-add.md`。（FR-006；AC-007）

## Phase 4: User Story 2 — 显式替换与冲突（Priority: P1）

- [X] T008 [US2] 在 `tests/integration/skill-cli-replace.test.js` 建立替换/冲突契约：正确基线成功且
  单版本、旧附件清理、元数据默认保留；过期/缺失基线返回 `4` 且当前内容不变。
  （FR-006、FR-009；AC-007、AC-011）
- [X] T009 [US2] 实现 replace 流程（保留/替换元数据、expected revision、fast-forward 检查）；
  复验 T008。（FR-006、FR-009；AC-011）
- [X] T010 [US2] 在隔离临时仓库执行替换成功/冲突，记录提交、产物差异、退出码与未运行项到
  `specs/005-skill-cli/validation/us5-replace.md`。（FR-006；AC-011）

## Phase 5: User Story 3 — GitHub 来源导入（Priority: P2）

- [X] T011 [US3] 在 `tests/integration/skill-cli-import.test.js` 建立来源导入契约：固定来源树、
  截断/404/403/限流/越界/符号链接失败、普通网页 URL 拒绝；使用注入来源，不访问网络。
  （FR-006、FR-007；AC-007、AC-008）
- [X] T012 [US3] 实现 `scripts/lib/skill-cli/source-github.js`：结构化定位、不可变提交、完整文件树、
  错误映射；与本地输入共用校验；复验 T011。（FR-006、FR-007；AC-007）
- [X] T013 [US3] 在隔离环境用夹具/受控来源执行导入，记录命令、退出码、来源失败与未运行项到
  `specs/005-skill-cli/validation/us5-import.md`。（FR-006；AC-007）

## Phase 6: User Story 4 — 状态查询与等待（Priority: P2）

- [X] T014 [P] [US4] 在 `tests/unit/skill-cli-status.test.js` 建立状态派生契约：build/deploy
  job 组合、superseded、pending、失败与 `--wait` 超时 `8`；不得误报 published。
  （FR-009；AC-011）
- [ ] T015 [US4] 实现 `scripts/lib/skill-cli/status.js` 与 `--wait` 轮询；复验 T014。
  （FR-009；AC-011）
- [ ] T016 [US4] 用受控 POC-002 运行或固定运行状态执行 status/wait，记录 JSON、退出码、超时与
  未运行项到 `specs/005-skill-cli/validation/us5-status.md`。（FR-009；AC-011）

## Phase 7: User Story 5 — README 命令契约（Priority: P3）

- [ ] T017 [US5] 在 `README.md` 增加 Agent 命令章节：前提/认证、preview/add/import/replace/status、
  `--publish/--wait`、退出码、替换/冲突、来源导入、排错；示例使用占位凭证，未实现能力标规划。
  （FR-006、FR-010；AC-007、AC-008）
- [ ] T018 [US5] 按 README 在隔离临时仓库走完预览/发布/冲突/状态，记录命令、结果与偏差到
  `specs/005-skill-cli/validation/us5-readme.md`。（FR-006；NFR-006）

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T019 [P] 运行 `npm test`、`npm run lint`、`npm run format:check`、`npm run security`；
  记录退出码、测试数量、扫描结果与未运行项到 `specs/005-skill-cli/validation/us5-quality.md`。
  （NFR-003、NFR-006；AC-008）
- [ ] T020 [P] 定向更新 `README.md`、`AGENTS.md` 的 US-005 状态、可执行命令、受控结果和未完成项；
  不写未验证命令或线上成功。（NFR-006；AC-007）
- [ ] T021 在受控 POC-002 执行一次真实发布/替换/状态查询（需授权），记录运行 URL、提交 SHA、
  JSON 状态与未运行项到 `specs/005-skill-cli/validation/us5-poc.md`；生产 Pages 未切换。
  （FR-006、FR-009；AC-007、AC-011）
- [ ] T022 复核 `spec.md`、`contracts/` 与 `validation/`：未改内容 schema、搜索/详情前端、发布权限
  或生产 Pages；失败项与未运行项单独列出；更新 tasks/plan 状态，记录到
  `specs/005-skill-cli/validation/us5-final-review.md`。
  （FR-006、FR-007、FR-009；AC-007、AC-008、AC-011）
- [ ] T023 对照 quickstart 在干净副本复核命令与退出码，确认 README/契约/实现一致；记录结果到
  `specs/005-skill-cli/validation/us5-quickstart.md`。（NFR-006；AC-007）

## Dependencies & Execution Order

```text
T001 ──┬─ T002, T003 ── T004
       │                    │
       ├─ US1: T005 → T006 → T007
       ├─ US2: T008 → T009 → T010（依赖 T006 的发布流程）
       ├─ US3: T011 → T012 → T013（依赖 T006 的候选/校验）
       ├─ US4: T014 → T015 → T016（T014 可与 US2/US3 并行）
       └─ US5: T017 → T018（依赖实现稳定）
                      │
        T019, T020 ───┴→ T021 → T022 → T023
```

- T001 无依赖；T002/T003 不同文件可并行；T004 依赖两者。
- US1 是 MVP；US2/US3 依赖 US1 的候选与发布模块；US4 可与 US2/US3 并行。
- `README.md` 由 T017/T020 串行修改；`scripts/skill-cli.js` 与共享库由 T004/T006/T009/T012/T015 串行。
- T019/T020 可并行（不同文件）；T021 依赖实现与文档；T022 最后执行，T023 在 T022 后复核。

### Within Each User Story

- 先写测试并确认真实失败，再实现；已由 US-003/US-004 覆盖的行为直接复用，不伪造失败。
- 同一文件只能串行修改；不同文件可并行。
- 真实远端写入只在 T021 受控仓库执行；默认测试使用临时裸远端与注入边界。

## Parallel Examples

### Foundational

T002（unit 参数/退出码）与 T003（fixture）为不同文件，可并行；T004 在两者之后。

### User Stories

US1 完成后，US2 与 US4 可并行；US3 依赖 US1 的候选模块。测试文件彼此独立，可并行编写，
但共享实现文件必须串行。

### Polish

T019（检查）与 T020（文档）为不同文件，可并行；T023 在 T022 后复核 quickstart。

## Implementation Strategy

### MVP First

先完成 T001～T007：参数/输出骨架、预览零写入、合法本地新增与 noop；不声称替换、来源导入、
状态等待或真实远端发布已完成。

### Incremental Delivery

Setup → 骨架 → US1 预览/新增 → US2 替换/冲突 → US3 来源导入 → US4 状态/等待 → US5 README →
全量检查/受控发布/最终复核。每步在隔离环境验证；受控仓库操作单独授权、单独报告。

## Notes

- 不执行 `skills/` 中任何脚本/测试，不安装其依赖；来源读取与候选处理只作数据。
- 不新增 npm 依赖；Git/`gh` 为文档化前置命令；不改内容 schema、前端或 US-003 发布权限。
- 生产 Pages 源、environment、分支保护和线上切换不在任务默认授权内；T021 使用 POC-002，
  未获授权时必须记录未运行。
- 提交按逻辑组拆分，仅暂存本故事文件；推送、合并 main 和生产发布需单独明确授权。
