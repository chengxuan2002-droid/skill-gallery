# US-007 汇总质量与安全检查

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T021；运行 `npm run check`、`npm run security` 和工作流/发布静态测试，记录实际命令、
数量、退出码和未运行项。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`；锁定基线仍为 Node 26.3.0/npm 11.16.0。
首次运行前本地 `node_modules` 缺少 ESLint/Prettier 开发依赖，执行 `npm ci` 安装 104 个包后重跑；
安装时出现 Node 版本 EBADENGINE 警告，未把本机版本冒充锁定基线。

## 1. npm run check

```bash
npm run check
```

结果：退出码 `0`；`npm run lint`、`npm run format:check`、`npm test` 依次通过。

| 步骤 | 结果 |
|---|---|
| `npm run lint` | 退出码 0 |
| `npm run format:check` | 退出码 0；所有匹配文件使用 Prettier 风格 |
| `npm test` | 282 项：280 通过、0 失败、2 跳过 |

`npm test` 覆盖单元、集成、发布/同步 workflow、状态模型、保真、路径/凭证、不可信内容、来源
检查/应用/冲突/许可、调度和回滚语义。2 项跳过为环境限制（符号链接创建不可用/基线红测），不计为失败。

## 2. npm run security

```bash
npm run security
```

| 检查 | 文件数 | 发现数 | 退出码 |
|---|---|---|---|
| `security:secrets` | 355 | 0 | 0 |
| `security:code` | 56 | 0 | 0 |
| `security:deps` | 1 | 0 | 0 |

三项均 `status=passed`；输出只有检查名、状态、文件数和空 `findings`，未打印凭证或源码片段。
依赖审计通过 high/critical 阈值；详细边界见 `security.md`。

## 3. macOS runner 补充

GitHub-hosted `macos-latest` run `43588719771`（2026-11-14）使用 Node 26.3.0/npm 11.16.0 重复了
`npm run check`、`npm run security` 和 `npm run build`：282 项测试 281 通过、0 失败、1 跳过；
安全 secrets 350/code 56/deps 1，findings 0；构建 contentRevision `faa0f345...` 与生产一致。
详见 `macos-ci.md`。

## 4. 工作流/发布静态检查

`npm test` 中包含的发布/同步静态测试覆盖：

- `publish-workflow`、`publish-same-run`、`publish-sync-workflow`、`publish-security-workflow`、
  `publish-summary-workflow`、`publish-deploy-workflow`：触发、权限、同次运行、摘要和部署前 freshness；
- workflow 固定 SHA、无 `workflow_run`/`pull_request_target`、无 secret/PAT、最小权限；
- `publish-check` 的 current/superseded/invalid 退出码和只读目标检查。

这些是本地静态/夹具断言；生产 environment 的真实演练见 `production-environment.md`，不能把静态断言
等同于远程行为。

## 5. 未运行与限制

- 本机为 Node 22.21.0/Windows；Node 26.3.0/Linux 与 GitHub-hosted macOS runner 的结果以 CI/runner
  为准，未在本机复验。
- 生产 environment 审批、生产部署失败注入、MIME/缓存基础头和一次真实 403 已补验（见
  `production-environment.md`、`fixed-address.md`、`remote-errors.md`）；真实 source-sync 429、
  Safari/移动实机和 CDN/强刷仍未运行；见 `residual-gaps.md`。
- `npm ci` 只更新被忽略的本地依赖目录，不改变锁文件或站点内容。
