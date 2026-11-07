# Phase 0 Research: US-005 Agent 命令维护

**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本阶段只做技术判定与现状核实，不实现命令、不修改远程仓库、不发布。命令的输入、输出和退出码
沿用已确认的 FR-006、C-05、DEC-006；不新增 npm 依赖。具体 GitHub API/`gh` 字段在实施时按项目
规则用 Context7 或官方资料核实后再落代码。

## 1. 认证与权限

- **Decision**: 认证复用现有 Git 凭证助手与 `gh` 登录会话；CLI 不接受 token 参数、不读取或打印
  token、不把凭证写入仓库/日志/JSON；未授权或凭证失效通过 git/gh 的非零结果映射到退出码 `3`。
- **Rationale**: Q-001/DEC-006 已确认复用 GitHub 权限与既有授权；避免新增凭证入口和泄露面。
- **Alternatives considered**: 自建 token 文件/环境变量（增加泄露与轮换风险）；站内登录（违反 Q-001）。
- **Verified**: US-003 工作流已使用 `persist-credentials: false` 与 GitHub 权限；US-004 README 已说明
  管理员使用 GitHub 授权；本地 `gh` 已登录（keyring），不读取其值。

## 2. GitHub 来源读取

- **Decision**: `import` 只接受结构化定位（owner/repo/path + ref 策略/ref）；先解析到不可变提交 SHA，
  再用 GitHub Git Trees/Blobs 读取完整文件或子树；`truncated`、子模块、符号链接、越界路径和缺失
  文件一律失败关闭。使用 `gh api` 复用认证；不解析网页、不猜测最新版。
- **Rationale**: TechnicalSolution 3.5 要求同一不可变修订与官方 API；避免 HTML 抓取和版本猜测。
- **Alternatives considered**: 直接 `git clone` 上游（可能执行 hooks/包含历史与越界文件，边界更宽）；
  网页抓取（脆弱且不安全）；第三方下载库（新增依赖，无必要）。
- **Verified**: `gh api` 是现有受信任工具；Git Trees API 的 `truncated` 与 Blobs 字段在实施时以官方
  文档核实；US-006 将复用同一来源定位模型。

## 3. 隔离工作副本与发布

- **Decision**: 发布前 `git fetch` 远端默认分支，使用临时目录中的 detached worktree（基于远端基线）
  暂存目标 Skill 原件、`catalog/<slug>.json` 与跟踪字段；提交后以非 force 方式推送；完成后移除
  worktree。用户工作区不被 reset、clean 或 `git add .`。
- **Rationale**: worktree 共享对象库与凭证助手，避免完整 clone；隔离目录满足“不重置用户工作区”。
  远端基线比较与 fast-forward 检查阻止覆盖。
- **Alternatives considered**: 直接在当前工作区提交（污染用户改动，禁止）；完整临时 clone（更慢、
  仍需网络）；`git commit-tree` 手工构造（复杂、易错）。

## 4. noop、冲突与单版本

- **Decision**: 候选先经现有 schema/路径/文件准入校验并计算内容摘要；与现有 slug 内容一致且记录
  未变时返回 noop；同 slug 不同内容必须 `replace` 且 `--expected-revision` 等于远端基线，否则冲突
  退出 `4`。替换按新清单重建，旧附件不进入新提交；不保留公开旧版本。
- **Rationale**: FR-006 要求防覆盖；US-001/US-003 已有摘要与单版本语义，复用以避免第二套规则。
- **Alternatives considered**: 仅比较 `updated_at`/版本号（不能识别内容变化）；允许隐式覆盖（禁止）。

## 5. 状态查询与等待

- **Decision**: `status --run` 使用 `gh` 查询运行与 job 状态；`content_status` 由 build job 派生，
  `deploy_status` 由 deploy job/step 派生；当 build 成功且 deploy 步骤跳过时派生 `superseded`；
  `--wait` 以固定间隔轮询直到 published/failed/timeout，超时退出 `8` 并保留运行链接。
- **Rationale**: 现有维护工作流的 deploy 仅在目标过期时跳过，可由 job/step 结果稳定派生；不新增
  artifact 或状态服务。
- **Alternatives considered**: 新增机器可读状态 artifact（改变 US-003/工作流契约，超出本轮）；
  解析 Step Summary（API 不暴露，脆弱）；只看整体结论（无法区分构建/部署）。
- **Verified**: `maintain.yml` 的 deploy 步骤仅在 `freshness == current` 时执行；US-003 已定义
  `published/failed/superseded` 语义。实施时核实 `gh run view --json jobs` 字段。

## 6. 输出、退出码与脱敏

- **Decision**: stdout 只输出单行 JSON（`slug`、`content_revision`、`content_status`、
  `deploy_status`、`commit_sha`、`run_url`、`public_url`、`errors`）；诊断到 stderr 且只含稳定码与
  位置；退出码：`0` 成功/preview/noop/submitted/published，`2` 参数或校验失败，`3` 未授权，
  `4` 冲突，`5` 来源读取失败，`6` 构建失败，`7` 部署失败，`8` 等待超时。
- **Rationale**: C-05 与 TechnicalSolution 已定义；单行 JSON 便于 Agent 调用，不混入调试日志。
- **Alternatives considered**: 人类可读为主（难以稳定解析）；多行 JSON/表格（契约不清）。

## 7. 测试与验证策略

- **Decision**: 单元测试覆盖参数互斥、退出码、JSON 形状与脱敏、noop/冲突、状态派生；集成测试在
  临时裸仓库与本地来源夹具中执行 preview/publish/replace/import/status；来源读取与运行查询可注入，
  默认测试不访问网络、不推真实远端；受控 POC-002 只在单独授权后执行真实发布。
- **Rationale**: 宪章 IX 要求先建立能识别错误的验证；避免测试依赖 GitHub 可用性或写入真实仓库。
- **Alternatives considered**: 直接对生产仓库测试（不可接受）；只做单元测试（无法证明 Git/发布行为）。

## 8. 不新增依赖与边界

- **Decision**: 不新增 npm 包；Git/`gh` 作为文档化前置命令。README 说明未实现能力（自动更新、
  ZIP 解压、站内后台）为规划；示例使用 `YOUR_*_HERE`。
- **Rationale**: 复用现有工具链与授权；保持发布产物与内容 schema 不变。
- **Alternatives considered**: 引入 GitHub SDK/CLI 封装（增加供应链与维护成本，无必要）。
