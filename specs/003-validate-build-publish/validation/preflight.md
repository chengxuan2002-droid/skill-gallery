# US-003 实施前基线

**记录时间**: 2026-11-07（Asia/Shanghai）
**任务**: T001（FR-011、NFR-006；AC-014）
**范围**: 只读盘点；未修改 Pages、environment、分支保护、`dist/` 或任何原件。

## 1. 分支与提交

| 项 | 值 |
|---|---|
| 当前分支 | `codex/us-003-validate-build-publish`（从 US-002 功能分支堆叠） |
| HEAD | `b9b355c74922f0c7825686f1121c636113021fa4` |
| 相对 `origin/main` | 领先 100 个提交；未合并 `main` |
| US-002 状态 | T001–T026 已完成本地验收；功能分支 `codex/us-002-search-detail-share` 已推送，未合并 `main`、未发布 |
| US-001 T041 | macOS 仍未运行，复选框保持未勾选；本故事不关闭该缺口 |

## 2. 本地运行时

| 项 | 锁定/期望 | 实际 | 说明 |
|---|---|---|---|
| Node.js | `26.3.0`（`.node-version`、`engines >=26.3.0 <27`） | `v22.21.0` | 本地与锁定基线不一致；本故事验证不得声称为 Node 26.3.0 通过 |
| npm | `11.16.0`（`packageManager`） | `10.9.4` | 同上；依赖安装与测试结果需注明实际版本 |
| 平台 | win32 | win32 | 本地验证；Linux/CI 与 macOS 另记 |

## 3. 现有 dist

- `dist/` 存在，时间为 2026-11-04 06:32:58，未由本任务修改。
- `dist/manifest.json`：`contentRevision=068cd50d57fc3a528bd824437f8ec357a8cbea3acb1d4fb75ebec7a30799840a`，
  21 个产物（artifacts），4 个 skill。
- 本故事的所有构建/验证使用系统临时目录，不覆盖该工作区 `dist/`。

## 4. GitHub 远程设置（只读观察，未修改）

| 项 | 当前值 |
|---|---|
| 站点地址 | `https://chengxuan2002-droid.github.io/skill-gallery/` |
| Pages build type | `legacy`（source branch 模式） |
| Pages source | `main` / `/` |
| Pages status | `built` |
| `github-pages` environment | 存在；protection rule 为 `branch_policy` |
| 本任务变更 | 无；未修改 Pages 源、environment、分支保护或线上内容 |

**注意**：自定义 `deploy-pages` 工作流要求 Pages Source 为 “GitHub Actions”；当前仍为
`legacy/main`。生产切换需单独授权，T008 只交付工作流文件，T018 才在受控仓库验证切换。

## 5. 固定 action 版本

| Action | 版本 | 完整 SHA |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `astral-sh/setup-uv` | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` |
| `actions/upload-pages-artifact` | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `actions/deploy-pages` | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |

前三个与现有 `quality.yml` 一致；后两个为本故事新增，均已在规划阶段按 GitHub 官方 Release 核对。

## 6. 凭证与未运行项

- 未读取、打印、写入任何 token、cookie、密钥或环境变量值；只查询 Pages/environment 的公开配置字段。
- 未运行真实 Pages 部署、未触发 GitHub Actions、未修改远程设置。
- 未在 Node 26.3.0/npm 11.16.0 下复验；后续本地结果按实际 v22.21.0/npm 10.9.4 记录。
- macOS、Safari/移动实机、生产 MIME/缓存/回滚仍为未验证项。
