# Implementation Plan: US-007 整体验收与交接

**Branch**: `codex/us-007-overall-acceptance` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md)，含 FR-001～FR-011、NFR-001～NFR-006、Demo-001～003、
AC-001～AC-015、US-001～US-006 基线及宪章 1.0.0。

**Implementation Status**: 有条件验收/交接（2026-11-14）。T001–T022 已执行；Demo-001～003 为受控通过；
生产 environment/部署失败、MIME/缓存基础头、真实 403 和 macOS runner 已补验；剩余子项见
`validation/residual-gaps.md`，不判定整包通过。

## Summary

对已完成的 US-001～US-006 做一次整体验收：建立 AC/Demo 矩阵，复核固定地址、原件保真、检索/详情/
分享、手动与命令维护、来源自动更新、失败恢复、状态与安全边界；把本地、受控 POC 和生产证据分开，
逐项标注通过、受控通过、未运行或失败。用户已确认 Demo-002 可使用 POC-003 受控证据，US-007 可带
未运行项进入验收，但不得把未运行项计为通过。

## Technical Context

**Language/Version**: 不新增运行时；使用现有 Node 26.3.0 基线和 `node:test`，本地可用 Node 22.21。

**Primary Dependencies**: 不新增 npm 依赖；复用 `scripts/`、`tests/`、GitHub Actions、POC-002/003
和现有 validation。

**Storage**: 无数据库；证据写入 `specs/007-overall-acceptance/validation/`，不改变公开 schema。

**Testing**: 复用 `npm run check`、`npm run security`、`node scripts/skill-cli.js`、`node scripts/sync-skills.js`、
`node scripts/check-site.js`、`scripts/publish-check.js` 与浏览器/HTTP 检查；新增验证以只读为主。

**Target Platform**: Windows 本地、GitHub Actions ubuntu-24.04、生产 GitHub Pages
`/skill-gallery/`。

**Project Type**: 现有静态站点 + 构建/发布/来源同步链的验收，不改前端和内容 schema。

**Constraints**: 不执行收录 Skill 脚本；不写生产内容；不把配置/受控 POC 报告为生产已执行；
不把未运行项写成通过；不让凭证进入报告。

**Scale/Scope**: 当前 4 项生产 Skill；AC-001～015、Demo-001～003、US-001～006 的范围。

## Constitution Check

| 原则 | 计划边界 | 证据 |
|---|---|---|
| I 固定地址与稳定身份 | 复核生产首页、旧 hash、子路径资源 | AC-005/AC-014 证据 |
| II GitHub 后台与权限 | 区分管理员/Agent/访客；未授权无副作用 | AC-006/007/008 |
| III 原件保真 | 对照原件、附件、ZIP、字节和许可 | AC-001/002/004 |
| IV 可验证来源更新 | POC-003 受控证据；生产来源未配置则如实说明 | AC-009/010 |
| V 单一当前版本 | 只保留一个 slug 版本，历史用于恢复 | AC-009/011 |
| VI 失败保留真实状态 | 提交/构建/部署/调度分开；未运行不计通过 | AC-010/011/014 |
| VII 凭证与不可信内容 | 不执行上游；报告脱敏；公开产物白名单 | AC-008/012 |
| VIII 简洁精准 | 只做验收证据和文档，不新增功能 | 差异复核 |
| IX 规格追溯 | 每项 AC/Demo 有状态、证据和未运行说明 | 矩阵与 final-review |

Phase 0/1 后复核：无新增业务决策、无 schema/前端变更，无宪章豁免。

## Project Structure

```text
specs/007-overall-acceptance/
├── spec.md
├── plan.md
├── tasks.md
├── checklists/
│   └── requirements.md
└── validation/
    ├── acceptance-matrix.md
    ├── demo-001.md
    ├── demo-002.md
    ├── demo-003.md
    ├── fixed-address.md
    ├── fidelity.md
    ├── security.md
    ├── residual-gaps.md
    └── final-review.md
```

**Structure Decision**: 只新增验收目录与证据文件；不修改 `skills/`、`catalog/`、前端或发布权限。
生产只读检查；受控复验使用现有 POC-002/003 和临时副本。

## Verification Flow and Boundaries

1. **矩阵**：为 AC-001～AC-015、Demo-001～003 建立 `AcceptanceItem`，写状态、证据、命令/运行 ID。
2. **Demo-001**：在隔离副本执行手动单文件/目录新增、替换、下架；执行 `skill-cli` preview/add/import/
   replace/status；从生产或本地 dist 检查检索、详情、复制、原件和 ZIP。
3. **Demo-002**：引用 POC-003 的 branch/release/pinned、v1→v2、许可基线、无变化、同次发布；
   记录生产 schedule run `43533439066` 为延迟触发，生产来源为空。
4. **Demo-003**：引用 POC-002/003 的 404、冲突、许可阻断、部署失败、同提交重跑、revert；
   对未运行的真实 403/限流单独标注。
5. **固定地址与浏览器**：生产只读检查首页/索引/详情/原件/ZIP 和旧 hash；浏览器证据复用 US-002；
   Safari/移动实机未运行需列出。
6. **安全与保真**：复核 `npm run security`、Gitleaks/Semgrep、原件字节/ZIP 清单、公开产物白名单。
7. **残留缺口**：T041 macOS、US-005 真实 `gh api`/`--wait`、生产 environment 审批、生产部署失败注入、
   MIME/缓存、真实 403/限流；每项写明影响和恢复/补验方式。
8. **交接**：更新 README/AGENTS/validation，区分配置、生成、提交、部署；最终报告不得把未运行项
   计入通过，也不得宣称 US-007 整包完成。

## Implementation Sequence

| 顺序 | 工作 | 证据 |
|---|---|---|
| 1 | 盘点 AC/Demo 和现有证据，建立矩阵骨架 | `validation/acceptance-matrix.md` |
| 2 | Demo-001 手动/CLI/公开取用复核 | `validation/demo-001.md` |
| 3 | Demo-002 POC-003 与生产调度状态复核 | `validation/demo-002.md` |
| 4 | Demo-003 失败/冲突/部署失败/恢复复核 | `validation/demo-003.md` |
| 5 | 固定地址、旧链接、子路径、浏览器可达 | `validation/fixed-address.md` |
| 6 | 原件/附件/ZIP 保真与安全边界 | `validation/fidelity.md`、`security.md` |
| 7 | 未运行项清单与影响 | `validation/residual-gaps.md` |
| 8 | 交接文档和最终复核 | `validation/final-review.md`、README/AGENTS |

## Complexity Tracking

无宪章违反项，无新增架构或依赖。验收期间只读生产，写入仅限受控 POC 和隔离副本。

## Planning Verification

规划读取了 `specs/007-overall-acceptance/spec.md`、宪章、四份 0.2 文档、US-001～US-006 的
spec/plan/tasks/validation、当前 `main`、POC-002/003 运行记录和生产状态；未执行生产写入、未切换
生产配置。T001–T022 已由 tasks.md 驱动执行，最终结论为有条件验收/交接（见 `validation/final-review.md`），
不自动扩大生产发布授权。
