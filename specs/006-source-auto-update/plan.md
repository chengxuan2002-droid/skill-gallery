# Implementation Plan: US-006 来源定期检查与自动替换

**Branch**: 功能标识 `006-source-auto-update`；当前实际 Git 分支 `main`（本次未创建功能分支） |
**Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md)，含 FR-008/009/007、NFR-001/003/004、AC-009/010/011/012、
DEC-007/008、Q-002/003/004 及 US-003/004/005 已验收基线。

**Implementation Status**: Implemented and merged（2026-11-13）；T001–T030 完成，生产 `main` 调度已启用；
实际 03:17 定时触发尚未单独观察。

## Summary

为已收录 Skill 提供结构化 GitHub 来源检查与自动替换：解析分支/Release/pinned 到不可变提交，
读取同一修订的完整文件树与适用许可，比较内容摘要，复用既有校验/构建/发布链验证候选，按完整清单
替换当前内容并保留站内元数据；许可变化、本地修改、并发基线变化和非法候选失败关闭。工作流新增
`sync` job，在每日 03:17 Asia/Shanghai（UTC 19:17）或手动触发时检查，只提交目标文件，并在同一
运行中把新提交交给既有 build/deploy，实现单版本、失败保留、状态可观察和受控恢复。

## Technical Context

**Language/Version**: Node 26.3.0 / CommonJS（`package.json` engines 锁定 `>=26.3.0 <27`）；
GitHub Actions `ubuntu-24.04`；本地可用 Windows/Linux Node 22.21 执行兼容测试，但发布基线以
`.node-version` 的 26.3.0 为准。

**Primary Dependencies**: 不新增 npm 产品依赖；复用 `yaml` 2.9.1、现有 catalog schema、
`validate`/`content-store`/`build-site`/`publish`、US-005 的候选与工作副本工具。GitHub 读取复用
已安装 `gh` CLI；远程写入复用 Git 凭证助手；Node 内置 `fetch`/`child_process` 不新增包。

**Storage**: 无数据库。来源配置与最近同步结果保存在 `catalog/<slug>.json` 的 `source_tracking`；
候选在系统临时目录准备；运行报告只在 Actions Step Summary（可选临时文件），不新增公开索引字段。

**Testing**: `node:test`。单元测试覆盖来源解析、固定 SHA、路径/截断/链接拒绝、内容摘要与 noop/
conflict、许可策略、报告状态和脱敏；集成测试在临时 Git 仓库与注入来源读取器中执行检查、完整替换、
批次提交、失败保留和重跑；工作流结构测试覆盖 schedule、权限、checkout ref、同次运行和 token 边界。
默认测试不访问网络、不执行上游脚本或真实远端写入。

**Target Platform**: GitHub Actions ubuntu-24.04 负责定时/手动维护；Windows/Linux 本地可运行
check/apply 的受控副本；公开站点仍为 GitHub Pages `/skill-gallery/`。

**Project Type**: 现有原生静态站点 + 构建/发布流水线 + 受信任同步 CLI；不改前端、内容 schema、
公开下载或手动维护规则。

**Performance Goals**: 单来源读取超时 30 秒、最多 3 次重试；整体维护运行超时上限 30 分钟；
来源按串行或有限并发处理；只在上游修订或树读取后计算摘要，不重复构建未变化候选。

**Constraints**: 单一当前版本；整体替换并删除上游已删除附件；无脚本执行、无依赖安装、无凭证泄露；
不 force push、不降低分支保护；无变化不创建空提交；内容提交、构建、部署分开报告；每日
03:17 Asia/Shanghai（UTC 19:17），平台延迟/跳过不承诺 SLA；生产调度已于 2026-11-13 启用，
实际定时触发以运行记录为准。

