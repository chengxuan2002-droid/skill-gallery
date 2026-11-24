#!/usr/bin/env python3
"""一键流水线：链接 -> Markdown 文稿。

单条与批量两种模式（自动/显式）：
  单条:   python3 dy.py "https://v.douyin.com/xxxx/" -o ./notes
          python3 dy.py "分享文案..." -o ./notes --engine sherpa
  批量:   python3 dy.py --links-file urls.txt -o ./notes
          # urls.txt 每行一个链接或整段分享文案，逐条处理互不中断

按来源分流（详见 douyin2md/sources.py 与 docs/architecture.md）：
  抖音        -> dy_fetch.py（元数据 + 音频）-> 转写 -> Markdown
  微信视频号  -> wx_fetch.py（只读元数据 + 高清封面）-> Markdown（metadata-only 降级）
  其它        -> unsupported_source，给出可解释提示，不再丢给 yt-dlp

每条成功转写的内容默认产出两个文件：`<前缀>-逐字稿.md`（含附录 A 专名校正对照表、
附录 B 可靠性说明）与 `<前缀>-总结.md`（要点式，逐条带时间节点）。总结由 agent 写标注
JSON 后用 ``to-md --annotations`` 重新渲染；没有转写正文时只产出元数据文稿。
``--single-file`` 保留旧的单篇合并产物。

批量时先全部下载音频到一个目录，再统一交给转写脚本（本地模型只加载一次），
避免每个视频重复加载模型。降级条目没有音频，不参与转写，但照常产出文稿。

内部产物保存在 <输出目录>/.artifacts/。
"""

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from douyin2md.sources import (  # noqa: E402
    ALL_STATUSES,
    DOUYIN,
    STATUS_MEDIA_BLOCKED,
    STATUS_METADATA_ONLY,
    STATUS_NEED_LOGIN,
    STATUS_OK,
    STATUS_UNSUPPORTED,
    WEIXIN_CHANNELS,
    detect_source,
    meta_id,
    source_advice,
    status_advice,
)


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


def classify(meta: dict, audio) -> str:
    """把 meta 契约映射到批量清单的 5 个结果状态。"""
    if meta.get("source") == WEIXIN_CHANNELS:
        if meta.get("extraction_status") == "need_login":
            return STATUS_NEED_LOGIN
        if meta.get("playability") == "client_only":
            return STATUS_MEDIA_BLOCKED
        return STATUS_METADATA_ONLY
    return STATUS_OK


def fetch_one(url: str, work: Path, args, quiet: bool):
    """按来源获取单条内容，返回 (meta, audio_path, status)；失败时 meta 为 None。"""
    source = detect_source(url)

    if source == WEIXIN_CHANNELS:
        cmd = [sys.executable, str(HERE / "wx_fetch.py"), url,
               "-o", str(work), "--cover-dir", str(Path(args.output_dir).expanduser())]
        if getattr(args, "ocr", False):
            cmd.append("--ocr")
            if getattr(args, "ocr_backend", None):
                cmd += ["--ocr-backend", args.ocr_backend]
            if getattr(args, "ocr_min_confidence", None) is not None:
                cmd += ["--ocr-min-confidence", str(args.ocr_min_confidence)]
        label = "视频号只读元数据"
    elif source == DOUYIN:
        cmd = [sys.executable, str(HERE / "dy_fetch.py"), url, "-o", str(work)]
        if args.cookies:
            cmd += ["--cookies", args.cookies]
        if args.cookies_from_browser:
            cmd += ["--cookies-from-browser", args.cookies_from_browser]
        if getattr(args, "no_capture_fallback", False):
            cmd.append("--no-capture-fallback")
        if getattr(args, "force_capture", False):
            cmd.append("--force-capture")
        label = "抖音元数据与音频"
    else:
        print(f"  ✗ [unsupported_source] {source_advice(source)}", file=sys.stderr)
        return None, None, STATUS_UNSUPPORTED

    if quiet:
        cmd.append("-q")
    p = run(cmd, f"{label}: {url[:60]}", quiet)
    if p.returncode != 0:
        err = (p.stderr or p.stdout or "").strip()[-300:]
        print(f"  ✗ 获取失败: {err}", file=sys.stderr)
        status = STATUS_NEED_LOGIN if ("need_login" in err or "playwright" in err) else "failed"
        return None, None, status
    try:
        meta = json.loads(p.stdout)
    except json.JSONDecodeError:
        print(f"  ✗ 解析元数据失败: {(p.stdout or '')[:200]}", file=sys.stderr)
        return None, None, "failed"

    if meta.get("capture_fallback") and not quiet:
        print("  ℹ 抖音直连受风控拦截，已自动由浏览器拦截兜底取得真实媒体",
              file=sys.stderr)

    audio = Path(meta.get("audio_path") or "").expanduser()
    audio = audio if audio.is_file() else None
    return meta, audio, classify(meta, audio)


