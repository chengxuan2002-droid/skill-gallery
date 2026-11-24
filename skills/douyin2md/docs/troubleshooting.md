# 故障排查与环境相关记录

> 本文收录的是**实测踩坑**，与具体机器/网络环境有关；`SKILL.md` 只保留通用规则。
> 排查前先跑 `bash bin/douyin2md doctor`，确认 Python、ffmpeg、可选模块、cookie 与模型状态。

## 通用故障表

| 报错 / 现象 | 原因 | 处理 |
| --- | --- | --- |
| `Fresh cookies (not necessarily logged in) are needed` | cookie 缺失或过期；现多由 `aweme/detail` 签名风控触发 | 新版 `url` 会自动切浏览器拦截兜底，无需手工处理；确需刷新 cookie 用 `bash bin/douyin2md cookie` |
| `Blocked by ArgusSecurityPlugin` | 裸 HTTP 请求被风控 | 必须用浏览器 cookie，不要自己写 requests 请求 detail 接口 |
| `未安装 sherpa-onnx` | 缺本地中文引擎 | `pip install -e '.[local]'` |
| `模型 'xxx' 尚未下载` | 模型未下载 | `bash bin/douyin2md model download` |
| sherpa 模型下载失败 | 网络不通 | `export HF_ENDPOINT=https://hf-mirror.com`，或改用云端引擎 |
| `invalid Netscape format cookies file` | cookie 格式错误 | 用 `cookie` 子命令生成，勿手写 |
| 拿到元数据但无音频 | 视频删除/私密/图文作品 | detail.json 含 `image_post_info` 即为图文作品，无音频轨，只能取 `desc` 文案 |
| 转写结果为空 | 纯音乐/无口播，或 VAD 不兼容 | 属正常结果，不要编造内容；确认有人声仍为空时移走 `~/.douyin2md/models/silero_vad.onnx` 走固定分段 |
| VAD 未生效 | `silero_vad.onnx` 与当前 sherpa 版本不匹配 | 自动退化为固定 20 秒切片，转写正常，仅时间戳粒度变粗 |
| 换 `paraformer-zh-int8` 后转写 0 字 | `model download` 顺带下的 VAD 与 paraformer 不兼容 | 把 `silero_vad.onnx` 改名成 `*.incompatible`，退化为固定分段 |
| 批量个别失败 | 单条被限流/视频删除 | 不中断整批，结束后对失败条单独重试 |
| cookie 有效但仍 403 / detail 空 | 已升级 msToken + `a_bogus` 签名校验 | `url` 已自动兜底；只需单独取 mp4 时用 `bash bin/douyin2md capture "<链接>" --fresh` |
| `Unsupported URL`（非抖音链接） | 链接来源未被识别，旧版会原样丢给 yt-dlp | 新版按来源分流：视频号走元数据降级，未知来源返回 `unsupported_source` 并提示本地文件改用 `transcribe` |
| 短链报 generic/TLS 错误、诊断显示「未知错误」 | `v.douyin.com` 短链未解析就交给 yt-dlp，跳转目标 `www.iesdouyin.com` 在部分网络下 TLS 不可达 | 新版 `resolve_short_url()` 先解析成 `www.douyin.com/video/<id>` 长链；解析失败自动回退原始链接，不改变既有行为 |
| `Fresh cookies (not necessarily logged in) are needed` | 抖音 `aweme/detail` 的 Argus / `a_bogus` 签名风控，**不必然要求登录** | 实测 3 份 cookie + Chrome cookie + 新鲜游客 cookie 直连均不通过；新版 `url` 自动切浏览器拦截兜底并照常产出逐字稿，`--force-capture` 可跳过这次必然失败的直连 |
| 浏览器页面标题变成「验证码中间页」、`[risk] 未取得 aweme/detail` | 复用旧 Chrome profile + 大量登录 cookie 被风控标记 | 兜底默认用 `--fresh` 全新空 profile 游客态（实测稳定拿到 detail）；失败再自动用常规会话互补一次。手动 `capture` 加 `--fresh`；仍失败则等风控解除，不高并发重试、不破解验证码 |
| 兜底失败提示「浏览器拦截未启动」/ `need_login` | 缺 `playwright` 或本机 Google Chrome | 装 `pip install -e '.[browser]'` + Chrome；不需要时加 `--no-capture-fallback` 退回纯 yt-dlp 行为 |
| 单条抖音链接只有元数据、没有转写正文 | 旧版 `if audio and batch:` 使单条模式跳过转写阶段 | 已修复：单条与批量都进入 `dy_transcribe.py`；批量仍复用音频暂存目录，模型只加载一次 |
| 封面 OCR 结果把「大模型」识别成「大棋型」 | 艺术字/竖排文字的机器识别误差 | 结果已标「⚠️ 低置信度」并附「须人工核对」；**不得写入转写正文或当作视频内时间点** |
| 拿到元数据但没有任何视频流字段 | 微信视频号预览页的平台侧策略，不是抓取失败 | 见下节；不要补抖音 cookie、不要跑 `capture`、不要反复重试 |
| `ModuleNotFoundError: No module named 'playwright'` | 用错 Python 解释器 | 见下节 |

