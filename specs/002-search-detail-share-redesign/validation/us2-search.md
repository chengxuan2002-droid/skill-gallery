# US1 检索与筛选本地验收

日期：2026-11-05。范围：T012；映射 FR-002、FR-004，NFR-002，AC-003、AC-005、AC-015。
本记录只覆盖检索核心、固定查询集、URL 状态和构建集成；真实浏览器交互、可访问性与性能由
T020/T022 承担，不把 Node/vm 结果冒充浏览器验收。

## 环境

- Windows 11；本地 Node 22.21.0、npm 10.9.4。声明基线仍为 Node 26.3.0，未在本记录中冒充该版本。
- 使用 `tests/support/search-fixture.js` 的隔离临时项目；未写正式 catalog、`skills/` 或 `dist/`。
- 不执行收录 Skill 的脚本/测试，不安装其依赖。

## 实际命令与结果

| 检查 | 实际结果 |
|---|---|
| `node --test tests/unit/search-core.test.js` | exit 0；8/8 通过 |
| `node --test tests/integration/search-assets.test.js` | exit 0；2/2 通过 |
| `npm test` | exit 0；148 项中 147 通过、0 失败、1 跳过 |
| `npm run lint` / `npm run format:check` | exit 0 |
| 固定查询集（`fixed-skills.json` 的 12 个用例） | 12/12 符合预期 slug 顺序 |
| `createSearchFixtureProject({count:8})` + `buildFixturePreview` | `status=built`；`assets/app-search.js` 存在；索引 8 项；`index.html` 引入搜索模块 |

构建夹具的 `contentRevision` 为 `f7f2a356f47f124e5da95f607564073d4a4587aefd641bd182ba5086d9464264`；
它只用于隔离夹具，不是生产内容修订。

## 已验证行为

- 精准模式：规范化连续片段、双引号短语、拼写错误不自动纠错。
- 模糊模式：英文轻微拼写容错、中文连续子串兜底。
- 筛选：标签/平台/来源/作者同维 OR、跨维 AND；缺失字段不匹配；筛选选项只来自实际值。
- 排序：相关度、更新时间倒序、同分/同日期 slug 稳定排序。
- URL：空 Hash 与 `#/` 等价；查询、模式、筛选、排序解析与构建；非法 mode/sort 回退；
  详情/列表分享地址保持 `/skill-gallery/` 前缀且不含凭证。
- 构建：新模块进入 dist 和 `contentRevision`；缺少模块时整批构建失败。

## 未运行与限制

- 未执行真实浏览器搜索输入、模式按钮、筛选 checkbox、排序 select 和复制按钮的交互；
  T020 将验证浏览器可访问性，T022 将验证 1,000 项/10 MiB 浏览器 p95。
- 未验证 Chromium/Firefox/WebKit 多浏览器矩阵；未验证生产 Pages MIME/缓存或发布。
- 本记录不改变 US-001 的复制、下载、旧链接、T041 macOS 缺口或生产发布状态。
