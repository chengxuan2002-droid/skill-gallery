#!/usr/bin/env python3
"""用真实浏览器加载抖音视频页，拦截 aweme/detail 响应，直接拿到元数据与字幕，
并下载视频（含音频）到本地。绕开 yt-dlp 对 a_bogus 签名的依赖。

用法:
  python3 dy_browser_capture.py <视频长链或短链> [-o 输出目录] [--name 文件前缀]
  python3 dy_browser_capture.py https://www.douyin.com/video/7653031071289773355 \
      -o /path/to/.artifacts_adv --name adv
  python3 dy_browser_capture.py <长链> --no-download   # 只保存 detail.json

说明:
  - 传短链会自动解析出 aweme_id 并拼成长链（解析需绕过本机 MITM 代理：env -u http_proxy ...）
  - cookie 默认读 ~/.douyin2md/cookies_merged.txt（由 dy_cookie_merge_msToken.py 生成）

输出:
  <out>/<aweme_id>.detail.json   原始 detail JSON（含 desc、video、subtitle 等）
  <out>/<name>.mp4               视频文件
"""
import os, sys, re, json, argparse, subprocess, shutil, importlib, tempfile
from pathlib import Path

REQUIRED = ("playwright",)          # 本脚本硬依赖
NEXT_STAGE = ("sherpa_onnx",)       # 后续 dy_transcribe.py 转写所需


def _probe(py: str, mods) -> bool:
    try:
        r = subprocess.run(
            [py, "-c", "import " + ", ".join(mods)],
            capture_output=True, timeout=90,
        )
        return r.returncode == 0
    except Exception:
        return False


def _candidates():
    """按可能性排序列出候选解释器（去重、只保留存在且可执行的）。"""
    home = Path.home()
    cands = [
        sys.executable,
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        "/usr/bin/python3",
        shutil.which("python3"),
        shutil.which("python"),
    ]
    # 托管版本目录：versions/*/bin/python3（新版本优先）、envs/*/bin/python
    base = home / ".workbuddy" / "binaries" / "python"
    if base.exists():
        vers = sorted((base / "versions").glob("*/bin/python3"), reverse=True) if (base / "versions").exists() else []
        envs = sorted((base / "envs").glob("*/bin/python")) if (base / "envs").exists() else []
        # 优先尝试同时具备 playwright + sherpa 的托管版本
        both = [str(p) for p in vers if _probe(str(p), REQUIRED + NEXT_STAGE)]
        cands = both + cands
        cands += [str(p) for p in vers if str(p) not in both]
        cands += [str(p) for p in envs]

    seen, out = set(), []
    for c in cands:
        if not c:
            continue
        try:
            rp = os.path.realpath(c)
        except Exception:
            continue
        if rp in seen or not os.path.exists(c) or not os.access(c, os.X_OK):
            continue
        seen.add(rp)
        out.append(c)
    return out


def ensure_interpreter():
    """缺 playwright 时自动切换到装了它的解释器重跑；缺 sherpa 时提示转写该用哪个。"""
    def has(mods):
        try:
            for m in mods:
                importlib.import_module(m)
            return True
        except Exception:
            return False

    if not has(REQUIRED):
        if os.environ.get("DOUYIN2MD_REEXEC"):
            raise SystemExit(
                "已重试仍未找到带 playwright 的解释器。\n"
                "请手动安装：pip3 install playwright && playwright install chrome"
            )
        for py in _candidates():
            if py == os.path.realpath(sys.executable):
                continue
            if _probe(py, REQUIRED):
                print(f"[env] 当前解释器缺 {'/'.join(REQUIRED)}，自动切换到 {py}", flush=True)
                os.environ["DOUYIN2MD_REEXEC"] = "1"
                os.execv(py, [py] + sys.argv)
        raise SystemExit(
            f"未找到带 {'/'.join(REQUIRED)} 的解释器。\n"
            "请安装：pip3 install playwright && playwright install chrome"
        )

    if not has(NEXT_STAGE):
        for py in _candidates():
            if _probe(py, NEXT_STAGE):
                print(f"[env] 注意：本解释器缺 {'/'.join(NEXT_STAGE)}，"
                      f"后续转写请用：{py} dy_transcribe.py <mp4> -o <输出>.json")
                break
        else:
            print(f"[env] 注意：未找到带 {'/'.join(NEXT_STAGE)} 的解释器，后续转写可能失败。")

MERGED = Path.home() / ".douyin2md" / "cookies_merged.txt"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def resolve_long_url(url: str) -> str:
    """短链 -> https://www.douyin.com/video/<aweme_id>（需绕过本机代理才能拿到重定向）"""
    m = re.search(r"/video/(\d+)", url)
    if m:
        return f"https://www.douyin.com/video/{m.group(1)}"
    env = {k: v for k, v in __import__("os").environ.items()
           if k.lower() not in ("http_proxy", "https_proxy", "all_proxy")}
    r = subprocess.run(["curl", "-sI", url], capture_output=True, text=True, env=env)
    loc = ""
    for line in (r.stdout or "").splitlines():
        if line.lower().startswith("location:"):
            loc = line.split(":", 1)[1].strip()
    m = re.search(r"/video/(\d+)", loc)
    if not m:
        raise SystemExit(f"无法从短链解析 aweme_id: {url}\n{loc}")
    return f"https://www.douyin.com/video/{m.group(1)}"


