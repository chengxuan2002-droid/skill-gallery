# Quickstart: US-004 管理员手动维护

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本指南只描述实施后的可执行验证步骤；字段、错误码与不变量见 [data-model.md](data-model.md) 和
[manual-maintenance 契约](contracts/manual-maintenance.md)。不包含生产 Pages 授权或真实发布承诺。

## 1. 前置条件

- Node 26.3.0、npm 11.16.0（以 `.node-version`、`package.json` 为准）；干净 checkout。
- 已安装固定扫描器：`npm run setup:security`（需要 uv 与网络）。
- 手动维护需要 GitHub 仓库写权限；访客无需账户。
- 生产 Pages 源切换与真实发布需单独授权；未授权时只做隔离副本与受控临时仓库验证。

```bash
npm ci
npm run setup:security
```

## 2. 管理入口检查

```bash
node --test tests/unit/site-entry.test.js
```

期望：页脚“管理”链接指向 `https://github.com/chengxuan2002-droid/skill-gallery`，使用
`rel="noopener"`；页面不存在登录表单、文件输入或上传按钮。

## 3. 合法新增（隔离副本）

在系统临时目录复制 `index.html`、`assets/`、`catalog/`、`skills/`、`.nojekyll` 与 `package.json`，
新增单文件 Skill：

```text
skills/manual-sample.md
catalog/manual-sample.json
```

记录至少包含 `schemaVersion=1`、`slug=manual-sample`、`display_name`、`description`、
`content_path=skills/manual-sample.md`，其余字段可为空数组或 `null`。构建：

```bash
ISOLATED_ROOT=/path/to/isolated node -e "require('./scripts/lib/build-site').buildSite({projectRoot: process.env.ISOLATED_ROOT, outputName: 'dist'}).then((r) => { console.log(JSON.stringify(r)); process.exit(r.ok ? 0 : 1); })"
```

期望：退出码 0、`status=built`；`dist/assets/search-index.json` 含 `manual-sample`，
`dist/details/manual-sample.json` 与 `dist/skills/manual-sample/<sha256>.bin` 存在且字节一致。

## 4. 非法批次（整批阻止）

在隔离副本删除该 Skill 的一个附件，或写入非法 `catalog` 字段后重新构建。期望：退出码非零、
诊断含 `E_MAIN_MISSING`/`E_SCHEMA`/`E_PATH`，且旧 `dist/` 文件集合与摘要不变。

## 5. 替换、下架与恢复

- **替换**：修改同 slug 原件与记录后重建；确认 `dist` 只有一个该 slug，旧附件不再出现，
  `downloads/<slug>.zip`（目录型）只包含新清单。
- **下架**：删除原件与 `catalog/<slug>.json` 后重建；确认索引、`details/<slug>.json`、
  `downloads/<slug>.zip` 均不存在，其他条目不受影响。
- **恢复**：在隔离 Git 仓库中用 `git revert` 生成恢复提交后重建；确认 `contentRevision` 回到
  基线、slug 与 `#/skill/<slug>` 链接保持。

## 6. 受控仓库手动发布（需授权）

在受控临时仓库（POC-002）用 GitHub 网页后台等价操作：

1. 上传单文件/文件夹并新增/编辑 `catalog/<slug>.json`，提交默认分支。
2. 观察 `maintain.yml` 运行：`build` 与 `deploy` 分开显示；成功后访问站点子路径与详情链接。
3. 提交一个非法批次，确认构建失败、无部署、旧站仍可读。
4. 显式替换与下架各执行一次，确认单版本与索引移除。
5. 记录运行 URL、目标提交、`contentRevision`、状态和未运行项。

生产 Pages 未切换时，第 6 步只可在受控仓库执行；不得把受控结果报告为生产发布。

## 7. 记录与报告

在 `specs/004-manual-skill-maintenance/validation/` 记录实际命令、退出码、测试数量、构建结果、
运行 URL 和未运行项。本地构建成功、提交成功或 PR 合并均不等于线上发布。
