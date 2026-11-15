#!/usr/bin/env python3
"""合并两类 cookie，构造能通过抖音 web detail JSON 风控的 Netscape 文件：

1) 登录态会话 cookie（sessionid / sid_tt / sid_guard 等）—— 从 Chrome Default 配置
   经 browser_cookie3 读取（用户已登录抖音）。
2) 反爬动态 token（msToken / __ac_nonce / s_v_web_id / ttwid 等）—— 由真实浏览器
   加载视频页后 JS 生成，短生命周期，必须现取现用。

合并后写入 ~/.douyin2md/cookies_merged.txt 供 yt-dlp 使用。
"""
import sys
from pathlib import Path

OUT = Path.home() / ".douyin2md" / "cookies_merged.txt"
DEFAULT_CF = Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies"
URL = "https://www.douyin.com/video/7653031071289773355"


def netscape_line(c):
    domain = c.get("domain") or ""
    if not domain:
        return None
    flag = "TRUE" if domain.startswith(".") else "FALSE"
    secure = "TRUE" if c.get("secure") else "FALSE"
    exp = int(c.get("expires") or 0)
    if exp == -1:
        exp = 0
    return f"{domain}\t{flag}\t{c.get('path') or '/'}\t{secure}\t{exp}\t{c.get('name')}\t{c.get('value') or ''}"


def from_browser_cookie3():
    import browser_cookie3 as bc
    cj = bc.chrome(cookie_file=str(DEFAULT_CF))
    out = {}
    for c in cj:
        out[(c.domain or "", c.name)] = {
            "domain": c.domain, "name": c.name, "value": c.value,
            "path": c.path, "secure": c.secure, "expires": c.expires,
        }
    return out


def from_playwright():
    from playwright.sync_api import sync_playwright
    import time, re
    collected = {}
    ms_token = {"v": None}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(Path.home() / ".douyin2md" / "ms-profile"),
            headless=True, channel="chrome",
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--proxy-server=direct://", "--proxy-bypass-list=*"],
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            viewport={"width": 1440, "height": 900}, locale="zh-CN",
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        def on_request(route):
            pass
        def capture(req):
            u = req.url
            m = re.search(r"[?&]msToken=([^&]+)", u)
            if m and not ms_token["v"]:
                ms_token["v"] = m.group(1)
        ctx.on("request", capture)

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        # 轮询等待 msToken（动态 token 由风控 JS 注入，可作为 query 也可作 cookie）
        for _ in range(20):
            for c in ctx.cookies():
                if c["name"] == "msToken" and c.get("value"):
                    ms_token["v"] = c["value"]
            if ms_token["v"]:
                break
            page.wait_for_timeout(1500)
        # 若仅出现在请求 query 中，则手动注入为 cookie，供 yt-dlp 读取
        if ms_token["v"] and not any(c["name"] == "msToken" for c in ctx.cookies()):
            try:
                ctx.add_cookies([{
                    "name": "msToken", "value": ms_token["v"],
                    "domain": ".douyin.com", "path": "/", "secure": True,
                }])
            except Exception as e:
                print("     add_cookies msToken 失败:", e)
        # 全量收集浏览器此刻的 cookie
        for c in ctx.cookies():
            collected[(c.get("domain"), c["name"])] = c
        ctx.close()
    print(f"     捕获 msToken: {'YES' if ms_token['v'] else 'NO'}")
    return collected


def main():
    print("[1/2] 读取 Chrome Default 登录态 cookie ...")
    logged = from_browser_cookie3()
    print(f"     登录态 cookie: {len(logged)} 条 (含 sessionid={('' ,'sessionid') in logged or (False)})")
    sid = any(k[1] == "sessionid" for k in logged)
    print(f"     sessionid 存在: {sid}")

    print("[2/2] 浏览器加载视频页取动态 msToken ...")
    fresh = from_playwright()
    fresh_keys = sorted({k[1] for k in fresh})
    print(f"     浏览器 cookie: {len(fresh)} 条, 关键: {[k for k in ('msToken','__ac_nonce','s_v_web_id','ttwid') if k in fresh_keys]}")

    merged = dict(logged)
    merged.update(fresh)  # 浏览器动态 token 覆盖同名项
    lines = ["# Netscape HTTP Cookie File", "# merged: logged-in session + fresh msToken"]
    n = 0
    for c in merged.values():
        line = netscape_line(c)
        if line:
            lines.append(line)
            n += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n已写出 {n} 条合并 cookie -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
