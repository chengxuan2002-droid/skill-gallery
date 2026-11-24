---
name: douyin2md
description: 把抖音视频或本地音视频转成 Markdown 文稿。用户发抖音链接（v.douyin.com 短链、www.douyin.com/video/<id>、或含链接的分享文案）要求"转文字/提取文案/整理成笔记/存成 md/生成逐字稿/总结一下"时使用；一次发多个链接或整个列表/收藏夹要求"批量/全部转成 md"时也使用；发本地音视频文件或目录要求转录时同样适用。自动区分单条与批量，无需用户选择脚本。默认交付两个文件：带时间戳的逐字稿（末尾附语音识别专名校正对照表与可靠性说明）与要点式总结（视频主题 + 核心方法，逐条标注章节或时间节点）。支持元数据提取、语音转写（本地离线或云端）、YAML frontmatter。发微信视频号链接（weixin.qq.com/sph/...）时自动按来源降级为元数据+高清封面摘要，并明确标注缺失项。抖音直连被风控拦截时自动切换浏览器拦截兜底，仍产出完整逐字稿。
license: MIT
---

# douyin2md — 视频转 Markdown 文稿

这是一个标准 **Agent Skill**：只要某个 agent 框架支持 Agent Skills，
把本目录放进它的 skills 目录即可识别并调用，**无需修改任何文件**。
`SKILL.md` 位于仓库根，frontmatter 只使用标准字段；脚本引用全部是相对路径，
不含任何机器专属的绝对路径、解释器路径或本机目录。

## 调用约定

所有能力收敛到**一个入口**：`bin/douyin2md`。它用自身位置定位技能根目录，
因此从任意工作目录调用都有效。以下命令默认 cwd 为 `SKILL.md` 所在目录；
若不是，请先 `cd` 到技能目录，或写成绝对路径：

```bash
bash bin/douyin2md --help          # 查看全部子命令
python3 -m douyin2md --help        # 等价写法（需 PYTHONPATH 指向技能根）
douyin2md --help                   # pip install -e . 之后的等价命令
```

统一接口表：

| 子命令 | 作用 |
| --- | --- |
| `url <链接或文案>` | 单个链接 → **逐字稿 + 总结**两个 Markdown（自动按来源分流：抖音全链路含风控自动兜底 / 视频号元数据降级） |
| `batch <links.txt>` | 批量链接，每条一组「逐字稿 + 总结」，单条失败不中断，结束输出状态清单 |
| `transcribe <文件/目录>` | 本地音视频 → 转写 JSON（无需 cookie） |
| `to-md --meta <json>` | 元数据 + 转写 JSON → 两个 Markdown；`--annotations` 重新渲染专名校正与总结 |
| `capture <链接> [--fresh]` | 手动风控兜底：浏览器拦截 detail 响应并下载 mp4（`--fresh` 用全新游客会话） |
| `model <list\|status\|download\|path>` | 本地 ASR 模型管理 |
| `cookie [--check]` | 浏览器登录导出 cookie |
| `doctor` | 只读环境体检（不联网、不安装） |
| `config` | 打印生效配置（密钥只显示 set/not set） |

## 模式自动选择（先读这一段）

**不要问用户要单条还是批量，更不要让用户自己选脚本。** 按输入形态直接执行：

| 用户给的东西 | 执行 |
| --- | --- |
| 1 个抖音链接 / 1 段分享文案 | `bash bin/douyin2md url "<链接或文案>" -o ./notes` |
| 1 个微信视频号链接 | `bash bin/douyin2md url "<链接>" -o ./notes`（自动降级，见下节） |
| 多个链接 / 列表 / 收藏夹 / "全部" | 逐行写入临时文件，再 `bash bin/douyin2md batch urls.txt -o ./notes` |
| 1 个本地音视频文件 | `bash bin/douyin2md transcribe ./录音.mp4 -o 录音.json` |
| 本地一个目录 / 一批文件 | `bash bin/douyin2md transcribe ./访谈集/ -o ./访谈转录/`（模型只加载一次） |
| 抖音直连被风控（`Fresh cookies` / Argus） | **无需手动干预**：`url` 自动切浏览器拦截兜底；仅在要单独取 mp4 时才用 `capture "<链接>" -o ./.artifacts --fresh` |

