# US-006 状态、重跑与恢复验收

**日期**: 2026-11-13（Asia/Shanghai）
**范围**: T018–T020；运行报告、提交/内容/部署状态分离、同提交重跑与受控恢复。

## 1. 自动测试

```bash
node --test tests/unit/source-sync-report.test.js
node --test tests/unit/source-sync-state.test.js
node --test tests/unit/publish-status.test.js
node --test tests/unit/publish-summary.test.js
node --test tests/integration/publish/publish-same-run.test.js
```

结果：相关测试全部通过。报告字段封闭，逐来源状态只允许
`unchanged/candidate/updated/failed/conflict/policy_blocked/unsupported`；`updated` 必须有提交 SHA，
`unchanged` 不伪造提交；提交、内容、部署状态分开；摘要和错误只保留稳定码与安全位置。

## 2. POC 部署失败与旧站保留

源 v5 修订 `4965bdae91c7...` 触发消费端同步；分支运行使用 `poc-deploy-fail`，其 `github-pages`
environment 不允许该分支部署：

- run：[43420335014](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420335014)
- 结果：`sync` success、`build` success、`deploy` failure（environment branch policy 拒绝）。
- 内容提交：`a542e872f2ba`；失败后线上 revision 仍为 `e489a35a...`，旧站保留。
- 没有把提交成功报告为已发布。

## 3. 同一提交重跑

main 手动 dispatch（`sync=false`）：

- run：[43420502326](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420502326)
- 结果：`sync` skipped、`build` success、`deploy` success。
- main HEAD 仍为 `a542e872f2ba`，没有新增内容提交；线上 revision 变为 `e52d42db...`。

该场景同时验证了 workflow 修复：`deploy` 使用
`if: always() && needs.build.result == 'success'`，避免 sync 被跳过时 build 成功但 deploy 被隐式跳过。
修复后的 push 运行 [43420037710](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420037710)
为 `sync skipped / build success / deploy success`。

## 4. 受控 revert 恢复

在消费端 main 执行 `git revert a542e872f2ba`（恢复提交 `8e93adaf924b`）并推送：

- run：[43420712186](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420712186)
- 结果：`sync` skipped、`build` success、`deploy` success。
- 线上 revision 回到 `e489a35a...`；`source-poc` slug 保持，digest 为 `329714b9...`；历史未被改写。

## 5. 状态观察

| 运行 | commit_status | content_status | deploy_status | 观察 |
|---|---|---|---|---|
| 43208732789 | committed | built | published | 基线提交同次发布 |
| 43208983544 | committed | built | published | v2 替换同次发布 |
| 43209635536 | not_applicable | noop | pending | 无变化不部署 |
| 43420335014 | committed | built | failed | 部署失败、旧站保留 |
| 43420502326 | not_applicable | built | published | 同一提交重跑成功 |
| 43420712186 | not_applicable | built | published | revert 恢复成功 |

## 6. 未运行

- 生产 `main` 的部署失败注入、environment 审批和发布后 MIME/缓存复验。
- 真实 403、限流等待、真实截断树和真实符号链接/子模块。
