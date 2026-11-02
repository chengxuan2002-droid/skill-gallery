# C-04：静态读取、旧链接与完整取用

版本：1；仅 US-001 必要读取/展示，不引入 FR-002 搜索升级或完整详情改版。
遵循 [数据模型](../data-model.md)、[C-03 输出布局](content-pipeline.md)、四份 0.2 文档与宪章 1.0.0。

## 1. 公共 JSON

### assets/search-index.json

顶层为对象，不再是旧数组：

~~~json
{
  "schemaVersion": 1,
  "contentRevision": "SHA256_HEX_PLACEHOLDER",
  "skills": []
}
~~~

每项包含 slug、digest、display_name、description、tags、platforms、author、declared_version、
homepage_url、repository_url、source_type、usage、notes、license、created_at、updated_at、
content_text、detail_url、raw_url、download_url。字段类型按数据模型；slug 唯一。
前端把 display_name 映射到既有列表与搜索需要的 name，不要求重写现有搜索算法。
未知 schemaVersion、旧数组或损坏 JSON 进入 load_failed，不当成空库。

### details/<slug>.json

包含 schemaVersion、contentRevision、slug、digest、上述公开显示字段及 field_sources、skill_name、
body_html、raw_url、files、directories、download_url、download_name、download_sha256、download_size。
files 为 PublicFile 数组：path、size、sha256、executable、download_name、url，可选 media_url。
directories 仅空目录相对路径。单文件 files 只有一个原名 .md；目录文件清单以 SKILL.md 为入口。
没有原文字符串副本；原文从 raw_url 的完整字节取得，避免 JSON/文本归一化改变内容。

对所有公开字符串按文本插入；仅 body_html 可以进入 HTML 片段位置，因为它已完成清理和 URL 映射。
不得将原始 notes、作者、名称或地址通过字符串插入未经转义的 HTML 属性。

### manifest.json

包含 schemaVersion、contentRevision、skills（各 slug/digest/原件清单/空目录）和 artifacts（path/size/sha256）。
artifacts 覆盖除 manifest 自身外所有文件，只允许 C-03 列明的公开目录/入口；不公开完整 catalog 或 source_tracking。
摘要字符串实际必须是 64 位十六进制；上述占位示例只表达外层形状，不是可验收的发布数据。

## 2. 站点基址、路由与快照一致性

- 站点基址为当前文档目录，忽略 Hash；所有内部 URL 相对此基址解析。项目路径是 /skill-gallery/，禁止写成 /assets 或 /downloads 根路径。
- slug 与路径段分别正确编解码，路径不允许 ..、绝对地址或凭证参数。不要用 Hash 的相对路径当资源根。
- 保留以下路由，直接打开/刷新/复制后身份一致：

~~~text
/skill-gallery/#/skill/superpower-systematic-debugging
/skill-gallery/#/skill/code-review-assistant
/skill-gallery/#/skill/refactoring-workflow
/skill-gallery/#/skill/handoff-codex
~~~

- 空 Hash 或既有列表入口继续可用。未知/非法 slug 显示 not_found，不能回退展示其他 Skill。
- index 与 detail 必须 schemaVersion/contentRevision 一致，detail.slug/digest 必须与索引记录一致；否则 snapshot_mismatch，提示刷新，不提供混合快照下载。
- raw/附件/ZIP 使用文件摘要或清单校验；缺失或摘要不符停止对应操作并提示不可用。不能在 404 时保存错误页为原件。
- 索引与详情读取避免缓存旧响应；前端还要忽略快速切换路由后的过期异步响应，不能把 A 的原文放进 B 的详情。
- 构建器与读端 schema 同次交付；不要求旧脚本读取新索引。跨生产发布的缓存策略/陈旧 artifact 不覆盖问题留 US-003，本轮不声称已经发布验证。

## 3. 安全详情

- 展示正文中的代码、列表、表格与中文；清除 script、iframe、object/embed、表单、事件、style 和危险 URL，固定标签/属性白名单，不依赖浏览器自行忽略脚本。
- 允许的正文标签以标题 h1～h6、段落/换行/分隔、列表、引用、强调、pre/code、表格、a、img 为限；源属性仅 href/rel/target、src/alt/title 和必要语言类。所有原件 id/name 均移除；唯一 id 例外是下方由构建器生成并核对的标题 ID，不接受原件 onclick 等属性。
- 外链仅无账号密码的 http/https，打开新窗口时带 noopener/noreferrer。本文锚点按下方规则映射，原始文件字节保持不变。
- 相对附件链接映射到清单中的下载入口。不能把原始 HTML/SVG 插入 innerHTML/iframe 或作为同源活动页面导航。SVG/其他不支持的本地图片显示 alt 与附件下载入口；安全栅格图片走 media_url。
- 原始脚本只可作为原件或 ZIP 成员交付，不执行、不导入、不安装。普通 Markdown 附件作为文件下载，不隐式执行其“使用说明”。

