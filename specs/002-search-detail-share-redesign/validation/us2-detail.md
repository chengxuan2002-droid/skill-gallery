# US2 详情/分享验收（T016）

日期：2026-11-05。范围：问题 2、4 的列表复制/返回状态修复，T016 的详情、分享、原文复制和下载回归，
以及问题 2、3、4 的浏览器预检。映射 FR-003、FR-004、FR-010；AC-004、AC-005、AC-012、AC-013 的本地部分。
本记录不表示 T017～T026 或生产发布已通过。

## 环境

- Windows 11；Node 22.21.0（声明基线仍为 Node 26.3.0，本记录未冒充该版本）。
- Microsoft Edge 156.0.4314.58 headless；临时 Node CDP 脚本驱动，未新增 E2E 框架或产品依赖。
- 使用 `createDetailFixtureProject` + `buildFixturePreview` 生成隔离 dist；另把正式四项 catalog/原件
  复制到同一临时项目，用于四个旧详情链接，未写工作区 `dist/`，未执行收录 Skill 的脚本。
- 通过 `createPreviewServer` 以 `/skill-gallery/` 前缀读取；浏览器端口和临时目录在结束时清理；
  临时脚本未提交。

## 自动测试

| 检查 | 实际结果 |
|---|---|
| `node --test tests/unit/list-view.test.js tests/unit/app-routing.test.js` | exit 0；4/4 通过 |
| `npm test` | exit 0；157 项中 156 通过、0 失败、1 跳过 |
| `npm run lint` / `npm run format:check` | exit 0 |
| `npm run security:secrets` / `npm run security:code` | 通过，无发现；`security:deps` 未重跑 |

红灯证据：

- 列表视图测试在修复前找不到 `#list-manual-copy`，确认复制失败没有可复制值。
- 路由测试在修复前 `state.pendingDetailSlug` 为 `undefined`；直接打开详情后 `sessionStorage`
  仍保留 `#/?q=stale`，确认过期返回状态未被清除。

## 浏览器验收

### 四个旧详情链接

| slug | 首次打开标题 | 刷新后 |
|---|---|---|
| `superpower-systematic-debugging` | Systematic Debugging | 标题和 Hash 不变 |
| `code-review-assistant` | Code Review Assistant | 标题和 Hash 不变 |
| `refactoring-workflow` | Refactoring Workflow | 标题和 Hash 不变 |
| `handoff-codex` | handoff-codex | 标题和 Hash 不变 |

四个链接均保持 `#/skill/<slug>`；刷新后仍读取同一 Skill。

### 详情字段

- `complete-detail`：声明版本 `1.2.3`、作者、来源、更新时间、官方主页、开源地址、许可和创建时间均显示；
  站点说明、功能简介、适用场景与使用方法、备注、原文、附件、来源与许可分区存在；
  代码块和表格保留；`references/guide.md` 附件入口存在。
- `missing-detail`：内容标识为 digest 前 12 位 `7854c8394eb7`；作者、来源、更新时间、官方主页、
  开源地址、许可和创建时间均显示“未提供”，未编造版本或元数据。

### 分享、复制与状态

| 场景 | 实际结果 |
|---|---|
| 详情分享失败 | `copy_failed`；“复制失败，请手动复制下方链接”；手动值等于 `#/skill/complete-detail` 规范地址 |
| 详情分享成功 | `ready`；“分享链接已复制”；剪贴板收到同一地址；手动面板隐藏 |
| 列表分享失败 | `copy_failed`；“复制失败，请手动复制下方链接”；`#list-manual-copy` 可见 |
| 列表分享成功 | `ready`；“列表链接已复制”；剪贴板收到 `#/?q=sample` 地址；手动面板隐藏 |
| 未知 slug | `not_found`；显示“未找到该 Skill”和重试入口；重试回到列表 |
| 原文复制 | `ready`；剪贴板文本与 raw 原件严格一致；本次完整详情原文 189 字符 |

### US-001 取用回归

| 场景 | 实际结果 |
|---|---|
| 目录包下载 | `complete-detail.zip`；SHA-256 和大小与 detail 的 `download_sha256`/`download_size` 一致 |
| 附件下载 | `guide.md`；SHA-256 和大小与清单一致 |
| 单文件原件下载 | `missing-detail.md`；SHA-256 和大小与 detail 的下载摘要一致 |

### 同 slug 更新

修改 `complete-detail` 源内容后重新构建：`contentRevision` 改变；重新打开旧
`#/skill/complete-detail` 链接仍为同一 slug/标题，正文出现 `Version Two`，没有旧版本入口。

### 条件与返回预检

- 条件 chip 显示 `查询：debug`、`精准模式`、`标签：sample`、`排序：名称`；依次单项清除后地址回到 `#/`。
- 从列表卡片进入详情后返回，恢复 `#/?q=sample`。
- 直接打开详情后返回，导航前写入的 `#/?q=stale` 已被清除，返回列表根。

## 未运行与限制

- 未运行 T017～T026 的响应式、多浏览器、键盘、对比度、性能、隔离四项构建和最终复核。
- 未验证生产 GitHub Pages MIME/缓存、T041 macOS 或发布状态。
- 浏览器下载为真实临时文件并计算 SHA-256；未执行下载内容。
- 剪贴板使用页面内模拟，未写入真实操作系统剪贴板。
- 临时 CDP 脚本未提交，长期可重复的回归由 `tests/unit/*.test.js` 和隔离构建任务承担。
