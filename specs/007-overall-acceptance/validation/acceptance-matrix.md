# US-007 Acceptance Matrix

**日期**: 2026-11-14
**状态骨架**: T002 建立；T003 已补入可追溯证据入口。所有项仍为 `未运行`，等待后续故事任务复核。
**状态口径**: 只允许 `通过`、`受控通过`、`未运行`、`失败`。未运行不得计为通过。
**Demo-002 口径**: 用户已确认 POC-003 受控证据可作为“受控通过”；不得写成生产自动更新已发生。

## 1. Demo 场景

| ID | 验收点 | 关联 | US-007 状态 | 证据入口 | 备注 |
|---|---|---|---|---|---|
| Demo-001 | 手动/Agent 维护到检索、详情、复制、下载 | US-001、US-005；AC-001/008/012/015 | 受控通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`fidelity.md`；`specs/004-manual-skill-maintenance/validation/manual-add.md`、`specs/005-skill-cli/validation/us5-add.md` | 手动/CLI/生产数据已验证；浏览器复制未重跑 |
| Demo-002 | 来源 v1→v2 自动更新、单版本、旧附件清理 | US-006、US-007；AC-009/011/014 | 未运行 | `specs/006-source-auto-update/validation/us6-poc.md`、`us6-license.md`、`us6-workflow.md`；run `43533439066` | 可标“受控通过”；待 T008–T010 |
| Demo-003 | 404/冲突/非法候选/部署失败→状态→修复/恢复 | US-003、US-007；AC-008/010/012/014 | 未运行 | `specs/003-validate-build-publish/validation/us3-recovery.md`、`specs/006-source-auto-update/validation/us6-status.md` | 待 T011–T013 |

## 2. AC 逐项矩阵

| ID | 验收点摘要 | 关联 | US-007 状态 | 证据入口 | 备注 |
|---|---|---|---|---|---|
| AC-001 | 数据与迁移：四项 slug/附件保持，非法批次非零退出 | FR-001、FR-011 | 未运行 | `specs/001-preserve-skill-content/validation/acceptance.md`、`us1-migration.md`、`tests/integration/migration.test.js` | 待 T003 索引 |
| AC-002 | 原件/目录包保真：路径、字节、未知字段、许可 | FR-001、FR-004、NFR-001 | 通过 | `specs/007-overall-acceptance/validation/fidelity.md`、`specs/001-preserve-skill-content/validation/acceptance.md`、`tests/integration/distribution.test.js` | 生产 raw/ZIP 已逐字节核对 |
| AC-003 | 搜索：精准/模糊/多维筛选/排序/分享恢复 | FR-002 | 受控通过 | `specs/002-search-detail-share-redesign/validation/us2-search.md`、`tests/unit/search-core.test.js` | 16 项搜索/列表/分享测试通过；未重跑生产浏览器 |
| AC-004 | 详情：功能/用法/原文/版本/作者/缺失提示 | FR-003 | 受控通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`specs/002-search-detail-share-redesign/validation/us2-detail.md` | 生产 JSON 字段与下载入口已核对；视觉复用 US-002 |
| AC-005 | 旧 hash 链接/替换后读取新版/复制失败提示 | FR-004 | 受控通过 | `specs/002-search-detail-share-redesign/validation/us2-detail.md`、`tests/unit/share-link.test.js` | 复制失败提示由单测覆盖；未重跑真实剪贴板 |
| AC-006 | GitHub 后台手动上传/替换/下架/非法批次 | FR-005 | 通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`specs/004-manual-skill-maintenance/validation/manual-add.md` | 7 项手动维护测试通过 |
| AC-007 | Agent 预览/提交/重复/替换/状态/退出码 | FR-006、NFR-006 | 通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`specs/005-skill-cli/validation/us5-add.md` | 28 项 CLI/状态测试通过 |
| AC-008 | 访客只读、未授权无写入、无凭证回显 | FR-007 | 未运行 | `specs/003-validate-build-publish/validation/us3-security.md`、`specs/006-source-auto-update/validation/us6-final-review.md`、`tests/integration/publish/publish-security.test.js` | 待 T017 |
| AC-009 | 自动替换：slug/单版本/增删附件/站内备注 | FR-008、NFR-001 | 未运行 | `specs/006-source-auto-update/validation/us6-apply.md`、`us6-poc.md` | 可标“受控通过” |
| AC-010 | 失败与冲突：404/限流/非法/许可/本地修改/重跑 | FR-008、FR-009、NFR-004 | 未运行 | `specs/006-source-auto-update/validation/us6-conflict.md`、`us6-check.md` | 真实 403/限流未运行 |
| AC-011 | 状态与恢复：检查/更新/部署/重跑/revert | FR-009 | 未运行 | `specs/006-source-auto-update/validation/us6-status.md`、`specs/003-validate-build-publish/validation/us3-recovery.md`、`specs/005-skill-cli/validation/us5-status.md` | 待 T012 |
| AC-012 | 内容边界：HTML/URL/越界/链接/脚本不执行 | FR-003、FR-007、FR-008、NFR-003 | 未运行 | `specs/001-preserve-skill-content/validation/us3-failures.md`、`tests/integration/untrusted-content.test.js`、`specs/006-source-auto-update/validation/us6-conflict.md` | 待 T017 |
| AC-013 | 界面：360/768/1440、明暗、键盘、对比度 | FR-010、NFR-005 | 未运行 | `specs/002-search-detail-share-redesign/validation/us2-accessibility.md`、`us2-cross-browser.md` | Safari/移动实机未运行 |
| AC-014 | 构建部署：白名单、同快照、旧地址/子路径/刷新 | FR-011、NFR-004、NFR-006 | 未运行 | `specs/003-validate-build-publish/validation/us3-links.md`、`us3-same-run.md`、`production-pages.md`、`specs/006-source-auto-update/validation/us6-workflow.md` | 生产 MIME/缓存未运行 |
| AC-015 | 性能：1,000 项/10 MiB/50 查询 p95 | NFR-002 | 未运行 | `specs/002-search-detail-share-redesign/validation/us2-performance.md` | 仅隔离夹具，不是生产承诺 |

