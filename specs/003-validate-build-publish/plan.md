# Implementation Plan: US-003 校验、构建与原地址发布流水线

**Branch**: 功能标识 `003-validate-build-publish`；实际 Git 分支 `codex/us-003-validate-build-publish`
（从 US-002 功能分支堆叠，未合并 main）。

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: `specs/003-validate-build-publish/spec.md`，含四个内部切片、FR-007/009/011、
NFR-003/004/006、AC-008/011/012/014 及生产授权边界。

**Implementation Status**: T001–T033 已完成本地/受控验证（T018/T022/T025 在受控临时公开仓库执行；
Foundational 见 [validation/foundational.md](validation/foundational.md)；US1 见
[validation/us3-snapshot.md](validation/us3-snapshot.md) 与
[validation/us3-links.md](validation/us3-links.md)；US2 测试契约见
`tests/unit/publish-status.test.js`、`tests/integration/publish/publish-superseded.test.js` 与
`tests/integration/publish/publish-deploy-workflow.test.js`，恢复演练见
[validation/us3-recovery.md](validation/us3-recovery.md)，Step Summary 见
[validation/us3-summary.md](validation/us3-summary.md)；US3 安全契约见
`tests/integration/publish/publish-security.test.js`、
`tests/integration/publish/publish-security-workflow.test.js` 与
[validation/us3-security.md](validation/us3-security.md)；US4 同次运行/noop 见
`tests/integration/publish/publish-same-run.test.js`、`tests/unit/publish-noop.test.js` 与
[validation/us3-same-run.md](validation/us3-same-run.md)；取用回归与最终复核见
[validation/us3-regression.md](validation/us3-regression.md)、
[validation/us3-final-review.md](validation/us3-final-review.md)）。生产 Pages 未启用。
T018 的受控 POC-002 结果见 [validation/us3-recovery.md](validation/us3-recovery.md) 第 6 节。
生产 Pages 源、environment、分支保护和线上切换未修改；US-004～US-007 仍未开始。

## Summary

在 US-001/US-002 已本地验收的构建与静态站点上补齐发布链：新增发布前产物校验
（白名单、manifest 双向一致、同快照、凭证扫描）、显式 Pages artifact 部署、最小 job 权限、
并发与过期检查、运行状态与摘要。使用单次 `maintain.yml` 的 `build`→`deploy` job 链保证
自动化提交后可在同一运行显式发布；后续 US-006 在同一工作流增加 `sync` job。真实生产 Pages
配置与线上切换需要单独授权，本故事先交付可审阅配置、本地/受控验证和未运行记录。

## Technical Context

**Language/Version**: 构建与验证脚本 Node 26.3.0 / CommonJS（`package.json` engines 锁定
`>=26.3.0 <27`）；GitHub Actions `ubuntu-24.04`；前端资产不改。

**Primary Dependencies**: 不新增 npm 产品依赖。复用 `scripts/lib/secrets.js`、现有 `yaml` 2.9.1
（测试解析工作流）和既有构建/诊断模块。GitHub 官方 action 与扫描器 Action 使用完整 SHA：
`actions/checkout@v7.0.1`（`3d3c42e5aac5ba805825da76410c181273ba90b1`）、
`actions/setup-node@v7.1.0`（`949feb2413d6458794dcd2491c4babbbce0c15c1`）、
`astral-sh/setup-uv@v10.3.3`（`68559e99cc807c1eb7e9238fd43a15bba460eec2`）、
`actions/upload-pages-artifact@v5.0.0`（`fc324d3547104276b827a68afc52ff2a11cc49c9`）、
`actions/deploy-pages@v5.0.1`（`368f82528645a54fb793d4d04e342629a3f51346`）。
不引入 `configure-pages`。

**Storage**: 无新增持久存储。构建产物仍为 `dist/`；发布状态写入 GitHub 运行记录与
`$GITHUB_STEP_SUMMARY`，不建数据库、状态服务或额外 artifact。`dist/manifest.json` 为同快照校验依据。

**Testing**: `node:test` 显式运行 `tests/unit/*.test.js`、`tests/integration/*.test.js`。
新增单元测试覆盖白名单、manifest 双向一致、路径/链接拒绝、凭证扫描、目标 SHA 与状态字段；
集成测试在临时项目构建 `dist` 后注入额外文件、篡改字节、凭证文件和过期 revision；
工作流测试静态断言触发、权限、environment、并发、固定 SHA、artifact 路径和无 `pull_request_target`。
真实 Pages 部署只在受控仓库、获授权后执行。

**Target Platform**: GitHub Actions + GitHub Pages；站点保持
`https://chengxuan2002-droid.github.io/skill-gallery/` 与 `/skill-gallery/` 子路径；
运行器 `ubuntu-24.04`，Node/npm 以 `.node-version`、`package.json` 为准。

