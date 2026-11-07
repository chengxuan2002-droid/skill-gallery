# Phase 1 Data Model: US-002 检索、详情、分享与视觉改版

**Date**: 2026-11-05 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本故事不新增持久化存储，不改变 catalog、搜索索引或详情 JSON 的 `schemaVersion=1` 契约。
下列模型是前端检索状态、派生视图和可分享地址的逻辑模型；现有索引/详情字段仍是唯一数据来源。

## 1. SearchState

| 字段 | 类型 | 规则 |
|---|---|---|
| `query` | string | 用户输入；空白视为无关键词；不做 HTML 插入；最长长度由输入控件限制，不写入持久存储 |
| `mode` | `fuzzy` \| `exact` | 缺省 `fuzzy`；非法值回退 `fuzzy` |
| `tags` | string[] | 多选；去重；同维 OR |
| `platforms` | string[] | 多选；去重；同维 OR |
| `sourceTypes` | string[] | 多选；去重；同维 OR |
| `authors` | string[] | 多选；去重；同维 OR |
| `sort` | `auto` \| `name` \| `updated` | 缺省 `auto`；非法值回退 `auto`；显式选择在查询/筛选变化后保持 |

**派生规则**：

- `auto` 且有关键词时按相关度；`auto` 且无关键词时按 `updated_at` 倒序；`name` 按显示名称；
  `updated` 按 `updated_at` 倒序；同分/同日期按 slug 升序。
- 空字符串、`null`、缺失筛选值不当作“全部”；不匹配该维度条件，清除条件后重新出现。
- 搜索状态只存在于当前地址和运行时；不写入 catalog 或公开内容。

## 2. SearchDocument

来自现有 `dist/assets/search-index.json` 的单个 `skills` 项；运行时派生规范化字段，不新增公开字段。

| 字段 | 来源 | 用途 |
|---|---|---|
| `slug` | 索引 | 稳定身份、结果链接、排序兜底 |
| `display_name` / `description` | 索引 | 显示、名称/简介检索与权重 |
| `tags` / `platforms` | 索引 | 卡片、筛选、检索 |
| `author` / `source_type` | 索引 | 筛选、详情元数据 |
| `usage` / `notes` | 索引 | 适用场景与用法、备注、检索 |
| `declared_version` / `updated_at` | 索引 | 卡片/详情版本与更新时间 |
| `content_text` | 索引 | 正文纯文本检索；不得作为原文导出 |
| `digest` | 索引 | 详情快照校验与内容标识 |
| `detail_url` / `raw_url` / `download_url` | 索引 | 详情与取用入口 |

**派生字段**：`normalizedName`、`normalizedDescription`、`normalizedTags`、`normalizedPlatforms`、
`normalizedAuthor`、`normalizedSourceType`、`normalizedUsage`、`normalizedNotes`、`normalizedContentText`。
规范化使用 Unicode NFC、转小写和空白折叠；派生字段只在内存中存在。

## 3. SearchResult

| 字段 | 类型 | 规则 |
|---|---|---|
| `slug` | string | 唯一；与索引一致 |
| `score` | number | 精准命中权重或 MiniSearch 分数加连续子串加权 |
| `matchedFields` | string[] | 可选，用于调试/测试；不进入公开产物 |
| `document` | SearchDocument | 结果卡片和详情链接的运行时引用 |

**排序**：先按有效排序规则；相关度/名称/更新时间相同时按 slug 升序。搜索结果先去重，再应用筛选。

## 4. FilterOptions

| 字段 | 类型 | 规则 |
|---|---|---|
| `tags` | `{value, count}[]` | 当前索引实际值；按稳定顺序排序 |
| `platforms` | `{value, count}[]` | 当前索引实际值 |
| `sourceTypes` | `{value, count}[]` | 当前索引实际值；缺失值不生成选项 |
| `authors` | `{value, count}[]` | 当前索引实际值；缺失值不生成选项 |

选项值必须与索引中的原始字符串一致；显示文本必须按纯文本处理。筛选选项是派生数据，不写入 catalog。

## 5. RouteState / ShareAddress

| 状态 | 表示 | 规则 |
|---|---|---|
| 列表 | 空 Hash、`#/` 或 `#/?q=...&mode=...&tag=...&platform=...&source=...&author=...&sort=...` | 空 Hash 与 `#/` 等价；参数白名单；重复键为数组；`mode=fuzzy`、`sort=auto` 可省略 |
| 详情 | `#/skill/<slug>` | 稳定身份；不附加查询参数；slug 由 `encodeURIComponent` 处理 |
| 列表返回位置 | `sessionStorage` 中的列表 Hash | 仅用于当前浏览会话的返回；不进入公开分享身份 |