## 3. 故事状态汇总

| 故事 | 范围 | US-007 状态 | 证据入口 |
|---|---|---|---|
| US-001 | 原件保真、迁移、完整取用 | 未运行 | `specs/001-preserve-skill-content/validation/final-review.md`、`acceptance.md` |
| US-002 | 搜索、详情、分享、可访问 | 未运行 | `specs/002-search-detail-share-redesign/validation/us2-final-review.md` |
| US-003 | 校验、构建、固定地址发布 | 未运行 | `specs/003-validate-build-publish/validation/us3-final-review.md`、`production-pages.md` |
| US-004 | GitHub 后台手动维护 | 未运行 | `specs/004-manual-skill-maintenance/validation/manual-final-review.md` |
| US-005 | Agent CLI 与 README | 未运行 | `specs/005-skill-cli/validation/us5-final-review.md`、`us5-poc.md` |
| US-006 | 来源检查、自动替换、状态与调度 | 未运行 | `specs/006-source-auto-update/validation/us6-final-review.md`、`us6-poc.md` |

## 4. 初始缺口登记（待后续任务关闭或保留）

- T041 macOS 未验证（`specs/specs/001-preserve-skill-content/validation/platform.md`）。
- US-005 真实 `gh api` 导入与 `--wait` 运行发现未补验（`specs/specs/005-skill-cli/validation/us5-final-review.md`）。
- 生产 environment 审批、部署失败注入、发布后 MIME/缓存未验证。
- 真实 403/限流、真实截断/子模块/符号链接、二进制下载逐字节对比未运行。
- 生产来源为空；Demo-002 只能写“受控通过”。
- 2026-11-15 03:17 窗口尚未到达；2026-11-14 延迟 run `43533439066` 只作为调度触发证据。

## 5. 更新规则

- T003 已建立证据索引 `validation/evidence-index.md`；本矩阵只补证据列，不改变状态。
- T007/T010/T013 更新对应 Demo 和 AC；T016/T017 更新保真/安全；T022 做最终复核。
- 任何未运行项保留在矩阵中，不能删除或改成通过。
