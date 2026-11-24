#!/usr/bin/env python3
"""微信视频号「带会话字段差异验证」（P2-2，可选工具，**默认绝不执行**）。

用于验证方案 2.3 节的待验证假设：带登录态后 ``get_feed_info`` 是否额外
下发视频流字段。工具只做**字段名/字段集合差异比对**，不下载视频流、
不伪造签名、不绕过鉴权、不破解客户端校验。

合规前置条件（缺一不可，脚本会强制检查）：
  1. 显式传入 ``--authorize``，表示用户已授权本次验证；
  2. 显式传入 ``--cookies <Netscape 文件>``，会话由用户自行提供；
  3. 内容本身已获授权（由用户确认，工具无法代查）。

报告只包含字段名、字段集合差异与页面提示，**绝不输出 cookie 值**。
若 cookie 文件里没有微信域名，报告会明确标注「仅为链路连通性验证，
不能用于判定平台限制结论」。

用法:
    python3 wx_session_check.py "https://weixin.qq.com/sph/<id>" \
        --cookies /path/to/cookies.txt --authorize --out report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from douyin2md.sources import WEIXIN_CHANNELS, detect_source  # noqa: E402
from wx_fetch import (  # noqa: E402
    CLIENT_ONLY_HINTS, STREAM_KEYS, UA, preview_url_of, scan_stream_fields,
)

COMPLIANCE = ("仅比对字段名与字段集合差异；不输出 cookie 值、不下载视频流、"
              "不伪造客户端签名、不绕过鉴权或 DRM。结果只用于判定平台字段策略。")
REFUSAL = ("[refused] 本工具需要用户显式授权与自行提供的会话。"
           "请加 --authorize 并用 --cookies 指定 Netscape cookie 文件；"
           "同时确认内容已获授权。未授权时不执行任何带会话请求。")


def load_netscape(path: Path) -> list:
    """读取 Netscape cookie 文件为 playwright 可用的字典（值只在内存中使用）。"""
    cookies = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            continue
        domain, _, cpath, secure, exp, name, value = parts
        cookies.append({
            "name": name,
            "value": value,
            "domain": domain.lstrip(".") if domain.startswith(".") else domain,
            "path": cpath,
            "secure": secure == "TRUE",
            "expires": int(exp) if exp.isdigit() and int(exp) else -1,
        })
    return cookies


def cookie_domains(cookies: list) -> list:
    return sorted({str(c.get("domain") or "") for c in cookies if c.get("domain")})


def looks_like_weixin_session(domains: list) -> bool:
    return any(("weixin" in d or "wechat" in d) for d in domains)


def feed_keys(payload: dict) -> list:
    return sorted(((payload.get("data") or {}).get("feedInfo") or {}).keys())


def hint_of(text: str) -> str:
    return next((h for h in CLIENT_ONLY_HINTS if h in (text or "")), "")


def build_report(before: dict, before_text: str, after: dict, after_text: str,
                 cookie_info: dict) -> dict:
    """纯函数：把两次拦截结果压成可复核的差异报告（离线可测）。"""
    kb, ka = feed_keys(before), feed_keys(after)
    sb, sa = scan_stream_fields(before), scan_stream_fields(after)
    new_keys = sorted(set(ka) - set(kb))
    new_streams = sorted(set(sa) - set(sb))
    hb, ha = hint_of(before_text), hint_of(after_text)

    if not (kb and ka):
        conclusion = ("至少一次未取得有效 feedInfo，无法比对字段差异；"
                      "结论保持「未验证」，不推断平台策略。")
    elif new_streams:
        conclusion = ("带会话后新增视频流字段，会话可能参与下发判定；"
                      "本工具不下载，请人工评估授权边界后再决定下一步。")
    else:
        conclusion = ("带会话后仍未出现视频流字段，支持「平台侧客户端能力限制」结论；"
                      "页面扫码提示与客户端版本门槛不受 cookie 影响。")

    warnings = ["动态字段 dynamicExportId 有时效，报告不记录其取值"]
    if not cookie_info.get("session_looks_like_weixin"):
        warnings.append("cookie 中未发现微信域名：本次仅为链路连通性验证，"
                        "不能用于判定 2.3 假设")
    if hb or ha:
        warnings.append("页面渲染提示属于前端文案，非接口字段，单独列出")

    return {
        "tool": "wx_session_check",
        "verified_hypothesis": "2.3 带登录态是否额外下发视频流字段",
        "authorized_by_user": True,
        "compliance": COMPLIANCE,
        "cookie_file": cookie_info.get("cookie_file"),
        "cookie_count": cookie_info.get("cookie_count", 0),
        "cookie_domains": cookie_info.get("cookie_domains", []),
        "session_looks_like_weixin": cookie_info.get("session_looks_like_weixin", False),
        "redacted": True,
        "before": {"feed_keys": kb, "stream_fields": sb, "page_hint": hb,
                   "has_feed_info": bool(kb)},
        "after": {"feed_keys": ka, "stream_fields": sa, "page_hint": ha,
                  "has_feed_info": bool(ka)},
        "new_keys": new_keys,
        "new_stream_fields": new_streams,
        "checked_stream_keys": list(STREAM_KEYS),
        "conclusion": conclusion,
        "warnings": warnings,
    }


def capture_once(preview_url: str, cookies: list, timeout_ms: int) -> tuple[dict, str]:
    """渲染预览页并拦截 get_feed_info；playwright 缺失时给出结构化错误。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - 取决于运行环境
        raise RuntimeError("缺少 playwright；请 pip3 install playwright 并确保装有 Chrome") from exc

    hits = []

    def on_response(resp):
        if "/api/" in resp.url and "feed" in resp.url:
            try:
                body = resp.json()
            except Exception:
                return
            if isinstance(body, dict):
                hits.append(body)

    text = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            ctx = browser.new_context(user_agent=UA,
                                      viewport={"width": 1280, "height": 900})
            if cookies:
                try:
                    ctx.add_cookies(cookies)
                except Exception as exc:
                    raise RuntimeError(f"注入会话失败：{exc}") from exc
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

    usable = [h for h in hits if ((h.get("data") or {}).get("feedInfo"))]
    return (usable[0] if usable else {}), text


