# US-006 Quickstart 走查

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T028；按 [quickstart.md](../quickstart.md) 在受控副本执行，不修改生产内容。

## 1. 前置

- Node `v22.21.0`、npm `10.9.4`（锁定 Node 26.3.0 未在本机复验）。
- `gh` 已登录；未在命令、文件或输出中放置 token。
- 使用 POC-002 临时 clone 与临时裸远端；不执行 `skills/` 中的脚本，不安装收录 Skill 依赖。

## 2. 检查与无变化

```bash
node scripts/sync-skills.js --help
node scripts/sync-skills.js --slug branch-poc --json
node scripts/sync-skills.js --slug release-poc --json
node scripts/sync-skills.js --slug pinned-poc --json
node scripts/sync-skills.js --slug missing-poc --json
```

结果：

- `--help` 输出选项与边界，退出码 0。
- branch → `candidate`；release/pinned → `unchanged`；missing → `failed` + `E_SOURCE_NOT_FOUND`。
- 检查模式未写工作区、未提交、未推送；stdout 为单行 JSON。

## 3. 单版本替换

```bash
node scripts/sync-skills.js --slug source-poc --apply --push --report sync-report.json --summary sync-summary.md
```

在 POC-002 workflow dispatch 中执行同一入口：

- 基线 run 43208732789：提交 `0c68fed4c008`，只更新 catalog。
- v2 run 43208983544：提交 `7b439a18f6d3`，旧附件删除、新附件出现、站内字段保留。
- 无变化 run 43209635536：`changed=false`，build/deploy skipped，无新提交。

## 4. 状态与恢复

- `sync-summary.md`/Step Summary 显示来源状态、revision、digest、许可状态、commit/content/deploy 状态；
  不含 token、响应正文或原始异常。
- 部署失败重跑与受控 revert 未执行；见 [us6-status.md](us6-status.md)。

## 5. 偏差

- quickstart 的“模拟部署失败”和“受控 revert”未运行；其余检查、应用、无变化、失败保留和同次发布
  已按受控副本走通。
- POC 使用精简 workflow（不运行完整 check/security），与生产 `maintain.yml` 的完整构建检查不同；
  生产构建检查由 CI 与 US-003 覆盖。
