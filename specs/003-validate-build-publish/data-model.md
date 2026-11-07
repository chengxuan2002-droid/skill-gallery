# Phase 1 Data Model: US-003 校验、构建与原地址发布流水线

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本故事不新增持久化数据库或内容 schema；下列模型描述发布运行、构建产物、部署目标与诊断的
逻辑结构，供 `scripts/lib/publish.js`、`maintain.yml`、测试和契约共用。现有
`catalog`、搜索索引、详情 JSON、原件与 ZIP 的 `schemaVersion=1` 契约不变。

## 1. RunStatus

一次发布运行的可公开状态。字段封闭，只允许下列键；不得写入凭证、原始响应或未脱敏异常。

| 字段 | 类型 | 规则 |
|---|---|---|
| `run_id` | string | GitHub 运行标识；非空 |
| `trigger` | `push` \| `workflow_dispatch` \| `schedule` | 本轮实现前两者；`schedule` 留 US-006 |
| `target_sha` | string | 40 位小写十六进制目标提交 |
| `content_revision` | string \| null | 构建产物内容标识；构建前为 null |
| `content_status` | `pending` \| `built` \| `noop` \| `failed` | 内容校验/构建状态，与部署分开 |
| `deploy_status` | `pending` \| `deploying` \| `published` \| `failed` \| `superseded` | 部署状态 |
| `reason` | string \| null | 稳定错误码（如 `E_ARTIFACT_EXTRA_FILE`），不含自由文本详情 |
| `run_url` | string \| null | GitHub 运行链接；不包含凭证 |

状态转换：

```text
pending → built → deploying → published
pending → failed
built → superseded（部署前发现远端 HEAD 已变化）
deploying → failed（部署失败或等待超时）
```

`content_status` 与 `deploy_status` 必须能同时表达“已构建/已提交但部署失败”，不得合并为单一成功/失败。

## 2. BuildArtifact

`dist/` 内的一个公开静态文件，来源为现有构建清单 `manifest.artifacts`。

| 字段 | 类型 | 规则 |
|---|---|---|
| `path` | string | 项目相对 POSIX 路径；无绝对路径、`..`、反斜杠、控制字符、空段 |
| `size` | integer | 原始字节数，非负 |
| `sha256` | string | 64 位小写十六进制 |
| `kind` | `html` \| `asset` \| `index` \| `detail` \| `raw` \| `download` \| `media` \| `manifest` | 由路径推导，仅用于诊断 |

允许路径前缀：`index.html`、`.nojekyll`、`assets/`、`details/`、`downloads/`、`skills/`、`media/`；
`manifest.json` 只作为清单自身，不进入 `artifacts` 列表。实际文件集合必须与 `manifest.artifacts`
双向完全一致；`manifest.skills` 只作内容摘要，不参与文件集合判断。

## 3. Manifest

现有 `dist/manifest.json` 的只读视图。

| 字段 | 类型 | 规则 |
|---|---|---|
| `schemaVersion` | 1 | 必须为 1 |
| `contentRevision` | string | 与 `assets/search-index.json`、各 `details/<slug>.json` 一致 |
| `skills` | object[] | 现有构建摘要；不新增字段 |
| `artifacts` | BuildArtifact[] | 按 `path` 排序；不包含 `manifest.json` |

验证规则：hash/大小一致、无重复路径、无符号链接/非普通文件、无额外文件、无 `..` 越界。

## 4. DeployTarget

| 字段 | 类型 | 规则 |
|---|---|---|
| `target_sha` | string | 本次要部署的提交；默认 `github.sha` |
| `remote_head` | string | 部署前从默认分支读取的远端 HEAD |
| `decision` | `current` \| `superseded` | 两者相等为 current，否则 superseded |
| `checked_at` | string \| null | 可选 ISO 8601；仅在运行记录/摘要中使用 |

规则：两个 SHA 都必须是 40 位小写十六进制；无法读取远端 HEAD 时按失败关闭，不猜测为 current。

## 5. VerificationDiagnostic

| 字段 | 类型 | 规则 |
|---|---|---|
| `code` | string | 稳定错误码，如 `E_ARTIFACT_EXTRA_FILE`、`E_ARTIFACT_HASH`、`E_SECRET` |
| `path` | string \| null | 项目相对路径；越界/非法输入时可为 null |
| `message` | string | 简短、已脱敏；不回显文件内容、token 或原始异常 |

诊断只用于运行日志/摘要；公开页面不展示。

## 6. PermissionContext

| 字段 | 值 | 允许的动作 |
|---|---|---|
| `visitor` | 未登录访客 | 只读公开站点 |
| `unauthorized` | 无仓库写权限 | 读取；写入/触发部署必须失败且无副作用 |
| `authorized` | 管理员或授权 Agent | 按同一校验规则提交/触发/部署 |
| `untrusted_source` | fork PR、外部来源 | 不获得写权限、不部署、不读取凭证 |

## 7. RecoveryRecord

| 字段 | 类型 | 规则 |
|---|---|---|
| `recovery_sha` | string | 受控历史恢复提交的 40 位 SHA |
| `restored_slug` | string[] | 受影响的既有 slug；不得改名 |
| `published_revision` | string \| null | 恢复后重新构建的内容标识 |
| `status` | `prepared` \| `published` \| `failed` | 与正常发布共用 RunStatus 语义 |

恢复必须重新构建并发布，不直接改写线上快照；不强制 push，不清除 Git 历史。