**Project Type**: 现有原生静态站点及其构建/发布流水线；只改 M-03 的发布编排与 M-07 子集，
不改内容 schema、前端行为或 US-001/US-002 的验收结果。

**Performance Goals**: 发布工作流总时限候选 30 分钟（含依赖安装、扫描、构建和部署）；
不与 NFR-002 的查询 p95 混用。部署前校验只遍历一次产物，不重复构建；超时保留上次正常站点。

**Constraints**: 只发布 `dist/` 白名单；非法输入整批阻止；部署失败保留上次正常站点；
同一提交重跑幂等；旧快照不得覆盖新快照；重复部署同一快照可接受，不要求检测线上是否已相同，
但不得创建空内容提交或伪装成内容更新；不修改分支保护、environment 或 Pages 源来绕过失败；
不把本地构建/工作流文件存在报告为线上已发布；T041 macOS 与 US-002 合并决策保持不变。

**Scale/Scope**: 正式内容 4 项；产物规模由现有构建决定；不读取 1,000 项性能夹具。
本故事只实现 M-07 的发布子集与 `scripts/lib/publish.js`；M-05/M-06、US-004～US-007 不在本轮。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 宪章原则 | 计划边界 | 设计与证据入口 |
|---|---|---|
| I 固定地址与稳定身份 | 只发布 `dist/`；保留 `/skill-gallery/` 与四个旧 `#/skill/<slug>` 链接 | workflow 契约、quickstart 受控检查 |
| II GitHub 后台与写入权限 | 复用 GitHub Actions；写入/部署仅授权环境；不新增访客登录或站内后台 | Permissions 表、未授权场景 |
| III 原件保真与元数据分离 | 发布不重建正文、不改 catalog/schema；从现有构建产物部署 | build 入口不变、同快照校验 |
| V 单一当前版本 | 部署当前快照；不提供旧版入口；恢复走受控历史 | RunStatus/RecoveryRecord |
| VI 失败保留与真实状态 | 构建失败不部署；部署失败保留旧站；提交/部署分开报告 | 状态模型、失败注入测试 |
| VII 凭证与不可信内容 | 产物凭证扫描、最小权限、无 PAT、内容不执行 | `publish.js`、workflow 契约 |
| VIII 简洁精准 | 不新增 npm 依赖；复用现有构建与秘密策略；只加 1 个工作流和 2 个脚本/测试文件 | 结构树、依赖清单 |
| IX 规格追溯与证据 | 保留 FR/NFR/AC 编号；本地/受控证据与未运行项分开 | 下方映射、validation 记录 |

Phase 0 后复核：Pages action 权限、environment、concurrency 和 artifact 要求已按 Context7 与
官方 README 核对；未发现新的宪章违反项。Phase 1 后复核：contracts 只新增发布校验/状态接口，
不改变内容或前端契约。结论：无宪章冲突，无需豁免。GATE 通过的是设计合规性，不是发布验收。

## Project Structure

### Documentation (this feature)

```text
specs/003-validate-build-publish/
├── spec.md                 # 已有
├── checklists/requirements.md
├── plan.md                 # 本文件
├── research.md             # Phase 0：发布机制、权限、并发、校验、版本
├── data-model.md           # Phase 1：RunStatus、Artifact、DeployTarget、Diagnostic
├── contracts/
│   ├── publish.md          # 发布前校验、目标判定、CLI 与不变量
│   └── workflow.md          # maintain.yml 触发、权限、并发、artifact、状态
├── quickstart.md           # 本地与受控环境验证步骤
├── validation/             # 实施时生成：命令、退出码、运行 URL、未运行项
└── tasks.md                # 下一阶段生成，不在本次规划内
```

### Source Code (repository root)

```text
.github/workflows/maintain.yml          # 新增：push main / dispatch → build → deploy
scripts/lib/publish.js                  # 新增：产物校验、目标判定、状态与摘要
scripts/lib/publish-summary.js          # 新增：从 CI 环境构造 RunStatus 摘要
scripts/publish-check.js                # 新增：本地/CI 校验 CLI（artifact/target）
scripts/publish-summary.js              # 新增：Step Summary CI 入口
tests/unit/publish.test.js              # 新增：纯函数与状态契约
tests/unit/publish-summary.test.js      # 新增：摘要状态与脱敏
tests/integration/publish/publish-artifact.test.js # 新增：构建产物与失败注入
tests/integration/publish/publish-workflow.test.js # 新增：工作流静态断言
tests/integration/publish/publish-summary-workflow.test.js # 新增：摘要字段静态断言
assets/                                 # 不改
catalog/、skills/                       # 不改
scripts/lib/build-site.js               # 不改；复用其 manifest 输出
.github/workflows/quality.yml           # 不改；保留独立质量门禁
```

