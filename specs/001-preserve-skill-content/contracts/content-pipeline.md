# C-01 / C-02 / C-03：内容与本地构建契约

版本：1；功能 US-001。依据 [数据模型](../data-model.md)、[spec](../spec.md) 和上游 [唯一契约](../../../docs/TechnicalSolution.md#contracts)。
接口是本地受信任站点代码，不是 HTTP 上传、管理 CLI 或远程同步协议。

## C-01：无写入校验

**调用者**：M-02、M-03、四项迁移工具和受信任测试。输入为项目根、图库记录及其受控原件；
输出为规范化记录、文件/引用清单或结构化 diagnostics。不得改写源文件或旧 dist，不静默跳过非法条目。

### 记录与原件

- catalog 只接受其目录内直接的 <slug>.json 记录；按记录选择内容，不能扫描整个 skills 自动增项。四项初始记录外的目录原样保留。
- schemaVersion、slug、显示名称、简介、content_path 必需，类型见数据模型。重复 slug、重复来源所有权、未知顶层字段、主文档缺失或空白均失败。
- 必需显示值迁移时可从原件取得；原件不必有 tags/platforms。构建时记录本身必须完整。原件缺少 YAML 可由记录提供；存在 YAML 则必须合法。
- frontmatter 只在开头识别，允许 BOM 与 LF/CRLF；闭合行必须准确，未闭合报错；正文中的分隔线不当成第二段 YAML。YAML 根须为映射，重复键、非字符串键、多文档/自定义 tag 及超限别名失败。未知扩展字段保留于原件，已知字段存在却类型错误不能被覆写掩盖。
- 对 metadata.version 等约定字段做有界读取，不把任意 YAML 对象合并到 JS 原型或公开 JSON。

### 文件准入与所有权

1. 只允许记录指向 skills/<slug>.md 或 skills/<slug>/SKILL.md。单文件范围仅自身；目录范围为该 Skill 目录，所有正常文件、嵌套附件、许可和空目录均应完整纳入。
2. lstat 逐级检查项目入口和目录项，拒绝符号链接、硬链接（普通文件 nlink>1）、设备、FIFO/socket 等非普通项。校验前不跟随链接读取或枚举越界目录。
3. 拒绝绝对路径、盘符、NUL/控制字符、反斜杠歧义、遍历越界、重复路径，以及 NFC/大小写折叠后冲突。正常中文、空格及安全目录内的相对层级不改名。
4. **硬性禁止**：任意层级 .git/.svn/.hg、.ssh/.aws/.gnupg/.azure/.kube 和 .config/gcloud 等凭证目录；.env 与实际 .env.* 环境文件、.npmrc/.pypirc/.netrc/.git-credentials、常见私钥文件和私钥块。命中即整次失败，不能靠点路径准入绕过。
5. **仅系统噪声排除**：.DS_Store、._*、__MACOSX 目录、Thumbs.db、desktop.ini；摘要列明排除路径。它们不属于公开原件清单。任何正文真实引用这些被排除项仍失败。
6. **合法点资源**：包含点开头路径段的其他文件须在本条记录 allowed_dot_paths 中逐文件明确列出，否则 E_DOT_PATH_REVIEW。声明目录前缀不代表放行整个子树；多余/不存在的准入项也报错。仅 .env.example/.env.sample/.env.template 可作为明确模板经此规则准入，仍须通过疑似凭证检测。
7. 其余普通文件不做扩展名过滤，不因二进制或可执行脚本而漏收。站点只作为数据读取，绝不调用、import、source 或安装其依赖；项目根工具/文档目录不在内容选择范围。
8. 初始限额：每 Skill 最多 500 普通文件，总原始字节不超过 20 MiB，主文档不超过 1 MiB（均含边界）。先 stat 检查再读取，读取后复核；超限失败，无部分结果。
9. 对原件与图库记录应用下方固定的 SECRET-01～04 最小规则，命中任一规则即 E_SECRET、整批失败。只给规则编号/安全位置，禁止输出命中值；不得删掉命中片段后继续成功。此检测不宣称识别任意私密文本，管理员仍对公开收录范围负责。

<a id="secret-policy"></a>

### 凭证检测规则（A1 修订，policyVersion=1）

以下是本站固定的探测边界，不是对第三方凭证全部有效格式的声明。修改规则集合、阈值或例外须同步夹具与 policyVersion，后者参与 contentRevision。

| 规则 | 固定判定 |
|---|---|
| SECRET-01 | 识别 BEGIN/END 私钥边界的标签集合：PRIVATE KEY、RSA PRIVATE KEY、EC PRIVATE KEY、DSA PRIVATE KEY、OPENSSH PRIVATE KEY、ENCRYPTED PRIVATE KEY。出现 BEGIN 后，只有匹配 END 且去边界后的全部非空白正文恰为一个下述占位值时放行；否则（含缺 END）拒绝。不得输出或尝试解析私钥。 |
| SECRET-02 | 任意位置出现 ghp_、gho_、ghu_、ghs_、ghr_、github_pat_、sk- 之一，紧接至少 20 个连续 ASCII 字母/数字/下划线/连字符，即拒绝；大小写敏感，不以总长度或远端验证判断真假。该规则不享受赋值占位例外。 |
| SECRET-03 | 检查 key=value、key: value 的单行字面量，兼容可选 export、引号键、JSON 对象内键；键只含 ASCII 字母/数字/下划线/连字符，前面须为行首、空白、左花括号或逗号。键去引号、ASCII 小写、连字符换下划线后，命中 password/passwd/pwd/token/access_token/refresh_token/api_key/apikey/client_secret/private_key/secret/authorization/cookie，或以 _password/_token/_api_key/_client_secret/_private_key/_secret 结尾，则检查值。值为完整单/双引号串或仅由 ASCII 字母/数字/下划线/连字符组成的裸标量；须以行尾、注释或逗号/右花括号/右方括号/分号结束（允许中间空白），不截取函数调用/拼接/成员访问等表达式，不求值。Authorization 另接受未加引号的单个 Bearer/Basic 加一个裸值，并先去该大小写不敏感的前缀再比较。非空且非下述占位值即拒绝。 |
| SECRET-04 | 对 http/https URL 中的 userinfo 做纯本地检查：有冒号时检查密码部分，无冒号时检查整个 userinfo；非空且非下述占位值即拒绝，不发网络请求。此例外不改变展示/元数据 URL 禁止 userinfo 的其他规则。 |

占位值只包括：完整的 `YOUR_<一个或多个大写 ASCII 字母/数字/下划线>_HERE`、`<REDACTED>`、`***`，
以及美元符号加一个大写环境变量名（可加一对花括号；变量名以大写字母或下划线开头，后续仅大写字母/数字/下划线）。
仅为比较而去首尾空白及一对值引号，不改原文件，不执行环境变量展开；空值和裸 null 不视为凭证。
demo、test、example 及任意短字符串不是通用豁免值。SECRET-01 对占位私钥正文仅去空白，不去引号或接受环境变量引用。

SECRET-01/02 在全部受控文件的原始字节上查 ASCII 特征；SECRET-03/04 只对合法 UTF-8 派生文本和记录字符串检查。
不解码任意编码载荷、不执行表达式、不查询环境或远端。SECRET-03 未匹配的其他语法不等于已确认无凭证，
管理员审查发现的其他敏感输入同样不得收录。路径硬性禁止项不因正文有占位值而放行。
每条规则至少有命中、占位/合法对照与边界夹具；SECRET-02 另测 19/20 字符，SECRET-03 另测动态表达式不误截取。
命中值一律显示 `<REDACTED>`；误报保留原件/旧输出并暂停本次生成，不能加临时跳过开关。
维护者可改用经确认可公开的输入后重试，规则调整须同步本契约和测试，不能靠改写下载原件消除告警。

### Markdown 引用

- 以每个 Markdown 文件所在目录为基准；覆盖主文档、README、references 等全部 .md 附件。只识别实际渲染且清理后保留的 a[href]/img[src]，不扫描代码字符串或活动标签。
- #fragment 与路径为空的 ?query#fragment 识别为本文锚点；展示按 C-04 映射到受控标题，不能覆盖 SPA 的技能 Hash 路由，原件中的链接字节不改。完整 http/https 是外链，不在构建期访问或验证可达；拒绝 protocol-relative URL 的展示。
- 其他 scheme（包括 javascript/data/file/blob/mailto）从展示移除，不尝试当本地文件读取；绝对本地路径及带盘符/反斜杠/越界的本地引用报路径错误。
- 对相对 URL 的路径只百分号解码一次，再做 POSIX 归一化与范围检查。允许 ../ 指向同一目录 Skill 内文件，禁止进入其他 Skill、catalog 或项目文件。编码后的分隔/遍历不得绕过边界；二次编码不继续解码去猜目标。
- 只查已验证文件清单，不按引用扩大收录范围。真实本地目标不存在或被排除，产生 E_REFERENCE_MISSING 并使整批失败；越界产生 E_PATH。诊断包含所属 Markdown 与安全相对引用，敏感值脱敏。
- 合法链接映射到 PublicFile 下载入口；相对 .md 附件作为只读原件取用，不新增 SPA 路由。主文档内部锚点保持当前详情。

## C-02：快照与 digest（本轮子集）

M-02 使用 C-01 边界读入 Buffer，记录完整文件清单、空目录、执行位和摘要。
对文件内容、清单及 catalog 取一致快照；构建完成准备切换前复核输入，变化则 E_SOURCE_CHANGED。
校验、渲染、原件副本和 ZIP 只使用此快照，不分别重读产生不同版本。

本轮不实现候选上传、远程 expected_revision、内容树替换或 Git 提交；这些仍由后续 C-02/C-05/C-06 调用扩展。现阶段失败不得修改 skills 或 catalog。

## 四项一次性迁移工具

规划入口为 node scripts/migrate-catalog.js，默认等价 --dry-run；--write 显式生成记录，两者互斥。
它只处理 spec 的四项固定路径，不导入任意目录、不访问网络、不提交 Git。

- 从四项原件读取显示名称、简介、标签、平台、用法/备注及合法已知字段；缺失可选信息为 null/[]，不编造日期、作者、网址或许可。
- 先验证全部输入与候选记录，记录六文件基线；若四项任意非法或现有记录不同，整批不落盘。
- --dry-run 仅输出预期记录路径、计数及验证结果；--write 只新增四份记录。已存在且语义一致为 noop，不自动覆盖差异；写入中途失败回收本次新建记录，既有记录不变。
- 成功退出 0；校验、参数、冲突或 I/O 失败退出 1 并给脱敏诊断。该辅助命令的退出约定不冒充未来 C-05 上传 CLI。

## C-03：完整静态构建

保留 node scripts/build-index.js 命令名，未来等价 npm run build。输入为项目根中明确选中的记录、受控内容和网页源文件；
公开产物仅 dist，必要中间目录/控制文件只写下方协议列出的同父私有路径，不再覆盖根 assets/search-index.json。
受信任测试可直接以临时项目根/输出目录调用公共构建函数，不为用户增加任意扫描/上传 CLI 参数。

**事务顺序**：

1. 先取得下方本地锁，再检查未结束事务并按恢复表处理；不能盲删未知临时路径或用户文件。遗留锁不自动抢占，确认原构建已退出后仅解除匹配的锁，保留事务记录与候选/backup，重跑构建才在新锁保护下恢复。
2. 完成全部 C-01/C-02 校验，在 dist 同父目录生成 staging；禁止直接写现有 dist。
3. 只复制网页入口、CSS/JS、固定 MiniSearch 与许可、.nojekyll；生成下列布局。parser、npm 元数据、源码仓库和后台日志不复制进站点。
4. ZIP 输出流完整完成后再取 hash；生成 details/index/manifest，核对所有产物、引用、逐文件摘要和单一 contentRevision。完成输入变化复核后才切换。
5. 先持久记录 promoting，再将旧 dist 改名 backup、将 staging 改名 dist；校验新 dist 后记录 promoted，作为本地提交点。在此之前任一步失败须回滚，恢复失败保留唯一有效副本并报告 E_RECOVERY_REQUIRED。两次 rename 不是无间隙原子事务，不承诺强杀/断电时连续服务。
6. 提交前失败退出 1，旧内容/记录不变；已有有效 dist 在正常可捕获失败下恢复原路径/字节，首次失败不留半成品 dist。提交后返回 0/built，不报告 published；只清理归属明确的临时项，清理成功则 cleanup_status=complete，失败则 cleanup_status=pending 并保留记录/副本及脱敏提示，不能在部分删除旧 backup 后又回滚它。清理状态不写入公开 JSON。

<a id="local-recovery"></a>

### 本地锁、事务记录与恢复（U1 修订）

默认输出名为 dist；以下路径均在输出同父目录，测试输出以其安全单段目录名代替 dist。
锁为 .dist.lock/owner.json；锁目录以互斥创建取得，owner 含 schemaVersion=1、32 位小写十六进制 run_id、正整数 pid。
已有锁一律不自动解除：owner 缺失/损坏或为链接时报 E_RECOVERY_REQUIRED，其余已持锁状态报 E_BUSY
（包括看似遗留但尚未人工解除的锁）。不用年龄/超时认定锁失效。
人工确认原进程退出、核对 owner 属于本输出（若有事务再核对其 run_id 对应关系）后，仅移除匹配的锁，再运行原构建命令；
无事务时也不据此清理任何候选目录。没有新增强制恢复/上传 CLI。

事务记录 .dist.transaction.json 含 schemaVersion=1、run_id（格式同 owner）、output_name（必须等于本次输出的安全单段目录名）、phase、
had_previous（布尔）、previous_manifest_sha256（有旧输出为 64 位小写十六进制，否则 null）、candidate_manifest_sha256（64 位小写十六进制）。
phase 仅 prepared/promoting/promoted；staging 和 backup 路径固定由 run_id 派生为
`.dist.stage-<run_id>`、`.dist.backup-<run_id>`，不接受记录中的任意绝对或相对路径。
prepared 在候选及旧输出的 manifest/产物全部校验后、任何 dist 改名前写入；
状态更新先写 `.dist.transaction.tmp-<run_id>` 再替换记录，记录写失败不能执行下一步。控制文件/目录拒绝链接。
提交前失败或启动恢复只按下表操作；归属需记录合法、派生路径一致、对应 manifest 及其产物摘要匹配，
仅名字相似不证明归属。恢复旧事务使用旧记录的 run_id，不要求等于本次新锁的 run_id。
缺少记录、hash 不符、出现额外文件或状态组合不明时不猜测、不覆盖。

| 持锁后的记录/实际输出 | 恢复动作 |
|---|---|
| 无事务记录 | 正常开始；不扫描删除未知 stage/backup。 |
| prepared/promoting；dist 为旧快照、backup 不存在 | 保留旧 dist；只清理能验证的本事务 stage，结束未提交事务。 |
| prepared/promoting；dist 缺失、backup 为旧快照 | backup 恢复到 dist；只清理归属可证的候选，结束未提交事务。 |
| prepared/promoting；dist 为候选、backup 为旧快照、stage 不存在 | 尚未提交：候选移回 stage，再恢复 backup，完成回滚；不悄悄提交中断候选。 |
| prepared/promoting；had_previous=false | 无 backup 且候选至多在 stage/dist 一处时，移除可验证候选恢复“无输出”；不影响其他文件。 |
| promoted；dist 为候选、stage 不存在、backup 为旧快照或不存在 | 保留已提交 dist，继续可验证 backup 的清理；成功后删事务记录，不能回滚已提交结果。 |
| promoted 但 dist 缺失；backup 仍可验证 | 先恢复可用 backup，再报 E_RECOVERY_REQUIRED，保留记录供人工核对，不宣称候选 built。 |
| 其他/记录损坏/归属或摘要无法验证/恢复 I/O 失败 | E_RECOVERY_REQUIRED，保留现有 dist、记录和可恢复副本，给脱敏位置/原因；不得删唯一可用副本。 |

清理未完成时保留 promoted 记录；下次持锁按表处理，残缺 backup 无法验证则停止自动清理并保留可用 dist。
启动恢复若未能结束旧事务，返回 1/E_RECOVERY_REQUIRED，不创建新事务或覆盖旧记录；
0/built 且 cleanup_status=pending 仅用于本次新构建已经越过提交点的情况，不能把未执行的新构建报成功。
事务记录、锁、随机标识与清理状态都不进入 dist、内容 digest、contentRevision 或业务日期；
它们是本地恢复资料，不是旧版图库。协议仅处理本地可验证中断，不承诺断电耐久或网络文件系统锁语义。

~~~text
dist/
├── .nojekyll
├── index.html
├── assets/{app.js,style.css,search-index.json}
├── assets/vendor/{minisearch-6.3.0.min.js,LICENSE.minisearch}
├── details/<slug>.json
├── skills/<slug>/<file-sha256>.bin       # 原始字节，原名/原路径在清单中
├── media/<slug>/<sha256>.<raster-ext>    # 仅确实用于 img 的安全栅格副本
├── downloads/<slug>.zip                # 仅目录型
└── manifest.json
~~~

每次完整生成新输出，不增量遗留旧附件；摘要相同的文件资源允许同 slug 内共享 URL，不影响包内原路径。
主文档也以 .bin 原字节交付，前端设置原始 .md 文件名；不以活动扩展名静态公开附件。
media 只允许经格式签名检查的 PNG/JPEG/GIF/WebP/AVIF；不是按扩展名宣称图片安全。
不支持的图片格式仍保留原件并给下载入口，不能无提示删掉资源。ZIP 文件内容与其原始目录清单完全一致。

### 诊断

错误形状见数据模型，至少区分 E_SCHEMA、E_YAML、E_UTF8、E_DUPLICATE、E_MAIN_MISSING、
E_PATH、E_LINK_FILE、E_DOT_PATH_REVIEW、E_SECRET、E_LIMIT、E_REFERENCE_MISSING、
E_SOURCE_CHANGED、E_BUSY、E_BUILD、E_RECOVERY_REQUIRED。
参数/校验失败不能继续替换输出；parser 异常/文件错误转成安全诊断，不回显原始片段或完整凭证。
恢复失败是需要处理的失败状态，不能宣称原位置仍可用或成功部署。

追溯：FR-001/004/011，NFR-001/003/006，DEC-002/003/005/009，
AC-001/002、AC-012 本地部分、AC-014 本地支撑。
