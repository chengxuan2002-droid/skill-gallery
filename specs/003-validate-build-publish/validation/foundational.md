# US-003 Foundational 验收

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: T003–T009；共享发布校验、CLI、工作流骨架和本地回归。

## 1. 执行环境

| 项 | 值 |
|---|---|
| 分支 | `codex/us-003-validate-build-publish` |
| 实际运行时 | Node `v22.21.0`、npm `10.9.4` |
| 锁定基线 | Node `26.3.0`、npm `11.16.0` |
| 说明 | 本地版本与锁定基线不一致；以下结果只代表当前 Windows/Node 22 环境 |

## 2. 命令与结果

| 命令 | 退出码 | 结果 |
|---|---|---|
| `node --test tests/unit/publish.test.js tests/integration/publish-artifact.test.js tests/integration/publish-workflow.test.js` | 0 | 10 项：9 通过、0 失败、1 跳过（symlink 创建不可用） |
| `npm run lint` | 0 | ESLint 无错误 |
| `npm run format:check` | 0 | Prettier 全部通过 |
| `npm test` | 0 | 174 项：172 通过、0 失败、2 跳过（symlink 1 项 + 既有 legacy 基线 1 项） |
| `node scripts/publish-check.js artifact --dist <临时 dist>` | 0 | `status=verified`，`files=20` |
| `node scripts/publish-check.js artifact --dist <篡改 dist>` | 6 | `status=failed`，`E_ARTIFACT_HASH` |
| `node scripts/publish-check.js target --target <sha> --remote <sha>` | 0 | `decision=current` |
| `node scripts/publish-check.js target --target <sha> --remote <other>` | 4 | `decision=superseded` |

## 3. 覆盖内容

- `verifyArtifact`：manifest 双向一致、白名单、`..`/绝对路径/反斜杠/控制字符/重复路径、
  隐藏文件、符号链接（本机跳过）、大小/SHA-256、`contentRevision` 同源、文本文件凭证扫描。
- `evaluateDeployTarget`：40 位 SHA、`current`/`superseded`。
- `createRunStatus`：封闭字段、`commit_status`、`content_status`、`deploy_status`、
  可选起止时间和 `run_url`。
- `renderSummary`：提交/构建/部署状态分开，运行链接或时间；不回显恶意 reason。
- `.github/workflows/maintain.yml` 静态检查：触发、工作流级并发、job 级超时、默认权限、
  `dist` artifact、`github-pages` environment、`pages` 并发组、固定 SHA、无
  `pull_request_target`/`secrets.`。
- 临时项目构建未覆盖工作区 `dist/`；现有 `dist/manifest.json` 仍为
  `contentRevision=068cd50d57fc3a528bd824437f8ec357a8cbea3acb1d4fb75ebec7a30799840a`，
  21 个产物、4 个 skill，时间未变化。

## 4. 未运行项

- 未在 Node 26.3.0/npm 11.16.0 或 Linux/CI 复验。
- 未执行 `.github/workflows/maintain.yml` 的远程运行；未启用 Pages GitHub Actions 源。
- 未进行真实 Pages 部署、environment 审批或线上检查。
- Windows 不允许创建符号链接，对应测试跳过；未在支持环境补跑。
- T010–T013 的 US1 验收已由 [us3-snapshot.md](us3-snapshot.md) 与
  [us3-links.md](us3-links.md) 记录；T014–T016 的 US2 测试契约已完成；
  T017–T032（US2 验证/US3/US4/Polish）未执行。