def main() -> int:
    ap = argparse.ArgumentParser(description="视频号带会话字段差异验证（可选、需授权）")
    ap.add_argument("url", help="视频号短链或预览页链接")
    ap.add_argument("--cookies", required=True, help="用户自行提供的 Netscape cookie 文件")
    ap.add_argument("--authorize", action="store_true",
                    help="显式确认：已获内容授权，并授权本次带会话验证")
    ap.add_argument("--out", help="报告输出路径（默认打印到 stdout）")
    ap.add_argument("--timeout", type=int, default=45, help="浏览器超时秒数")
    args = ap.parse_args()

    if not args.authorize:
        print(REFUSAL, file=sys.stderr)
        return 2
    cookie_path = Path(args.cookies).expanduser()
    if not cookie_path.is_file():
        print(f"[refused] cookie 文件不存在: {cookie_path}", file=sys.stderr)
        return 2
    if detect_source(args.url) != WEIXIN_CHANNELS:
        print("[refused] 仅接受微信视频号链接", file=sys.stderr)
        return 2
    try:
        preview_url, _ = preview_url_of(args.url)
    except ValueError as exc:
        print(f"[refused] {exc}", file=sys.stderr)
        return 2

    cookies = load_netscape(cookie_path)
    domains = cookie_domains(cookies)
    info = {
        "cookie_file": cookie_path.name,     # 只留文件名，不留路径与值
        "cookie_count": len(cookies),
        "cookie_domains": domains,
        "session_looks_like_weixin": looks_like_weixin_session(domains),
    }

    try:
        before, before_text = capture_once(preview_url, [], args.timeout * 1000)
        after, after_text = capture_once(preview_url, cookies, args.timeout * 1000)
    except Exception as exc:
        print(f"[FAIL] 浏览器渲染/拦截失败: {exc}", file=sys.stderr)
        return 1

    report = build_report(before, before_text, after, after_text, info)
    report["preview_url"] = preview_url
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"[OK] 报告已写入 {out}", file=sys.stderr)
    else:
        print(payload)
    return 0 if report["before"]["has_feed_info"] and report["after"]["has_feed_info"] else 1


if __name__ == "__main__":
    sys.exit(main())
