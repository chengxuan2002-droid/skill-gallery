# US-005 受控 POC 发布验收（T021）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 在受控临时公开仓库 POC-002 用 `skill-cli` 执行真实新增、替换与状态查询，观察
`maintain.yml` 部署结果；生产 Pages 未切换。
**环境**: 操作端 Windows 11、Node `v22.21.0`/npm `10.9.4`；受控运行在 GitHub runner
`ubuntu-24.04`、Node 26.3.0（由 `.node-version` 决定）。

## 1. 受控仓库

| 项 | 值 |
|---|---|
| 仓库 | `chengxuan2002-droid/skill-gallery-poc-20261107`（公开，`main`） |
| Pages source | `build_type=workflow` |
| 起始 HEAD | `e05dd3e4a2ad7e7a7a237b9554105f15ae8556e4` |
| 工作流 | POC 精简版 `maintain.yml`（保留构建/artifact/部署/摘要；未运行完整 check/security） |

候选：`skills/cli-poc-us5.md` + `catalog/cli-poc-us5.json`，通过 CLI 在临时 clone 中发布。

## 2. 新增

| 检查 | 结果 |
|---|---|
| 命令 | `node scripts/skill-cli.js add <candidate> --meta <meta> --publish` |
| 退出码 | 0 |
| 输出 | `status=submitted`、`commit_sha=92da16bf25867583d323179cb1a52a4d52ea682b`、`deploy_status=pending` |
| 运行 | [42395342747](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42395342747)（push） |
| 运行结论 | build/deploy 均成功 |
| `status --run` | 退出码 0、`status=published`、`content_status=built`、`deploy_status=published`、`run_url` 与提交正确 |
| 站点 | `contentRevision=991bca8b36102889e003ae30f5fd195a253a45b540bd5e34423d421c24d7d59c`，包含 `cli-poc-us5` |

## 3. 替换

| 检查 | 结果 |
|---|---|
| 命令 | `node scripts/skill-cli.js replace cli-poc-us5 <candidate> --expected-revision 92da16b… --publish --wait` |
| 退出码 | 0 |
| 输出 | `status=submitted`、`commit_sha=5e5b75cada5c78d9f0a278662e84c1f68a58a485`、`deploy_status=pending` |
| 运行 | [42395444891](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42395444891)（push） |
| 运行结论 | build/deploy 均成功 |
| `status --run` | 退出码 0、`status=published`、`deploy_status=published` |
| 站点 | `contentRevision=c2d2b3228a6ee7343cdfa47b1ad286c0d091dfd6236995478336482ba0b6a4e0` |
| 详情 | `details/cli-poc-us5.json` 的 revision 与索引一致，正文包含替换标记；索引中只有 1 个 `cli-poc-us5` |

## 4. 偏差与状态查询失败路径

- `--wait` 在替换后立即查询运行未找到（push 后 GitHub 尚未列出运行），按 README 记录返回
  `submitted/pending`；随后手动 `status --run` 得到 `published`。这符合当前“只有找到运行才轮询”的
  文档，但不是“等待必达发布”，后续可增加运行发现重试。
- 对不存在的运行 `status --run 99999999999`：退出码 `5`、`E_SOURCE`，不误报状态。
- POC 仓库保留新增/替换提交与 `cli-poc-us5` 内容；未删除临时仓库。

## 5. 未运行与限制

- 未用 `import` 读取真实 GitHub 来源（默认 `gh api` 读取器仍未远程验证）。
- 未验证 environment 审批、分支保护、并发过期或部署失败重跑（US-003 已有独立证据）。
- 未验证浏览器详情/分享/下载交互、MIME/缓存或移动端。
- 生产 Pages 仍为 `legacy`，未切换；本记录不是生产发布验收。
