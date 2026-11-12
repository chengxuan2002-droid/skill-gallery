# Phase 0 Research: US-006 来源定期检查与自动替换

**Date**: 2026-11-12 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本文件记录技术决策、依据和替代方案；不改变业务规格。来源事实以 `docs/` 0.2 文档、现有代码与
当前官方资料为准。

## 1. GitHub 来源读取与不可变修订

- **Decision**: 复用 US-005 已验证的 GitHub 读取逻辑，将其提取为共享的
  `scripts/lib/github-source.js`；`scripts/lib/skill-cli/source-github.js` 保留兼容出口。
  使用结构化 `owner/repository`、`path`、`ref_policy`、`ref`，通过 `gh api` 解析分支、
  Release 或 pinned 提交，再读取同一 SHA 的递归树和 blob。`truncated`、子模块、符号链接、
  越界路径和普通网页 URL 全部失败关闭。
- **Rationale**: US-005 已有路径校验、错误映射、大小上限和注入读取器测试；复用可避免 M-05/M-06
  两套 API 行为，并保持固定提交、二进制与完整树语义一致。
- **Alternatives considered**:
  - 新增独立 Octokit/HTTP 读取器：引入新依赖和第二套错误/路径规则。
  - 逐文件 Contents API：更容易遗漏树截断/链接/子模块，且无法证明同一修订。
  - 抓取网页：不允许，无法保证完整性和不可变性。
- **Evidence**: `scripts/lib/skill-cli/source-github.js`、US-005 `us5-import`/`us5-final-review`、
  IndustryResearch R-012、TechnicalSolution 3.5。

## 2. 内容摘要、无变化与本地冲突

- **Decision**: 使用现有 `computeDigest`/`snapshotSkill` 的内容摘要（路径、字节、可执行位、
  空目录）；候选摘要等于当前内容摘要为 unchanged；当前内容摘要与
  `source_tracking.last_synced_digest` 不一致为 conflict；候选与上次同步修订不同但摘要相同
  只记录检查，不创建空提交。
- **Rationale**: 摘要覆盖完整清单而非只比较版本字符串；与 US-001/003/005 的字节保真和单版本
  证据一致。
- **Alternatives considered**:
  - 比较 `declared_version`：需求明确版本未变也可能更新，不足。
  - 比较文件 mtime/大小：不稳定，无法证明内容身份。
  - 直接比较 Git diff：依赖上游历史结构，不能覆盖所有来源策略。
- **Evidence**: `scripts/lib/content-store.js`、`scripts/lib/file-admission.js`、
  DemandAnalysis FR-008、TechnicalSolution 3.5。

## 3. 候选校验与完整替换

- **Decision**: 复用 `catalog-schema`、`validateSkillInput`/`snapshotSkill` 和 US-005 的临时
  候选目录；候选先完整获取并验证，再按新清单整体替换，删除旧附件，保留站内 display_name、
  tags、notes、usage、分类和来源配置（仅更新同步结果字段）。有效变更合并为一次批次提交。
- **Rationale**: 与构建器共用同一校验器，避免自动路径绕过手动/CLI 规则；整体替换满足当前
  单版本语义；批次提交使页面、索引、详情和下载来自同一内容快照。
- **Alternatives considered**:
  - 只覆盖同路径文件：会残留上游已删除附件，违反 AC-009。
  - 每个来源单独提交：会产生多份快照和多次部署，增加部分失败风险。
  - 改写上游 frontmatter 补站点字段：违反原件保真和元数据分离。
- **Evidence**: `scripts/lib/validate.js`、`scripts/lib/catalog-schema.js`、
  `scripts/lib/skill-cli/candidate.js`、TechnicalSolution 3.5、DemandAnalysis AC-009。

## 4. 许可策略

- **Decision**: 启用的自动来源必须能从同一修订的来源子树读取到可识别的许可文件（如 `LICENSE*`、
  `COPYING*`、`NOTICE*`）；仓库根/其他目录的许可只作为人工核对信息，不自动视为该子树适用许可。
  首次同步无子树许可即 policy_blocked；后续比较候选与当前内容中的许可文件路径和字节，缺失或
  变化暂停替换并报告。运行报告记录许可路径与摘要，不新增公开 schema 字段。
- **Rationale**: 许可必须可追溯且变化时暂停；利用当前内容树已有许可文件即可比较，不引入新持久
  字段或额外 API，也不会假定整个仓库同一许可。
- **Alternatives considered**:
  - GitHub license API：只覆盖仓库级许可，子目录/Skill 适用许可可能不同。
  - 只看 catalog 的 `license` 字符串：无法发现许可文件内容变化。
  - 自动替换并稍后审查：违反 FR-008 的许可暂停要求。
- **Evidence**: DemandAnalysis FR-008、AC-010、TechnicalSolution 7、IndustryResearch R-004。

## 5. 工作流集成与写入认证

