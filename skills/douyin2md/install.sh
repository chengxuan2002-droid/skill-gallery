#!/usr/bin/env bash
# douyin2md 一键安装脚本
#
# 会把本 skill 安装到 agent 的技能目录，并装齐所有依赖。幂等，可重复运行。
#
# 说明:
#   依赖统一由 pyproject.toml / requirements.txt 声明；推荐 --skip-deps 只分发文件，
#   再按 docs/configuration.md 用 pip install -e '.[all]' 显式安装所需可选组。
#   装好后统一入口是 bash bin/douyin2md <子命令>，从任意工作目录都可用。
#
# 用法:
#   bash install.sh                          # 装到 ~/.agents/skills（Codex/Copilot/Gemini 通用）
#   bash install.sh --target codex,claude    # 同时装到多个 agent
#   bash install.sh --no-whisper             # 兼容旧参数（faster-whisper 已移除，空操作）
#   bash install.sh --no-sherpa              # 跳过 sherpa-onnx 中文引擎
#   bash install.sh --skip-deps              # 只拷贝文件，不装依赖
#   bash install.sh --dry-run                # 只打印将要执行的操作
#   bash install.sh --uninstall              # 卸载

set -uo pipefail

# ---------- 配置 ----------
SKILL_NAME="douyin2md"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGETS="codex"
SKIP_DEPS=0
DRY_RUN=0
UNINSTALL=0
NO_WHISPER=0
NO_SHERPA=0
NO_PLAYWRIGHT=0

# ---------- 输出 ----------
c_reset=$'\033[0m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'
c_red=$'\033[31m'; c_blue=$'\033[34m'; c_dim=$'\033[2m'
if [ ! -t 1 ]; then
  c_reset=""; c_green=""; c_yellow=""; c_red=""; c_blue=""; c_dim=""
fi
ok()   { printf "  ${c_green}✓${c_reset} %s\n" "$1"; }
warn() { printf "  ${c_yellow}!${c_reset} %s\n" "$1"; }
err()  { printf "  ${c_red}✗${c_reset} %s\n" "$1" >&2; }
info() { printf "  ${c_dim}%s${c_reset}\n" "$1"; }
step() { printf "\n${c_blue}▸ %s${c_reset}\n" "$1"; }

# ---------- 参数 ----------
while [ $# -gt 0 ]; do
  case "$1" in
    --target)        TARGETS="$2"; shift 2 ;;
    --skip-deps)     SKIP_DEPS=1; shift ;;
    --dry-run)       DRY_RUN=1; shift ;;
    --uninstall)     UNINSTALL=1; shift ;;
    --no-whisper)    NO_WHISPER=1; shift ;;
    --no-sherpa)     NO_SHERPA=1; shift ;;
    --no-playwright) NO_PLAYWRIGHT=1; shift ;;
    -h|--help)       sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^#\{1,\} \{0,1\}//'; exit 0 ;;
    *) err "未知参数: $1"; exit 1 ;;
  esac
done

# ---------- 目标目录映射 ----------
target_dir() {
  case "$1" in
    codex|agents)  echo "$HOME/.agents/skills/$SKILL_NAME" ;;
    codex-local)   echo "$HOME/.codex/skills/$SKILL_NAME" ;;
    workbuddy)     echo "$HOME/.workbuddy/skills/$SKILL_NAME" ;;
    claude)        echo "$HOME/.claude/skills/$SKILL_NAME" ;;
    cursor)        echo "$HOME/.cursor/skills/$SKILL_NAME" ;;
    gemini)        echo "$HOME/.gemini/skills/$SKILL_NAME" ;;
    copilot)       echo "$HOME/.copilot/skills/$SKILL_NAME" ;;
    *)             return 1 ;;
  esac
}

run() {
  if [ "$DRY_RUN" -eq 1 ]; then info "[dry-run] $*"; else "$@"; fi
}

# ---------- 卸载 ----------
if [ "$UNINSTALL" -eq 1 ]; then
  step "卸载 $SKILL_NAME"
  IFS=',' read -ra list <<< "$TARGETS"
  for t in "${list[@]}"; do
    d="$(target_dir "$t")" || { err "未知目标: $t"; continue; }
    if [ -d "$d" ]; then
      run rm -rf "$d" && ok "已删除 $d"
    else
      info "$d 不存在，跳过"
    fi
  done
  info "cookie 与配置保留在 ~/.douyin2md/，如需清除：rm -rf ~/.douyin2md"
  exit 0
