# T002～T010 基础层验证记录

日期：2026-11-03。范围：US-001 的 T002～T010。映射 FR-001、FR-004、FR-011、NFR-001、NFR-003、NFR-006，
DEC-002、DEC-003、DEC-005、DEC-009，AC-001、AC-002、AC-012 的本地处理子集，以及 AC-014 的本地支撑。
本记录不表示 T011 以后任务、业务 AC、生产构建或发布已完成。

## 环境

- Windows 11；实际 Node 22.21.0、npm 10.9.4。
- 计划基线与 `.node-version` 仍为 Node 26.3.0；官方下载与镜像在本环境未能在可用时间内完成，
  因此本轮证据不能冒充 26.3.0、Linux 或 macOS 的验证。
- 依赖精确锁定：yaml 2.9.1、marked 18.1.2、sanitize-html 2.18.1、yazl 3.3.1、minisearch 6.3.0；
  yauzl 3.4.0 仅开发依赖。隔离副本 `npm ci --ignore-scripts` exit 0。

## 提交与结果

| 任务 | 提交                 | 实际验证                                                                           |
| ---- | -------------------- | ---------------------------------------------------------------------------------- |
| T002 | `56e697e`            | `npm ls --depth=0` 精确版本；隔离 `npm ci` exit 0；engines 警告因 Node 22 环境     |
| T003 | `5afcfeb`、`61d14ce` | 夹具 3/3 通过；原件摘要不变；未创建 catalog；空目录运行时创建                      |
| T004 | `8841a29`            | 旧实现 1 项通过、1 项按设计跳过；`LEGACY_FIDELITY_EXPECTED=1` 时完整断言按预期失败 |
| T005 | `f38f09b`            | YAML PoC 8/8；BOM/CRLF、折叠、嵌套、非法键、自定义 tag、别名上限                   |
| T006 | `0cdf9f4`            | 渲染/清理/ZIP 4/4；活动内容清理、伪链接不生成 href、ZIP 字节/模式/空目录           |
| T007 | `afd77f0`            | 先写 17 项契约测试；入口未实现时按预期红                                           |
| T008 | `44521a9`、`2bc5ae4` | 17/17 通过；路径、点资源、凭证规则、容量边界与脱敏诊断                             |
| T009 | `70f0be2`            | 先写 6 项快照契约；入口未实现时按预期红                                            |
| T010 | `c922fd4`            | 6/6 通过；四项真实原件只读快照成功（1/1/1/3 文件）                                 |

新增测试合计 40 项：39 通过、1 项按设计跳过（T004 的基线红灯断言），0 失败。

## 回归与限制

- `npm test`：64 项，58 通过、5 失败、1 跳过。5 项失败均来自既有 bootstrap 测试在 Windows
  无法创建 `node_modules` 符号链接（EPERM），不是本轮代码或测试断言失败。
- `npm run lint`：exit 0。
- 新增/修改文件 Prettier 检查通过；全仓 `format:check` 仍因工作区既有文件被 CRLF checkout
  报 17 项差异，未批量重排格式。
- `npm run security:secrets` 与 `security:code`：exit 2、`TOOL_UNAVAILABLE`；
  `npm run setup:security`：`UNSUPPORTED_PLATFORM`。当前安装器只覆盖 macOS/Linux，
  因此不能声称真实扫描器已在本环境通过。
- 四项 Skill 快照只读；执行前后 `git status` 未出现原件改动。未运行任何收录脚本。
- T004 的红灯复现与 T006 的 PoC 限制分别见 [regression.md](regression.md)、
  [render-archive-poc.md](render-archive-poc.md)；T005 见 [yaml-poc.md](yaml-poc.md)。
- 未推送、未发布；`catalog/`、`dist/`、迁移、构建、预览与前端取用仍属于后续任务。
