# US-007 Acceptance Matrix

**日期**: 2026-11-14
**状态骨架**: T002 建立；T003 补入证据入口；T007/T010/T013 更新 Demo-001～003 及对应 AC；T022
最终复核后为有条件验收/交接；2026-11-14 补验生产 environment/部署失败、MIME/缓存基础头、真实 403
和 macOS runner 后，剩余子项见 `residual-gaps.md`，仍不判定整包通过。
**状态口径**: 只允许 `通过`、`受控通过`、`未运行`、`失败`。未运行不得计为通过。
**Demo-002 口径**: 用户已确认 POC-003 受控证据可作为“受控通过”；不得写成生产自动更新已发生。

## 1. Demo 场景

| ID | 验收点 | 关联 | US-007 状态 | 证据入口 | 备注 |
|---|---|---|---|---|---|
| Demo-001 | 手动/Agent 维护到检索、详情、复制、下载 | US-001、US-005；AC-001/008/012/015 | 受控通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`fidelity.md`；`specs/004-manual-skill-maintenance/validation/manual-add.md`、`specs/005-skill-cli/validation/us5-add.md` | 手动/CLI/生产数据已验证；浏览器复制未重跑 |
| Demo-002 | 来源 v1→v2 自动更新、单版本、旧附件清理 | US-006、US-007；AC-009/011/014 | 受控通过 | `specs/007-overall-acceptance/validation/demo-002.md`、`specs/006-source-auto-update/validation/us6-poc.md`、`us6-license.md`、`us6-status.md`、`us6-workflow.md`；run `43533439066` | POC-003 受控证据；生产 `source_tracking` 为 `null`，未发生生产自动更新 |
| Demo-003 | 404/冲突/非法候选/部署失败→状态→修复/恢复 | US-003、US-007；AC-008/010/012/014 | 受控通过 | `specs/007-overall-acceptance/validation/demo-003.md`、`production-environment.md`、`specs/003-validate-build-publish/validation/us3-recovery.md`、`specs/006-source-auto-update/validation/us6-status.md`、`us6-conflict.md` | POC/隔离 + 49 项定向测试；生产 environment/部署失败已补验；真实 429/限流未运行 |

## 2. AC 逐项矩阵

| ID | 验收点摘要 | 关联 | US-007 状态 | 证据入口 | 备注 |
|---|---|---|---|---|---|
| AC-001 | 数据与迁移：四项 slug/附件保持，非法批次非零退出 | FR-001、FR-011 | 通过 | `specs/001-preserve-skill-content/validation/acceptance.md`、`us1-migration.md`、`tests/integration/migration.test.js` | 四项迁移/非法批次已验收；T021 全量测试通过；T041 macOS runner 已补验 |
| AC-002 | 原件/目录包保真：路径、字节、未知字段、许可 | FR-001、FR-004、NFR-001 | 通过 | `specs/007-overall-acceptance/validation/fidelity.md`、`specs/001-preserve-skill-content/validation/acceptance.md`、`tests/integration/distribution.test.js` | 生产 raw/ZIP 已逐字节核对 |
| AC-003 | 搜索：精准/模糊/多维筛选/排序/分享恢复 | FR-002 | 受控通过 | `specs/002-search-detail-share-redesign/validation/us2-search.md`、`tests/unit/search-core.test.js` | 16 项搜索/列表/分享测试通过；未重跑生产浏览器 |
| AC-004 | 详情：功能/用法/原文/版本/作者/缺失提示 | FR-003 | 受控通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`specs/002-search-detail-share-redesign/validation/us2-detail.md` | 生产 JSON 字段与下载入口已核对；视觉复用 US-002 |
| AC-005 | 旧 hash 链接/替换后读取新版/复制失败提示 | FR-004 | 受控通过 | `specs/002-search-detail-share-redesign/validation/us2-detail.md`、`tests/unit/share-link.test.js` | 复制失败提示由单测覆盖；未重跑真实剪贴板 |
| AC-006 | GitHub 后台手动上传/替换/下架/非法批次 | FR-005 | 通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`specs/004-manual-skill-maintenance/validation/manual-add.md` | 7 项手动维护测试通过 |
| AC-007 | Agent 预览/提交/重复/替换/状态/退出码 | FR-006、NFR-006 | 通过 | `specs/007-overall-acceptance/validation/demo-001.md`、`specs/005-skill-cli/validation/us5-add.md` | 28 项 CLI/状态测试通过 |
| AC-008 | 访客只读、未授权无写入、无凭证回显 | FR-007 | 受控通过 | `specs/007-overall-acceptance/validation/security.md`、`specs/003-validate-build-publish/validation/us3-security.md`、`tests/integration/publish/publish-security.test.js` | POC 匿名 401/凭证零回显/只读；生产未授权写与 fork/受限身份未运行 |
| AC-009 | 自动替换：slug/单版本/增删附件/站内备注 | FR-008、NFR-001 | 受控通过 | `specs/007-overall-acceptance/validation/demo-002.md`、`specs/006-source-auto-update/validation/us6-apply.md`、`us6-poc.md` | POC-003 v1→v2 受控；生产来源未配置 |
| AC-010 | 失败与冲突：404/限流/非法/许可/本地修改/重跑 | FR-008、FR-009、NFR-004 | 受控通过 | `specs/007-overall-acceptance/validation/demo-002.md`、`demo-003.md`、`specs/006-source-auto-update/validation/us6-conflict.md`、`us6-check.md`、`us6-license.md`、`us6-status.md` | 真实 404/许可变化/冲突/部署失败有证据；真实 403/限流未运行；Demo-003 已复核 |
| AC-011 | 状态与恢复：检查/更新/部署/重跑/revert | FR-009 | 受控通过 | `specs/007-overall-acceptance/validation/demo-003.md`、`production-environment.md`、`specs/006-source-auto-update/validation/us6-status.md`、`specs/003-validate-build-publish/validation/us3-recovery.md`、`specs/005-skill-cli/validation/us5-status.md` | POC 部署失败/同提交重跑/revert + 隔离演练；生产 environment/部署失败已补验 |
| AC-012 | 内容边界：HTML/URL/越界/链接/脚本不执行 | FR-003、FR-007、FR-008、NFR-003 | 受控通过 | `specs/007-overall-acceptance/validation/demo-003.md`、`specs/001-preserve-skill-content/validation/us3-failures.md`、`tests/integration/untrusted-content.test.js`、`tests/unit/path-attacks.test.js`、`specs/006-source-auto-update/validation/us6-conflict.md` | 不可信内容/路径/脚本不执行测试通过；真实远程截断/子模块/符号链接未运行；T017 复核安全边界 |
| AC-013 | 界面：360/768/1440、明暗、键盘、对比度 | FR-010、NFR-005 | 受控通过 | `specs/007-overall-acceptance/validation/fixed-address.md`、`specs/002-search-detail-share-redesign/validation/us2-accessibility.md`、`us2-cross-browser.md` | Chrome/Firefox/WebKit 夹具通过；Safari/移动实机/读屏器未运行 |
| AC-014 | 构建部署：白名单、同快照、旧地址/子路径/刷新 | FR-011、NFR-004、NFR-006 | 受控通过 | `specs/007-overall-acceptance/validation/fixed-address.md`、`production-environment.md`、`handoff.md`、`specs/003-validate-build-publish/validation/us3-links.md`、`us3-same-run.md`、`production-pages.md`、`specs/006-source-auto-update/validation/us6-workflow.md` | 生产地址/子路径/旧链接、同快照、MIME/缓存基础头、environment 审批和部署失败已补验；CDN/强刷未运行 |
| AC-015 | 性能：1,000 项/10 MiB/50 查询 p95 | NFR-002 | 受控通过 | `specs/002-search-detail-share-redesign/validation/us2-performance.md`、`us2-cross-browser.md` | 隔离夹具 p95 39.9/48.0/50.0ms；不是生产网络或设备承诺 |