fi

# ---------- 环境检测 ----------
OS="$(uname -s)"
case "$OS" in
  Darwin) OS_LABEL="macOS"; PKG="brew" ;;
  Linux)  OS_LABEL="Linux";  PKG="apt" ;;
  *)      OS_LABEL="$OS";    PKG="" ;;
esac

printf "${c_blue}douyin2md 安装程序${c_reset}\n"
info "系统: $OS_LABEL  目标: $TARGETS  脚本目录: $SCRIPT_DIR"

if [ ! -f "$SCRIPT_DIR/SKILL.md" ]; then
  err "在 $SCRIPT_DIR 下没找到 SKILL.md，请在 skill 目录内运行本脚本"
  exit 1
fi

# ---------- 1. 依赖 ----------
if [ "$SKIP_DEPS" -eq 1 ]; then
  step "跳过依赖安装（--skip-deps）"
else
  step "检查依赖"

  # python3
  if command -v python3 >/dev/null 2>&1; then
    ok "python3 $(python3 -V 2>&1 | awk '{print $2}')"
  else
    err "未找到 python3，请先安装 Python 3.9+"
    exit 1
  fi

  # ffmpeg（必需：抽音频、切片）
  if command -v ffmpeg >/dev/null 2>&1; then
    ok "ffmpeg $(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')"
  else
    warn "缺少 ffmpeg，正在安装..."
    if [ "$PKG" = "brew" ]; then
      if ! command -v brew >/dev/null 2>&1; then
        err "未安装 Homebrew。请访问 https://brew.sh 安装后重试，或手动: brew install ffmpeg"
        exit 1
      fi
      run brew install ffmpeg && ok "ffmpeg 安装完成" || { err "ffmpeg 安装失败"; exit 1; }
    elif [ "$PKG" = "apt" ]; then
      info "需要 sudo 权限安装 ffmpeg"
      run sudo apt-get update -qq && run sudo apt-get install -y -qq ffmpeg && ok "ffmpeg 安装完成" \
        || { err "ffmpeg 安装失败"; exit 1; }
    else
      err "请手动安装 ffmpeg 后重试: https://ffmpeg.org/download.html"
      exit 1
    fi
  fi

  # pip 安装（处理 PEP 668 externally-managed 限制）
  pip_install() {
    local pkg="$1"
    if python3 -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('$2') else 1)" 2>/dev/null; then
      ok "$pkg 已安装，跳过"
      return 0
    fi
    info "安装 $pkg ..."
    if [ "$DRY_RUN" -eq 1 ]; then info "[dry-run] pip3 install $pkg"; return 0; fi
    if pip3 install -q "$pkg" 2>/dev/null; then
      ok "$pkg 安装完成"
    elif pip3 install -q --break-system-packages "$pkg" 2>/dev/null; then
      ok "$pkg 安装完成（--break-system-packages）"
    else
      err "$pkg 安装失败，请手动执行: pip3 install $pkg"
      return 1
    fi
  }

  # 模块名与包名不一致，单独映射
  check_py_pkg() {
    local pkg="$1" mod="$2"
    if python3 -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('$mod') else 1)" 2>/dev/null; then
      ok "$pkg 已安装，跳过"
    else
      info "安装 $pkg ..."
      if [ "$DRY_RUN" -eq 1 ]; then info "[dry-run] pip3 install $pkg"; return 0; fi
      if pip3 install -q "$pkg" 2>/dev/null; then ok "$pkg 安装完成"
      elif pip3 install -q --break-system-packages "$pkg" 2>/dev/null; then
        ok "$pkg 安装完成（--break-system-packages）"
      else
        err "$pkg 安装失败"; return 1
      fi
    fi
  }

  check_py_pkg "yt-dlp" "yt_dlp"

  if [ "$NO_PLAYWRIGHT" -eq 1 ]; then
    warn "跳过 playwright（--no-playwright）。将只能手动提供 cookie"
  else
    check_py_pkg "playwright" "playwright"
    if [ "$DRY_RUN" -eq 0 ]; then
      if python3 -m playwright install --help >/dev/null 2>&1; then
        if python3 -c "
