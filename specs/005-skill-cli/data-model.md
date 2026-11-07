# Phase 1 Data Model: US-005 Agent 命令维护

**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本故事不新增持久化数据库或内容 schema。下列模型描述命令输入、候选、发布结果与状态视图；
现有 `catalog`、搜索索引、详情 JSON、原件与 ZIP 的 `schemaVersion=1` 契约不变。

## 1. CliInvocation

一次命令调用。

| 字段 | 类型 | 规则 |
|---|---|---|
| `command` | `preview` \| `add` \| `import` \| `replace` \| `status` | 必填；互斥 |
| `input` | string \| null | `add`/`preview` 的本地路径；`replace` 的新内容路径 |
| `source` | SourceSpec \| null | `import` 必填；与 `input` 互斥 |
| `metaPath` | string \| null | `add`/`import` 必填；`replace` 可选（缺省保留原记录） |
| `slug` | string \| null | `replace`/`status` 使用；slug 规则同 catalog |
| `expectedRevision` | string \| null | `replace` 必填；40 位提交标识 |
| `publish` | boolean | 缺省 false；true 才允许远端写入 |
| `wait` | boolean | 仅 publish 时可用；等待部署完成 |
| `json` | boolean | 缺省 true；stdout 单行 JSON |
| `runId` | string \| null | `status` 必填 |
| `timeoutSeconds` | integer | `--wait` 总时限；上限受文档约束 |

校验：互斥选项冲突、缺少必填、`--wait` 未 publish、非法 slug/SHA 均返回退出码 `2`。

## 2. Candidate

校验后的候选内容。

| 字段 | 类型 | 规则 |
|---|---|---|
| `kind` | `file` \| `directory` | 由输入/来源推导 |
| `files` | object[] | `path`（POSIX 相对）、`bytes`、`sha256`、`executable` |
| `digest` | string | 覆盖排序路径与文件字节的 SHA-256；不只看主文档 |
| `record` | ContentRecord | 与原件分离的站内记录 |
| `source` | SourceSpec \| null | 来源导入时保留定位 |
| `mainPath` | string | `skills/<slug>.md` 或 `skills/<slug>/SKILL.md` 对应主文档 |

校验：最多 500 个普通文件、总量 20 MiB、主文档 1 MiB；拒绝符号链接/硬链接、绝对路径、`..`、
反斜杠、控制字符、隐藏凭证与疑似凭证内容；不执行任何文件。

## 3. ContentRecord

沿用 `catalog/<slug>.json` 的封闭 schema：`schemaVersion=1`、`slug`、`display_name`、
`description`、`content_path` 必填；标签、平台、作者、地址、版本、来源、用法、备注、许可、日期与
`source_tracking` 可选。`replace` 默认保留原记录，显式 `--meta` 时整体替换并重新校验。

## 4. SourceSpec

| 字段 | 类型 | 规则 |
|---|---|---|
| `provider` | `github` | 本轮唯一支持值 |
| `repository` | string | `owner/repo` |
| `path` | string | 仓库内单文件或目录；POSIX 相对 |
| `refPolicy` | `branch` \| `release` \| `pinned` | 解析到不可变提交 |
| `ref` | string | 分支名、Release 标识或固定提交 |

读取要求：先解析到不可变 SHA；完整读取文件树（`truncated` 即失败）；拒绝子模块、符号链接、
越界路径；404/403/429/超时映射到来源读取失败（`5`）。

## 5. PublishOutcome

| 字段 | 类型 | 规则 |
|---|---|---|
| `slug` | string | 目标 slug |
| `content_revision` | string \| null | 构建产物标识；预览为候选摘要或 null |
| `content_status` | `previewed` \| `noop` \| `built` \| `failed` | 与部署分离 |
| `deploy_status` | `pending` \| `deploying` \| `published` \| `failed` \| `superseded` | 未发布时不得为 published |
| `commit_sha` | string \| null | 发布提交；预览/noop 可为 null |
| `run_url` | URL \| null | 运行链接；不含凭证 |
| `public_url` | URL \| null | 详情/公开链接；仅在安全时输出 |
| `errors` | Diagnostic[] | 稳定错误码与位置，不含自由文本/响应正文 |

状态转换：

```text
preview → previewed（无写入）
add/import/replace → noop（同内容）或 built → submitted → published
built/submitted → failed（构建或部署失败）
built → superseded（部署前发现远端已变化）
status/wait → published | failed | superseded | pending
```

## 6. RunStatusView

| 字段 | 类型 | 规则 |
|---|---|---|
| `run_id` | string | 运行标识 |
| `content_status` | `pending` \| `built` \| `noop` \| `failed` | 由 build job/step 派生 |
| `deploy_status` | `pending` \| `deploying` \| `published` \| `failed` \| `superseded` | 由 deploy job/step 派生 |
| `conclusion` | `success` \| `failure` \| `cancelled` \| `skipped` \| `pending` | 运行整体结论 |
| `run_url` | URL | 运行链接 |
| `reason` | 稳定错误码 \| null | 如 `E_SUPERSEDED`、`E_DEPLOY_FAILED` |

派生规则：build 失败 → `content_status=failed`；build 成功且 deploy 步骤跳过 → `superseded`；
deploy 成功 → `published`；deploy 失败 → `failed`；运行未结束 → `pending/deploying`。无法确定时
不得报告 published。

## 7. Diagnostic 与 Conflict

| 字段 | 类型 | 规则 |
|---|---|---|
| `code` | string | 稳定错误码，如 `E_SCHEMA`、`E_PATH`、`E_SECRET`、`E_CONFLICT`、`E_SOURCE`、`E_BUILD`、`E_DEPLOY`、`E_TIMEOUT` |
| `path` | string \| null | 项目/来源相对路径；越界时为 null |
| `message` | string | 简短、已脱敏；不回显文件内容、token 或原始响应 |
| `expected` / `actual` | string \| null | 仅冲突使用；提交标识，不含凭证 |

冲突不修改当前内容；来源失败不删除现有版本；诊断只进入 stderr/JSON，不进入公开页面。
