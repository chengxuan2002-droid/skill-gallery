# Feature Specification: 整体验收与交接（US-007）

**Feature Branch**: `codex/us-007-overall-acceptance`

**Created**: 2026-11-14

**Status**: Draft

**Feature Directory**: `specs/007-overall-acceptance/`

**Input**: User request: “进入 US-007 整体验收”。依据上游 FR-001～FR-011、NFR-001～NFR-006、
Demo-001～003、AC-001～AC-015，以及 US-001～US-006 已验收基线和项目宪章 1.0.0。

## Baseline

- US-001～US-006 已完成本地/受控实现与验收；生产 Pages 已切换，US-006 生产调度已启用。
- US-006 的 2026-11-14 03:17 窗口在 05:10 CST 前未出现；08:19 CST 出现延迟 schedule run
  `43533439066`（sync success、build/deploy skipped）。
- 当前生产 catalog 的 `source_tracking` 全部为 `null`，尚无生产来源；Demo-002 的自动更新证据来自
  POC-003 受控验证，用户已确认可接受为受控证据。
- US-001 T041 macOS 未验证；US-005 真实 `gh api` 导入与 `--wait` 运行发现未补验；生产 environment
  审批、部署失败注入、发布后 MIME/缓存未验证。
- 用户已确认：US-007 可以带着未运行项进入验收，但**不得把未运行计为通过或宣称整包完成**。

## User Scenarios & Testing

### User Story 1 - 手动/命令维护到公开取用（Priority: P1）

管理员通过 GitHub 后台或 `skill-cli` 维护 Skill，访客从固定站点完成检索、详情、复制和下载。

**Independent Test**：在隔离副本和受控仓库完成一次手动新增/替换、一次 CLI preview/add/import，
再从公开站点检索、打开详情、复制和下载，核对原件字节与 slug。

**Acceptance Scenarios**：

1. **Given** 合法单文件或目录型 Skill，**When** 管理员通过 GitHub 后台提交，**Then** 构建发布后
   列表、详情、复制和下载均可见，旧链接保持。对应 Demo-001、AC-001/AC-005。
2. **Given** 已登录的 Agent，**When** 执行 `skill-cli` preview/add/import/replace/status，**Then**
   预览零写入、提交只含目标文件、状态区分 submitted/published。对应 Demo-001、AC-007/AC-011。
3. **Given** 非法或含凭证的输入，**When** 提交或预览，**Then** 整批失败、旧站保留、诊断不含凭证值。
   对应 AC-008/AC-012。

### User Story 2 - 上游升级到单一新版（Priority: P1）

受控 GitHub 来源从 v1 更新到 v2 后，自动检查、完整替换并发布同一 slug，不保留旧附件或第二版本。

**Independent Test**：使用 POC-003 的源仓库和消费端 POC-002，核对 branch/release/pinned、增删附件、
许可基线和同次发布；生产调度延迟 run 作为调度触发证据。

**Acceptance Scenarios**：

1. **Given** 已启用来源和上次同步基线，**When** 上游 v2 删除旧附件并新增文件，**Then** 单版本替换、
   slug 不变、旧附件消失、站内字段保留。对应 Demo-002、AC-009。
2. **Given** 相同内容或无变化检查，**When** 再次运行，**Then** unchanged/noop，不创建内容提交。
   对应 AC-009/AC-011。
3. **Given** 许可缺失/变化或本地修改，**When** 检查执行，**Then** policy_blocked/conflict，当前版本保留。
   对应 AC-010。
4. **Given** 生产每日调度已启用，**When** 查看 schedule 运行，**Then** 可区分真实运行与手动重跑；
   延迟/跳过不被写成准点 SLA。对应 AC-011、Q-004。

### User Story 3 - 失败、冲突到恢复（Priority: P1）

404、限流、非法候选、构建失败、部署失败或并发变化时，系统失败关闭；管理员能查看状态、重跑同一提交
并通过受控历史恢复。

**Independent Test**：使用 POC-002/003 和现有测试夹具注入 404、许可变化、冲突、构建/部署失败，
核对旧站保留、同提交重跑和 revert 恢复。

**Acceptance Scenarios**：

1. **Given** 来源 404/限流/截断/非法候选，**When** 检查执行，**Then** 该来源失败、其他来源继续、
   当前版本保留。对应 Demo-003、AC-010/AC-012。
2. **Given** 内容已提交但部署失败，**When** 管理员查看状态，**Then** 显示“提交成功、部署失败”，
   线上保留旧站。对应 AC-011。
3. **Given** 需要恢复，**When** 通过受控 revert 提交并重新发布，**Then** slug、旧链接和单版本保持，
   历史未被强制改写。对应 AC-011。

### User Story 4 - 固定地址、旧链接与浏览器可达（Priority: P2）

站点继续位于 `https://chengxuan2002-droid.github.io/skill-gallery/`，资源兼容 `/skill-gallery/`，
既有 `#/skill/<slug>` 和列表分享链接保持。

**Independent Test**：对生产站点检查首页、索引、详情、原件、下载和旧 hash 链接，并在可用浏览器
覆盖 360/768/1440、明暗主题、键盘操作；未验证的 Safari/移动实机单独记录。

**Acceptance Scenarios**：

1. **Given** 固定站点和既有 slug，**When** 打开旧详情/列表链接，**Then** 仍可访问对应内容或明确
   未找到状态，不出现错误路由。对应 AC-005/AC-014。