判断不清时按「能直接跑的最小范围」执行，完成后补问是否需要处理更多。
批量输出自动带 `序号-作者-标题` 前缀（`01-作者-标题-逐字稿.md` / `-总结.md`），避免同名覆盖；
批量逐条串行，不要高并发以免限流。
`url` / `batch` 跑完只是**第一遍**：总结还是 pending 骨架，必须按「输出形态」一节的流程
补写标注 JSON 并重新渲染。

## 首次准备

```bash
bash bin/douyin2md doctor                 # 先看缺什么，纯只读
bash bin/douyin2md model download         # 下载本地中文模型（约 60MB，一次性）
bash bin/douyin2md cookie                 # 弹浏览器登录，导出 cookie（一次性）
bash bin/douyin2md cookie --check         # 校验 cookie 是否仍有效
```

依赖与配置统一由 `pyproject.toml` / `requirements.txt` / `config.example.json` 声明，
详见 `docs/configuration.md` 与各框架的 `docs/agent-compatibility.md`。

## 统一配置

优先级：命令行参数 > `DOUYIN2MD_*` 环境变量 > `DOUYIN2MD_CONFIG` 指定的 JSON >
`~/.douyin2md/config.json` > 仓库根 `config.json` > 内置默认值。

| 目的 | 环境变量 | 默认值 |
| --- | --- | --- |
| 运行时数据目录 | `DOUYIN2MD_HOME` | `~/.douyin2md` |
| 输出目录 | `DOUYIN2MD_OUTPUT_DIR` | `./notes` |
| 转写引擎 | `DOUYIN2MD_ENGINE` | `auto` |
| 语言 | `DOUYIN2MD_LANGUAGE` | `zh` |
| 模型 / 设备 / provider | `DOUYIN2MD_MODEL` / `DOUYIN2MD_DEVICE` / `DOUYIN2MD_PROVIDER` | 空 / `auto` / 空 |
| cookie 文件 | `DOUYIN2MD_COOKIES` | 空 |
| 云端 Key | `SILICONFLOW_API_KEY` / `OPENAI_API_KEY` | 不设置则走本地引擎 |

**密钥只走环境变量，不写配置文件、不写仓库、不打印值。**

## 引擎与模型

`--engine` 默认 `auto`：sherpa（本地中文）> siliconflow（云端）> openai（云端）。
`local` 是 `sherpa` 的兼容别名；faster-whisper 已移除，旧 whisper 档位自动映射到 sherpa。
`bash bin/douyin2md model list` 查看可选模型：`sense-voice-int8`（默认）/ `paraformer-zh-int8` /
`paraformer-zh` / `zipformer-zh-int8`。中文内容显式保持 `language=zh`。

## 输出形态：两个交付文件（默认且必须）

一次成功转写产出**两个** Markdown，前缀相同（批量带 `01-` 序号前缀），格式示例见
`examples/示例输出-逐字稿.md` 与 `examples/示例输出-总结.md`：

| 文件 | 必须包含 | 谁产出 |
| --- | --- | --- |
| `<前缀>-逐字稿.md` | frontmatter + 元信息表 + 视频文案 `desc` + 带 `[mm:ss]` 的转写正文 + **附录 A 语音识别专名校正对照表** + **附录 B 可靠性说明** | 脚本渲染 |
| `<前缀>-总结.md` | `## 视频主题` + `## 核心方法` 两部分要点，每条带章节或时间节点 | agent 写标注 JSON，脚本渲染 |

视频描述文案与口播转写是两种不同来源，都要保留，不要互相替代。

### 「总结」的写法（不写文章）

- 只写两部分，不写导语、过渡段、结语或推荐语：
  - **视频主题**：核心话题是什么、传达了哪些核心观点；
  - **核心方法**：视频中介绍或演示的关键技术、实现思路、论证方式。
