# US-004 最终差异复核（T017）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 对照 `spec.md`、`contracts/` 与 `validation/` 复核 T001–T016 的实际差异、验证结果和
未运行项；只读检查仓库与远程状态，不推送、不部署、不切换生产 Pages。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）；
受控运行在 GitHub runner `ubuntu-24.04`、Node 26.3.0。

## 1. 差异范围

以 US-003 tip `b57570daffc23bf515cef70ebc3bc785f91284cb` 为基线，US-004 共 18 个提交，变更仅涉及：

| 文件 | 变更 |
|---|---|
| `index.html` | 页脚增加低权重“管理”外链 |
| `README.md`、`AGENTS.md` | 手动维护步骤、字段、失败处理、替换/下架/恢复、状态 |
| `tests/unit/site-entry.test.js` | 入口静态契约 |
| `tests/integration/manual-maintenance.test.js`、`tests/support/manual-fixture.js` | 手动维护集成测试与夹具 |
| `specs/004-manual-skill-maintenance/**` | 规格、计划、任务、契约与 validation |
| `tasks.md`/`plan.md` 状态 | 进度与证据入口 |

复核结果：

| 检查 | 结果 |
|---|---|
| `skills/`、`catalog/`、`assets/`、`scripts/`、`.github/workflows/`、`package.json`、`package-lock.json` | 无差异 |
| 内容 schema、搜索/详情前端、US-003 发布链 | 未修改 |
| 新增 npm 依赖 | 无 |
| `dist/` 纳入版本控制 | 0 个文件 |
| 生产 Pages 设置 | 未修改；仍为 `build_type=legacy`、`source=main:/`、`status=built` |
| 生产 `main` | `365d577e8eb7460d3619d98201425a4b3a93c255`，未变 |
| US-004 分支 | `codex/us-004-manual-maintenance` 仅本地，未推送 |

## 2. 验证汇总

| 验证 | 结果 |
|---|---|
| `npm test` | 220 项：218 通过、0 失败、2 跳过 |
| `npm run lint` / `npm run format:check` | 退出码 0 |
| `npm run security` | secrets 268 文件、code 37 文件、deps 1 文件，findings 均为 0 |
| 管理入口契约 | 页脚链接指向受信任仓库，`target="_blank"`、`rel="noopener"`；无表单/文件输入 |
| 隔离新增/失败/替换/下架/恢复 | [manual-add.md](manual-add.md)、[manual-failures.md](manual-failures.md)、[manual-replace-remove-recovery.md](manual-replace-remove-recovery.md) |
| 受控 POC-002 | 新增/非法/替换/下架运行均完成；非法批次 build failure、deploy skipped，站点不变；替换后单版本，下架后详情 404、索引恢复 4 项。见 [manual-poc.md](manual-poc.md) |

公开页面复核：新增内容仅为页脚外链；`assets/`、搜索索引与详情 schema 未变，公开页面不包含
运行日志、错误码或后台状态。

## 3. 验收映射

| 验收 | 本轮证据 | 状态 |
|---|---|---|
| AC-006 手动新增/修改/替换/下架 | 集成测试 + 隔离演练 + POC-002 运行 | 本地/受控通过；生产未运行 |
| AC-008 访客只读、未授权无副作用、凭证不回显 | 入口静态断言、安全扫描、US-003 未授权证据 | 本地/受控通过；生产未运行 |
| AC-011 状态分离、失败保留、单版本、恢复 | US-003 发布链证据 + POC 非法/替换/下架运行 + 隔离恢复演练 | 本地/受控通过；生产未运行 |
| FR-005/007/009/010 | 见上述场景、README 与契约 | 覆盖本轮范围 |
| NFR-003/004/006 | 安全扫描 0 findings；失败保留证据；README 可独立执行 | 本地/受控通过 |

成功标准：US004-SC-01/02/03/04 由隔离与 POC 证据支撑；US004-SC-05 的说明步骤已可执行，
但未由独立维护者从零复跑。

## 4. 未运行与剩余风险

- 生产 Pages 未切换；没有生产手动发布、environment 审批或线上回滚验证。
- POC-002 使用精简 workflow，未远程运行完整 `npm run check`/`npm run security`。
- 未在浏览器验证页脚视觉、键盘焦点、移动端布局、详情/分享/下载交互或下架后的旧链接跳转。
- 未验证线上 MIME、缓存和直接资源响应；本地/受控构建不替代发布后检查。
- 未在 Node 26.3.0/Linux 本地复验；受控运行由 GitHub runner 覆盖。
- US-004 分支未推送、未创建 PR；US-003 PR #1 仍 OPEN，main 未合并。
- POC 仓库保留 T016 的 5 个测试提交（`3d84341`～`e05dd3e`），内容已恢复；临时仓库未删除。
- US-005～US-007（Agent CLI、自动更新、整体验收）仍未开始。

## 5. 结论

US-004 的本地与受控范围完整：管理入口、手动维护说明、合法新增、非法批次、替换、下架、恢复与
权限边界均有可追溯证据；未发现对内容 schema、搜索/详情前端、发布权限或生产 Pages 的越界改动。
生产启用与线上发布仍需单独授权和验证，不能把本记录当作线上成功。