**Scale/Scope**: 当前正式内容 4 项；单文件/目录来源；单 Skill 最多 500 个普通文件、20 MiB、
主文档 1 MiB；不做非 GitHub 来源、站内后台、ZIP 解压或公开版本选择。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 宪章原则 | 计划边界 | 设计与证据入口 |
|---|---|---|
| I 固定地址与稳定身份 | 同步只改内容与 catalog，不重命名 slug/路由/子路径 | 回归测试、旧链接检查 |
| II GitHub 后台与写入权限 | 仅 `sync` job 获 `contents: write`；复用 GitHub 权限，不新增公开写入入口 | workflow 测试、权限矩阵 |
| III 原件保真与元数据分离 | 候选按完整清单替换；站内标签/备注/用法/来源配置保留 | 字节/清单/元数据测试 |
| IV 可验证的 GitHub 来源更新 | 固定 SHA、完整树、许可检查、内容摘要、失败关闭 | 来源夹具、POC-003 |
| V 单一当前版本 | 整体替换并删除旧附件；不累积版本目录 | 两修订集成测试 |
| VI 失败保留真实状态 | 冲突/失败不覆盖；同次运行显式部署；部署失败保留旧站 | 故障注入、状态契约 |
| VII 凭证与不可信内容 | 不执行上游内容；token 仅在 sync 步骤；摘要脱敏 | 安全测试、Gitleaks/Semgrep |
| VIII 简洁精准 | 复用现有校验/构建/发布；不新增产品依赖或前端 | 差异复核、依赖清单 |
| IX 规格追溯与证据 | FR/AC/PoC 映射；本地/受控/生产分开报告 | tasks、validation、POC-003 |

Phase 0 前复核：来源范围、单版本、许可和调度均来自已确认的 Q-002/003/004 与 DEC-007/008；
不新增业务决策。Phase 1 后复核：设计只新增同步入口、共享 GitHub 读取和 workflow 扩展；无宪章
违反项，无需豁免。

## Project Structure

### Documentation (this feature)

```text
specs/006-source-auto-update/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── source-sync.md
│   └── workflow-sync.md
└── tasks.md              # 由 $speckit-tasks 生成
```

### Source Code (repository root)

```text
scripts/sync-skills.js                 # 新增：检查/应用入口，参数、报告与退出码
scripts/lib/github-source.js           # 新增/提取：GitHub 来源解析、树读取、固定 SHA
scripts/lib/source-license.js          # 新增：许可文件识别与摘要
scripts/lib/source-sync.js             # 新增：运行编排与报告出口
scripts/lib/source-sync-check.js       # 新增：来源选择、摘要比较、许可策略
scripts/lib/source-sync-candidate.js   # 新增：来源文件到候选快照
scripts/lib/source-sync-apply.js       # 新增：批次提交与完整替换
scripts/lib/source-sync-report.js      # 新增：封闭报告与脱敏 Step Summary
scripts/lib/content-store.js           # 复用：digest、snapshot、读取前后一致性
scripts/lib/catalog-schema.js          # 复用：source_tracking 字段校验
scripts/lib/catalog-source-license.js  # 新增：last_synced_license 形状校验
scripts/lib/skill-cli/source-github.js # 改为共享读取器的薄适配，保持 US-005 行为
scripts/lib/skill-cli/candidate.js     # 复用：候选校验与临时目录
scripts/lib/skill-cli/workspace.js     # 复用/扩展：显式路径暂存、批次提交、非 force 推送
.github/workflows/maintain.yml         # 修改：schedule、sync job、同次运行 ref、权限
tests/unit/source-sync*.test.js        # 新增：策略、状态、报告、脱敏
tests/integration/source-sync*.test.js # 新增：临时仓库、注入来源、替换/冲突/失败
tests/integration/publish/*.test.js    # 更新：触发、权限、sync 前置与同次运行断言
tests/support/source-sync-fixture.js   # 新增：来源/仓库/运行夹具
README.md                              # 修改：来源配置、手动重跑、状态、许可/冲突与恢复
```

**Structure Decision**: 同步入口只编排；来源读取、候选校验、内容摘要、构建发布复用现有模块。
将 GitHub 读取从 `skill-cli/` 提取到共享模块，避免 M-05 与 M-06 各有一份 API/路径校验器；
`skill-cli/source-github.js` 保留兼容出口，不改变 US-005 合同。工作流只增加一个 `sync` job，
不新增第二条发布 workflow。

## Design Flow and Boundaries

1. 读取 `catalog/*.json`，按 `source_tracking.enabled` 和可选 `--slug` 选择来源；未配置、禁用或
   非 GitHub 来源标记 unconfigured/paused/unsupported，不发起请求。
2. 解析 `ref_policy`：branch 读取分支引用，release 选择最新非草稿/非预发布 Release，pinned 校验
   固定 SHA 可达；所有策略最终得到不可变提交。截断、子模块、符号链接、越界路径和网页 URL 失败关闭。
3. 读取同一修订的完整树、二进制文件和许可文件；计算候选摘要。候选摘要等于当前内容摘要时
   unchanged；当前内容摘要与 `last_synced_digest` 不一致时 conflict；候选摘要与已同步摘要相同但
   修订变化时 unchanged，不创建空提交。