- **一条要点一行**，句末用 `（[mm:ss]）` 标注时间节点；有明确章节时用
  `（[mm:ss] · 章节名）`。没有位置就无法回溯，视为不合格。
- 要点是压缩后的判断句（一般 ≤ 60 字），不复制整段原文、不做逐句转述；
  一条要点只讲一件事，不要把多个论点塞进一句。
- 只依据逐字稿与元数据。外部资料只允许用于确认**专名拼写**，且必须写进
  `corrections[].evidence` 或 `reliability.external_sources`，由附录 B 披露。
- 视频确实没讲方法时，`methods` 写一条说明（如「本视频为观点阐述，未介绍可复用方法」），
  不要硬凑步骤。

### 「逐字稿」的两份附录（缺一不可）

**附录 A 语音识别专名校正对照表**：三列——原识别结果 / 校正结果 / 出现位置（时间节点，
可选章节名）。要求：

- 每一条实际改写都必须在表里出现，正文呈现的是校正后的版本；
- 未命中的校正**不得删除**，出现位置写「未命中（原因）」，并在附录 B 逐条说明；
- 用外部资料定案的，单列「核对来源」。

**附录 B 可靠性说明**：三段——

- **客观依据**（脚本自动生成）：素材来源、转写引擎与语言、转写覆盖段数与时间轴、
  超过 20 秒的空白区间、专名校正生效/未命中条数、总结要点统计；
- **结论支撑**：`reliability.conclusions`，把关键结论对到时间节点；
- **需解释 / 澄清 / 特别说明**：`reliability.notes` + 自动检查结果（未命中校正、
  缺位置的要点、超出视频时长的时间节点、过长要点、总结未定稿）。

### 必做流程：写标注 JSON 再渲染

脚本只做排版，不做语义归纳。`url` / `batch` 先产出逐字稿和一份 `summary_status: pending`
的总结骨架，随后必须：

1. 读同目录逐字稿，按视频实际章节切分，写出标注 JSON（模板 `examples/标注示例.json`）；
2. 用 `--annotations` 重新渲染同一前缀的两个文件；
3. 复查：`summary_status: ok`、附录 A 无遗留「未命中」、每条要点都有时间节点。

```bash
bash bin/douyin2md to-md \
  --meta ./notes/.artifacts/<id>.meta.json \
  --transcript ./notes/.artifacts/transcripts/<id>.json \
  --annotations ./notes/.artifacts/<id>.annotations.json -o ./notes
```

标注 JSON 结构：

| 键 | 作用 |
| --- | --- |
| `corrections[]` | `original` / `corrected` / 可选 `evidence`；脚本改正文并自动记录出现位置 |
| `summary.one_line` | 可选，一句话概括 |
| `summary.topic[]` | `label`（核心话题/核心观点）、`text`、`at` |
| `summary.methods[]` | `name`、`at`、`points[]`（`text` + `at`） |
| `reliability.conclusions[]` | 结论 → 时间节点，写入附录 B「结论支撑」 |
| `reliability.notes[]` | `kind`（需解释/需澄清/特别说明）、`text`、`at` |
| `reliability.external_sources[]` | 逐字稿之外的核对来源 |

`--annotations` 只适用于单条：`dy.py` 在批量模式会直接拒绝，批量请逐条用
`to-md --annotations` 重新渲染。批量条目重渲染时必须带 `--filename "<序号>-<作者>-<标题>"`
（与首次产出的前缀一致），否则会丢掉序号前缀、生成重复文件。

### 需要旧行为时

`--single-file`（`url` / `batch` / `to-md`）保留旧的**单篇合并文稿**：不拆总结、不带附录，
产物与历史版本逐字一致；`--stdout` 自动按单文件渲染，方便管道。

### 哪些情况不产出两个文件

没取得视频流（视频号 `metadata_only`）或转写为空时，只产出元数据文稿，**不生成总结**——
没有逐字稿就没有可回溯的总结，不得臆造；日志会明确说明。