def load_netscape(path):
    cookies = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            continue
        domain, _, path_, secure, exp, name, value = parts
        cookies.append({
            "name": name, "value": value, "domain": domain.lstrip(".") if domain.startswith(".") else domain,
            "path": path_, "secure": secure == "TRUE",
            "expires": int(exp) if exp.isdigit() and int(exp) else -1,
        })
    return cookies


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("-o", "--out", default=str(Path.home() / "Downloads" / "dy_capture"))
    ap.add_argument("--name", default=None, help="输出 mp4 文件名前缀，默认用 aweme_id")
    ap.add_argument("--cookies", default=str(MERGED))
    ap.add_argument("--no-download", action="store_true",
                    help="只拦截并保存 detail.json，不下载 mp4（供 --no-audio 复用）")
    ap.add_argument("--fresh", action="store_true",
                    help="使用全新临时 Chrome 会话且不预置 cookie（游客态，最不易触发验证码中间页）")
    ap.add_argument("--profile-dir", default=None,
                    help="覆盖默认 Chrome 持久化 profile 目录")
    args = ap.parse_args()
    ensure_interpreter()

    URL = resolve_long_url(args.url)
    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"目标: {URL}")

    from playwright.sync_api import sync_playwright
    cookies = [] if args.fresh else load_netscape(args.cookies)
    print(f"加载 {len(cookies)} 条 cookie" + ("（--fresh 游客态）" if args.fresh else ""))

    tmp_profile = None
    if args.fresh:
        tmp_profile = tempfile.mkdtemp(prefix="dy2md-fresh-")
        profile_dir = tmp_profile
    else:
        profile_dir = args.profile_dir or str(Path.home() / ".douyin2md" / "cap-profile")
    Path(profile_dir).mkdir(parents=True, exist_ok=True)

    captured = {"detail": None, "play_url": None}
    ok = False
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=True, channel="chrome",
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            user_agent=UA,
            viewport={"width": 1440, "height": 900}, locale="zh-CN",
        )
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        if cookies:
            try:
                ctx.add_cookies(cookies)
            except Exception as e:
                print("add_cookies 警告:", e)

        def on_response(resp):
            u = resp.url
            if "aweme" in u and ("detail" in u or "play" in u or "feed" in u):
                try:
                    body = resp.json()
                    if "aweme_detail" in body or "awemeDetail" in body:
                        captured["detail"] = body
                        print("  ✓ 捕获 aweme/detail 响应")
                except Exception:
                    pass
        ctx.on("response", on_response)

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)
        title = page.title()
        print(f"  页面标题: {title[:60]!r}")
        if ("验证码" in title or "中间页" in title) and not captured["detail"]:
            print("  [risk] 命中验证码中间页：当前会话已被风控标记，"
                  "建议改用 --fresh（全新游客会话）")
        for _ in range(2):
            try:
                page.click("video", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(5000)

        ok = bool(captured["detail"])
        if captured["detail"]:
            aweme = captured["detail"].get("aweme_detail") or captured["detail"].get("awemeDetail") or {}
            aweme_id = aweme.get("aweme_id", "unknown")
            video = aweme.get("video") or {}
            play = video.get("play_addr") or {}
            urllist = play.get("url_list") or []
            if urllist:
                captured["play_url"] = urllist[0]
            if not captured["play_url"]:
                b = video.get("backup_play_addr") or {}
                if b.get("url_list"):
                    captured["play_url"] = b["url_list"][0]
            print(f"  play_url: {'YES' if captured['play_url'] else 'NO'}")
            detail_path = OUT / f"{aweme_id}.detail.json"
            detail_path.write_text(json.dumps(captured["detail"], ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  已保存 detail -> {detail_path}")
            name = args.name or aweme_id
        else:
            print("  ✗ 未捕获 aweme/detail 响应")
            name = args.name or "unknown"

        ctx.close()

    if args.no_download:
        print("  --no-download: 已跳过视频下载（detail.json 仍已保存）")
    elif captured["play_url"]:
        mp4 = OUT / f"{name}.mp4"
        print("下载视频中 ...")
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-headers", f"Referer: https://www.douyin.com/\r\nUser-Agent: {UA}",
            "-i", captured["play_url"], "-c", "copy", str(mp4),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if mp4.exists() and mp4.stat().st_size > 1000:
            print(f"  ✓ 视频已下载 -> {mp4} ({mp4.stat().st_size//1024} KB)")
        else:
            print("  ✗ 视频下载失败:", (r.stderr or "")[:400])
    else:
        print("  无 play_url，跳过下载")

    if tmp_profile:
        shutil.rmtree(tmp_profile, ignore_errors=True)
    if not ok:
        print("  [risk] 未取得 aweme/detail（常见于验证码中间页）；"
              "可加 --fresh 用全新游客会话重试")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
