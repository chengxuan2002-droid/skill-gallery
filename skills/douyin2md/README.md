# douyin2md

把一个抖音链接（或本地音视频）变成**两个** Markdown 交付物：一篇带 YAML frontmatter、
带时间戳的**逐字稿**（末尾附「语音识别专名校正对照表」与「可靠性说明」），一篇要点式
**总结**（视频主题 + 核心方法，逐条标注章节或时间节点，不写文章）。

微信视频号链接会自动按来源降级：预览页不下发视频流，只取元数据与高清封面，产出明确
标注缺失项的 `metadata_only` 文稿（不臆造转写或时间戳）。抖音直连若被 Argus / `a_bogus`
风控拦截，`url` 会自动切换浏览器拦截兜底，仍产出完整逐字稿，无需手动换脚本。

这既是一个**标准 Agent Skill**，也是一个普通 Python 项目。任何支持 Agent Skills 的框架
（Claude Code、Codex、WorkBuddy、Cursor、Gemini CLI、GitHub Copilot CLI、OpenCode、goose…）
把本仓库放进它的 skills 目录就能识别，**无需修改仓库内任何文件**。

## 为什么说是「通用」

| 原来的问题 | 现在的做法 |
| --- | --- |
| 8 个脚本各自是入口，agent 要背命令 | 单一入口 `bin/douyin2md <子命令>`，配置注入后转发到原脚本 |
| 依赖散落在 `install.sh` 的 brew/pip 命令里 | `pyproject.toml` extras（`core` / `local` / `browser` / `all`）+ `requirements.txt` |
| 数据目录、模型、Key 硬编码在各脚本 | `douyin2md/config.py` 统一读取：默认值 → JSON 配置 → 环境变量 → 命令行 |
| SKILL.md 里混着本机路径、解释器踩坑 | SKILL.md 只讲通用调用；环境相关记录移到 `docs/troubleshooting.md` |
| 命令依赖 cwd 或某个固定安装目录 | 入口用 `BASH_SOURCE` 自定位技能根，任意工作目录可调用 |
| 各框架安装方式靠口头说明 | `docs/agent-compatibility.md` 逐框架给出目录与命令 |

原始脚本 `scripts/*.py` 作为兼容层继续可单独调用，命令行参数保持兼容；
新入口只做转发，历史笔记里的命令依然有效。本版对 4 个既有脚本（`dy.py` / `dy_fetch.py` /
`dy_tomd.py` / `dy_browser_capture.py`）做了增量修改，并新增 3 个适配器/诊断脚本
（`wx_fetch.py` / `wx_ocr.py` / `wx_session_check.py`）。默认产物由单篇改为
「逐字稿 + 总结」两个文件；加 `--single-file` 可回到与 `main` 分支逐字一致的单篇文稿。
详见 `CHANGELOG.md` 与 `docs/architecture.md`。

## 快速开始

### 作为 Agent Skill 安装（推荐）

仓库：`https://github.com/chengxuan2002-droid/douyin2md.git`（**Public**，可匿名 clone，
无需账号权限；SSH 备选为 `git@github.com:chengxuan2002-droid/douyin2md.git`）。

```bash
REPO=https://github.com/chengxuan2002-droid/douyin2md.git
# 任选你的框架（详见 docs/agent-compatibility.md）
git clone "$REPO" ~/.claude/skills/douyin2md      # Claude Code
git clone "$REPO" ~/.agents/skills/douyin2md      # Codex / Copilot CLI / Gemini CLI
git clone "$REPO" ~/.workbuddy/skills/douyin2md   # WorkBuddy
```

也可以在本仓库检出目录里一键装到多个框架（不依赖网络）：

```bash
bash install.sh --target codex,claude,workbuddy --skip-deps
bash install.sh --dry-run        # 先看会做什么
```

装完直接对 agent 说「把这个抖音视频转成 md：<链接>」即可自动触发。

