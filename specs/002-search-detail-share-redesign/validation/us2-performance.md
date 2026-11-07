# US-002 检索性能（T022）

日期：2026-11-05。范围：T022；NFR-002；AC-015。候选通过线为 p95 ≤ 200ms。
本记录是隔离夹具上的 Chromium headless 测量，不是生产网络或真实设备承诺。

## 环境与负载

- Windows 11；Node 22.21.0（声明基线仍为 Node 26.3.0，本记录未冒充该版本）。
- Google Chrome 152.0.7977.83 headless；设备指标 1440×900、deviceScaleFactor 1。
- `tests/support/search-fixture.js` 的 `createSearchFixtureProject`：1,000 项、总正文 10 MiB
  （10,485,760 字节）。
- 隔离临时项目构建 dist，`createPreviewServer` 以 `/skill-gallery/` 前缀读取；未写工作区 `dist/`，
  查询测量期间不使用网络请求。
- 浏览器报告 `hardwareConcurrency=20`、`deviceMemory=16` GB。

## 方法

- 数据加载并出现结果卡片后开始测量；先执行一次 `warmup` 查询并排除，再执行固定 50 条中英查询。
- 每条查询设置 `#skill-search` 输入值并派发 `input` 事件，从派发前记录 `performance.now()`，
  到下一帧 `requestAnimationFrame` 回调读取结果卡片/命中数；包含搜索、筛选、排序和 DOM 更新。
- p50/p95/max 直接由 50 个浏览器内耗时计算；p95 使用升序第 48 个值（`ceil(50×0.95)`）。
- 查询集（固定 50 条）：

```text
debug, debugging, review, code review, handoff, workflow, markdown,
document conversion, security, tests, maintainability, pull request, bug,
reproduce, problem solving, code quality, sample, long code, table,
chinese path, alpha, beta, productivity, format, verify, 调试, 文档, 转换,
交接, 进度, 代码, 审查, 安全, 测试, 维护, 表格, 代码块, 中文路径, 样例,
快速开始, 复现, 定位, 修复, 验证, 办公文档, 批量处理, 结构化, 备份, 备注,
最小标准
```

## 结果

| 指标 | 实际值 |
|---|---|
| 查询数量 | 50 |
| p50 | 35.4ms |
| p95 | 39.9ms |
| max | 41.1ms |
| 候选通过线 | 200ms |
| 判定 | PASS（Chromium headless 隔离夹具） |

最后一条查询 `最小标准` 在该负载中无匹配，结果区显示“0 个结果”；空结果更新也计入测量。
本结果不包含首次页面加载、网络传输、真实移动设备或生产缓存。

补充跨浏览器结果（同一夹具/查询集）：

| 浏览器 | p50 | p95 | max | 判定 |
|---|---|---|---|---|
| Firefox 157.0 | 41.0ms | 48.0ms | 52.0ms | PASS |
| WebKit 27.2 | 47.0ms | 50.0ms | 153.0ms | PASS |

详见 [us2-cross-browser.md](us2-cross-browser.md)。

## 未运行与限制

- Firefox/WebKit 的补充结果见 [us2-cross-browser.md](us2-cross-browser.md)；仍未验证真实移动设备。
- 未测量生产 Pages 首载、网络延迟、缓存头或真实 1,000 项内容来源。
- T022 的候选通过线沿用 NFR-002，不把本机结果写成生产性能承诺。
