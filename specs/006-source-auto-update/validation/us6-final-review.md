# US-006 最终复核

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T027；对照 spec、plan、data-model、contracts、quickstart、validation 与当前差异。

## 1. 已实现

| 范围 | 结果 | 证据 |
|---|---|---|
| 共享 GitHub 读取 | branch/release/pinned、固定 SHA、完整树、mode、限制、许可、错误码 | `scripts/lib/github-source.js`、[us6-check.md](us6-check.md) |
| 检查链路 | 零写入、unchanged/candidate、幂等、逐来源隔离 | `scripts/lib/source-sync.js`、[us6-check.md](us6-check.md) |
| 单版本替换 | 完整替换、旧附件删除、站内字段保留、单文件/目录互换 | `scripts/lib/source-sync.js`、[us6-apply.md](us6-apply.md) |
| 许可与冲突 | 许可路径/摘要基线、缺失/变化阻断、本地修改/基线前进 conflict、失败保留 | [us6-conflict.md](us6-conflict.md)、[us6-license.md](us6-license.md) |
| 报告与状态 | 封闭字段、提交/内容/部署分离、脱敏摘要 | `scripts/lib/source-sync-report.js`、[us6-status.md](us6-status.md) |
| 调度与同次发布 | schedule/dispatch、sync 唯一写 job、build/deploy target SHA | `.github/workflows/maintain.yml`、[us6-workflow.md](us6-workflow.md) |
| 运行说明 | 来源配置、检查/应用、许可/冲突、调度与恢复 | `README.md` |

## 2. 规格影响

- 实现单文件↔目录互换时必须更新 `content_path`；已在 [data-model.md](../data-model.md) 的
  `ContentRecord` 允许字段中记录，保持 slug 不变。该字段只在完整候选通过校验后更新。
- 单文件来源的许可从来源文件同目录或仓库根读取；目录来源只认来源子树。成功同步后
  `source_tracking.last_synced_license` 持久化许可路径与 sha256；旧记录无基线时目录来源回退当前内容
  许可，单文件在首次 apply 建立基线。该可选字段已更新 data-model、source-sync 契约与 README。
- 没有新增 npm 依赖、数据库、前端入口或第二条发布 workflow。

## 3. 未完成 / 未运行

- **T020 仅部分完成**：未在 POC 注入部署失败、未执行部署失败后的同提交重跑和受控 revert 恢复；
  只有无变化 dispatch 与 automatic build/deploy 成功证据。US-003 的旧站保留证据不能替代本故事
  自动提交后的同链路验证。
- 真实 403、限流等待、真实截断树、真实子模块/符号链接和真实二进制下载逐字节对比未运行。
- 生产 `main` 的每日调度、environment 审批、发布后 MIME/缓存未验证；POC 的 schedule 配置不等于
  生产启用。
- push 运行中 deploy 被跳过的原因未定位；不作为通过证据。
- 本机 Node 22.21.0 与锁定 26.3.0 不同，Node 26.3.0/Linux 以 CI 为准。

## 4. 结论

US-006 的来源检查、单版本替换、许可/冲突、报告和同次发布主链路已完成本地/受控验证；T020 的
部署失败重跑/恢复和真实 403/限流等边界仍保留为未完成项。不能把本次结果写成生产调度已启用或
US-007 整体验收通过。
