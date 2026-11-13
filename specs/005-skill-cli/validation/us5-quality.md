# US-005 全量检查记录（T019）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 运行 US-005 的规范、测试与安全检查；只读检查现有实现，不修改业务行为、不写工作区
`dist/`、不部署、不推送。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）；
Gitleaks 8.30.1、Semgrep 1.183.0；依赖审计固定查询 `https://registry.npmjs.org/`。

## 结果

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npm run lint` | 0 | ESLint 无错误 |
| `npm run format:check` | 0 | Prettier 全部通过 |
| `npm test` | 0 | 241 项：239 通过、0 失败、2 跳过 |
| `npm run security:secrets` | 0 | 299 个文件、0 findings |
| `npm run security:code` | 0 | 47 个文件、0 findings |
| `npm run security:deps` | 0 | 1 个锁文件、0 findings（0 个漏洞） |

2026-11-12 复核 `npm test` 为 242 项（240 通过、0 失败、2 跳过）；本表保留 US-005 收口时点。

`npm test` 覆盖 `tests/unit/*.test.js`、`tests/integration/*.test.js` 与
`tests/integration/publish/*.test.js`；US-005 新增 `scripts/skill-cli.js`、
`scripts/lib/skill-cli/`、`tests/unit/skill-cli-{args,status}.test.js` 与
`tests/integration/skill-cli-{add,replace,import}.test.js`、`tests/support/skill-cli-fixture.js`。
2 项跳过分别为基线红灯检查（未设置 `LEGACY_FIDELITY_EXPECTED`）与本平台不支持符号链接创建。

本轮未新增 npm 依赖，未修改内容 schema、搜索/详情前端、US-003 发布链、`skills/`、`catalog/`
或根 `assets/search-index.json`；CLI 只在隔离 worktree/临时目录操作。

## 未运行

- 未在 GitHub Actions runner 执行完整 `npm run check`/`npm run security`。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 本地复验。
- 本记录时点未执行真实 POC-002 发布/替换/状态查询（T021 后续已执行）或生产发布。
