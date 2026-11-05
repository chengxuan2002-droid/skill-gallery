# US3 响应式、主题与键盘验收（T020）

日期：2026-11-05。范围：T017～T020；FR-010、NFR-005；AC-013 的本地部分。
本记录不表示 Firefox、WebKit、生产 Pages 或发布验收通过。

## 环境

- Windows 11；Node 22.21.0（声明基线仍为 Node 26.3.0，本记录未冒充该版本）。
- Chromium：Google Chrome 152.0.7977.83 headless，Node CDP 临时脚本驱动。
- 使用 `createDetailFixtureProject` + `buildFixturePreview` 生成隔离 dist；临时修改完整详情样例，
  加入长代码行、长链接和锚点，用于溢出与减少动效检查。
- 通过 `createPreviewServer` 以 `/skill-gallery/` 前缀读取；未写工作区 `dist/`。
- 临时脚本与截图未提交；截图在临时目录，操作记录如下。

## 自动测试

| 检查 | 实际结果 |
|---|---|
| `node --test tests/unit/app-theme.test.js tests/unit/app-routing.test.js tests/unit/list-view.test.js` | exit 0；10/10 通过 |
| `npm test` | exit 0；163 项中 162 通过、0 失败、1 跳过 |
| `npm run lint` / `npm run format:check` | exit 0 |

主题与焦点单测覆盖：已保存主题优先、无保存时跟随系统、手动切换持久化、无保存时响应系统变化、
列表标题/详情标题路由焦点。

## 浏览器验收

### 主题

| 场景 | 实际结果 |
|---|---|
| 系统浅色且无保存主题 | `data-theme=light`；页面背景 `rgb(255, 255, 255)` |
| 系统深色且无保存主题 | `data-theme=dark`；页面背景 `rgb(15, 15, 16)` |
| 手动切换 | 变为深色，`localStorage.skill-gallery-theme=dark`；刷新后保持深色 |
| 主题按钮 | `aria-label` 为“切换到浅色主题”/“切换到深色主题” |

### 视口与布局

| 宽度 | 页面横向溢出 | 筛选按钮 | 筛选面板 | 列表列数 | 卡片列数 |
|---|---|---|---|---|---|
| 360px | 无 | 显示 | 默认收起 | 1 | 1 |
| 768px | 无 | 显示 | 默认收起 | 1 | 1 |
| 1440px | 无 | 隐藏 | 始终显示 | 2 | 3 |

360/768px 点击筛选按钮后 `aria-expanded=true`，面板显示；再次点击收起。详情页在三种宽度均无页面外
横向溢出，代码块内部可横向滚动且 `overflow-x:auto`。

### 对比度

统计了列表和详情的主要文本/控件，正文对比全部不低于 4.5:1：

| 主题 | 最低值 | 最低元素 | 其他代表值 |
|---|---|---|---|
| 浅色 | 4.75:1 | `.badge` | `.skill-card-footer` 4.83；`.btn-primary` 6.7；正文 17.4 |
| 深色 | 6.7:1 | `.btn-primary` | `.app-subtitle` 6.78；`.detail-text` 15.64 |

### 减少动效

- `prefers-reduced-motion: reduce` 匹配成功。
- `.skill-card` 过渡时长为 `1e-05s`（CSS `0.01ms`）。
- 页面无自动播放视频、无 canvas/粒子背景。
- 点击详情锚点时 `scrollIntoView` 使用 `behavior=auto`，不使用平滑滚动。

### 键盘

- 360px：纯键盘可达主题按钮、搜索框和筛选按钮；筛选按钮获得清晰 2px 实线焦点，Enter 可展开/收起。
- 1440px：Tab 可达搜索框、模式按钮、筛选 checkbox、排序 select、复制列表链接和卡片；
  卡片 Enter 打开详情，焦点落到详情标题；Tab 可达查看原文、复制原文、下载 ZIP、复制分享链接；
  Shift+Tab 回到“返回列表”，Enter 返回后焦点落到列表标题。焦点环均为 2px 实线。

## T020 发现并修复

T017 的 `.markdown-body` 全局 `overflow-wrap:anywhere` 会让代码块中的长行换行，导致代码块不产生内部
横向滚动。T020 为 `.markdown-body pre` 和 `pre code` 固定 `white-space: pre`、`word-break: normal`、
`overflow-wrap: normal`；三种宽度复验后代码块可内部滚动，页面外无溢出。

## 未运行与限制

- **Firefox、WebKit 未安装/未运行**，不能声称跨三浏览器通过；本记录只有 Chromium 结果。
- 未验证真实操作系统读屏器、屏幕阅读器语音、真实移动设备或触摸手势。
- 未验证生产 GitHub Pages MIME/缓存、T041 macOS、上传/自动更新/发布。
- T017～T019 的样式/语义/主题已在本地完成；最终差异复核和全量回归仍属 T021～T026。
