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
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from douyin2md.sources import (  # noqa: E402
    DOUYIN, detect_source, extract_url, source_advice,
)

DEFAULT_COOKIES = Path.home() / ".douyin2md" / "cookies.txt"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 实测踩到的错误 -> 修复动作。这部分是本 skill 的核心价值。
DIAGNOSIS = [
    ("Fresh cookies", "抖音 aweme/detail 被 Argus / a_bogus 风控拦截（不一定要求登录）。"
                      "先刷新 cookie 重试；仍失败改用浏览器拦截兜底："
                      "`bash bin/douyin2md capture \"<链接>\" -o ./notes`"),
    ("ArgusSecurity", "请求缺少风控签名。必须使用浏览器 cookie，裸 HTTP 已不可用"),
    ("Sign not match|invalid signature|a_bogus", "签名参数失效：更新 yt-dlp，或改用 `capture` 浏览器拦截兜底"),
    ("SSL: UNEXPECTED_EOF|SSL_ERROR_SYSCALL|Connection reset by peer|Unable to download webpage",
     "TLS/代理层失败，常见于短链跳转目标 www.iesdouyin.com 不可达。"
     "本工具会先把短链解析为 www.douyin.com/video/<id> 再重试；若仍失败请检查代理，或用 `capture` 兜底"),
    ("Unable to download JSON|Failed to download web detail", "接口返回异常，多为 cookie 过期，请重新导出 cookie"),
    ("Video unavailable|视频不存在|已删除", "视频已被作者删除或设为私密，无法获取"),
    ("Unsupported URL|\\[generic\\]", "链接未能被 DouyinIE 识别（多为短链跳转失败）。"
                                     "检查短链解析结果，或直接用 www.douyin.com/video/<id> 长链"),
    ("HTTP Error 403", "被限流。等待一段时间，或换用登录态 cookie"),
    ("network|timed out|Connection", "网络问题。检查网络/代理后重试"),
]


def diagnose(stderr: str) -> str:
    for pattern, advice in DIAGNOSIS:
        if re.search(pattern, stderr, re.I):
            return advice
    return "未知错误。运行 `yt-dlp -v <链接>` 查看详细日志"


def normalize_input(text: str) -> str:
    """从一段分享文案里提取抖音链接（复用统一的 URL 归一化规则）。"""
    text = text.strip()
    try:
        return extract_url(text)
    except ValueError:
        raise ValueError(f"未在输入中找到链接: {text[:50]!r}") from None


def extract_aweme_id(url: str):
    m = re.search(r"/video/(\d+)", url)
    if m:
        return m.group(1)
    m = re.search(r"modal_id=(\d+)", url)
    if m:
        return m.group(1)
    return None


