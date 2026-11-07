# US-001 取用回归（T024）

日期：2026-11-05。范围：T024；FR-004；AC-002、AC-005 回归。本记录不表示生产发布。
在 T023 等价的隔离四项构建上执行：同一源文件与构建方式，`contentRevision` 与 T023 一致。

## 环境

- Windows 11；Node 22.21.0（声明基线仍为 Node 26.3.0，本记录未冒充该版本）。
- Google Chrome 152.0.7977.83 headless；`npm run build` + `npm run preview` 在临时副本运行。
- 构建结果：`status=built`、`cleanup_status=complete`、`contentRevision` 与 T023 相同。
- 仅临时项目写 dist；未写工作区 `dist/`，未提交生成物。

## 回归结果

| 场景 | 实际结果 |
|---|---|
| 当前版本 | 索引 4 项、详情 4 项、列表 4 张卡片；slug 唯一 |
| 四个旧链接 | 四个 `#/skill/<slug>` 直接打开并刷新，标题与 Hash 保持 |
| 原文复制 | `code-review-assistant` 剪贴板文本与 raw 原件严格一致（1027 字符） |
| 单文件原件下载 | `code-review-assistant.md`；SHA-256/大小与 detail 一致 |
| 目录 ZIP 下载 | `handoff-codex.zip`；SHA-256/大小与 detail 一致 |
| 附件下载 | `openai.yaml`；SHA-256/大小与清单一致 |
| 复制失败 | 剪贴板拒绝时 `copy_failed`；手动值包含 `#/skill/handoff-codex`；未显示成功 |
| 下载失败 | 删除当前 ZIP 后点击下载，状态 `download_failed`、提示“资源不可用”；下载目录无文件 |

四个旧链接标题：

| slug | 标题 |
|---|---|
| `superpower-systematic-debugging` | Systematic Debugging |
| `code-review-assistant` | Code Review Assistant |
| `refactoring-workflow` | Refactoring Workflow |
| `handoff-codex` | handoff-codex |

## 未运行与限制

- 未验证生产 GitHub Pages MIME/缓存、部署失败、授权恢复或回滚。
- 未运行 Firefox、WebKit；未验证 T041 macOS。
- 未实现/未验证上传、GitHub 后台维护、自动更新、发布或 Q-004 调度。
- 本记录中的下载是隔离临时构建的真实文件，不是生产站点下载。
