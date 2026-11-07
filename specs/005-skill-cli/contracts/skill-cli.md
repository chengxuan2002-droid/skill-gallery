# Contract: Agent 命令维护（C-05）

**Feature**: US-005 | **Date**: 2026-11-08 | **Spec**: [../spec.md](../spec.md)

本契约定义命令行入口、结构化输出、退出码和不变量。命令复用 US-003 发布链与 US-004 手动维护规则，
不新增第二套校验器；实际构建/部署行为以 US-003 publish/workflow 契约为准。

## 1. 命令与选项

```text
node scripts/skill-cli.js preview <path> --meta <record.json> [--json]
node scripts/skill-cli.js add <path> --meta <record.json> [--publish] [--wait] [--json]
node scripts/skill-cli.js import --repo <owner/repo> --path <path> --ref <ref> --meta <record.json> [--publish] [--wait]
node scripts/skill-cli.js replace <slug> <path> --expected-revision <sha> [--meta <record.json>] [--publish] [--wait]
node scripts/skill-cli.js status --run <run-id> [--json]
```

- `preview` 只读：不写入工作区、不提交、不推送。
- `add`/`import` 要求 `--meta`；`replace` 缺省保留原记录，`--meta` 时整体替换。
- `--publish` 才允许远端写入；`--wait` 仅用于发布后的部署等待。
- `--repo`/`--path`/`--ref` 只接受结构化 GitHub 定位；不接受任意网页 URL。
- `--json` 为默认输出模式；stdout 只能有一行机器 JSON。

## 2. JSON 输出

```json
{
  "status": "ok",
  "slug": "example",
  "content_revision": "…",
  "content_status": "built",
  "deploy_status": "pending",
  "commit_sha": "…",
  "run_url": "https://github.com/owner/repo/actions/runs/123",
  "public_url": "https://chengxuan2002-droid.github.io/skill-gallery/#/skill/example",
  "errors": []
}
```

失败示例：

```json
{
  "status": "failed",
  "slug": "example",
  "content_revision": null,
  "content_status": "failed",
  "deploy_status": "pending",
  "commit_sha": null,
  "run_url": null,
  "public_url": null,
  "errors": [{ "code": "E_SCHEMA", "path": "catalog/example.json", "message": "缺少必填字段" }]
}
```

要求：字段封闭；`errors` 只含 `code`/`path`/`message`（冲突可含 `expected`/`actual`）；
不得包含 token、cookie、响应正文、环境变量、文件内容或原始异常。

## 3. 退出码

| 退出码 | 含义 |
|---|---|
| `0` | preview/noop/submitted/published 按要求完成（以 JSON 状态区分） |
| `2` | 参数、元数据或校验失败 |
| `3` | 未授权或无写权限 |
| `4` | 冲突（远端基线变化、expected revision 不匹配、非 fast-forward） |
| `5` | 来源读取失败（404/403/限流/超时/截断/不支持） |
| `6` | 构建或产物校验失败 |
| `7` | 部署失败 |
| `8` | `--wait` 等待超时（运行可能继续，保留 run URL） |

## 4. 发布不变量

- 预览不得写入工作区、提交、推送或部署。
- 发布只在隔离工作副本中基于远端基线暂存目标 Skill、`catalog/<slug>.json` 与跟踪字段；
  不使用 `git add .`、不 reset/clean 用户工作区、不 force push。
- 同内容重复提交返回 noop；不同内容同 slug 必须有显式 `replace` 与匹配的 `--expected-revision`。
- 单版本：替换按新清单重建，旧附件不进入新提交；不保留公开旧版入口。
- 提交成功或构建成功不得报告 published；只有观察到部署成功才输出 published。
- 失败保留当前内容与线上站点；清理临时副本，不产生部分写入。
- 未授权、来源失败、冲突、构建/部署失败均返回非零退出码且诊断脱敏。

## 5. 状态派生

`status`/`--wait` 以运行与 job 状态派生：

- build 失败 → `content_status=failed`；
- build 成功且 deploy 步骤跳过 → `deploy_status=superseded`；
- deploy 成功 → `published`；deploy 失败 → `failed`；运行未结束 → `pending`；
- 无法确定时返回 `pending`/`failed`，不得猜测为 published。

若未来工作流增加新的跳过原因，必须先更新本契约与测试，避免把其他情况误判为 superseded。

## 6. 与现有契约的关系

- 产物校验、目标判定、状态模型与摘要沿用
  [US-003 publish 契约](../../003-validate-build-publish/contracts/publish.md) 与
  [workflow 契约](../../003-validate-build-publish/contracts/workflow.md)。
- 日志/摘要不得进入访客页面；公开链接只在安全 URL 时输出。
- 本契约不改变部署权限、触发范围、并发或 Pages 设置。

## 7. README 要求

README MUST 包含：前提（Node/Git/gh）、认证与权限、预览、发布、替换、来源导入、状态查询、
`--wait` 与超时、退出码与排错；示例使用 `YOUR_*_HERE`，未实现能力标“规划”，不写真实凭证或
未验证命令。
