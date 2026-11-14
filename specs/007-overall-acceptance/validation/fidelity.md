# US-007 保真检查（Demo-001 部分）

**日期**: 2026-11-14
**范围**: T006；生产公开原件和 ZIP 与本地收录原件的逐字节核对。完整保真验收仍由 T016 复核。

## 1. 生产索引

- URL：`https://chengxuan2002-droid.github.io/skill-gallery/`
- revision：`faa0f345a85673f60fda1d4cb3b61594b242ae631ab89b264387eec6875c429a`
- Skill 数量：4

## 2. 单文件

| slug | raw 字节 | 与本地原件 | 详情 SHA-256 |
|---|---|---|---|
| `code-review-assistant` | 1044 | 一致 | `756a8c91...` |
| `refactoring-workflow` | 1020 | 一致 | `9091ac22...` |
| `superpower-systematic-debugging` | 1222 | 一致 | `80fbf9b3...` |

## 3. 目录包

`handoff-codex`：

- ZIP：`downloads/handoff-codex.zip`
- 条目：3（`SKILL.md`、`agents/openai.yaml`、`scripts/create_handoff.sh`）
- 每个条目与 `skills/handoff-codex/` 本地原件字节一致
- ZIP SHA-256 与详情 `download_sha256` 一致：`57a94d447205...`

## 4. 边界

- 本次只核对当前生产 4 项；未覆盖新增/替换后的 ZIP 回归，后者由 T004 的构建夹具和 US-001/US-003 validation 覆盖。
- 未执行浏览器下载交互；只做 HTTP 字节与 ZIP 条目核对。
- 不把搜索文本或详情 HTML 当作原件；详情 `raw_url`/`download_url` 指向保真文件。
