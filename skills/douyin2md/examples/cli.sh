#!/usr/bin/env bash
# 统一入口使用示例（只演示，不会自动执行任何联网/下载动作）
# 从仓库根运行：bash examples/cli.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
D2M="bash $ROOT/bin/douyin2md"

$D2M --help
$D2M doctor                       # 只读体检
$D2M config                       # 生效配置（密钥脱敏）
$D2M model list                   # 可用本地 ASR 模型

# 首次准备（按需手动执行，会下载模型 / 打开浏览器）
# $D2M model download
# $D2M cookie

# 单条：一个链接或一段分享文案
# $D2M url "https://v.douyin.com/REPLACE_ME/" -o ./notes

# 批量：每行一个链接
# $D2M batch "$ROOT/examples/urls.txt" -o ./notes

# 本地音视频：单文件 / 整个目录（无需 cookie）
# $D2M transcribe ./会议录音.mp4 -o 会议录音.json
# $D2M transcribe ./访谈集/ -o ./访谈转录/

# 指定本地模型、保留中间音频
# $D2M url "https://v.douyin.com/REPLACE_ME/" --engine sherpa --model sense-voice-int8 --keep-audio

# 云端转写（密钥只走环境变量）
# export SILICONFLOW_API_KEY="YOUR_KEY_HERE"
# $D2M url "https://v.douyin.com/REPLACE_ME/" --engine siliconflow

# 风控兜底
# $D2M capture "https://v.douyin.com/REPLACE_ME/" -o ./.artifacts

# 自定义配置文件（--config 可放在任意位置）
# $D2M url "<链接>" --config "$ROOT/config.example.json"
