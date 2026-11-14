# US-007 保真检查

**日期**: 2026-11-14
**范围**: T006 生产公开原件和 ZIP 与本地收录原件的逐字节核对；T016 复核原件、附件、二进制夹具、
许可、相对路径和 ZIP 清单。

## 1. 生产索引

- URL：`https://chengxuan2002-droid.github.io/skill-gallery/`
- revision：`faa0f345a85673f60fda1d4cb3b61594b242ae631ab89b264387eec6875c429a`
- Skill 数量：4

## 2. 单文件

| slug | raw 字节 | 与本地原件 | 详情 SHA-256 |
|---|---|---|---|
| `code-review-assistant` | 1044 | 一致 | `756a8c91...` |
| `refactoring-workflow` | 1020 | 一致 | `9091ac22...` |
| `superpower-systematic-debugging` | 1222 | 一致 | `80fbf9b3...` |

## 3. 目录包

`handoff-codex`：

- ZIP：`downloads/handoff-codex.zip`
- 条目：3（`SKILL.md`、`agents/openai.yaml`、`scripts/create_handoff.sh`）
- 每个条目与 `skills/handoff-codex/` 本地原件字节一致
- ZIP SHA-256 与详情 `download_sha256` 一致：`57a94d447205...`

## 4. 边界（T006）

- 本次只核对当前生产 4 项；未覆盖新增/替换后的 ZIP 回归，后者由 T004 的构建夹具和 US-001/US-003 validation 覆盖。
- 未执行浏览器下载交互；只做 HTTP 字节与 ZIP 条目核对。
- 不把搜索文本或详情 HTML 当作原件；详情 `raw_url`/`download_url` 指向保真文件。

## 5. T016 复核

**日期**: 2026-11-14。复核方式：重新读取生产索引/详情，下载 raw 和 ZIP，与本地 `skills/` 原件逐字节
比较；另运行构建夹具测试覆盖二进制、许可、空目录和 mode。未执行浏览器下载交互。

### 5.1 原件与附件

| slug | 详情 `contentRevision` | 本地/远端字节 | SHA-256 与详情 |
|---|---|---|---|
| `code-review-assistant` | `faa0f345...` | 1044 / 1044 | 一致 |
| `handoff-codex`（3 个文件） | `faa0f345...` | 220、1058、2583；逐文件一致 | 一致 |
| `refactoring-workflow` | `faa0f345...` | 1020 / 1020 | 一致 |
| `superpower-systematic-debugging` | `faa0f345...` | 1222 / 1222 | 一致 |

### 5.2 ZIP 清单与模式

`downloads/handoff-codex.zip`：

- 下载字节 3033，ZIP SHA-256 与详情 `download_sha256` 一致。
- 条目 3 个，均为相对路径且以 `handoff-codex/` 为根：
  `agents/openai.yaml`（220，0644）、`scripts/create_handoff.sh`（1058，0755）、`SKILL.md`（2583，0644）。
- 每个条目字节和 SHA-256 与本地原件、详情 `files` 一致；可执行位在 ZIP 外部属性中保留为 `0755`。
- 没有额外文件、绝对路径、`..` 段或旧附件残留。

### 5.3 许可、二进制与相对路径

- 当前生产 4 项的 catalog `license` 均为 `null`，详情 `files` 也没有 LICENSE 文件；本轮不宣称生产
  许可文件已覆盖。POC `source-poc` 的 MIT 许可基线见 `demo-002.md`，不属于生产。
- 当前生产 4 项没有二进制附件；`tests/integration/distribution.test.js` 的 4 项构建夹具测试覆盖
  单文件字节、目录 ZIP 的许可/二进制/空目录/mode、URL 边界和内容 revision，结果 4/4 通过。
- 详情中的文件路径均为相对路径，raw/download URL 位于 `/skill-gallery/` 前缀下；未发现绝对 URL 或
  越界路径。

### 5.4 未运行

- 未在生产重新执行新增/替换后的 ZIP 回归；未做浏览器下载交互。
- 未对 POC `assets/binary.bin` 做独立 URL 下载逐字节对比；`us6-poc.md` 只记录清单保留。
- 真实移动设备/读屏器/生产 MIME 缓存不在本文件范围。
