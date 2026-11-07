# Implementation Plan: US-004 管理员手动维护

**Branch**: 功能标识 `004-manual-skill-maintenance`；实际 Git 分支 `codex/us-004-manual-maintenance`
（从 US-003 分支堆叠，未合并 main）。**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md)，含四个内部切片、FR-005/007/009/010、NFR-003/004/006、
AC-006/008/011 及生产授权边界。

**Implementation Status**: T001–T017 已完成本地/受控验证（T016 在 POC-002 执行；入口、手动流程、
失败/替换/下架/恢复与最终复核见 [validation/](validation/)）；生产 Pages 未启用，手动提交、
本地构建或受控验收不等于线上发布。

## Summary

在 US-003 已交付的校验/构建/发布链上补齐管理员手动维护闭环：使用 GitHub 仓库文件管理作为唯一
后台，管理员通过网页新增/修改/替换/下架 Skill 与站内记录，提交到默认分支后由 `maintain.yml`
校验、构建和部署。站点只增加低权重“管理”外链，不新增站内后台、登录、数据库或上传接口；
README 提供可独立执行的操作说明、必填字段、失败处理与恢复步骤。生产 Pages 源切换与真实发布
仍需单独授权。

## Technical Context

**Language/Version**: Node 26.3.0 / CommonJS（`package.json` engines 锁定 `>=26.3.0 <27`）；
站点为原生 HTML/CSS/JS，不引入框架；GitHub Actions `ubuntu-24.04`。

**Primary Dependencies**: 不新增 npm 产品依赖或开发依赖。复用现有构建（`scripts/lib/build-site.js`）、
校验（`scripts/check-project.js`、`scripts/lib/file-admission.js`、`catalog-schema.js`）与发布
（`scripts/lib/publish.js`、`.github/workflows/maintain.yml`）、现有 `node:test`、`yaml` 2.9.1。

**Storage**: 无新增持久存储。内容与站内记录仍为 `skills/`、`catalog/`；发布状态由 GitHub 运行记录
与 Step Summary 承担；恢复使用 Git 历史，不新增数据库或状态服务。

**Testing**: `node:test` 单元/集成测试。新增站点入口静态断言（管理外链指向受信任仓库、无登录表单/
文件输入、低权重结构）；README 改为人工审查 + 链接/命令可执行性检查。手动流程的构建、非法批次、
替换、下架与恢复在隔离副本验证，受控部分在 POC-002 授权范围内补充。

**Target Platform**: GitHub 仓库后台 + GitHub Actions + GitHub Pages；站点保持
`https://chengxuan2002-droid.github.io/skill-gallery/` 与 `/skill-gallery/` 子路径；运行器
`ubuntu-24.04`，Node/npm 以 `.node-version`、`package.json` 为准。

**Project Type**: 现有原生静态站点与发布流水线；只改静态首页/样式、README 和少量测试，
不改内容 schema、搜索/详情前端行为或 US-001～US-003 的验收结果。

**Performance Goals**: 不新增页面运行时依赖；管理外链为静态 HTML，不影响首屏、搜索或发布时延。
手动维护的构建/发布时间沿用 US-003 的 `maintain.yml` 时限（build 30 分钟、deploy 10 分钟）。

**Constraints**: 访客只读；写入仅 GitHub 授权身份；不建站内后台、不新增 ZIP 解压、不执行 Skill
脚本、不安装其依赖；非法批次整批阻止且旧站保留；替换保持单版本并清理旧附件；下架移除索引/详情/
下载；恢复走受控历史提交；生产 Pages 未授权不切换；README 示例不含凭证；未实现命令必须标“规划”。

**Scale/Scope**: 正式内容 4 项；手动维护单文件/目录；不读取性能夹具。US-005 CLI、US-006 来源检查/
调度、US-007 整体验收不在本轮。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 宪章原则 | 计划边界 | 设计与证据入口 |
|---|---|---|
| I 固定地址与稳定身份 | 不改路由/子路径；管理外链不改变站点身份 | 入口测试、构建回归 |
| II GitHub 后台与写入权限 | 复用 GitHub 文件管理与 Actions；不建站内后台/登录；管理入口仅为外链 | 入口契约、README、权限边界 |
| III 原件保真与元数据分离 | 手动替换只改 `skills/` 与 `catalog/`，不改写原件语义；展示/搜索/下载继续分离 | 构建回归、单版本检查 |
| V 单一当前版本 | 替换清理旧附件；下架移除当前条目；不提供旧版入口 | 隔离替换/下架验证 |
| VI 失败保留与真实状态 | 非法批次不部署；提交/构建/部署分开；恢复走受控历史 | US-003 发布链证据、手动流程验证 |
| VII 凭证与不可信内容 | 不新增凭证；不执行 Skill 脚本；产物白名单沿用 | `npm run security`、US-003 证据 |
| VIII 简洁精准 | 只加静态外链、README 和入口测试；不新增依赖 | 差异复核 |
| IX 规格追溯与证据 | 保留 FR/NFR/AC 编号；本地/受控证据分开 | 任务映射、validation 记录 |

