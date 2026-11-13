# Quickstart: US-006 来源检查与自动替换验证

**Date**: 2026-11-12 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本指南只描述可执行的验证步骤；实现细节以
[source-sync 契约](contracts/source-sync.md)、[workflow 契约](contracts/workflow-sync.md) 和
[data-model](data-model.md) 为准。默认步骤使用隔离临时仓库与注入来源夹具；真实 GitHub 来源写入
仍需授权；生产调度已于 2026-11-13 启用，实际定时触发以运行记录为准。

## 1. 前置条件

- Node 26.3.0、npm 11.16.0（本地兼容测试可用 Node 22.21，但发布基线以 `.node-version` 为准）。
- 已安装 Git；真实来源验证需要已登录的 `gh`，不得在命令、文件或输出中放置 token。
- 使用临时副本，不直接修改用户工作区；默认不要运行 `npm run build` 写入工作区 `dist/`。
- 不执行 `skills/` 中任何脚本或测试，不安装收录 Skill 的依赖。

## 2. 隔离检查与无变化

1. 在临时项目复制一份合法 Skill 和 catalog 记录，给记录添加已启用的 GitHub
   `source_tracking`（使用注入来源或受控测试仓库）。
2. 执行检查：

   ```bash
   node scripts/sync-skills.js --slug example --json
   ```

   期望：退出码 `0`；stdout 单行 JSON；状态为 `unchanged` 或 `candidate`；工作区无写入、无提交、
   无推送；报告包含真实检查时间和来源修订。
3. 再执行一次相同检查。期望：相同结果、幂等，不新增提交。
4. 模拟来源返回 404/403/429/超时/目录截断。期望：该来源 `failed` 并带稳定错误码；其他来源继续
   检查；当前内容不变。

## 3. 单版本完整替换

1. 准备同一来源的两个受控修订：v2 新增一个文件并删除 v1 的一个附件。
2. 在隔离临时仓库执行：

   ```bash
   node scripts/sync-skills.js --slug example --apply --json
   ```

   期望：退出码 `0`；报告中该来源为 `updated`；只生成一个批次提交，包含目标原件和
   `catalog/example.json`；`git show --stat` 不含无关文件。
3. 核对当前内容树、`catalog/example.json`、索引/详情/下载：slug 不变、列表只有一项、旧附件消失、
   站内标签/备注/用法保留。
4. 重复执行；期望 `unchanged`，不新增提交。
5. 将上游声明版本保持不变但修改正文/附件；期望按内容摘要识别为 `updated`，不以版本字符串跳过。
6. 交换单文件与目录来源形态（受控夹具）；期望按完整新清单替换，旧路径不残留，既有 slug 和分享
   链接保持。

## 4. 许可、本地修改与冲突

1. 删除候选许可文件或修改许可内容；期望 `policy_blocked`，当前内容保留，报告只记录许可状态/
   路径，不自动替换。
2. 手工修改当前内容但不更新 `last_synced_digest`；期望 `conflict`，不覆盖本地修改，不 force push。
3. 在检查与提交之间推进远端基线或制造并发提交；期望 `conflict` 或 `superseded`，当前内容保留。
4. 注入截断树、子模块、符号链接、越界路径或非法元数据；期望 `failed`，诊断只含稳定码和位置。
5. 一个来源失败、另一个来源有合法更新；期望前者失败、后者仍可提交；全量构建失败时不得部署。

## 5. 状态、重跑与恢复

1. 查看运行报告/Step Summary：逐来源显示检查时间、修订、摘要、许可、结果和错误码；
   `content_status`/`deploy_status`/commit 状态分开。
2. 模拟部署失败：期望线上保留上次正常站点，状态为部署失败；按同一提交重跑不新增内容提交。
3. 模拟无变化检查：期望记录真实检查时间，但 Git 提交数为 0。
4. 使用受控 `git revert`/restore 恢复上一份有效内容，走同一构建/发布路径；期望 slug、旧链接和
   单版本保持，历史未被强制改写。

## 6. 调度与同次发布

1. 在受控仓库配置 schedule（UTC `17 19 * * *`，即每日 03:17 Asia/Shanghai）和
   `workflow_dispatch` 的 `sync`/`slug` 输入。
2. 手动触发：

   ```bash
   gh workflow run maintain.yml -f sync=true -f slug=example
   gh run watch
   ```

   期望：sync 与 build/deploy 在同一次运行中；build checkout 使用 sync 提交；deploy 使用 build
   的 target SHA；Step Summary 显示来源状态、提交状态、内容状态和部署状态。
3. 无变化运行：build/deploy 跳过，不创建空提交或空部署。
4. `sync=false` 手动重发：不检查来源，仅按当前提交重跑构建/部署。
5. 延迟/跳过/失败：以运行记录为准，手动重跑同一代码路径；不声称准点 SLA 或线上已更新。

## 7. 真实来源 POC-003（需授权）

在受控公开 GitHub 仓库准备：

- 分支、Release、pinned 三种来源；
- 两修订增删文件、二进制、许可文件；
- 非法/截断/链接/子模块夹具；
- 限流/404/403 夹具（可在读取器层注入）。

执行真实检查/替换后记录：来源修订、提交 SHA、运行 URL、逐来源状态、旧附件删除、站内字段保留、
许可证路径/摘要和未运行项。POC-003 不替代生产调度或生产发布验收。

## 8. 通过标准与未运行项

- 通过：上述场景的退出码、JSON/报告字段、提交/文件清单、失败保留和同次发布均符合契约；
  `npm test`、`npm run lint`、`npm run format:check`、`npm run security`、工作流静态检查通过。
- 未运行项必须单独列出：实际 03:17 定时触发、environment 审批、真实远端限流、生产 MIME/缓存、
  浏览器交互或 US-007 全链路验收。不得用本地夹具通过代替这些项。
