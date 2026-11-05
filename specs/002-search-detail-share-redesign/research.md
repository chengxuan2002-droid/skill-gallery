# Phase 0 Research: US-002 检索、详情、分享与视觉改版

**Date**: 2026-11-05 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本阶段只做技术判定和现状核实，不实现业务、不修改站点内容。所有决定均沿用四份 0.2 文档、
宪章 1.0.0 与 US-001 已验收契约；没有遗留待澄清项。

## 1. 搜索组合：MiniSearch 负责英文模糊，连续子串负责精准/中文

- **Decision**: 复用已锁定的 MiniSearch 6.3.0 作为模糊检索主路径，使用字段权重、前缀和
  `fuzzy: 0.2`；精准模式不经过分词评分，直接对规范化后的完整查询做连续子串匹配；
  模糊结果再用连续子串命中补充和加权，确保中文至少按连续片段命中。
- **Rationale**: MiniSearch 已由 US-001 锁定并本地分发，浏览器无需新增依赖；上游技术方案 3.3
  明确要求英文词项容错、中文连续片段保底，且不做语义检索。每个输入只执行一次 MiniSearch 查询，
  再对已得结果做筛选/排序，符合 NFR-002 的延迟目标。
- **Alternatives considered**: 引入服务端/语义搜索（增加后端、凭证与运维，超出本故事）；
  自写编辑距离和分词器（重复成熟库能力，风险高）；只用 MiniSearch（中文分词和精准短语不可控）。
- **Verified**: Context7 `/lucaong/minisearch` 的 `SearchOptions` 文档确认 `boost`、`prefix`、
  `fuzzy`、`combineWith`、`fields` 可用；当前 `assets/app.js` 已使用 MiniSearch 6.3.0。

## 2. 字段权重和排序

- **Decision**: 搜索字段覆盖 `display_name`、`description`、`tags`、`platforms`、`author`、
  `source_type`、`usage`、`notes`、`content_text`。模糊检索字段权重按
  名称 4、简介/用途/标签 2、平台/作者/来源/备注/正文 1；精准模式按同一优先级计算命中权重。
  同分按 slug 稳定排序。
- **Rationale**: 上游技术方案 3.3 要求名称命中优先、说明/标签次之、正文再次；现有索引已在
  `publicFields` 和 `content_text` 中提供这些公开字段，无需新增 schema。
- **Alternatives considered**: 只按 MiniSearch 默认分数（名称不突出）；增加手工评分表
  （无用户可解释收益，增加维护成本）。

## 3. 精准模式的多词和引号

- **Decision**: 规范化采用 Unicode NFC、转小写、空白折叠。精准模式把未加引号的多词查询作为
  一个完整连续片段匹配；成对双引号界定完整短语；未闭合引号按字面字符处理并产生确定结果/空结果。
  模糊模式不把引号当作短语语法。
- **Rationale**: 与上游“精准模式连续片段、双引号完整短语”一致，也与 clarification 记录的默认值一致；
  行为可测试，不需要额外自然语言解析。
- **Alternatives considered**: 精准模式按空白拆分后 AND（会改变“连续片段”语义）；
  自写查询语法（超出本轮用户需求）。

## 4. URL 分享与路由状态

- **Decision**: 列表使用 Hash 参数
  `#/?q=<query>&mode=<fuzzy|exact>&tag=<tag>&platform=<platform>&source=<source>&author=<author>&sort=<auto|name|updated>`；
  重复键表示多选；`mode=fuzzy` 和 `sort=auto` 可省略。详情继续使用 `#/skill/<slug>`。
  列表状态变化用 `history.replaceState` 更新地址，避免触发 `hashchange` 重渲染；进入详情前把列表 Hash
  保存到 `sessionStorage`，详情返回按钮优先恢复它，直接打开旧链接则回到列表根。
- **Rationale**: 上游技术方案 3.3 推荐 Hash 查询参数并保留旧详情链接；`replaceState` 保持输入焦点和
  浏览器历史整洁；`sessionStorage` 只保存当前会话的返回位置，不改变公开详情身份。
