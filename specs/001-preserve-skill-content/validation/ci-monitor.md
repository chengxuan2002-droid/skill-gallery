# 提前建设检查 CI 与现站基础监测：验证记录

日期：2026-11-02。用户授权先补检查型 CI 与现有网站基础可用性监测，沿用初始化的逐步提交要求。
映射 FR-011、NFR-003/004/006、DEC-001/008/009、AC-014 的工程/可用性支撑子集。
该增量不实现 US-001 业务、生产构建部署、浏览器异常采集或来源更新 Q-004。

## 交付

- `.github/workflows/quality.yml`：main push、PR、手动触发，固定 Node 26.3.0、npm 11.16.0、uv 0.12.3。
  安装根锁与固定扫描器，执行已有 check/security；不使用特权 PR、不保留 checkout 凭证、不共享缓存、不发布/写回/上传原始报告。
- `.github/workflows/site-monitor.yml`：默认分支定时/手动读取现站，用户已确认改为每小时一次，cron 为 `7 * * * *`（UTC）。
  不需要 npm 安装、凭证或第三方监控 SDK；失败表现为 Actions 失败，邮件等仍取决于维护者自己的通知设置。
- `scripts/check-site.js` / `npm run monitor:site`：固定站点、四资源、8 秒请求超时、失败重试一次；HTTP/MIME/非空及首页/旧索引结构验证。
  不跟随重定向、不接受任意 URL 命令参数、不执行返回脚本；只输出路径、状态、类型码、HTTP 状态及尝试次数，不输出正文/原始异常。
- `tests/integration/site-monitor.test.js`：本地 HTTP 服务的 13 项新增行为测试；项目格式检查同时覆盖两份 workflow。

## 实际结果

| 检查 | 真实结果 |
|---|---|
| 初始 CLI 拒绝测试 | 入口未实现时 exit 1，未满足约定；实现后 exit 0 |
| 监测集成测试 | exit 0，13/13；包含正常、200 错误页、错误 MIME/JSON、空内容、重试、重定向、断连和响应体超时 |
| npm run check | exit 0；Lint/格式通过，24/24 测试通过，无真实网站依赖 |
| npm run security | exit 0；凭证/源码检查无发现，依赖无 high/critical，仍报告 6 个 moderate 受影响依赖 |
| npm run monitor:site | exit 0；首页、app.js、style.css、search-index.json 均 HTTP 200 且内容检查通过，各一次成功 |
| Actionlint 1.7.12 | 两份实际 workflow exit 0；unknown_context 违规副本 exit 1，未抑制规则 |
| 权限和 Action 固定审查 | 仅 contents: read；完整 40 位 SHA，checkout persist-credentials=false，无 secrets/特权触发/发布步骤 |
| 已提交快照隔离验证 | 本地 clone 后 npm ci、setup:security、check、security 均 exit 0；复用本地固定扫描器，不等于 Linux runner 首次安装验证 |

Actionlint 官方归档 SHA-256：`aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f`，
对应 1.7.12 darwin_arm64，校验后仅用于项目外静态验证；未安装全局工具或将其放入发布内容。
本机未安装 ShellCheck/Pyflakes，不能把 Actionlint 的语法/表达式验证称为这两项额外检查通过。

Action 固定版本由官方 release/tag 和 action.yml 核实：

| Action | 版本 | 完整 SHA |
|---|---|---|
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 |
| actions/setup-node | v7.1.0 | 949feb2413d6458794dcd2491c4babbbce0c15c1 |
| astral-sh/setup-uv | v10.3.3 | 68559e99cc807c1eb7e9238fd43a15bba460eec2 |

## 原件与范围保护

执行前记录工作区文件摘要/模式；完成前比对全部既有 Skill 和无关文件，要求零变化。
只修改当前工程方案/任务、package scripts、监测脚本/测试、workflow 和相关说明。
README 使用仅含本轮差异的索引版本提交，用户先前的介绍段落仍留在工作区；office2md 和其他既有未跟踪资产不收录、不执行、不提交。
没有新增产品依赖、迁移、格式化站点源码、改索引或更改部署地址。

## 远程状态与启用边界

公开接口核实仓库默认分支为 main，并存在 active 的 pages-build-deployment 工作流。
GitHub 连接器传输失败后使用公开只读接口；Pages 设置接口未能读取，因此不声称已核实其具体发布配置。
用户于 2026-11-02 明确授权推送及检查运行，并将监测周期改为每小时一次。
恢复 SSH 认证后，15 个本地提交已正常快进推送，main 更新至 `7667fb5`，没有 force push；此前未提交的用户资产保持原状。

实际远程验证（同一代码修订 7667fb5）：

- [Quality checks #1](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41395094243)：push 触发，completed/success。
  Ubuntu runner 的固定 Node/npm/uv、根安装、扫描器首次安装、check 和 security 各步骤均成功。
- [Site availability #1](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41395235887)：从 main 手动触发，completed/success；实际网站检查步骤成功。
- [既有 Pages 发布](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41395092606)：本次推送触发，build/deploy/report 均 success，站点地址不变。

GitHub 返回两个新 workflow 均 active；每小时第 7 分的 cron 已位于默认分支并启用。
首次手动执行证明 runner/网络/内容检查可用，不声称首次 schedule 事件已发生、严格准点或邮件已送达。
通知设置及 quality 合并必需项本次未调整，需要分别核对维护者设置。后续仅同步说明文件，不修改已验证的工作流/监测代码。

定时事件可能延迟/丢弃，公开仓库无活动 60 天可能自动停用；不通过空提交规避。
这不是浏览器 E2E、完整下载保真、发布一致性或独立严格可用性 SLA。新版首页/索引契约变更时同步调整监测断言。

依据：[固定 Action](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/find-and-customize-actions)、
[调度](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)、
[通知](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)、
[Actionlint](https://github.com/rhysd/actionlint/blob/main/docs/usage.md)。
