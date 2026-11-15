# 依赖与统一配置

## 依赖分层

| 层 | 用途 | 安装 |
| --- | --- | --- |
| `core` | 抖音链接解析、元数据与音频获取（`yt-dlp`） | `pip install -e .` |
| `local` | 本地离线中文 ASR（`sherpa-onnx`、`numpy`） | `pip install -e '.[local]'` |
| `browser` | 浏览器登录导出 cookie、风控兜底（`playwright`、`browser-cookie3`） | `pip install -e '.[browser]'` |
| `all` | 以上全部 | `pip install -e '.[all]'` |
| `dev` | 单元测试（`pytest`） | `pip install -e '.[dev]'` |

系统级外部命令（pip 管不了）：

```bash
brew install ffmpeg        # macOS；Ubuntu/Debian: sudo apt install ffmpeg
python3 -m playwright install chromium   # 仅 browser 组需要
```

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

布尔环境变量接受 `1/true/yes/on`（不区分大小写）。

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
