# Feature Specification: Agent 命令维护 Skill（US-005）

**Feature Branch**: `codex/us-005-skill-cli`

**Created**: 2026-11-08

**Status**: Implemented（本地/受控验收完成并合并 main；生产 Pages 已切换，生产 environment 审批与部署失败注入未运行；见 [plan.md](plan.md)）

**Input**: 用户确认进入 US-005（Agent 命令与 README）。依据上游 FR-006、FR-007、FR-009、NFR-003、
NFR-006、AC-007、AC-008、AC-011，以及 DEC-006、Q-001 与 TechnicalSolution 3.4/C-05 已确认约束。

## 上游映射与范围

| 上游 | 本轮适用内容 | 证据 |
|---|---|---|
| FR-006 | 本地文件/目录或受支持来源 + 元数据；校验预览与非交互执行；同内容 noop；同 slug 不同内容需显式替换并携带基线修订；输出 slug、内容标识、变更/发布状态、公开链接或运行标识；README 完整 | AC-007 |
| FR-007 | 仅管理员/授权 Agent；复用既有 Git/gh 授权；不新增凭证入口；不执行第三方内容 | AC-008 |
| FR-009 | 提交、构建、部署状态分开；失败保留旧站；按同一提交重跑 | AC-011 |
| NFR-003/006 | 无凭证泄露、无内容执行、路径边界；README 可独立执行 | AC-008 |

**本轮不做**：自动来源检查/调度（US-006）、站内后台、ZIP 解压、跨平台格式导出；生产 Pages 切换已在
合并后单独执行，不在本故事验收内。
`import` 只做一次性结构化来源获取；持续跟踪与冲突矩阵由 US-006 承担。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 校验预览与新增（Priority: P1）

管理员或用受权 Agent 在本地 checkout 中给出单文件/目录 Skill 与元数据，先做只读预览；确认后执行
发布。命令输出结构化 JSON，区分校验、提交、构建与部署状态；相同内容重复提交为 no-op。

**Why this priority**：这是命令维护的最低可用闭环，也是与手动维护共用规则的入口。

**Independent Test**：在隔离临时仓库对合法单文件/目录执行预览与发布（本地模拟远端），检查预览无写入、
发布只暂存该 Skill 相关文件、输出字段与退出码正确；相同内容再次提交为 noop。

**Acceptance Scenarios**：

1. **Given** 合法本地单文件/目录与完整元数据，**When** 执行预览，**Then** 退出码 `0`，输出
   `content_status` 预览结果和 slug，且不写入工作区、不提交、不推送。对应 FR-006、AC-007。
2. **Given** 预览通过，**When** 执行发布且未指定等待，**Then** 输出提交标识、运行链接（若可查询）与
   `content_status`/`deploy_status`，状态不得把“已提交”写成“已发布”。对应 FR-006、FR-009。
3. **Given** 相同 slug 与相同内容再次提交，**When** 校验执行，**Then** 返回 noop，不创建空内容提交。
   对应 FR-006、AC-011。
4. **Given** 未认证或无写权限，**When** 执行发布，**Then** 返回可区分的未授权退出码，不产生提交或
   远端副作用。对应 FR-007、AC-008。

---

### User Story 2 - 显式替换与冲突（Priority: P1）

对已存在 slug 使用不同内容时必须显式替换，并携带期望基线修订；远端基线已变化或未提供基线时返回
冲突，不覆盖当前内容、不 force push。

**Why this priority**：命令是高频写入路径，静默覆盖会破坏当前版本和他人修改。

**Independent Test**：在隔离仓库准备基线提交，分别用正确/过期 `--expected-revision` 执行替换，
检查成功路径单版本、冲突路径保留当前内容且退出码可区分；`--meta` 缺省时保留原站内元数据。

**Acceptance Scenarios**：

1. **Given** 已存在 slug 与正确的基线修订，**When** 执行显式替换，**Then** 该 slug 仍只有一个当前
   版本，旧附件按新清单清理，站内元数据默认保留。对应 FR-006、AC-007。
2. **Given** 远端基线已前进或基线修订不匹配，**When** 执行替换，**Then** 返回冲突退出码，保留当前
   内容，不 force push、不重写历史。对应 FR-006、FR-009。
3. **Given** 未提供基线修订且目标 slug 已存在，**When** 执行替换，**Then** 返回参数/冲突错误，
   不静默覆盖。对应 FR-006。

---

### User Story 3 - GitHub 来源导入（Priority: P2）

管理员给出结构化 GitHub 来源（owner/repo/path、ref 策略）与元数据，一次性获取同一不可变修订的
单文件或目录并执行与本地输入相同的校验；不解析网页、不执行来源脚本、不安装依赖。

**Why this priority**：命令需要支持常见来源导入，但持续跟踪属于 US-006。

