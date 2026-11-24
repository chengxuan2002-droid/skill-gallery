# 依赖与统一配置

## 依赖分层

| 层 | 用途 | 安装 |
| --- | --- | --- |
| `core` | 抖音链接解析、元数据与音频获取（`yt-dlp`） | `pip install -e .` |
| `local` | 本地离线中文 ASR（`sherpa-onnx`、`numpy`） | `pip install -e '.[local]'` |
| `browser` | 浏览器登录导出 cookie、抖音风控兜底、微信视频号预览页渲染、会话字段验证（`playwright`、`browser-cookie3`） | `pip install -e '.[browser]'` |
| 封面 OCR | 系统级后端（macOS Vision 用 `swift`；或 `brew install tesseract`），**无新增 pip 依赖** | 缺失时自动降级 |
| `all` | 以上全部 | `pip install -e '.[all]'` |
| `dev` | 单元测试（`pytest`） | `pip install -e '.[dev]'` |

系统级外部命令（pip 管不了）：

```bash
brew install ffmpeg        # macOS；Ubuntu/Debian: sudo apt install ffmpeg
python3 -m playwright install chromium   # 仅 browser 组需要
```

微信视频号适配器 `scripts/wx_fetch.py` 用 `channel="chrome"` 启动**本机 Google Chrome**，
因此除 Playwright 外还需安装 Chrome 浏览器本体；缺失时适配器返回
`need_login` 状态并给出提示，不会抛 traceback。

云端转写（siliconflow / openai 兼容接口）**不需要额外 Python 包**，只用标准库 `urllib`，
但需要设置 API Key 环境变量。

> 国内网络装依赖可加清华镜像：
> `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e '.[all]'`
> 模型下载走 Hugging Face，不可达时设 `export HF_ENDPOINT=https://hf-mirror.com`。
>
> 本仓库的安装/体检命令**不会自动安装依赖**：`doctor` 是纯只读体检，
> 依赖由使用者按上表显式安装。

## 配置优先级

```
命令行参数  >  DOUYIN2MD_* 环境变量  >  DOUYIN2MD_CONFIG 指定的 JSON
           >  ~/.douyin2md/config.json  >  仓库根 config.json  >  内置默认值
```

`--config <文件>` 可以出现在命令的任意位置。`config.example.json` 是模板，
复制成上述任一路径即可；未知字段会被忽略，不会污染子脚本参数。

```bash
cp config.example.json ~/.douyin2md/config.json
bash bin/douyin2md config                  # 打印生效配置，密钥只显示 set/not set
bash bin/douyin2md doctor --json           # 机器可读的环境体检
```

## 配置项全表

| JSON 键 | 环境变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `home` | `DOUYIN2MD_HOME` | `~/.douyin2md` | cookie、模型、浏览器 profile 的根目录 |
| `output_dir` | `DOUYIN2MD_OUTPUT_DIR` | `./notes` | Markdown 输出目录 |
| `engine` | `DOUYIN2MD_ENGINE` | `auto` | `auto` / `sherpa` / `siliconflow` / `openai` / `local` |
| `model` | `DOUYIN2MD_MODEL` | 空 | `bash bin/douyin2md model list` 查看 |
| `language` | `DOUYIN2MD_LANGUAGE` | `zh` | 中文内容保持 `zh` |
| `device` | `DOUYIN2MD_DEVICE` | `auto` | 兼容旧参数，sherpa 引擎不使用 |
| `provider` | `DOUYIN2MD_PROVIDER` | 空 | sherpa 执行提供方：`coreml` / `cpu` / `cuda` |
| `cookies` | `DOUYIN2MD_COOKIES` | 空 | Netscape 格式 cookie 文件路径 |
| `cookies_from_browser` | `DOUYIN2MD_COOKIES_FROM_BROWSER` | 空 | `chrome` / `safari` / `edge` |
| `api_base` | `DOUYIN2MD_API_BASE` | 空 | OpenAI 兼容接口地址 |
| `keep_audio` | `DOUYIN2MD_KEEP_AUDIO` | `false` | 保留中间音频 |
| `no_timestamps` | `DOUYIN2MD_NO_TIMESTAMPS` | `false` | 正文不带时间戳 |
| `no_frontmatter` | `DOUYIN2MD_NO_FRONTMATTER` | `false` | 不写 YAML frontmatter |
| `ocr` | `DOUYIN2MD_OCR` | `false` | 视频号高清封面做本地 OCR（仅 `url` / `batch` 有效） |
| `ocr_backend` | — | `auto` | `auto` / `macos-vision` / `tesseract` / `none` |
| `ocr_min_confidence` | — | `0.8` | 低于该置信度的 OCR 行标记「⚠️ 低置信度」 |
| `no_capture_fallback` | `DOUYIN2MD_NO_CAPTURE_FALLBACK` | `false` | 禁用抖音直连失败时的浏览器拦截自动兜底 |
| `force_capture` | `DOUYIN2MD_FORCE_CAPTURE` | `false` | 抖音跳过 yt-dlp，直接用浏览器拦截 |

