#!/usr/bin/env python3
"""一键流水线：抖音链接 -> Markdown 文稿。

单条与批量两种模式（自动/显式）：
  单条:   python3 dy.py "https://v.douyin.com/xxxx/" -o ./notes
          python3 dy.py "分享文案..." -o ./notes --engine sherpa
  批量:   python3 dy.py --links-file urls.txt -o ./notes
          # urls.txt 每行一个抖音链接或整段分享文案，逐条处理互不中断

批量时先全部下载音频到一个目录，再统一交给转写脚本（本地模型只加载一次），
避免每个视频重复加载模型。

内部依次调用 dy_fetch.py -> dy_transcribe.py -> dy_tomd.py，
中间产物保存在 <输出目录>/.artifacts/。
"""

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd, desc, quiet=False) -> subprocess.CompletedProcess:
    if not quiet:
        print(f"\n▶ {desc}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True)


def extract_links(url_or_file, links_file) -> list:
    """收集要处理的链接（去空、去重、保序）。传入链接或整个分享文案均可。"""
    raw = []
    if url_or_file:
        u = url_or_file.strip()
        if u:
            raw.append(u)
    if links_file:
        p = Path(links_file).expanduser()
        if not p.is_file():
            print(f"[FAIL] 链接文件不存在: {p}", file=sys.stderr)
            sys.exit(1)
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw.append(line)
    links, seen = [], set()
    for u in raw:
        if u not in seen:
            seen.add(u)
            links.append(u)
    if not links:
        print("[FAIL] 没有要处理的链接。传入链接或使用 --links-file 指定文件",
              file=sys.stderr)
        sys.exit(1)
    return links


def fetch_one(url: str, work: Path, args, quiet: bool):
    """下载单个视频的元数据+音频，返回 (meta, audio_path)。失败返回 None。"""
    cmd = [sys.executable, str(HERE / "dy_fetch.py"), url, "-o", str(work)]
    if args.cookies:
        cmd += ["--cookies", args.cookies]
    if args.cookies_from_browser:
        cmd += ["--cookies-from-browser", args.cookies_from_browser]
    if quiet:
        cmd.append("-q")
    p = run(cmd, f"解析: {url[:60]}", quiet)
    if p.returncode != 0:
        print(f"  ✗ 获取失败: {(p.stderr or p.stdout).strip()[-300:]}", file=sys.stderr)
        return None
    try:
        meta = json.loads(p.stdout)
    except json.JSONDecodeError:
        print(f"  ✗ 解析元数据失败: {(p.stdout or '')[:200]}", file=sys.stderr)
        return None
    audio = Path(meta.get("audio_path") or "").expanduser()
    return meta, audio if audio.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description="抖音链接一键转 Markdown（单条/批量）")
    ap.add_argument("url", nargs="?", help="抖音链接或含链接的分享文案（单条模式）")
    ap.add_argument("--links-file", help="批量模式：每行一个抖音链接/分享文案的文件")
    ap.add_argument("-o", "--output-dir", default="./notes", help="Markdown 输出目录")
    ap.add_argument("--cookies", help="Netscape cookie 文件路径")
    ap.add_argument("--cookies-from-browser", help="从浏览器读取 cookie: chrome/safari/edge")
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "sherpa", "siliconflow", "openai", "local"])
    ap.add_argument("--model", help="ASR 模型名（sherpa: sense-voice-int8 等；local: small/medium）")
    ap.add_argument("--language", default="zh")
    ap.add_argument("--device", default="auto", help="本地推理设备: auto/cpu/cuda")
    ap.add_argument("--provider", default="",
                    help="sherpa 引擎执行提供方（默认 macOS 用 coreml，其余 cpu）")
    ap.add_argument("--no-timestamps", action="store_true")
    ap.add_argument("--no-frontmatter", action="store_true")
    ap.add_argument("--keep-audio", action="store_true", help="保留音频文件")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    links = extract_links(args.url, args.links_file)
    batch = len(links) > 1
    if not args.quiet:
        print(f"[模式] {'批量' if batch else '单条'}  {len(links)} 个链接", file=sys.stderr)

    out_dir = Path(args.output_dir).expanduser()
    work = out_dir / ".artifacts"
    work.mkdir(parents=True, exist_ok=True)

    # ---- 1) 逐条获取元数据与音频 ----
    staging = work / "audio_batch"
    if batch:
        staging.mkdir(parents=True, exist_ok=True)
    metas, audio_map, failed = [], {}, []
    for i, link in enumerate(links, 1):
        print(f"\n[{i}/{len(links)}] 处理: {link[:70]}", file=sys.stderr)
        got = fetch_one(link, work, args, args.quiet)
        if not got:
            failed.append(link)
            continue
        meta, audio = got
        vid = str(meta.get("aweme_id"))
        meta_path = work / f"{vid}.meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        metas.append(meta)
        if audio and batch:
            # 集中到一个目录，便于后续批量转写时只加载一次模型
            shutil.copy2(audio, staging / f"{vid}.mp3")
            audio_map[vid] = str(audio)

    if not metas:
        print(f"\n[FAIL] 所有链接都获取失败（{len(failed)} 个）", file=sys.stderr)
        return 1

    # ---- 2) 转写：批量时把音频集中到目录、只调一次转写脚本（模型只加载一次）；
    #          单条时直接转写该音频 ----
    tr_dir = work / "transcripts"
    tr_dir.mkdir(parents=True, exist_ok=True)
    if audio_map:
        tr_cmd = [sys.executable, str(HERE / "dy_transcribe.py")]
        if batch:
            tr_cmd += [str(staging), "-o", str(tr_dir)]
        else:
            vid0 = next(iter(audio_map))
            tr_cmd += [audio_map[vid0], "-o", str(tr_dir / f"{vid0}.json")]
        tr_cmd += ["--engine", args.engine, "--language", args.language,
                   "--device", args.device]
        if args.model:
            tr_cmd += ["--model", args.model]
        if args.provider:
            tr_cmd += ["--provider", args.provider]
        p = run(tr_cmd, "语音转写" + ("（批量，模型只加载一次）" if batch else ""),
                args.quiet)
        if p.returncode != 0:
            print(f"  ⚠️ 转写失败/未完成: {(p.stderr or p.stdout or '').strip()[-400:]}",
                  file=sys.stderr)

    # ---- 3) 逐条生成 Markdown ----
    md_ok = 0
    for idx, meta in enumerate(metas, 1):
        vid = str(meta.get("aweme_id"))
        meta_path = work / f"{vid}.meta.json"
        tr_path = tr_dir / f"{vid}.json"
        md_cmd = [sys.executable, str(HERE / "dy_tomd.py"),
                  "--meta", str(meta_path), "-o", str(out_dir)]
        if tr_path.exists():
            md_cmd += ["--transcript", str(tr_path)]
        if batch:
            prefix = f"{idx:02d}-"
            md_cmd += ["--filename",
                       prefix + (meta.get("author") or "") + "-" + (meta.get("title") or "")]
        if args.no_timestamps:
            md_cmd.append("--no-timestamps")
        if args.no_frontmatter:
            md_cmd.append("--no-frontmatter")
        p = run(md_cmd, f"生成 Markdown ({idx}/{len(metas)})", args.quiet)
        if p.returncode == 0:
            md_ok += 1
            if not args.quiet:
                print(f"  ✓ {p.stdout.strip()}", file=sys.stderr)
        else:
            print(f"  ✗ {vid} Markdown 生成失败: {(p.stderr or '')[:300]}", file=sys.stderr)

    # ---- 4) 清理音频（除非 --keep-audio） ----
    if not args.keep_audio:
        for src in audio_map.values():
            try:
                Path(src).unlink()
            except OSError:
                pass
        if batch:
            shutil.rmtree(staging, ignore_errors=True)

    if not args.quiet:
        print(f"\n🎉 完成: Markdown {md_ok}/{len(metas)} 篇，输出到 {out_dir}",
              file=sys.stderr)
        if failed:
            print(f"   失败 {len(failed)} 条（见上方日志），如需重试请单独处理。",
                  file=sys.stderr)
    return 0 if failed == [] and md_ok == len(metas) else 1


if __name__ == "__main__":
    sys.exit(main())
