# Skill Gallery 业界调研

> 状态：资料核实完成，三个关键决策已确认 · 版本：0.2 · 日期：2026-11-01
> 对象：存量 Skill Gallery 下一轮改造。需求见 [DemandAnalysis.md](DemandAnalysis.md)，实现建议见 [TechnicalSolution.md](TechnicalSolution.md)。

本项目适合定位为个人精选 Skill 的管理与分发站。公开目录、原作者仓库和本地安装工具已经能解决部分发现与使用问题；本项目的价值在于把个人收藏、自建内容、来源追踪与当前版本汇总在固定网站中。保留既有页面地址可行，但写入与定时更新需要静态托管之外的执行环境。用户已确认复用 GitHub 仓库后台，首版自动更新覆盖 GitHub 公开来源，网站和当前文件只保留最新版并允许保留 Git 历史。不另建账户系统；具体检查时间仍为启用前配置项。

## 一、领域定义与相邻概念

### 1.1 本项目管理什么

Skill 是 Agent 可读取的操作知识及附属资源。Agent Skills 规范将其组织为包含 `SKILL.md` 的目录，允许脚本、参考资料和资产；不是只有一段提示词。[Agent Skills 规范](https://agentskills.io/specification)（R-001）。本项目还需兼容目前已经收录的独立 Markdown 文件，不以改造为理由丢弃它们。

### 1.2 真实场景

管理员发现别人分享的 Skill 或创建自己的 Skill，将内容和来源纳入个人库；访客通过搜索或筛选找到它，查看介绍、用法与版本，下载完整内容或分享详情链接。上游有变化时，系统检查来源并验证候选内容，更新网站当前版本，失败则保留可用内容。

### 1.3 相邻方案

| 类型 | 解决的问题 | 交付物 | 与本项目关系 |
|---|---|---|---|
| 公共 Skill 目录 | 发现流行或分类内容 | 搜索结果、安装入口 | 可作为来源，不代替个人精选管理 |
| 原作者仓库 | 创作、发布、维护原件 | 原始文件、提交、发布记录 | 自动更新的权威来源 |
| 本地安装工具 | 将技能安装到 Agent 环境 | 本地文件和来源记录 | 可互补，不等于网站上传接口 |
| 个人画廊 | 保存、查询、分发自己的精选集合 | 固定链接、完整包和当前版本 | 本次产品边界 |

网站负责保存和交付 Skill；下载行为不等于执行或已在某个 Agent 中验证可用。

## 二、代表方案与取舍

| 方案 | 已核实能力与证据 | 可复用处 | 局限与本项目判断 |
|---|---|---|---|
| skills.sh 及其 CLI | 官网提供发现目录与安装说明，Packs 文档说明集合分享和更新（R-002、R-003） | 发现来源、集合呈现方式 | 可以先试用集合分享；是否满足个人后台、指定地址和单版本规则需另验，不能断言没有 |
| anthropics/skills | 仓库按目录保存技能及附属资源；不同目录许可有区别（R-004） | 目录结构、真实内容样例 | 是作者内容仓库，个人策展及搜索页面仍需自己组织 |
| GitHub 仓库后台 + Pages + Actions | 浏览器和命令行可提交文件，Pages 提供静态站点，Actions 可按事件和计划运行（R-005～R-008） | 现有项目可渐进改造；身份、历史和执行环境可复用 | 管理界面偏开发者；调度不保证准点，长期无活动可能停用 |
| 本地文件夹 + Git + README | 当前仓库本身就是这一替代流程（R-009） | 最低迁移成本，原文与附件可保真 | 手动维护索引、查找和来源状态不集中，用户已提出改进要求 |

### 2.1 机会来自具体工作流

不是因为缺少公共目录，而是用户已经需要同时保存外部和自建内容、按个人维度查找、从 Agent 上传、保持网站版本新鲜。这些目标来自本次七条用户要求；没有进行额外用户访谈，也没有市场规模数据。

### 2.2 自建是否值得

若仅需分享一个集合，先用现成 Packs 会更省维护；但本次明确要求地址保持 `https://chengxuan2002-droid.github.io/skill-gallery/`，并参考已有代码继续迭代。因此推荐保留现有展示层，复用 GitHub 承担管理和自动化。独立后台是备选，不能在用户未选定时增加服务、认证和费用。

## 三、用户需求、证据和反证

| 需求证据 | 直接影响 | 如何验证价值 |
|---|---|---|
| BIZ-001：收藏外部及自建 Skill，保存、使用、分享、升级 | 原始文件必须完整；稳定身份与来源分离 | 收藏、下载、替换后原分享链接仍可用 |
| BIZ-002：多维度、精准及模糊检索，查介绍、用法、版本、作者和地址 | 搜索模式与详情信息必须明确 | 使用中文、英文、拼写错误及组合筛选验收集 |
| BIZ-003：手动和 Agent 命令上传，命令写入 README | 两个入口共用校验与发布逻辑 | 从全新工作目录仅阅读 README 完成上传 |
| BIZ-004：无访客账户登录，管理员后台维护 | 公开读取与受限写入分开 | 匿名不能写；管理员授权操作可完成 |
| BIZ-005：定期检查来源，自动更新，单一版本 | 来源定位、变更检测、完整替换、失败保留 | 候选新版删除附件时，旧附件也消失 |
| BIZ-006/007：简洁且有科技感，网站地址不变 | 精炼视觉与路径兼容 | 现有深链接与子路径资源检查 |

反证条件：如果日常只需本地安装或现成分享集合即可满足使用，复杂后台和跨站采集的收益可能不足。应先验证一个真实上传与更新闭环，再扩张来源适配。

## 四、生态与部署约束

### 4.1 可复用资产

现有站点是原生 JS SPA，采用 Hash 路由，Skill 文件及构建索引均在仓库。2026-11-01 抓取公开页面得到四条结果，包含平台、标签和详情入口；浏览器直连返回连接错误，未完成线上截图或视觉实测。页面文本与本地四条索引大体一致，不能据此证明部署提交与本地完全相同。

### 4.2 必须正视的限制

- GitHub Pages 托管静态输出，不能在页面内直接完成受保护的服务端写入或后台定时运行（R-005）。后台可复用 GitHub，也可另设服务，但后者仍要处理管理员认证。
- Actions 定期执行受平台调度影响；公开仓库长期无活动会停用计划任务。必须展示检查时间并提供人工重跑，不能承诺永远准点无人维护（R-006）。
- 自动化用 `GITHUB_TOKEN` 推送通常不会触发另一个 `push` 工作流；同步成功后的发布必须显式衔接（R-007）。
- 公共仓库可读不代表所有内容都有再分发许可；导入应保留作者、来源和许可信息（R-004）。

### 4.3 现有实现的关键缺口

代码审阅显示：索引中的 `content` 是去除代码块后的纯文本，详情和导出仍复用它；导出遗漏版本字段。当前手写 frontmatter 解析器只支持有限 YAML 写法，无法完整覆盖标准 Skill 元数据；例如本地未跟踪的 `office2md` 使用 `>-` 且缺图库必填字段，当前会被跳过。改造必须先区分“保真原件”和“搜索投影”，不能以现有代码作为正确行为基准（R-009）。

## 五、产品定位

一句话定位：让个人把精选的外部与自建 Skill 保存到固定网站，快速查明用途并完整取用，由授权维护入口更新内容，由自动化保持受支持来源的新鲜度。

| 定位 | 当前兑现 | 边界 |
|---|---|---|
| 精选收藏而非全网收录 | 管理员决定收录哪些技能 | 不做全网爬虫与榜单竞争 |
| 单一当前版本 | 同一 slug 只展示并分发一个有效版本 | 用户已确认允许保留 Git 历史，不提供旧版网站入口（Q-003） |
| 无访客登录 | 浏览、搜索、下载、分享无需账户 | 管理写入必须授权 |
| 渐进改造 | 复用页面、Hash 路由、内容库 | 不因科技风格而重写全栈 |

## 六、演进方向

| 阶段 | 用户结果 | 启动条件 |
|---|---|---|
| 本轮核心 | 收藏、查找、完整取用、手动/命令维护、GitHub 来源自动更新、固定地址发布 | 三个关键决策已确认，按故事依赖分阶段实现和验证 |
| 扩展 | 增加 GitHub 之外的更新适配器、来源迁移辅助 | 有明确真实来源和稳定接口 |
| 远期 | 可选语义检索、跨设备本地安装同步 | 关键词检索或下载流程确有不足 |

不把社交、用户中心、付费、在线执行 Skill 纳入本轮。

## 附录 A：术语

`slug` 是站内稳定标识；`upstream revision` 是精确上游提交；`version` 是上游声明的版本标签，可能不存在；`digest` 是内容身份；`publish` 表示已经部署可读，不等于本地已保存或 Git 已提交。

## 附录 B：来源与证据

所有外部资料访问日期均为 2026-11-01。官方资料核实能力，不等于本项目集成已经验证；无采用量或性能结论。

| ID | 支持主张 | 直接来源 | 性质与限制 |
|---|---|---|---|
| R-001 | SKILL.md、目录及元数据规则 | [Agent Skills specification](https://agentskills.io/specification) | 官方规范；不保证所有 Agent 实现一致 |
| R-002 | 目录、安装和生态定位 | [skills.sh Docs](https://www.skills.sh/docs) | 官网声称；未执行安装 |
| R-003 | 集合分享及更新 | [skills.sh Packs](https://www.skills.sh/docs/packs) | 官网说明；未测试 Packs |
| R-004 | 原作者目录实例与不同许可 | [anthropics/skills](https://github.com/anthropics/skills) | 官方仓库 README；许可需逐项检查 |
| R-005 | 静态托管和项目站点路径 | [What is GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | 官方文档 |
| R-006 | 调度、默认分支、停用条件 | [Events: schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) | 官方文档；不是调度 SLA |
| R-007 | Token 触发行为 | [Trigger a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow) | 官方文档；需集成验证 |
| R-008 | 手动上传和 CLI 触发 | [Adding a file](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)、[gh workflow run](https://cli.github.com/manual/gh_workflow_run) | 官方文档；本次无远程写入 |
| R-009 | 本地基线及已知缺陷 | [构建脚本](../scripts/build-index.js)、[前端](../assets/app.js)、[旧设计](../specs/2026-08-02-skill-gallery-design.md) | 实际代码审阅；基线提交 `0b319a3` |
| R-010 | 线上内容快照 | [现有网站](https://chengxuan2002-droid.github.io/skill-gallery/) | Firecrawl 文本抓取成功；未完成浏览器视觉验证 |
| R-011 | Pages 构建发布能力 | [Publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) | Context7 及官方资料；Action 版本实现前锁定 |
| R-012 | Git 树读取、文件模式与截断处理 | [Git trees API](https://docs.github.com/en/rest/git/trees) | 官方文档；固定 SHA 读取与文件模式需在 POC-003 验证 |
| R-013 | Pages artifact 与部署 job 要求 | [Custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) | 官方文档；未修改当前仓库设置 |

## 附录 C：假设处置与剩余缺口

| ID | 待验证判断 | 影响及验证 |
|---|---|---|
| ASM-001 | 管理入口选择 | Q-001 已关闭：用户确认复用 GitHub 后台；实际操作便利性在 AC-006 验证 |
| ASM-002 | 首版更新来源范围 | Q-002 已关闭：用户确认首版 GitHub 自动更新；实际适配在 POC-003 验证 |
| ASM-003 | 单版本与历史口径 | Q-003 已关闭：用户确认当前网站和文件仅留最新版，允许 Git 历史恢复 |
| ASM-004 | 每日检查、1,000 条内容是合理起步口径 | 候选设计参数，非用户承诺或实测；需求列明测量环境 |