2. **Given** 360/768/1440 视口和明暗主题，**When** 使用键盘检索、筛选、打开详情和复制，**Then**
   主链路可用、无横向溢出、焦点可见。对应 AC-013/AC-015。
3. **Given** 下载原件或目录 ZIP，**When** 解包比对，**Then** 文件清单、字节、可执行位和许可保持。
   对应 AC-002/AC-004。

### User Story 5 - 交接、未运行项与恢复路径（Priority: P2）

交接材料列明实际状态、证据、未运行项和恢复方式；不把本地/受控/生产状态混写。

**Independent Test**：从干净 checkout 按 README 执行预览、发布、状态查询、恢复说明；逐项核对
AC/Demo 矩阵和未运行项。

**Acceptance Scenarios**：

1. **Given** 干净副本，**When** 按 README 执行可行命令，**Then** 命令、退出码、状态字段与实际一致。
   对应 AC-007/AC-011。
2. **Given** 未运行项，**When** 审阅交接报告，**Then** 每项标注“未运行”及原因，不列入通过。
   对应 AC-001～AC-015 的未覆盖部分。
3. **Given** 生产调度已启用，**When** 报告生产状态，**Then** 区分配置、实际运行、内容提交、构建和
   部署，不把延迟 schedule run 写成准点执行。对应 AC-011/AC-014。

## Requirements

### Functional Requirements

- **FR-001（验收矩阵）**：系统 MUST 提供 AC-001～AC-015、Demo-001～003 与 US-001～US-006 的逐项
  状态矩阵，状态只能是“通过 / 受控通过 / 未运行 / 失败”，并附证据路径、命令或运行标识。
- **FR-002（Demo-001）**：MUST 验证手动与命令维护到公开取用，包括单文件/目录、替换、下架、检索、
  详情、复制、原件和 ZIP 下载。
- **FR-003（Demo-002）**：MUST 用 POC-003 受控证据验证 v1→v2 自动更新、单版本、许可基线和无变化；
  用户已确认受控证据可作为本项通过依据，但 MUST 标明“受控通过”，不得写成生产自动更新。
- **FR-004（Demo-003）**：MUST 验证 404/限流/非法候选/许可变化/本地冲突/构建失败/部署失败/并发过期，
  确认旧站保留、状态可区分、同提交重跑和受控恢复。
- **FR-005（固定地址）**：MUST 验证生产首页、索引、详情、原件、下载和旧 hash 链接；资源路径
  MUST 兼容 `/skill-gallery/`。
- **FR-006（保真）**：MUST 对比原件、附件、二进制、许可、相对路径和 ZIP 清单；不得用搜索文本代替原件。
- **FR-007（安全）**：MUST 复核凭证无泄漏、无上游脚本执行、路径/URL 边界和公开产物白名单；未授权
  写入不得产生副作用。
- **FR-008（状态与恢复）**：MUST 区分提交、构建、部署和调度状态；部署失败/过期保留旧站；重跑幂等；
  恢复使用受控 Git 历史，保持 slug 和旧链接。
- **FR-009（未运行项）**：MUST 单独列出 T041 macOS、US-005 真实 `gh api`/`--wait`、生产 environment
  审批、生产部署失败注入、MIME/缓存、真实 403/限流等未运行项；不得计为通过。
- **FR-010（交接）**：MUST 更新 README/AGENTS/validation 的状态、命令、已知缺口和恢复路径；文档、
  受控验证和生产发布分别表述。

### Success Criteria

- **US007-SC-01**：AC-001～AC-015 和 Demo-001～003 100% 出现在矩阵中，且每项有状态、证据和未运行说明。
- **US007-SC-02**：Demo-001 主链路（维护→检索→详情→复制→下载）通过，原件/ZIP 清单与字节一致。
- **US007-SC-03**：Demo-002 的受控证据完整，单版本、旧附件清理、许可基线和无变化均通过。
- **US007-SC-04**：Demo-003 的失败矩阵 100% 失败关闭，旧站保留、同提交重跑和受控恢复有运行标识。
- **US007-SC-05**：固定地址、旧链接和 `/skill-gallery/` 资源检查通过；未验证的 Safari/移动实机明确列出。
- **US007-SC-06**：未运行项数量、原因和影响 100% 可追溯；报告不出现凭证、响应正文或原始异常。
- **US007-SC-07**：生产调度配置、已观察 run、实际触发时间和未观察窗口分别记录；不把延迟 run 写成准点。

## Key Entities

- **AcceptanceItem**：AC/Demo 编号、范围、状态、证据、命令/运行标识、未运行原因。
- **HandoffReport**：实际完成项、受控通过项、未运行项、生产状态、恢复步骤和剩余风险。
- **ProductionState**：站点 revision、最新部署 run、调度配置、已观察 schedule run、来源配置状态。

## Scope and Constraints

**本轮做**：只做验收、证据整理、文档交接和必要的受控复验；可读取生产站点和 Actions 运行记录。
**本轮不做**：新增业务功能、重写前端、扩展来源适配器、降低验收标准、把未运行项写成通过。
生产写入、配置真实来源或部署失败注入仍按项目授权边界单独处理。

## Assumptions

- Demo-002 的 POC-003 受控证据已被用户接受；生产尚无真实来源，因此不声称生产自动更新已实际发生。
- US-007 可以带着未运行项完成“有条件验收/交接”，但整包通过必须等关键未运行项关闭或用户明确接受。
- 生产调度首次 window 已出现延迟 run；后续 window 的观察不阻塞验收矩阵，但必须如实标注。
