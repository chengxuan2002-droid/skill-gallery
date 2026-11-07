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

## 2. 发布检查 CLI 冒烟（T029）

使用 `tests/support/publish-fixture.js` 在系统临时目录构建隔离 `dist/`，未写入工作区 `dist/`；
所有输出均为单行 JSON，诊断只含 `code`/`path`/固定 `message`。

| 命令/场景 | 退出码 | JSON 结果 |
|---|---|---|
| `node scripts/publish-check.js artifact --dist <隔离 dist>` | 0 | `status=verified`、`content_revision=c48791d508cf5e3b306d21f8ce60330c391538d5505e248704bae35bac980578`、`files=20`、`diagnostics=[]` |
| `... target --target <sha> --remote <同一 sha>` | 0 | `decision=current`，两个 40 位 SHA 原样返回 |
| `... target --target <sha> --remote <另一 sha>` | 4 | `decision=superseded`，未执行部署 |
| `... target --target not-a-sha --remote <sha>` | 2 | `decision=null`，`E_TARGET_SHA`，stderr 仅错误码 |
| 篡改隔离 `dist/index.html` 后 `artifact` | 6 | `status=failed`、`E_ARTIFACT_HASH`，stderr 仅错误码，旧产物未被修改 |
| `E_ARTIFACT_HASH` 诊断 | — | 只含位置与规则，不回显文件内容 |

冒烟结束后删除临时项目，未执行 `dist/` 中的脚本、未发起网络请求。
