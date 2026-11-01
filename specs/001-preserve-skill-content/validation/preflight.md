# 工程初始化前置检查

日期：2026-11-02。用户已授权执行 project-bootstrap；仅本地工程基线，不开展业务实现、CI、远程写入或部署。

固定站点：https://chengxuan2002-droid.github.io/skill-gallery/；资源前缀 /skill-gallery/。
Node 26.3.0、npm 11.16.0；根工程使用 CommonJS。

## 既有工作区

以下状态于首次写入前记录；用户既有修改/未跟踪资产受保护。README、当前主文档及功能 plan/tasks 仅定向追加本轮工程状态。

```text
 M README.md
 M docs/superpowers/plans/2026-08-02-skill-gallery.md
 M specs/2026-08-02-skill-gallery-design.md
?? .agents/
?? .specify/
?? AGENTS.md
?? docs/AiProgrammingGuide.md
?? docs/DemandAnalysis.md
?? docs/IndustryResearch.md
?? docs/TechnicalSolution.md
?? handoff/handoff-20260803-000000.md
?? skills/office2md/
?? specs/001-preserve-skill-content/
```

完整文件摘要与模式暂存于项目外，仅用于前后核对；不保存文件内容或凭证。
四项 Skill 六个文件基线见 migration-baseline.json；office2md 未纳管，不执行、不安装、不收录、不修改。

## 验收范围

1. 补齐根运行时、精确开发依赖与锁，隔离安装验证。
2. Lint/格式/受限测试入口及凭证、源码、依赖安全检查，用拒绝样例验证真实退出码。
3. 核对原件摘要、执行位及无关文件，记录真实结果。

原有业务任务不因此完成；T002/T003 的业务依赖和数据夹具仍待后续实施。
