# US-005 状态查询与等待验收（T016）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 用固定运行/job 状态验证 `statusOutcome` 与 `waitForRun` 的派生、退出码和超时语义；
不访问 GitHub、不使用凭证，不查询真实 POC 运行。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 方法

向 `scripts/lib/skill-cli/status.js` 注入固定运行对象：

- build/deploy job 组合：pending、published、superseded、build failed、deploy failed；
- `waitForRun` 注入 reader 与假时钟：先 pending 后 published 的序列，以及始终 pending 的超时序列；
- 检查 `exitCodeFor` 退出码；不调用 `gh run view`，不读取 Step Summary。

## 2. 结果

| 运行状态 | `content_status` | `deploy_status` | 错误码 | 退出码 |
|---|---|---|---|---|
| 进行中（pending） | pending | pending | — | 0 |
| 成功发布 | built | published | — | 0 |
| 部署过期（deploy 步骤 skipped） | built | superseded | `E_SUPERSEDED` | 4 |
| 构建失败 | failed | pending | `E_BUILD` | 6 |
| 部署失败 | built | failed | `E_DEPLOY` | 7 |

等待场景：

| 场景 | 结果 |
|---|---|
| pending → published | `status=published`、`timeout=false`，停止轮询 |
| 始终 pending | `status=pending`、`timeout=true`、`E_TIMEOUT`、退出码 `8` |
| 超时/失败/过期 | 均不输出 `published`；保留 `run_url`（固定对象中的运行链接） |

## 3. 未运行与限制

- 未查询真实 POC-002 运行或 `gh run view`；默认读取器字段（`status/conclusion/jobs/headSha/url`）
  仍需在 T021 或受控环境验证。
- 状态由 job/step 结论派生，不读取 Step Summary；若未来工作流增加新的跳过原因，需先更新契约。
- `--wait` 只有找到对应提交的运行时才轮询；本地裸远端或 gh 不可用会保留 submitted/pending。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
