# US-005 最终差异复核（T022）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 对照 `spec.md`、`contracts/` 与 `validation/` 复核 T001–T021 的实际差异、验证结果和
未运行项；只读检查仓库与远程状态，不推送、不部署、不切换生产 Pages。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）；
受控运行在 GitHub runner `ubuntu-24.04`、Node 26.3.0。

## 1. 差异范围

以 US-004 tip `cd2144ea4b45165d9a0d14b4695c8df9d9b80473` 为基线，US-005 共 26 个提交，变更仅涉及：

| 文件 | 变更 |
|---|---|
| `scripts/skill-cli.js`、`scripts/lib/skill-cli/*.js` | 新增 CLI 入口与 args/output/candidate/workspace/publish/replace/import/source-github/status 模块 |
| `tests/unit/skill-cli-{args,status}.test.js`、`tests/integration/skill-cli-{add,replace,import}.test.js`、`tests/support/skill-cli-fixture.js` | 新增参数、状态、预览/新增、替换、导入与夹具测试 |
| `README.md`、`AGENTS.md` | Agent 命令契约、状态与边界 |
| `specs/005-skill-cli/**` | 规格、计划、任务、契约与 validation |

| 检查 | 结果 |
|---|---|
| `skills/`、`catalog/`、`assets/`、`index.html`、`.github/workflows/`、`package.json`、`package-lock.json` | 无差异 |
| 内容 schema、搜索/详情前端、US-003 发布链 | 未修改 |
| 新增 npm 依赖 | 无 |
| `dist/` 纳入版本控制 | 0 个文件 |
| 生产 Pages | 未修改；仍为 `build_type=legacy`、`source=main:/`、`status=built` |
| 生产 `main` | `365d577e8eb7460d3619d98201425a4b3a93c255`，未变 |
| US-005 分支 | `codex/us-005-skill-cli` 仅本地，未推送 |

## 2. 验证汇总

| 验证 | 结果 |
|---|---|
| `npm test` | 241 项：239 通过、0 失败、2 跳过 |
| `npm run lint` / `npm run format:check` | 退出码 0 |
| `npm run security` | secrets 299 文件、code 47 文件、deps 1 文件，findings 均为 0 |
| 隔离预览/新增/替换/导入/状态 | 证据见 [us5-add.md](us5-add.md)、[us5-replace.md](us5-replace.md)、[us5-import.md](us5-import.md)、[us5-status.md](us5-status.md) |
| 受控 POC-002 | 新增 `92da16b`（run 42395342747）、替换 `5e5b75c`（run 42395444891），`status` 均为 `published`；见 [us5-poc.md](us5-poc.md) |

公开页面复核：CLI 不修改前端资产；`content_status`/`deploy_status` 分离，提交/构建成功不报告
published；诊断只含稳定码与位置。

## 3. 验收映射

| 成功标准 | 证据 | 状态 |
|---|---|---|
| US005-SC-01 预览零写入 | 集成测试、[us5-add.md](us5-add.md)、[us5-readme.md](us5-readme.md) | 通过 |
| US005-SC-02 发布字段与 published 时机 | 测试、POC 新增/替换 + status | 通过（受控） |
| US005-SC-03 noop/冲突 | 测试、[us5-replace.md](us5-replace.md) | 通过 |
| US005-SC-04 来源失败关闭 | 测试、[us5-import.md](us5-import.md) | 通过（注入来源） |
| US005-SC-05 凭证零回显/零执行 | 安全扫描、诊断断言 | 通过（本地） |
| US005-SC-06 等待真实状态 | 单测、[us5-status.md](us5-status.md) | 通过（固定状态） |
| FR-006/007/009/010 | 上述场景与 README | 覆盖本轮范围 |

## 4. 未运行与剩余风险

- 默认 `gh api` 来源读取与 release 策略未做真实网络验证；`import` 只在注入来源下验收。
- `--wait` 在 push 后立即查询可能尚未发现运行，按文档返回 `submitted/pending`；POC 替换后手动
  `status` 才得到 published。若要求“等待必达发布”，需增加运行发现重试并更新契约。
- 生产 Pages 未切换；没有生产发布、environment 审批或线上回滚验证（后续已切换，见第 6 节）。
- 未验证浏览器详情/分享/下载、MIME/缓存或移动端。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 本地复验；受控运行由 GitHub runner 覆盖。
- US-005 分支未推送、未创建 PR；US-003 PR #1、US-004 PR #2 仍 OPEN，main 未合并（后续均已合并，见第 6 节）。
- POC 仓库保留 `cli-poc-us5` 新增/替换内容；临时 clone 未保留。
- US-006/US-007（自动更新、整体验收）仍未开始。

## 5. 结论

US-005 的本地与受控范围完整：预览、新增、替换/冲突、来源导入、状态/等待、README 与权限/凭证边界
均有可追溯证据；未发现对内容 schema、前端、发布权限或生产 Pages 的越界改动。生产启用与线上发布
仍需单独授权和验证。

## 6. 后续状态（2026-11-12 同步）

本记录保留 2026-11-08 复核时点。此后 US-005 已推送并合并 main（PR #3），生产 Pages 已于
2026-11-08 切换为 GitHub Actions 并成功发布，证据见
[US-003 production-pages.md](../../003-validate-build-publish/validation/production-pages.md)。
真实 `gh api` 来源导入和 `--wait` 运行发现仍未补验；本记录不因此改写为生产验收通过。
