# US-001/US-002 取用回归（T032）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在系统临时目录复制正式站点内容并构建 `dist/`，回归原文（含 frontmatter）、单文件/目录
ZIP/附件下载摘要、详情/列表分享、四个旧链接和当前单版本；不修改工作区 `dist/`、不部署、不修改
生产 Pages。受控站点回归未执行。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0 未在本机复验）；
构建使用 `scripts/lib/build-site.js`，ZIP 读取使用锁定 `yauzl`。

## 1. 隔离构建

| 项 | 结果 |
|---|---|
| `contentRevision` | `f8143ad0059b30bd1404c4ef9d05f40559525ecbdcb47d2a8b2dabdbb032006d` |
| 产物文件数 | 24 |
| Skill 数 | 4 |
| 详情文件 | 4 个 JSON，slug 无重复（当前单版本） |
| 构建退出 | `ok=true`，无诊断 |

## 2. 原文与下载保真

| 检查 | 结果 |
|---|---|
| 原文复制 | 4 个 slug 的主文档在 `dist` 中与原件逐字节一致 |
| frontmatter | 4 个主文档均保留 `---` 起始的 frontmatter |
| 附件/文件清单 | `detail.files` 的 `path`、`size`、`sha256` 与原件一致；`download_name` 保持原文件名 |
| 单文件下载 | `code-review-assistant`、`refactoring-workflow`、`superpower-systematic-debugging` 的 `download_url` 等于 `raw_url`，摘要与原件一致 |
| 目录 ZIP | `handoff-codex.zip` 根目录为 `handoff-codex/`，3 个文件字节与原件一致；`download_size`/`download_sha256` 与 ZIP 实际字节一致 |
| 公开 URL | 每个 `detail.files[].url` 都存在于 `dist` 且摘要一致；清单与详情来自同一 `contentRevision` |

## 3. 详情、列表分享与旧链接

```text
node --test tests/unit/share-link.test.js tests/unit/app-routing.test.js tests/unit/list-view.test.js
```

结果：退出码 `0`；9 项通过、0 失败、0 跳过。覆盖详情分享的规范 URL、列表分享的查询/模式/筛选/排序
且不含凭证、直接用摘要作为内容身份、详情路由返回列表状态、复制失败时显示手动值。

隔离构建中确认：

| 检查 | 结果 |
|---|---|
| 四个旧链接 | `#/skill/code-review-assistant`、`#/skill/handoff-codex`、`#/skill/refactoring-workflow`、`#/skill/superpower-systematic-debugging` 对应详情文件均存在 |
| 列表入口 | 索引含同一 4 项，`detail_url` 指向存在的详情 JSON |
| 单版本 | 索引与 `details/` 均无重复 slug 或历史版本文件 |

## 4. 未运行与限制

- 受控站点回归未执行：POC-002 的内容已在 T025 被临时修改，生产 Pages 未授权切换；本轮只做隔离构建
  等价检查。
- 未在真实浏览器复验刷新、直接打开详情、复制交互或移动端；这些仍以 US-002 已记录的浏览器证据为准。
- 未验证线上 MIME、缓存或子路径的实际响应；隔离构建只证明产物与前端模块未被本故事改变。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
