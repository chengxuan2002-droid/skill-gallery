#!/usr/bin/env python3
"""把音频/视频转成带时间戳的文字稿。

单文档与批量两种模式，模型只加载一次、批量时跨文件复用：

  单文档:  python3 dy_transcribe.py a.mp3                    # JSON 打印到 stdout
           python3 dy_transcribe.py a.mp3 -o transcript.json
  批量:    python3 dy_transcribe.py ./视频目录/ -o ./结果/    # 目录下所有音视频
           # 模型加载一次后循环处理，每文件输出 <文件名>.json，单文件失败不中断

引擎（--engine，默认 auto 自动挑选）：
  sherpa      本地中文引擎，离线、最快、体积最小（默认，需先 dy_model.py download）
  siliconflow 硅基流动云端 SenseVoiceSmall（需 SILICONFLOW_API_KEY）
  openai      OpenAI 兼容云端接口（需 OPENAI_API_KEY）
  local       sherpa 的兼容别名（历史上指 faster-whisper，现已统一为 sherpa 本地引擎）

auto 决策：已下载 sherpa 模型 -> sherpa；否则有云端 Key -> 云端；否则报错指引。

注意：本项目已移除 faster-whisper 依赖（需 torch、1.5GB+）。--engine local 与
旧的 whisper 档位（tiny/base/small/medium/large）会自动映射到 sherpa 本地模型。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SILICONFLOW_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"
SILICONFLOW_MODEL = "FunAudioLLM/SenseVoiceSmall"
OPENAI_URL = "https://api.openai.com/v1/audio/transcriptions"

CLOUD_MAX_BYTES = 48 * 1024 * 1024  # 云端单次上传上限，超过则切片
SEGMENT_SECONDS = 540               # 9 分钟一段

# 本地批处理支持的音/视频扩展名
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".opus",
              ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".ts", ".webm", ".wma"}

SRC_DIR = Path(__file__).resolve().parent


def _add_src_to_path():
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))


# --------------------------------------------------------------------------
# 工具
# --------------------------------------------------------------------------

def probe_duration(path: str) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, check=True)
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def to_wav_16k(src: str, dst: str) -> None:
    """转成 16kHz 单声道 wav（sherpa-onnx 要求）。"""
    subprocess.run(
        ["ffmpeg", "-v", "quiet", "-i", src, "-ar", "16000", "-ac", "1",
         "-f", "wav", "-y", dst], check=True)


def split_audio(path: str, tmpdir: str, seconds: int = SEGMENT_SECONDS) -> list:
    dur = probe_duration(path)
    if dur <= 0 or dur <= seconds:
        return [(path, 0.0)]
    parts, idx, start = [], 0, 0.0
    while start < dur:
        out = os.path.join(tmpdir, f"part_{idx:03d}.mp3")
        subprocess.run(
            ["ffmpeg", "-v", "quiet", "-i", path, "-ss", str(start),
             "-t", str(seconds), "-acodec", "libmp3lame", "-q:a", "0", "-y", out],
            check=True)
        parts.append((out, start))
        start += seconds
        idx += 1
    return parts


def collect_files(input_path: Path) -> list:
    """单文件 -> [文件]；目录 -> 递归收集音视频并排序。"""
    if input_path.is_dir():
        files = sorted(
            p for p in input_path.rglob("*")
            if p.suffix.lower() in AUDIO_EXTS and not p.name.startswith("."))
        return files
    return [input_path]


# --------------------------------------------------------------------------
# 引擎加载（模型只加载一次，供单条与批量共用）
# --------------------------------------------------------------------------

# 旧的 faster-whisper 档位，收到后自动映射到 sherpa 本地模型
LEGACY_WHISPER_SIZES = {"tiny", "base", "small", "medium", "large",
                        "tiny.en", "base.en", "small.en", "medium.en",
                        "large-v1", "large-v2", "large-v3", "turbo"}


def normalize_engine(args) -> str:
    """归一化引擎名与模型名，保持对旧 faster-whisper 用法的向后兼容。

    - --engine local  ->  sherpa（本地轻量引擎）
    - --model small / medium 等 whisper 档位  ->   sherpa 默认模型
    """
    engine = args.engine
    if engine == "local":
        print("  [提示] --engine local 已指向 sherpa 本地引擎"
              "（faster-whisper 已移除）", file=sys.stderr)
        engine = "sherpa"
    if engine == "sherpa" and args.model in LEGACY_WHISPER_SIZES:
        print(f"  [提示] whisper 档位 '{args.model}' 不受支持，"
              f"改用 sherpa 默认模型 {_default_model()}", file=sys.stderr)
        args.model = None
    return engine


def _default_model() -> str:
    _add_src_to_path()
    import dy_model
    return dy_model.DEFAULT_MODEL


def resolve_engine(args, api_key: str) -> str:
    """auto 决策 + 返回最终 engine 名。没有任何可用引擎时给出指引并退出。"""
    engine = normalize_engine(args)
    if engine != "auto":
        return engine
    _add_src_to_path()
    import dy_model
    preferred = args.model if args.model in dy_model.MODELS else dy_model.DEFAULT_MODEL
    if dy_model.is_ready(preferred):
        return "sherpa"
    if api_key:
        return "siliconflow"
    print(
        "[FAIL] 未配置任何转写引擎。请任选其一：\n"
        "  1) 下载本地中文模型（推荐，约 60MB，离线、最快）:\n"
        "     python3 dy_model.py download\n"
        "  2) 或设置云端 API Key:\n"
        "     export SILICONFLOW_API_KEY=\"sk-xxx\"", file=sys.stderr)
    raise SystemExit(1)


def load_engine(engine: str, args, api_key: str):
    """按引擎加载模型/配置。本地引擎的句柄会在批处理中复用。"""
    if engine == "sherpa":
        return _load_sherpa(args)
    if engine == "local":
        # resolve_engine 已归一化，走到这里说明被直接调用，同样按 sherpa 处理
        return _load_sherpa(args)
    # cloud 类：无本地模型，句柄只存配置
    if engine == "siliconflow":
        if not api_key:
            print("[FAIL] 缺少 API Key。设置 SILICONFLOW_API_KEY，或改用 --engine sherpa",
                  file=sys.stderr)
            raise SystemExit(1)
        handle = {"kind": "cloud", "api_base": args.api_base or SILICONFLOW_URL,
                  "model": args.model or SILICONFLOW_MODEL}
        handle["api_key"] = api_key
        return handle
    if engine == "openai":
        if not api_key:
            print("[FAIL] 缺少 API Key。设置 OPENAI_API_KEY 或传 --api-key",
                  file=sys.stderr)
            raise SystemExit(1)
        handle = {"kind": "cloud", "api_base": args.api_base or OPENAI_URL,
                  "model": args.model or "whisper-1"}
        handle["api_key"] = api_key
        return handle
    raise SystemExit(f"[FAIL] 未知引擎: {engine}")


def _load_sherpa(args):
    _add_src_to_path()
    import dy_model

    if args.model and args.model not in dy_model.MODELS:
        raise SystemExit(
            f"[FAIL] 模型 '{args.model}' 不是 sherpa 引擎支持的模型。\n"
            f"       可选: {', '.join(dy_model.MODELS)}\n"
            f"       下载: python3 dy_model.py download <key>\n"
            f"       提示: tiny/base/small/medium 等 whisper 档位已不再支持，"
            f"会自动改用 {dy_model.DEFAULT_MODEL}")
    key = args.model or dy_model.DEFAULT_MODEL
    if not dy_model.is_ready(key):
        raise SystemExit(
            f"[FAIL] 模型 '{key}' 尚未下载。请先执行:\n"
            f"       python3 dy_model.py download {key}")

    try:
        import sherpa_onnx
    except ImportError:
        raise SystemExit(
            "[FAIL] 未安装 sherpa-onnx。请执行:\n"
            "       pip3 install sherpa-onnx numpy\n"
            "       python3 dy_model.py download sense-voice-int8")

    mdir = dy_model.model_dir(key)
    engine_type = dy_model.MODELS[key][1]
    model_files = sorted(mdir.glob("model.int8.onnx")) or sorted(mdir.glob("model*.onnx"))
    if not model_files:
        raise SystemExit(f"[FAIL] {mdir} 下未找到 model*.onnx，请重新下载模型")
    model_file, tokens_file = model_files[0], mdir / "tokens.txt"

    kwargs = {"num_threads": os.cpu_count() or 2}
    if args.provider:
        kwargs["provider"] = args.provider
    elif sys.platform == "darwin":
        kwargs["provider"] = "coreml"  # Apple Silicon 神经网络引擎

    def _make():
        if engine_type == "sense_voice":
            return sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=str(model_file), tokens=str(tokens_file),
                use_itn=True, language=args.language or "auto", **kwargs)
        if engine_type == "paraformer":
            return sherpa_onnx.OfflineRecognizer.from_paraformer(
                paraformer=str(model_file), tokens=str(tokens_file), **kwargs)
        if engine_type == "zipformer_ctc":
            return sherpa_onnx.OfflineRecognizer.from_zipformer_ctc(
                model=str(model_file), tokens=str(tokens_file), **kwargs)
        raise SystemExit(f"[FAIL] 不支持的模型类型: {engine_type}")

    rec = None
    try:
        rec = _make()
    except Exception as e:
        if kwargs.get("provider") == "coreml":
            print("  CoreML 初始化失败，回退 CPU:", str(e)[:100], file=sys.stderr)
            kwargs["provider"] = "cpu"
            rec = _make()
        else:
            raise
    if rec is None:
        raise SystemExit("[FAIL] 模型初始化失败")

    vad_file = dy_model.MODEL_HOME / "silero_vad.onnx"
    return {"kind": "sherpa", "key": key, "engine_type": engine_type,
            "rec": rec, "vad_file": str(vad_file) if vad_file.is_file() else None,
            "vad_cached": {}}


# --------------------------------------------------------------------------
# 单文件识别（批量时循环调用同一 handle）
# --------------------------------------------------------------------------

def transcribe_one(engine: str, handle: dict, path: str, tmpdir: str,
                   language: str) -> dict:
    if engine in ("sherpa", "local"):
        return _transcribe_sherpa_file(handle, path, tmpdir, language)
    return transcribe_cloud(path, handle["api_base"], handle["api_key"],
                            handle["model"], language, tmpdir)


def _transcribe_sherpa_file(handle: dict, path: str, tmpdir: str,
                            language: str) -> dict:
    import wave

    import numpy as np
    import sherpa_onnx

    # 转 16k 单声道 wav 并读取
    wav = os.path.join(tmpdir, f"sherpa_{abs(hash(path)) & 0xffffff:06x}.wav")
    to_wav_16k(path, wav)
    with wave.open(wav, "rb") as wf:
        sr = wf.getframerate()
        samples = np.frombuffer(wf.readframes(wf.getnframes()),
                                dtype=np.int16).astype(np.float32) / 32768.0

    rec = handle["rec"]
    segments = []

    if handle.get("vad_file"):
        cfg = sherpa_onnx.VadModelConfig()
        cfg.silero_vad.model = handle["vad_file"]
        cfg.silero_vad.threshold = 0.5
        cfg.silero_vad.min_silence_duration = 0.25
        cfg.silero_vad.min_speech_duration = 0.25
        cfg.silero_vad.max_speech_duration = 25  # 单段上限，防过长短句截断
        cfg.sample_rate = sr
        vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=100)
        vad.accept_waveform(samples)
        vad.flush()
        while not vad.empty:
            seg = vad.front
            start_sec = seg.start / sr
            buf = np.array(seg.samples, dtype=np.float32)
            stream = rec.create_stream()
            stream.accept_waveform(sr, buf)
            rec.decode_stream(stream)
            text = (stream.result.text or "").strip()
            if text:
                segments.append({
                    "start": round(start_sec, 2),
                    "end": round(start_sec + len(seg.samples) / sr, 2),
                    "text": text})
            vad.pop()
    else:
        # 无 VAD：固定 20 秒切片兜底
        win = sr * 20
        for i in range(0, len(samples), win):
            buf = samples[i:i + win]
            stream = rec.create_stream()
            stream.accept_waveform(sr, buf)
            rec.decode_stream(stream)
            text = (stream.result.text or "").strip()
            if text:
                segments.append({"start": round(i / sr, 2),
                                 "end": round((i + len(buf)) / sr, 2),
                                 "text": text})

    return {"text": "\n".join(s["text"] for s in segments),
            "segments": segments,
            "engine": f"sherpa:{handle['key']}",
            "language": language}


def transcribe_cloud(path: str, api_base: str, api_key: str, model: str,
                     language: str, tmpdir: str) -> dict:
    import urllib.request
    import uuid

    segments = []
    parts = split_audio(path, tmpdir) if os.path.getsize(path) > CLOUD_MAX_BYTES \
        else [(path, 0.0)]
    for part, offset in parts:
        boundary = f"----douyin2md{uuid.uuid4().hex}"
        with open(part, "rb") as f:
            audio = f.read()
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += (f'Content-Disposition: form-data; name="file"; '
                 f'filename="{os.path.basename(part)}"\r\n').encode()
        body += b"Content-Type: audio/mpeg\r\n\r\n"
        body += audio
        body += f"\r\n--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="model"\r\n\r\n{model}\r\n'.encode()
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            api_base, data=body,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (data.get("text") or "").strip()
        if text:
            segments.append({"start": offset, "end": None, "text": text})

    return {"text": "\n".join(s["text"] for s in segments),
            "segments": segments,
            "engine": f"cloud:{model}",
            "language": language}


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="音频/视频转文字（支持单文件与目录批量）")
    ap.add_argument("audio",
                    help="音频/视频文件路径，或目录（目录=批量处理其中所有音视频）")
    ap.add_argument("-o", "--output",
                    help="单文件: 结果 JSON 路径（默认 stdout）；批量: 输出目录（默认 输入目录/transcripts）")
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "sherpa", "siliconflow", "openai", "local"],
                    help="转写引擎。local 为 sherpa 的兼容别名（faster-whisper 已移除）")
    ap.add_argument("--model",
                    help="模型：sherpa 引擎用 dy_model.py list 的 key（默认 "
                         "sense-voice-int8）；openai 引擎用 whisper-1")
    ap.add_argument("--language", default="zh", help="语言代码，中文用 zh")
    ap.add_argument("--device", default="auto",
                    help="已废弃：保留仅为兼容旧命令行，sherpa 引擎不使用该参数")
    ap.add_argument("--provider", default="",
                    help="sherpa 执行提供方: 空=macOS 自动 coreml/其他 cpu；coreml/cpu/cuda")
    ap.add_argument("--api-base", help="OpenAI 兼容接口地址")
    ap.add_argument("--api-key", help="API Key，也可用 SILICONFLOW_API_KEY / OPENAI_API_KEY")
    args = ap.parse_args()

    input_path = Path(args.audio).expanduser()
    if not input_path.exists():
        print(f"[FAIL] 路径不存在: {input_path}", file=sys.stderr)
        return 1

    files = collect_files(input_path)
    if not files:
        print(f"[FAIL] {input_path} 下没有找到音/视频文件", file=sys.stderr)
        return 1

    batch = input_path.is_dir() or len(files) > 1
    api_key = args.api_key or os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")

    engine = resolve_engine(args, api_key)
    if not args.output and not batch:
        # 单文件 stdout 模式不需要 handle 复用的提示
        pass

    print(f"[模式] {'批量' if batch else '单文件'}  {len(files)} 个文件  引擎={engine}",
          file=sys.stderr)

    # 加载模型（只一次）
    handle = load_engine(engine, args, api_key)

    ok_n, fail_n = 0, 0
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, f in enumerate(files, 1):
            try:
                result = transcribe_one(engine, handle, str(f), tmpdir, args.language)
                results.append((f, result))
                ok_n += 1
                n = len(result.get("text") or "")
                print(f"  [{i}/{len(files)}] ✓ {f.name}  "
                      f"({n}字, {len(result.get('segments') or [])}段)",
                      file=sys.stderr)
            except Exception as e:
                fail_n += 1
                print(f"  [{i}/{len(files)}] ✗ {f.name}: {str(e)[:150]}", file=sys.stderr)

    if batch:
        out_dir = Path(args.output).expanduser() if args.output \
            else (input_path / "transcripts")
        out_dir.mkdir(parents=True, exist_ok=True)
        for f, result in results:
            target = out_dir / f"{f.stem}.json"
            target.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                              encoding="utf-8")
        print(f"[完成] 成功 {ok_n} / 失败 {fail_n}，JSON 输出到 {out_dir}",
              file=sys.stderr)
        if not results and fail_n:
            return 1
    else:
        result = results[0][1]
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[OK] 已写入 {args.output}", file=sys.stderr)
        else:
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
    return 0 if fail_n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
