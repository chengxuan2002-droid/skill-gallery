#!/usr/bin/env python3
"""把元数据 + 转写结果拼成一篇 Markdown。

用法:
    python3 dy_tomd.py --meta meta.json --transcript transcript.json -o ./notes
    python3 dy_tomd.py --meta meta.json -o ./notes          # 只有元数据（未转写）
    python3 dy_tomd.py --meta meta.json --transcript t.json --no-timestamps
    python3 dy_tomd.py --meta meta.json --transcript t.json --stdout

输出文件默认命名为 <作者>-<标题>.md（已清洗非法字符）。
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

UNSAFE = r'[\\/:*?"<>|\r\n\t]'


def safe_name(s: str, limit: int = 60) -> str:
    s = re.sub(UNSAFE, "_", (s or "").strip())
    s = re.sub(r"\s+", " ", s).strip(" .")
    return (s[:limit] or "untitled")


def fmt_ts(sec) -> str:
    try:
        sec = float(sec)
    except (TypeError, ValueError):
        return "00:00"
    m, s = divmod(int(sec), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fmt_count(n):
    if n is None:
        return "-"
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f} 亿"
    if n >= 10_000:
        return f"{n / 10_000:.1f} 万"
    return str(n)


def fmt_date(s):
    if not s:
        return "-"
    s = str(s)
    if re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s


def build(meta: dict, transcript: dict, with_ts: bool = True,
          frontmatter: bool = True, summary: str = "") -> str:
    title = meta.get("title") or meta.get("desc") or "抖音视频"
    author = meta.get("author") or "-"
    url = meta.get("webpage_url") or "-"
    vid = meta.get("aweme_id") or "-"
    dur = meta.get("duration_text") or (fmt_ts(meta.get("duration_sec")) if meta.get("duration_sec") else "-")
    tags = meta.get("tags") or []
    text = (transcript or {}).get("text") or ""
    segments = (transcript or {}).get("segments") or []

    out = []
    if frontmatter:
        out.append("---")
        out.append(f"title: {json.dumps(title, ensure_ascii=False)}")
        out.append(f"author: {json.dumps(author, ensure_ascii=False)}")
        out.append(f"source: {url}")
        out.append(f"aweme_id: \"{vid}\"")
        out.append(f"date: {fmt_date(meta.get('upload_date'))}")
        out.append(f"duration: {dur}")
        out.append(f"type: douyin-transcript")
        out.append(f"transcribed_at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if (transcript or {}).get("engine"):
            out.append(f"asr_engine: {transcript['engine']}")
        if tags:
            out.append("tags:")
            for t in tags[:15]:
                out.append(f"  - {t}")
        out.append("---")
        out.append("")

    out.append(f"# {title}")
    out.append("")

    out.append("| 项目 | 值 |")
    out.append("| --- | --- |")
    out.append(f"| 作者 | {author} |")
    out.append(f"| 视频 ID | `{vid}` |")
    out.append(f"| 时长 | {dur} |")
    out.append(f"| 发布 | {fmt_date(meta.get('upload_date'))} |")
    out.append(f"| 点赞 | {fmt_count(meta.get('like_count'))} |")
    out.append(f"| 评论 | {fmt_count(meta.get('comment_count'))} |")
    out.append(f"| 收藏 | {fmt_count(meta.get('save_count'))} |")
    out.append(f"| 播放 | {fmt_count(meta.get('view_count'))} |")
    out.append(f"| 原链接 | {url} |")
    out.append("")

    if summary:
        out.append("## 摘要")
        out.append("")
        out.append(summary.strip())
        out.append("")

    desc = (meta.get("desc") or "").strip()
    if desc and desc != title:
        out.append("## 视频文案")
        out.append("")
        out.append(desc)
        out.append("")

    if text:
        out.append("## 转写正文")
        out.append("")
        if segments and with_ts and any(s.get("start") is not None for s in segments):
            for seg in segments:
                out.append(f"**[{fmt_ts(seg.get('start'))}]** {seg.get('text','').strip()}")
                out.append("")
        else:
            out.append(text)
            out.append("")

    if tags:
        out.append("## 话题标签")
        out.append("")
        out.append(" ".join(f"#{t}" for t in tags if t))
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"> 本文稿由 douyin2md 自动生成于 "
               f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
               + (f"，转写引擎：{transcript['engine']}" if (transcript or {}).get("engine") else "")
               + "。内容版权归原作者所有。")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 Markdown 文稿")
    ap.add_argument("--meta", required=True, help="dy_fetch.py 输出的元数据 JSON")
    ap.add_argument("--transcript", help="dy_transcribe.py 输出的转写 JSON")
    ap.add_argument("-o", "--output-dir", default="./notes", help="输出目录")
    ap.add_argument("--filename", help="自定义输出文件名（不含扩展名）")
    ap.add_argument("--no-timestamps", action="store_true", help="正文不带时间戳")
    ap.add_argument("--no-frontmatter", action="store_true", help="不加 YAML frontmatter")
    ap.add_argument("--summary", help="追加一段摘要（通常由 agent 生成后传入）")
    ap.add_argument("--stdout", action="store_true", help="打印到标准输出而不写文件")
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    transcript = None
    if args.transcript:
        p = Path(args.transcript)
        transcript = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    md = build(meta, transcript, with_ts=not args.no_timestamps,
               frontmatter=not args.no_frontmatter, summary=args.summary)

    if args.stdout:
        sys.stdout.write(md)
        return 0

    name = args.filename or f"{safe_name(meta.get('author') or '')}-{safe_name(meta.get('title') or '')}"
    name = name.strip("-")
    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.md"
    path.write_text(md, encoding="utf-8")
    print(f"[OK] {path}")
    print(f"     字数: {len(md)}  转写正文: {len((transcript or {}).get('text') or '')} 字")
    return 0


if __name__ == "__main__":
    sys.exit(main())