布尔环境变量接受 `1/true/yes/on`（不区分大小写）；`ocr_backend` 与 `ocr_min_confidence`
也可通过命令行 `--ocr-backend` / `--ocr-min-confidence` 覆盖。`no_capture_fallback` /
`force_capture` 对应命令行 `--no-capture-fallback` / `--force-capture`，对缺少新键的
旧配置字典保持兼容（按默认关闭处理）。

**抖音自动兜底的运行条件**：`playwright` + 本机 Google Chrome（`channel="chrome"`），
与视频号适配器相同；`--fresh` 模式使用临时创建、用完即删的空 profile，不读写
`~/.douyin2md/cap-profile`。缺失 Chrome 时兜底失败并给出可解释错误，不会抛 traceback；
此时可用 `--no-capture-fallback` 退回纯 yt-dlp 行为。

封面 OCR 不引入新的 Python 依赖：macOS 走系统 Vision（临时编译 Swift 小工具，需 `swift`），
其它平台可选系统命令 `tesseract`（`brew install tesseract`）。两者都缺失时返回
`available=false`，文稿照常产出 `metadata_only` 版本，不会报错中断。
**OCR 文字须人工核对，不得当作口播内容、字幕或视频内时间戳。**

`scripts/wx_session_check.py` 与上述配置无关，是独立的可选验证工具：必须由用户提供
Netscape cookie 并显式加 `--authorize` 才会发出带会话请求，未授权时直接退出（rc=2）、
不联网；报告已脱敏，不写入任何 cookie 值，也不下载视频。

## 密钥

| 环境变量 | 用途 |
| --- | --- |
| `SILICONFLOW_API_KEY` | 硅基流动云端转写 |
| `OPENAI_API_KEY` | OpenAI 兼容接口转写 |

规则：

- 密钥**只**通过环境变量提供，不写 `config.json`、不写仓库、不传给 `config`/`doctor` 的输出。
- 这两个变量由 `scripts/dy_transcribe.py` 自行读取；统一入口不会把它们打印出来。
- `config` 子命令只显示 `set` / `not set`，不显示值。
- `.gitignore` 已排除 `config.json`、`cookies*.txt`、`*.cookies`、`notes/`、媒体与模型缓存。

## 典型配置示例

只走本地离线、保留中间音频：

```bash
export DOUYIN2MD_ENGINE=sherpa
export DOUYIN2MD_KEEP_AUDIO=1
bash bin/douyin2md url "https://v.douyin.com/xxxx/" -o ./notes
```

走云端、指定输出目录：

```bash
export SILICONFLOW_API_KEY="YOUR_KEY_HERE"
export DOUYIN2MD_OUTPUT_DIR=./output
bash bin/douyin2md batch urls.txt
```

项目级固定配置（提交给团队，不含密钥）：

```bash
bash bin/douyin2md --config ./team-config.json batch urls.txt
```