**Independent Test**：用隔离/模拟来源返回固定文件树，检查导入内容与校验、来源不可达或目录截断时
返回可区分错误且不写入当前内容。

**Acceptance Scenarios**：

1. **Given** 合法 GitHub 单文件/目录定位，**When** 执行导入预览，**Then** 获取同一修订的完整候选，
   校验通过并输出 slug/状态，不执行来源脚本。对应 FR-006、FR-007、AC-007/008。
2. **Given** 来源 404、403、限流或目录截断，**When** 执行导入，**Then** 返回来源读取失败退出码，
   不写入当前内容、不删除现有版本。对应 FR-006、FR-009。
3. **Given** 未提供结构化定位或使用普通网页地址，**When** 执行导入，**Then** 拒绝为不支持来源，
   不猜测最新版。对应 FR-006。

---

### User Story 4 - 状态查询与等待（Priority: P2）

管理员按运行标识查询最近状态，或要求命令等待部署完成；等待超时返回可区分退出码并保留运行链接，
只有观察到部署成功才报告 published。

**Why this priority**：命令必须能把提交、构建和部署结果如实反馈给调用者。

**Independent Test**：用固定运行状态响应模拟 submitted/building/published/failed/superseded 与超时，
检查 JSON 字段、退出码和“不得误报已发布”。

**Acceptance Scenarios**：

1. **Given** 有效运行标识，**When** 查询状态，**Then** 输出 `content_status`、`deploy_status`、
   `run_url` 与稳定错误码；不输出凭证。对应 FR-009、AC-011。
2. **Given** 已提交但部署未完成，**When** 使用等待选项，**Then** 在超时前持续查询；超时返回专用
   退出码并保留运行链接，不报告 published。对应 FR-009。
3. **Given** 运行已失败或过期，**When** 查询状态，**Then** 如实返回 failed/superseded，不提供
   虚假成功。对应 FR-009、AC-011。

---

### User Story 5 - README 命令契约（Priority: P3）

README 说明安装/前提、认证、预览、发布会话、替换、来源导入、状态查询、退出码与排错；示例使用
占位凭证，未实现能力标“规划”。

**Why this priority**：命令只有在文档可独立执行时才可交付。

**Independent Test**：按 README 在干净 checkout 完成预览、发布（隔离远端）、替换冲突与状态查询；
文档中的命令与退出码与实际一致。

**Acceptance Scenarios**：

1. **Given** 干净 checkout 与已授权 Git/gh 会话，**When** 按 README 操作，**Then** 可完成预览、
   发布、替换和状态查询，无需写入 token 参数。对应 FR-006、NFR-006。
2. **Given** 文档示例包含凭证字段，**When** 审查，**Then** 只允许 `YOUR_*_HERE` 等占位值；
   未实现命令必须标注规划。对应 FR-007、AC-008。

### Edge Cases

- 预览/发布遇到非法元数据、路径越界、缺失附件、凭证或超限：返回校验错误，不写入、不提交。
- 相同内容重复提交：noop；不同内容同 slug 未显式替换或基线过期：conflict。
- 远端并发更新、非 fast-forward、分支保护拒绝：失败关闭，不 force push、不降低保护。
- 来源 401/403/404/429/超时/目录截断/Symlink/子模块：返回可区分错误，不替换当前内容。
- 等待期间运行排队、取消、过期或超时：输出真实状态与运行链接，不误报 published。
- 输出包含运行链接、提交标识和公开链接：不得包含 token、cookie、响应正文或原始异常。
- 本地提交成功但部署失败：明确 deploy_failed，旧站保留，可按同一提交重试。
- 未授权身份、无 gh 会话或凭证过期：返回未授权/读取失败，不产生部分写入。
- README 中未实现能力：标记规划，不作为可执行命令承诺。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-006（本轮）**：系统 MUST 提供非交互命令，支持本地单文件/目录与结构化 GitHub 来源的
  `add`/`import`、已存在 slug 的 `replace`、按运行标识的 `status`，以及只读预览和可选的发布/等待。
  输入 MUST 包含 Skill 内容与必要元数据；已存在 slug 的新内容 MUST 显式替换并携带期望基线修订，
  不匹配 MUST 返回冲突，不静默覆盖、不 force push。相同内容重复提交 MUST 为 noop，不创建空内容
  提交。发布 MUST 在隔离工作副本中基于远端基线进行，只暂存该 Skill 的原件、图库记录与跟踪文件；
  MUST NOT 使用 `git add .`、重置用户工作区或提交无关文件。输出 MUST 为结构化 JSON，包含 slug、
  内容标识、`content_status`、`deploy_status`、提交标识、运行链接与公开链接（可用时）；本地保存
  或提交成功 MUST NOT 报告为已发布。退出码 MUST 区分成功/参数错误/未授权/冲突/来源失败/构建失败/
  部署失败/等待超时。**验收**：User Story 1～4；AC-007。
