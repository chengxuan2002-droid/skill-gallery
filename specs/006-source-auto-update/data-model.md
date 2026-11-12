# Phase 1 Data Model: US-006 来源定期检查与自动替换

**Date**: 2026-11-12 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本故事不新增数据库或公开内容 schema。来源配置复用现有 `catalog/<slug>.json` 的
`source_tracking` 字段；候选、运行报告和状态为运行期数据，不进入公开搜索索引。

## 1. SourceTracking

| 字段 | 类型 | 规则 |
|---|---|---|
| `provider` | `"github"` | 当前唯一支持值；未知 provider 视为 unsupported，不发起请求 |
| `repository` | string | `owner/repo`，拒绝网页 URL、空格和额外斜杠 |
| `path` | string | 仓库内 POSIX 相对路径；单文件或目录；拒绝越界/反斜杠/控制字符 |
| `ref_policy` | `branch` \| `release` \| `pinned` | 必须解析到不可变提交 |
| `ref` | string | 分支名、Release 标识或 40 位固定提交；不可为空 |
| `enabled` | boolean | 仅 true 时参与定时/手动检查 |
| `last_synced_revision` | string \| null | 最近成功替换的来源修订 |
| `last_synced_digest` | string \| null | 最近成功替换的内容摘要，覆盖完整文件清单 |
| `synced_at` | ISO 8601 带时区 \| null | 最近成功替换时间；不因无变化检查刷新 |

状态：

```text
unconfigured（source_tracking=null）
  → enabled（管理员启用且配置合法）
  → paused（管理员禁用或主动暂停）
  → unsupported（provider 非 github 或定位不受支持）
```

- `last_checked_at` 不属于持久化字段；每次运行的检查时间只进入运行报告，避免无变化检查制造提交。
- `last_synced_digest` 与当前内容摘要不一致时视为本地修改冲突。
- 首次启用且无 `last_synced_digest` 时，不允许静默覆盖已有内容；候选与当前内容一致可建立基线，
  否则返回 conflict。

## 2. CandidateSnapshot

| 字段 | 类型 | 规则 |
|---|---|---|
| `slug` | string | catalog 中的稳定标识 |
| `revision` | 40 位 SHA | 来源解析后的不可变提交 |
| `kind` | `single` \| `directory` | 由 catalog `content_path` 与候选结构共同决定 |
| `files` | object[] | 相对路径、字节、SHA-256、可执行位；覆盖主文档和全部附件 |
| `directories` | string[] | 需要保留的空目录 |
| `digest` | SHA-256 | 复用现有 `computeDigest`；覆盖路径、字节、可执行位和空目录 |
| `license` | object \| null | 来源子树内识别到的许可文件路径与摘要；缺失为 null |
| `validation` | object | 复用现有 schema/路径/凭证/大小/主文档校验结果 |

读取限制沿用现有规则：每 Skill 最多 500 个普通文件、20 MiB、主文档 1 MiB；拒绝符号链接、
硬链接、子模块、绝对路径、`..`、反斜杠、控制字符、凭证路径和疑似凭证内容。候选仅作为数据读取，
不执行脚本或安装依赖。

## 3. MaintenanceRun

| 字段 | 类型 | 规则 |
|---|---|---|
| `run_id` | string | Actions 运行标识或本地运行标识 |
| `trigger` | `push` \| `schedule` \| `workflow_dispatch` \| `manual` | 触发方式 |
| `started_at` / `finished_at` | ISO 8601 \| null | 真实时间；未知为 null |
| `commit_sha` | 40 位 SHA \| null | 本次批次提交；无变化为 null |
| `commit_status` | `not_applicable` \| `committed` \| `failed` | 与内容/部署状态分开 |
| `changed` | boolean | 本次是否有内容提交 |
| `sources` | SourceResult[] | 每个来源的逐项结果 |
| `content_revision` | string \| null | 构建产物标识；未构建为 null |
| `content_status` | `pending` \| `built` \| `noop` \| `failed` | 沿用发布状态模型 |
| `deploy_status` | `pending` \| `deploying` \| `published` \| `failed` \| `superseded` | 沿用发布状态模型 |