from playwright.sync_api import sync_playwright
import sys
try:
    with sync_playwright() as p:
        p.chromium.executable_path
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
          ok "chromium 已就绪"
        else
          info "下载 chromium（约 150MB，首次较慢）..."
          python3 -m playwright install chromium >/dev/null 2>&1 \
            && ok "chromium 安装完成" || warn "chromium 下载失败，可稍后手动: python3 -m playwright install chromium"
        fi
      fi
    fi
  fi

  # faster-whisper 已从本 skill 移除：需 torch、1.5GB+。
  # 本地 ASR 统一用 sherpa-onnx（约 60MB 模型，无需 torch，中文更准）。
  if [ "$NO_WHISPER" -eq 1 ]; then
    info "faster-whisper 已移除，--no-whisper 为保持兼容的空操作"
  else
    info "跳过 faster-whisper（需 torch/1.5GB+），本地 ASR 改用 sherpa-onnx"
  fi

  # sherpa-onnx：中文更准、体积更小的本地引擎（仅 ~51MB 依赖，不需 torch）
  if [ "$NO_SHERPA" -eq 1 ]; then
    warn "跳过 sherpa-onnx（--no-sherpa）"
  else
    check_py_pkg "sherpa-onnx" "sherpa_onnx"
    check_py_pkg "numpy" "numpy"
  fi
fi

