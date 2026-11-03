# push/PR 安全扫描 CI 补强

日期：2026-11-03。用户要求确认 GitHub Actions 配置，并确保每次 push/PR 自动运行 Gitleaks 与 Semgrep，
不依赖开发机本地环境。映射 NFR-003/NFR-006、DEC-005/009、AC-012/014 的工程支撑子集。

## 现有配置与缺口

仓库已有 `.github/workflows/quality.yml`，原先只在 `main` push、所有 PR 和手动触发时运行；
安全扫描通过聚合 `npm run security` 执行，未把 Gitleaks/Semgrep 作为显式步骤展示。
开发机 `.tools` 未安装扫描器，本地 `npm run check` 仍有 2 项扫描器用例失败，因此不能依赖本地环境。

`site-monitor.yml` 仍是默认分支定时/手动可用性监测，不承担源代码扫描。

## 本次配置

- 触发：所有分支的 `push`、所有 `pull_request`、`workflow_dispatch`。
- 运行环境：`ubuntu-24.04`；Node 来自 `.node-version`（26.3.0），npm 固定 11.16.0，
  uv 固定 0.12.3；`actions/checkout`、`actions/setup-node`、`astral-sh/setup-uv` 使用完整 SHA。
- 安装：`npm ci --ignore-scripts`，`npm run setup:security` 下载/安装固定 Gitleaks 8.30.1 与 Semgrep 1.183.0。
- 显式扫描步骤：
  - `npm run check`（Lint、格式、受信任测试）
  - `npm run security:secrets`（Gitleaks）
  - `npm run security:code`（Semgrep）
  - `npm run security:deps`（根依赖审计）
- 四个步骤均 `continue-on-error` 后由最终门禁汇总：任一步非 success 即 job 失败；
  测试失败不会跳过扫描，单项扫描失败也不会阻止其余扫描。
- 权限仅 `contents: read`，`persist-credentials: false`，无部署、写回、Issue/PR 评论或报告上传；
  不缓存扫描器，不使用 `pull_request_target`，不授予 fork 写权限。

## 本地验证

| 检查 | 结果 |
|---|---|
| YAML 解析（yaml 2.9.1） | `quality.yml` 解析成功；`push`/`pull_request`/`workflow_dispatch` 均存在 |
| `npm run format:check` | exit 0，workflow 由 Prettier 格式化检查覆盖 |
| `npm run lint` | exit 0，自有源码不受 workflow 改动影响 |
| 本地扫描器 | 未安装；本地无法执行 Gitleaks/Semgrep，改由 CI 安装执行 |
| Actionlint | 本机未安装；未把 YAML/Prettier 检查冒充 Actionlint 通过 |

## 远程状态与待验证

本改动尚未推送；远程 `main` 仍运行旧版 workflow。首次 push 或 PR 后必须在 GitHub Actions 确认：
runner 安装固定扫描器成功、四个步骤实际执行、最终门禁按失败汇总。未观察前不能声称线上已生效。
未修改分支保护、通知设置、Pages 或 site-monitor；未创建 PR、未推送、未发布。

## 失败与边界

网络/下载/安装失败、扫描器版本不符、Gitleaks/Semgrep 规则错误或依赖审计失败均使 job 失败，不当作通过。
扫描范围仍是自有源码、已跟踪公开原件和根锁；未纳管 office2md 不自动加入扫描，不执行 Skill 脚本。
