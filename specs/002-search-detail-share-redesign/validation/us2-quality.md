# US-002 全量质量门禁（T021）

日期：2026-11-05。范围：T021；NFR-003、NFR-006；AC-012、AC-014 的工程支撑。
本记录只覆盖本地检查，不表示生产发布、跨浏览器或依赖零漏洞。

## 环境

- Windows 11；Node 22.21.0（声明基线仍为 Node 26.3.0，本记录未冒充该版本）。
- 使用根 `package-lock.json` 与已安装 `.tools` 扫描器；未安装或执行任何收录 Skill 的依赖。
- 未格式化 `skills/` 原件，未修改 `catalog/` 或根 `assets/search-index.json`。

## 实际命令与结果

| 命令 | 退出码 | 实际结果 |
|---|---|---|
| `npm run lint` | 0 | 无 ESLint 错误 |
| `npm run format:check` | 0 | 所有受检文件符合 Prettier |
| `npm test` | 0 | 163 项中 162 通过、0 失败、1 跳过（legacy 基线红检查） |
| `npm run security` | 0 | secrets/code/deps 三项均通过 |

### 安全检查明细

| 检查 | 结果 |
|---|---|
| `security:secrets` | 203 个文件，无发现 |
| `security:code` | 31 个文件，无发现 |
| `security:deps` | 通过 high/critical 阻断；报告 4 个 moderate：`@eslint/config-array`、`@eslint/js`、`eslint`、`minimatch` |

依赖审计的 moderate 项仍存在，不能称为零漏洞；未新增产品依赖。

## 本次修复

T017～T020 引入的样式和可访问改造已由上述门禁覆盖。T020 发现并修复了 `.markdown-body` 全局
`overflow-wrap` 导致代码块不滚动的样式问题；修复只涉及 `assets/style.css`，未格式化原件或无关文件。

## 未运行与限制

- 未运行 Firefox、WebKit 或真实移动设备。
- 未验证生产 GitHub Pages 的 MIME/缓存、直接资源响应头或部署回滚。
- 未验证 T041 macOS、上传 CLI、自动更新、生产发布和 Q-004 调度。
- 本地 `npm test` 与 `.tools` 扫描器结果不替代远程 CI 或生产发布验收。