# ---------- 2. 安装 skill ----------
step "安装 skill 文件"
INSTALLED=()
IFS=',' read -ra list <<< "$TARGETS"
for t in "${list[@]}"; do
  t="$(echo "$t" | tr -d ' ')"
  d="$(target_dir "$t")" || { err "未知目标: $t（可选: codex claude cursor gemini copilot codex-local workbuddy）"; continue; }

  if [ "$d" = "$SCRIPT_DIR" ]; then
    ok "目标目录就是当前目录，无需复制"
    INSTALLED+=("$d")
    continue
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    info "[dry-run] 复制 $SCRIPT_DIR -> $d"
    INSTALLED+=("$d")
    continue
  fi

  mkdir -p "$(dirname "$d")"
  rm -rf "$d"
  mkdir -p "$d"
  cp -R "$SCRIPT_DIR"/. "$d"/
  # 只分发技能本体：清掉仓库元数据、缓存与本机运行时/敏感文件。
  # 尤其 cookies*.txt / config.json 属于本机数据，绝不能跟着复制进技能目录。
  rm -rf "$d"/.git "$d"/.workbuddy "$d"/.pytest_cache "$d"/.venv "$d"/venv \
         "$d"/.idea "$d"/.vscode "$d"/notes "$d"/douyin_out "$d"/models \
         "$d"/build "$d"/dist
  find "$d" -type d \( -name '__pycache__' -o -name '*.egg-info' -o -name '.artifacts*' \) \
       -prune -exec rm -rf {} + 2>/dev/null || true
  find "$d" -type f \( -name '.DS_Store' -o -name 'Thumbs.db' \
       -o -name '*.pyc' -o -name '*.pyo' -o -name '*.json.tmp' \
       -o -name 'cookies*.txt' -o -name '*.cookies' -o -name 'config.json' \
       -o -name '*.mp3' -o -name '*.mp4' -o -name '*.m4a' -o -name '*.wav' \
       -o -name '*.flac' -o -name '*.mov' -o -name '*.mkv' -o -name '*.aac' \
       -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \) -delete 2>/dev/null || true
  chmod +x "$d"/install.sh "$d"/scripts/*.py "$d"/bin/douyin2md "$d"/examples/cli.sh 2>/dev/null
  ok "$d"
  INSTALLED+=("$d")
done

# ---------- 3. 自检 ----------
step "自检"
SELFTEST_OK=1

for d in "${INSTALLED[@]}"; do
  if [ "$DRY_RUN" -eq 1 ]; then continue; fi

  # BOM 检查（带 BOM 的 SKILL.md 会被静默忽略）
  if head -c 3 "$d/SKILL.md" | od -An -tx1 | grep -q "ef bb bf"; then
    err "$d/SKILL.md 含 UTF-8 BOM，会导致 skill 无法加载"
    SELFTEST_OK=0
  elif [ -f "$d/SKILL.md" ]; then
    ok "SKILL.md 无 BOM"
  else
    err "$d/SKILL.md 不存在"
    SELFTEST_OK=0
  fi

  # frontmatter 检查
  if head -1 "$d/SKILL.md" | grep -q '^---$' \
     && grep -qE '^name:' "$d/SKILL.md" \
     && grep -qE '^description:' "$d/SKILL.md"; then
    ok "frontmatter 格式正确（name + description）"
  else
    err "SKILL.md 缺少 name/description frontmatter"
    SELFTEST_OK=0
  fi

  # 脚本完整性（9 个原始脚本，capture / cookie 辅助脚本同样纳入校验）
  missing=0
  for s in dy.py dy_fetch.py dy_transcribe.py dy_tomd.py dy_model.py \
           dy_cookie.py dy_cookie_headless.py dy_cookie_merge_msToken.py \
           dy_browser_capture.py; do
    [ -f "$d/scripts/$s" ] || { err "缺少 scripts/$s"; missing=1; }
  done
  [ "$missing" -eq 0 ] && ok "9 个原始脚本齐全"

  # 统一入口与接口层
  if [ -f "$d/bin/douyin2md" ] && [ -f "$d/douyin2md/cli.py" ]; then
    ok "统一入口 bin/douyin2md 就绪"
  else
    err "缺少统一入口 bin/douyin2md 或 douyin2md/cli.py"
    SELFTEST_OK=0
  fi
done

if [ "$DRY_RUN" -eq 0 ] && [ "$SKIP_DEPS" -eq 0 ]; then
  command -v ffmpeg >/dev/null 2>&1 && ok "ffmpeg 可用" || { err "ffmpeg 仍不可用"; SELFTEST_OK=0; }
  python3 -c "import yt_dlp" 2>/dev/null && ok "yt-dlp 可用" || { err "yt-dlp 仍不可用"; SELFTEST_OK=0; }
fi

# ---------- 4. 收尾 ----------
printf "\n"
if [ "$DRY_RUN" -eq 1 ]; then
  printf "${c_yellow}以上是 dry-run 预览，未执行任何实际修改。${c_reset}\n"
  printf "去掉 --dry-run 正式执行。\n"
  exit 0
fi

if [ "$SELFTEST_OK" -eq 1 ]; then
  printf "${c_green}安装完成。${c_reset}\n\n"
else
  printf "${c_yellow}安装完成，但自检发现问题（见上）。${c_reset}\n\n"
fi

printf "统一入口（任意工作目录都可用，无需记忆 8 个脚本）:\n"
printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md --help${c_reset}\n"
printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md doctor${c_reset}   只读体检\n\n"

printf "下一步（只需做一次）:\n\n"
N=1
if [ "$NO_SHERPA" -eq 0 ]; then
  printf "  ${N}. 下载中文 ASR 模型（约 60MB，中文比 Whisper 更准且体积小 10 倍）:\n"
  printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md model download${c_reset}\n\n"
  N=$((N+1))
fi
printf "  ${N}. 导出抖音 cookie（会弹出浏览器，扫码登录）:\n"
printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md cookie${c_reset}\n\n"
N=$((N+1))
printf "  ${N}. 验证:\n"
printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md cookie --check${c_reset}\n"
printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md model status${c_reset}\n\n"
N=$((N+1))
printf "  ${N}. 试跑:\n"
printf "     ${c_blue}bash ${INSTALLED[0]}/bin/douyin2md url \"抖音链接\" -o ./notes${c_reset}\n\n"

printf "  依赖分层、配置优先级与环境变量见 docs/configuration.md；\n"
printf "  各框架如何识别见 docs/agent-compatibility.md。\n"
printf "  之后重开一个 agent 会话，直接说「把这个抖音视频转成 md: <链接>」即可自动触发。\n"
printf "  ${c_dim}若 skill 未生效，重启对应 agent 让它重新扫描技能目录。${c_reset}\n"

exit $((1 - SELFTEST_OK))
