# Quickstart: US-003 校验、构建与原地址发布流水线

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本指南只描述实施后的可执行验证步骤；状态字段、退出码和产物规则见
[data-model.md](data-model.md)、[publish 契约](contracts/publish.md) 与
[workflow 契约](contracts/workflow.md)。不包含生产发布授权或真实 Pages 设置变更。

## 1. 前置条件

- Node 26.3.0、npm 11.16.0（以 `.node-version` 和 `package.json` 为准）。
- 干净 checkout；不执行 `skills/` 中的脚本或测试，不安装收录 Skill 的依赖。
- 本地已安装固定安全扫描器：`npm run setup:security`（需要 uv 与网络）。
- 生产仓库、Pages 源、environment 和 branch protection 未获授权时，只执行本地步骤；
  真实部署与线上检查必须单独授权。

```bash
npm ci
npm run setup:security
```

## 2. 本地构建与产物校验

```bash
npm run check
npm run security
npm run build
node scripts/publish-check.js artifact --dist dist
```

期望：

- `npm run build` 输出 `status=built` 且 `dist/manifest.json` 存在；失败时不替换旧 `dist/`。
- 产物校验输出 `status=verified`、`content_revision` 与 `files` 数量，退出码 `0`。
- 内容未变化时允许重复部署同一快照；验收只要求不新建内容提交且不把重复部署伪装成内容更新。

## 3. 失败路径（隔离副本）

在临时项目或构建副本中依次注入以下情况，每次确认退出码非零且不修改被验证的旧产物：

```bash
# 额外文件
printf 'x' > dist/docs-plan.md
node scripts/publish-check.js artifact --dist dist

# 篡改字节
printf 'tampered' >> dist/index.html
node scripts/publish-check.js artifact --dist dist

# 凭证类文件
printf 'YOUR_API_KEY_HERE' > dist/.env
node scripts/publish-check.js artifact --dist dist
```

期望退出码 `6`，诊断只包含 `code`、`path` 和脱敏后的 `message`；不得回显文件内容或凭证值。

## 4. 目标提交判定

```bash
node scripts/publish-check.js target --target "$GITHUB_SHA" --remote "$GITHUB_SHA"
node scripts/publish-check.js target --target "$GITHUB_SHA" --remote "<另一个 40 位 SHA>"
```

期望：第一个退出码 `0`、`decision=current`；第二个退出码 `4`、`decision=superseded`。
非 40 位十六进制输入返回 `2`。

## 5. 工作流静态检查

```bash
node --test tests/integration/publish/publish-workflow.test.js
```

期望：

- 触发仅 `push: main` 和 `workflow_dispatch`，无 `pull_request_target`。
- 工作流级 `concurrency` 为 `maintain-${{ github.ref }}`、`cancel-in-progress: false`；
  build job `timeout-minutes: 30`、deploy job `timeout-minutes: 10`。
- `build` 仅有 `contents: read`；`deploy` 仅有 `pages: write`、`id-token: write` 和
  checkout/目标判定所需的 `contents: read`。
- artifact 路径为 `dist`，部署 job 使用 `github-pages` environment 与 `pages` 并发组。
- 所有第三方 action 使用完整 SHA，无浮动的 `@vN`。
- 无凭证、token、PAT 或未固定 URL。

## 6. 受控环境发布（需授权）

在受控测试仓库执行，不修改生产 Pages：

1. 将 Pages Source 切换为 “GitHub Actions”，创建/确认 `github-pages` environment。
2. 推送合法内容到 `main`，观察 `build` 与 `deploy` 均成功，记录运行 URL、目标 SHA、
   `content_revision` 与 `page_url`。
3. 访问固定站点首页、`/skill-gallery/` 资源、四个旧 `#/skill/<slug>` 链接并刷新。
4. 注入非法内容（缺失附件/非法元数据），确认构建失败、无部署、旧站点仍可读。
5. 模拟部署失败（例如临时撤销 Pages 权限或让部署步骤失败），确认提交状态与部署状态分开显示，
   旧站点保持可用；用同一 commit 重跑，确认不新建内容提交、成功后状态为已发布。
6. 触发两次相邻运行，确认旧运行在部署前被标记 `superseded`，旧快照不覆盖新快照。
7. 以未授权身份尝试触发，确认无写入、无部署副作用。
8. 恢复演练：在隔离副本对一次内容提交生成 `git revert` 恢复提交，重新构建/发布，确认 slug、
   旧链接和单版本保持；不 force push、不改写历史。
9. 回归取用：复制原文（含 frontmatter）、单文件/目录 ZIP/附件下载摘要、详情/列表分享和
   当前单版本；记录结果，受控站点不可用时只做隔离构建等价检查并记未运行。

## 7. 记录与报告

在 `specs/003-validate-build-publish/validation/` 记录实际命令、退出码、测试数量、扫描结果、
运行 URL、目标 SHA、状态和未运行项。未获得授权或未实际执行的生产 Pages 启用、环境审批、
MIME/缓存和线上回滚必须明确写为未运行，不能以本地预览或工作流文件存在代替。
