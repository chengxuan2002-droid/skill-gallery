# US4 同一运行显式发布验收（T025）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在用户授权的受控临时公开仓库 POC-002 模拟一次机器式内容提交，观察同一次运行内
`build`→`deploy` 显式衔接；再对同一提交重发，确认重复部署同一快照且不产生新的内容提交。
未修改生产仓库、生产 Pages 或分支保护。
**环境**: 操作端 Windows 11；Node `v22.21.0`、npm `10.9.4`；受控运行在 GitHub runner
`ubuntu-24.04`、Node `26.3.0`（由仓库 `.node-version` 决定）。

## 1. 受控仓库与前置

| 项 | 值 |
|---|---|
| 仓库 | `chengxuan2002-droid/skill-gallery-poc-20261107`（公开，`main`） |
| Pages source | `build_type=workflow` |
| 工作流 | `.github/workflows/maintain.yml`（POC 精简版：保留构建、artifact 校验、上传、目标判定、摘要；移除 `setup:security`、`npm run check`、`npm run security`） |
| 变更前 HEAD | `8c86a3972580cb8053a4843d17fd17f4d32a909e` |
| 变更前站点 `contentRevision` | `82afef70fa4bedfe243723263a11c75a900d433f8e35e7374f2ae747ae0d23b8` |

机器式提交由操作端在临时 clone 中生成，只修改 `catalog/code-review-assistant.json` 的 `notes`，
不触碰生产内容或 `skills/` 原件；该提交仅存在于临时仓库。

## 2. 内容提交与同次运行发布

| 检查 | 结果 |
|---|---|
| 新提交 | `d27381534911c1e347d7431bf7bb40a9a5ac523a`（`test: simulate machine content update`） |
| 触发方式 | `push` 到 `main`，未额外 dispatch |
| 运行 | [42377824309](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42377824309) |
| 目标提交 | 与推送提交一致：`d27381534911c1e347d7431bf7bb40a9a5ac523a` |
| Job 结果 | `build` success；`deploy` success（同一次运行） |
| 部署后站点 `contentRevision` | `2ceb63c19812d6953956cb9a4af001f587d0ad82cb3df7450bea8037d617de82`（与变更前不同） |

该运行由 push 触发后在同一运行内完成构建与部署，未等待另一条工作流或另一次 push。

## 3. 同一提交重发

| 检查 | 结果 |
|---|---|
| 触发方式 | `workflow_dispatch`（`main`，无参数） |
| 运行 | [42377905399](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42377905399) |
| 目标提交 | 与上一次运行相同：`d27381534911c1e347d7431bf7bb40a9a5ac523a` |
| Job 结果 | `build` success；`deploy` success |
| 重发后站点 `contentRevision` | 仍为 `2ceb63c19812d6953956cb9a4af001f587d0ad82cb3df7450bea8037d617de82` |
| 仓库 HEAD 重发前/后 | `d27381534911c1e347d7431bf7bb40a9a5ac523a` / 同一值，未新增内容提交 |
| 站点技能数 | 4，未变化 |

重复部署保持同一快照和同一 `contentRevision`；自动化本身没有创建空内容提交。

## 4. noop 语义

POC 精简 workflow 的摘要固定使用 `content_status=built`，未实现内容是否变化的自动判定；
因此本次远程记录只能证明“同一提交重发同一快照、不新增内容提交”，不能把重发报告为 `noop`。
`noop` 状态模型与摘要由 T024 的本地单元测试覆盖（`tests/unit/publish-noop.test.js`）；
US-006 接入来源检查后才有机器化的 noop 判定。

## 5. 未运行与限制

- POC 使用精简 workflow，未在远程运行 `npm run check`、`npm run security` 或完整发布门禁。
- 未验证生产仓库的 Pages 切换、environment 审批、分支保护或线上缓存/MIME。
- 未构造真实机器人身份或 PAT；机器式提交由操作端在临时仓库生成。
- 临时仓库保留本次测试提交（`d273815`）；如需清理，应单独确认后执行，不强制改写历史。
- 本记录不表示 US-006 的来源检查、Q-004 调度或生产自动发布已完成。
