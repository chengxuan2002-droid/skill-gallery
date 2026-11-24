# 结构与流水线

## 分层

```
agent 框架（只读 SKILL.md）
        │  自然语言触发
        ▼
bin/douyin2md  ──►  douyin2md/cli.py  ──►  douyin2md/config.py
  自定位技能根         子命令 + 配置注入        默认值/JSON/环境变量
        │                    │
        │                    └──► douyin2md/sources.py
        │                           来源判定 / 状态契约（纯逻辑、不联网）
        ▼  subprocess（sys.executable + 绝对路径）
scripts/*.py   原始实现（可单独调用）
               + wx_fetch.py（来源适配）/ wx_ocr.py（封面 OCR）
               + wx_session_check.py（授权后的会话字段验证）
               + dy_fetch.py::capture_fallback()（抖音直连失败自动兜底）
```

- **接口层**（`douyin2md/`）：只做参数归并、配置读取、环境体检与来源判定，不含网络业务
  逻辑、不安装依赖；`doctor` 仍为只读。
- **实现层**（`scripts/`）：原有脚本继续可单独调用，命令行参数与抖音产物格式保持兼容。
  本版对 `dy.py` / `dy_fetch.py` / `dy_tomd.py` / `dy_browser_capture.py` 做了增量修改，
  并新增 `wx_fetch.py` / `wx_ocr.py` / `wx_session_check.py`；历史笔记里的
  `python3 scripts/dy.py ...` 依然有效。
- **文档层**（`docs/`）：框架接入、配置、排障与架构；环境相关的踩坑与本机路径都放这里，
  不污染 `SKILL.md`。

## 来源适配（`url` / `batch` 入口）

`douyin2md/sources.py::detect_source()` 是**唯一判定源**（纯标准库、不联网、可离线单测）。
cli 层先给出来源提示，`dy.py::fetch_one()` 按结果分流：

| 来源 | 适配器 | 产物 | 结果状态 |
| --- | --- | --- | --- |
| 抖音 | `dy_fetch.py`（直连失败自动 `capture_fallback`）→ `dy_transcribe.py` → `dy_tomd.py` | 逐字稿 + 总结两个文件 | `ok` / `failed` |
| 微信视频号 | `wx_fetch.py` → `dy_tomd.py` | 元数据 + 高清封面，`metadata_only` 文稿 | `metadata_only` / `media_blocked_by_platform` |
| 未知来源 | 不调用任何抓取脚本 | 可解释的错误提示 | `unsupported_source` / `need_login` |

`wx_fetch.py` 只做只读提取：按短链规则还原落地页 → 桌面 UA 浏览器渲染 →
拦截 `get_feed_info` 响应 → 压缩成统一 `meta.json` 契约（`source` / `source_id` /
`extraction_status` / `playability` / `missing` / `evidence`）→ 下载去缩图参数的高清封面。
**不尝试下载视频流**：平台在预览端不下发播放地址，裸 HTTP 请求还会被
`permission verification failed` 拒绝。

批量模式按条记录状态，降级条目无音频、不参与转写，但仍生成 Markdown；
结束由 `_print_status_summary()` 输出分级清单，单条失败不中断整批。

## 三段式流水线（抖音，`url` / `batch`）

```
dy.py
 ├─ 1. dy_fetch.py        链接/分享文案 → 元数据 JSON + 音频（yt-dlp + cookie）
 │      ├─ resolve_short_url()   v.douyin.com 短链 → www.douyin.com/video/<id> 长链
 │      └─ 1a. 失败自动兜底     capture_fallback() → dy_browser_capture.py（--fresh 游客会话）
 │              aweme/detail → slim_from_detail() → 与 yt-dlp 完全相同的 meta.json 契约
 │              （audio_path 指向 mp4；带 capture_fallback: true）
 ├─ 2. dy_transcribe.py   音频/mp4 → 带 segments 时间戳的转写 JSON
 │        ├─ sherpa       本地离线（默认，模型在 ~/.douyin2md/models/）
 │        └─ siliconflow / openai 兼容接口（需 API Key）
 └─ 3. dy_tomd.py         元数据 + 转写 → 两个交付文件
         ├─ <前缀>-逐字稿.md   frontmatter + 元信息表 + [mm:ss] 正文 + 附录 A/B
         └─ <前缀>-总结.md     视频主题 / 核心方法（要点式，逐条带时间节点）
```

**两文件渲染是纯排版**：`dy_tomd.py` 不做语义归纳，总结内容来自 agent 写的标注 JSON
（`--annotations`），脚本负责校验每条要点是否带章节/时间节点、把专名校正应用到正文并
自动计算出现位置、汇总可靠性事实（转写覆盖、时间轴空白、校正命中率、要点统计）。
`--single-file` 保留旧的单篇合并产物，用于兼容历史调用与管道。

**兜底不改变下游契约**：`slim_from_detail()` 输出的字段集与 `slim()` 完全一致，
`dy.py` 的转写/清理/文稿生成逻辑零改动；`--single-file` 下的文稿与 `main` 分支逐字一致。
开关 `--no-capture-fallback`（禁用）/ `--force-capture`（跳过直连），
`--no-audio` 时兜底透传 `--no-download` 只取元数据。

