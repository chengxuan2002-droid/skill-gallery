# 故障排查与环境相关记录

> 本文收录的是**实测踩坑**，与具体机器/网络环境有关；`SKILL.md` 只保留通用规则。
> 排查前先跑 `bash bin/douyin2md doctor`，确认 Python、ffmpeg、可选模块、cookie 与模型状态。

## 通用故障表

| 报错 / 现象 | 原因 | 处理 |
| --- | --- | --- |
| `Fresh cookies (not necessarily logged in) are needed` | cookie 缺失或过期 | `bash bin/douyin2md cookie`，或 `--cookies-from-browser chrome` |
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
| cookie 有效但仍 403 / detail 空 | 已升级 msToken + `a_bogus` 签名校验 | 改用 `bash bin/douyin2md capture "<链接>"` |
| `ModuleNotFoundError: No module named 'playwright'` | 用错 Python 解释器 | 见下节 |

## 风控升级：为什么需要 capture

抖音 detail 接口新增 msToken（由页面风控 JS 注入）与 `a_bogus` 签名校验。
静态 cookie 文件里没有 msToken，因此即使登录态有效，yt-dlp 也可能 403。
`dy_browser_capture.py` 的做法：

1. 读 `~/.douyin2md/cookies_merged.txt`（由 `dy_cookie_merge_msToken.py` 生成）；
2. Playwright `channel="chrome"` 无头打开视频页，拦截 `aweme/v1/web/aweme/detail` 响应拿 JSON；
3. `ffmpeg -headers "Referer: https://www.douyin.com/"` 拉 `play_addr` 存 mp4；
4. 交给 `dy_transcribe.py` 转写。

产出 `<out>/<aweme_id>.detail.json`（desc / 作者 / create_time / duration / statistics）
与 `<out>/<name>.mp4`。元数据可直接取用，不必绕 `dy_tomd.py` 模板。

## 环境相关踩坑（2026-09 本机实测）

- **短链解析**：解析 `v.douyin.com` 短链时某些代理会 MITM，需要临时绕过代理：
  `env -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy curl -sI <短链> | grep -i location`；
  而 `www.douyin.com` 主体需要走默认代理才有网，无头 Chrome 不要加 `--proxy-server=direct://`。
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
- 用户说「总结 / 核心内容」时要的是结构化总结文档，不是逐字稿；两者别混。
- 原文有缺陷（重复段落、未闭合符号、错拼）时正文保留原样，问题写在正文外的编者注；
  专有名词拼写以权威来源为准，并在编者注里说明原因。

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
