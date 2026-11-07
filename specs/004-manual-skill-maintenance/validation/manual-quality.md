# US-004 全量检查记录（T014）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 运行 US-004 的规范、测试与安全检查；只读检查现有实现，不修改业务行为、不写工作区
`dist/`、不部署、不推送。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）；
Gitleaks 8.30.1、Semgrep 1.183.0；依赖审计固定查询 `https://registry.npmjs.org/`。

## 结果

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npm run lint` | 0 | ESLint 无错误 |
| `npm run format:check` | 0 | Prettier 全部通过 |
| `npm test` | 0 | 220 项：218 通过、0 失败、2 跳过 |
| `npm run security:secrets` | 0 | 266 个文件、0 findings |
| `npm run security:code` | 0 | 37 个文件、0 findings |
| `npm run security:deps` | 0 | 1 个锁文件、0 findings（0 个漏洞） |

`npm test` 覆盖 `tests/unit/*.test.js`、`tests/integration/*.test.js` 与
`tests/integration/publish/*.test.js`；US-004 新增 `tests/unit/site-entry.test.js`、
`tests/integration/manual-maintenance.test.js` 与 `tests/support/manual-fixture.js`。
2 项跳过为平台不支持的符号链接创建场景。

本轮未新增 npm 依赖，未修改内容 schema、搜索/详情前端、US-003 发布链、`skills/`、`catalog/`
或根 `assets/search-index.json`；页面只新增页脚管理外链。

## 未运行

- 未在 GitHub Actions runner 执行完整 `npm run check`/`npm run security`。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 本地复验。
- 未在浏览器中检查页脚视觉、键盘焦点、移动端布局或旧链接交互。
- 未切换生产 Pages，未做真实发布。
