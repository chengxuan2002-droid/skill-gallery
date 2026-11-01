# Implementation Plan: US-001 原件保真、图库模型、旧库迁移与完整取用

**Branch**: 功能标识 001-preserve-skill-content；实际 Git 分支为 main，本次未创建分支。  
**Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)  
**Input**: specs/001-preserve-skill-content/spec.md，含本地附件缺失整次失败的澄清 A。

## Summary

保留四项现有 Skill 的 slug、原件路径与全部受控附件，新增独立 catalog 记录；以原字节快照生成搜索索引、安全详情、原件下载及完整目录 ZIP。现有 build-index.js 升级为完整 dist 构建入口，原生前端只适配新静态契约及必要取用操作。所有条目共同校验，任一非法输入或缺失本地附件均使整次失败，保留源文件和上次有效输出。

依据四份 0.2 文档：[调研](../../docs/IndustryResearch.md)、[需求](../../docs/DemandAnalysis.md)、[技术方案](../../docs/TechnicalSolution.md)、[编程规范](../../docs/AiProgrammingGuide.md)，以及 [AGENTS.md](../../AGENTS.md)、[宪章](../../.specify/memory/constitution.md) 1.0.0。沿用 FR/NFR/DEC/M/C/AC 编号，本地三个故事切片均属于上游 US-001。

## Technical Context

**Language/Version**: 原生浏览器 JavaScript、HTML/CSS；构建继续 CommonJS，marked 动态 import。Node 26.3.0 为本地基线，实施时固定版本并声明 >=26.3.0 <27；不在本轮决定生产 CI 运行时。

**Primary Dependencies**: 构建端 yaml 2.9.1、marked 18.1.2、sanitize-html 2.18.1、yazl 3.3.1；浏览器沿用 minisearch 6.3.0 并本地分发。yauzl 3.4.0 仅作开发期 ZIP 验证。实施期以精确版本及 package-lock 锁定，先完成 PoC，不使用未锁 CDN。

**Storage**: skills 为只读原件；catalog/<slug>.json 为站内记录；dist 为唯一公开产物目录，同父私有临时目录/控制文件仅按 C-03 使用。无数据库、后台服务、浏览器写入凭证或公开版本历史。

