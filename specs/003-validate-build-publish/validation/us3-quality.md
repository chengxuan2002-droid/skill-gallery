# US-003 全量检查、冒烟与质量记录

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: T027 全量检查与 T029 发布检查 CLI 冒烟；只读检查现有实现与测试，不修改业务行为、
不写工作区 `dist/`、不部署、不推送。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）；
Gitleaks 8.30.1、Semgrep 1.183.0；依赖审计固定查询 `https://registry.npmjs.org/`。

## 1. 全量检查（T027）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npm run lint` | 0 | ESLint 无错误 |
| `npm run format:check` | 0 | Prettier 全部通过 |
| `npm test` | 0 | 211 项：209 通过、0 失败、2 跳过 |
| `npm run security:secrets` | 0 | 248 个文件、0 findings |
| `npm run security:code` | 0 | 37 个文件、0 findings |
| `npm run security:deps` | 0 | 1 个锁文件、0 findings（0 个漏洞） |

`npm test` 覆盖 `tests/unit/*.test.js`、`tests/integration/*.test.js` 与
`tests/integration/publish/*.test.js`；2 项跳过为平台不支持的符号链接创建场景。本轮未新增
npm 依赖、未修改 `skills/`、`catalog/`、内容 schema、前端行为或根 `assets/search-index.json`。

未运行：GitHub Actions runner 上的完整 `npm run check`/`npm run security`、Node 26.3.0/Linux
本地复验，以及生产 Pages 部署。
