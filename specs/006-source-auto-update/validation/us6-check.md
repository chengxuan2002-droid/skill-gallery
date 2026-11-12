# US-006 检查与无变化验收

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T009–T011；检查模式、固定修订、无变化与逐来源失败隔离。真实来源读取在 POC-003 消费端副本执行，不改写工作区。

## 1. 自动测试

```bash
node --test tests/unit/github-source.test.js
node --test tests/integration/source-sync-check.test.js
node --test tests/unit/source-sync-state.test.js
```

结果：全部通过；覆盖 branch/release/pinned、固定 40 位 SHA、Release 缺失、截断树、子模块/符号链接、
越界路径、500 文件/20 MiB/主文档 1 MiB、mode 保真、404/403/429/超时/限流映射、`unchanged`/`candidate`、
重复检查幂等和单来源失败隔离。

## 2. 真实 POC 检查

在 POC-002 临时副本执行（源仓库 `chengxuan2002-droid/skill-gallery-source-poc-20261112`）：

| 场景 | 来源策略 | 结果 |
|---|---|---|
| `branch-poc` | branch `main` | `candidate`；revision `7e8437e664af276afa4343d324d40dda9a69cb1d`；digest `e84013cf...` |
| `release-poc` | release latest（v1.0.0） | `unchanged`；revision `e679bab62906c77efb79168e99c8d53271ef1b64`；digest `05fdffbf...` |
| `pinned-poc` | pinned v1 SHA | `unchanged`；revision 与 pinned 相同；digest `05fdffbf...` |
| `missing-poc` | 不存在的仓库 | `failed`；`E_SOURCE_NOT_FOUND` |

命令：

```bash
node scripts/sync-skills.js --slug branch-poc --json
node scripts/sync-skills.js --slug release-poc --json
node scripts/sync-skills.js --slug pinned-poc --json
node scripts/sync-skills.js --slug missing-poc --json
```

检查模式未写入工作区、未提交、未推送；输出为单行封闭 JSON。`release` 未回到分支，`pinned` 未前移。

## 3. 无变化调度运行

POC-002 workflow dispatch（`sync=true`, `slug=source-poc`，源 main 已等于当前内容）：

- run [43209635536](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43209635536)
- `sync` success；`build`/`deploy` skipped；最新提交仍为 `7b439a18f6d3`，未产生空提交。

## 4. 未运行

- 真实 403、真实限流等待和真实截断树；由注入测试覆盖，未伪造远程成功。
- 生产 `main` 的每日调度；POC 的 schedule 配置不等于生产启用。