Phase 0 前复核：手动维护复用已确认的 Q-001、DEC-001/006/008，不引入新框架或外部 API；无需新增
技术查证。Phase 1 后复核：设计只增加静态入口与文档，不改变内容/发布契约；无宪章冲突，无需豁免。
GATE 通过的是设计合规性，不是手动发布验收。

## Project Structure

### Documentation (this feature)

```text
specs/004-manual-skill-maintenance/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/manual-maintenance.md
├── validation/           # 实施时生成：步骤、退出码、未运行项
└── tasks.md              # 由 $speckit-tasks 生成
```

### Source Code (repository root)

```text
index.html                              # 修改：页脚低权重“管理”外链
assets/style.css                        # 修改：管理外链的轻量样式（不改变主视觉）
README.md                               # 修改：手动维护操作说明与边界
tests/unit/site-entry.test.js           # 新增：管理外链/无登录表单静态断言
skills/、catalog/                       # 不改；由管理员按说明手动维护
scripts/、.github/workflows/maintain.yml # 不改；复用 US-003 校验/构建/发布
```

**Structure Decision**: 管理入口放在现有静态页脚，复用站点样式；不新增前端模块或路由。
手动维护说明放入 README 现有“添加 Skill”章节，避免第二套文档；测试只断言入口的静态契约。

## Design Flow and Boundaries

1. 管理员在 GitHub 仓库后台新增/编辑 `skills/` 原件与 `catalog/<slug>.json`，提交到默认分支。
2. `maintain.yml` 对默认分支 push 执行全量校验、构建、产物校验和部署；校验失败整批阻止。
3. 非法批次不产生可部署产物，平台保留上次正常站点；运行记录与 Step Summary 分开显示提交/构建/部署。
4. 替换保持同一 slug 单版本，构建按新清单清理旧附件；下架删除原件与记录后从索引/详情/下载消失。
5. 恢复使用受控 `revert`/恢复提交重新构建发布，保持 slug、旧链接与历史。
6. 站点页脚提供低权重“管理”外链指向仓库；不提供登录、上传表单或隐藏入口授权。
7. README 说明必填字段、目录/单文件步骤、失败处理、运行标识、替换/下架/恢复与未实现命令边界。
8. 生产 Pages 源、environment、分支保护和真实切换不在本轮代码内修改；POC-002 仅在授权范围验证。

详细字段与接口以 [data-model.md](data-model.md)、
[manual-maintenance 契约](contracts/manual-maintenance.md) 为准；quickstart 只负责可执行验证步骤。

## Implementation Sequence and Traceability

| 顺序 | 范围与依赖 | 必须获得的证据 | 上游映射 |
|---|---|---|---|
| 1 | 先写 `tests/unit/site-entry.test.js` 失败契约：管理外链、无登录/文件输入、低权重结构 | 入口指向受信任仓库且无后台假象 | FR-007、FR-010；AC-008 |
| 2 | 修改 `index.html` 与 `assets/style.css`，通过入口测试 | 访客只读；管理入口可见但不扩展权限面 | FR-007、FR-010；AC-008 |
| 3 | 更新 README 手动维护章节（字段、步骤、失败、替换/下架/恢复、命令边界） | 干净环境可独立执行；不写未验证命令 | FR-005、NFR-006；AC-006 |
| 4 | 隔离副本验证合法新增/替换/下架/非法批次与恢复 | 构建/索引/详情/下载变化与失败保留证据 | FR-005、FR-009；AC-006、AC-011 |
| 5 | 受控 POC-002 等价手动提交（授权范围内） | 运行 URL、目标提交、发布状态；生产未切换 | FR-005、FR-009；AC-006、AC-011 |
| 6 | 运行 `npm test`、`npm run lint`、`npm run format:check`、`npm run security` | 记录实际命令、退出码、测试与扫描结果 | NFR-003、NFR-006；AC-008 |

先建立入口/流程验证再实现；已由 US-003 覆盖的发布行为直接复验，不伪造失败。生产配置未授权时，
第 5 步记录未运行，不能以本地构建或工作流文件存在代替。

## Complexity Tracking

无宪章违反项，无额外架构豁免。手动维护直接复用现有 GitHub 后台、构建和发布链，只增加一个静态
外链和文档，不新建服务或抽象。

## Planning Verification

本次只读取 spec、宪章、现有首页/构建/校验/发布代码与上游 0.2 文档；未修改业务实现、未运行构建、
未触碰生产 Pages。US-004 不引入新的库、SDK、API 或 CLI 用法；GitHub 手动维护与权限约束沿用已确认的
Q-001、DEC-001、DEC-006、DEC-008，无需新增 Context7 查证。后续若发现 GitHub 后台行为与规格冲突，
先按宪章 IX 更新规格/契约/任务，不降低验收。
