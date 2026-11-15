#!/usr/bin/env python3
"""获取抖音视频的元数据与音频。

链路：分享文案/短链/长链 -> aweme_id -> yt-dlp(+cookie) -> 元数据 JSON + 音频文件

为什么不自己请求 aweme/detail 接口：实测（2026-09）抖音对该接口启用了 Argus
风控，裸请求返回 "Blocked by ArgusSecurityPlugin Uifid Not Found"，带匿名 cookie
则返回 200 + 空 body。yt-dlp 的 DouyinIE 由社区持续跟进签名与风控，复用它比自己
维护解析逻辑稳得多。

用法:
    python3 dy_fetch.py "https://v.douyin.com/xxxx/" -o ./out
    python3 dy_fetch.py "7.43 xxx:/ 复制打开抖音 https://v.douyin.com/xxx/" -o ./out
    python3 dy_fetch.py "https://www.douyin.com/video/123" --cookies-from-browser chrome
    python3 dy_fetch.py "链接" --no-audio        # 只要元数据
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_COOKIES = Path.home() / ".douyin2md" / "cookies.txt"

# 实测踩到的错误 -> 修复动作。这部分是本 skill 的核心价值。
DIAGNOSIS = [
    ("Fresh cookies", "抖音风控拦截。运行 `python3 dy_cookie.py` 登录并导出 cookie，"
                      "再用 --cookies 指定，或 --cookies-from-browser chrome"),
    ("ArgusSecurity", "请求缺少风控签名。必须使用浏览器 cookie，裸 HTTP 已不可用"),
    ("Sign not match|invalid signature|a_bogus", "签名参数失效，更新 yt-dlp: pip3 install -U yt-dlp"),
    ("Unable to download JSON|Failed to download web detail", "接口返回异常，多为 cookie 过期，请重新导出 cookie"),
    ("Video unavailable|视频不存在|已删除", "视频已被作者删除或设为私密，无法获取"),
    ("Unsupported URL", "链接格式不支持。支持 v.douyin.com 短链、www.douyin.com/video/<id>、含链接的分享文案"),
    ("HTTP Error 403", "被限流。等待一段时间，或换用登录态 cookie"),
    ("network|timed out|Connection", "网络问题。检查网络/代理后重试"),
]


def diagnose(stderr: str) -> str:
    for pattern, advice in DIAGNOSIS:
        if re.search(pattern, stderr, re.I):
            return advice
    return "未知错误。运行 `yt-dlp -v <链接>` 查看详细日志"


def normalize_input(text: str) -> str:
    """从一段分享文案里提取抖音链接。"""
    text = text.strip()
    m = re.search(r"https?://[^\s\u4e00-\u9fff]+", text)
    if not m:
        raise ValueError(f"未在输入中找到链接: {text[:50]!r}")
    url = m.group(0).rstrip(".,;)）】")
    return url


def extract_aweme_id(url: str):
    m = re.search(r"/video/(\d+)", url)
    if m:
        return m.group(1)
    m = re.search(r"modal_id=(\d+)", url)
    if m:
        return m.group(1)
    return None


def build_cmd(url: str, out_dir: Path, cookies, from_browser, audio: bool, quiet: bool) -> list:
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-warnings",
        "--no-playlist",
        "--write-info-json",
        "--no-color",
    ]
    if audio:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    else:
        cmd += ["--skip-download"]

    cmd += ["-o", str(out_dir / "%(id)s" / "%(id)s.%(ext)s")]

    if cookies:
        cmd += ["--cookies", str(cookies)]
    elif from_browser:
        cmd += ["--cookies-from-browser", from_browser]
    elif DEFAULT_COOKIES.exists():
        cmd += ["--cookies", str(DEFAULT_COOKIES)]

    if quiet:
        cmd.append("--quiet")
    cmd.append(url)
    return cmd


def pick_meta(out_dir: Path, aweme_id):
    """从 yt-dlp 写出的 info.json 中挑出目标视频的元数据。"""
    if aweme_id:
        direct = out_dir / aweme_id / f"{aweme_id}.info.json"
        if direct.exists():
            return json.loads(direct.read_text(encoding="utf-8"))
    files = sorted(out_dir.glob("*/*.info.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    return json.loads(files[0].read_text(encoding="utf-8"))


def slim(info: dict, url: str) -> dict:
    """压缩成下游好用的结构，避免把几百个字段全丢给 agent。"""
    duration = info.get("duration")
    return {
        "aweme_id": info.get("id"),
        "title": (info.get("title") or info.get("description") or "").strip(),
        "desc": (info.get("description") or "").strip(),
        "author": info.get("uploader") or info.get("channel"),
        "author_id": info.get("uploader_id"),
        "author_url": info.get("uploader_url") or info.get("channel_url"),
        "duration_sec": duration,
        "duration_text": f"{int(duration // 60):02d}:{int(duration % 60):02d}" if duration else None,
        "upload_date": info.get("upload_date"),
        "timestamp": info.get("timestamp"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "repost_count": info.get("repost_count"),
        "save_count": info.get("save_count"),
        "thumbnail": info.get("thumbnail"),
        "tags": info.get("tags") or [],
        "webpage_url": info.get("webpage_url") or url,
        "extractor": info.get("extractor"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="获取抖音视频元数据与音频")
    ap.add_argument("url", help="抖音链接或含链接的分享文案")
    ap.add_argument("-o", "--output", default="./douyin_out", help="输出目录")
    ap.add_argument("--cookies", help="Netscape cookie 文件路径")
    ap.add_argument("--cookies-from-browser", help="从浏览器读取 cookie，如 chrome / safari / edge")
    ap.add_argument("--no-audio", action="store_true", help="只取元数据，不下载音频")
    ap.add_argument("-q", "--quiet", action="store_true")
    ap.add_argument("--raw", action="store_true", help="输出 yt-dlp 原始 JSON 而非精简结构")
    args = ap.parse_args()

    try:
        url = normalize_input(args.url)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    out_dir = Path(args.output).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    aweme_id = extract_aweme_id(url)
    cmd = build_cmd(url, out_dir, args.cookies, args.cookies_from_browser,
                    audio=not args.no_audio, quiet=args.quiet)

    if not args.quiet:
        print(f"[1/2] 解析并下载: {url}", file=sys.stderr)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or "") + (proc.stdout or "")
        print(f"[FAIL] 获取失败\n{err.strip()[:800]}", file=sys.stderr)
        print(f"\n💡 诊断建议: {diagnose(err)}", file=sys.stderr)
        return 1

    info = pick_meta(out_dir, aweme_id)
    if not info:
        print("[FAIL] 未找到 yt-dlp 输出的 info.json", file=sys.stderr)
        return 1

    vid = info.get("id") or aweme_id
    audio_path = out_dir / str(vid) / f"{vid}.mp3" if not args.no_audio else None
    result = info if args.raw else slim(info, url)
    if not args.raw:
        result["audio_path"] = str(audio_path) if audio_path and audio_path.exists() else None

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
