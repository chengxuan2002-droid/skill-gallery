# Phase 0 Research: US-003 校验、构建与原地址发布流水线

**Date**: 2026-11-07 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本阶段只做技术判定和现状核实，不实现流水线、不修改远程仓库设置、不发布。技术事实已按项目要求先查
Context7 GitHub Actions 资料，再用 GitHub 官方 action 发布记录与 README 核对版本和权限要求；查询不含凭证。
生产 Pages 配置、环境审批和线上切换仍需维护者单独授权。

## 1. 发布机制：Actions artifact + 显式 deploy job

- **Decision**: 使用自定义 GitHub Actions 工作流：构建 job 生成 `dist/`，经
  `actions/upload-pages-artifact` 上传名为 `github-pages` 的 artifact；部署 job 在
  `github-pages` environment 中调用 `actions/deploy-pages`，仅授予 `pages: write` 与 `id-token: write`。
- **Rationale**: DEC-008 要求校验、构建和部署在同一 workflow 显式衔接，线上一次切换一个 Pages
  artifact；该机制只发布构建产物，不发布整个仓库，符合白名单与失败保留要求。
- **Verified**: 官方 README 明确部署 job 至少需要 `pages: write` 和 `id-token: write`，建议使用
  `github-pages` environment；artifact 默认名为 `github-pages`；`upload-pages-artifact` 的 `path`
  指定静态目录，默认 retention 1 天。
- **Versions**: `actions/deploy-pages@v5.0.1`（`368f82528645a54fb793d4d04e342629a3f51346`）、
  `actions/upload-pages-artifact@v5.0.0`（`fc324d3547104276b827a68afc52ff2a11cc49c9`）。
  均为 GitHub 官方仓库最新 Release；按仓库现有规则使用完整 SHA 固定。
- **Alternatives considered**: 发布分支/gh-pages 目录（会把非白名单文件或历史带入公开产物，且失败保留弱）；
  第三方部署 action（增加供应链与权限风险，无必要）；只依赖 push 触发的另一条工作流（违反 DEC-008）。

## 2. Pages 源设置与受控验证

- **Decision**: 自定义工作流发布要求仓库 Pages 源为 “GitHub Actions”。该设置属于外部配置，本故事先写
  可审阅工作流与本地/受控仓库验证；POC-002 在受控测试仓库切换到 GitHub Actions 后验证显式部署。
- **Rationale**: 官方文档说明使用 source branch 时部署必须来自该源分支；当前站点仍由旧基线提供，
  直接改生产设置可能影响现站。把“配置切换”和“代码交付”分开，符合宪章 VI、IX 和发布授权边界。
- **Alternatives considered**: 直接从 `main` 按分支源发布（无法只发布 `dist/`，且与现有目录结构冲突）；
  在未授权时修改生产 Pages 设置（超出本故事授权）。

## 3. 同一运行显式衔接，不使用隐式 push 链

- **Decision**: 单一 `maintain.yml` 包含 `build` 与 `deploy` 两个 job；后续 US-006 在同一工作流增加
  `sync` job，提交后通过 `needs` 进入同一运行的构建与部署。
- **Rationale**: AC-014 明确要求自动提交后的发布不依赖另一次隐含 push；同一运行可追踪目标提交、
  构建产物和部署结果，失败可按同一 commit 重跑。
- **Alternatives considered**: `workflow_run` 链（跨运行状态和顺序更难保证）；让机器人 push 再触发
  另一条部署工作流（明确被 AC-014 排除）。

## 4. 产物验证：manifest 双向一致、白名单和凭证扫描

- **Decision**: 新增 `scripts/lib/publish.js`。部署前验证 `dist/manifest.json` 与实际文件集合双向一致
  （manifest 列出的文件必须存在且大小/hash 一致，实际文件也必须全部在 manifest 中），路径仅允许
  `index.html`、`.nojekyll`、`assets/`、`details/`、`downloads/`、`skills/`、`media/`；拒绝绝对路径、
  `..`、反斜杠、控制字符、符号链接、非普通文件、隐藏文件（`.nojekyll` 除外）和凭证类文件名；
  对文本类文件复用 `scripts/lib/secrets.js` 的 `scanSecrets`，诊断只报告路径与规则。
- **Rationale**: 现有 `verifyStage` 只检查 manifest 列出的文件存在与摘要，不检查“额外文件”；
  发布前需要独立验证白名单和越界。复用已有内容校验/凭证规则，避免第二套策略。
