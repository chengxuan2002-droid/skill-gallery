# US2 完整查阅、复制和下载验收

日期：2026-11-03。范围：US-001 内部 US2 切片（T025–T030）。映射 FR-004、FR-011，
NFR-001、NFR-003、NFR-006，DEC-002、DEC-005、DEC-009，AC-002、AC-005、AC-012，
US001-SC-02、US001-SC-03。本记录不表示上游 US-001 整体完成或已发布。

## 环境

- Windows 11；Node 22.21.0、npm 10.9.4；Microsoft Edge 156.0.4314.58 headless。
- 真实四项 `dist` 通过 `npm run build` 生成；目录包 `handoff-codex.zip` 与三项附件来自同一构建。
- 浏览器通过本地 `createPreviewServer` 的 `/skill-gallery/` 前缀读取；未访问生产站点。
- 剪贴板成功/拒绝由页面内 `navigator.clipboard.writeText` 模拟；下载由 Chromium
  `Browser.setDownloadBehavior` 写入临时目录后计算 SHA-256，未执行下载内容。
- 使用 Node CDP 临时脚本驱动浏览器；未新增 E2E 框架或产品依赖。
- 404、摘要不符和不支持 schema 使用隔离的 dist 副本：删除/篡改 raw 或 ZIP 字节，或把索引 schemaVersion 改为 2。

## 自动测试

| 命令 | 结果 |
|---|---|
| `node --test tests/integration/distribution.test.js` | exit 0；4/4 通过。单文件原名/raw/摘要；目录 ZIP 根、附件、许可、二进制、空目录、执行位；PublicFile URL 边界；前端模块参与 contentRevision |
| `node --test tests/integration/build-contract.test.js tests/integration/distribution.test.js tests/integration/preview.test.js tests/unit/build-render.test.js` | exit 0；17/17 通过 |
| `npm test` | exit 1；100 项中 97 通过、2 失败、1 跳过；两项失败为本机未安装 Gitleaks/Semgrep，非 US2 断言失败 |
| `npm run lint` / `npm run format:check` | exit 0 |

## 浏览器场景

| 场景 | 实际结果 |
|---|---|
| 四个旧 Hash 链接直接访问并刷新 | 四个标题均正确，刷新后仍为对应 Skill；`#/skill/<slug>` 未改变 |
| 查看完整原文 | `handoff-codex` raw 文本 1271 字符，与源文件严格 UTF-8 解码结果完全相等；状态 `ready` |
| 复制原文成功 | 模拟剪贴板收到完整 raw 文本，状态“原文已复制” |
| 复制原文被拒绝 | 状态 `copy_failed`，显示“复制失败，请手动选择下方原文”，保留可见原文区；无成功提示 |
| 复制分享链接成功 | 得到 `http://127.0.0.1:<port>/skill-gallery/#/skill/handoff-codex` |
| 复制分享链接被拒绝 | 状态 `copy_failed`，手动输入框可见且包含分享链接；无成功提示 |
| 下载目录 ZIP | `handoff-codex.zip`，3033 字节；SHA-256 与 detail 的 `download_sha256` 一致 |
| 下载附件 | `openai.yaml`，220 字节；SHA-256 与 detail 的 PublicFile 摘要一致 |
| raw 被阻断 | 状态 `raw_unavailable`，提示“原文不可用”，未用 `content_text` 兜底 |
| raw 404 / 摘要不符 | 分别状态 `raw_unavailable`，提示“资源不可用”/“资源摘要不一致”；未保存错误页或显示原文 |
| ZIP/附件被阻断 | 状态 `download_failed`，提示“下载失败，资源不可用”，未报告成功 |
| ZIP 摘要不符 | 状态 `download_failed`，提示“资源摘要不一致”，未发起下载 |
| 不支持 schemaVersion | 状态 `load_failed`，显示“无法加载图库，请重试”，不当作空库 |
| BOM/CRLF 原文 | 独立夹具复制后首字符 U+FEFF，包含 CRLF，内容与源字节严格相等 |
| 未知 slug | 状态 `not_found`，显示“未找到该 Skill”及重试 |
| 过期索引/详情混读 | 状态 `snapshot_mismatch`，显示“内容快照已更新，请刷新页面” |
| 快速切换详情 | 延迟第一个详情请求后切到第二个，最终标题为 Refactoring Workflow，未显示迟到内容 |
| 基本搜索回归 | 根列表 4 项；输入 `debug` 得到 2 项结果 |
| 中文/重复标题锚点 | 重复“快速开始”链接映射到 `#skill-heading-3`；点击后技能 Hash 不变，目标标题存在 |
| 未知本文锚点 | 链接无 href，文本显示“未知（未找到本文锚点）” |
| 表格/代码/相对附件 | 页面保留 table、code，附件链接映射到该 Skill 的 `.bin` URL |
| 同 slug 第二快照 | 旧 `#/skill/same` 链接仍打开同一身份；重建后正文从 Version One 变为 Version Two，contentRevision 改变 |
| 四旧链接资源前缀 | 列表、详情与下载 URL 均在 `/skill-gallery/` 下；未请求根路径 `/assets` |

## 未运行与限制

- 未验证生产 GitHub Pages 的 MIME/缓存/直接资源响应头；该部分属于 US-003。
- 未在 Firefox、WebKit、移动端或键盘/读屏下复验；未做 US-002 的完整检索、视觉和性能验收。
- 剪贴板使用页面内模拟，未写入真实操作系统剪贴板；下载为真实文件并计算摘要。
- Windows 不保留 POSIX 执行位；ZIP 模式按当前平台源状态验证，macOS/Linux 仍由 T041 复核。
- 未执行 US3 的非法批次、路径攻击、构建故障矩阵和不可信内容完整验收。

## 追溯

T025 自动测试、T026 浏览器场景、T027 原文/复制、T028 下载、T029 快照/分享/状态、
T030 本记录与真实下载摘要。上游 US-001 仍需 US3 与 Polish 收口，不能以本记录宣称完成。