- **Decision**: 在现有 `maintain.yml` 增加 `sync` job，只在 `schedule` 或带 `sync=true` 的
  `workflow_dispatch` 运行；`sync` job 获 `contents: write`，其他 job 保持只读。checkout 保持
  `persist-credentials: false`；仅在 sync 步骤以受限 `GH_TOKEN` 执行 `gh auth setup-git` 和
  来源读取/推送，不使用 PAT 或自定义 secret。`build` 在 sync 成功且 `changed=true` 或 sync
  被跳过时运行，checkout `needs.sync.outputs.commit_sha || github.sha`；`deploy` 使用 build 的
  目标 SHA 做 freshness 检查。无变化不 build/deploy。
- **Rationale**: 满足 DEC-008 的“同次运行显式部署”，不依赖 bot push 触发第二条 workflow；
  写入权限只落在 sync job，token 不进入仓库配置或公开产物。
- **Alternatives considered**:
  - 独立 sync workflow + push 触发发布：违反显式衔接，且 bot push 不保证触发另一 workflow。
  - `persist-credentials: true`：token 持久在 runner 的 git 配置，扩大暴露面。
  - 使用 PAT/自定义 secret：无必要，增加轮换和泄露风险。
  - sync job 也只读、由人工提交：不满足自动更新闭环。
- **Evidence**: US-003 `contracts/workflow.md` 第 2/8 节、TechnicalSolution DEC-008、
  Context7 查询 `/websites/github_en_actions`（schedule/UTC、workflow_dispatch、permissions）与
  `/actions/checkout`（persist-credentials）。

## 6. 调度时间与时区

- **Decision**: 使用 UTC cron `17 19 * * *`，对应每日 03:17 Asia/Shanghai；在 README 和 workflow
  注释写明时区换算。增加手动 `workflow_dispatch`，与计划运行共用同一 sync 代码路径；不承诺平台
  准点 SLA，延迟/跳过可在运行记录中识别并手动重跑。
- **Rationale**: 官方 Actions 调度默认 UTC；固定 UTC 表达式避免不同 runner/平台的时区解释差异。
  Q-004 已确认 03:17 Asia/Shanghai，未要求按用户本地时间变化。
- **Alternatives considered**:
  - 使用 runner 本地时区或本地 cron：不可移植，且生产调度不可观察。
  - 为了“准点”做多次空提交：违反 FR-008，且可能掩盖真实无变化。
- **Evidence**: DemandAnalysis Q-004、AC-009/011、TechnicalSolution 8、Context7 GitHub Actions
  `schedule` 文档（默认 UTC，POSIX cron，最短 5 分钟）。

## 7. 状态、报告与恢复

- **Decision**: sync 运行输出封闭字段报告和脱敏 Step Summary：逐来源检查/更新结果、来源修订、
  内容摘要、许可状态、错误码、批次提交 SHA；现有 build/deploy 摘要继续显示内容/部署状态，
  使用 build 的目标 SHA 和 commit status。无变化检查记录真实时间但不写 Git；公开页面不显示
  内部日志。部署失败/过期仍按 US-003 语义处理；恢复使用受控 revert/restore。
- **Rationale**: 复用已验收的发布状态模型，补充来源级可观察性；不新增数据库、公开运行日志或
  旧版本入口。
- **Alternatives considered**:
  - 新建站内状态后台：超出范围，且需要新的认证/存储。
  - 把逐项状态写入 catalog：会因无变化检查产生无意义提交，且公开数据可能泄露内部错误。
  - 只依赖 workflow 结论：无法区分单来源失败与无变化。
- **Evidence**: TechnicalSolution 3.6、4、5；US-003 `contracts/publish.md`、US-005 status。

## 8. 测试与 POC-003

- **Decision**: 默认测试使用注入来源读取器、临时 Git 仓库和临时裸远端；覆盖分支/Release/pinned、
  完整树/二进制、删除文件、noop、conflict、许可、失败隔离、批次提交、报告脱敏和工作流结构。
  POC-003 在受控公开 GitHub 仓库验证真实固定 SHA、Release/pinned、删除文件、限流/错误和许可；
  不在默认测试中访问网络或写真实远端。
- **Rationale**: 与宪章 IX 和 US-003/005 的测试策略一致；真实来源边界由单独授权的 POC-003 证明，
  不把注入夹具当作网络集成通过。
- **Alternatives considered**:
  - 所有测试访问真实 GitHub：慢、易受限流/网络影响，且难以覆盖错误矩阵。
  - 只做 mock、不做 POC-003：不能证明真实 API/许可/树行为。
- **Evidence**: US-003/US-005 validation、TechnicalSolution POC-003、AiProgrammingGuide US-006。

## 9. 未决事项

- 生产调度启用、environment 审批和真实仓库设置仍需单独授权；本计划只覆盖实现与受控验证。
- 若实施发现 `source_tracking` 无法承载许可追溯，必须先记录 schema 变更影响并更新规格/数据模型，
  不在实现中静默扩字段。
