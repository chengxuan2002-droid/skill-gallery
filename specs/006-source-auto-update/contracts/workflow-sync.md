# Contract: 同步与同次发布工作流（C-07 扩展）

**Feature**: US-006 | **Date**: 2026-11-12 | **Spec**: [../spec.md](../spec.md)

本契约扩展 [US-003 workflow 契约](../../003-validate-build-publish/contracts/workflow.md)：
在同一个 `maintain.yml` 运行中增加 `sync` job，再把批次提交交给既有 `build`/`deploy`。
不新建第二条发布 workflow，不用 `workflow_run` 或 bot push 隐式衔接。

## 1. 触发

| 事件 | 条件 | 行为 |
|---|---|---|
| `push` | 默认分支 `main` | 不运行来源检查；按当前提交 build/deploy |
| `schedule` | UTC `17 19 * * *`（每日 03:17 Asia/Shanghai） | 运行 sync；有变化才 build/deploy |
| `workflow_dispatch` | 手动；`sync`（boolean，默认 false）、`slug`（可选 string） | `sync=true` 检查来源；默认仅重发当前提交 |

- 计划任务在默认分支最新提交上运行；平台延迟、跳过或停用不承诺准点 SLA。
- 手动输入只允许普通值（slug/sync），不传递文件内容、token 或任意 URL。
- 不在本工作流监听 `pull_request`、`pull_request_target`、`workflow_run` 或 fork 来源。

## 2. Job 图

```text
sync（仅 schedule/manual sync=true）
  └─ build（sync 跳过或 changed=true 时运行）
       └─ deploy（build 成功且目标未过期）
```

- `sync` 成功但 `changed=false`：跳过 build/deploy，不制造空提交或空部署。
- `sync` 被跳过（push 或 manual `sync=false`）：build/deploy 按当前触发提交运行。
- `sync` 全局失败：不 build/deploy；逐来源失败由报告表达，不阻断其他有效来源的候选。
- `build` checkout 目标为 `needs.sync.outputs.commit_sha || github.sha`；`deploy` checkout 和
  freshness 检查使用 build 输出的 target SHA，确保同一运行发布同一快照。
- build/deploy 的 Step Summary 使用 target SHA 与 `commit_status`；不得用 `github.sha`
  代替同步提交。

## 3. 权限与凭证

| Job | `permissions` | 说明 |
|---|---|---|
| `sync` | `contents: write` | 只用于读取来源、提交批次、非 force 推送 |
| `build` | `contents: read` | 校验、构建、上传 Pages artifact |
| `deploy` | `contents: read`、`pages: write`、`id-token: write` | 部署；无仓库写权限 |

- 工作流默认 `permissions: contents: read`；不得使用 `write-all`。
- 所有 checkout 保持 `persist-credentials: false`。
- `sync` 的 token 只在必要的 `gh auth setup-git`/来源读取步骤以受限 `GH_TOKEN` 提供；
  不使用 PAT、自定义 secret 或把 token 写入仓库、命令行日志、报告或摘要。
- `build`/`deploy` 不获得 `contents: write`，不参考 token。
- 安全测试必须显式断言：仅 `sync` 可写、`GH_TOKEN` 只出现在 sync 步骤、无 `secrets.*`/PAT/
  `github.token` 泄漏到摘要或公开产物。该测试更新是 US-006 合同的一部分，不得以放宽其他 job
  权限换取通过。

## 4. Sync Job 步骤

1. Checkout，`persist-credentials: false`，`fetch-depth` 足以读取目标提交和批次提交。
2. 使用 `.node-version`、锁定 npm 和根锁安装依赖；不安装收录 Skill 的依赖。
3. 设置 git 提交身份（机器人/维护者固定值，不含个人凭证）。
4. 在受限步骤配置 `gh` 认证，运行 `node scripts/sync-skills.js --apply --push ...`。
5. 输出 `changed`、`commit_sha`、`commit_status` 和报告路径；token 只在该 job 的运行期内使用，
   不持久到仓库、报告或摘要；build/deploy 不获得写权限。
6. 无论成功/失败，写入脱敏 source sync 摘要；不把上游响应正文或内部异常写入摘要。
7. `sync` job `timeout-minutes: 30`；单来源超时/重试受来源读取器约束，总时限不突破 job 时限。

## 5. Build/Deploy 衔接

- build 的 `needs` 包含 `sync`；checkout `ref` 使用 sync 提交或触发提交。
- build 必须重新执行现有 `npm run check`、`npm run security`、`npm run build`、
  `publish-check.js artifact`；不能因为来源检查通过就跳过全量构建。
- build 输出 `target_sha`（实际 checkout 的 40 位 SHA）；deploy 使用该 SHA 做
  `publish-check.js target`，不读取 `github.sha` 代替。
- build/deploy 的 `PUBLISH_COMMIT_STATUS` 使用 sync 输出的 `committed`，无提交使用
  `not_applicable`；状态分离，不把提交成功写成部署成功。
- 无变化时 build/deploy 不运行；需要重发当前快照时手动 `sync=false`，不依赖空提交。

## 6. 并发、失败与恢复

- 工作流级 `concurrency: maintain-${{ github.ref }}`、`cancel-in-progress: false`；部署 job
  继续使用 `pages` 组，不并行部署。
- sync 提交前读取远端基线；推送非 fast-forward 或被拒绝返回 conflict，不 force push、不降低分支
  保护。
- 部署失败保留上次正常站点，状态为 deploy_failed；按同一提交重跑不新建内容提交。
- 旧运行晚到时不覆盖新快照；deploy 的 freshness 检查为 superseded 时跳过部署并如实报告。
- 恢复使用受控 revert/restore 提交并重新构建发布；保持 slug、旧链接和 Git 历史。
- 来源单项失败、构建失败、部署失败和成功发布在摘要中分开显示；公开页面不展示内部日志。

## 7. 测试要求

- 工作流结构测试必须覆盖：`schedule` 存在且 cron 为 UTC 19:17；`workflow_dispatch` 输入；
  `sync` 仅在 schedule/manual sync 时运行；`sync` 是唯一 `contents: write` job；build/deploy
  仍为最小权限；所有 action 固定完整 SHA；checkout 不持久凭证。
- 同次运行测试必须断言 build checkout 使用 sync commit、deploy 使用 build target SHA，
  且不存在第二条发布 workflow/`workflow_run` 链。
- 安全测试必须断言 token 只出现在 sync 步骤、无 PAT/自定义 secret、摘要不含敏感上下文。
- 真实调度/同次发布用受控 POC-002/003 验证；不把本地 YAML 静态检查当作生产调度通过。
