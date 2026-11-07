# US-003 最终差异复核（T030）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 对照 `spec.md`、`contracts/`、`validation/` 复核 T019–T032 的实际差异、验证结果与未运行项；
只读检查仓库、远程分支状态和生产 Pages 设置，不推送、不合并、不部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 差异范围

以 US-002 分支本地 tip `b98b09a75c040997191d170f171d6ee839d40e7c` 为基线，US-003 共 44 个提交，
变更仅涉及：

- 新增 `.github/workflows/maintain.yml`、`scripts/lib/publish*.js`、`scripts/publish-check.js`、
  `scripts/publish-summary.js`；
- 新增/重组发布相关测试与 `tests/support/publish-fixture.js`，`package.json` 仅调整 `test` glob；
- 新增 US-003 规格、计划、任务、契约与 validation 记录；
- 定向更新 `README.md`、`AGENTS.md` 的本故事状态。

复核结果：

| 检查 | 结果 |
|---|---|
| `skills/`、`catalog/`、`assets/`、`index.html`、`assets/search-index.json`、`package-lock.json` | 无差异 |
| 新增 npm 依赖 | 无；`package.json` 仅新增 `tests/integration/publish/*.test.js` 测试入口 |
| `dist/` 纳入版本控制 | 0 个文件 |
| 全仓格式化或无关重构 | 无；仅本故事文件与测试路径重组 |
| Pages 设置、分支保护、environment | 未修改；生产 Pages 仍为 `build_type=legacy`、`source=main:/`、`status=built` |

## 2. 验证汇总

| 验证 | 结果 |
|---|---|
| `npm test` | 211 项：209 通过、0 失败、2 跳过 |
| `npm run lint` / `npm run format:check` | 退出码 0 |
| `npm run security` | secrets 248 文件、code 37 文件、deps 1 文件，findings 均为 0 |
| `publish-check.js artifact/target` | 冒烟退出码 `0/4/2/6` 与契约一致，诊断不回显值 |
| 受控 POC-002 | 部署失败/旧站保留/同提交重跑（T018）、同次运行发布（T025）、匿名未授权 `401` 且无副作用（T022） |
| 隔离恢复与取用回归 | `git revert` 恢复后 `contentRevision` 回到基线；4 个 slug、旧链接、单版本、原文/ZIP 保真通过（T031/T032） |

证据入口：[us3-security.md](us3-security.md)、[us3-same-run.md](us3-same-run.md)、
[us3-recovery.md](us3-recovery.md)、[us3-regression.md](us3-regression.md)、
[us3-quality.md](us3-quality.md)、[us3-snapshot.md](us3-snapshot.md)、[us3-links.md](us3-links.md)。

## 3. 公开页面暴露

- 发布摘要由 `scripts/publish-summary.js` 写入 `$GITHUB_STEP_SUMMARY`，只存在于 Actions 运行记录；
  公开前端资产与首页不含 `GITHUB_STEP_SUMMARY`、`PUBLISH_*`、运行链接或错误码标记。
- 索引/详情 schema、slug、下载 URL 和前端行为未改动；公开页面仍只展示既有 `updated_at` 等同步字段，
  不新增运行日志、失败码或原始异常。
- 本地 `monitor:site` 两次重试均超时（非通过）；直接 GET 生产首页返回 HTTP 200、1,233 字节。
  该探测只说明现站可访问，不证明 MIME、缓存或子路径在发布后仍正确。

## 4. 验收映射与状态

| 成功标准 | 本地/受控结果 | 生产状态 |
|---|---|---|
| US003-SC-01/02 非法产物阻止、白名单与同快照 | 通过（隔离构建与注入测试） | 未部署 |
| US003-SC-03 固定地址、子路径、旧链接、刷新 | 隔离构建与 POC 站点子路径通过；浏览器未复验 | 生产 Pages 未切换，未在发布后验证 |
| US003-SC-04 部署失败状态、同提交重跑 | POC-002 通过 | 生产未运行 |
| US003-SC-05 未授权零副作用、凭证零回显、内容零执行 | 本地契约 + POC 匿名尝试通过 | 生产未运行 |
| US003-SC-06 状态区分、并发/过期、同次运行 | 本地测试 + POC 同次运行通过 | 生产未运行 |

## 5. 未运行与剩余风险

- 生产 Pages 源、environment、分支保护和线上切换未修改；本故事交付的是可审阅配置、本地/受控验证，
  不是生产发布验收。
- US-002 分支未合并 `main`（本地 tip 比远端多 2 个提交）；US-003 分支未推送、未合并。
- T041 的 macOS 缺口保持未验证、未勾选；US-002/US-001 既有浏览器与平台证据未重新执行。
- 未在 Node 26.3.0/Linux 本地复验；未在本地运行完整 `npm run check`/`npm run security` 的 GitHub
  runner 组合（POC 使用精简 workflow，未含 check/security）。
- 未验证发布后线上 MIME、缓存、直接资源响应或真实回滚；POC 临时公开仓库尚未删除。
- US-004～US-007（上传入口、维护命令、来源检查/Q-004 调度、整体验收）仍未实现。

## 6. 结论

US-003 的本地与受控验证范围完整：产物校验、最小权限、失败保留、过期/重跑、同次运行、匿名未授权
拒绝、隔离恢复与取用回归均有可追溯证据；未发现对本故事边界外的内容、schema、前端或依赖改动。
生产启用与线上发布仍需单独授权和验证，不能把本记录当作线上成功。