## 风控升级：从手动 capture 到自动兜底

抖音 detail 接口新增 msToken（由页面风控 JS 注入）与 `a_bogus` 签名校验。
静态 cookie 文件里没有 msToken，因此即使登录态有效，yt-dlp 也可能 403。
`dy_browser_capture.py` 的做法：

1. Playwright `channel="chrome"` 无头打开视频页，拦截 `aweme/v1/web/aweme/detail` 响应拿 JSON；
2. `ffmpeg -headers "Referer: https://www.douyin.com/"` 拉 `play_addr` 存 mp4；
3. 交给 `dy_transcribe.py` 转写。

产出 `<out>/<aweme_id>.detail.json`（desc / 作者 / create_time / duration / statistics）
与 `<out>/<name>.mp4`。元数据可直接取用。

**2026-11-20 起这一步已自动化**：`dy_fetch.py` 直连失败时调用 `capture_fallback()`，
把 detail 映射成与 yt-dlp 完全相同的 `meta.json`（`slim_from_detail()`），
`audio_path` 指向 mp4，下游转写与文稿生成零改动。默认参数下
`bash bin/douyin2md url "<分享文案>" -o ./notes` 一次跑通：
样本取得 23MB / 6:18 真实视频 → sherpa 2156 字 / 19 段 → 7355 字节带时间戳文稿，
`meta.json` 带 `capture_fallback: true`，状态 `ok`。

**会话策略（对照实测）**：复用 `~/.douyin2md/cap-profile` + 1028 条登录 cookie 时
页面标题变成「验证码中间页」、拿不到 detail；改用全新空 profile 的游客态
（`--fresh`）则稳定捕获 5 次 `aweme/detail` 与 `play_addr`。自动兜底默认先 fresh，
失败再用常规会话互补重试一次；显式传 `--cookies` 时优先尊重登录态。
`--no-download` 支持只取元数据不下载 mp4（`--no-audio` 透传）。
脚本遇验证码会打印 `[risk]` 诊断，**只换会话重试一次，不破解验证码、不伪造签名**。

## 微信视频号预览页：为什么拿不到视频流（2026-11-19 实测）

样本 `https://weixin.qq.com/sph/AiQ59Q9O3y`。**结论：平台侧策略，不是抓取失败。**
`url` 子命令会自动分流到 `scripts/wx_fetch.py`，产出 `metadata_only` 文稿（带缺失清单）与高清封面。

