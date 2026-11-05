# US-002 最终差异复核（T026）

日期：2026-11-05。范围：T026；对照 T001 基线、当前 validation 记录和四份 0.2 规范。
本记录确认本地代码/文档状态，不表示已推送、合并 main 或发布。

## 基线与分支

- 复核基于 T025 提交 `6618667`；`origin/main` 为 `365d577`，当前分支
  `codex/us-002-search-detail-share` 无上游跟踪，领先 main 87 个提交。
- US-002 规格起点为 `dbc42aa`；以下差异以该提交到复核 HEAD 比较。
- 未创建 PR、未推送、未修改 Pages 或分支保护。

## 内容与 schema

| 检查 | 结果 |
|---|---|
| 六原件 SHA-256/大小 | 与 `migration-baseline.json` 全部一致，0 处不匹配 |
| `skills/`、`catalog/`、根 `assets/search-index.json` | 相对 `dbc42aa` 无差异 |
| `package.json` / `package-lock.json` | 无差异，未新增依赖 |
| `scripts/lib/build-inputs.js`、`build-outputs.js` | 各仅增加 `assets/app-search.js` 一行 |
| `index.html` | 仅增加 `assets/app-search.js` script 标签 |
| 索引/详情 schema | 仍为 `schemaVersion=1`；未新增 catalog 字段或迁移 |

US-002 变更范围（截至 T025）：`assets` 6 个文件、`tests` 13 个文件、`specs` 11 个文件、
根 README/AGENTS、`index.html` 和两个构建资产清单；无原件、catalog、根索引或依赖改动。

## 质量、性能与回归

- T021：`npm test` 163 项（162 通过、0 失败、1 跳过）；lint/format 通过；
  `security:secrets` 203 个文件无发现，`security:code` 31 个文件无发现，
  `security:deps` 通过 high/critical 阈值并报告 4 个 moderate。
- T022：1,000 项/10 MiB 隔离夹具、Chrome 152 headless、50 次固定查询，p95 39.9ms
  （候选线 200ms）；不是生产承诺。
- T023/T024：隔离四项构建 `status=built`、`cleanup_status=complete`；`dist/assets/app-search.js` 存在；
  四个旧链接和刷新可用；单文件/ZIP/附件下载摘要一致；复制/下载失败反馈未被误报为成功。
- 当前单版本：索引/详情/列表均为 4 项唯一 slug，无旧版本入口。

## 安全与权限边界

- 未新增管理员后台、访客登录、站内写入或第三方写入接口；前端动作只读取公开产物、复制文本和下载文件。
- 既有页脚 `Source` 外链保持低权重 http(s) 外部链接，不是管理后台，也不构成授权。
- 未在变更、文档、日志或示例中发现凭证；SECRET 规则和扫描结果只报告位置/类型。
- 活动内容仍只以构建期清理后的 `body_html` 展示；原件下载和搜索文本分离未改变。

## 未完成与风险

- **T041 macOS 仍未运行**，复选框保持未勾选，不能宣称 macOS/跨平台通过。
- Firefox、WebKit 未运行；只验证了 Chrome 152（Chromium）和 Edge 156。
- 未验证生产 GitHub Pages MIME/缓存、直接资源安全、部署失败回滚或 Pages 配置。
- 上传 CLI、GitHub 后台维护、自动更新、生产发布和 Q-004 调度仍未实现。
- `assets/app-views.js` 为 398 行，超过项目 300 行约束；建议后续拆分。
- 依赖审计仍有 4 个 moderate；性能只代表隔离 Chromium headless 夹具。
- 临时 CDP 脚本和截图未提交；可重复的 Node 测试与 validation 记录已提交。

## 结论

US-002 的 T001–T026 已完成本地实现、验收和文档收口，保留了 US-001 的原件保真、复制/下载、
旧链接和当前单版本；T041 macOS、生产发布和后续维护故事仍未完成。本次不推送、不合并 main、不发布。
