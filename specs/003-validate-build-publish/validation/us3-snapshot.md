# US1 发布快照验收（T011、T013）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: T011 隔离构建与产物校验；T013 重复构建稳定性。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线仍为 Node 26.3.0/npm 11.16.0）。

## 1. 隔离项目

- 从工作区复制 `index.html`、`.nojekyll`、`assets/`、`skills/`、`catalog/` 到系统临时目录，
  未复制工作区 `dist/`，未执行收录 Skill 的脚本。
- 使用 `scripts/lib/build-site.js` 生成临时 `dist/`；结束删除临时目录。
- 正式四项 slug：`code-review-assistant`、`handoff-codex`、`refactoring-workflow`、
  `superpower-systematic-debugging`。

## 2. T011 构建与 publish-check

| 项 | 结果 |
|---|---|
| 构建 | `ok=true`，`cleanup_status=complete` |
| `contentRevision` | `f8143ad0059b30bd1404c4ef9d05f40559525ecbdcb47d2a8b2dabdbb032006d` |
| manifest / 索引 / 四个详情 revision | 全部相同（4/4 detail 的 `digest_match=true`） |
| `node scripts/publish-check.js artifact --dist <临时 dist>` | exit `0`；`status=verified`，`files=25`，`diagnostics=[]` |
| 白名单/额外文件 | 通过；产物仅含 `index.html`、`.nojekyll`、`assets/`、`details/`、`downloads/`、`skills/`、`manifest.json` |
| 工作区 `dist/` | 未改动，仍为 `contentRevision=068cd50d...`、21 个产物、4 个 skill |

## 3. T013 重复构建

对同一隔离项目连续构建两次：

| 项 | 结果 |
|---|---|
| 第一次/第二次构建 | 均 `ok=true` |
| `contentRevision` | 两次均为 `f8143ad0059b30bd1404c4ef9d05f40559525ecbdcb47d2a8b2dabdbb032006d` |
| artifact 集合/大小/SHA-256 | 两次一致（24 个 manifest artifacts） |
| `publish-check` | 第二次产物仍 `status=verified` |

## 4. 未运行与限制

- 未在 Node 26.3.0/npm 11.16.0、Linux/CI 或真实 GitHub Pages 上运行。
- 未修改 Pages 源、environment 或分支保护；未部署。
- 未重新运行 Safari/移动实机、生产 MIME/缓存或回滚验证。
