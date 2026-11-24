#!/usr/bin/env python3
"""微信视频号预览页：只读元数据适配器。

严格只做「元数据 + 高清封面」，**不承诺、也不尝试下载视频流**。
平台在预览端不下发任何播放地址（实测 2026-11-19），因此产物状态恒为
``metadata_only``；需要逐字稿时，请由用户在微信客户端保存视频/录屏，
再走 ``transcribe`` -> ``to-md``（该链路与来源完全解耦）。

实现要点（与 docs/troubleshooting.md 的踩坑记录一致）：
- 短链 ``https://weixin.qq.com/sph/<id>`` 的落地页是 ``finder-preview/pages/sph``
  的 SPA 空壳，静态 HTML 无内容；**HEAD 返回 405**，不要用 HEAD 探活。
- 接口 ``/finder-preview/api/feed/get_feed_info`` 带页面上下文校验：
  裸 HTTP 直连返回 ``permission verification failed``，必须用真实浏览器
  渲染后**拦截响应**（请求方法以实际拦截到的为准，不硬编码 GET/POST）。
- 微信 UA 与桌面 UA 的 HTTP 响应体相同，差异在前端 JS 分支；这里固定用
  桌面 Chrome UA，避免 ``WeixinJSBridge`` 分支短路。
- ``coverUrl`` 末尾的 ``wxampicformat=503&picformat=200`` 是缩图参数，去掉后
  可取到高清封面（实测 540x720 -> 1080x1440）。

用法:
    python3 wx_fetch.py "https://weixin.qq.com/sph/AiQ59Q9O3y" -o ./out
    python3 wx_fetch.py "分享文案..." -o ./out --cover-dir ./notes

stdout 只输出一份 meta JSON（供 dy.py 读取），诊断信息一律走 stderr。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from wx_ocr import NOTE as OCR_NOTE, ocr_image  # noqa: E402
from douyin2md.sources import (  # noqa: E402
    EXTRACTION_METADATA_ONLY,
    EXTRACTION_NEED_LOGIN,
    STATUS_NEED_LOGIN,
    WEIXIN_CHANNELS,
    detect_source,
    extract_url,
)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
SHORT_LINK_RE = re.compile(r"weixin\.qq\.com/sph/([A-Za-z0-9_-]+)")
HD_STRIP_PARAMS = {"wxampicformat", "picformat"}
STREAM_KEYS = (
    "videoUrl", "h264", "h265", "playUrl", "play_addr",
    "mediaUrl", "streamUrl", "url_list",
)
CLIENT_ONLY_HINTS = ("扫码前往微信观看", "暂时无法播放", "微信版本较低")
MISSING_FIELDS = ["video_stream", "asr", "subtitles", "timestamps"]


def preview_url_of(text: str) -> tuple[str, str]:
    """返回 (落地页 URL, 内容 ID)。短链按平台固定规则还原，不依赖网络。"""
    url = extract_url(text)
    m = SHORT_LINK_RE.search(url)
    if m:
        sid = m.group(1)
        return f"https://channels.weixin.qq.com/finder-preview/pages/sph?id={sid}", sid
    parts = urlsplit(url)
    if "channels.weixin.qq.com" in (parts.hostname or ""):
        sid = dict(parse_qsl(parts.query)).get("id") or ""
        return url, sid
    raise ValueError("不是可识别的微信视频号链接")


def hd_cover_url(url: str) -> str:
    """去掉封面 URL 的缩图参数，保留其余查询串（含可能的有效期签名）。"""
    if not url:
        return ""
    parts = urlsplit(url)
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k not in HD_STRIP_PARAMS]
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(kept), parts.fragment))


def scan_stream_fields(payload: dict) -> list:
    """全字段扫描，返回出现过的视频流字段名（大小写敏感按平台实际字段）。"""
    raw = json.dumps(payload, ensure_ascii=False)
    return [k for k in STREAM_KEYS if k in raw]


def capture(preview_url: str, timeout_ms: int) -> tuple[dict, str]:
    """用真实浏览器渲染落地页并拦截 get_feed_info 响应，返回 (响应体, 页面文本)。

    单独请求该接口会被 ``permission verification failed`` 拒绝，因此这里不提供
    裸 HTTP 捷径；playwright 缺失时给出结构化状态而非 traceback。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - 取决于运行环境
        raise RuntimeError(
            f"[{STATUS_NEED_LOGIN}] 缺少 playwright，无法渲染视频号预览页；"
            "请 `pip3 install playwright` 并确保本机装有 Google Chrome"
        ) from exc

    hits = []

    def on_response(resp):
        if "/api/" in resp.url and "feed" in resp.url:
            try:
                body = resp.json()
            except Exception:
                return
            if isinstance(body, dict) and isinstance((body.get("data") or {}), dict):
                hits.append(body)

    text = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            ctx = browser.new_context(user_agent=UA,
                                      viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            page.on("response", on_response)
            page.goto(preview_url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_timeout(1500)
            try:
                text = " ".join(page.inner_text("body").split())
            except Exception:
                text = ""
        finally:
            browser.close()

    usable = [h for h in hits if (h.get("data") or {}).get("feedInfo")]
    if not usable:
        raise RuntimeError(
            f"[{STATUS_NEED_LOGIN}] 未捕获到有效的 get_feed_info 响应；"
            "可能是内容不可访问、需要登录态，或页面结构已变更"
        )
    return usable[0], text


def _ts_to_date(value) -> str:
    try:
        return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError, OverflowError):
        return "-"


def build_meta(payload: dict, text: str, short_link: str,
               preview_url: str, source_id: str) -> dict:
    """把平台响应压成下游统一的 meta 契约（字段与 dy_fetch.slim 尽量对齐）。"""
    data = payload.get("data") or {}
    feed = data.get("feedInfo") or {}
    author = data.get("authorInfo") or {}
    scene = data.get("sceneInfo") or {}

    desc = (feed.get("description") or "").strip()
    cover = (feed.get("coverUrl") or "").strip()
    if not desc and not cover:
        raise RuntimeError(
            f"[{STATUS_NEED_LOGIN}] get_feed_info 未下发 feedInfo 内容；"
            "内容可能已删除、设为私密或需要登录态"
        )

    streams = scan_stream_fields(payload)
    hint = next((h for h in CLIENT_ONLY_HINTS if h in text), "")
    evidence = [
        "get_feed_info 完整响应扫描未发现视频流字段"
        + (f"（检测字段：{', '.join(STREAM_KEYS)}）" if not streams else ""),
        "预览页按平台设计仅提供元数据与封面，本适配器未尝试下载视频流",
    ]
    if streams:
        evidence.append(f"接口出现流字段名 {', '.join(streams)}，本适配器仍不下载")
    if hint:
        evidence.append(f"页面渲染提示「{hint}」")
    if scene.get("expiredTime"):
        evidence.append("sceneInfo 含 expiredTime，dynamicExportId 为动态时效值，不可复用")
    evidence.append(
        "互动数据按接口原始字段名映射（likeCountFmt→点赞等）；"
        "页面图标顺序与字段命名存在对应歧义，不做二次推断"
    )

    first = re.split(r"[。！？\n]", desc, maxsplit=1)[0].strip()
    head = first[:30].strip().rstrip("“\"‘'（(,，、")
    title = (head + "…") if len(first) > 30 else (first or "微信视频号内容")
    if title == desc:
        title = f"{title}（元数据摘要）"

    return {
        "source": WEIXIN_CHANNELS,
        "source_id": source_id or "weixin",
        "webpage_url": short_link,
        "resolved_url": preview_url,
        "title": title,
        "desc": desc,
        "author": author.get("nickname") or "-",
        "upload_date": _ts_to_date(feed.get("createtime")),
        "duration_sec": None,
        "duration_text": None,
        "view_count": None,
        "like_count": feed.get("likeCountFmt"),
        "comment_count": feed.get("commentCountFmt"),
        "save_count": feed.get("favCountFmt"),
        "repost_count": feed.get("forwardCountFmt"),
        "thumbnail": hd_cover_url(cover),
        "cover_url": hd_cover_url(cover),
        "cover_local": None,
        "tags": [],
        "extractor": "weixin-channels-preview",
        "extraction_status": EXTRACTION_METADATA_ONLY,
        "playability": "client_only" if hint or not streams else "unknown",
        "missing": list(MISSING_FIELDS),
        "evidence": evidence,
        "audio_path": None,
    }


def download_cover(url: str, path: Path) -> bool:
    """下载高清封面；失败只影响附件，不影响元数据产物。"""
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Referer": "https://channels.weixin.qq.com/"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            blob = resp.read()
        if not blob:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="微信视频号预览页只读元数据提取")
    ap.add_argument("url", help="视频号短链/落地页链接，或含链接的分享文案")
    ap.add_argument("-o", "--output", default="./douyin_out", help="工作目录")
    ap.add_argument("--cover-dir", default=None, help="封面输出目录（默认同 --output）")
    ap.add_argument("--timeout", type=int, default=45, help="浏览器超时秒数")
    ap.add_argument("--no-cover", action="store_true", help="不下载封面")
    ap.add_argument("--ocr", action="store_true",
                    help="对高清封面做本地 OCR（可选；结果须人工核对，不冒充转写）")
    ap.add_argument("--ocr-backend", default="auto",
                    choices=["auto", "macos-vision", "tesseract", "none"])
    ap.add_argument("--ocr-min-confidence", type=float, default=0.8,
                    help="低于该置信度的 OCR 行标记为低置信度")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    if detect_source(args.url) != WEIXIN_CHANNELS:
        print("[unsupported_source] 仅接受微信视频号预览链接", file=sys.stderr)
        return 2

    try:
        short_link = extract_url(args.url)
        preview_url, source_id = preview_url_of(args.url)
    except ValueError as exc:
        print(f"[unsupported_source] {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(f"[1/2] 渲染预览页: {preview_url}", file=sys.stderr)
    try:
        payload, text = capture(preview_url, args.timeout * 1000)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # 浏览器启动/网络异常
        print(f"[FAIL] [{EXTRACTION_NEED_LOGIN}] 浏览器渲染失败: {exc}", file=sys.stderr)
        return 2

    try:
        meta = build_meta(payload, text, short_link, preview_url, source_id)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    cover_local = None
    if not args.no_cover:
        cover_dir = Path(args.cover_dir or args.output).expanduser()
        cover_path = cover_dir / f"{meta['source_id']}_封面.jpg"
        if download_cover(meta["cover_url"], cover_path):
            meta["cover_local"] = str(cover_path)
            cover_local = cover_path
            if not args.quiet:
                print(f"[2/2] 高清封面: {cover_path}", file=sys.stderr)
        else:
            meta["evidence"].append("高清封面下载失败，仅保留封面 URL")
            if not args.quiet:
                print("[2/2] 封面下载失败，仅保留 URL", file=sys.stderr)

    if args.ocr:
        result = ocr_image(cover_local, args.ocr_backend, args.ocr_min_confidence)
        meta["cover_ocr"] = result
        if result["available"]:
            meta["evidence"].append(
                f"高清封面本地 OCR（{result['backend']}）识别到 {len(result['lines'])} 行文字，"
                f"其中 {len(result['low_confidence'])} 行低置信度；{OCR_NOTE}")
            if not args.quiet:
                print(f"[P2] 封面 OCR: {len(result['lines'])} 行"
                      f"（{len(result['low_confidence'])} 行低置信度，须人工核对）",
                      file=sys.stderr)
        else:
            meta["evidence"].append(f"封面 OCR 不可用：{result['reason']}")
            if not args.quiet:
                print(f"[P2] 封面 OCR 不可用：{result['reason']}", file=sys.stderr)

    json.dump(meta, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
