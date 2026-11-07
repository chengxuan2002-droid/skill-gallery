# Step Summary RunStatus 补齐验收（T033）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在 `.github/workflows/maintain.yml` 的 build/deploy Step Summary 中补齐完整 RunStatus 字段；
不改变触发、权限、部署顺序或 Pages 配置。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`；未在 GitHub runner 执行。

## 1. 实现

- `scripts/lib/publish-summary.js`：从 `PUBLISH_*` 环境变量构造 RunStatus，复用
  `scripts/lib/publish.js` 的 `createRunStatus` 与 `renderSummary`；写入
  `$GITHUB_STEP_SUMMARY`，也支持本地 stdout。
- `scripts/publish-summary.js`：CI 入口；环境缺失或状态非法时输出稳定错误码并退出 `2`。
- `.github/workflows/maintain.yml`：
  - build job 输出 `content_revision`，在构建后写入 build 摘要；
  - build 摘要使用 `steps.build.outcome` 区分 `built`/`failed`，部署状态为 `pending`；
  - deploy 摘要使用 `steps.freshness.outputs.decision`、`steps.deployment.outcome` 和
    `needs.build.outputs.content_revision`，区分 `published`/`failed`/`superseded`；
  - 两个摘要步骤均使用 `if: always()`，并保留可选的安全页面地址。

摘要包含：运行标识/链接、触发方式、目标 SHA、`commit_status`、`content_revision`、
`content_status`、`deploy_status`、`started_at`/`finished_at`（未知为 `unknown`，由 `run_url`
回退）和失败码或 `superseded` 说明。

## 2. 命令与结果

| 命令 | 退出码 | 结果 |
|---|---|---|
| `node --test tests/unit/publish-summary.test.js tests/integration/publish-summary-workflow.test.js` | 0 | 8 项通过、0 失败 |
| `npm test` | 0 | 196 项：194 通过、0 失败、2 跳过 |
| `npm run lint` | 0 | ESLint 无错误 |
| `npm run format:check` | 0 | Prettier 全部通过 |
| `npm run security` | 0 | secrets 240 文件、code 37 文件、deps 1 文件；findings 均为空 |

覆盖场景：build 成功/失败、build 后发布步骤失败、deploy `published`/`failed`/`superseded`、
页面地址安全过滤、额外环境变量不回显、摘要文件追加和工作流字段/顺序静态断言。

## 3. 未运行与限制

- 未在 GitHub Actions runner 实际执行；未观察远程运行摘要。
- 未执行真实 Pages 部署、environment 审批或受控仓库 POC-002。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验。
- 摘要中的 `started_at`/`finished_at` 保持 `null`，由 `run_url` 提供运行定位；没有编造时间。