**单条与批量都进入转写阶段**（2026-11-20 修复：旧版 `if audio and batch:` 使单条链接
跳过转写，只产出元数据文稿）。批量模式（>1 个链接）先把音频集中到
`<输出目录>/.artifacts/audio_batch/`，再一次性调用 `dy_transcribe.py <目录>`，
**本地模型只加载一次**；单条模式直接对取回的音频调用 `dy_transcribe.py`，不复制暂存。
单条失败不中断整批，结束时给出成功/失败清单。中间产物在 `.artifacts/`，
除非 `--keep-audio` 否则自动清理。

本地文件模式（`transcribe`）跳过抖音获取链路，**不需要 cookie**：
`dy_transcribe.py` 递归扫描目录里的 `mp3/wav/m4a/flac/mp4/mov/mkv…`，
每文件输出一个 `<文件名>.json`。

## 风控兜底路径（自动 + 手动 `capture`）

抖音 web 端对 `aweme/v1/web/aweme/detail` 有 Argus 风控，后来又加了
msToken + `a_bogus` 签名校验，yt-dlp 直连稳定报 `Fresh cookies ... are needed`。
`dy_browser_capture.py` 不自己实现签名，而是用真实浏览器加载页面并**拦截 detail 响应**
取元数据，再用 `ffmpeg -headers "Referer: https://www.douyin.com/"` 直接拉
`play_addr` 存 mp4，最后交给 `dy_transcribe.py`。

- **自动**：`dy_fetch.py::capture_fallback()` 在直连失败（含拿不到 info.json）时调用它，
  最多两种会话各试一次，产物解析成统一 `meta.json` 后由 `dy.py` 照常完成转写与文稿。
- **手动**：`bash bin/douyin2md capture "<链接>" -o ./.artifacts --fresh` 只取 mp4。
- **会话策略**：`--fresh` 使用全新空 profile + 游客态。2026-11-20 对照实测，复用旧
  profile + 1028 条登录 cookie 会命中「验证码中间页」，全新游客会话稳定取得 detail；
  自动兜底默认先 fresh，失败用常规会话互补，显式 `--cookies` 时优先尊重登录态。
  遇验证码只换会话重试一次，不破解验证码、不伪造签名。

详见 `docs/troubleshooting.md`。

## 数据边界

| 位置 | 内容 | 是否进仓库 |
| --- | --- | --- |
| `~/.douyin2md/` | cookie、浏览器 profile、ASR 模型 | 否（`.gitignore`） |
| `<输出目录>/.artifacts/` | 中间音频、元数据、转写 JSON | 否 |
| `./notes/`（可配置） | 最终 Markdown 与视频号高清封面 | 否 |
| 仓库内 | 代码、文档、示例、测试、配置模板 | 是 |

## 设计约束

- 不改写第三方/原始脚本：兼容层只转发，参数与原 argparse 定义一一对应。
- 不含机器专属路径：`SKILL.md` 与 `bin/douyin2md` 都用自身位置解析。
- 配置单一来源：`douyin2md/config.py`，密钥只走环境变量。
- 体检只读：`doctor` 用 `importlib.util.find_spec` 和 `shutil.which` 检查，
  不 import 可选模块、不联网、不安装。
- 来源判定单一实现：`cli.py` 与 `scripts/` 共用 `douyin2md/sources.py`，脚本通过
  把仓库根插入 `sys.path` 导入，因此 `scripts/*.py` 仍可脱离入口单独调用。
- 降级是一等契约：`extraction_status=metadata_only` 由 `meta.json` 驱动，
  `dy_tomd.py` 自动输出缺失清单；没有转写正文时不生成总结（不得臆造），
  只产出元数据文稿。`--single-file` 下的旧抖音 meta 产物保持逐字兼容。
- 两文件契约：默认产物为 `<前缀>-逐字稿.md` 与 `<前缀>-总结.md`；总结的每条要点必须
  带章节或时间节点，缺位置会被渲染为「未标注」并计入附录 B，不静默放过。
- 校正留痕：专名校正由 `corrections` 标注驱动，正文改为校正后写法，附录 A 记录
  原识别结果与出现位置；未命中的条目保留并解释，不删除。
- 视频号适配器只读：不绕过鉴权、客户端校验或 DRM，不尝试构造播放地址。
- 封面 OCR 是**可选证据**：`--ocr` 默认关闭，后端失败自动降级；`cover_ocr` 只用于
  「封面文字（OCR，须人工核对）」区块，不进入转写正文、不生成时间戳。
- 会话验证需显式授权：`wx_session_check.py` 未加 `--authorize` 不发任何带会话请求，
  报告脱敏（不含 cookie 值、不记录动态凭证取值），且只比对字段差异。
- 抖音短链先归一化：`dy_fetch.py::resolve_short_url()` 解析失败时回退原链接，
  保证任何网络环境下不会比旧版更难用；精确诊断只改提示文案，不改下载参数。
- 兜底只做「同一契约的另一种取法」：不改写 `dy_transcribe.py` / `dy_tomd.py`，
  不因 `capture_fallback` 在文稿里新增区块；失败如实报平台限制，不高并发重试。
