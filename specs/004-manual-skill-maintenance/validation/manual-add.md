# US-004 手动新增验收（T004）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在系统临时目录复制正式站点内容（`index.html`、`assets/`、`catalog/`、`skills/`），
依次新增单文件与目录型 Skill 及其 `catalog` 记录，调用现有构建并核对索引/详情/下载；不写工作区
`dist/`、不执行收录 Skill 的脚本、不推送或部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 步骤与命令

1. 复制正式站点内容到临时目录，保留 4 个现有 slug 与首页/前端资产。
2. 新增 `skills/manual-single.md` 与 `catalog/manual-single.json`
   （`content_path=skills/manual-single.md`），调用 `scripts/lib/build-site.js` 构建。
3. 在新项目上继续新增 `skills/manual-pack/SKILL.md`、`skills/manual-pack/references/note.md` 与
   `catalog/manual-pack.json`（`content_path=skills/manual-pack/SKILL.md`），再次构建。
4. 核对 `manifest.json`、`assets/search-index.json`、`details/<slug>.json`、原件下载与目录 ZIP；
   结束后删除临时目录。

验证脚本只在临时目录运行，未提交；构建调用与线上 `maintain.yml` 相同。

## 2. 单文件新增

| 检查 | 结果 |
|---|---|
| 构建 | `ok=true`，无诊断 |
| `contentRevision` | `0fea11504813ee709c94e66fdcfe67a6f33a093c3742858f49d6aae1ec5e01e0` |
| 产物文件数 | 26 |
| 索引包含 `manual-single` | 是 |
| 详情 `contentRevision` 与 manifest 一致 | 是 |
| 原件下载字节与源文件一致 | 是 |
| `download_sha256`/`download_size` 与实际字节一致 | 是 |

## 3. 目录型新增

| 检查 | 结果 |
|---|---|
| 构建 | `ok=true`，无诊断 |
| `contentRevision` | `50c6efad08e2532d146181f1a2dfbcc2bfbf6a428bfab2a8aaee73eb8c1c9356` |
| 产物文件数 | 30 |
| 索引包含 `manual-pack` | 是 |
| 详情 `contentRevision` 与 manifest 一致 | 是 |
| 主文档字节与源文件一致 | 是 |
| 下载 URL | `downloads/manual-pack.zip` |
| `download_sha256`/`download_size` 与 ZIP 一致 | 是 |
| ZIP 条目 | 2 个（`manual-pack/SKILL.md`、`manual-pack/references/note.md`），字节与源文件一致 |

## 4. 既有内容保持

| 检查 | 结果 |
|---|---|
| 原有 slug | `code-review-assistant`、`handoff-codex`、`refactoring-workflow`、`superpower-systematic-debugging` 全部保留 |
| 最终索引 slug 数 | 6（4 原有 + 2 新增），无重复 |
| 最终 `contentRevision` | `50c6efad08e2532d146181f1a2dfbcc2bfbf6a428bfab2a8aaee73eb8c1c9356` |

## 5. 未运行与限制

- 未在 GitHub 网页后台实际拖拽上传或触发 Actions；该部分留给受控仓库 T016。
- 未切换生产 Pages，未做真实发布；本记录只证明隔离构建与产物内容。
- 未在浏览器中查看新增条目的交互、分享或下载按钮；构建/索引/字节检查不替代浏览器验收。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
