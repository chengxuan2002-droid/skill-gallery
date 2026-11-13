# US-006 调度与同次发布验收

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T021–T024；workflow 结构、权限、手动/计划同一路径、同次 build/deploy 与无变化跳过。

## 1. 工作流结构测试

```bash
node --test tests/integration/publish/publish-sync-workflow.test.js \
  tests/integration/publish/publish-workflow.test.js \
  tests/integration/publish/publish-same-run.test.js \
  tests/integration/publish/publish-security-workflow.test.js \
  tests/integration/publish/publish-summary-workflow.test.js
```

结果：全部通过。断言包括：

- `schedule` cron 为 UTC `17 19 * * *`；`workflow_dispatch` 提供 `sync`（boolean）与 `slug`（string）。
- `sync` 是唯一 `contents: write` job；build 只读；deploy 仅 `pages: write`/`id-token: write`。
- 所有 checkout `persist-credentials: false`；`GH_TOKEN` 只出现在 sync 的两个步骤。
- build checkout `needs.sync.outputs.commit_sha || github.sha`；deploy checkout 与 freshness 使用 build 的
  `target_sha`；摘要使用同一 `commit_status`。
- 没有 `workflow_run`、`pull_request_target`、`secrets.*` 或 PAT；所有 action 使用完整 SHA。

## 2. POC 同次运行

消费端 POC-002 使用精简 `maintain.yml`（保留 sync/build/deploy 与摘要，未运行完整 check/security）：

| 场景 | 运行 | 结果 |
|---|---|---|
| 首次基线（源 v1） | [43208732789](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208732789) | sync/build/deploy 均 success；提交 `0c68fed4c008` |
| 源 v2 更新 | [43208983544](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208983544) | sync/build/deploy 均 success；提交 `7b439a18f6d3` |
| 无变化 | [43209635536](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43209635536) | sync success；build/deploy skipped；无新提交 |
| push 基线（修复前） | [43208462776](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208462776) | build success；deploy skipped；暴露 sync 跳过时 deploy 被隐式跳过 |
| push 修复后 | [43420037710](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420037710) | sync skipped；build/deploy success |

`sync` job 的 Step Summary 显示来源状态、提交状态、内容状态和部署状态；公开页面只显示内容结果，
不显示 token、上游响应正文或内部异常。

## 3. 调度说明

- `17 19 * * *` 是 UTC；对应每日 03:17 Asia/Shanghai。平台延迟、跳过或停用不承诺准点 SLA。
- 手动 `sync=false` 只按当前提交重发；该路径已在 T020 的
  [43420502326](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420502326)
  执行，build/deploy success 且未新增内容提交。
- `deploy` 使用 `if: always() && needs.build.result == 'success'`；workflow 测试覆盖 build 成功但 sync
  被跳过时仍运行 deploy。
- 生产 `main` 调度已于 2026-11-13 启用（PR #6 合并 `27c6b36dcab8f654f0279a2a822f1bb6042f765e`）；
  push run [43421560371](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43421560371)
  为 sync skipped、build/deploy success；手动 sync run
  [43421951464](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43421951464)
  为 sync success、无变化、build/deploy skipped。

## 4. 未运行

- 2026-11-14 首次 03:17 Asia/Shanghai 窗口轮询至 05:10 CST，未出现 `Maintain site` 的 schedule run；
  同期只有 `Site availability` 的 schedule 运行。不能声称已定时执行，下一窗口为 2026-11-15 03:17。
- environment 审批和发布后 MIME/缓存复验仍未运行。
- 真实部署失败后的同提交重跑与受控 revert 已见 [us6-status.md](us6-status.md)；本文件不重复其运行记录。
