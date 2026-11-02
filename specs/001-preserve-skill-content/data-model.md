# US-001 数据模型

依据四份 0.2 主文档、宪章 1.0.0、[spec](spec.md) 与 [research](research.md)。这里只定义 US-001；版本指 schema、内容身份、原件声明三个不同概念，不混用。

## 1. SkillOriginal / FileEntry：受控原件快照

| 字段 | 类型与规则 |
|---|---|
| slug | 稳定身份，来自图库记录 |
| content_path | 项目相对 POSIX 路径；仅 skills/<slug>.md 或 skills/<slug>/SKILL.md；路径保持现状 |
| kind | 根据 content_path 推导 single_file 或 directory，不重复手工配置 |
| root_name | 单文件为原文件名；目录为原目录名，作为 ZIP 根 |
| files | 按原相对路径排序的 FileEntry；目录相对其 Skill 根，单文件只有自身 |
| directories | 原目录内空目录相对路径，保留在 ZIP 中；不把目录当空文件 |
| digest | SHA-256 内容身份，覆盖原路径、逐文件字节摘要、执行位和空目录；不依赖 version |

FileEntry：path 为未经重命名的相对 POSIX 路径；bytes 为内部 Buffer；size 为原始字节数；
sha256 为 64 位小写十六进制；executable 为布尔。Buffer 不序列化进入搜索索引。
主文档必须是非空、合法 UTF-8；派生文本识别 BOM/换行，原始 Buffer 不变。二进制附件不按文本解码。

digest 使用固定格式的 JSON 数组：版本标记、按 UTF-8 路径字节排序的 [path, sha256, executable] 文件项和排序后的空目录项，再对其 UTF-8 字节做 SHA-256。结构化编码避免简单路径拼接产生歧义。文件系统 mtime、当前日期、Git HEAD 不参与内容 digest。

关系：一个 SkillOriginal 属于一个 CatalogRecord；同一路径不能被两项记录拥有。一个文件可有原件资源及媒体副本，但都指向同一源字节，不代表两个版本。

## 2. CatalogRecord：站内记录

存储为 catalog/<slug>.json，schemaVersion=1，构建只读。字段命名沿用 DEC-003 与上游 9.1。

| 字段 | 类型 / 必需性 | 含义 |
|---|---|---|
| schemaVersion | 必需整数，固定 1 | 图库契约版本 |
| slug | 必需非空字符串 | 1～64 位小写 ASCII 字母、数字、单连字符分段；文件名必须一致 |
| display_name / description | 必需非空字符串 | 显示名称和简介；迁移/样例生成时可从合法原件提取 |
| content_path | 必需非空字符串 | 关联唯一主文档 |
| tags / platforms | 字符串数组，缺省 [] | 分类、平台；无额外业务必填条件 |
| author / homepage_url / repository_url | 可选 string 或 null | 缺省从原件约定字段读取；显式 null 表示明确未提供 |
| declared_version | 可选 string 或 null | 原件声明或显式覆写，不要求 SemVer，不是 digest |
| source_type | 可选 string 或 null | 来源分类说明；不等同于已配置同步 |
| usage / notes / license | 可选 string 或 null | 站内用法、备注和许可说明 |
| created_at / updated_at | 可选 YYYY-MM-DD 或 null | 已知业务日期；缺失不补当前日期 |
| source_tracking | null 或上游定义的对象 | 本轮迁移全部为 null；可保留已合法配置对象，但不发远程请求或报告自动更新成功 |
| allowed_dot_paths | 字符串数组，缺省 [] | 本次细化的安全点文件精确路径准入，不可越过凭证禁止项 |

未知 catalog 顶层字段报类型/契约错误，避免拼写错误被忽略；source_tracking 的扩展不随意发布给访客。
source_tracking 对象沿用上游 provider/repository/path/ref_policy/ref/enabled 与 last_synced_revision/last_synced_digest/synced_at 结构：GitHub provider、非空定位字段、branch/release/pinned 策略、布尔开关、可空同步结果；本轮仅校验结构，不实现 C-06。
必需字段不存在不能靠构建时临时推导生成成功；创建/迁移记录时先完成这些字段。上游“只有 name/description 的标准样例”指原件不必具有图库专属字段，并非免除独立图库记录。

### 合并与来源规则

1. 原件 YAML 的已知字段若存在，必须满足类型；不能用记录覆写来掩盖原件非法值。
2. slug、display_name、description、tags、platforms、usage、notes 由 catalog 控制。迁移先把既有同名站内字段复制到记录，随后编辑记录不回写原件。
3. author/homepage_url/repository_url/license/date 等：catalog 明确出现的合法值优先（包括 null）；未出现才读原件约定的同名字段，兼容原件 homepage/repository 别名。未命中为 null。
4. declared_version：显式 catalog 值优先，否则原件顶层 version，再 metadata.version，最后 null。存在的已知版本字段必须为非空字符串；不自动把数字转字符串。
5. 原件 name 用作 skill_name，不强制与 slug 一致，也不要求现有中文名符合新技能 ID 格式；没有则 null。原件 description 及所有未知字段仍完整保存在原字节中。
6. 规范化记录另给 field_sources，值为 catalog、frontmatter、frontmatter.metadata 或 missing，供详情如实说明；缺失统一显示“未提供”，不编造作者、地址、版本。
7. homepage/repository 仅接受无账号密码的 http/https 绝对 URL；空字符串和非法日期报错，不按 null 吞掉。

