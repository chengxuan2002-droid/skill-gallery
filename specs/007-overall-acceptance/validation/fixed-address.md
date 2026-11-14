# US-007 固定地址、旧链接与浏览器可达

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T014–T015；生产固定地址、`/skill-gallery/` 子路径、旧 hash 链接、详情/原件/ZIP 可达，
以及 US-002 的响应式、主题、键盘和减少动效证据复核。
**方式**: `npm run monitor:site`、只读 HTTP 请求和 `node --test` 分享链接测试；未写生产内容，
未在浏览器重跑交互。

## 1. T014 生产固定地址

### 1.1 首页与静态资源

```bash
npm run monitor:site
```

结果：`status=passed`，四个资源均为 HTTP 200、首次尝试通过：

| 路径 | 状态 | 类型检查 |
|---|---|---|
| `/` | 200 | `text/html`；标题和 `id="app"` 存在 |
| `assets/app.js` | 200 | JavaScript |
| `assets/style.css` | 200 | CSS |
| `assets/search-index.json` | 200 | JSON、`schemaVersion=1`、含 slug/digest |

### 1.2 索引与四项详情

生产索引：

- URL：`https://chengxuan2002-droid.github.io/skill-gallery/assets/search-index.json`
- `contentRevision`：`faa0f345a85673f60fda1d4cb3b61594b242ae631ab89b264387eec6875c429a`
- Skill 数量：4

| slug | 详情路径 | HTTP | `contentRevision` 与索引 |
|---|---|---|---|
| `code-review-assistant` | `details/code-review-assistant.json` | 200 | 一致 |
| `handoff-codex` | `details/handoff-codex.json` | 200 | 一致 |
| `refactoring-workflow` | `details/refactoring-workflow.json` | 200 | 一致 |
| `superpower-systematic-debugging` | `details/superpower-systematic-debugging.json` | 200 | 一致 |

### 1.3 原件与 ZIP

| 资源 | HTTP | 字节/清单 | 结果 |
|---|---|---|---|
| `code-review-assistant` raw | 200 | 1044 | SHA-256 与详情 `download_sha256` 一致 |
| `handoff-codex` raw（SKILL.md） | 200 | 2583 | SHA-256 与详情一致 |
| `handoff-codex` ZIP | 200 | 3033；3 个条目 | ZIP SHA-256 与详情一致；条目见 `fidelity.md` |
| `refactoring-workflow` raw | 200 | 1020 | SHA-256 与详情一致 |
| `superpower-systematic-debugging` raw | 200 | 1222 | SHA-256 与详情一致 |

所有资源 URL 位于 `/skill-gallery/` 前缀下；详情中的 `raw_url`、`download_url` 和文件 `url` 均为相对路径，
未出现绝对 URL 或越界路径。

### 1.4 旧 hash 链接与列表分享

- 四个既有详情地址 `#/skill/code-review-assistant`、`#/skill/handoff-codex`、
  `#/skill/refactoring-workflow`、`#/skill/superpower-systematic-debugging` 由 US-002 的浏览器证据覆盖；
  四个 slug 仍存在于当前生产索引。
- `#/?q=...` 列表分享地址由 `tests/unit/share-link.test.js` 覆盖：在 `/skill-gallery/` 下生成规范
  detail/list URL，查询、模式、筛选和排序参数编码，且不包含凭证。

本次定向测试：

```bash
node --test tests/unit/share-link.test.js tests/unit/list-view.test.js
```

结果：6 项通过、0 失败。未重新运行真实浏览器；旧链接的刷新/路由行为复用
`specs/002-search-detail-share-redesign/validation/us2-detail.md` 的浏览器证据。

## 2. 生产 MIME 与缓存补充

**日期**: 2026-11-14。使用只读 `curl -I` 检查当前生产响应头；未写生产内容。

| 资源 | 状态 | Content-Type | Cache-Control | 其他 |
|---|---|---|---|---|
| 首页 `/skill-gallery/` | 200 | `text/html; charset=utf-8` | `max-age=600` | `Last-Modified`、`ETag` |
| `assets/app.js` | 200 | `application/javascript; charset=utf-8` | `max-age=600` | `Last-Modified`、`ETag` |
| `assets/search-index.json` | 200 | `application/json; charset=utf-8` | `max-age=600` | `Last-Modified`、`ETag` |
| `details/code-review-assistant.json` | 200 | `application/json; charset=utf-8` | `max-age=600` | `Last-Modified`、`ETag` |
| `skills/code-review-assistant/<sha>.bin` | 200 | `application/octet-stream` | `max-age=600` | `Last-Modified`、`ETag` |
| `downloads/handoff-codex.zip` | 200 | `application/x-zip-compressed` | `max-age=600` | `Last-Modified`、`ETag` |
| 不存在的详情路径 | 404 | `text/html; charset=utf-8` | — | GitHub Pages 默认 404，不伪装成 JSON |

结论：直接原件使用 `application/octet-stream`，ZIP 使用 `application/x-zip-compressed`，详情/索引
使用 JSON；当前生产缓存策略为 600 秒。未验证 CDN 边缘缓存清除、浏览器强刷后的资源一致性或
完整资源安全审计，因此不把本项写成“缓存/直接资源安全已全部通过”。

## 3. T015 浏览器与可访问性证据复核

### 2.1 已有证据

| 证据 | 环境 | 覆盖 | 结果 |
|---|---|---|---|
| `specs/002-search-detail-share-redesign/validation/us2-accessibility.md` | Chrome 152 headless | 360/768/1440、明暗主题、键盘、减少动效、对比度 | 通过本地夹具 |
| `specs/002-search-detail-share-redesign/validation/us2-cross-browser.md` | Firefox 157.0、WebKit 27.2 | 布局、主题、键盘、减少动效、1,000 项/50 查询 | 通过本地夹具 |

关键复核点：

- 360/768px 无页面外横向溢出，筛选面板默认收起且可由键盘展开；1440px 为两栏列表/多列卡片。
- 浅色最低对比度 4.75:1，深色 6.7:1；正文和主要控件不低于 4.5:1。
- `prefers-reduced-motion: reduce` 下卡片过渡为 `0.01ms`，锚点滚动不为平滑滚动。
- 键盘可完成搜索、筛选、打开详情、复制链接、查看原文、下载 ZIP 和返回列表；焦点环为 2px 实线。
- 1,000 项/10 MiB 夹具的 50 查询 p95：Chrome 39.9ms、Firefox 48.0ms、WebKit 50.0ms；这是隔离
  夹具候选线，不是生产网络或设备承诺。

### 2.2 未运行与限制

- Safari 实机、移动实机、真实触摸手势和读屏器语音未运行；WebKit 27.2 是 Playwright 的 Windows
  构建，不等同于 Safari。
- 未在本次重新运行生产浏览器交互，也未验证生产 MIME/缓存（见 T018）。
- 未验证真实生产设备性能和网络条件；AC-013/AC-015 的证据仍限定为本地/受控环境。
