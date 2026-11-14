# US-007 Demo-003：失败、冲突到恢复

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T011–T013；来源 404/限流/非法候选/许可/本地冲突/并发过期；构建/部署失败、同提交重跑、
受控 revert。
**复核方式**: 读取 `specs/003-validate-build-publish/validation/` 与
`specs/006-source-auto-update/validation/`，重新运行 49 项定向测试，并用 GitHub API 复核 POC 运行
job 和当前 POC manifest。未写生产内容，未执行收录 Skill 的脚本。
**结论**: `受控通过`。失败路径均失败关闭并保留当前版本；POC-002/003 的部署失败、旧站保留、
同提交重跑和受控 revert 有运行证据；生产 environment 审批和部署失败注入已于 2026-11-14 补验
（见 `production-environment.md`）。真实 source-sync 429 仍未触发。

复核命令（节选）：

```bash
node --test tests/unit/github-source.test.js tests/unit/source-sync-state.test.js \
  tests/unit/publish-status.test.js tests/integration/source-sync-check.test.js \
  tests/integration/source-sync-conflict.test.js tests/integration/untrusted-content.test.js \
  tests/integration/skill-cli-replace.test.js tests/integration/publish/publish-superseded.test.js
gh api repos/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420335014/jobs
gh api repos/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420502326/jobs
gh api repos/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43420712186/jobs
```

## 1. T011 失败与冲突矩阵

| 场景 | 证据/测试 | 结果 | 当前版本保留 |
|---|---|---|---|
| 来源 404 | POC-003 `missing-poc`：不存在的仓库；`github-source.test.js` 404 映射 | `failed`/`E_SOURCE_NOT_FOUND`；Release 404 映射为 `E_SOURCE_UNAVAILABLE` | 现有内容与远端基线不变 |
| 限流/403 | `source-sync-check.test.js` 注入 `E_SOURCE_RATE_LIMIT`；`github-source.test.js` 瞬态 502 重试 | 该来源 `failed`、其他来源继续；真实 403/429 未运行 | 当前内容与提交不变 |
| 截断/子模块/符号链接 | `github-source.test.js` 注入 `E_SOURCE_TRUNCATED`、`E_SOURCE_LINK`；POC 限制说明 | 失败关闭，不读取链接内容；真实远程对象未运行 | 当前内容不变 |
| 非法候选路径 | `source-sync-conflict.test.js` 的 `../evil.md` | `failed`/`E_PATH`，未写入目标原件 | 现有 slug/文件不变 |
| 许可缺失/变化 | `source-sync-conflict.test.js`；POC run `43374128999` | `policy_blocked`/`E_LICENSE_MISSING` 或 `E_LICENSE_CHANGED`；无新提交 | 旧附件和当前版本保留 |
| 本地修改冲突 | `source-sync-conflict.test.js` | `conflict`/`E_CONFLICT_LOCAL`；本地编辑内容保留 | 不覆盖本地修改 |
| 首次启用内容不同 | `source-sync-conflict.test.js` | `conflict`/`E_CONFLICT_BASELINE`，要求先建立基线 | 不写原件 |
| 并发/过期基线 | `source-sync-conflict.test.js` 远端基线前进；`skill-cli-replace.test.js` 过期 `--expected-revision`；`publish-superseded.test.js` | `E_CONFLICT` 或 publish `superseded`（退出码 4）；不 force push、不写目标 | 远端与当前提交保持 |
| 构建/部署失败 | `us3-recovery.md` 隔离演练；POC run `43420335014` | `content_status=built`、`deploy_status=failed`，旧 `dist`/旧站保留 | 旧产物字节与 SHA-256 不变 |
| 来源失败隔离 | `source-sync-check.test.js` 一个来源超时、另一个继续 | 失败来源不影响其他来源检查 | 成功来源仍可报告状态 |

对应 `us6-conflict.md` 与 `us6-check.md` 的结论：所有 `policy_blocked`/`conflict`/`failed` 分支在
测试和 POC 中均未写入目标原件，当前版本、当前站点和 Git 历史保持；诊断只输出稳定错误码和路径。

## 2. 定向测试结果

```text
tests 49
pass 49
fail 0
skipped 0
```

覆盖：404/Release 404、瞬态重试与限流注入、截断/链接/子模块拒绝、非法路径、许可缺失/变化、
本地修改冲突、首次基线冲突、远端基线前进、过期 expected revision、publish superseded、状态分离、
不可信内容清理、凭证/路径诊断脱敏。测试未执行收录 Skill 的脚本，也未访问生产仓库。

## 3. T012 部署失败、同提交重跑与受控 revert

`us6-status.md` 的 POC-002 运行；本次用 GitHub API 重新核对 job 结论：

| 场景 | run | job 复核 | 内容/站点结果 |
|---|---|---|---|
| 部署失败 | `43420335014` | sync success、build success、deploy failure | 内容提交 `a542e872f2ba`；线上保留旧 revision `e489a35a...`；状态为 committed/built/failed |
| 同一提交重跑 | `43420502326` | sync skipped、build success、deploy success | 无新内容提交；线上 revision 变为 `e52d42db...` |
| 受控 revert | `43420712186` | sync skipped、build success、deploy success | 恢复提交 `8e93adaf924b`；线上回到 `e489a35a...`；slug 与 digest `329714b9...` 保持，历史未改写 |

隔离演练（`us3-recovery.md`）补充了不依赖远程的同类语义：部署步骤退出码 `1` 时旧 `dist` 文件集合、
大小和 SHA-256 与失败前一致；同一目标提交重跑得到相同 `contentRevision` 且不新增内容提交；
伪造过期目标返回 `superseded`/退出码 `4`，不部署。POC run `43420335014` 的 workflow 总结论为
failure，job 级 deploy 失败不会被 build 成功掩盖。

复核时 POC 首页返回 HTTP 200（1,417 字节），`manifest.json` 的 `contentRevision` 为
`649d7bd2354ea684abbbdb4aa2e27dc8057cdc0a65a5da19c93e19c2670df797`。这是 T020 之后 POC schedule
run `43533694919` 按当前来源重新同步 v5 的结果，不代表 T020 历史 revision 被改写，也不形成第二版本。

## 4. 未运行与限制

- 真实 403 已观察（见 `remote-errors.md`）；真实 429 限流等待、真实截断树、真实子模块/符号链接、
  真实二进制下载逐字节对比未运行；由注入测试覆盖，不能写成远程通过。
- 生产 environment 审批和部署失败注入已于 2026-11-14 补验；MIME/缓存基础头已复核；CDN/强刷、
  真实浏览器刷新未运行。
- POC-002 使用精简 workflow，未在远程运行完整 `npm run check`/`npm run security`；本轮不把它
  当作生产发布或生产安全验收。
- 未伪造远程 403/限流结果；未删除 POC 仓库或改写其历史。

## 5. T013 状态

- Demo-003：`受控通过`（POC + 隔离 + 定向测试）。
- AC-010（失败与冲突）：`受控通过`；真实 403 已观察，真实 429 未触发。
- AC-011（状态与恢复）：`受控通过`；POC 部署失败/重跑/revert 与隔离演练有证据；生产 environment
  审批和部署失败注入已补验（`production-environment.md`）。
- AC-012（内容边界）：`受控通过`；HTML/URL/路径/脚本不执行与凭证脱敏测试通过，真实远程截断/
  子模块/符号链接未运行；T017 仍将复核安全边界，不把本轮状态当作生产安全验收。
