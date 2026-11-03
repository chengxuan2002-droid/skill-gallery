# US1 迁移与本地查阅验收

日期：2026-11-03。环境：Windows 11、Node 22.21.0、npm 10.9.4；五项均在仓库外临时项目执行，
未写仓库 catalog、未改原件、未发布。映射 FR-001、FR-011、NFR-001、NFR-006，
DEC-002、DEC-003、DEC-009，AC-001、AC-002、AC-005，US001-SC-01、US001-SC-05。

## 隔离项目

复制 `scripts/`、四项六原件、标准单文件样例、office2md 哨兵、网页源文件、旧索引和依赖锁；
未复制仓库 catalog，未复制 office2md 实现。迁移前记录六原件、office2md 哨兵与标准样例 SHA-256。

## 迁移与构建

| 步骤 | 命令 | 实际结果 |
|---|---|---|
| dry-run | `node scripts/migrate-catalog.js --dry-run` | exit 0，`dry_run`，未创建 catalog |
| write | `node scripts/migrate-catalog.js --write` | exit 0，恰好四份记录，source_tracking 全 null |
| 第二次 write | 同命令 | exit 0，`noop`，catalog 摘要不变 |
| 站内修改 | 仅修改 superpower 记录的 `tags`/`notes` | 原件摘要全部不变 |
| build | `node scripts/build-index.js` | exit 0，`built`，`cleanup_status=complete` |
| 重复 build | 同命令 | exit 0，`content_revision` 相同，无伪日期 |

`content_revision`：`a61084e355cb0e08488a404f1626d01b6ff4c78c3129e9f6b4247a7c9898037f`。

## 核对结果

- 索引恰好四项：`code-review-assistant`、`handoff-codex`、`refactoring-workflow`、
  `superpower-systematic-debugging`；无 `standard-sample`/`office2md` 记录。
- 站内标签新增 `acceptance`、备注写入后，索引反映新值；六原件、office2md 哨兵、标准样例 SHA-256 不变。
- 每项 `details/<slug>.json` 的 `updated_at` 与 catalog/原件日期一致，未改成执行当天。
- 四项 `raw_url` 字节与原件逐字节一致；main file 的 sha256 与原件摘要一致。
- 重复 build 的 `contentRevision` 与详情日期不变；旧 dist 被完整替换，无 `.dist.*` 遗留。

## 本地查阅

用 T023 的预览服务器指向临时 dist，Edge headless 打开四个旧 Hash 链接：

~~~text
/skill-gallery/#/skill/superpower-systematic-debugging
/skill-gallery/#/skill/code-review-assistant
/skill-gallery/#/skill/refactoring-workflow
/skill-gallery/#/skill/handoff-codex
~~~

四项均渲染详情标题、`markdown-body` 和返回按钮，未出现未找到、加载失败或快照不一致；根列表渲染
4 张卡片和搜索框。

独立标准样例使用另一临时项目与独立 catalog 记录构建：索引 1 项，正文代码块保留，`raw_url` 与
样例原件字节一致；未写入正式四项 catalog。

## 回归与限制

- `node --test tests/integration/export-regression.test.js`：1 通过、1 按设计跳过；旧缺陷仍可复现。
- 未运行 US2 的复制/下载反馈、US3 的完整故障矩阵、生产 Pages MIME/缓存或发布；未推送、未发布。
- Edge headless 只证明脚本执行后 DOM 具备标题/正文/返回/列表/搜索，不替代人工键盘、剪贴板、
  窄屏或视觉验收；Windows 不保留 POSIX 执行位，跨平台 ZIP 模式仍由 T041 验收。
- 仓库 `catalog/` 与六原件保持 T017/T001 的状态；本记录不改变 site 线上内容。
