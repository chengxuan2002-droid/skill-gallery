# US-006 单版本完整替换验收

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T012–T014；候选应用、单版本替换、旧附件清理与站内字段保留。消费端为 POC-002。

## 1. 自动测试

```bash
node --test tests/integration/source-sync-apply.test.js
```

结果：全部通过。覆盖目录 v2 增删文件、声明版本不变但正文变化、单文件↔目录互换、站内字段保留、
只提交目标路径、旧附件消失、重复 apply 幂等，以及 local project root 不被推送改写。

## 2. POC 基线

- 源 v1 SHA：`e679bab62906c77efb79168e99c8d53271ef1b64`
- 消费端基线提交：`8237989a3c551cd5ea867423491f765c7f99b9c5`
- 首次同步 run：[43208732789](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208732789)
- 同步提交：`0c68fed4c008`，仅修改 `catalog/source-poc.json`，建立 `last_synced_digest`；
  内容与 v1 相同，没有改写原件。

## 3. v2 替换

源 v2 SHA：`7e8437e664af276afa4343d324d40dda9a69cb1d`（正文更新、删除 `references/old.md`、
新增 `references/new.md` 与 `notes.txt`）。

- run：[43208983544](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208983544)
- 同步提交：`7b439a18f6d3`
- 变更文件：
  - `catalog/source-poc.json`（同步修订/摘要/时间）
  - `skills/source-poc/SKILL.md`
  - `skills/source-poc/notes.txt`（新增）
  - `skills/source-poc/references/new.md`（新增）
  - `skills/source-poc/references/old.md`（删除）

核对：

| 检查 | 结果 |
|---|---|
| slug | 仍为 `source-poc`，未重命名 |
| 当前清单 | 只有 v2 文件；`references/old.md` 不在远端树 |
| 站内字段 | `display_name`、`tags`、`notes`、`usage` 保留 |
| 来源字段 | `last_synced_revision=7e8437e...`，digest 与候选一致 |
| 公开索引 | `source-poc` 只有一项；`content_text` 为 v2 正文；revision `9e9455c6...` |
| 部署 | 同次运行 build/deploy 成功 |

## 4. 未运行

- 真实二进制下载逐字节对比（POC 的 `assets/binary.bin` 已随清单保留，未逐字节记录 URL 下载）。
- 生产站点发布；POC-002 的发布不作为生产更新。
