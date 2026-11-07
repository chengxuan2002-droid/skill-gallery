# US-004 基线预检（T001）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 固定 US-004 开始前的分支、工程基线、首页状态、生产 Pages 与受控仓库状态；
不读取或打印凭证，不修改页面、远程仓库或 Pages 设置。

## 1. 分支与提交

| 项 | 值 |
|---|---|
| 分支 | `codex/us-004-manual-maintenance`（从 US-003 分支堆叠） |
| HEAD | `08907db59b4a3997bfe1b21ccb45a8de3604fa43` |
| 已推送 | 否（US-004 分支仅本地） |
| 工作区 | 干净 |

## 2. 工程基线

| 项 | 值 |
|---|---|
| Node / npm 实际版本 | `v22.21.0` / `10.9.4` |
| 锁定版本 | Node `26.3.0` / npm `11.16.0`（未在本机复验） |
| `npm test` | 211 项：209 通过、0 失败、2 跳过（符号链接创建不可用） |
| 测试入口 | `tests/unit/*.test.js`、`tests/integration/*.test.js`、`tests/integration/publish/*.test.js` |
| 安全扫描器 | 本机 `.tools` 已安装固定 Gitleaks/Semgrep（版本见 `config/security-tools.json`） |

## 3. 首页与入口现状

- `index.html` 页脚当前只有技能计数、分隔符和 `Source` 外链
  （`href="https://github.com/"`，通用地址）；没有“管理”外链。
- 首页没有登录表单、`<input type="file">` 或上传按钮；访客只读。
- 管理入口契约要求见 `specs/004-manual-skill-maintenance/contracts/manual-maintenance.md`。

## 4. 生产与受控环境

| 项 | 值 |
|---|---|
| 生产 Pages | `build_type=legacy`、`source=main:/`、`status=built`（未切换） |
| 生产 `main` | 与本地 `main` 一致；US-003 分支已推送并创建 PR #1（未合并） |
| POC-002 | `chengxuan2002-droid/skill-gallery-poc-20261107`，公开，Pages `build_type=workflow` |
| POC 最近运行 | `42377824309`（push，success）、`42377905399`（dispatch，success），目标 `d273815` |
| POC workflow | 精简版 `maintain.yml`：保留构建/校验/上传/部署/摘要，移除完整 check/security |

## 5. 授权与边界

- T001–T003 只做本地预检、测试与文档；不推送、不部署、不切换生产 Pages。
- 手动发布的受控验证（后续 T016）使用 POC-002；生产 Pages 保持 `legacy`，真实启用需单独授权。
- 不执行 `skills/` 中的脚本或测试，不安装其依赖；不读取或打印任何凭证。
