"""douyin2md 统一命令行入口。

所有 agent 框架只需调用同一个命令::

    bash bin/douyin2md <子命令> [参数]

本文件只负责参数归并、配置注入与转发，不改写 ``scripts/`` 下任何原始脚本。
``bin/douyin2md`` 用自身位置定位仓库根，因此从任意工作目录调用都有效。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .config import ROOT, config_path, load_config, pick, redacted

SCRIPTS = ROOT / "scripts"

OPTIONAL_MODULES = (
    ("yt_dlp", "获取元数据/音频（核心）"),
    ("sherpa_onnx", "本地离线中文转写（可选 local）"),
    ("numpy", "本地转写数值依赖（可选 local）"),
    ("playwright", "浏览器登录 / 拦截兜底（可选 browser）"),
    ("browser_cookie3", "从浏览器读取 cookie（可选 browser）"),
)
SECRET_ENV = ("SILICONFLOW_API_KEY", "OPENAI_API_KEY")


def _exec(argv: list[str]) -> int:
    """把请求转发给 scripts/ 下的原始脚本，保留其退出码。"""
    script = str(SCRIPTS / argv[0])
    if not Path(script).is_file():
        print(f"[FAIL] 缺少脚本: {script}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, script, *argv[1:]]).returncode


def _opt(args: list[str], flag: str, value) -> None:
    if value:
        args.extend([flag, str(value)])


def _pipeline_parent() -> argparse.ArgumentParser:
    """dy.py（url / batch 共用）的参数集合。"""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("-o", "--output-dir", default=None, help="Markdown 输出目录")
    p.add_argument("--engine", default=None, choices=["auto", "sherpa", "siliconflow", "openai", "local"])
    p.add_argument("--model", default=None, help="ASR 模型名")
    p.add_argument("--language", default=None, help="语言代码，中文用 zh")
    p.add_argument("--device", default=None, help="兼容旧参数")
    p.add_argument("--provider", default=None, help="sherpa 执行提供方")
    p.add_argument("--cookies", default=None, help="Netscape cookie 文件路径")
    p.add_argument("--cookies-from-browser", default=None, help="chrome/safari/edge")
    p.add_argument("--no-timestamps", action="store_true", default=None)
    p.add_argument("--no-frontmatter", action="store_true", default=None)
    p.add_argument("--keep-audio", action="store_true", default=None)
    p.add_argument("-q", "--quiet", action="store_true")
    return p


def _pipeline_args(ns, cfg) -> list[str]:
    args = ["-o", str(pick(ns.output_dir, "output_dir", cfg))]
    for flag, key, attr in (
        ("--engine", "engine", "engine"),
        ("--model", "model", "model"),
        ("--language", "language", "language"),
        ("--device", "device", "device"),
        ("--provider", "provider", "provider"),
        ("--cookies", "cookies", "cookies"),
        ("--cookies-from-browser", "cookies_from_browser", "cookies_from_browser"),
    ):
        _opt(args, flag, pick(getattr(ns, attr, None), key, cfg))
    for flag, key, attr in (
        ("--no-timestamps", "no_timestamps", "no_timestamps"),
        ("--no-frontmatter", "no_frontmatter", "no_frontmatter"),
        ("--keep-audio", "keep_audio", "keep_audio"),
    ):
        if pick(getattr(ns, attr, None), key, cfg):
            args.append(flag)
    if getattr(ns, "quiet", False):
        args.append("-q")
    return args


def cmd_url(ns, cfg) -> int:
    return _exec(["dy.py", ns.target, *_pipeline_args(ns, cfg)])


def cmd_batch(ns, cfg) -> int:
    return _exec(["dy.py", "--links-file", ns.links_file, *_pipeline_args(ns, cfg)])


def cmd_transcribe(ns, cfg) -> int:
    args = ["dy_transcribe.py", ns.path]
    _opt(args, "-o", ns.output)
    for flag, key, attr in (
        ("--engine", "engine", "engine"),
        ("--model", "model", "model"),
        ("--language", "language", "language"),
        ("--device", "device", "device"),
        ("--provider", "provider", "provider"),
        ("--api-base", "api_base", "api_base"),
    ):
        _opt(args, flag, pick(getattr(ns, attr, None), key, cfg))
    if ns.api_key:
        args.extend(["--api-key", ns.api_key])
    return _exec(args)


def cmd_tomd(ns, cfg) -> int:
    args = ["dy_tomd.py", "--meta", ns.meta]
    _opt(args, "--transcript", ns.transcript)
    _opt(args, "-o", ns.output_dir or cfg["output_dir"])
    _opt(args, "--filename", ns.filename)
    _opt(args, "--summary", ns.summary)
    if ns.no_timestamps:
        args.append("--no-timestamps")
    if ns.no_frontmatter:
        args.append("--no-frontmatter")
    if ns.stdout:
        args.append("--stdout")
    return _exec(args)


def cmd_capture(ns, cfg) -> int:
    args = ["dy_browser_capture.py", ns.url, "-o", str(ns.out or (Path(cfg["home"]).expanduser() / "capture"))]
    _opt(args, "--name", ns.name)
    _opt(args, "--cookies", ns.cookies or cfg["cookies"])
    return _exec(args)


def cmd_model(ns, cfg) -> int:
    # dy_model.py 只有 download 子命令接受 model / --force / --no-vad，
    # 其余 action 收到这些参数会直接报错，因此不下发。
    args = ["dy_model.py", ns.action]
    if ns.action in {"download", "path"} and ns.model_name:
        args.append(ns.model_name)
    if ns.action == "download":
        if ns.force:
            args.append("--force")
        if ns.no_vad:
            args.append("--no-vad")
    return _exec(args)


def cmd_cookie(ns, cfg) -> int:
    args = ["dy_cookie.py"]
    _opt(args, "--out", ns.out or str(Path(cfg["home"]).expanduser() / "cookies.txt"))
    _opt(args, "--profile", ns.profile)
    _opt(args, "--timeout", ns.timeout)
    if ns.check:
        args.append("--check")
    return _exec(args)


def cmd_doctor(ns, cfg) -> int:
    """只读环境体检：不联网、不安装依赖、不执行 scripts/ 下的脚本。"""
    home = Path(cfg["home"]).expanduser()
    modules = {}
    for name, desc in OPTIONAL_MODULES:
        try:
            found = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            found = False
        modules[name] = {"available": found, "purpose": desc}
    report = {
        "python": sys.version.split()[0],
        "skill_root": str(ROOT),
        "config_file": str(config_path(ns.config)) if config_path(ns.config) else None,
        "home": str(home),
        "home_exists": home.is_dir(),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "cookies_file": str(home / "cookies.txt"),
        "cookies_exists": (home / "cookies.txt").is_file(),
        "models_dir_exists": (home / "models").is_dir(),
        "secrets": {name: "set" if os.environ.get(name) else "not set" for name in SECRET_ENV},
        "modules": modules,
        "missing_core": [name for name in ("yt_dlp",) if not modules[name]["available"]],
    }
    report["status"] = "ok" if not report["missing_core"] and report["ffmpeg"] else "degraded"
    if ns.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"douyin2md {__version__}  doctor  [{report['status']}]")
        print(f"  Python      {report['python']}")
        print(f"  技能根目录  {report['skill_root']}")
        print(f"  生效配置    {report['config_file'] or '内置默认值'}")
        print(f"  ffmpeg      {report['ffmpeg'] or '未找到'}")
        print(f"  cookie      {'已存在' if report['cookies_exists'] else '未生成'}  {report['cookies_file']}")
        print(f"  模型目录    {'已存在' if report['models_dir_exists'] else '未下载'}")
        print("  可选模块:")
        for name, info in modules.items():
            mark = "OK" if info["available"] else "--"
            print(f"    [{mark:2}] {name:<18} {info['purpose']}")
        print("  云端 Key    " + ", ".join(f"{k}={v}" for k, v in report["secrets"].items()))
        if report["missing_core"]:
            print("  提示: 缺少核心依赖，先按 docs/configuration.md 安装。")
    return 0


def cmd_config(ns, cfg) -> int:
    data = redacted(cfg)
    data["config_file"] = str(config_path(ns.config)) if config_path(ns.config) else None
    if ns.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for key, value in data.items():
            print(f"{key:<26} {value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="douyin2md",
        description="抖音视频 / 本地音视频 → Markdown 文稿（统一入口）",
        epilog="所有子命令都可用 --config 指定配置文件；详见 docs/configuration.md",
    )
    ap.add_argument("--version", action="version", version=f"douyin2md {__version__}")
    ap.add_argument("--config", default=None, help="配置文件路径（可放在任意位置）")
    sub = ap.add_subparsers(dest="command", required=True, metavar="<子命令>")

    shared = _pipeline_parent()
    p = sub.add_parser("url", parents=[shared], help="单个抖音链接/分享文案 → Markdown")
    p.add_argument("target", help="链接或含链接的分享文案")
    p.set_defaults(func=cmd_url)

    p = sub.add_parser("batch", parents=[shared], help="批量链接文件 → 每篇一个 Markdown")
    p.add_argument("links_file", help="每行一个链接/分享文案的文件")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("transcribe", help="本地音视频文件/目录 → 转写 JSON（无需 cookie）")
    p.add_argument("path", help="文件或目录")
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--engine", default=None, choices=["auto", "sherpa", "siliconflow", "openai", "local"])
    p.add_argument("--model", default=None)
    p.add_argument("--language", default=None)
    p.add_argument("--device", default=None)
    p.add_argument("--provider", default=None)
    p.add_argument("--api-base", default=None)
    p.add_argument("--api-key", default=None, help="建议改用环境变量，避免出现在进程列表")
    p.set_defaults(func=cmd_transcribe)

    p = sub.add_parser("to-md", help="元数据 JSON + 转写 JSON → Markdown")
    p.add_argument("--meta", required=True)
    p.add_argument("--transcript", default=None)
    p.add_argument("-o", "--output-dir", default=None)
    p.add_argument("--filename", default=None)
    p.add_argument("--summary", default=None)
    p.add_argument("--no-timestamps", action="store_true")
    p.add_argument("--no-frontmatter", action="store_true")
    p.add_argument("--stdout", action="store_true")
    p.set_defaults(func=cmd_tomd)

    p = sub.add_parser("capture", help="风控兜底：浏览器拦截 detail 响应并下载 mp4")
    p.add_argument("url")
    p.add_argument("-o", "--out", default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--cookies", default=None)
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("model", help="本地 ASR 模型管理: list/status/download/path")
    p.add_argument("action", choices=["list", "status", "download", "path"])
    p.add_argument("model_name", nargs="?", default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-vad", action="store_true")
    p.set_defaults(func=cmd_model)

    p = sub.add_parser("cookie", help="浏览器登录并导出 cookie")
    p.add_argument("--check", action="store_true")
    p.add_argument("--out", default=None)
    p.add_argument("--profile", default=None)
    p.add_argument("--timeout", type=int, default=None)
    p.set_defaults(func=cmd_cookie)

    p = sub.add_parser("doctor", help="只读环境体检（不联网、不安装）")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("config", help="打印生效配置（密钥仅显示 set/not set）")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_config)
    return ap


def main(argv=None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    # 允许 --config 出现在子命令之后
    explicit = None
    cleaned: list[str] = []
    index = 0
    while index < len(raw):
        token = raw[index]
        if token == "--config" and index + 1 < len(raw):
            explicit = raw[index + 1]
            index += 2
            continue
        if token.startswith("--config="):
            explicit = token.split("=", 1)[1]
            index += 1
            continue
        cleaned.append(token)
        index += 1

    ap = build_parser()
    ns = ap.parse_args(cleaned)
    explicit = explicit or ns.config
    try:
        cfg = load_config(explicit)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    ns.config = explicit
    return int(ns.func(ns, cfg) or 0)
