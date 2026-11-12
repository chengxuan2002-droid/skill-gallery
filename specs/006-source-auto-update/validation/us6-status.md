# US-006 状态、重跑与恢复验收（部分）

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T018–T020；运行报告、提交/内容/部署状态分离、同提交重跑与受控恢复。

## 1. 自动测试

```bash
node --test tests/unit/source-sync-report.test.js
node --test tests/unit/source-sync-state.test.js
node --test tests/unit/publish-status.test.js
node --test tests/unit/publish-summary.test.js
```

结果：相关测试全部通过。报告字段封闭，逐来源状态只允许
`unchanged/candidate/updated/failed/conflict/policy_blocked/unsupported`；`updated` 必须有提交 SHA，
`unchanged` 不伪造提交；提交、内容、部署状态分开；摘要和错误只保留稳定码与安全位置。

## 2. POC 状态观察

| 运行 | commit_status | content_status | deploy_status | 观察 |
|---|---|---|---|---|
| [43208732789](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208732789) | committed | built | published | 基线提交同次发布 |
| [43208983544](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208983544) | committed | built | published | v2 替换同次发布 |
| [43209635536](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43209635536) | not_applicable | noop | pending | 无变化不部署 |

Step Summary 与报告使用同一 `target_sha`/`commit_status`，没有把提交成功写成“已发布”。

## 3. 未运行

- **真实部署失败注入**：本 POC 未修改消费端 workflow 制造部署失败；没有实际观察“提交成功、部署失败、
  旧站保留”。US-003 已有受控部署失败/旧站保留证据，但不能替代 US-006 自动提交后的同链路验证。
- **同提交重跑**：未在部署失败后执行；无变化 dispatch 已证明不新增提交，但不等同部署失败重跑。
- **受控 `git revert` 恢复**：未执行；POC 保留源 v1/v2 与提交历史，可在后续授权下演练。

上述缺口已在 [us6-final-review.md](us6-final-review.md) 与任务状态中保留，不宣称 T020 完整通过。