- **FR-007（本轮）**：命令 MUST 仅由管理员或授权 Agent 在受信任环境执行，认证 MUST 复用既有
  Git/gh 会话，MUST NOT 要求把 token 写入参数、仓库或输出。未授权、无写权限或凭证过期 MUST 失败
  关闭且无远端副作用。第三方 Skill MUST 作为数据处理，MUST NOT 执行其脚本/测试或安装依赖；
  凭证 MUST NOT 进入页面、产物、日志、示例或 JSON 输出。命令与手动维护 MUST 共用同一校验和发布
  规则。**验收**：User Story 1、3；AC-008。
- **FR-009（本轮）**：命令 MUST 分开报告内容提交、构建与部署状态，提供运行标识与稳定错误原因；
  部署失败 MUST 保留上次正常站点，允许按同一提交重跑；等待超时 MUST 保留运行链接并返回专用
  退出码，不报告成功。公开页面 MUST NOT 展示运行日志或内部错误。**验收**：User Story 2、4；
  AC-011。
- **FR-010（本轮）**：README MUST 说明前提、安装/运行、认证、预览、发布、替换、来源导入、状态
  查询、退出码与排错；示例 MUST 使用占位凭证；未实现命令 MUST 标记规划。**验收**：User Story 5；
  AC-007、NFR-006。

**适用非功能需求与验收边界**：

| 上游 ID | 本轮适用规则 | 本轮验收 | 留给后续的部分 |
|---|---|---|---|
| NFR-003 | 无凭证泄露、无内容执行、路径/来源边界 | AC-008 的命令路径 | 自动同步失败矩阵由 US-006 承担 |
| NFR-006 | 干净 checkout 可执行、依赖锁定、README 完整 | AC-007 的命令说明 | 平台安装包/发行渠道 |
| NFR-004 | 冲突不覆盖、重试幂等、等待不误报 | AC-011 的命令路径 | 调度与并发矩阵由 US-006 承担 |

**上游 AC 映射**：

| 上游验收 | 本轮操作与证据 | 覆盖声明 |
|---|---|---|
| AC-007 | 预览、发布、noop、替换/冲突、来源导入、状态查询、README | 覆盖 Agent 命令路径 |
| AC-008 | 授权复用、无凭证输出、不执行内容、未授权无副作用 | 覆盖命令路径；上传入口仍属后续 |
| AC-011 | 提交/构建/部署分离、部署失败保留、按同一提交重跑 | 覆盖命令状态与重跑语义 |

### Key Entities

- **命令请求**：操作类型（preview/add/import/replace/status）、内容定位或来源、元数据、期望基线、
  发布/等待选项；不含凭证。
- **内容记录**：与原件分离的站内元数据；替换默认保留，显式提供时更新。
- **发布结果**：slug、内容标识、提交标识、`content_status`、`deploy_status`、运行链接、公开链接、
  稳定错误码；状态不得合并。
- **来源定位**：provider、repository、path、ref 策略与 ref；只允许结构化 GitHub 定位。
- **冲突与诊断**：期望基线不匹配、远端变化、来源不可达、构建/部署失败或等待超时；诊断脱敏。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **US005-SC-01**：预览在 100% 场景下不写入工作区、不提交、不推送；退出码与 JSON 状态可区分。
- **US005-SC-02**：合法新增/导入发布后 100% 输出 slug、内容标识与提交标识；只有观察到部署成功
  才报告 published。
- **US005-SC-03**：相同内容重复提交 100% 返回 noop，不新增内容提交；同 slug 未显式替换或基线
  过期 100% 返回冲突且保留当前内容。
- **US005-SC-04**：来源 404/403/限流/目录截断 100% 失败关闭，不删除或覆盖当前版本。
- **US005-SC-05**：命令输出、日志、示例与 README 中的凭证回显为 0；收录 Skill 的脚本执行次数为 0。
- **US005-SC-06**：等待超时与部署失败 100% 返回真实状态与运行链接，不误报成功；同一提交重试
  不依赖新内容提交。

## Assumptions

- 管理员已具备仓库写权限；命令在项目 checkout 或受控临时 checkout 中运行，认证复用 Git/gh 会话
  （Q-001、DEC-006）。
- 发布目标为当前仓库默认分支的远端基线；远端变化返回冲突，不 force push。
- `import` 只做一次性结构化 GitHub 获取；自动跟踪、调度与许可变化策略属于 US-006。
- 生产发布与 Pages 切换需单独授权；验收可在隔离临时仓库与受控 POC-002 完成。
- 未实现能力（如 ZIP 解压、平台格式导出）在 README 标记规划，不纳入本轮成功标准。