| 现象 | 原因 / 正确做法 |
| --- | --- |
| 短链 HEAD 返回 405 | 必须用 GET；301 到 `channels.weixin.qq.com/finder-preview/pages/sph?id=<id>` |
| 落地页只有约 2.7KB | SPA 空壳，内容由 `get_feed_info` 接口下发，抓静态 HTML 无用 |
| 微信 UA 下页面「空白」 | **HTTP 响应体与桌面 UA 完全相同**（实测均 2733 字节），差异在前端 `WeixinJSBridge` 渲染分支；统一用桌面 Chrome UA |
| 裸 HTTP 直接请求接口 | 返回 `{"errCode":-1,"errMsg":"permission verification failed"}`；接口带页面上下文校验，必须用真实浏览器渲染后**拦截响应**（方法以实际拦截为准，本次为 GET） |
| 接口不下发视频流 | `feedInfo` 仅 `picInfo/description/jumpInfo/*CountFmt/createtime/isHardAd/coverUrl`，无 `duration` 与任何流字段；页面渲染「可扫码前往微信观看此内容」 |
| 换入口仍无法播放 | `/finder-preview/pages/feed?eid=` → 「此内容暂时无法播放」；`/web/pages/feed?eid=` → 「当前微信版本较低…」，属客户端版本门槛，不是单纯 cookie 问题 |
| 换 exportId 重试无效 | `sceneInfo.dynamicExportId` 每次请求取值不同且有 `expiredTime`，是动态时效凭证，不可缓存复用 |
| 封面分辨率只有 540×720 | `coverUrl` 末尾 `wxampicformat=503&picformat=200` 是缩图参数，去掉后 1080×1440 |
| 互动数看起来对不上 | 页面图标顺序与接口字段命名有歧义（实测 `favCountFmt=253 / forwardCountFmt=1331 / likeCountFmt=223 / commentCountFmt=25`，页面依次显示 253/1331/223/25），按接口**原始字段名**映射，不做二次推断 |

### 封面 OCR 与会话验证（2026-11-20 补做）

- `--ocr` 对高清封面做本地识别，macOS 走系统 Vision、其它平台可选 `tesseract`，
  都不需要新增 Python 包。实测 1080×1440 封面识别到 3 行文字，其中「破解大棋型幻觉」
  被正确标为低置信度（正确应为「大模型」）——**机器结果必须人工核对，不得写入转写正文
  或当作视频内时间点**；后端缺失时 `cover_ocr.available=false`，文稿照常产出。
- `scripts/wx_session_check.py` 仅在用户提供 cookie + `--authorize` 时执行；未授权即
  退出（rc=2）、不联网。报告脱敏（不含 cookie 值、不记录动态 `dynamicExportId` 取值）。
  一次带非微信 cookie 的连通性验证显示：带会话前后 `feedInfo` 键集无变化、
  `new_stream_fields=[]`，页面扫码提示与客户端版本门槛不受影响；报告已明确标注
  **该次验证不能用于判定「登录态是否解锁播放」假设**，需要用户提供真实微信会话才能定论。
- 该工具只做字段差异比对，不下载视频、不构造播放地址、不绕过鉴权或客户端校验。

需要逐字稿时，只能由用户在微信客户端保存视频或录屏，提供本地文件后走
`transcribe` → `to-md`；传入非空转写后模板自动升级为完整文稿。
`capture` 只针对抖音 `aweme/detail` 的 msToken + `a_bogus`，对视频号不适用。
不绕过鉴权、客户端校验或 DRM。

## 环境相关踩坑（2026-09 本机实测）

- **短链解析**：解析 `v.douyin.com` 短链时某些代理会 MITM，需要临时绕过代理：
  `env -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy curl -sI <短链> | grep -i location`；
  而 `www.douyin.com` 主体需要走默认代理才有网，无头 Chrome 不要加 `--proxy-server=direct://`。
  2026-11-19 实测：`www.iesdouyin.com` 在本机 TLS 握手失败，短链原样交给 yt-dlp 会落到
  generic 提取器报 TLS 错误。现由 `dy_fetch.py::resolve_short_url()` 先还原为
  `www.douyin.com/video/<id>` 再下载，失败自动回退；若随后报
  `Fresh cookies (not necessarily logged in) are needed`，说明已进入 Argus / `a_bogus`
  风控，改用 `capture` 兜底（该路径实测可取到真实 mp4 与 `aweme/detail`）。
- **解释器不一致**：`dy_browser_capture.py` 需要 playwright，`dy_transcribe.py` 需要
  sherpa-onnx，历史上两者可能不在同一个解释器里。脚本会自动探测并打印
  `[env] 自动切换到 …`；全自动找不到时手动
  `pip3 install playwright && playwright install chrome`。
  现在推荐用 `python3 -m venv .venv && pip install -e '.[all]'` 建一个统一环境，
  再用 `bash bin/douyin2md` 调用，避免解释器漂移。
