---
name: douyin2md
description: 把抖音视频或本地音视频转成 Markdown 文稿。用户发抖音链接（v.douyin.com 短链、www.douyin.com/video/<id>、或含链接的分享文案）要求"转文字/提取文案/整理成笔记/存成 md/生成逐字稿/总结一下"时使用；一次发多个链接或整个列表/收藏夹要求"批量/全部转成 md"时也使用；发本地音视频文件或目录要求转录时同样适用。自动区分单条与批量，无需用户选择脚本。支持元数据提取、语音转写（本地离线或云端）、带时间戳正文、YAML frontmatter。
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
| `url <链接或文案>` | 单个抖音链接 → Markdown |
| `batch <links.txt>` | 批量链接，每条一篇 Markdown，单条失败不中断 |
| `transcribe <文件/目录>` | 本地音视频 → 转写 JSON（无需 cookie） |
| `to-md --meta <json>` | 元数据 + 转写 JSON → Markdown |
| `capture <链接>` | 风控兜底：浏览器拦截 detail 响应并下载 mp4 |
| `model <list\|status\|download\|path>` | 本地 ASR 模型管理 |
| `cookie [--check]` | 浏览器登录导出 cookie |
| `doctor` | 只读环境体检（不联网、不安装） |
| `config` | 打印生效配置（密钥只显示 set/not set） |

## 模式自动选择（先读这一段）

**不要问用户要单条还是批量，更不要让用户自己选脚本。** 按输入形态直接执行：

| 用户给的东西 | 执行 |
| --- | --- |
| 1 个抖音链接 / 1 段分享文案 | `bash bin/douyin2md url "<链接或文案>" -o ./notes` |
| 多个链接 / 列表 / 收藏夹 / "全部" | 逐行写入临时文件，再 `bash bin/douyin2md batch urls.txt -o ./notes` |
| 1 个本地音视频文件 | `bash bin/douyin2md transcribe ./录音.mp4 -o 录音.json` |
| 本地一个目录 / 一批文件 | `bash bin/douyin2md transcribe ./访谈集/ -o ./访谈转录/`（模型只加载一次） |
| 主路径 403 / detail 返回空 | `bash bin/douyin2md capture "<链接>" -o ./.artifacts` |

判断不清时按「能直接跑的最小范围」执行，完成后补问是否需要处理更多。
批量输出自动带 `序号-作者-标题.md` 前缀，避免同名覆盖；批量逐条串行，不要高并发以免限流。

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

## 输出形态

默认产出**逐字稿**：YAML frontmatter + 元信息表 + 视频文案 `desc` + 带时间戳转写正文
（格式见 `examples/示例输出.md`）。视频描述文案与口播转写是两种不同来源，都要保留，不要互相替代。

用户说「提取核心内容 / 总结 / 讲的是什么 / 有哪些方法和步骤」时，要的是**结构化总结文档**，
不是逐字稿。常用骨架：主题 → 核心方法（配表格）→ 实施步骤 → 横向对比 → 进阶点 → 转写来源说明。
`desc` / 作者 / 时长 / 统计信息可从 detail.json 直取，自行写 frontmatter 更灵活。

**专名核实（必须做）**：口播里的英文/品牌专名易错，三级校验依次是
① 换一档模型重跑交叉校验 → ② `ffmpeg` 抽帧读画面字幕定案 → ③ 查项目官网/仓库核对拼写。
两个模型一致也可能都错，不能据此下结论。抽帧看片头标题、结构切换处、结尾念产品名处。

## 注意事项

- **禁止臆造**：转写失败或为空时如实说明，绝不编造视频内容。
- 原文有缺陷时保留原样，问题写在正文外的编者注里。
- 合规：仅用于自己创作或已获授权的内容，下载内容版权归原作者。
- 用户要求「与之前提取的几期对比 / 有什么进阶点」时，按
  `docs/troubleshooting.md` 的「系列内容的跨期对比」做表格与脉络图，只依据已提取内容。
- 深入阅读：`docs/agent-compatibility.md`（各框架接入与加载陷阱）、`docs/configuration.md`（依赖与配置）、
  `docs/architecture.md`（流水线）、`docs/troubleshooting.md`（风控、故障表、内容质量）。
