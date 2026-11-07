# Phase 1 Data Model: US-004 管理员手动维护

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本故事不新增持久化数据库或内容 schema。下列模型描述手动维护操作、站内记录、入口与结果，
供 README、测试和 validation 共用；现有 `catalog`、搜索索引、详情 JSON、原件与 ZIP 的
`schemaVersion=1` 契约不变。

## 1. ManualMaintenanceAction

管理员通过 GitHub 后台执行的一次手动操作。

| 字段 | 类型 | 规则 |
|---|---|---|
| `action` | `add` \| `update_metadata` \| `replace` \| `remove` | 新增、仅改站内信息、显式替换、下架 |
| `slug` | string | 既有或新增的站内稳定标识；`^[a-z0-9]+(?:-[a-z0-9]+)*$`，≤64 字符 |
| `files` | path[] | 单文件或目录型原件相对路径；必须位于 `skills/<slug>` 范围 |
| `record` | ContentRecord \| null | 新增/元数据修改/替换时的站内记录；下架时为 null |
| `actor` | string | GitHub 账户或授权 Agent 标识（不保存 token） |
| `commit_ref` | string | 提交标识；用于恢复与运行定位 |

状态转换：

```text
add → validated → committed → built → published
update_metadata → validated → committed → built → published
replace → validated → committed → built → published（同一 slug 单版本）
remove → validated → committed → built → published（条目从索引/详情/下载消失）
任一阶段失败 → failed（保留当前有效内容与线上站点）
```

## 2. ContentRecord

现有 `catalog/<slug>.json` 的只读视图；手动维护不得新增未知字段。

| 字段 | 类型 | 规则 |
|---|---|---|
| `schemaVersion` | 1 | 固定 |
| `slug` | string | 必填；稳定身份；不因维护改名 |
| `display_name` | string | 必填；非空 |
| `description` | string | 必填；非空 |
| `content_path` | string | 必填；`skills/<slug>.md` 或 `skills/<slug>/SKILL.md` |
| `tags` / `platforms` | string[] | 可选；缺省为空数组 |
| `allowed_dot_paths` | string[] | 可选；受现有点路径准入规则约束 |
| `author` / `homepage_url` / `repository_url` / `declared_version` | string \| null | 可选；URL 必须无凭证的 http/https |
| `usage` / `notes` / `license` / `source_type` | string \| null | 可选；不进入原件 |
| `created_at` / `updated_at` | YYYY-MM-DD \| null | 可选；合法日历日期 |
| `source_tracking` | object \| null | 可选；provider/repository/path/ref_policy/ref/enabled 等；不触发自动检查 |

校验规则：未知顶层字段拒绝；缺必填字段返回 `E_SCHEMA`；路径越界返回 `E_PATH`；主文档缺失返回
`E_MAIN_MISSING`；疑似凭证返回 `E_SECRET`；文件数量/大小超限拒绝。诊断只报告路径、字段和规则。

## 3. AdminEntry

站点页脚的低权重管理入口。

| 字段 | 类型 | 规则 |
|---|---|---|
| `label` | string | 固定“管理”或等价短文本 |
| `href` | string | 受信任仓库后台地址；无凭证、无自定义查询参数 |
| `target` / `rel` | string | 新窗口打开；`rel="noopener"` |
| `presentation` | `footer-link` | 低权重外链，不是主操作按钮 |

不变量：不出现站内登录表单、文件输入、上传按钮或隐藏授权路径；入口不改变访客只读能力。

## 4. MaintenanceResult

一次手动维护运行的可公开结果；字段复用 US-003 RunStatus，不新增状态枚举。

| 字段 | 类型 | 规则 |
|---|---|---|
| `action` | ManualMaintenanceAction.action | 本次操作类型 |
| `target_sha` | string | 40 位提交标识 |
| `commit_status` | `not_applicable` \| `committed` \| `failed` | 提交状态 |
| `content_revision` | string \| null | 构建产物内容标识 |
| `content_status` | `pending` \| `built` \| `noop` \| `failed` | 校验/构建状态 |
| `deploy_status` | `pending` \| `deploying` \| `published` \| `failed` \| `superseded` | 部署状态 |
| `reason` | 稳定错误码 \| null | 如 `E_SCHEMA`、`E_PATH`、`E_MAIN_MISSING`、`E_SECRET` |
| `run_url` | URL \| null | 运行记录链接；不含凭证 |

## 5. RecoveryRecord

| 字段 | 类型 | 规则 |
|---|---|---|
| `recovery_sha` | string | 受控历史恢复提交的 40 位标识 |
| `restored_slug` | string[] | 受影响的既有 slug；不得改名 |
| `published_revision` | string \| null | 恢复后重新构建的内容标识 |
| `status` | `prepared` \| `published` \| `failed` | 与正常发布共用 RunStatus 语义 |

恢复必须重新构建并发布，不直接改写线上快照；不强制 push，不清除 Git 历史。
