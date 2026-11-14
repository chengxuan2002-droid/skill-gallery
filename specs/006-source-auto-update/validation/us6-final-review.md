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

- **T020 已完成受控验证**：部署失败/旧站保留、同提交重跑、受控 revert 恢复见
  [us6-status.md](us6-status.md)。同时修复了 sync 被跳过时 deploy 可能被隐式跳过的问题：
  deploy 现在使用 `if: always() && needs.build.result == 'success'`。
- 真实 403、限流等待、真实截断树、真实子模块/符号链接和真实二进制下载逐字节对比未运行。
- 生产 `main` 调度已于 2026-11-13 启用（PR #6）；push run 43421560371 与手动 sync run 43421951464
  已验证发布/无变化路径。2026-11-14 首次 03:17 窗口轮询至 05:10 CST 前未出现；08:19 CST 出现延迟 schedule run 43533439066（sync success，build/deploy skipped），
  下一窗口为 2026-11-15 03:17；environment 审批和发布后 MIME/缓存未验证。
- 本机 Node 22.21.0 与锁定 26.3.0 不同，Node 26.3.0/Linux 以 CI 为准。

## 4. 结论

US-006 的来源检查、单版本替换、许可/冲突、报告、调度与同次发布主链路已完成本地/受控验证；
T020 的部署失败重跑/恢复已完成；生产 `main` 调度已启用，2026-11-14 首次 03:17 窗口在 05:10 CST 前
未出现 schedule run，08:19 CST 出现延迟 run 43533439066（sync success，build/deploy skipped）。
真实 403/限流、实际定时触发的后续窗口和 US-007 整体验收仍未完成，不能把本次结果写成 US-007 已通过。