def main() -> int:
    ap = argparse.ArgumentParser(description="链接一键转 Markdown（单条/批量，自动按来源分流）")
    ap.add_argument("url", nargs="?", help="链接或含链接的分享文案（单条模式）")
    ap.add_argument("--links-file", help="批量模式：每行一个链接/分享文案的文件")
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
    ap.add_argument("--annotations",
                    help="标注 JSON，用于重新渲染单条的逐字稿附录与总结（仅单条模式）")
    ap.add_argument("--single-file", action="store_true",
                    help="旧行为：每条只产出一篇合并文稿（不拆总结、不带附录）")
    ap.add_argument("--ocr", action="store_true", help="视频号高清封面做本地 OCR（可选）")
    ap.add_argument("--ocr-backend", default="auto",
                    choices=["auto", "macos-vision", "tesseract", "none"])
    ap.add_argument("--ocr-min-confidence", type=float, default=0.8)
    ap.add_argument("--no-capture-fallback", action="store_true",
                    help="禁用抖音直连失败时的浏览器拦截自动兜底")
    ap.add_argument("--force-capture", action="store_true",
                    help="抖音跳过 yt-dlp，直接用浏览器拦截（已知直连被风控时用）")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    links = extract_links(args.url, args.links_file)
    batch = len(links) > 1
    if batch and args.annotations:
        print("[FAIL] --annotations 是单条标注，批量模式请逐条用 `to-md --annotations` 重新渲染",
              file=sys.stderr)
        return 2
    if not args.quiet:
        print(f"[模式] {'批量' if batch else '单条'}  {len(links)} 个链接", file=sys.stderr)

    out_dir = Path(args.output_dir).expanduser()
    work = out_dir / ".artifacts"
    work.mkdir(parents=True, exist_ok=True)

    # ---- 1) 逐条获取元数据与音频（按来源分流，单条失败不中断批量） ----
    staging = work / "audio_batch"
    if batch:
        staging.mkdir(parents=True, exist_ok=True)
    metas, audio_map, failed, status_map = [], {}, [], {}
    for i, link in enumerate(links, 1):
        print(f"\n[{i}/{len(links)}] 处理: {link[:70]}", file=sys.stderr)
        meta, audio, status = fetch_one(link, work, args, args.quiet)
        status_map[link] = status
        if meta is None:
            failed.append(link)
            continue
        vid = meta_id(meta)
        meta_path = work / f"{vid}.meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        metas.append(meta)
        if audio:
            # 单条模式也要登记音频，否则不会进入转写阶段（历史缺陷：
            # 旧代码写成 `if audio and batch`，单条链接只产元数据文稿）。
            audio_map[vid] = str(audio)
            if batch:
                # 集中到一个目录，便于后续批量转写时只加载一次模型
                shutil.copy2(audio, staging / f"{vid}.mp3")

    if not metas:
        print(f"\n[FAIL] 所有链接都获取失败（{len(failed)} 个）", file=sys.stderr)
        _print_status_summary(status_map, args.quiet)
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
        vid = meta_id(meta)
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
        if args.annotations:
            md_cmd += ["--annotations", args.annotations]
        if args.single_file:
            md_cmd.append("--single-file")
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
        unit = "篇" if args.single_file else "组（逐字稿+总结）"
        print(f"\n🎉 完成: Markdown {md_ok}/{len(metas)} {unit}，输出到 {out_dir}",
              file=sys.stderr)
        if not args.single_file:
            print("   总结若为 summary_status=pending，需写标注 JSON 后 "
                  "`to-md --annotations` 重新渲染。", file=sys.stderr)
        if failed:
            print(f"   未处理 {len(failed)} 条（见上方日志），如需重试请单独处理。",
                  file=sys.stderr)
    _print_status_summary(status_map, args.quiet)
    return 0 if failed == [] and md_ok == len(metas) else 1


def _print_status_summary(status_map: dict, quiet: bool) -> None:
    """按状态分级输出清单，让降级与失败可区分。"""
    if quiet or not status_map:
        return
    print("\n[状态清单]", file=sys.stderr)
    for status in (*ALL_STATUSES, "failed"):
        items = [link for link, st in status_map.items() if st == status]
        if items:
            label = status_advice(status) if status in ALL_STATUSES else "获取或解析失败"
            print(f"   {status:<28} {len(items):>2} 条  {label}", file=sys.stderr)
            for link in items:
                print(f"      - {link[:70]}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