- **长视频**：10 分钟以上 mp4 有 60–120MB，转写只要十几秒，用后台任务跑即可。
- **Windows**：Playwright profile 路径与 macOS 的 Chrome Default 不同，
  `dy_cookie_merge_msToken.py` 的默认 Chrome cookie 路径需要按平台调整。

## 内容质量

- **专名核实三级校验**：换模型交叉校验 → `ffmpeg` 抽帧读画面字幕定案 → 查项目官网/仓库。
  两个 ASR 模型一致也可能都错（实测 sense-voice 与 paraformer 都把 Fable 5 听成别的词）。
- 抽帧位置：片头 00:00–00:03、结构切换处、结尾 30 秒内念产品名处；一次 5–8 帧。
- 转写失败或为空时如实说明，**绝不编造视频内容**。
- 视频描述 `desc` 是作者写的文案，转写正文来自语音，两者都要保留。
- 交付固定为两个文件：`-逐字稿.md`（含附录 A 专名校正对照表、附录 B 可靠性说明）与
  `-总结.md`（视频主题 + 核心方法，要点式，逐条带时间节点）。只交一份视为未完成。
- 总结不写文章：不写导语/结语，不逐段复述；一条要点只讲一件事。
- 专名拼写以权威来源为准，**同时**写进附录 A 的原识别/校正/出现位置，不要只在正文里改掉；
  未命中的校正保留并解释，不删除。
- 原文有缺陷（重复段落、未闭合符号、错拼）时正文保留原样，问题写进附录 B
  「需解释 / 澄清 / 特别说明」，不改写正文。

### 两个文件的常见失败

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 总结是 `summary_status: pending` | 只跑了流水线，没写标注 JSON | 按 SKILL.md「输出形态」写 `summary` 后用 `to-md --annotations` 重渲染 |
| 要点末尾是「未标注章节/时间节点 ⚠️」 | `points[].at` 缺失或写错格式 | 补 `at`（`mm:ss` / `hh:mm:ss`），`09:99` 这类非法值会被判为无效 |
| 附录 A 出现「未命中」 | `original` 与转写文本不一致（同音异写、已被其他条目覆盖） | 核对逐字稿原文后改 `original`，或确认该处无需校正 |
| 日志提示时间节点超出视频时长 | 时间戳抄错或视频时长字段异常 | 复核对应位置的 `[mm:ss]` |
| 只出现一个 md 文件 | 无转写正文（`metadata_only` 或转写为空） | 属预期：不生成总结；补转写后用 `to-md` 重跑 |
| 批量传 `--annotations` 被拒绝 | 标注是单条内容 | 批量先出骨架，再逐条 `to-md --annotations` |

### 系列内容的跨期对比

用户常要求「说明本期相比之前提取的其他期有什么区别和进阶点」。这类需求技能本身管不了，
必须由 agent 自行接续：

1. 先读项目记忆（最近的日志优先）与同目录已有历史文档，确认此前提取过哪些期、
   各自产出文件在哪；
2. 用**表格**做多期横向对比，维度建议：对象工具 / 核心命题 / 视角 / 抽象层次 /
   驱动方式 / 证据强度 / 关键新概念 / 横向对比；再补一段「一贯未变的主张」；
3. 文末用一张演进脉络图（期号 + 日期 + 主线）串起来，并互相链接已有文档。

**对比依据只能来自已提取的内容**，没有提取过的期次不要凭印象写。

## 技能加载陷阱

- **UTF-8 BOM**：`SKILL.md` 一旦带 BOM（`ef bb bf`），部分框架会**静默忽略**整个技能，
  现象是"装好了却不触发"。`install.sh` 的自检已包含 BOM 检查；手工拷贝后可用
  `head -c 3 SKILL.md | od -An -tx1` 确认前 3 字节是 `2d 2d 2d`（`---`）。
- **frontmatter 必需字段**：`name` 与 `description` 缺一不可，且必须是 YAML 键值；
  `description` 要写清触发场景，否则框架无法判断何时调用。
- **技能目录名**应与 frontmatter 的 `name` 一致，便于各框架索引。
