# US-007 Evidence Index

**日期**: 2026-11-14
**范围**: T003；汇总 US-001～US-006 的 validation、POC 运行 ID、生产页面和测试入口。
**状态**: 索引只提供证据位置，不改变 `acceptance-matrix.md` 的初始 `未运行` 状态。

## 1. 故事证据入口

| 故事 | 主要 validation | 关键运行/测试 |
|---|---|---|
| US-001 | `specs/001-preserve-skill-content/validation/acceptance.md`、`us1-migration.md`、`us1-test-contracts.md`、`us2-browser.md`、`us3-failures.md`、`final-review.md`、`platform.md`；`specs/007-overall-acceptance/validation/demo-001.md`、`fidelity.md` | `tests/integration/migration.test.js`、`tests/integration/distribution.test.js`、`tests/integration/untrusted-content.test.js`；T041 macOS 未运行 |
| US-002 | `specs/002-search-detail-share-redesign/validation/us2-search.md`、`us2-detail.md`、`us2-accessibility.md`、`us2-cross-browser.md`、`us2-performance.md`、`us2-regression.md`、`us2-build.md`、`us2-final-review.md` | `tests/unit/search-core.test.js`、`tests/unit/list-view.test.js`、`tests/unit/share-link.test.js`、`tests/unit/app-*.test.js` |
| US-003 | `specs/003-validate-build-publish/validation/us3-snapshot.md`、`us3-links.md`、`us3-same-run.md`、`us3-recovery.md`、`us3-security.md`、`us3-summary.md`、`us3-regression.md`、`production-pages.md` | POC-002 runs `42355651634`、`42355755607`、`42355846761`、`42377824309`、`42377905399`；生产 `42396936423`、`42397297833` |
| US-004 | `specs/004-manual-skill-maintenance/validation/manual-add.md`、`manual-replace-remove-recovery.md`、`manual-failures.md`、`admin-entry.md`、`manual-final-review.md`；`specs/007-overall-acceptance/validation/demo-001.md` | `tests/integration/manual-maintenance.test.js`、`tests/integration/invalid-batch.test.js` |
| US-005 | `specs/005-skill-cli/validation/us5-add.md`、`us5-replace.md`、`us5-import.md`、`us5-status.md`、`us5-readme.md`、`us5-quickstart.md`、`us5-poc.md`、`us5-real-gh.md`、`us5-final-review.md`；`specs/007-overall-acceptance/validation/demo-001.md` | POC-002 runs `42395342747`、`42395444891`、`43612050209`、`43612262185`；真实 `gh api`/`--wait` 已补验 |
| US-006 | `specs/006-source-auto-update/validation/preflight.md`、`us6-check.md`、`us6-apply.md`、`us6-conflict.md`、`us6-license.md`、`us6-status.md`、`us6-workflow.md`、`us6-poc.md`、`us6-quality.md`、`us6-final-review.md`、`us6-quickstart.md` | POC-003 runs 见下；生产 push `43421560371`、`43450476280`、`43509219426`；手动 sync `43421951464`；延迟 schedule `43533439066` |

## 2. POC 与生产运行索引

| 场景 | run ID | 结果摘要 | 证据 |
|---|---|---|---|
| US-005 POC-002 新增 | `42395342747` | submitted → published | `005-skill-cli/validation/us5-poc.md` |
| US-005 POC-002 替换 | `42395444891` | submitted → published | 同上 |
| US-005 真实导入 | `43612050209` | `us5-real-import` 提交 `19bf63c...`；build/deploy success | `005-skill-cli/validation/us5-real-gh.md` |
| US-005 真实 `--wait` | `43612262185` | `us5-real-wait` 提交 `1017dd4...`；published | 同上 |
| US-006 基线同步 | `43208732789` | sync/build/deploy success；提交 `0c68fed4c008` | `006-source-auto-update/validation/us6-workflow.md` |
| US-006 v2 替换 | `43208983544` | sync/build/deploy success；提交 `7b439a18f6d3` | 同上 |
| US-006 无变化 | `43209635536` | sync success；build/deploy skipped | 同上 |
| US-006 许可基线 | `43373881404` | 提交 `40d8cfc33d69`；写入 `last_synced_license` | `us6-license.md` |
| US-006 许可变化 | `43374128999` | policy_blocked；build/deploy skipped | 同上 |
| US-006 恢复 MIT | `43374438621` | unchanged；build/deploy skipped | 同上 |
| US-006 部署失败 | `43420335014` | sync/build success；deploy failure；旧站保留 | `us6-status.md` |
| US-006 同提交重跑 | `43420502326` | sync skipped；build/deploy success；无新内容提交 | 同上 |
| US-006 受控 revert | `43420712186` | build/deploy success；revision 恢复 | 同上 |
| 生产 push | `43421560371` | sync skipped；build/deploy success | `us6-workflow.md` |
| 生产手动 sync | `43421951464` | sync success；无变化；build/deploy skipped | 同上 |
| 生产延迟 schedule | `43533439066` | sync success；build/deploy skipped；08:19 CST | 同上 |