- **Alternatives considered**: 只信任构建结果（无法发现产物被替换或混入额外文件）；重新实现扫描器
  （冗余且容易与 SECRET-01～04 不一致）；对二进制全量做凭证扫描（误报高，且输入准入已覆盖原件）。

## 5. 并发、过期与重跑

- **Decision**: 工作流级 `concurrency` 使用 `maintain-${{ github.ref }}` 且 `cancel-in-progress: false`；
  部署 job 使用 `pages` 组且 `cancel-in-progress: false`。部署前用
  `git ls-remote https://github.com/${GITHUB_REPOSITORY}.git refs/heads/main` 取得远端 HEAD，
  与 `github.sha` 比较；不同则标记 `superseded` 并跳过部署。
- **Rationale**: 官方文档确认同一并发组只运行一个任务、`cancel-in-progress: false` 不取消进行中的部署；
  远端 HEAD 检查阻止旧快照覆盖新快照，满足 AC-011/NFR-004。
- **Alternatives considered**: `cancel-in-progress: true`（可能取消正在进行的更新/部署）；
  只靠 GitHub 排队（平台会取消较旧的 pending，仍需运行前检查）；无过期检查（旧运行晚到会回写）。

## 6. 触发范围与权限

- **Decision**: `push` 仅 `main`，加 `workflow_dispatch`；不监听 PR、fork 或 `pull_request_target`。
  checkout 使用 `persist-credentials: false`；默认 `contents: read`，部署 job 单独授予
  `pages: write`、`id-token: write`；不引入 PAT 或仓库 secret。
- **Rationale**: 访客可读、写入仅授权环境；PR/fork 不获得部署权限；默认 token 最小权限，符合 AC-008。
- **Alternatives considered**: 在 PR 中部署预览（增加权限面和环境配置，超出本轮）；使用 PAT（增加
  凭证轮换与泄露风险，无必要）。

## 7. 状态与报告

- **Decision**: `publish.js` 输出封闭字段的 JSON 状态（内容提交、构建、部署、目标 SHA、运行标识、
  失败码），工作流把脱敏后的结果写入 `$GITHUB_STEP_SUMMARY`；不新建外部日志服务、Issue 评论或
  额外状态数据库。GitHub 运行记录保存执行详情。
- **Rationale**: AC-011 只要求可区分状态和重跑入口；运行记录 + Step Summary 足够，且避免扩大权限。
- **Alternatives considered**: 上传额外状态 artifact（增加保留/读取复杂度，暂无必要）；
  Issue 评论（需要 issues:write，噪声大）。

## 8. 测试与验证策略

- **Decision**: 单元测试覆盖白名单、manifest 双向一致、路径/符号链接拒绝、凭证扫描、目标 SHA 判定
  与状态序列化；集成测试在临时项目构建 `dist` 后注入额外文件、篡改字节、增加凭证文件和过期的
  `contentRevision`，确认全部失败关闭；工作流测试静态断言触发、权限、环境、并发、固定 SHA、
  artifact 路径和无 `pull_request_target`。
- **Rationale**: 真实 Pages 部署需要外部授权；本地/受控验证可覆盖失败路径，且不依赖生产。
- **Alternatives considered**: 只做 YAML 语法检查（不足以证明权限/白名单）；直接在生产仓库试验
  （不可接受的副作用）。

## 9. 版本与依赖

- **Decision**: 不新增 npm 产品依赖。继续 Node 26.3.0、npm 11.16.0 与现有锁文件；测试解析工作流时
  使用已锁定 `yaml` 2.9.1。GitHub Actions 全部使用完整 SHA。
- **Rationale**: 复用现有工具链，避免供应链扩大；`yaml` 已在构建依赖中，不新增包。
- **Alternatives considered**: 引入 actionlint 或部署框架（增加开发依赖和配置，收益不足）。

## 10. 未决与授权边界

- 生产 Pages 源、environment 保护规则、分支保护和实际线上切换未在本阶段修改，也未验证。
- 受控测试仓库与 GitHub runner 是否可用未在本阶段确认；不可用时以本地测试、工作流静态断言和
  未运行记录交付，不能声称远程发布通过。
- 当前 `main` 仍是旧基线，US-002 分支未合并；发布工作流按运行时内容树构建，不把合并决策写入本故事。
