# 生产 Pages 启用与首次发布记录

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 合并 US-002～US-005 后，将生产 Pages Source 从 `legacy` 切换为 GitHub Actions，并由
`maintain.yml` 完成首次真实发布；记录回滚命令与未运行项。生产仓库设置变更经用户授权。
**环境**: GitHub 仓库 `chengxuan2002-droid/skill-gallery`，runner `ubuntu-24.04`、Node 26.3.0；
操作端 Windows 11、Node 22.21.0。

## 1. 合并与切换

| 步骤 | 结果 |
|---|---|
| PR #1（US-002+US-003） | merge commit `351a183132ea6dcfee6b35c4f202e9951290e210` |
| PR #2（US-004，重定向 base main） | merge commit `54524052e935b635020d5791f4f256d9f596427f` |
| PR #3（US-005） | merge commit `96578b94db0f4f5d42b53f0708a77a412a360fdc` |
| PR #4（站点监测索引 schema 修正） | merge commit `4ef344707f3421b7adf6af52b127370a43f99d35` |
| Pages 切换前 | `build_type=legacy`、`source=main:/`、`status=built` |
| 切换命令 | `gh api --method PUT repos/chengxuan2002-droid/skill-gallery/pages -f build_type=workflow` |
| 切换后 | `build_type=workflow`、`status=built`、`html_url=https://chengxuan2002-droid.github.io/skill-gallery/` |

`github-pages` environment 已存在，deployment branch policy 仅允许 `main`；未修改分支保护（main
原本未保护）或 environment 审批。

## 2. 首次真实发布

| 运行 | 目标提交 | 结果 |
|---|---|---|
| [42396751499](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/42396751499) | `351a183` | build 成功；deploy 因后续提交超前而跳过（superseded） |
| [42396785034](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/42396785034) | `5452405` | build 成功；deploy 跳过（superseded） |
| [42396936423](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/42396936423) | `96578b9` | 切换 Source 后 build/deploy 均成功 |
| [42397297833](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/42397297833) | `4ef3447` | build/deploy 均成功（监测修正后重发同一快照） |

切换前 legacy Pages 会按 `main:/` 自动构建根目录；合并期间曾短暂提供根目录版本（旧
`assets/search-index.json` schema），切换为 GitHub Actions 后由 `dist` 覆盖。

## 3. 线上检查

| 检查 | 结果 |
|---|---|
| `contentRevision` | `faa0f345a85673f60fda1d4cb3b61594b242ae631ab89b264387eec6875c429a` |
| 索引 | `schemaVersion=1`、4 个 slug |
| 首页 | HTTP 200、1,623 字节、包含“管理”外链与 `id="app"` |
| `assets/app.js` | HTTP 200、`application/javascript`、6,104 字节 |
| `assets/style.css` | HTTP 200、`text/css` |
| 详情 | 四个 slug 的 `details/<slug>.json` 均可读，`contentRevision` 与索引一致，`digest` 匹配 |
| 目录 ZIP | `downloads/handoff-codex.zip` HTTP 200、`application/x-zip-compressed`、3,033 字节 |
| 站点监测 | `npm run monitor:site` 通过（修正索引 schema 后） |
| 旧链接 | 索引 slug 对应 `#/skill/<slug>`；Hash 路由由前端处理，未做服务端断言 |

## 4. 回滚与未运行

回滚候选（未执行）：将 Pages Source 改回 legacy 并重新指向 main 根目录：

```text
gh api --method PUT repos/chengxuan2002-droid/skill-gallery/pages \
  -f build_type=legacy -f 'source[branch]=main' -f 'source[path]=/'
```

未运行/未验证：

- 生产 environment 审批（当前仅 branch policy，无 required reviewers）。
- 生产部署失败注入、旧站保留与同提交重跑（受控 POC-002 已有证据，生产未重复）。
- 浏览器中的 Hash 旧链接/刷新、移动端、Safari。
- 线上 MIME/缓存策略、CDN 行为与直接资源安全的完整审计。
- 每小时 `site-monitor` 工作流在修正合并后的首次定时运行；以 GitHub 运行记录为准。
