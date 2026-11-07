# 旧实现内容损失复现

日期：2026-11-03。任务 T004；映射 FR-004、NFR-001、DEC-002、AC-002。
本记录只复现旧实现缺陷，不表示新构建或业务验收已通过。

## 环境与隔离

- Windows 11；本机实际 Node 22.21.0、npm 10.9.4。
- 计划基线 Node 26.3.0 本轮不可用（官方下载与镜像均未能在可用时间内完成），因此不得把本记录当作 26.3.0 或 Linux 证据。
- 测试在系统临时目录复制 `scripts/build-index.js`、`assets/app.js`、`tests/fixtures/legacy/legacy-skill.md` 后执行；未运行仓库正式目录中的旧构建，未改写任何原件。

## 实际结果

命令：`node --test tests/integration/export-regression.test.js`

- exit 0；1 项通过，1 项跳过（跳过的是需要显式开启的保真红灯断言）。
- 隔离旧构建 exit 0，生成 1 条索引；`content` 保留表格文本，但代码围栏 `const preserved = 'code fence';` 已被移除。
- 旧 `buildFullMarkdown` 输出的 frontmatter 不含 `version: 9.9.9`，正文不含代码围栏和原始嵌套字段。

红灯复现命令：`LEGACY_FIDELITY_EXPECTED=1 node --test tests/integration/export-regression.test.js`

- exit 1；完整原文断言失败，实际导出缺少 `version: 9.9.9`，且代码围栏已丢失。
- 该失败是 T004 要求的基线证据，不代表当前缺陷已被修复。

## 后续约束

T018/T024 必须对同一源字节改验新 raw 出口；不得把上述有损文本重建算法复制为测试期望。
在 Node 26.3.0 与 Linux 上重新执行前，本记录只证明旧缺陷在本次环境可复现。
