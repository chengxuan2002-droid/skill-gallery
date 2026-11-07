# Implementation Plan: US-005 Agent 命令维护

**Branch**: 功能标识 `005-skill-cli`；实际 Git 分支 `codex/us-005-skill-cli`
（从 US-004 分支堆叠，未合并 main）。**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md)，含五个内部切片、FR-006/007/009/010、NFR-003/004/006、
AC-007/008/011 及生产授权边界。

**Implementation Status**: T001–T022 已完成本地/受控验证（T021 在 POC-002 执行；证据见
[validation/](validation/)）；T023 quickstart 走查待完成；生产 Pages 未启用。

## Summary

在现有项目 checkout 上提供非交互 Agent 命令：本地单文件/目录或结构化 GitHub 来源的预览、
新增、显式替换、来源导入和运行状态查询；发布在隔离工作副本中基于远端基线暂存该 Skill 相关文件，
复用 US-003 校验/构建/发布链与 US-004 手动维护规则。输出单行 JSON 与稳定退出码，认证复用既有
Git/gh 会话，不要求 token 参数。生产发布与 Pages 切换仍需单独授权。

## Technical Context

**Language/Version**: Node 26.3.0 / CommonJS（`package.json` engines 锁定 `>=26.3.0 <27`）；
命令运行于项目 checkout 或受控临时 checkout；GitHub Actions `ubuntu-24.04`。

**Primary Dependencies**: 不新增 npm 产品依赖；复用现有 `yaml` 2.9.1、`catalog-schema`、
`build-inputs`/`build-site`、`publish.js`、`secrets.js`。GitHub 读取/状态查询复用已安装 `gh` CLI
的既有认证；远程写入复用 Git 凭证助手。Node 内置 `fetch`/`child_process` 不新增包。

**Storage**: 无新增持久存储。候选内容在系统临时目录准备；提交只包含目标 Skill 的原件、
`catalog/<slug>.json` 与相关跟踪字段；不写工作区 `dist/`，不新增数据库或状态服务。

**Testing**: `node:test`。单元测试覆盖参数解析、退出码、JSON 输出、noop/冲突判定、状态派生与脱敏；
集成测试在临时 Git 仓库与本地来源夹具中执行预览/发布/替换/导入/查询；不加真实远端写入，
受控 POC-002 单独授权验证。依赖注入来源读取与运行查询，避免默认网络请求。

**Target Platform**: Windows/Linux Node 26.3.0；Git 与 `gh` 为前置命令；站点仍为 GitHub Pages
`/skill-gallery/`。生产 Pages 未切换。

**Project Type**: 现有原生静态站点 + 构建/发布流水线 + 新增 CLI；不改前端、内容 schema 或发布权限。

**Performance Goals**: 预览只读取一次候选与现有记录；发布不重复构建；状态查询轮询间隔固定
（如 5–10 秒）并受 `--wait` 总时限约束；不把查询 p95 与发布时限混用。

**Constraints**: 单行 JSON stdout；诊断到 stderr 且脱敏；退出码 `0/2/3/4/5/6/7/8`；不执行第三方
脚本/测试、不安装依赖；不 `git add .`、不 force push、不降低分支保护；冲突或来源失败保留当前内容；
本地提交/构建成功不得报告为已发布；README 示例不含凭证。

**Scale/Scope**: 正式内容 4 项；单文件/目录候选；不读取性能夹具。US-006 自动检查/调度、站内后台、
ZIP 解压和生产切换不在本轮。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 宪章原则 | 计划边界 | 设计与证据入口 |
|---|---|---|
| I 固定地址与稳定身份 | 不改站点/路由/子路径；CLI 不重命名既有 slug | 回归测试、README |
| II GitHub 后台与写入权限 | 复用 Git/gh 授权；不新增凭证入口；命令与手动维护同规则 | C-05 契约、权限测试 |
| III 原件保真与元数据分离 | 只暂存目标原件与站内记录；不改写原件字节 | 隔离仓库测试、字节比对 |
| V 单一当前版本 | 替换清理旧附件；不累积版本 | 替换/冲突测试 |
| VI 失败保留与真实状态 | 提交/构建/部署分开；冲突/来源失败不覆盖；等待超时不误报 | 状态契约、失败注入 |
| VII 凭证与不可信内容 | 不执行来源脚本、不安装依赖；输出脱敏 | 安全测试、`npm run security` |
| VIII 简洁精准 | 新增 CLI 与库拆分；不新增依赖、不改前端 | 结构树、差异复核 |
| IX 规格追溯与证据 | 保留 FR/NFR/AC；本地/受控证据分开 | 任务映射、validation |

