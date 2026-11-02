# YAML 元数据读取 PoC

日期：2026-11-03。任务 T005；映射 FR-001、NFR-001、DEC-003、AC-001、AC-002。
本记录验证已锁定 `yaml` 的读取边界，不表示 T008 生产校验器或业务验收已经完成。

## 环境与固定选项

- Windows 11；本机实际 Node 22.21.0；`yaml@2.9.1`（精确锁定）。
- 计划基线 Node 26.3.0 本轮不可用；本记录不能冒充该运行时的证据。
- 使用 `parseDocument(text, { schema: 'core', strict: true, uniqueKeys: true, maxAliasCount: 100 })`。
- 只在开头识别 `---`，以第一个独立 `---` 行结束；正文中的分隔线不开启第二段 YAML。

## 实际结果

命令：`node --test tests/unit/yaml-poc.test.js`

- exit 0；8/8 通过，无跳过。
- 标准字段、`>-` 折叠、嵌套及未知扩展字段可读取；原文 source 字符串未被 stringify 改写。
- BOM 与 CRLF 可读取；派生的正文文本按 `\n` 归一化，原始 Buffer 仍应由快照层单独保真。
- 重复键产生解析错误；数字键被识别为非字符串键。
- 非法 YAML 报错；未闭合 frontmatter 由边界逻辑判为不可用。
- 自定义 tag 产生 warning/error，不能被静默接受。
- 小规模别名可 `toJS()`；101 个别名在 `toJS()` 时抛出 alias 资源上限错误。`parseDocument` 本身不报该错误，生产实现必须在 `toJS()` 外加错误处理，不能只检查 `document.errors`。

## 对 T008 的约束

- 读取后只提取约定字段，不把整棵 YAML 对象传播到公开 JSON。
- 未知字段与原始字节仍由快照保真；不得 `stringify` 原件。
- BOM/CRLF 归一化只作用于派生文本，不能写回原件。
- `toJS()` 必须与 `maxAliasCount=100` 一起受控调用并捕获异常。
