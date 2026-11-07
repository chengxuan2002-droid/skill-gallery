# Contract: 发布工作流（M-07 子集）

**Feature**: US-003 | **Date**: 2026-11-07 | **Spec**: [../spec.md](../spec.md)

本契约定义 `.github/workflows/maintain.yml` 的触发、权限、并发、产物和状态边界。工作流只负责
校验、构建、上传 Pages artifact 和显式部署；内容校验与构建入口仍是现有
`npm run check`、`npm run build` 和 `scripts/lib/publish.js`，不另建第二套规则。

## 1. 触发

| 事件 | 条件 | 用途 |
|---|---|---|
| `push` | 仅默认分支 `main` | 合法提交后的发布 |
| `workflow_dispatch` | 手动，支持重跑同一提交 | 管理员重试/恢复入口 |

不在本工作流监听 `pull_request`、`pull_request_target` 或 fork 来源；PR 检查继续由
`quality.yml` 承担。`schedule` 留给 US-006 的 Q-004 调度，本故事不添加。

## 2. 权限（job 级最小权限）

| Job | `permissions` | 说明 |
|---|---|---|
| `build` | `contents: read` | checkout、依赖安装、校验、构建、上传 artifact |
| `deploy` | `pages: write`、`id-token: write` | 只做 Pages 部署；不需要仓库写权限 |
| 未来 `sync`（US-006） | `contents: write` | 仅同步 job 可提交；不得下放给 build/deploy |

工作流默认 `permissions: contents: read`。checkout 必须 `persist-credentials: false`；
不使用 PAT、自定义 secret 或 `GITHUB_TOKEN` 之外的凭证。任何权限不足必须失败关闭，不降低分支保护。

## 3. 并发与过期

```yaml
concurrency:
  group: maintain-${{ github.ref }}
  cancel-in-progress: false
```

部署 job：

```yaml
concurrency:
  group: pages
  cancel-in-progress: false
```

部署前比较目标提交与远端默认分支 HEAD；不一致时状态为 `superseded`，跳过 `deploy-pages`，
但 job 不得误报“已发布”。同一提交重跑幂等，不新建内容提交。

## 4. 构建与 artifact

1. Checkout（`fetch-depth` 足够读取目标提交；无持久凭证）。
2. 使用 `.node-version` 与锁定 npm 版本；全局安装 `npm@11.16.0`（禁用 audit/fund），
   `npm ci --ignore-scripts --no-audit --no-fund`。
3. 安装固定扫描器 `npm run setup:security`（uv/Gitleaks/Semgrep 版本以
   `config/security-tools.json` 为准）；工具缺失或网络失败即停止。
4. 运行 `npm run check` 与 `npm run security`；失败即停止，不上传 artifact、不部署。
5. 运行 `npm run build`，要求退出码 0 且 `dist/manifest.json` 存在。
6. 运行 `node scripts/publish-check.js artifact --dist dist`；失败即停止。
7. 使用固定 SHA 的 `actions/upload-pages-artifact` 上传 `dist/`，artifact 名称保持默认
   `github-pages`，retention 使用默认值（1 天）。

固定 action 版本：

| Action | 版本 | 完整 SHA |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `astral-sh/setup-uv` | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` |
| `actions/upload-pages-artifact` | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `actions/deploy-pages` | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |

不引入 `configure-pages`：构建产物与 base path 固定为 `/skill-gallery/`，Pages 配置属于外部设置。

## 5. 部署

- `deploy` job `needs: build`，`environment: github-pages`，使用固定 SHA 的 `actions/deploy-pages`。
- 部署前以 `git ls-remote https://github.com/${GITHUB_REPOSITORY}.git refs/heads/main` 读取远端 HEAD，
  调用 `publish-check.js target`；`superseded` 时不执行部署。
- 部署失败必须保留上次正常线上快照（平台行为），状态显示 `deploy_failed`；重跑同一提交不新建内容提交。
- 部署成功后输出 `page_url` 到 Step Summary；不得把“artifact 上传成功”当作“已部署”。

## 6. 状态与摘要

Step Summary 至少包含：运行标识/链接、触发方式、目标 SHA、`content_revision`、
`content_status`、`deploy_status`、失败码或 `superseded` 说明。禁止写入 token、cookie、
响应正文、环境变量、用户文件内容或原始异常堆栈。公开页面不展示运行日志。

## 7. 外部前提（未授权不修改）

- 仓库 Pages 的 Source 必须为 “GitHub Actions”；`github-pages` environment 按需配置保护规则。
- 分支保护、environment 审批、生产仓库设置和线上切换由维护者单独授权；POC-002 只在受控仓库验证。
- 若环境审批导致部署等待/超时，状态为等待或失败，不算发布成功。

## 8. US-006 扩展点

US-006 在同一工作流增加 `sync` job（`contents: write`），提交候选后通过 `needs` 进入现有
`build`/`deploy`；不得改为依赖机器人 push 触发的另一条工作流。US-003 的工作流结构必须允许该扩展，
但本故事不实现来源检查、调度或提交逻辑。
