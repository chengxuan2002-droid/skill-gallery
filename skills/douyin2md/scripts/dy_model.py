#!/usr/bin/env python3
"""管理 sherpa-onnx 的中文 ASR 模型（下载、列表、校验）。

为什么用 sherpa-onnx 而不是 FunASR：
  - 依赖轻：onnxruntime ~51MB vs torch ~1722MB
  - 不联网：FunASR 内嵌 ModelScope SDK，即使模型在本地也会尝试联网校验
            （GitHub Issues #2573/#1581/#1286），内网环境会卡死
  - 中文更准：Paraformer / SenseVoice 中文 CER 明显优于 Whisper

用法:
    python3 dy_model.py list                              # 列出可选模型
    python3 dy_model.py download                          # 下载默认模型（自动选最快源）
    python3 dy_model.py download sense-voice-int8-2025    # 下载指定模型
    python3 dy_model.py status                            # 查看已下载
    python3 dy_model.py path sense-voice-int8-2025        # 打印模型目录，供脚本调用

默认模型为 sense-voice-int8-2025（SenseVoice 2025-09-09 int8，最新）。

若 GitHub Release 全部超时（国内网络常见），可从 HuggingFace 镜像手动取：
    https://hf-mirror.com/csukuangfj/<MODEL_DIR_NAME>/resolve/main/model.int8.onnx
    https://hf-mirror.com/csukuangfj/<MODEL_DIR_NAME>/resolve/main/tokens.txt
下载后放到 ~/.douyin2md/models/<MODEL_DIR_NAME>/ 即可，本脚本会自动识别。
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

MODEL_HOME = Path(os.getenv("SHERPA_MODEL_DIR",
                             Path.home() / ".douyin2md" / "models"))

# GitHub Release 上的官方模型（k2-fsa/sherpa-onnx）
BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"
VAD_URL = f"{BASE}/silero_vad.onnx"

# 多个下载源，逐个尝试，国内可走镜像
MIRRORS = [
    ("github",   f"{BASE}/{{name}}.tar.bz2"),
    ("ghproxy",  "https://ghproxy.com/https://github.com/k2-fsa/sherpa-onnx/"
                 "releases/download/asr-models/{name}.tar.bz2"),
    ("ghfast",   "https://ghfast.top/https://github.com/k2-fsa/sherpa-onnx/"
                 "releases/download/asr-models/{name}.tar.bz2"),
]

# 模型名 -> (说明, 引擎类型, 体积)
MODELS = {
    "sense-voice-int8-2025": (
        "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09",
        "sense_voice", "~226MB",
        "SenseVoice 2025-09 量化版（最新），中英日韩粤，默认首选",
    ),
    "sense-voice-int8": (
        "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17",
        "sense_voice", "~60MB",
        "中英日韩粤，量化版。体积小、速度快，日常首选",
    ),
    "sense-voice": (
        "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17",
        "sense_voice", "~230MB",
        "同上未量化版，精度略高，体积大 4 倍",
    ),
    "paraformer-zh-int8": (
        "sherpa-onnx-paraformer-zh-int8-2025-10-07",
        "paraformer", "~60MB",
        "纯中文 INT8，中文 CER 最低，适合纯普通话内容",
    ),
    "paraformer-zh": (
        "sherpa-onnx-paraformer-zh-2024-03-09",
        "paraformer", "~220MB",
        "纯中文完整版，中文识别最佳",
    ),
    "paraformer-zh-small": (
        "sherpa-onnx-paraformer-zh-small-2024-03-09",
        "paraformer", "~30MB",
        "轻量版，资源受限设备用，精度有损",
    ),
    "zipformer-zh-int8": (
        "sherpa-onnx-zipformer-ctc-zh-int8-2025-07-03",
        "zipformer_ctc", "~50MB",
        "Zipformer CTC 中文量化版，CPU 上很快",
    ),
}

DEFAULT_MODEL = "sense-voice-int8-2025"


def model_dir(key: str) -> Path:
    return MODEL_HOME / MODELS[key][0]


def is_ready(key: str) -> bool:
    d = model_dir(key)
    if not d.is_dir():
        return False
    has_model = any(d.glob("model*.onnx"))
    return has_model and (d / "tokens.txt").exists()


def vad_ready() -> bool:
    return (MODEL_HOME / "silero_vad.onnx").is_file()


def _download(url: str, dest: Path, label: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done / total * 100
                    sys.stdout.write(f"\r    {label} {pct:5.1f}%  "
                                     f"({done/1048576:.0f}/{total/1048576:.0f} MB)")
                    sys.stdout.flush()
            sys.stdout.write("\n")
        return True
    except Exception as e:
        sys.stdout.write("\n")
        print(f"    失败: {type(e).__name__}: {str(e)[:80]}")
        if dest.exists():
            dest.unlink()
        return False


def cmd_list(_args) -> int:
    print("可选模型（--model 用左边的 key）:\n")
    print(f"  {'key':22s} {'体积':>8s}  {'状态':6s} 说明")
    print("  " + "-" * 76)
    for key, (dir_name, _engine, size, desc) in MODELS.items():
        mark = "已下载" if is_ready(key) else "-"
        star = " *" if key == DEFAULT_MODEL else ""
        print(f"  {key:22s} {size:>8s}  {mark:6s} {desc}{star}")
    print(f"\n  默认模型: {DEFAULT_MODEL}（带 * 号）")
    print(f"  模型目录: {MODEL_HOME}")
    print("\n  中文精度: paraformer-zh > sense-voice >> whisper")
    print("  体积/速度: sense-voice-int8 (60MB) 是精度与体积的最佳平衡")
    return 0


def cmd_status(_args) -> int:
    print(f"模型目录: {MODEL_HOME}\n")
    any_ok = False
    for key in MODELS:
        ok = is_ready(key)
        any_ok = any_ok or ok
        print(f"  {'✓' if ok else ' '} {key:22s} {MODELS[key][2]:>8s}  {MODELS[key][3]}")
    print(f"\n  {'✓' if vad_ready() else ' '} silero_vad.onnx (VAD，长音频分段必需)")
    if not any_ok:
        print("\n  尚未下载任何模型。运行: "
              f"python3 {Path(__file__).name} download {DEFAULT_MODEL}")
    return 0


def cmd_download(args) -> int:
    key = args.model
    if key not in MODELS:
        print(f"[FAIL] 未知模型: {key}。用 list 查看可选值", file=sys.stderr)
        return 1

    dir_name = MODELS[key][0]
    if is_ready(key) and not args.force:
        print(f"[OK] {key} 已存在: {model_dir(key)}")
        print("     加 --force 可重新下载")
    else:
        MODEL_HOME.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            tarball = Path(tmp) / f"{dir_name}.tar.bz2"
            print(f"下载 {key} ({MODELS[key][2]}) ...")
            ok = False
            for name, tpl in MIRRORS:
                url = tpl.format(name=dir_name)
                print(f"  尝试源: {name}")
                if _download(url, tarball, "下载中"):
                    print("  解压中...")
                    try:
                        with tarfile.open(tarball, "r:bz2") as tf:
                            tf.extractall(MODEL_HOME)
                        ok = True
                        print(f"  ✓ 已解压到 {model_dir(key)}")
                        break
                    except Exception as e:
                        print(f"  解压失败: {e}")
                        shutil.rmtree(model_dir(key), ignore_errors=True)
            if not ok:
                print(f"\n[FAIL] 所有下载源均失败。可手动下载后解压到 "
                      f"{MODEL_HOME}/{dir_name}/:\n"
                      f"      {MIRRORS[0][1].format(name=dir_name)}", file=sys.stderr)
                return 1

    # VAD 模型（长音频分段需要）
    if not args.no_vad:
        if vad_ready():
            print("[OK] VAD 模型已存在")
        else:
            print("下载 VAD 模型（silero_vad，约 2MB）...")
            MODEL_HOME.mkdir(parents=True, exist_ok=True)
            dest = MODEL_HOME / "silero_vad.onnx"
            done = False
            for label, prefix in [("github", ""), ("ghproxy", "https://ghproxy.com/")]:
                print(f"  尝试源: {label}")
                if _download(prefix + VAD_URL, dest, "VAD"):
                    done = True
                    break
            if not done:
                print("  ⚠️ VAD 下载失败，长音频将退化为固定分段")

    print(f"\n[OK] 完成。使用方式:")
    print(f"     python3 dy_transcribe.py audio.mp3 --engine sherpa --model {key}")
    return 0


def cmd_path(args) -> int:
    key = args.model
    if not is_ready(key):
        print(f"[FAIL] {key} 未下载。先运行: python3 dy_model.py download {key}",
              file=sys.stderr)
        return 1
    d = model_dir(key)
    model_file = sorted(d.glob("model.int8.onnx")) or sorted(d.glob("model*.onnx"))
    if not model_file:
        print(f"[FAIL] {d} 下未找到 model.onnx", file=sys.stderr)
        return 1
    print(f"{model_file[0]}\t{d / 'tokens.txt'}\t{MODELS[key][1]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="sherpa-onnx 中文模型管理")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="列出可用模型").set_defaults(func=cmd_list)
    sub.add_parser("status", help="查看已下载模型").set_defaults(func=cmd_status)
    d = sub.add_parser("download", help="下载模型")
    d.add_argument("model", nargs="?", default=DEFAULT_MODEL)
    d.add_argument("--force", action="store_true", help="已存在也重新下载")
    d.add_argument("--no-vad", action="store_true", help="不下载 VAD 模型")
    d.set_defaults(func=cmd_download)
    p = sub.add_parser("path", help="打印模型路径（供 transcribe 调用）")
    p.add_argument("model", nargs="?", default=DEFAULT_MODEL)
    p.set_defaults(func=cmd_path)
    return ap.parse_args().func(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