### 作为普通 Python 包安装

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[all]'          # 或 '[local]' / '[browser]'，见 docs/configuration.md
douyin2md --help
```

系统还需 `ffmpeg`（macOS `brew install ffmpeg`，Ubuntu `apt install ffmpeg`）。

### 首次准备（每次换环境只做一次）

```bash
bash bin/douyin2md doctor            # 只读体检：缺什么一目了然
bash bin/douyin2md model download    # 本地中文模型，约 60MB
bash bin/douyin2md cookie            # 浏览器登录导出 cookie
```

## 输出：两个文件

每次成功转写产出同一前缀的两个 Markdown：

| 文件 | 内容 |
| --- | --- |
| `<作者>-<标题>-逐字稿.md` | frontmatter + 元信息表 + 视频文案 + 带 `[mm:ss]` 的转写正文 + **附录 A 语音识别专名校正对照表**（原识别 / 校正 / 出现位置）+ **附录 B 可靠性说明**（客观依据 / 结论支撑 / 需解释澄清项） |
| `<作者>-<标题>-总结.md` | **视频主题**（核心话题、核心观点）+ **核心方法**（关键技术、实现思路、论证方式），一条要点一行，句末标 `（[mm:ss]）` 或 `（[mm:ss] · 章节名）` |

总结由脚本渲染、由 agent 提供内容：`url` / `batch` 先出逐字稿和一份
`summary_status: pending` 的总结骨架，随后按需写标注 JSON 重新渲染：

```bash
bash bin/douyin2md to-md \
  --meta ./notes/.artifacts/<id>.meta.json \
  --transcript ./notes/.artifacts/transcripts/<id>.json \
  --annotations ./ann.json -o ./notes
