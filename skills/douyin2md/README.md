# douyin2md

把一个抖音链接（或本地音视频）变成一篇带 YAML frontmatter 的 Markdown 文稿：
元信息表 + 视频描述文案 + 带时间戳的口播转写正文。

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

原始脚本 `scripts/*.py` **保持字节不变**，作为兼容层继续可用；新入口只做转发，
因此既统一了接口，也不会破坏已有调用或历史笔记里的命令。

## 快速开始

### 作为 Agent Skill 安装（推荐）

仓库：`git@github.com:chengxuan2002-droid/douyin2md.git`（当前为 **Private**，
clone 需要该 GitHub 账号的访问权限；HTTPS 地址为
`https://github.com/chengxuan2002-droid/douyin2md.git`）。

```bash
REPO=git@github.com:chengxuan2002-droid/douyin2md.git
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

## 统一命令速查

```bash
bash bin/douyin2md url "https://v.douyin.com/xxxx/" -o ./notes          # 单条
bash bin/douyin2md batch urls.txt -o ./notes                             # 批量
bash bin/douyin2md transcribe ./会议录音.mp4 -o 会议录音.json             # 本地单文件
bash bin/douyin2md transcribe ./访谈集/ -o ./访谈转录/                    # 本地目录批量
bash bin/douyin2md capture "https://v.douyin.com/xxxx/" -o ./.artifacts  # 风控兜底
bash bin/douyin2md model list | status | download | path
bash bin/douyin2md cookie --check
bash bin/douyin2md doctor --json                                         # 机器可读体检
bash bin/douyin2md config                                                # 生效配置（密钥脱敏）
```

常用参数：`--engine auto|sherpa|siliconflow|openai|local`、`--model`、`--language zh`、
`--cookies`、`--cookies-from-browser`、`--no-timestamps`、`--keep-audio`、`-o`、`-q`。
`--config <文件>` 可放在命令任意位置。完整说明见 `docs/configuration.md`。

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
│   └── config.py              # 配置优先级与脱敏
├── scripts/                   # 原始流水线脚本（兼容层，保持原样）
│   ├── dy.py                  # 链接 → Markdown（单条 + 批量）
│   ├── dy_fetch.py            # 元数据 + 音频
│   ├── dy_transcribe.py       # 语音转文字
│   ├── dy_tomd.py             # 拼装 Markdown
│   ├── dy_model.py            # 本地模型管理
│   ├── dy_cookie*.py          # cookie 获取 / 合并
│   └── dy_browser_capture.py  # 浏览器拦截兜底
├── docs/                      # 框架兼容、配置、架构、排障
├── examples/                  # 输出样例、链接清单、CLI 与提示词示例
└── tests/                     # 配置与入口的零依赖单测
```

## 深入文档

- `docs/agent-compatibility.md` — 各框架如何识别与安装（无需改代码）
- `docs/configuration.md` — 依赖分层、配置优先级、环境变量全表
- `docs/architecture.md` — 三段式流水线与兼容层设计
- `docs/troubleshooting.md` — 风控、cookie、模型、解释器踩坑
- `examples/` — 可照抄的命令与 agent 提示词

## 合规与许可

仅供个人学习研究与已获授权内容使用；下载内容版权归原作者所有，请勿商用或传播。
本项目代码以 MIT 许可发布，见 `LICENSE`。cookie 与模型缓存由 `.gitignore` 排除，
**不要把登录态文件或 API Key 提交进仓库**。