<a id="heading-anchors"></a>

### 标题 ID 与片段映射（I1 修订，policyVersion=1）

1. 先渲染并清理，移除全部源 id/name（即使原值形似合法受控 ID）。再按清理后保留的 h1～h6 的出现顺序，
   从 1 生成 skill-heading-1、skill-heading-2 等 ID；只允许这些标题各自拥有本次生成的 ID。
   后续清理/自检必须保留这些对应值，其他元素一律没有 id/name；不按原件属性选择 ID。
2. 为每个标题的可见纯文本建立别名：实体解码后做 NFC、ASCII 大写转小写、连续空白转一个连字符，
   删除 Unicode 字母/数字、下划线、连字符之外的字符；空结果用 section。
   按出现顺序分配未使用别名：先尝试基名，冲突则追加 -1、-2 等直至唯一。
   这是本站固定规则，不宣称完整复刻第三方站点的标题算法；映射仅在构建内使用，不新增公开 JSON 字段或依赖。
3. path 为空或解析后指向主文档自身的片段链接，片段只百分号解码一次并做 NFC 后按别名查找；
   已存在别名重写为对应 #skill-heading-N，空片段定位正文顶部。原文中的 URL 不回写。
   不存在/非法编码的片段不按缺附件处理：移除 href，并显示“未找到本文锚点”；不得读取其他文件或令整批失败。
   其他附件的片段不扩展成新 SPA 页面。
4. 详情内本文锚点由可信点击处理阻止默认 Hash 导航，仅在当前正文标题集合内定位/滚动；
   不替换现有 #/skill/<slug>，不增加新的标题分享路由，不对全页面任意 ID 做跳转。
5. 固定用例：两个“快速开始”分别得到别名 快速开始、快速开始-1 和 ID skill-heading-1/2；
   “API Token”得到 api-token；另覆盖空标题、标点/行内代码、自然后缀碰撞、编码中文片段、
   原件伪造 id/name、未知片段，以及最终清理后 ID 仍在且点击后技能路由不变。

## 4. 查看原文、复制、下载

| 操作 | 数据源与成功条件 | 失败行为 |
|---|---|---|
| 查看完整原文 | raw_url 响应成功、大小/sha256 一致，严格 UTF-8 解码；包含 frontmatter 和完整正文 | 显示原文不可用，不用 content_text 兜底 |
| 复制原文 | 已校验完整文本，保留 BOM/换行内容，不 trim，不经过 textarea 再重建；等待剪贴板 API 实际完成 | 明确失败，保留安全文本区供手动选取，不显示“已复制” |
| 下载单文件 | 原始主文档字节，原始 .md 文件名，大小/摘要正确 | 明示不可用，不保存错误响应 |
| 下载完整目录 | downloads/<slug>.zip，解包后原根目录/路径/字节/许可一致 | 无响应或摘要错误则失败，无成功提示 |
| 下载附件 | PublicFile.url 原字节，Blob 类型 application/octet-stream，download_name 原文件名 | 失败保留详情，不直接导航到活动文件 |
| 复制分享链接 | 固定站点基址加 #/skill/<slug>；仅成功写剪贴板后提示 | 明示失败并提供可手工复制的链接 |

Blob URL 仅作已校验字节的下载句柄，按安全时机回收；它不属于允许原文嵌入的 URL scheme。
目录 ZIP 的执行位为规范化 0644/0755；取用是下载，不自动运行脚本。
浏览器无法证明用户最终写入磁盘，提示仅表示资源已验证且浏览器已发起下载，不能宣称已安装。

## 5. 可观测状态与本轮边界

最少区分 loading、ready、not_found、load_failed、snapshot_mismatch、raw_unavailable、
copy_failed、download_failed。错误区提供重试/返回或手动复制方式；不给访客内部堆栈、私有路径或密钥值。
未知作者、版本、官方地址显示“未提供”，不隐藏成伪造默认值。

复制/下载操作在合法详情基础上验收，不改主题、筛选信息架构或整站响应式设计。
本地 preview 只服务 dist，/skill-gallery/ 之外不映射项目文件；.bin 为 application/octet-stream，
网页 MIME 按明确类型返回，原件不做 HTML 内容嗅探。生产 Pages 响应头与直接资源访问须在 US-003 发布前复核，
不能以本地响应头推断线上已经安全。

追溯：FR-004/011、NFR-001/003/006；AC-002、AC-005 链接/反馈、
AC-012 预览安全、AC-014 本地前缀与同快照支撑。
