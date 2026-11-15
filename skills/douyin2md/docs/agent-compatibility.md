# 各 Agent 框架接入说明

## 为什么「无需修改」

本仓库满足 Agent Skills 的通用约定：

1. `SKILL.md` 在**仓库根目录**，frontmatter 只含标准字段 `name` / `description`
   （`license` 为可选标准字段，不认识的框架会忽略）。
2. 所有调用都是相对路径：`bash bin/douyin2md <子命令>`；入口脚本用
   `BASH_SOURCE` 定位技能根，不依赖调用方的工作目录，也不写死任何安装位置。
3. 仓库里没有框架专属配置（无 `.claude-plugin/`、无 `plugin.json`、无硬编码 `~/.codex/...`），
   因此同一份文件可以同时放进任意框架的 skills 目录。
4. 运行时数据统一放 `~/.douyin2md/`（可由 `DOUYIN2MD_HOME` 改），
   多个框架共用同一份 cookie 与模型缓存，不会互相覆盖。

框架只需做一件事：**把本目录放进它扫描 skills 的位置**。

## 安装位置对照表

仓库地址：`git@github.com:chengxuan2002-droid/douyin2md.git`（Private，需账号权限），
下表的 `<repo>` 即指它；HTTPS 备选为
`https://github.com/chengxuan2002-droid/douyin2md.git`。

| 框架 | 用户级 skills 目录 | 安装命令 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `git clone <repo> ~/.claude/skills/douyin2md` |
| Codex | `~/.agents/skills/`（通用共享）或 `~/.codex/skills/` | `bash install.sh --target codex` |
| WorkBuddy | `~/.workbuddy/skills/` | `bash install.sh --target workbuddy` |
| Cursor | `~/.cursor/skills/` | `bash install.sh --target cursor` |
| Gemini CLI | `~/.gemini/skills/` | `bash install.sh --target gemini` |
| GitHub Copilot CLI | `~/.copilot/skills/` 或 `~/.agents/skills/` | `bash install.sh --target copilot` |
| OpenCode / goose / Cline / Windsurf | 各自的 skills 目录 | `git clone <repo> <该框架 skills 目录>/douyin2md` |
| 项目级（任意框架） | `<项目>/.agents/skills/` 或 `.claude/skills/` | `git clone <repo> .agents/skills/douyin2md` |

`install.sh` 支持的目标名：`codex`（= `~/.agents/skills`，默认）、`codex-local`、`claude`、
`cursor`、`gemini`、`copilot`、`workbuddy`。多个目标用逗号分隔，例如
`bash install.sh --target codex,claude,workbuddy --skip-deps`。
`--dry-run` 可先预览，`--uninstall` 可移除。

> 私有仓库：clone 需要该 GitHub 账号的访问权限；公开分享时把仓库可见性改为 Public 即可。

## 触发方式

装完后不用记命令，直接用自然语言（各框架相同）：

```text
把这个抖音视频转成 md：https://v.douyin.com/xxxx/
把这几个链接都整理成笔记：<链接1> <链接2> <链接3>
把 ./访谈集/ 里的音频全部转录成 md
```

框架读取 `SKILL.md` 的 `description` 决定是否触发，再按「模式自动选择」表调用统一入口。

## 等价入口（三种，任选其一）

| 入口 | 适用 | 说明 |
| --- | --- | --- |
| `bash bin/douyin2md …` | **Agent 默认，推荐** | 无需 pip 安装，从任意 cwd 可用 |
| `python3 -m douyin2md …` | 已把技能根加入 `PYTHONPATH` | `bin/douyin2md` 内部就是这么调的 |
| `douyin2md …` | `pip install -e .` 之后 | `pyproject.toml` 的 console script |

三者共用同一份 `douyin2md/cli.py`，参数与行为完全一致。

## 多框架并存

四个框架可以同时安装同一版本：它们读的是各自的副本，但运行时共享
`~/.douyin2md/` 下的 cookie 与模型。升级时**逐个副本更新**，避免版本漂移：

```bash
for d in ~/.claude/skills/douyin2md ~/.agents/skills/douyin2md \
         ~/.workbuddy/skills/douyin2md ~/.codex/skills/douyin2md; do
  [ -d "$d" ] && git -C "$d" pull --ff-only
done
```

若副本是拷贝而非 git clone，用 `rsync -a --delete --exclude=.git <新仓库>/ "$d"/` 同步。
升级后跑一次 `bash bin/douyin2md doctor` 确认环境未缺失。