## 3. 测试与安全检查入口

| 检查 | 入口 | 最近结果 |
|---|---|---|
| 单元/集成测试 | `npm test`（`tests/unit/*.test.js`、`tests/integration/*.test.js`、`tests/integration/publish/*.test.js`） | 286 项：284 通过、0 失败、2 跳过 |
| Lint/格式 | `npm run lint`、`npm run format:check` | 最近通过 |
| 凭证/源码/依赖 | `npm run security` | secrets 362、code 56、deps 1，findings 0 |
| 生产站点只读 | `https://chengxuan2002-droid.github.io/skill-gallery/`、`assets/search-index.json` | 首页 200、4 项、revision `faa0f345...` |
| 发布目标检查 | `node scripts/publish-check.js target/artifact` | 见 US-003 validation |

## 4. Demo-001 本次证据

| 任务 | 命令/检查 | 结果 | 证据 |
|---|---|---|---|
| T004 手动维护 | `node --test tests/integration/manual-maintenance.test.js` | 7/7 通过 | `demo-001.md` |
| T005 Agent CLI | `add`/`replace`/`import`/`status`/`args` 测试 | 28/28 通过 | `demo-001.md` |
| T006 公开取用 | 生产首页/索引/详情/raw/ZIP 只读检查 | 4 项；raw/ZIP 字节一致 | `demo-001.md`、`fidelity.md` |
| T006 搜索/复制 | `search-core`、`list-view`、`share-link` 单测 | 16/16 通过；浏览器未重跑 | `demo-001.md` |

## 5. 使用规则

- 本索引只指向已有证据；不能把“有文件”当作“已通过”。
- 真实 403/限流、T041 macOS、US-005 真实 `gh`/`--wait`、生产 environment/部署失败注入/MIME 缓存
  的已关闭/未运行状态以 `residual-gaps.md` 为准；关闭项仍需保留证据链接。
- 状态变更只能由后续验收任务写入，并附证据；不得用本索引替代实测。

## 6. US-007 本次新增证据

| 任务 | 证据 | 结果 |
|---|---|---|
| T008–T010 | `demo-002.md` | POC-003 受控通过；生产来源为空 |
| T011–T013 | `demo-003.md` | 失败/冲突/恢复受控通过；49 项定向测试 |
| T014–T015 | `fixed-address.md`、`remote-errors.md` | 生产固定地址/详情/raw/ZIP、MIME/缓存头只读复核；真实 403 观察 |
| T016 | `fidelity.md` | 原件/附件/ZIP/模式逐字节复核；4/4 distribution 测试 |
| 补验 | `production-environment.md` | 生产 environment 审批、部署失败/旧站保留/恢复 |
| 补验 | `macos-ci.md` | GitHub-hosted macOS runner `43588719771`；T041 补验 |
| T017 | `security.md` | `npm run security` 0 发现；27 项安全/路径测试 |
| T018 | `residual-gaps.md` | 未运行项、影响与补验方式 |
| T019 | `handoff.md` | 干净 worktree 命令与退出码 |
| T020 | README、AGENTS.md | US-007 状态/未运行项/恢复入口 |
| T021 | `quality.md` | 本地 `npm run check` 286 项；US-005 分支 run `43613336137` 在 Node 26.3/Linux 通过（286 项 285/0/1）；`npm run security` 0 发现 |
| T022 | `final-review.md` | 有条件验收/交接，不宣称整包通过 |
