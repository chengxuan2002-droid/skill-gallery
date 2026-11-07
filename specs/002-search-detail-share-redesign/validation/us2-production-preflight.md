# 生产 Pages 只读预检

日期：2026-11-06。范围：US-002 遗留的生产 MIME/缓存/直接资源风险；不执行部署、回滚或发布。
本记录不能替代 US-003 的生产发布验收。

## 当前线上响应

对 `https://chengxuan2002-droid.github.io/skill-gallery/` 只读请求：

| 资源 | 状态 | Content-Type | Cache-Control | 其他 |
|---|---|---|---|---|
| `/` | 200 | `text/html; charset=utf-8` | `max-age=600` | `Access-Control-Allow-Origin: *` |
| `assets/app.js` | 200 | `application/javascript; charset=utf-8` | `max-age=600` | 同上 |
| `assets/style.css` | 200 | `text/css; charset=utf-8` | `max-age=600` | 同上 |
| `assets/search-index.json` | 200 | `application/json; charset=utf-8` | `max-age=600` | 同上 |

四个资源的 MIME 与当前线上版本匹配；响应未包含 `X-Content-Type-Options: nosniff` 或 CSP。

## 直接资源

当前线上仍是旧版内容，直接请求：

| 路径 | 状态 | Content-Type | `nosniff` / `Content-Disposition` |
|---|---|---|---|
| `skills/handoff-codex/SKILL.md` | 200 | `text/markdown; charset=utf-8` | 无 / 无 |
| `skills/handoff-codex/agents/openai.yaml` | 200 | `text/yaml` | 无 / 无 |

这说明 GitHub Pages 对直接请求的原件按其扩展名返回文本类型，平台没有提供本项目可设置的
`nosniff` 或强制下载响应头。旧版线上站点不包含 US-002 的 `.bin`/ZIP 产物，因此这些新产物的生产
MIME、缓存和直接访问行为仍未被验证。

## 风险结论

- HTML/JS/CSS/JSON 的当前线上 MIME 正确，缓存为 10 分钟；US-002 新构建仍需部署后再验。
- GitHub Pages 平台未提供自定义安全响应头；`nosniff`/CSP/强制下载不能由当前仓库配置解决。
- 新 `.bin`、ZIP 和附件的生产 MIME/直接访问需在 US-003 发布验收时实际检查；不能把本地 preview 结果
  当成生产结果。
- 部署失败回滚未验证：当前没有维护/部署 workflow，也没有生产发布授权；不能用本地 dist 恢复替代
  Pages 部署回滚。此项留待 US-003 及生产授权。