**Structure Decision**: 复用现有 M-03 构建产物与 M-07 工作流位置；发布校验放
`scripts/lib/publish.js`，CLI 只做参数解析和 JSON 输出，不复制规则。工作流只增加一个
`maintain.yml`，不新建部署框架、状态服务或额外 npm 包。

## Design Flow and Boundaries

1. 工作流在 `main` push 或手动触发时运行；`build` job 安装锁定依赖与固定扫描器，
   执行 `npm run check`、`npm run security` 和 `npm run build`。
2. `publish-check.js artifact` 读取 `dist/manifest.json`，验证实际文件集合与 manifest 双向一致、
   路径白名单、摘要、同快照和凭证规则；失败立即停止，不进入部署。
3. `upload-pages-artifact` 上传 `dist/` 为 `github-pages` artifact；`deploy` job 依赖 build，
   在 `github-pages` environment 中运行。
4. 部署前比较 `github.sha` 与远端默认分支 HEAD；不一致标记 `superseded` 并跳过部署，
   不误报已发布。
5. `deploy-pages` 只执行一次线上切换；失败保留平台上次正常快照，状态为 `deploy_failed`；
   同一提交重跑不新建内容提交。
6. 工作流把脱敏状态写入 Step Summary；运行记录保存目标 SHA、内容标识、构建/部署结果和失败码。
7. 后续 US-006 在同一工作流增加 `sync` job，提交后通过 `needs` 进入 build/deploy；
   本故事保留结构，但不实现来源检查、调度或提交。
8. 生产 Pages 源、environment、分支保护和真实线上切换不在代码中修改；受控仓库 POC-002
   单独记录，未授权时只交付可审阅配置和本地验证。

详细字段、状态和退出码以 [data-model.md](data-model.md)、[publish 契约](contracts/publish.md)、
[workflow 契约](contracts/workflow.md) 为准；quickstart 只负责可执行验证步骤。

## Implementation Sequence and Traceability

| 顺序 | 范围与依赖 | 必须获得的证据 | 上游映射 |
|---|---|---|---|
| 1 | 先写 `tests/unit/publish.test.js`、`tests/integration/publish-artifact.test.js` 的失败契约 | 白名单、双向 manifest、路径/链接/凭证、目标 SHA、状态字段能识别错误实现 | FR-009、FR-011；AC-011、AC-014 |
| 2 | 实现 `scripts/lib/publish.js` 与 `scripts/publish-check.js` | 合法产物 `verified/current`；额外文件、篡改、凭证、过期 revision 全部失败关闭；错误 JSON 脱敏 | FR-007、FR-009、FR-011；AC-008、AC-011、AC-014 |
| 3 | 新增 `.github/workflows/maintain.yml`，补 `tests/integration/publish-workflow.test.js` | 触发/权限/environment/并发/固定 SHA/artifact 路径/无 `pull_request_target` 静态通过 | FR-007、FR-011；AC-008、AC-014 |
| 4 | 在隔离副本执行完整 build + publish-check，注入构建失败、部署失败、superseded、受控恢复提交和并发场景 | 合法发布、失败保留、重跑幂等、恢复语义、旧快照不覆盖新快照的证据 | FR-009、NFR-004；AC-011、AC-014 |
| 5 | 运行 `npm run lint`、`npm run format:check`、`npm test`、`npm run security` | 记录实际命令、退出码、测试数量、扫描结果和未运行项 | NFR-003、NFR-006；AC-008 |
| 6 | 受控测试仓库 POC-002（需授权）或记录未运行 | Pages 源切换、合法/非法发布、部署失败重跑、恢复、取用回归、旧链接/子路径/刷新、运行 URL | FR-011；AC-011、AC-014 |
| 7 | 定向更新 README/AGENTS 与 validation 记录 | 实际可执行命令、发布状态、生产未启用和剩余风险；不写假设性命令 | NFR-006；AC-014 工程支撑 |

T001 先失败再实现；已由共享层覆盖的行为直接复验，不伪造失败。真实生产配置未授权时，
第 6 步记为未运行，不能以第 3～5 步代替远程发布验收。

## Complexity Tracking

无宪章违反项，无额外架构豁免。复用现有构建、秘密策略和一个 GitHub Pages artifact；
拒绝第三方部署框架、状态数据库、额外 CLI 平台或第二套内容校验器。

## Planning Verification

本次只读取规格、上游文档、现有构建/工作流/秘密模块，并查证 GitHub Actions Pages 部署权限与
action 版本；未运行新业务实现、未修改 `dist/`、未创建或修改远程仓库设置、未发布。
Context7 查询覆盖 `pages: write`、`id-token: write`、environment 和 concurrency；
官方 action README/Release 核实了 artifact 名称、权限要求和固定 SHA。
后续实施若发现 Pages 源/环境要求与本计划冲突，先按宪章 IX 更新契约和任务，不降低验收。
