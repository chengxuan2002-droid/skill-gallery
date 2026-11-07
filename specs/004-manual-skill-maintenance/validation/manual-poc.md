# US-004 受控仓库手动维护验收（T016）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 在用户授权的受控临时公开仓库 POC-002 以 GitHub 推送等价手动提交，依次执行新增、非法
批次、清理、替换和下架，观察 `maintain.yml` 的构建/部署结果与站点内容。生产 Pages 未切换。
**环境**: 操作端 Windows 11、Node `v22.21.0`/npm `10.9.4`；受控运行在 GitHub runner
`ubuntu-24.04`、Node `26.3.0`（由 `.node-version` 决定）。

## 1. 受控仓库与基线

| 项 | 值 |
|---|---|
| 仓库 | `chengxuan2002-droid/skill-gallery-poc-20261107`（公开，`main`） |
| Pages source | `build_type=workflow` |
| 工作流 | POC 精简版 `maintain.yml`：保留构建、artifact 校验、上传、目标判定、摘要；未运行完整 `check`/`security` |
| 起始 HEAD | `d27381534911c1e347d7431bf7bb40a9a5ac523a` |
| 起始站点 `contentRevision` | `2ceb63c19812d6953956cb9a4af001f587d0ad82cb3df7450bea8037d617de82`（4 个 slug） |

提交由临时 clone 生成并推送到 `main`；等价于管理员在 GitHub 后台提交文件与 `catalog` 记录。

## 2. 新增（合法）

| 检查 | 结果 |
|---|---|
| 提交 | `3d843415908f5345bc85ea32cb7a12d99eb597e9`（`skills/manual-poc.md` + `catalog/manual-poc.json`） |
| 运行 | [42389206664](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42389206664)（push） |
| 状态 | `build` success；`deploy` success |
| 站点 `contentRevision` | `994e86ecba4eba7d344f1eec37af62cd22a3f0e85e77477606c59c426532c572` |
| 索引 | 5 个 slug，包含 `manual-poc` |
| 详情 | `details/manual-poc.json` 可访问，`contentRevision` 与索引一致 |

## 3. 非法批次（缺必填字段）

| 检查 | 结果 |
|---|---|
| 提交 | `6e1ecb4c13f451b13fe17a20454b634775242f65`（新增 `manual-bad`，记录缺 `display_name`） |
| 运行 | [42389308073](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42389308073)（push） |
| 状态 | `build` failure；`deploy` skipped；运行整体 failure |
| 站点 `contentRevision` | 仍为 `994e86ecba…c572`，无 `manual-bad` |
| 详情探测 | `details/manual-bad.json` 返回 `404` |
| 结论 | 非法批次整批阻止，未上传/部署，旧站保持 |

## 4. 清理与替换

| 步骤 | 提交 | 运行 | 结果 |
|---|---|---|---|
| 清理非法文件 | `7f35565f03ed2af48cd8ba62be379132c0aa8438` | [42389375459](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42389375459) | success；revision 仍为 `994e86ec…c572` |
| 替换 `manual-poc`（追加正文） | `0bfe855606ea41ad2a637e7314ce44ef89195392` | [42389631453](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42389631453) | success；revision `fa77d863a8472d20c4e70ef3829fd27bfcb3626649bdd5567939fc42f263fea6` |

替换后：`details/manual-poc.json` 的 `contentRevision` 与索引一致，正文包含新增的
“Replaced during the controlled manual drill.”；索引中只有 1 个 `manual-poc` 当前条目。

## 5. 下架

| 检查 | 结果 |
|---|---|
| 提交 | `e05dd3e4a2ad7e7a7a237b9554105f15ae8556e4`（删除原件与 `catalog/manual-poc.json`） |
| 运行 | [42389927894](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42389927894)（push） |
| 状态 | `build` success；`deploy` success |
| 站点 `contentRevision` | `2ceb63c19812d6953956cb9a4af001f587d0ad82cb3df7450bea8037d617de82`（与起始一致） |
| 索引 | 恢复 4 个 slug，无 `manual-poc` |
| 详情探测 | `details/manual-poc.json` 返回 `404` |
| 最终 HEAD | `e05dd3e4a2ad7e7a7a237b9554105f15ae8556e4`（本地与远端一致） |

下架后站点内容回到 T016 前状态，说明移除当前条目后索引、详情和下载一致更新；替换/新增/下架
均通过同一次运行内的 build → deploy 完成。

## 6. 未运行与限制

- POC 使用精简 workflow，未远程运行完整 `npm run check`/`npm run security`；生产 `maintain.yml`
  未在远程执行。
- 生产 Pages 仍为 `legacy`，未切换；本轮不是生产发布验收。
- 未验证浏览器中的详情/分享/下载交互、MIME/缓存或移动端；只检查索引、详情 JSON 与运行状态。
- 未验证 environment 审批、分支保护或权限失败；相关权限静态断言见 US-003。
- 推送期间出现短暂网络错误并重试成功；不影响提交、运行和站点结果。
- POC 仓库保留 5 个测试提交（`3d84341`～`e05dd3e`），当前内容已恢复；未删除临时仓库。