## 3. MigrationBaseline：四项迁移证据

关系固定为 [spec 基线表](spec.md#user-scenarios--testing-mandatory) 中四 slug 及六个文件；实施开始记录路径、sha256、大小及执行位。
不将旧 search-index 作为原文或元数据真相源，也不将 office2md 加入该基线。
迁移前后逐一核对源摘要；证据写入受信任测试结果，不作为站点内部资料公开。

迁移状态：discovered → validated → records_prepared → verified。
任何错误进入 failed，不更改原件；若已有不同 catalog，报告冲突并保留现有记录。重复执行一致记录为 noop。

## 4. DerivedSkill / PublicFile：只读投影

DerivedSkill 含 schemaVersion、contentRevision、slug、digest、规范化字段、field_sources、
skill_name、content_text、body_html、detail_url、raw_url、download_url 与 files。
索引与详情按 [静态契约](contracts/static-site.md) 分别裁剪字段；不在每处重复整个模型。

- content_text 仅检索；body_html 只允许构建清理后的 HTML；raw_url 指向完整主文档原字节。
- PublicFile 保存原 path、size、sha256、executable、download_name、url，可选 media_url；空目录不提供文件 URL。
- 所有公开 URL 为站点根相对地址，不以 / 开头、不含 .. 或敏感参数；磁盘绝对路径不进入 JSON。
- download_url：单文件为主文档资源，目录为 ZIP；另给 download_name、download_sha256、download_size。
- 主文档“查看原文/复制”从 raw_url 读取完整 UTF-8 文本，不能从 body_html/content_text 还原。

## 5. BuildManifest：整批快照与产物证据

schemaVersion=1；contentRevision 是整批输入身份，不是 Git revision 或版本号。
由排序后的受控原件、catalog、构建代码/策略版本、网页源文件、依赖锁与运行时标识共同生成；
不含日期、绝对工作区位置、Git 状态、docs/handoff 或未纳管目录。相同有效输入不得制造更新时间。

manifest 记录各 slug 的 digest、原文件清单、空目录与每个公开产物的相对路径/size/sha256。
不包含自身 hash，避免自引用；所有其他输出必须在产物清单内，清单不得出现凭证/私有路径。
派生 JSON 携带同一 contentRevision；前端拒绝跨修订混读。ZIP 的 hash 用于该次下载完整性，
跨环境保真比较解包内容，不强制压缩容器字节一致。

构建状态：idle → validating → snapshot_ready → staging → verified → promoting → ready。
提交前任一步失败进入 failed，清理本次候选并恢复/保留旧 dist；若补偿恢复失败进入 recovery_required，
保留可恢复副本并给位置与原因。成功提交后清理临时 backup；不建立公开旧版入口。

本地输出提交点为 C-03 的 promoted 记录成功写入，不是 Git 提交或网站发布。提交前失败回滚；
提交后清理失败保持 ready，另报 cleanup_status=pending，保留事务记录而不回滚已提交输出；
正常清理为 cleanup_status=complete。锁 Owner 与 LocalBuildTransaction 是私有恢复资料，
其字段、派生路径及恢复矩阵唯一以 [C-03 本地协议](contracts/content-pipeline.md#local-recovery) 为准，
不得混入 BuildManifest 或业务时间/内容身份。

构建内的标题别名 → 受控标题 ID 映射仅用于 C-04 的派生 HTML 与本文跳转，
不新增原件字段或公开详情字段；原件 id/name 与下载字节均不改写。

## 6. Diagnostic：脱敏且可修正

字段：code、slug（可空）、path（项目/Skill 相对位置）、line/column（可选）、message、severity=error。
stderr 可输出结构化诊断；不直接打印 parser 的带原文错误、环境变量、请求头或原始敏感引用。
缺失附件报告所在 Markdown 与安全相对引用；疑似凭证引用仅报告位置、用 <REDACTED> 替代值。
明确区分 schema/YAML/duplicate/path/reference/limit/secret/build/conflict/recovery 错误，
每个错误均有可操作原因，具体代码以 [内容契约](contracts/content-pipeline.md) 为准。
E_SECRET 只报告 SECRET-01～04 的规则编号与安全位置；policyVersion=1 的规则/占位边界以 C-01 为准，
不能通过记录覆写或临时忽略名单绕过。提交后清理未完成属于 built 的独立清理状态，
不冒充 severity=error 的构建失败诊断。