4. 通过共享候选构建器复用 schema、路径、凭证、大小和主文档校验；候选只作为数据处理，不执行脚本、
   不安装依赖，不跟随链接。
5. 许可策略：启用的自动来源必须能从同一修订的来源子树找到许可文件，并记录其适用性；仓库根/其他
   目录的许可只作人工参考，不自动放行。候选许可缺失、路径变化或字节变化时 policy_blocked，当前
   内容保留并报告。首次同步无子树许可同样阻断。
6. 应用候选：在干净基线中只写目标 Skill 原件和 `catalog/<slug>.json`；整体替换并删除旧清单外
   文件；更新 `last_synced_revision`、`last_synced_digest`、`synced_at`；保留站内字段。有效变更
   合并为一次批次提交，`git add` 只列目标路径，不使用 `git add .`。
7. 推送使用非 force；推送前重新读取远端基线，远端前进或非 fast-forward 返回 conflict，不覆盖。
8. 工作流：`sync` 只对 schedule/manual 运行；输出 `changed`、`commit_sha`、`commit_status`。
   `build` 在 sync 成功且 changed 或 sync 跳过时运行，checkout 指定 `commit_sha`；`deploy`
   使用 build 的 target SHA 做 freshness 检查，保证同一运行内发布同一快照。无变化不 build/deploy。
9. 失败保留：来源单项失败不阻断其他来源；全批构建失败不部署；部署失败保持旧站；重跑同一提交
   不新增内容提交；恢复使用受控 revert/restore 走同一构建发布路径。

## Implementation Sequence and Traceability

| 顺序 | 范围与依赖 | 必须获得的证据 | 上游映射 |
|---|---|---|---|
| 1 | 先写来源/摘要/状态/工作流失败契约 | 固定 SHA、截断/链接、noop、conflict、policy_blocked、schedule 和权限测试 | FR-008/009；AC-009/010/011/012 |
| 2 | 共享 GitHub 读取与候选准备 | 分支/Release/pinned、完整树、二进制、许可、注入读取器 | FR-008；NFR-001/003 |
| 3 | 摘要比较、元数据保留与完整替换 | 两修订增删文件、同版本变化、站内字段保留、旧附件清除 | FR-008；AC-009 |
| 4 | 本地冲突、许可阻断与并发 | 本地修改/许可变化/基线前进失败关闭，当前内容保留 | FR-008；AC-010 |
| 5 | 批次提交、状态报告与手动重跑 | 只暂存目标文件、一次提交、运行报告、重跑幂等 | FR-009；AC-011 |
| 6 | `maintain.yml` sync/schedule/dispatch/同次运行 | `contents: write` 仅 sync、checkout commit SHA、无变化不部署、成功/失败摘要 | FR-008/009；AC-011/014 |
| 7 | 安全边界与完整检查 | token 仅 sync 步骤、无 PAT/secret、Gitleaks/Semgrep/依赖审计通过 | NFR-003/004；AC-008/012 |
| 8 | POC-003 受控 GitHub 来源 | 固定 SHA、Release/pinned、删除文件、限流/错误、许可与二进制证据 | FR-008；AC-009/010/012 |

先建立能识别错误的验证，再实现；US-003 的构建/发布和 US-005 的候选/工作副本逻辑直接复用，
不伪造已完成的远端行为。

## Complexity Tracking

无宪章违反项，无额外架构豁免。新增一个受信任同步入口和一个 `sync` job；不新增 npm 产品依赖、
数据库、服务或前端组件。工作流安全测试需要纳入 `sync` job 的单项 `contents: write` 和受限
`GH_TOKEN` 使用，但 build/deploy 仍保持只读/最小权限。

## Planning Verification

本次规划读取了 US-006 规格、宪章、四份 0.2 文档、US-003/004/005 的 spec/plan/contracts/validation，
以及现有 `source-github.js`、`content-store.js`、`catalog-schema.js`、`workspace.js`、`publish.js`、
`maintain.yml` 与相关测试；未修改业务实现、未运行构建、未访问真实来源、未切换生产。
GitHub Actions 的 schedule UTC、workflow_dispatch 输入、job 权限和 checkout 凭证行为已用 Context7
查询当前官方资料（`/websites/github_en_actions`、`/actions/checkout`），版本相关用法在实施前再核对。
