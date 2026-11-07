---
description: "US-003 校验、构建与原地址发布流水线的实施任务"
---

# Tasks: US-003 校验、构建与原地址发布流水线

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[research.md](research.md)、[data-model.md](data-model.md)、
[publish 契约](contracts/publish.md)、[workflow 契约](contracts/workflow.md)、[quickstart.md](quickstart.md)。日期：2026-11-07。

**Prerequisites**: [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0，
以及四份 0.2 文档：[调研](../../docs/IndustryResearch.md)、[需求](../../docs/DemandAnalysis.md)、
[技术方案](../../docs/TechnicalSolution.md)、[编程规范](../../docs/AiProgrammingGuide.md)。

**Status**: 任务于 2026-11-07 生成；当前 33 项，T031/T032 为 2026-11-07 分析修订追加，
T033 为同日 Step Summary 补齐追加，不重排既有 T001～T030。T001–T021 与 T033 已完成
（T018 在受控临时公开仓库执行；Foundational 见 [validation/foundational.md](validation/foundational.md)；US1 见
[validation/us3-snapshot.md](validation/us3-snapshot.md) 与
[validation/us3-links.md](validation/us3-links.md)；US2 测试契约见
`tests/unit/publish-status.test.js`、`tests/integration/publish/publish-superseded.test.js` 与
`tests/integration/publish/publish-deploy-workflow.test.js`，恢复演练见
[validation/us3-recovery.md](validation/us3-recovery.md)，Step Summary 见
[validation/us3-summary.md](validation/us3-summary.md)；US3 安全契约见
`tests/integration/publish/publish-security.test.js`、
`tests/integration/publish/publish-security-workflow.test.js` 与
[validation/us3-security.md](validation/us3-security.md)）；T022–T032 未开始。
2026-11-07 已将 publish 集成测试重组到 `tests/integration/publish/`，`npm test` 同步覆盖该目录；
历史 validation 记录保留执行时路径。
T018 的受控 POC-002 结果见 [validation/us3-recovery.md](validation/us3-recovery.md) 第 6 节。
分支 `codex/us-003-validate-build-publish`（从 US-002 分支堆叠，当前未推送、未合并 main）。
生产 Pages 源、environment、分支保护和线上切换未修改、未发布；受控仓库不可用时按未运行记录。

**Tests**: spec 的 Independent Test、Acceptance Scenarios 与 US003-SC-01～06 要求验证；宪章 IX 要求
先建立能识别错误行为的验证。因此包含发布前产物、状态/过期、凭证边界和工作流静态契约测试。
测试夹具只作数据，不执行收录 Skill 的脚本或测试，不安装其依赖。

**Organization**: 四个用户故事对应 [spec.md](spec.md) 的内部切片，不占用上游其他 US 编号。
共享发布校验与工作流放在 Foundational；各故事在其上独立验证。同文件任务必须串行，`[P]` 不授权多 Agent。

## Format: [ID] [P?] [Story] Description

- 每项严格使用 `- [ ] Txxx [P?] [USx?] 描述 + 文件路径`。
- `[P]` 只表示不同文件、无未完成依赖时可并行；同一文件任务不得并行。
- Setup/Foundational/Polish 不加故事标签；User Story 阶段必须加 `[US1]`/`[US2]`/`[US3]`/`[US4]`。
- 路径相对项目根；`dist/` 是生成目录，不手改、不提交。

## Phase 1: Setup — 基线与隔离输入

**Purpose**: 在实现前固定当前分支、构建和外部配置状态，并提供可重复的最小发布夹具。

- [X] T001 [P] 在 `specs/003-validate-build-publish/validation/preflight.md` 记录：分支与 HEAD、
  Node/npm 实际版本与锁定版本、现有 `dist/` 状态、五个 action 版本/完整 SHA、Pages 源与
  environment 未修改、T041 macOS 与 US-002 合并状态；不读取或打印凭证。
  （FR-011、NFR-006；AC-014）
- [X] T002 [P] 在 `tests/support/publish-fixture.js` 创建最小发布夹具：生成含 `index.html`、
  `assets/` 前端模块、`catalog/` 与合法单文件/目录 Skill 的临时项目；调用
  `scripts/lib/build-site.js` 生成隔离 `dist/` 并返回路径；提供 40 位 SHA、额外文件、篡改字节和
  伪造凭证文件的注入辅助。凭证文件内容必须用占位符或运行时拼接生成，不写完整 token/私钥字面量；
  只写系统临时目录，不写工作区 `dist/`，不执行 Skill 脚本，测试结束清理临时目录。
  （FR-011、NFR-006；AC-014）

**Checkpoint**: 基线与隔离夹具可复现；尚未修改发布行为。

## Phase 2: Foundational — 共享发布校验与工作流

**Purpose**: 让所有故事共享同一套产物校验、目标判定、状态和发布工作流。

**⚠️ CRITICAL**: 本阶段未完成前，各用户故事无法独立验证发布。

### Tests for Foundational

- [X] T003 [P] 在 `tests/unit/publish.test.js` 先写失败契约：`verifyArtifact` 的 manifest 双向一致、
  路径白名单、`..`/绝对路径/反斜杠/控制字符/重复路径、符号链接/非普通文件、隐藏文件
  （`.nojekyll` 除外）、大小/SHA-256、`contentRevision` 同源、文本文件 `scanSecrets`；
  `evaluateDeployTarget` 的 40 位十六进制校验与 `current`/`superseded`；`createRunStatus` 的封闭
  字段/枚举（含 `commit_status`、可选 `started_at`/`finished_at`）；
  `renderSummary` 不包含凭证、响应正文或原始异常，并显示提交/构建/部署状态与运行时间或 `run_url`。
  （FR-007、FR-009、FR-011；AC-008、AC-011、AC-014）
- [X] T004 [P] 在 `tests/integration/publish-artifact.test.js` 先写失败契约：使用 T002 夹具构建
  `dist/` 后验证合法产物通过；额外文件、篡改字节、`.env`/`*.pem`/`id_rsa`、非同一
  `contentRevision` 全部失败关闭；失败不修改、不删除原 `dist/`。
  （FR-007、FR-011、NFR-003；AC-008、AC-014）
- [X] T005 [P] 在 `tests/integration/publish-workflow.test.js` 先写失败契约：解析
  `.github/workflows/maintain.yml`，断言只监听 `push: main` 与 `workflow_dispatch`、无
  `pull_request_target`/`workflow_run`、工作流级 `concurrency` 为 `maintain-${{ github.ref }}` 且
  `cancel-in-progress: false`、build job `timeout-minutes: 30`、deploy job `timeout-minutes: 10`、
  默认 `permissions.contents: read`；
  artifact 路径为 `dist`、部署 job 使用 `github-pages` environment 与 `pages` 并发组、
  所有 action 使用完整 40 位 SHA、无 `@vN` 浮动引用、无凭证或 PAT。T005 只覆盖基础结构；
  部署细节、权限细节和同次运行分别由 T016/T020/T023 补充，避免重复断言。
  （FR-007、FR-011；AC-008、AC-014）

### Implementation for Foundational

- [X] T006 实现 `scripts/lib/publish.js`：`verifyArtifact(distDir)`、`evaluateDeployTarget({targetSha,
  remoteHead})`、`createRunStatus(input)`、`renderSummary(status, context)`；复用
  `scripts/lib/secrets.js`，诊断只含 `code`/`path`/脱敏 `message`；不新增 npm 依赖、不修改内容
  schema、不写工作区 `dist/`。完成后复验 T003/T004。
  （FR-007、FR-009、FR-011；NFR-003；AC-008、AC-011、AC-014）
- [X] T007 实现 `scripts/publish-check.js`：支持
  `artifact --dist <dir>` 与 `target --target <sha> --remote <sha>`；stdout 单行机器 JSON，
  诊断到 stderr 且脱敏；退出码 `0` 通过/current、`2` 参数或读取错误、`4` superseded、
  `6` 产物无效；不写入、不执行 `dist/` 脚本、不发起网络请求。
  （FR-009、FR-011；AC-011、AC-014）
- [X] T008 新增 `.github/workflows/maintain.yml`：仅监听 `push: main` 与 `workflow_dispatch`；
  默认 `permissions: contents: read`，工作流级 `concurrency` 的 `group` 为
  `maintain-${{ github.ref }}`、`cancel-in-progress: false`；build job `timeout-minutes: 30`、
  deploy job `timeout-minutes: 10`；checkout 使用
  `persist-credentials: false`。`build` job 使用固定 checkout/setup-node/setup-uv，安装锁定依赖与
  扫描器，运行 `npm run check`、`npm run security`、`npm run build`、
  `node scripts/publish-check.js artifact --dist dist`，再用固定
  `upload-pages-artifact` 上传 `dist/`；`deploy` job `needs: build`，使用
  `github-pages` environment、`contents: read`、`pages: write` 和 `id-token: write`、`pages` 并发组，
  部署前比较远端 HEAD 并调用 `publish-check.js target`，`superseded` 时跳过部署；
  Step Summary 只写脱敏状态。不修改 Pages 设置或分支保护。
  （FR-007、FR-009、FR-011；NFR-003、NFR-004；AC-008、AC-011、AC-014）
- [X] T009 运行 `node --test tests/unit/publish.test.js tests/integration/publish-artifact.test.js
  tests/integration/publish-workflow.test.js`、`npm run lint`、`npm run format:check`；
  在 `specs/003-validate-build-publish/validation/foundational.md` 记录命令、退出码、测试数量和
  未运行项；只修复本故事引入的问题。
  （NFR-006；AC-014 工程支撑）

**Checkpoint**: 共享校验、CLI 和工作流骨架可测试；尚未进行真实 Pages 部署。

## Phase 3: User Story 1 — 只发布同一内容快照的合法静态产物（Priority: P1）MVP

**Goal**: 合法内容经全量校验、构建和白名单检查后，只部署来自同一快照的静态产物；
非法输入整批失败且不部署。

**Independent Test**: 使用 T002 的隔离项目构建 `dist/`，运行产物校验并注入额外文件、篡改字节和
非法元数据；确认合法产物通过、非法产物失败、旧产物不变；不依赖生产 Pages。

### Tests for User Story 1

- [X] T010 [US1] 在 `tests/integration/publish-artifact.test.js` 增加合法快照场景：索引、每个详情和
  manifest 的 `contentRevision` 一致，detail 的 `slug`/`digest` 与索引一致；第二次构建无变化时
  产物集合稳定；注入非法条目、缺失附件和额外文件时整批失败。
  （FR-009、FR-011；AC-011、AC-014）

### Implementation / Validation for User Story 1

- [X] T011 [US1] 在隔离副本执行 `npm run build` 和
  `node scripts/publish-check.js artifact --dist <隔离 dist>`；检查白名单、manifest 双向一致、
  同 `contentRevision`、无额外文件和凭证；记录到
  `specs/003-validate-build-publish/validation/us3-snapshot.md`，不写工作区 `dist/`。
  （FR-011、NFR-003；AC-008、AC-014）
- [X] T012 [US1] 在 T011 的隔离 dist 上运行 `node --test tests/integration/preview.test.js` 或
  `npm run preview`，核对 `/skill-gallery/` 子路径；Hash 路由的四个旧 `#/skill/<slug>` 链接和刷新
  使用 US-002 已记录的浏览器证据或人工在明确浏览器/版本中复验；记录命令、浏览器/版本、结果和
  未运行项，不能只用普通 HTTP 200 断言 Hash 路由通过。
  （FR-011；AC-014）
- [X] T013 [US1] 对同一隔离项目连续构建两次，确认无变化时 `contentRevision` 与产物集合稳定、
  `publish-check.js artifact` 仍通过、没有新增内容提交；允许重复部署同一快照，但不得伪装成
  内容更新；把结果补充到 `specs/003-validate-build-publish/validation/us3-snapshot.md`。
  （FR-009、FR-011；AC-011、AC-014）

**Checkpoint**: US1 的合法/非法产物与固定路径行为可独立验证。

## Phase 4: User Story 2 — 发布失败保留上次可用站点并可恢复（Priority: P1）

**Goal**: 提交、构建和部署状态分开显示；部署失败保留上次正常站点；同一提交重跑幂等；
旧快照不覆盖新快照；恢复走受控历史。

**Independent Test**: 用状态/目标单测和 CLI superseded 场景验证失败与重跑语义；
在受控仓库（如获授权）注入部署失败并检查旧站；不修改生产配置。

### Tests for User Story 2

- [X] T014 [P] [US2] 在 `tests/unit/publish-status.test.js` 写状态契约：`built`+`deploy_failed` 可
  同时表达；`superseded` 不表示成功；`commit_status` 只接受 `not_applicable/committed/failed`，
  `started_at`/`finished_at` 可空但只接受 ISO 8601；封闭字段拒绝未知键/枚举；`renderSummary`
  区分内容与部署状态且不泄露凭证/响应正文。
  （FR-009、NFR-004；AC-011）
- [X] T015 [P] [US2] 在 `tests/integration/publish-superseded.test.js` 写 CLI 契约：
  目标 SHA 与远端 HEAD 相同返回 `0/current`；不同返回 `4/superseded`；非法 SHA 返回 `2`；
  命令不写入仓库、不发起部署。
  （FR-009、NFR-004；AC-011）
- [X] T016 [US2] 在 `tests/integration/publish-deploy-workflow.test.js` 写部署 job 静态断言：
  `needs` 包含 `build`、`environment: github-pages`、`pages` 并发组、无 `continue-on-error`
  掩盖失败、部署前有目标判定步骤、失败时保留旧站点（不执行删除/回滚写操作）。只补部署 job
  断言，不重复 T005 的基础触发/权限项。
  （FR-009；AC-011、AC-014）

### Validation for User Story 2

- [X] T017 [US2] 运行 T014/T015/T016；在隔离副本模拟部署失败和 superseded（通过伪造远端 SHA
  或让部署步骤前置检查失败），确认旧 `dist/` 不变、状态可区分、同一提交重跑不新增内容提交；
  记录到 `specs/003-validate-build-publish/validation/us3-recovery.md`。
  （FR-009、NFR-004；AC-011）
- [X] T018 [US2] 如获授权，在受控测试仓库执行 POC-002：切换 Pages 源为 GitHub Actions，触发
  部署失败（权限/环境/步骤失败），确认旧站可用，按同一 commit 重跑成功；记录运行 URL、
  目标 SHA、状态和未运行项到
  `specs/003-validate-build-publish/validation/us3-recovery.md`；未获授权或环境不可用时只记录未运行。
  （FR-009、FR-011；AC-011、AC-014）
  **2026-11-07 状态**: 已完成受控 POC-002（临时公开仓库）；运行 URL、目标 SHA、部署失败、
  旧站保留和同一提交重跑结果见 [validation/us3-recovery.md](validation/us3-recovery.md) 第 6 节。

**Checkpoint**: 失败保留、重跑、过期和恢复语义可独立验证；生产未启用。

## Phase 5: User Story 3 — 写入与部署仅限受信环境（Priority: P1）

**Goal**: 访客只读；写入/部署仅授权环境；产物、日志和摘要无凭证；第三方内容只作数据处理。

**Independent Test**: 产物凭证/危险文件名测试、工作流权限静态断言和未授权受控尝试；
不执行 Skill 脚本，不使用真实凭证。

### Tests for User Story 3

- [X] T019 [P] [US3] 在 `tests/integration/publish-security.test.js` 写安全契约：`.env`、
  `*.pem`、`*.key`、`id_rsa`、token 前缀、私钥块和越界路径全部被拒绝；诊断只含位置/规则，
  不回显值；`dist/` 中的脚本不被执行（执行哨兵保持未触发）。token 前缀/私钥块测试值必须运行时
  构造或使用 `YOUR_*_HERE` 占位符，不得在源码中出现完整私钥块；用 `npm run security:secrets`
  验证为 0 个发现且不打印命中值。
  （FR-007、NFR-003；AC-008、AC-012）
- [X] T020 [US3] 在 `tests/integration/publish-security-workflow.test.js` 写权限静态断言：
  默认 `contents: read`；`build` 不授予写权限；`deploy` 仅 `pages: write`、`id-token: write`
  和 checkout/目标判定所需的 `contents: read`；
  checkout `persist-credentials: false`；无 PAT、secret、`pull_request_target`、fork 触发；
  Step Summary 不写入敏感字段。只补权限断言，不重复 T005 的基础结构项。
  （FR-007、NFR-003；AC-008）

### Validation for User Story 3

- [X] T021 [US3] 在隔离副本执行 T019/T020 和 `npm run security`（secrets/code/deps），记录
  扫描文件数、发现数、测试退出码到
  `specs/003-validate-build-publish/validation/us3-security.md`；不打印命中值或环境变量。
  （FR-007、NFR-003；AC-008、AC-012）
- [ ] T022 [US3] 如获授权，在受控仓库以无权限身份/不受信来源尝试触发构建与部署，确认无仓库、
  产物或线上副作用；记录到
  `specs/003-validate-build-publish/validation/us3-security.md`；未授权时记录未运行。
  （FR-007；AC-008）

**Checkpoint**: 凭证边界、权限和内容不执行可独立验证。

## Phase 6: User Story 4 — 自动提交后的显式发布衔接（Priority: P2）

**Goal**: 未来机器提交可在同一次运行显式进入构建与部署，不依赖隐式 push；无变化不制造空提交；
失败可按同一提交重跑。

**Independent Test**: 工作流结构断言 + 本地 noop/superseded 状态测试 + 受控仓库机器提交运行；
不实现 US-006 的来源检查或 Q-004 调度。

### Tests for User Story 4

- [ ] T023 [P] [US4] 在 `tests/integration/publish/publish-same-run.test.js` 写结构契约：`maintain.yml`
  只有一个发布工作流，`deploy` 与 `build` 在同一运行且 `needs` 链完整；不存在依赖
  `workflow_run` 或另一次 push 的部署入口；工作流注释/结构允许 US-006 增加 `sync` job 后
  通过 `needs` 进入 build/deploy。只补同次运行结构，不重复 T005 的基础触发/权限项。
  （FR-009、FR-011；AC-014）
- [ ] T024 [P] [US4] 在 `tests/unit/publish-noop.test.js` 增加 noop 场景：机器提交无内容变化时
  `content_status=noop`、`commit_status=not_applicable` 或 `committed`、不新建内容提交；
  允许重复部署同一快照，部署状态可为 `published` 或 `superseded`；失败重跑保持同一 `target_sha`。
  （FR-009；AC-011、AC-014）

### Validation for User Story 4

- [ ] T025 [US4] 在隔离/受控环境模拟机器提交（或等价 commit），确认同一运行显式构建并部署
  目标提交；无变化时允许重复部署同一快照，但不得新建内容提交或伪装成内容更新；记录到
  `specs/003-validate-build-publish/validation/us3-same-run.md`；未获授权时记录未运行。
  （FR-009、FR-011；AC-014）
- [ ] T026 [US4] 复核 `specs/003-validate-build-publish/research.md` 中“同次运行显式部署”的结论与
  实际工作流一致；如发现平台行为差异，先更新契约/计划再修改实现，不以隐式 push 补丁绕过。
  （FR-009、FR-011；AC-014）

**Checkpoint**: 四个故事均可独立验证；进入全量检查与范围复核。

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 完成全量检查、文档和最终复核，不新增业务能力。

- [ ] T027 [P] 运行 `npm run lint`、`npm run format:check`、`npm test`、`npm run security`；
  只修复本故事引入的失败；在
  `specs/003-validate-build-publish/validation/us3-quality.md` 记录实际命令、退出码、测试数量、
  扫描结果和未运行项；不得把工具缺失、网络失败或 `AUDIT_UNAVAILABLE` 当通过。
  （NFR-003、NFR-006；AC-008、AC-014）
- [ ] T028 [P] 定向更新 `README.md`、`AGENTS.md` 中本故事已实现并验证的命令、工作流状态、
  受控环境结果和未完成项；生产发布、US-004～US-007 仍标规划；不写未验证的命令或线上成功。
  （NFR-006；AC-014 工程支撑）
- [ ] T029 运行 `node scripts/publish-check.js artifact --dist <隔离 dist>` 与
  `node scripts/publish-check.js target ...` 的最终冒烟，确认退出码/JSON 与契约一致；
  记录到 `specs/003-validate-build-publish/validation/us3-quality.md`，不写工作区 `dist/`。
  （FR-009、FR-011；AC-011、AC-014）
- [ ] T030 对照 `spec.md`、`contracts/` 和 `validation/` 做最终差异复核：未改
  `skills/`、`catalog/`、索引/详情 schema、前端行为和根 `assets/search-index.json`；无凭证、
  额外依赖、全仓格式化或 Pages 设置修改；确认公开页面只展示 `updated_at`/`synced_at` 等成功同步
  信息，不出现运行日志或错误；T041 macOS 与 US-002 合并状态保持；更新 tasks/plan 状态并列出
  未运行项与剩余风险（SC-03/04/05 无受控仓库时标为未运行/部分），记录到
  `specs/003-validate-build-publish/validation/us3-final-review.md`。
  （FR-007、FR-009、FR-011；NFR-003、NFR-006；AC-008、AC-011、AC-014）

## Dependencies & Execution Order

### Phase Dependencies

```text
T001,T002 ── T003,T004,T005 ── T006 → T007 → T008 → T009
                                             │
        ┌────────────────────────────────────┴───────────────────────────┐
        ▼                    ▼                    ▼                      ▼
   US1: T010→T011→T012→T013  US2: T014,T015,T016   US3: T019,T020,T021    US4: T023,T024
                              →T017→{T018,T031}     →T022                 →T025→T026
        └────────────────────┴────────────────────┴──────────────────────┘
                                   ▼
                         T027,T028 → T029 → T032 → T030
```

T006/T007/T008 为共享阻塞项；T009 是 Foundational gate。各故事依赖 T009 完成，故事之间不互相阻塞。
T031/T032 为 2026-11-07 追加任务，不重排既有编号；T031 归入 US2，T032 归入 Polish。

### User Story Dependencies

- **US1**: 仅依赖 Foundational；是 MVP，验证合法/非法产物与固定路径。
- **US2**: 依赖 Foundational；独立验证失败、过期、重跑和恢复状态，可与 US1 并行。
- **US3**: 依赖 Foundational；独立验证凭证/权限/内容边界，可与 US1/US2 并行。
- **US4**: 依赖 Foundational；独立验证同次运行和 noop，可与前三者并行；受控仓库 POC 需授权。

### Within Each User Story

- 先写测试并确认真实失败，再实现/执行验证；已由共享层覆盖的行为直接复验，不伪造失败。
- 同一文件（`publish.test.js`、`publish-artifact.test.js`、`publish-workflow.test.js`、
  `publish-deploy-workflow.test.js`、`publish-security-workflow.test.js`、
  `publish-status.test.js`、`publish-noop.test.js`、`maintain.yml`）只能串行修改；
  不同文件可并行。
- 验证文件 `us3-recovery.md` 由 T017/T018/T031 串行写入；`us3-regression.md` 由 T032 写入。
- 真实 Pages 部署、权限尝试和机器提交只有在受控仓库授权后执行；否则记录未运行。

## Parallel Examples

### Foundational

T003（unit）、T004（artifact integration）、T005（workflow static）为不同文件，可在夹具完成后并行；
T006/T007/T008 按依赖串行，T009 最后执行。

### User Story 1

T010 完成后再执行 T011；T012 使用 T011 的构建产物，T013 在 T011 后串行补充 no-op 证据；
T012/T013 写入同一 `us3-snapshot.md`，需串行；T032 写 `us3-regression.md`，可在 T011 后独立执行。

### User Story 2

T014（状态单测）、T015（superseded CLI 集成）与 T016（部署工作流静态断言）为不同文件，可并行；
T017 等三者完成后执行；T031 本地恢复演练依赖 T017，可与 T018 并行；T018 需外部授权。

### User Story 3

T019（安全集成）与 T020（权限工作流静态断言）为不同文件，可并行；T021 等两者完成后执行；
T022 需外部授权。

### User Story 4

T023（同次运行结构测试）与 T024（noop 状态测试）为不同文件，可并行；T025/T026 在两者完成后执行，
其中 T025 需受控环境。

### Polish

T027（全量检查）与 T028（文档更新）可并行；T029 依赖 T027 的检查结果；T032 在 T011 后执行；
T030 最后执行并覆盖 T029/T032 的结果。

## Implementation Strategy

### MVP First

先完成 Phase 1～3（T001～T013），只交付可独立验证的“合法/非法产物 + 白名单 + 固定路径”；
不把状态/恢复、权限尝试或真实部署声称为完成。通过 US1 后再进入 US2/US3/US4。

### Incremental Delivery

共享校验与工作流 → US1 产物/快照 → US2 失败/恢复 → US3 权限/凭证 → US4 同次运行 →
Polish 全量检查/取用回归/文档/复核。每一步在隔离副本验证；受控仓库步骤单独授权、单独报告。

## Notes

- 不执行 `skills/` 中任何脚本/测试，不安装其依赖；发布产物中的脚本只作为文件。
- 不新增 npm 产品依赖；GitHub Actions 全部使用 plan/contracts 中的完整 SHA。
- `dist/` 是生成目录；测试和验证使用系统临时目录，不覆盖工作区 `dist/`。
- 生产 Pages 源、environment、分支保护和线上切换不在任务默认授权内；T018/T022/T025/T032 的受控部分
  未获授权时必须记录未运行，不能以本地测试或工作流文件存在代替。
- 不修改 US-001/US-002 的原件、catalog、schema、前端行为、旧链接或当前单版本。
- 提交按逻辑组拆分，仅暂存本故事文件；推送、合并 main 和生产发布需单独明确授权。

## 追加任务（2026-11-07 分析修订）

本批不重排既有 T001～T030：T031 归入 US2，T032 归入 Polish；两者均可先在隔离副本完成，
受控部署部分再按授权补充。

- [ ] T031 [US2] 在隔离副本生成一次内容提交及对应的受控恢复提交（`git revert` 或等价恢复），
  分别构建并记录恢复前后的 `contentRevision`；确认恢复后既有 slug、四个旧 `#/skill/<slug>` 链接、
  当前单版本和 Git 历史保持一致，不 force push；把命令、结果和未运行项写入
  `specs/003-validate-build-publish/validation/us3-recovery.md`。本任务不需要远程写入。
  （FR-009；AC-011）
- [ ] T032 [P] 在隔离构建或受控站点回归 US-001/US-002：复制原文（含 frontmatter）、
  单文件/目录 ZIP/附件下载摘要、详情/列表分享、四个旧链接和当前单版本；记录到
  `specs/003-validate-build-publish/validation/us3-regression.md`；受控部署未授权时
  只做隔离构建等价检查并记录未运行项。
  （FR-011；AC-002、AC-005 回归）

## 追加任务（2026-11-07 Step Summary 补齐）

- [X] T033 [US2] 在 `.github/workflows/maintain.yml` 的 build 与 deploy Step Summary 中补齐完整
  RunStatus 字段（运行标识/链接、触发方式、目标 SHA、`commit_status`、`content_revision`、
  `content_status`、`deploy_status`、时间或 `run_url`、失败码/`superseded` 说明和可选页面地址），
  复用 `scripts/lib/publish.js` 的状态模型；新增测试覆盖 build 成功/失败、deploy
  `published`/`failed`/`superseded`、摘要脱敏和工作流字段；不改变触发、权限和部署顺序。
  （FR-009；AC-011、AC-014）