def resolve_short_url(url: str, timeout: int = 15) -> str:
    """短链 -> ``www.douyin.com/video/<id>``，失败则原样返回。

    2026-11-19 真实联网回归发现：yt-dlp 对 ``v.douyin.com/<code>`` 会先访问
    302 目标 ``www.iesdouyin.com/share/...``，该域名在部分网络/代理环境下 TLS
    握手直接失败，退化成 ``[generic]`` 且诊断含糊。这里只读 Location 头部，
    提取 aweme_id 后换成 DouyinIE 能直接识别的长链；任何异常都不改变旧行为。
    """
    if (urlsplit(url).hostname or "").lower() != "v.douyin.com":
        return url
    try:
        proc = subprocess.run(
            ["curl", "-sS", "-D", "-", "-o", "/dev/null", "--max-redirs", "0",
             "--max-time", str(timeout), "-A", UA, url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        loc = ""
        for line in (proc.stdout or "").splitlines():
            if line.lower().startswith("location:"):
                loc = line.split(":", 1)[1].strip()
        m = re.search(r"/video/(\d+)", loc)
        if m:
            return f"https://www.douyin.com/video/{m.group(1)}/"
    except (OSError, subprocess.SubprocessError):
        pass
    return url


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


def slim_from_detail(detail: dict, url: str, audio_path) -> dict:
    """把浏览器拦截的 ``aweme/detail`` 转成与 ``slim()`` 完全一致的字段契约。

    2026-11-20 真实联网回归：yt-dlp 直连被 Argus / a_bogus 拦住，而浏览器渲染
    页面时 ``aweme/detail`` 会正常下发。这里只做字段映射，不改动下游任何逻辑；
    额外的 ``capture_fallback`` 标记用于让文稿/日志能区分两条获取路径。
    """
    aweme = detail.get("aweme_detail") or detail.get("awemeDetail") or {}
    if not aweme:
        return {}
    statistics = aweme.get("statistics") or {}
    author = aweme.get("author") or {}
    video = aweme.get("video") or {}
    desc = (aweme.get("desc") or "").strip()

    duration_ms = video.get("duration") or 0
    duration = round(duration_ms / 1000) if duration_ms else None
    create_time = aweme.get("create_time") or 0
    try:
        upload_date = datetime.fromtimestamp(create_time).strftime("%Y%m%d") if create_time else None
    except (OSError, OverflowError, ValueError):
        upload_date = None

    tags = [t.get("hashtag_name") for t in (aweme.get("text_extra") or [])
            if t.get("hashtag_name")]
    thumbnail = ((video.get("cover") or {}).get("url_list") or [None])[0]
    vid = aweme.get("aweme_id")

    return {
        "aweme_id": vid,
        "title": (desc.split("\n")[0][:60] if desc else None) or vid or "抖音视频",
        "desc": desc,
        "author": author.get("nickname"),
        "author_id": author.get("uid"),
        "author_url": None,          # aweme/detail 不提供主页 URL；保持契约字段齐全
        "duration_sec": duration,
        "duration_text": (f"{duration // 60:02d}:{duration % 60:02d}" if duration else None),
        "upload_date": upload_date,
        "timestamp": create_time or None,
        "view_count": statistics.get("play_count"),
        "like_count": statistics.get("digg_count"),
        "comment_count": statistics.get("comment_count"),
        "repost_count": statistics.get("share_count"),
        "save_count": statistics.get("collect_count"),
        "thumbnail": thumbnail,
        "tags": tags,
        "webpage_url": url,
        "extractor": "browser-capture (aweme/detail)",
        "capture_fallback": True,
        "audio_path": str(audio_path) if audio_path else None,
    }


def capture_fallback(url: str, out_dir: Path, cookies, want_audio: bool,
                     timeout: int = 240):
    """yt-dlp 失败时的浏览器拦截兜底，返回 ``(meta, error)``。

    产物落在 ``<out_dir>/capture/``：``<aweme_id>.detail.json`` 与 ``<aweme_id>.mp4``。
    mp4 直接作为 ``audio_path``（dy_transcribe.py 用 ffmpeg 按内容解码，支持 mp4）。
    ``want_audio=False`` 时传 ``--no-download``，只取元数据不消耗带宽。

    2026-11-20 实测：复用 ``~/.douyin2md/cap-profile`` + 1028 条登录 cookie 会命中
    「验证码中间页」，而全新空 profile 的游客态稳定拿到 ``aweme/detail``。因此
    无人值守默认先走 ``--fresh``，失败再用常规会话互补重试一次；用户显式给了
    cookie 时优先尊重其登录态，再回退 fresh。
    """
    cap_dir = out_dir / "capture"
    cap_dir.mkdir(parents=True, exist_ok=True)
    attempts = ([(False, cookies), (True, None)] if cookies
                else [(True, None), (False, None)])

    last_err = ""
    for idx, (fresh, ck) in enumerate(attempts, 1):
        cmd = [sys.executable, str(HERE / "dy_browser_capture.py"), url,
               "-o", str(cap_dir)]
        if fresh:
            cmd.append("--fresh")
        elif ck:
            cmd += ["--cookies", str(ck)]
        if not want_audio:
            cmd.append("--no-download")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.SubprocessError) as exc:
            last_err = f"浏览器拦截未启动: {exc}"
            continue
        # 把浏览器侧关键诊断透出来，避免失败时只剩一句「未捕获」
        for line in (proc.stdout or "").splitlines():
            if "[risk]" in line or "页面标题" in line or "加载 " in line:
                print(f"  [capture {idx}] {line.strip()}", file=sys.stderr)
        if proc.returncode != 0:
            last_err = (proc.stderr or proc.stdout or "").strip()[-300:]
            continue

        details = sorted(cap_dir.glob("*.detail.json"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
        if not details:
            last_err = "浏览器未捕获 aweme/detail 响应"
            continue
        try:
            detail = json.loads(details[0].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            last_err = f"detail.json 无法解析: {exc}"
            continue
        meta = slim_from_detail(detail, url, None)
        if not meta:
            last_err = "aweme/detail 内容为空"
            continue
        if want_audio:
            mp4 = cap_dir / f"{meta['aweme_id']}.mp4"
            if not (mp4.is_file() and mp4.stat().st_size > 1000):
                last_err = "已取得元数据但未下载到可转写的媒体文件"
                continue
            meta["audio_path"] = str(mp4)
        return meta, ""
    return None, last_err


def _emit(meta: dict) -> int:
    json.dump(meta, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="获取抖音视频元数据与音频")
    ap.add_argument("url", help="抖音链接或含链接的分享文案")
    ap.add_argument("-o", "--output", default="./douyin_out", help="输出目录")
    ap.add_argument("--cookies", help="Netscape cookie 文件路径")
    ap.add_argument("--cookies-from-browser", help="从浏览器读取 cookie，如 chrome / safari / edge")
    ap.add_argument("--no-audio", action="store_true", help="只取元数据，不下载音频")
    ap.add_argument("-q", "--quiet", action="store_true")
    ap.add_argument("--raw", action="store_true", help="输出 yt-dlp 原始 JSON 而非精简结构")
    ap.add_argument("--no-capture-fallback", action="store_true",
                    help="禁用直连失败时的浏览器拦截自动兜底（保持旧行为）")
    ap.add_argument("--force-capture", action="store_true",
                    help="跳过 yt-dlp，直接用浏览器拦截 aweme/detail（已知直连必失败时用）")
    args = ap.parse_args()

    try:
        url = normalize_input(args.url)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    # 独立调用时提前给出可解释提示，不再把非抖音链接丢给 yt-dlp 换一句 Unsupported URL
    source = detect_source(url)
    if source != DOUYIN:
        print(f"[unsupported_source] dy_fetch.py 仅处理抖音链接。{source_advice(source)}",
              file=sys.stderr)
        return 2

    out_dir = Path(args.output).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved = resolve_short_url(url)
    if resolved != url and not args.quiet:
        print(f"[0/2] 短链解析: {url} -> {resolved}", file=sys.stderr)
    url = resolved

    # 已知直连必被风控拦截时，跳过 yt-dlp 那次徒劳请求，直接走浏览器拦截。
    if args.force_capture:
        if not args.quiet:
            print("[1/2] --force-capture: 浏览器拦截 aweme/detail（跳过 yt-dlp）",
                  file=sys.stderr)
        meta, cap_err = capture_fallback(url, out_dir, args.cookies,
                                         want_audio=not args.no_audio)
        if not meta:
            print(f"[FAIL] 浏览器拦截兜底失败: {cap_err}", file=sys.stderr)
            return 1
        if not args.quiet:
            print("[2/2] 已取得真实媒体与元数据（browser-capture）", file=sys.stderr)
        return _emit(meta)

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
        if args.no_capture_fallback:
            return 1
        if not args.quiet:
            print("\n[2/2] 自动切换浏览器拦截兜底（aweme/detail）...", file=sys.stderr)
        meta, cap_err = capture_fallback(url, out_dir, args.cookies,
                                         want_audio=not args.no_audio)
        if not meta:
            print(f"[FAIL] 浏览器拦截兜底也失败: {cap_err}", file=sys.stderr)
            return 1
        if args.raw and not args.quiet:
            print("[提示] 兜底路径输出统一契约，--raw 不适用", file=sys.stderr)
        return _emit(meta)

    info = pick_meta(out_dir, aweme_id)
    if not info:
        print("[FAIL] 未找到 yt-dlp 输出的 info.json", file=sys.stderr)
        if args.no_capture_fallback:
            return 1
        if not args.quiet:
            print("\n[2/2] 自动切换浏览器拦截兜底...", file=sys.stderr)
        meta, cap_err = capture_fallback(url, out_dir, args.cookies,
                                         want_audio=not args.no_audio)
        if not meta:
            print(f"[FAIL] 浏览器拦截兜底也失败: {cap_err}", file=sys.stderr)
            return 1
        return _emit(meta)

    vid = info.get("id") or aweme_id
    audio_path = out_dir / str(vid) / f"{vid}.mp3" if not args.no_audio else None
    result = info if args.raw else slim(info, url)
    if not args.raw:
        result["audio_path"] = str(audio_path) if audio_path and audio_path.exists() else None

    return _emit(result)


if __name__ == "__main__":
    sys.exit(main())