```

标注 JSON 见 `examples/标注示例.json`，字段说明见 `SKILL.md`「输出形态」与
`scripts/dy_tomd.py` 顶部文档字符串。`--single-file` 回到旧的单篇合并文稿
（不拆总结、不带附录）；没有转写正文时只产出元数据文稿，不生成总结。

## 统一命令速查

```bash
bash bin/douyin2md url "https://v.douyin.com/xxxx/" -o ./notes          # 单条抖音（逐字稿 + 总结）
bash bin/douyin2md url "https://weixin.qq.com/sph/xxxx" -o ./notes      # 视频号（自动降级）
bash bin/douyin2md batch urls.txt -o ./notes                             # 批量（按来源分流）
bash bin/douyin2md transcribe ./会议录音.mp4 -o 会议录音.json             # 本地单文件
bash bin/douyin2md transcribe ./访谈集/ -o ./访谈转录/                    # 本地目录批量
bash bin/douyin2md to-md --meta m.json --transcript t.json --annotations ann.json -o ./notes  # 重新渲染
bash bin/douyin2md to-md --meta m.json --transcript t.json --single-file -o ./notes           # 旧单篇产物
bash bin/douyin2md capture "https://v.douyin.com/xxxx/" -o ./.artifacts --fresh  # 手动取 mp4（全新游客会话）
bash bin/douyin2md model list | status | download | path
bash bin/douyin2md cookie --check
bash bin/douyin2md doctor --json                                         # 机器可读体检
bash bin/douyin2md config                                                # 生效配置（密钥脱敏）
```

`url` / `batch` 先按来源分流：抖音走完整三段式；视频号走只读元数据 + 高清封面，产出
`metadata_only` 文稿（自动声明缺失项，不臆造时间戳）；未知来源返回 `unsupported_source`。
批量结束会输出状态清单。

**抖音直连被风控时自动兜底**：`dy_fetch.py` 先把短链解析成长链，直连仍失败
（`Fresh cookies` / Argus / `a_bogus`）就自动用真实浏览器拦截 `aweme/detail` 取得
mp4，映射成同一份 `meta.json` 契约后照常转写，最终仍是完整逐字稿。兜底默认用全新
游客会话（复用旧 profile + 登录 cookie 易命中「验证码中间页」），日志会提示
「已自动由浏览器拦截兜底取得真实媒体」，`meta.json` 带 `capture_fallback: true`。
开关：`--no-capture-fallback` 禁用、`--force-capture` 跳过直连；单独取 mp4 用
`capture --fresh`。**不破解验证码、不伪造签名。**

加 `--ocr` 可对视频号高清封面做本地文字识别（默认关闭，macOS 用
系统 Vision，结果单列「封面文字（OCR，须人工核对）」，**不得当作口播或时间戳**）：

```bash
bash bin/douyin2md url "https://weixin.qq.com/sph/xxxx" -o ./notes --ocr
```

视频号需要逐字稿时，请在微信客户端保存视频或录屏后用同一份 `meta.json` 合并转写结果：

```bash
bash bin/douyin2md transcribe ./视频.mp4 -o t.json
bash bin/douyin2md to-md --meta ./notes/.artifacts/<id>.meta.json --transcript t.json -o ./notes
```

`scripts/wx_session_check.py` 是可选的带会话字段差异验证工具，**默认不执行**：必须由用户
提供 cookie 并显式加 `--authorize` 才会发出带会话请求，报告脱敏且不下载视频。

详见 `SKILL.md` 的「非抖音来源」与 `docs/troubleshooting.md` 的视频号章节。

常用参数：`--engine auto|sherpa|siliconflow|openai|local`、`--model`、`--language zh`、
`--cookies`、`--cookies-from-browser`、`--no-timestamps`、`--keep-audio`、
`--annotations`（重新渲染专名校正与总结）、`--single-file`（旧单篇产物）、
`--no-capture-fallback` / `--force-capture`、
`--ocr` / `--ocr-backend auto|macos-vision|tesseract|none` / `--ocr-min-confidence 0.8`、
`-o`、`-q`。`--config <文件>` 可放在命令任意位置。完整说明见 `docs/configuration.md`。

## 仓库结构

```
douyin2md/
├── SKILL.md                   # Agent Skills 标准入口（agent 唯一必读文件）
├── README.md                  # 本文件
├── LICENSE                    # MIT
├── CHANGELOG.md
├── pyproject.toml             # 依赖分层 + console script
├── requirements.txt           # 依赖速查
├── config.example.json        # 统一配置模板
├── install.sh                 # 多框架一键安装 / 自检 / 卸载
├── bin/douyin2md              # 统一命令入口（自定位，任意 cwd 可用）
├── douyin2md/                 # 统一接口层
│   ├── __init__.py
│   ├── __main__.py            # python3 -m douyin2md
│   ├── cli.py                 # 子命令解析、配置注入、转发
│   ├── config.py              # 配置优先级与脱敏
│   └── sources.py             # 来源判定 / 状态契约（唯一判定源，纯逻辑）
├── scripts/                   # 流水线脚本（兼容层，可单独调用）
│   ├── dy.py                  # 链接 → Markdown（单条 + 批量，按来源分流）
│   ├── dy_fetch.py            # 抖音元数据 + 音频（短链解析、精确诊断、风控自动兜底）
│   ├── wx_fetch.py            # 视频号只读元数据 + 高清封面 + 可选 OCR（新增）
│   ├── wx_ocr.py              # 封面 OCR 适配器（macOS Vision / tesseract，新增）
│   ├── wx_session_check.py    # 授权后的会话字段差异验证（默认不执行，新增）
│   ├── dy_transcribe.py       # 语音转文字
│   ├── dy_tomd.py             # 渲染两个交付文件（逐字稿 + 附录 A/B、总结）
│   ├── dy_model.py            # 本地模型管理
│   ├── dy_cookie*.py          # cookie 获取 / 合并
│   └── dy_browser_capture.py  # 浏览器拦截兜底
├── docs/                      # 框架兼容、配置、架构、排障
├── examples/                  # 逐字稿/总结样例、标注 JSON 模板、链接清单、CLI 与提示词示例
└── tests/                     # 零依赖单测：配置、入口、来源判定、适配器契约、两文件契约与回归
```

## 深入文档

- `docs/agent-compatibility.md` — 各框架如何识别与安装（无需改代码）
- `docs/configuration.md` — 依赖分层、配置优先级、环境变量全表
- `docs/architecture.md` — 来源适配层、三段式流水线与降级契约
- `docs/troubleshooting.md` — 风控、cookie、模型、解释器踩坑、视频号预览页限制
- `examples/` — 可照抄的命令与 agent 提示词

## 合规与许可

仅供个人学习研究与已获授权内容使用；下载内容版权归原作者所有，请勿商用或传播。
本项目代码以 MIT 许可发布，见 `LICENSE`。cookie 与模型缓存由 `.gitignore` 排除，
**不要把登录态文件或 API Key 提交进仓库**。