### 专名核实（必须做）

口播里的英文/品牌专名易错，三级校验依次是
① 换一档模型重跑交叉校验 → ② `ffmpeg` 抽帧读画面字幕定案 → ③ 查项目官网/仓库核对拼写。
两个模型一致也可能都错，不能据此下结论。抽帧看片头标题、结构切换处、结尾念产品名处。
**核实结论必须落进附录 A**（原识别 / 校正 / 出现位置），不要只在正文里悄悄改掉。

## 抖音直连风控：自动兜底（2026-11-20 实测）

抖音 `aweme/detail` 的 Argus / `a_bogus` 签名风控会让 yt-dlp 直连稳定报
`Fresh cookies (not necessarily logged in) are needed`；短链跳转目标
`www.iesdouyin.com` 在部分网络下还会 TLS 不可达。**`url` / `batch` 会自动处理，不要让用户自己选脚本**：

1. `dy_fetch.py` 先把 `v.douyin.com` 短链只读解析成 `www.douyin.com/video/<id>` 长链；
2. 直连仍失败时自动调用 `dy_browser_capture.py`，由真实浏览器渲染页面并拦截
   `aweme/detail` 响应，取得元数据与 mp4；
3. 把 detail 映射成与 yt-dlp **完全相同**的 `meta.json` 契约，照常进入
   `transcribe` → `to-md`，最终产出带时间戳的完整逐字稿。

兜底默认使用**全新空 Chrome profile 的游客态**（`--fresh`）。2026-11-20 对照实测：
复用旧 profile + 1028 条登录 cookie 会命中「验证码中间页」，而全新游客会话稳定拿到
`aweme/detail`；用户显式传 `--cookies` 时优先尊重其登录态，失败再回退 fresh。
兜底成功时日志会出现「已自动由浏览器拦截兜底取得真实媒体」，`meta.json` 带
`capture_fallback: true` 与 `extractor: browser-capture (aweme/detail)`，
**文稿格式与直连成功时逐字一致**，不新增任何区块。

| 开关 | 用途 |
| --- | --- |
| （默认） | 直连失败自动兜底；视频号与未知来源不受影响 |
| `--no-capture-fallback` | 禁用自动兜底，保留旧行为（只报诊断并失败） |
| `--force-capture` | 已知直连必失败时跳过 yt-dlp，直接用浏览器拦截，省一次请求 |
| `--no-audio` | 兜底时只取元数据（透传 `--no-download`，不下载 mp4） |

对应配置 `no_capture_fallback` / `force_capture` 与环境变量
`DOUYIN2MD_NO_CAPTURE_FALLBACK` / `DOUYIN2MD_FORCE_CAPTURE`。
单独取 mp4 用 `bash bin/douyin2md capture "<链接>" -o ./.artifacts --fresh`。

遇到验证码中间页时脚本会明确打印 `[risk]` 诊断并自动换会话重试一次，
**不破解验证码、不伪造签名、不绕过鉴权**；若两次都失败，如实报平台限制，不要反复高并发重试。

## 非抖音来源：微信视频号（只读降级）

**自动按来源分流，不要让用户选脚本，也不要把视频号链接当成抖音抓取失败去反复重试。**

| 来源 | 判定 | 行为 |
| --- | --- | --- |
| 抖音 | `v.douyin.com` / `www.douyin.com/video/<id>` | 原三段式流水线，产出逐字稿 |
| 微信视频号 | `weixin.qq.com/sph/<id>` / `channels.weixin.qq.com` | 只读提取元数据 + 高清封面，产出 `metadata_only` 文稿 |
| 其它链接 | 未知来源 | 返回 `unsupported_source` 并提示改用 `transcribe`，不丢给 yt-dlp |

平台在预览页**不下发视频流**（接口 `get_feed_info` 无 `videoUrl` / `h264` / 时长字段，页面提示「可扫码前往微信观看」）。这是平台侧策略，不是抓取失败；补 cookie、换 UA、重试都不会改变结果。因此：

