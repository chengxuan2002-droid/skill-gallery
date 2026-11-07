# Phase 0 Research: US-004 管理员手动维护

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本阶段只做技术判定和现状核实，不实现页面、不修改远程仓库设置、不发布。US-004 不引入新的库、
SDK、API 或 CLI 用法：手动维护复用已确认的 Q-001、DEC-001、DEC-006、DEC-008，以及 US-003 已交付的
构建/发布链，因此没有需要新增 Context7 查证的技术集成。生产 Pages 源切换与真实发布仍需单独授权。

## 1. 手动维护入口与流程

- **Decision**: 管理员使用 GitHub 仓库网页后台新增/编辑原件与 `catalog/<slug>.json`，提交到默认
  分支；默认分支 push 触发现有 `maintain.yml` 执行校验、构建、产物验证与部署。要求目录按文件夹
  上传，不实现 ZIP 解压。
- **Rationale**: Q-001 已确认复用 GitHub 仓库文件管理与 Actions，不另建站内后台；GitHub UI 已提供
  单文件与文件夹上传能力，权限由仓库控制，无需额外登录或凭证。
- **Verified**: 上游 FR-005 明确首版按文件夹上传、不要求 ZIP；`maintain.yml` 仅在 `push: main` 与
  `workflow_dispatch` 运行（US-003 T005/T008/T020 静态断言与 POC-002 远程验证）；现有构建读取
  `catalog` 指向的 `skills/` 内容，不扫描未纳管目录。
- **Alternatives considered**: 自建站内上传后台（违反 Q-001，增加登录、凭证和攻击面）；首版支持
  ZIP 解压（边界和路径校验复杂，非必需）；只依赖本地构建（无法上线）。

## 2. 站点管理外链

- **Decision**: 在现有页脚增加低权重“管理”外链，指向
  `https://github.com/chengxuan2002-droid/skill-gallery`，使用 `target="_blank"` 与
  `rel="noopener"`；不新增登录表单、文件输入或上传按钮。
- **Rationale**: TechnicalSolution 3.3 将管理入口定义为低权重外链；隐藏入口不能作为权限控制，
  权限完全由 GitHub 控制。静态链接不增加运行时依赖或权限面。
- **Verified**: 现有 `index.html` 页脚已有静态外链结构；构建仅复制 `index.html`/`assets`；搜索、
  详情与路由不依赖页脚 DOM。
- **Alternatives considered**: 站内管理页/登录表单（违反 Q-001 与 FR-007）；仅在 README 说明
  （入口不可发现，不符合低权重外链要求）；隐藏路径（不构成权限控制，禁止）。

## 3. 站内记录字段与校验

- **Decision**: 手动维护沿用现有 `catalog` schema，不新增字段：必填 `schemaVersion=1`、`slug`、
  `display_name`、`description`、`content_path`；可选标签、平台、作者、地址、版本、来源、用法、
  备注、许可、日期与 `source_tracking`。目录型 Skill 的 `content_path` 指向 `skills/<slug>/SKILL.md`。
- **Rationale**: 现有 `validateCatalogRecord` 已封闭顶层字段并校验 slug、路径、URL、日期和来源跟踪；
  复用同一规则避免第二套校验器，手动与未来 CLI 共用规则。
- **Verified**: `scripts/lib/catalog-schema.js` 定义必填/可选字段与未知字段拒绝；
  `scripts/lib/build-inputs.js` 由 catalog 解析内容并计算 digest；缺失字段返回 `E_SCHEMA`，
  路径越界返回 `E_PATH`，主文档缺失返回 `E_MAIN_MISSING`。
- **Alternatives considered**: 新增手动专用字段（破坏封闭 schema 与 US-001 基线）；从 frontmatter
  自动补元数据（会改写或猜测站内信息，违反 DEC-003）。

## 4. 替换、下架与恢复

- **Decision**: 替换要求管理员显式编辑/替换同一 slug 的原件并提交；构建按新文件清单重建，
  旧附件不进入新产物；下架需要删除原件与 `catalog` 记录，构建后索引/详情/下载不再包含该条目；
  恢复使用受控 `git revert`/恢复提交重新构建发布，不 force push。
- **Rationale**: 现有构建每次从当前内容树生成完整 `dist/`，文件清单和 ZIP 只包含当前文件；
  发布链只部署当前快照，天然满足单一当前版本。
- **Verified**: US-003 T031 隔离演练已验证 `git revert` 后 `contentRevision` 回到基线、slug/旧链接/
  单版本保持；`build-outputs.js` 按当前 `snapshot.files` 生成附件与 ZIP；索引只包含当前 catalog 项。
- **Alternatives considered**: 保留旧版目录供回退（违反 Q-003 单版本与公开旧版禁令）；
  在构建中比较历史 digest 阻止同 slug 覆盖（手动 UI 无法提供基线修订，且属于 US-005/US-006 的
  显式替换/冲突检查范围）。

## 5. 失败保留与状态

- **Decision**: 手动维护不新增状态机；复用 US-003 的 `maintain.yml` 与 RunStatus：内容提交、
  构建、部署分开显示；校验/构建失败不上传 artifact、不部署；部署失败保留上次正常站点；
  运行记录与 Step Summary 提供运行标识和稳定错误码。
- **Rationale**: 手动与自动发布共用同一校验和发布规则，避免两套行为；US-003 已提供失败注入、
  superseded 和重跑证据。
- **Verified**: `specs/003-validate-build-publish/validation/` 中 us3-recovery、us3-summary、
  us3-final-review 记录了本地/受控失败保留、状态分离和重跑结果。
- **Alternatives considered**: 手动流程单独状态服务（无必要，扩大范围）；只依赖 GitHub 运行日志
  （无法在摘要中区分提交/构建/部署）。

## 6. 文档与边界

- **Decision**: 在 README 现有“添加 Skill”章节补充 GitHub 手动维护步骤、必填字段、单文件/目录示例、
  失败处理、替换/下架/恢复与未实现能力说明；不新增第二套操作手册。
- **Rationale**: FR-005/NFR-006 要求操作可独立执行；README 已是当前维护入口。未实现的 Agent CLI、
  ZIP 解压和自动更新必须标“规划”，示例使用占位凭证，不写未验证命令。
- **Verified**: README 当前已说明原件格式、catalog 独立记录、`npm run build` 与“无上传入口”；
  AGENTS 命令表提供可执行检查入口。
- **Alternatives considered**: 单独写 `docs/ManualMaintenance.md`（增加分叉风险，本轮无必要）；
  在页面内嵌操作教程（暴露维护细节，非访客价值）。

## 7. 测试与验证策略

- **Decision**: 新增静态入口测试，断言页脚“管理”链接指向受信任仓库、无登录表单/文件输入且不引入
  运行时依赖；手动流程在系统临时副本构建真实验证合法新增、非法批次、替换、下架与恢复；受控部分在
  POC-002 授权范围内以等价提交验证，生产未授权时记录未运行。
- **Rationale**: 入口是唯一新增的站点行为，可用静态断言识别错误；构建/发布行为已由 US-003 测试与
  发布链保护，避免重复实现测试。
- **Verified**: 现有 `node:test` 可读取 `index.html` 做静态断言；US-003 的 `publish-fixture` 与
  隔离构建方法可复用；`npm run build` 对非法输入整批失败且保留旧 `dist/`。
- **Alternatives considered**: 浏览器端到端上传测试（GitHub UI 不可在本地自动化，且需要真实权限）；
  只靠人工检查（无法在 CI 识别入口退化）。
