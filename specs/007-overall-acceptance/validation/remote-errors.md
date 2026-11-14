# 真实远程错误与限流观察

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: 补充真实 403 和 GitHub API 限流状态；不伪造远程结果，不消耗或滥用限额。
**方式**: 只读 `gh api`/HTTP 请求；未写生产内容，未执行收录 Skill 脚本。

## 1. 真实 403

```bash
gh api repos/octocat/Hello-World/actions/runners
```

结果：GitHub API 返回 HTTP `403`，消息为“需要 repository read permissions 或 repository runners
fine-grained permission”，`gh` 退出码 `1`。这是对公开示例仓库的只读请求，没有写入或副作用；用于
确认真实的 403 状态和稳定错误边界。

## 2. 限流状态

```bash
gh api rate_limit
```

结果：core 限额 `5000`、剩余 `4982`；search 限额 `30`、剩余 `30`。没有触发 429，也没有为了
测试而耗尽配额。

## 3. 部署侧真实失败

POC-002 的 `43420335014`（branch `poc-deploy-fail`）deploy job 在 `github-pages` environment
branch policy 下被拒绝：job 无步骤、状态为 failure，deployment status 由 `waiting` 变为 `failure`；
build 成功、旧站保留。该失败是真实的 environment 策略拒绝，不是伪造的 403 响应。

## 4. 未运行与限制

- 真实源同步 403/429 映射仍未在公开来源上触发：公开来源通常返回 200/404，私有来源可能隐藏为 404；
  为避免滥用限额，没有主动耗尽配额制造 429。
- `github-source.test.js` 的 `E_SOURCE_FORBIDDEN`/`E_SOURCE_RATE_LIMIT` 仍为注入测试；本轮真实 403
  证明 GitHub 会返回该状态，但不等于 source-sync 的 403 分支已远程端到端验证。
- 生产 environment 审批和生产部署失败注入仍未运行；POC 环境策略拒绝只作为受控证据。