**校验**：

- 未知参数安全忽略；非法 `mode`/`sort` 回退默认；重复/空筛选值去重后忽略。
- 查询和筛选值不得包含凭证、token、内部路径或管理信息；生成 URL 时使用标准编码。
- URL 解析与构建必须可往返：`build(parse(hash))` 不改变有效状态；非法输入不导致页面崩溃。
- 详情分享地址始终由当前文档目录作为基址并去掉 Hash 后拼接，保持 `/skill-gallery/` 子路径。

## 6. DetailViewModel

由现有 `details/<slug>.json` 映射，不新增字段。

| 展示区 | 数据来源 | 规则 |
|---|---|---|
| 名称/简介 | `display_name` / `description` | 缺失显示 slug/“未提供” |
| 标签/平台 | `tags` / `platforms` | 纯文本徽标；可为空 |
| 声明版本 | `declared_version` | 存在时显示；不要求 SemVer |
| 内容标识 | `digest` 前 12 位 | 声明版本缺失时作为版本区域的内容身份；与声明版本分开标注 |
| 作者 | `author` | 缺失“未提供” |
| 来源类型 | `source_type` | 缺失“未提供” |
| 官方主页/开源地址 | `homepage_url` / `repository_url` | 分别展示；仅 http/https；缺失“未提供” |
| 更新时间 | `updated_at` | 站内记录最近实质更新时间；缺失“未提供” |
| 适用场景与使用方法 | `usage` | 站点说明区；缺失“未提供” |
| 备注 | `notes` | 站点说明区；缺失隐藏或“未提供” |
| 原文 | `body_html` | 仅已清理 HTML；不从 `content_text` 重建 |
| 附件 | `files` / `directories` | 路径、大小、可执行位；下载仍走 US-001 校验 |
| 许可 | `license` | 缺失“未提供” |

## 7. UIState

| 视图 | 状态 | 触发/恢复 |
|---|---|---|
| 列表 | `loading` | 索引加载中；不可显示空库 |
| 列表 | `ready` | 有结果 |
| 列表 | `empty_library` | 索引无 Skill；提供说明，不伪造筛选结果 |
| 列表 | `empty_results` | 有 Skill 但条件无结果；显示清除条件 |
| 列表 | `load_failed` | 索引请求/解析失败；提供重试，不显示空库 |
| 详情 | `loading` / `ready` | 详情请求中/成功 |
| 详情 | `not_found` | slug 不存在；提供返回列表 |
| 详情 | `load_failed` | 详情请求/解析失败；提供重试 |
| 详情 | `snapshot_mismatch` | 索引与详情 `contentRevision`/`digest` 不一致；提示刷新 |
| 动作 | `copy_failed` | 剪贴板拒绝；保留手动复制文本，不提示成功 |
| 动作 | `raw_unavailable` / `download_failed` | 资源不可用/摘要不符；不保存错误页，不提示成功 |

**转换**：列表 `loading → ready|empty_library|load_failed`；筛选变化只在 `ready`/`empty_results` 间转换；
详情 `loading → ready|not_found|load_failed|snapshot_mismatch`；动作反馈独立于详情主体状态，可重复触发。

## 8. 关系与约束

- 一个索引对应 N 个 `SearchDocument`；一个 `SearchState` 产生 0～N 个 `SearchResult`；
  每个 `SearchResult.slug` 对应一个详情文档。
- 一个详情对应一个规范详情分享地址；列表状态产生一个可恢复的列表查询地址。
- `SearchState`、`SearchResult`、`FilterOptions`、`DetailViewModel` 均为运行时派生对象，不写入 catalog、
  `dist` 以外的位置或 Git。
- 现有 catalog/索引/详情 schema 的必填、可空、所有权、快照和内容身份规则继续由 US-001 的 M-01/M-02/M-03
  校验；本故事只补充前端参数和展示规则。

## 9. 验证矩阵

| 模型 | 必测 |
|---|---|
| SearchState | 默认值、去重、非法 mode/sort、URL 往返、筛选缺失值 |
| SearchDocument | 字段完整/缺失、规范化、正文不用于导出 |
| SearchResult | 精准/模糊/短语/中文、名称优先、同分 slug |
| FilterOptions | 实际值、计数、无值维度、同维 OR/跨维 AND |
| RouteState | 列表/详情路由、旧链接、编码、返回位置 |
| DetailViewModel | 字段来源、缺失“未提供”、版本/内容标识、站点说明与原文分区 |
| UIState | 空库/空结果/加载失败/未知 slug/快照不一致/复制失败 |