### SourceResult

| 字段 | 类型 | 规则 |
|---|---|---|
| `slug` | string | 目标 Skill |
| `source` | SourceTracking 子集 | provider/repository/path/ref_policy/ref/enabled |
| `status` | `unchanged` \| `candidate` \| `updated` \| `failed` \| `conflict` \| `policy_blocked` \| `unsupported` | 逐项结果 |
| `resolved_revision` | SHA \| null | 成功解析的来源修订 |
| `content_digest` | SHA-256 \| null | 候选或当前内容摘要 |
| `previous_digest` | SHA-256 \| null | 上次同步摘要 |
| `license_status` | `present` \| `missing` \| `changed` \| `not_applicable` | 许可策略结果 |
| `error_code` | 稳定错误码 \| null | 如 `E_SOURCE`、`E_CONFLICT`、`E_LICENSE`、`E_TRUNCATED` |
| `checked_at` | ISO 8601 | 真实检查时间 |

报告只允许封闭字段；错误消息必须脱敏，不回显上游响应正文、token、cookie 或文件内容。

## 4. ContentRecord

沿用 `catalog/<slug>.json` 封闭 schema。同步只能更新：

- `source_tracking.last_synced_revision`
- `source_tracking.last_synced_digest`
- `source_tracking.synced_at`
- 单文件与目录形态互换时的 `content_path`（保持 `slug` 不变，且只在完整新清单通过校验后更新）
- 适用时由来源声明的 `author`、`declared_version`、`repository_url` 等来源字段（按记录字段优先级）

以下站内字段不得被同步覆盖：`display_name`、`description`、`tags`、`platforms`、`usage`、
`notes`、`allowed_dot_paths`、`created_at` 及管理员维护的 `license`/地址字段（若来源没有明确
优先级）。候选内容与 catalog 记录分离；不改写第三方 `SKILL.md` 来补站内元数据。

## 5. PublicationOutcome

| 字段 | 类型 | 规则 |
|---|---|---|
| `commit_sha` | SHA \| null | 批次提交；无变化为 null |
| `content_revision` | string \| null | 构建产物标识 |
| `content_status` | `pending` \| `built` \| `noop` \| `failed` | 内容状态 |
| `deploy_status` | `pending` \| `deploying` \| `published` \| `failed` \| `superseded` | 部署状态 |
| `run_url` | URL \| null | 运行链接；不含凭证 |
| `public_url` | URL \| null | 详情/公开链接；仅在安全时输出 |
| `errors` | Diagnostic[] | 稳定错误码与位置；不含自由文本/响应正文 |

状态转换：

```text
unconfigured → enabled → paused/unsupported
checking → unchanged | candidate | failed | conflict | policy_blocked
candidate → validated → committed → building → deploying → published
committed → build_failed（不部署）
committed → deploy_failed（线上保留旧站，可按同一提交重跑）
build/deploy pending → superseded（目标已过期）
```

- 无变化：`unchanged`，`commit_status=not_applicable`，`content_status=noop`，`deploy_status=pending`。
- 有更新：`updated`，`commit_status=committed`，只有观察到部署成功才为 `published`。
- 失败：保留当前内容与旧站；不把来源失败、构建失败或部署失败合并为单一“成功”。

## 6. 不变量

1. 任何候选应用前必须完成来源修订锁定、完整树读取和现有校验。
2. 同一 slug 在当前内容树、索引和下载中只有一个有效版本；旧附件必须删除。
3. 候选、提交、构建和部署必须来自同一内容快照；同步提交后的 build checkout 必须指向该提交。
4. `last_synced_*` 只在成功提交后更新；无变化检查不写 Git。
5. 当前内容摘要与 `last_synced_digest` 不一致时不得自动覆盖。
6. 许可缺失或变化时不得自动替换。
7. 运行报告和 Step Summary 不包含凭证、上游响应正文或原始异常。