## 3. 故事状态汇总

| 故事 | 范围 | US-007 状态 | 证据入口 |
|---|---|---|---|
| US-001 | 原件保真、迁移、完整取用 | 受控通过 | `specs/007-overall-acceptance/validation/macos-ci.md`、`specs/001-preserve-skill-content/validation/final-review.md`、`acceptance.md` |
| US-002 | 搜索、详情、分享、可访问 | 受控通过 | `specs/002-search-detail-share-redesign/validation/us2-final-review.md` |
| US-003 | 校验、构建、固定地址发布 | 受控通过 | `specs/007-overall-acceptance/validation/production-environment.md`、`specs/003-validate-build-publish/validation/us3-final-review.md`、`production-pages.md` |
| US-004 | GitHub 后台手动维护 | 受控通过 | `specs/004-manual-skill-maintenance/validation/manual-final-review.md` |
| US-005 | Agent CLI 与 README | 受控通过 | `specs/005-skill-cli/validation/us5-final-review.md`、`us5-poc.md` |
| US-006 | 来源检查、自动替换、状态与调度 | 受控通过 | `specs/006-source-auto-update/validation/us6-final-review.md`、`us6-poc.md` |

故事状态的未运行子项：US-001 物理 Mac 变体；US-002 Safari/移动实机；US-003 CDN/浏览器强刷；
US-004 真实后台 UI/浏览器复制；US-005 真实 `gh api`/`--wait`；US-006 生产真实来源/后续调度窗口。
均不计为通过，详见 `residual-gaps.md`。

## 4. 初始缺口登记（待后续任务关闭或保留）

- T041 macOS 已由 GitHub-hosted runner `43588719771` 补验；物理 Mac/所有 macOS 变体未覆盖。
- US-005 真实 `gh api` 导入与 `--wait` 运行发现未补验（`specs/005-skill-cli/validation/us5-final-review.md`）。
- 生产 environment 审批和部署失败注入已补验并恢复；MIME/缓存基础头已复核，CDN/强刷未运行。
- 真实 source-sync 403（已观察一次真实 403）和 429（未触发）、真实截断/子模块/符号链接、
  二进制下载逐字节对比未运行。
- 生产来源为空；Demo-002 只能写“受控通过”；生产真实来源自动更新未运行。
- 2026-11-15 03:17 窗口尚未到达；2026-11-14 延迟 run `43533439066` 只作为调度触发证据。
- 完整缺口、影响和补验方式见 `residual-gaps.md`；最终结论见 `final-review.md`。

## 5. 更新规则

- T003 已建立证据索引 `validation/evidence-index.md`；T007/T010/T013 更新对应 Demo 和 AC；
  T016/T017 更新保真/安全；T022 已完成最终复核。
- 任何未运行子项保留在 `residual-gaps.md`，不能删除或改成通过；受控通过不等于整包通过。