- **Alternatives considered**: 把列表参数写入详情 URL（破坏稳定分享身份）；每次输入 `pushState`
  （污染历史、增加返回噪声）；只依赖 `hashchange` 重渲染整页（丢焦点、性能差）。
- **Security**: 只解析白名单参数；未知/非法值安全忽略；不把查询值写入 DOM 的 HTML 上下文；
  不包含凭证、内部路径或管理信息。

## 5. 数据映射：不新增 schema

- **Decision**: `description` 作为“功能简介”；`usage` 作为“适用场景与使用方法”；`notes` 作为“备注”；
  `declared_version` 存在时显示声明版本，缺失时显示当前内容 `digest` 的前 12 位作为“内容标识”；
  `updated_at` 作为“更新时间”；`author`、`homepage_url`、`repository_url`、`license`、`source_type`
  按现有公开字段展示。catalog、搜索索引和详情均保持 `schemaVersion=1`。
- **Rationale**: 现有 catalog schema 没有独立的“适用场景”字段，`usage` 实际承载场景与用法
  （例如 handoff-codex 的“适合多轮长对话……”）；详情已公开 `digest`，可直接做内容标识。
  不新增字段可以避免迁移四项记录和改变 US-001 已验收契约。
- **Alternatives considered**: 新增 `use_cases`/`scenarios` 字段（需要 schema/迁移/兼容决策，
  上游未定义）；把 `usage` 和 `notes` 合并（丢失站内备注与用法的区分）。

## 6. 筛选选项和缺失值

- **Decision**: 标签、平台、来源、作者筛选选项从当前索引实际值派生；无值维度不渲染空选项；
  缺失字段的 Skill 不匹配该维度筛选，清除条件后重新出现；同维度多选 OR，跨维度 AND。
- **Rationale**: 当前数据中作者/来源可能为 null，固定分类表会制造空结果；派生选项保持数据真实。
- **Alternatives considered**: 预置平台/来源 taxonomy（没有用户确认的分类表，易过时）；
  把 null 当“全部”匹配（会让筛选结果不可解释）。

## 7. 视觉与可访问实现

- **Decision**: 沿用原生 HTML/CSS/JS 和现有 CSS 变量，重构列表/详情的语义结构；桌面左筛选右结果，
  移动端折叠筛选和单列卡片；使用真实 `button`/`checkbox`/`select`/`a`，补 `label`、焦点样式、
  `aria-live` 结果计数、`aria-expanded` 移动筛选、减少动效媒体查询。主题优先读取已保存值，
  无保存值时跟随系统 `prefers-color-scheme`，切换后继续持久化。
- **Rationale**: 满足 AC-013，不引入 UI 框架；现有站点已经有主题变量和本地存储键，改造成本低。
- **Alternatives considered**: 引入组件/样式框架（违反简洁实现和新依赖约束）；
  只做视觉截图不补键盘/对比度（不能满足 NFR-005）。

## 8. 测试和性能验证

- **Decision**: 新增 `assets/app-search.js` 纯模块，用 `node:vm` 在单元测试中加载；新增/调整构建集成测试，
  验证新资产被复制且进入 `contentRevision`；浏览器验收使用现有 Edge/Chromium CDP 或人工流程，
  覆盖 Chromium/Firefox/WebKit（不可用则记录未运行）；用 `tests/support/search-fixture.js` 生成
  1,000 项/10 MiB 临时夹具，在本地 preview 中执行 50 次固定查询并记录 p95、设备、浏览器和查询集。
- **Rationale**: 现有工程已使用 `node:vm` 测试浏览器模块，不新增 jsdom/Playwright；性能验收必须
  在浏览器中测量结果可见时间，Node 微基准不能替代 AC-015。
- **Alternatives considered**: 引入 E2E 框架（新依赖和运行环境，US-001 未采用）；
  只用四项数据测性能（上游明确禁止）。

## Open Items

无未决技术项。T041 的 macOS 验证缺口、生产 Pages MIME/缓存/发布和 Q-004 调度均保持原状态，
不属于 US-002 的实现或验收范围。