Phase 0 前复核：命令输入/退出码来自已确认的 FR-006、C-05、DEC-006；不引入新框架。Phase 1 后复核：
设计只新增 CLI 与测试，不改变内容/发布契约；无宪章冲突，无需豁免。GATE 通过的是设计合规性，
不是命令验收。

## Project Structure

### Documentation (this feature)

```text
specs/005-skill-cli/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/skill-cli.md
├── validation/           # 实施时生成
└── tasks.md              # 由 $speckit-tasks 生成
```

### Source Code (repository root)

```text
scripts/skill-cli.js                    # 新增：CLI 入口（参数解析与退出码）
scripts/lib/skill-cli/                  # 新增：按职责拆分（每文件 <300 行）
├── args.js                             # 参数/命令解析
├── candidate.js                        # 本地/来源候选与元数据
├── source-github.js                    # 结构化 GitHub 读取（gh api / 注入边界）
├── workspace.js                        # 隔离临时 checkout、暂存与提交
├── publish.js                          # 调用既有构建/发布与状态派生
├── status.js                           # 运行状态查询与 --wait
└── output.js                           # 单行 JSON、脱敏与退出码
tests/unit/skill-cli*.test.js           # 参数、退出码、noop/冲突、状态派生
tests/integration/skill-cli*.test.js    # 临时 Git 仓库/来源夹具
README.md                               # 修改：命令契约与排错
assets/、catalog/、skills/              # 不改
.github/workflows/maintain.yml          # 不改；状态查询按现有运行/job 派生
```

**Structure Decision**: CLI 入口只做编排；规则放 `scripts/lib/skill-cli/`，复用 US-003/US-004
现有校验与发布模块，避免第二套校验器。来源读取与运行查询作为可注入边界，默认实现使用 `gh`，
测试不访问网络。

## Design Flow and Boundaries

1. 解析命令与选项（preview/add/import/replace/status），校验互斥参数与元数据文件；失败返回 `2`。
2. 准备候选：本地路径或结构化 GitHub 来源；来源必须解析到不可变提交并按完整文件树读取。
3. 复用现有 schema/路径/凭证/大小校验；预览只输出结果，不写入、不提交。
4. 发布时在系统临时目录建立隔离工作副本，基于远端默认分支基线，只暂存目标 Skill 与记录；
   相同内容返回 noop；不同内容同 slug 必须显式 replace 且 `--expected-revision` 匹配。
5. 提交后推送（非 force）；输出 commit SHA、运行链接（可查询时）与状态；部署未观察到成功前
   不得输出 published。
6. `--wait` 轮询运行/job 状态；构建成功且 deploy 步骤跳过时派生 `superseded`；超时返回 `8` 并保留
   运行链接。
7. 失败时清理临时副本，不修改用户工作区；冲突/来源失败/构建失败保留当前内容与线上站点。
8. README 说明前提、认证、命令、退出码、替换、导入、等待与排错；未实现能力标规划。

详细字段与退出码以 [data-model.md](data-model.md)、[skill-cli 契约](contracts/skill-cli.md) 为准；
quickstart 只负责可执行验证步骤。

## Implementation Sequence and Traceability

| 顺序 | 范围与依赖 | 必须获得的证据 | 上游映射 |
|---|---|---|---|
| 1 | 先写参数/输出/退出码失败契约 | 非法参数、未授权映射、JSON 单行与脱敏 | FR-006/007；AC-007/008 |
| 2 | 候选与校验（本地/来源） | 预览零写入；非法输入失败关闭 | FR-006；AC-007 |
| 3 | 隔离工作副本与发布 | 只暂存目标文件；noop；不写用户工作区 | FR-006/009；AC-007/011 |
| 4 | 替换与冲突 | 基线不匹配返回 4，保留当前内容 | FR-006/009；AC-011 |
| 5 | 来源导入与状态/等待 | 404/403/限流/截断失败；superseded/超时真实 | FR-006/009；AC-007/011 |
| 6 | README 与全量检查 | 干净 checkout 可执行；lint/test/security | FR-006；NFR-006；AC-007 |
| 7 | 受控 POC-002（单独授权） | 运行 URL、提交 SHA、状态与未运行项 | FR-006/009；AC-007/011 |

先建立能识别错误的验证，再实现；已由 US-003/US-004 覆盖的发布行为直接复用，不伪造失败。

## Complexity Tracking

无宪章违反项，无额外架构豁免。CLI 按职责拆分但保持在现有脚本目录；不新增服务、数据库或前端组件。

## Planning Verification

本次只读取 spec、宪章、US-003/US-004 契约与现有构建/秘密/发布模块；未修改业务实现、未运行构建、
未触碰生产 Pages。GitHub 来源与 `gh` 用法沿用 DEC-006/TechnicalSolution 已确认边界；实施涉及
GitHub API/CLI 具体行为时按项目规则用 Context7 或官方资料核实当前用法，再更新契约。
