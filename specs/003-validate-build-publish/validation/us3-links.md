# US1 子路径与旧链接验收（T012）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: T012；隔离四项 `dist/` 的 `/skill-gallery/` 子路径、详情/原件/下载和旧 Hash 链接。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（未冒充 Node 26.3.0）。

## 1. 隔离预览

使用 T011 的四项隔离构建 `dist/`，通过 `scripts/preview.js` 的 `createPreviewServer`
以 `/skill-gallery/` 前缀探测：

| 路径 | 状态 | Content-Type | 字节 |
|---|---|---|---|
| `/skill-gallery/` | 200 | `text/html; charset=utf-8` | 1,417 |
| `assets/app.js` | 200 | `application/javascript; charset=utf-8` | 6,104 |
| `assets/search-index.json` | 200 | `application/json; charset=utf-8` | 8,699 |
| `details/code-review-assistant.json` | 200 | `application/json; charset=utf-8` | 2,836 |
| `details/handoff-codex.json` | 200 | `application/json; charset=utf-8` | 5,318 |
| `details/refactoring-workflow.json` | 200 | `application/json; charset=utf-8` | 2,798 |
| `details/superpower-systematic-debugging.json` | 200 | `application/json; charset=utf-8` | 3,124 |
| `skills/code-review-assistant/*.bin` | 200 | `application/octet-stream` | 1,044 |
| `downloads/handoff-codex.zip` | 200 | `application/octet-stream` | 3,033 |
| `skills/refactoring-workflow/*.bin` | 200 | `application/octet-stream` | 1,020 |
| `skills/superpower-systematic-debugging/*.bin` | 200 | `application/octet-stream` | 1,222 |

11 个详情/原件/下载响应全部为 200；未出现 404 或根路径 `/assets/...` 依赖。

## 2. 旧 Hash 链接与刷新

Hash 路由不会发送到 HTTP 服务器；本次隔离预览只能确认 `/skill-gallery/` 首页和详情 JSON 可读。
四个旧 `#/skill/<slug>` 链接的客户端行为和刷新后同一 Skill 身份复用 US-002 已记录证据：

- [us2-detail.md](../../002-search-detail-share-redesign/validation/us2-detail.md) 的
  “四个旧详情链接”表：四个 `#/skill/<slug>` 首次打开和刷新后标题/Hash 不变（Edge 156 headless）。
- [us2-cross-browser.md](../../002-search-detail-share-redesign/validation/us2-cross-browser.md)
  记录 Firefox 157.0 / WebKit 27.2 的补充验收；Safari/移动实机仍未验证。

本任务未重新运行浏览器；不把 HTTP 200 当作 Hash 路由已复验。

## 3. 未运行与限制

- 未在 Node 26.3.0/npm 11.16.0、Linux/CI 或真实 GitHub Pages 上运行。
- 未重新运行 Safari/移动实机、生产 MIME/缓存或回滚验证。
- 旧 Hash 链接的当前浏览器复验引用 US-002 证据，未在本次重新执行。