- 文稿会自动带 `extraction_status: metadata_only`、frontmatter 的 `missing` 清单，以及正文顶部的「摘要说明（请先读）」区块；模板**不会编造**转写正文、字幕或视频内时间戳。
- 可用信息只有：官方描述 `desc`、作者、发布时间、互动数、高清封面画面文字。外部资料必须单列章节并标注「非视频内容」，不要冒充视频转写。
- 需要逐字稿时走 Tier 3：请用户在微信客户端保存视频或录屏 → 提供本地文件 →
  `bash bin/douyin2md transcribe <文件> -o t.json` →
  `bash bin/douyin2md to-md --meta <同一份 meta.json> --transcript t.json -o ./notes`。
  传入非空转写后自动升级为两个交付文件（逐字稿 + 待补全的总结骨架），不再显示降级说明。
- 批量混合来源时单条降级不中断，结束按 `ok / metadata_only / media_blocked_by_platform /
  need_login / unsupported_source` 输出状态清单。

**可选：封面文字 OCR（`--ocr`）**：默认关闭。`url` / `batch` 加 `--ocr` 后对高清封面做本地
OCR（macOS 用系统 Vision，其它平台可选 `tesseract`；`--ocr-backend auto|macos-vision|tesseract|none`），
结果写入 `meta.json` 的 `cover_ocr`，并在文稿里单列「封面文字（OCR，须人工核对）」。低于
`--ocr-min-confidence`（默认 0.8）的行标记「⚠️ 低置信度」。后端缺失/失败时自动降级为
`available=false`，不影响 `metadata_only` 文稿正常产出。**封面文字不是口播内容、字幕或时间戳**，
必须人工核对，不得据此推断视频内容。

**可选：带会话字段差异验证（`scripts/wx_session_check.py`）**：仅在用户显式提供登录态
（Netscape cookie 文件）并加 `--authorize` 时才会发出带会话请求；未授权时直接退出、不联网。
工具只比对带会话前后的接口字段差异并输出脱敏报告，**不下载视频、不构造播放地址、不绕过鉴权**。
2026-11-19 实测：带会话后仍未出现视频流字段；用非微信 cookie 完成的仅是链路连通性验证，
报告会明确标注「不能用于判定登录态假设」。

- 合规：不绕过鉴权、客户端校验或 DRM；仅用于自己创作或已获授权的内容。

## 注意事项

- **禁止臆造**：转写失败或为空时如实说明，绝不编造视频内容；视频号 `metadata_only` 文稿尤其不得编造时间戳。
- **两个文件一起交**：只给逐字稿或只给总结都算没做完；总结必须是 pending 之外的定稿，
  `summary_status: ok` 且每条要点都带时间节点。
- **总结不写文章**：不写导语/结语/推荐语，不逐段复述，不把逐字稿搬进总结；
  章节结构以视频本身为准，不要套用通用模板。
- **校正必须留痕**：正文改成校正后的写法，同时在附录 A 记录原识别结果与出现位置；
  未命中的条目保留并解释，不得悄悄删除。
- **封面 OCR 不等于转写**：OCR 文字须人工核对，只作画面文字证据，不得写入转写正文或当作视频内时间点。
- **视频号链接不要按抖音链路重试**：平台侧不下发视频流，按上节降级处理即可。
- 原文有缺陷时保留原样，问题写在附录 B「需解释 / 澄清 / 特别说明」里，不改写正文。
- 合规：仅用于自己创作或已获授权的内容，下载内容版权归原作者。
- 用户要求「与之前提取的几期对比 / 有什么进阶点」时，按
  `docs/troubleshooting.md` 的「系列内容的跨期对比」做表格与脉络图，只依据已提取内容。
- 深入阅读：`docs/agent-compatibility.md`（各框架接入与加载陷阱）、`docs/configuration.md`（依赖与配置）、
  `docs/architecture.md`（流水线）、`docs/troubleshooting.md`（风控、故障表、内容质量）。
