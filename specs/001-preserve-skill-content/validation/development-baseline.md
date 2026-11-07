# 可接续开发的完整基线

日期：2026-11-02（Asia/Shanghai）。依据用户“首先补齐并推送可接续开发的完整基线”的授权。
开发分支：`codex/development-baseline-20261102`；基于 `main` 的 `365d577`，不合入主分支或执行发布。

## 本次收录与精准修订

- 将此前未跟踪的两份 0.2 上游规范、宪章 1.0.0、US-001 规格/研究/模型/契约/检查表/quickstart、
  项目级 Skills 和 Spec Kit 脚本/模板/来源配置纳入版本控制，补齐既有 plan/tasks 的输入。
- 保留 README 的规范入口及两份旧设计/计划的历史提示；新增换电脑、更换 Agent、安装检查及功能指针恢复说明。
- 按宪章要求移除临时 Sync Impact Report 及其清理提示；不改变原则、版本或批准日期。
- quickstart 移除本机绝对路径，并区分已具备的工程入口与尚未实现的业务入口。
- `.specify/integrations/` 两份 manifest 中的文件摘要均与实际受控文件匹配；这些记录表示生成来源，
  不携带机器执行信任或 GitHub 写入授权。未修改生成器、模板或业务代码。

## 排除与保留

新增交接记录和未收录的 `skills/office2md/` 未暂存；它们的字节及权限保持不变。
既有已跟踪的 `handoff/handoff-20260802-201238.md` 沿用历史，不新增、删除或改写。
`.specify/feature.json` 保持本机忽略；依赖、扫描器、系统杂项及凭证不进入提交。
所有 Skill 原件、线上资源、索引和工作流保持原样。

## 实际验证

本轮工作区及由 Git 暂存内容导出的隔离副本分别执行：

| 检查 | 结果 |
|---|---|
| `npm run check` | 退出 0；Lint、只读格式检查通过；24 项受信任测试通过，零跳过 |
| `npm run security` | 退出 0；凭证及有限源码规则通过；依赖仍有 6 个 moderate，无 high/critical |
| `bash -n` 检查全部 `.specify/scripts/bash/*.sh` | 通过 |
| 新增 JSON 解析、上游及当前功能等规范本地 Markdown 路径检查 | 通过，零缺失路径；未将锚点或网络链接可达性算作已验证 |
| `git diff --cached --check` | 通过 |

隔离副本未复制本机 feature 指针、未收录 Skill 或新增交接文件：

1. 从根锁执行 `npm ci --ignore-scripts --no-audit --no-fund`，退出 0。
2. 复用本机 `.tools/`，执行 `npm run setup:security`，固定版本核对通过；未验证新机器首次下载安装。
3. 按 README 设置 `SPECIFY_FEATURE_DIRECTORY`，执行 `check-prerequisites.sh --json --require-spec --require-tasks --include-tasks`，
   退出 0，找到 spec/plan/tasks 及关联资料，重新生成的 `.specify/feature.json` 仍被 Git 忽略。
4. 在此隔离副本执行上述完整工程与安全检查，结果一致。

本轮验证环境为 macOS；不声称已经在另一台电脑或 Linux 完整复验。
Spec Kit 前置检查只证明资料存在，不是新的 `speckit-analyze` 或业务 AC 验收。

## 接续边界

任务表仍有 51 项：已完成 T001、T044～T051；T002/T003 只具备工程部分，业务工作尚未完成。
2026-11-03 后续：T002～T010 已完成，跨平台基线与 C-01 缺口修正见 [baseline-remediation.md](baseline-remediation.md)；
本文任务统计保留当时快照。
下一轮先复核规格/方案/任务一致性，再按明确授权实施；不要重跑初始化或覆盖已有规范。
`build`、正式 preview、迁移和上传 CLI 仍不是已实现能力。
交接及开发资料不能直接作为网站产物；合入主分支前须核对发布白名单。
本轮不改变 Pages、权限、通知或定时任务，也未验证网站监测的首次定时事件。
