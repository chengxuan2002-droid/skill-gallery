# 生产 environment 审批与部署失败演练

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: 生产 `skill-gallery` 的 `github-pages` environment；验证 required reviewer 等待/审批和
部署失败/旧站保留/恢复。用户已明确授权临时修改生产设置并在完成后恢复。
**结论**: `通过（受控生产演练）`。环境审批真实等待并由 API 审批；一次真实部署失败保留旧站；
设置已恢复为 `main` branch policy、无 required reviewer；生产 contentRevision 始终为
`faa0f345...`。

## 1. 初始状态与备份

| 项 | 值 |
|---|---|
| 环境 | `github-pages`（id `19157477891`） |
| protection_rules | 仅 `branch_policy` |
| branch policy | 仅 `main`（原 id `56266788`） |
| reviewers | 无 |
| 备份 | 临时文件，未提交；记录原始规则 |

## 2. required reviewer 审批

| 步骤 | 结果 |
|---|---|
| 临时添加 reviewer | 用户 `chengxuan2002-droid`（id `236188531`），`prevent_self_review=false` |
| 触发 | `maintain.yml` `workflow_dispatch` `sync=false`，run [43587421323](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43587421323) |
| build | success |
| deploy | `waiting`；`pending_deployments` 返回 environment `19157477891`，当前用户可审批 |
| 审批 | `POST .../runs/43587421323/pending_deployments`，`state=approved` |
| 完成 | run success；build/deploy success；生产 revision 仍 `faa0f345...` |
| 恢复 | 删除 reviewer；protection_rules 回到仅 `branch_policy` |

这是真实的生产 environment 等待/审批路径，不是本地模拟。审批由当前授权的管理员账号执行。

## 3. 部署失败与旧站保留

为触发真实失败，临时把 `github-pages` 的 custom branch policy 改为只允许
`codex/us7-deploy-fail`；`main` 不在允许列表。

| 步骤 | 结果 |
|---|---|
| 临时策略 | 允许 `codex/us7-deploy-fail`，移除 `main` |
| 触发 | run [43588024409](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43588024409)（`main`，`sync=false`） |
| job | sync skipped、build success、deploy failure（environment branch policy 拒绝） |
| 旧站 | 首页 HTTP 200、1,623 字节；索引 revision 仍 `faa0f345...`、4 项 |
| 恢复策略 | 移除测试策略，重新添加 `main`（新 id `66689572`）；恢复 custom policy |
| 重跑 | run [43588215125](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43588215125)，sync skipped、build/deploy success |
| 最终状态 | custom branch policy 仅 `main`；无 required reviewer；生产 revision 仍 `faa0f345...` |

中间尝试 `43587652022`（无 custom policy）和 `43587833157`（protected branches policy）均未阻止
`main` 部署，未作为失败证据；最终用“只允许测试分支”的策略触发真实失败。两次成功运行也未改变生产
revision。

## 4. 最终状态

- `github-pages` 仅保留 `branch_policy`；custom branch policy 仅 `main`（最终 id `66689572`）；
  无 required reviewer。
- 临时测试分支 `codex/us7-deploy-fail`/`codex/us7-macos-check` 不存在于远程。
- 生产索引 revision 始终为 `faa0f345...`、4 项；首页 HTTP 200。

## 5. 边界

- 演练只修改 environment protection 设置，未修改源码、catalog 或生产内容；未 force push。
- 审批使用当前管理员 token；没有创建新 secret 或 PAT。
- 生产 environment 审批和部署失败注入已完成受控演练；CDN/缓存清理、真实 429 等仍未运行。
