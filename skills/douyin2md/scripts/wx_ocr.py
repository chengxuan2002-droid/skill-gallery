#!/usr/bin/env python3
"""可选的封面 OCR 适配器（P2-1）。

设计目标：**可选、本地、优雅降级、绝不冒充转写**。

- 只读取本地封面图片，不联网、不上传、不调用云端 OCR。
- 后端优先级 ``auto`` = macOS Vision（Swift，零额外依赖）→ tesseract → 不可用。
- 任何后端缺失/失败都返回 ``available=false``，调用方照常产出元数据文稿，
  绝不因为 OCR 不可用而中断流水线。
- 输出带置信度；低于阈值（默认 0.8）的行标记 ``low_confidence``。
  实测 macOS Vision 会把「大模型」误识为「大棋型」（置信度 0.5），
  且会漏掉竖排小字（人名），因此产物必须标注「须人工核对」。

用法:
    python3 wx_ocr.py <封面图片> --json
    python3 wx_ocr.py <封面图片> --backend macos-vision --min-confidence 0.8
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NOTE = ("封面文字为本地 OCR 机器识别结果，可能误识或漏掉竖排/艺术字，须人工核对；"
        "不得作为视频口播内容、字幕或时间戳依据。")

VISION_SWIFT = r'''
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1, let img = NSImage(contentsOfFile: args[1]),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("ERR cannot load image")
    exit(3)
}
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
if #available(macOS 11.0, *) {
    req.recognitionLanguages = ["zh-Hans", "en-US"]
    req.automaticallyDetectsLanguage = false
}
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([req])
    for o in (req.results ?? []) {
        if let c = o.topCandidates(1).first {
            print(String(format: "%.3f\t%@", c.confidence, c.string))
        }
    }
} catch {
    print("ERR \(error)")
    exit(4)
}
'''

BACKENDS = ("auto", "macos-vision", "tesseract", "none")


def _unavailable(reason: str, backend=None) -> dict:
    return {
        "available": False,
        "backend": backend,
        "reason": reason,
        "text": "",
        "lines": [],
        "low_confidence": [],
        "note": NOTE,
    }


def _result(backend: str, lines: list, min_confidence: float) -> dict:
    normalized = []
    for text, conf in lines:
        conf = max(0.0, min(1.0, float(conf)))
        normalized.append({
            "text": text,
            "confidence": round(conf, 3),
            "low_confidence": conf < min_confidence,
        })
    low = [l["text"] for l in normalized if l["low_confidence"]]
    return {
        "available": True,
        "backend": backend,
        "text": "\n".join(l["text"] for l in normalized),
        "lines": normalized,
        "low_confidence": low,
        "min_confidence": min_confidence,
        "note": NOTE,
    }


def _parse_vision_output(stdout: str) -> list:
    lines = []
    for raw in stdout.splitlines():
        if "\t" not in raw:
            continue
        conf, text = raw.split("\t", 1)
        try:
            value = float(conf)
        except ValueError:
            continue
        if text.strip():
            lines.append((text.strip(), value))
    return lines


def _run_macos_vision(path: Path, timeout: int = 120) -> list:
    swift = shutil.which("swift")
    if sys.platform != "darwin" or not swift:
        raise RuntimeError("仅 macOS 且装有 swift 时可用")
    with tempfile.TemporaryDirectory(prefix="douyin2md-ocr-") as td:
        helper = Path(td) / "vision_ocr.swift"
        helper.write_text(VISION_SWIFT, encoding="utf-8")
        proc = subprocess.run([swift, str(helper), str(path)],
                              capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "swift 执行失败").strip()[:200])
    return _parse_vision_output(proc.stdout)


def _parse_tesseract_tsv(stdout: str) -> list:
    rows = []
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 12 or not parts[11].strip():
            continue
        try:
            conf = float(parts[10]) / 100.0
        except ValueError:
            continue
        rows.append((parts[11].strip(), conf))
    return rows


def _run_tesseract(path: Path, timeout: int = 120) -> list:
    exe = shutil.which("tesseract")
    if not exe:
        raise RuntimeError("未安装 tesseract")
    proc = subprocess.run([exe, str(path), "stdout", "-l", "chi_sim+eng",
                           "--psm", "11", "tsv"],
                          capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "tesseract 执行失败").strip()[:200])
    return _parse_tesseract_tsv(proc.stdout)


def ocr_image(path, backend: str = "auto", min_confidence: float = 0.8) -> dict:
    """识别封面文字；不可用时返回结构化降级结果，不抛异常。"""
    if backend not in BACKENDS:
        return _unavailable(f"未知 OCR 后端 {backend!r}，可选：{', '.join(BACKENDS)}")
    if backend == "none":
        return _unavailable("调用方显式关闭了 OCR")
    p = Path(path) if path else None
    if not p or not p.is_file():
        return _unavailable("封面图片不存在或尚未下载")

    order = (["macos-vision", "tesseract"] if backend == "auto" else [backend])
    runners = {"macos-vision": _run_macos_vision, "tesseract": _run_tesseract}
    errors = []
    for name in order:
        try:
            lines = runners[name](p)
            if lines:
                return _result(name, lines, min_confidence)
            errors.append(f"{name}: 未识别到文字")
        except Exception as exc:  # 后端缺失/执行失败一律降级
            errors.append(f"{name}: {exc}")
    return _unavailable("; ".join(errors))


def main() -> int:
    ap = argparse.ArgumentParser(description="本地封面 OCR（可选、不联网）")
    ap.add_argument("image", help="封面图片路径")
    ap.add_argument("--backend", default="auto", choices=list(BACKENDS))
    ap.add_argument("--min-confidence", type=float, default=0.8)
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON（默认输出文字）")
    args = ap.parse_args()
    result = ocr_image(args.image, args.backend, args.min_confidence)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["text"])
        if not result["available"]:
            print(f"[WARN] OCR 不可用：{result['reason']}", file=sys.stderr)
    return 0 if result["available"] else 1


if __name__ == "__main__":
    sys.exit(main())
