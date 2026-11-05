# US-002 隔离构建与子路径预览（T023）

日期：2026-11-05。范围：T023；FR-004、FR-011；AC-005、AC-014 的本地部分。
本记录不表示生产 Pages 已发布或 MIME/缓存已验证。

## 环境与隔离

- Windows 11；Node 22.21.0（声明基线仍为 Node 26.3.0，本记录未冒充该版本）。
- 从工作区复制 `package.json`、`package-lock.json`、`assets`、`catalog`、`skills`、`scripts`、`config`
  等源文件到系统临时目录；`node_modules` 使用只读 junction，未复制或安装依赖。
- 在工作区外执行 `npm run build` 和 `npm run preview`；未写工作区 `dist/`，未提交 `dist/`。
- 浏览器：Google Chrome 152.0.7977.83 headless。

## 构建

| 检查 | 实际结果 |
|---|---|
| `npm run build` | exit 0；`status=built`、`cleanup_status=complete` |
| `contentRevision` | `7c1224c71ddd2f3a9a14a0f3f38a3facecff74c6cab66140c42dbbd00e08aabc` |
| `dist/assets/app-search.js` | 存在 |
| 索引/详情/列表 | 4 个 slug、4 个详情、列表 4 张卡片 |
| 当前单版本 | 四个 slug 唯一，无旧版本目录或重复卡片 |
| 根 `assets/search-index.json` | 构建前后 SHA-256 均为 `2fca56cec4f61d3d77f72088821aad8ff2d220213ee71fd79eebe5145867dd2d` |

## 子路径与旧链接

- `npm run preview` 在 `http://127.0.0.1:8000/skill-gallery/` 启动。
- 列表加载的 8 个应用资源全部以 `/skill-gallery/` 开头；未请求根 `/assets`。
- 浏览器自动请求根 `/favicon.ico`，站点未配置 favicon；它不是应用资源，未作为子路径资源计入。
- 根 `/index.html` 返回 404，未把仓库根目录当作站点发布目录。
- 四个旧详情链接均成功打开并刷新：

| slug | 标题 |
|---|---|
| `superpower-systematic-debugging` | Systematic Debugging |
| `code-review-assistant` | Code Review Assistant |
| `refactoring-workflow` | Refactoring Workflow |
| `handoff-codex` | handoff-codex |

## 未运行与限制

- 未验证生产 GitHub Pages 的 MIME、缓存、直接资源响应头、部署失败或回滚。
- 未运行 Firefox、WebKit；未验证 T041 macOS。
- 未执行上传、自动更新、生产发布或 Q-004 调度。
- 本构建使用 Node 22.21.0 的隔离副本；不能据此声称已复验 Node 26.3.0 或远程 CI。