**Testing**: node:test 显式选择 tests/unit/*.test.js 和 tests/integration/*.test.js；独立 ZIP 解包与 SHA-256 比对；已有浏览器工具或人工完成子路径、复制、下载及不执行内容验收。专用 E2E 框架选择仍留 US-002。

**Target Platform**: 本地 macOS 与 Linux 构建；现代浏览器静态读取。保持 GitHub Pages 地址 https://chengxuan2002-droid.github.io/skill-gallery/，本轮仅验证本地等价 /skill-gallery/ 前缀，不发布。

**Project Type**: 现有单一静态网站及本地构建脚本，扩展既有结构。

**Performance Goals**: 本轮重点是四项迁移 100%、路径/字节零差异、零静默遗漏、失败零破坏。无本轮检索 p95 或整站视觉承诺；NFR-002、NFR-005 由 US-002 验收。

**Constraints**: 不改原件、不执行收录脚本、不扫描入库未纳管目录；完整校验后替换；不创建上传/自动更新/发布入口。初始工程上限每 Skill 500 文件、20 MiB 原始总字节、主文档 1 MiB，实施 PoC 固定边界测试后写入 README，不作为实测容量承诺。

**Scale/Scope**: 恰好迁移 spec 中四项正式收藏，标准格式及恶意样例仅在隔离夹具中。M-01、M-02、M-03 与 M-04 最小读取/取用适配；C-01、C-02 本地读取与摘要子集、C-03、C-04 本轮子集。M-05～M-07、C-05～C-07 不实现。

## Constitution Check

### 工程基线补充（2026-11-02）

用户授权先执行 project-bootstrap，仅补齐本地工程基线。沿用 Node 26.3.0/CommonJS 与既定目录，
新增精确开发依赖 ESLint 10.14.0、@eslint/js 10.0.1、globals 17.14.0、Prettier 3.9.10、eslint-config-prettier 10.1.8。
Node 内建测试、独立 Gitleaks 8.30.1/Semgrep CE 1.183.0 及 npm audit 分担工程检查，工具输出仅保留脱敏白名单字段。
仅验证受控源码/公开候选文件，原件只读且不执行；不新增产品运行依赖，不替代 C-01 的 SECRET-01～04。
映射 NFR-003/NFR-006、DEC-005/009 与 AC-012/014 的工程支撑子集；本地检查型 CI 也未纳入本次执行。
任务追加 T044～T047，T002/T003 只能记录部分覆盖；业务依赖、迁移/原文取用、自动更新、发布仍按原规划。

GATE：研究前审查和 Phase 1 设计后复核均通过。此处通过的是设计合规性，不是功能验收。

| 宪章原则 | 研究前边界 | 设计后复核与证据入口 |
|---|---|---|
| I 地址与身份 | 原地址、slug、Hash 不变 | C-04 的站点相对 URL 与四条旧链接；quickstart 的子路径验收 |
| II GitHub 后台与授权 | 不新增登录或管理端，不执行远程写入 | 仅本地构建/一次性迁移脚本；无 token 参数及上传 API；后续继续复用 GitHub |
| III 原件保真 | 原件、图库、搜索文本分离 | Buffer 快照、文件清单、raw/ZIP 与逐字节比对；未知信息为 null |
| IV GitHub 更新 | 保留已确认的首版 GitHub 边界 | 内容 digest 独立于 version；不实现来源适配，不声称已自动更新 |
| V 当前单版本 | 每 slug 唯一，不清除 Git 历史 | 新 dist 完整替换旧输出，无永久旧版目录或版本选择器 |
| VI 失败保留 | 全量失败阻断输出，真实报告阶段 | staging/backup 补偿恢复、故障注入、快照检查；不称本地成功为已发布 |
| VII 凭证与不可信内容 | 全部 Skill 内容为数据 | 路径/点文件/疑似凭证校验，构建清理，附件非活动交付，输出白名单，测试发现限制 |
| VIII 简洁精准 | 复用现有结构与原生前端 | 五个直接产品依赖、一个测试依赖均有用途；不升级搜索、不重写界面、不动用户资产 |
| IX 追溯与证据 | 只交付本故事及原编号映射 | 下方映射、contracts、quickstart；所有未运行 PoC 与生产验收明确标注 |

原件路径与包内路径保留；公开附件 URL 使用安全映射，不要求原始活动扩展名在网页原路径公开。此为 DEC-005 的安全展示细化，不改变原件下载。生产 MIME 与跨发布缓存验收继续归 US-003。没有需要豁免的宪章冲突，也不修改上游需求来迁就旧实现。

## Project Structure

### Documentation (this feature)

~~~text
specs/001-preserve-skill-content/
├── spec.md                         # 已有，含澄清 A，本轮不修改
├── checklists/requirements.md       # 已有，本轮不修改
├── plan.md                         # 本次规划
├── research.md                     # Phase 0
├── data-model.md                   # Phase 1
├── contracts/
│   ├── content-pipeline.md         # C-01/C-02/C-03
│   └── static-site.md              # C-04/公开静态读取与取用
└── quickstart.md                   # 实施后验证指南
~~~

tasks.md 由后续 $speckit-tasks 创建，本轮不创建。

### Source Code (repository root)

下列为未来实施的目标结构，本次仅写上面的规划文档。

~~~text
index.html                         # 只改静态依赖、契约与必要入口
assets/app.js                      # 新 schema、详情、完整复制与下载
assets/style.css                   # 仅原文区/错误状态必要样式
assets/search-index.json           # 旧实现基线，不再作为生成数据源
skills/                            # 原路径、原字节保留；不运行其中脚本
catalog/<slug>.json                # 新增四份图库记录
scripts/build-index.js             # 保留命令名，转调完整构建
scripts/migrate-catalog.js          # 仅四项旧库的一次性本地迁移
scripts/preview.js                  # 仅本地受限 dist 子路径预览
scripts/lib/validate.js             # M-01：schema、路径、引用与诊断
scripts/lib/content-store.js        # M-02：读取、快照与 digest
scripts/lib/build-site.js           # M-03：渲染清理、打包、输出事务
package.json / package-lock.json   # 新增精确依赖与真实命令
.node-version                      # 本地基线 26.3.0
tests/unit/*.test.js                # 受信任测试
tests/integration/*.test.js         # 迁移、构建、ZIP、失败保留
tests/fixtures/                     # 独立样例，绝不自动进入正式图库
dist/                              # 生成目录，不手改/不直接提交
~~~

**Structure Decision**: M-01～M-03 沿用上游唯一模块位置，文件数量最小化，不增加包层或服务层。迁移/预览脚本为本地辅助，不是 M-05 上传 CLI。后续实施只定向同步 README、AGENTS 中已经变化的真实命令，并新增必要的生成物忽略项；当前规划不改这些文件。

## Complexity Tracking

无宪章违反项，无额外架构豁免。采用已核实的解析/清理/ZIP 库以替代有损手写逻辑；node:test 复用运行时能力。拒绝数据库、全库重构、永久多版本产物、全仓测试发现和本轮专用浏览器测试框架。

## Design Flow and Boundaries

1. 显式读取 catalog 与其 content_path；先验证所属目录、记录、链接类型和文件限额，再取 Buffer 快照及基线。单文件只拥有自身，目录拥有受控子树。
2. 解析元数据并合并站内显示信息；记录为真相源之一，但不能掩盖原件中已知字段类型错误。对主文档及 Markdown 附件做安全解析和本地引用校验。
3. 在 staging 从同一快照生成 search-index、details、原件 .bin、必要媒体副本、目录 ZIP；复制明确允许的网页文件及 MiniSearch/许可，不复制整个仓库。
4. 生成 manifest，检查引用、文件 hash、快照身份和静态白名单；提交前重新核对输入摘要，输入中途变化则失败。全部成功才切换 dist；promoted 记录写入前的失败恢复旧输出。提交后的清理未完成保留有效新输出并报告 cleanup_status=pending，不回滚已提交结果。
5. 前端校验 schemaVersion/contentRevision，读取安全 body_html，原文从 raw 字节取得；复制等待实际成功，下载核对响应与摘要后按原名保存。跨快照/未知 slug/404 显式失败。

详细字段和错误以 [数据模型](data-model.md)、[内容契约](contracts/content-pipeline.md)、[静态契约](contracts/static-site.md) 为准；这里不再另建一份 schema。

### 分析修订记录（2026-11-02；依据 2026-11-01 分析）

| 分析项 | 定向细化 | 关联任务/验收 |
|---|---|---|
| A1 | C-01 固定 SECRET-01～04、占位值及误报处理，policyVersion=1 参与快照身份；不新增扫描依赖 | T007/T008/T031/T034/T035；NFR-003、AC-012 |
| U1 | C-03 明确锁/私有事务、归属校验、提交点及恢复矩阵；提交后清理状态独立报告 | T013/T020/T021/T033/T036/T040；FR-011、AC-012 |
| I1 | C-04 先移除源 id/name，再生成标题 ID/别名并映射片段；本文跳转保留技能 Hash | T006/T018/T022/T026/T037；FR-004/011、AC-002/005/012 |

本次只细化技术判定与验证口径，不改变四份 0.2 上游文档、宪章 1.0.0、功能范围或公开 schemaVersion=1。
三项规则细节以两份契约为唯一来源；私有控制目录与记录不进入 dist/digest/contentRevision，
其时间/随机值不成为版本或业务日期。

## Implementation Sequence and Traceability

以下是实现顺序与验证门禁，不是已完成任务或 tasks.md 替代品。

| 顺序 | 范围与依赖 | 必须获得的证据 | 上游映射 |
|---|---|---|---|
| 1 | 先复现旧 content 导出缺失，再做锁版本依赖 PoC | 旧实现不能满足完整代码/版本断言；YAML/清理/ZIP 组合通过 | DEC-002/003/005；AC-002/012 |
| 2 | M-01/M-02 数据、边界、摘要；再建立四项迁移记录 | 四 slug 与原件清单零变化；标准 name/description 样例成功；非法输入整次失败 | FR-001/011；NFR-001/003；AC-001/002 |
| 3 | M-03 完整静态构建及补偿恢复，依赖前两步 | 解包逐路径逐字节一致；输出只含允许项；提交前失败保留旧 dist，提交后清理失败保留有效新 dist | FR-004/011；NFR-001/003/006；AC-002/012/014 局部 |
| 4 | M-04 最小详情、原文、下载和旧 Hash 适配 | 四旧链接、子路径刷新、复制拒绝/下载不可用零误报，脚本不执行 | FR-004/011；AC-005/012；AC-002 |
| 5 | 干净副本复现、平台差异与范围审查 | 两副本身份/原件/附件一致；macOS/Linux ZIP 与恢复证据；原件/未跟踪资产未动 | NFR-006；US001-SC-01～07 |

AC-001/002 覆盖本故事规定的完整迁移和取用；AC-005 仅链接与反馈；AC-012 仅本地内容处理；AC-014 仅本地前缀与同快照支撑。检索升级、全面视觉、管理员上传、来源更新、Actions 和生产发布均不纳入本轮完成声明。

## Planning Verification

本次规划阶段只查证环境、源码和技术资料并校验文档。未运行未来 npm 命令、未安装业务依赖、未迁移原件、未执行 Skill、未开展业务 PoC、未发布。后续是否达到完成标准，以 [quickstart](quickstart.md) 的实际证据为准。

## 检查 CI 与现站基础监测补充（2026-11-02）

用户在初始化完成后明确授权提前补齐只检查 CI 与现有网站基础监测。此前不包含 Actions 的表述仍适用于 US-001 业务范围和首次初始化；本补充单独授权工程子集，不扩大业务实现或发布。
复用技术方案 1.3、现有根工程及 GitHub 后台；不创建平行产品规格。沿用 FR-011、NFR-003/004/006、DEC-001/008/009、AC-014 支撑子集。

1. T048：对齐方案/任务和可验收范围，提交。
2. T049：先用本地 HTTP 服务验证正常资源、200 错误页、错误 MIME/JSON、空索引、断连/超时、重试及无正文泄漏，再实现 scripts/check-site.js 和 npm run monitor:site。仅 CLI 默认读取固定站点，不提供任意 URL 的命令参数。
3. T050：创建两个只读 workflow，官方 Action 完整 SHA 固定、运行时与现有锁一致；静态校验、拒绝样例及完整工程检查通过后提交。不运行构建/部署。
4. T051：执行现站四地址探测，记录实际结果、原件保护、远程未启用项；更新 README/AGENTS 并提交。

监测采用每次 8 秒超时、失败再试一次、固定四资源。建议每 15 分钟，仅 GitHub 原生运行状态/维护者通知；用户后续频率选择以最终 workflow 为准。
本地测试不能依赖线上站点。代码与网络报告只输出固定类型、路径、HTTP 状态及尝试次数，不输出站点正文和原始错误。
验收证据写 validation/ci-monitor.md；远程执行与分支保护状态如实分列。原 43 项业务任务、T002/T003 未完成部分不改变。
