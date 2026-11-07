# 渲染、清理与 ZIP PoC

日期：2026-11-03。任务 T006；映射 FR-004、NFR-001、NFR-003、DEC-002、DEC-005、AC-002、AC-012。
本记录验证已锁定依赖的最小能力，不表示 T018/T037 的生产实现或业务验收已经完成。

## 环境与依赖

- Windows 11；本机实际 Node 22.21.0；计划基线 Node 26.3.0 本轮不可用。
- `marked@18.1.2`（动态 import）、`sanitize-html@2.18.1`、`yazl@3.3.1`、`yauzl@3.4.0`（仅验证）。
- 未执行任何夹具脚本，未运行收录 Skill 的代码。

## 实际结果

命令：`node --test tests/unit/render-archive-poc.test.js`

- exit 0；4/4 通过，无跳过。
- Markdown 代码块、表格和中文可保留；`script`、`iframe`、`form`、`onerror`、`onclick` 与 `javascript:` 被清理。
- 真实外链保留为 `href`；行内代码与代码围栏中的伪链接只作为文本保留，不生成 `href`。
- 先移除原件 `id`/`name`，再按出现顺序生成 `skill-heading-N`；伪造的 `skill-heading-9` 不被采信，生成 ID 在第二次白名单清理后仍保留。
- 中文重复标题得到 `快速开始`、`快速开始-1`；`API Token` 得到 `api-token`；空标题得到 `section`。
- `yazl` 在 `outputStream` 完成并写入文件后可被 `yauzl` 读取；二进制字节、中文文本、空目录和 0644/0755 模式一致。
- ZIP 容器整体 hash 未作为跨环境条件；测试只比较解包路径、字节和模式。

## 未覆盖与后续

- PoC 的允许标签/属性是测试内最小白名单，T018/T037 仍需实现 C-04 的完整 URL 映射、附件引用校验、媒体签名和最终 ID 自检。
- SVG/HTML 等活动附件必须以 `.bin`/下载入口交付；本 PoC 未实现媒体副本。
- 执行位在 Windows 上由 ZIP 元数据模拟；T041 仍需在 macOS/Linux 复核实际文件和 rename 行为。
- 本记录不能替代浏览器交互、复制/下载反馈或生产 Pages MIME 验收。
