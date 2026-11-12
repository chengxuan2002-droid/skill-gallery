# US-006 POC-003 受控 GitHub 来源验收

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T026；在受控公开仓库验证固定修订、Release/pinned、两修订增删文件、许可、真实 404 与注入边界。

## 1. 受控仓库

| 角色 | 仓库 | 说明 |
|---|---|---|
| 源 | `chengxuan2002-droid/skill-gallery-source-poc-20261112`（公开） | 新建，含 `skills/poc-skill`、LICENSE、二进制与两修订 |
| 消费端 | `chengxuan2002-droid/skill-gallery-poc-20261107`（公开） | 复用 POC-002，加入 US-006 代码、workflow 与 `source-poc` 记录 |

源修订：

- v1：`e679bab62906c77efb79168e99c8d53271ef1b64`，tag/Release `v1.0.0`（非草稿、非预发布）。
- v2：`7e8437e664af276afa4343d324d40dda9a69cb1d`，更新正文、删除 `references/old.md`、
  新增 `references/new.md` 与 `notes.txt`。
- `assets/binary.bin` 含 0/1/2/3/255 字节；`skills/poc-skill/LICENSE` 为 MIT。

## 2. 真实检查

| 策略 | 解析结果 | 状态 |
|---|---|---|
| branch `main` | `7e8437e...` | `candidate` |
| release latest | `e679bab...`（v1.0.0） | `unchanged` |
| pinned `e679bab...` | 同 pinned | `unchanged` |
| 不存在的仓库 | 无修订 | `failed` / `E_SOURCE_NOT_FOUND` |

Release 未退回分支；pinned 未前移；普通网页 URL、越界路径、子模块/符号链接由注入测试拒绝。

## 3. 应用与发布

- 基线同步：run [43208732789](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208732789)，
  提交 `0c68fed4c008`，只更新来源基线字段。
- v2 替换：run [43208983544](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208983544)，
  提交 `7b439a18f6d3`；旧附件删除、新附件出现、站内字段保留；同次 build/deploy 成功。
- 无变化：run [43209635536](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43209635536)，
  build/deploy skipped，无新提交。
- 公开索引：`source-poc` 只有一项，`content_text` 为 v2 正文，详情/下载来自同一内容快照。

## 4. 观察与限制

- 首次从本地 Git worktree 复制 v1 时，Windows 换行转换导致许可字节不同，检查正确返回
  `E_LICENSE_CHANGED`；按提交字节复制后通过。这验证了许可按路径与字节摘要比较。
- 未运行真实 403、限流等待、真实截断树、真实子模块/符号链接和真实二进制下载逐字节对比；
  默认测试已用注入夹具覆盖这些边界，不能把夹具结果写成远程通过。
- POC 的 push 运行 [43208462776](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208462776)
  中 deploy 被跳过，原因未定位；同次发布通过证据仅使用两个 manual dispatch 运行。
- POC-003 不替代生产调度、environment 审批或 US-007 整体验收。
