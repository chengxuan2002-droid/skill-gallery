#!/usr/bin/env python3
"""把元数据 + 转写结果拼成 Markdown 交付物。

默认产出**两个**文件（同一目录、同一前缀）::

    <作者>-<标题>-逐字稿.md   逐字转写 + 附录 A（专名校正对照表）+ 附录 B（可靠性说明）
    <作者>-<标题>-总结.md     要点式总结：视频主题 / 核心方法，逐条标注时间节点

用法:
    python3 dy_tomd.py --meta meta.json --transcript transcript.json -o ./notes
    python3 dy_tomd.py --meta m.json --transcript t.json --annotations ann.json -o ./notes
    python3 dy_tomd.py --meta m.json --transcript t.json --single-file -o ./notes  # 旧行为
    python3 dy_tomd.py --meta m.json --transcript t.json --stdout                # 旧行为（管道）

``--annotations`` 是 agent 写的标注 JSON（脚本只渲染，不做语义归纳）::

    {
      "corrections": [
        {"original": "桑德voice", "corrected": "SenseVoice",
         "evidence": "官方仓库 README 拼写（可选）"}
      ],
      "summary": {
        "one_line": "一句话概括（可选）",
        "topic": [
          {"label": "核心话题", "text": "……", "at": "00:00"},
          {"label": "核心观点", "text": "……", "at": "00:45"}
        ],
        "methods": [
          {"name": "方法名", "at": "02:10",
           "points": [{"text": "……", "at": "02:31"}]}
        ]
      },
      "reliability": {
        "conclusions": [{"text": "结论", "at": "01:20"}],
        "notes": [{"kind": "需澄清", "text": "……", "at": "03:10"}],
        "external_sources": ["专名拼写以官方仓库为准"]
      }
    }

约束（与 SKILL.md 一致）:
  * 总结只依据逐字稿与元数据，不引入外部资料；外部核对仅用于专名拼写，且须在
    ``corrections[].evidence`` / ``reliability.external_sources`` 中写明；
  * 每条要点必须带 ``at``（时间节点）或 ``section``（章节），否则渲染为「未标注」并记入附录 B；
  * 没有转写正文时只产出元数据文稿，**不生成总结**（不得臆造内容）；
  * 输出文件默认命名为 <作者>-<标题>-{逐字稿,总结}.md（已清洗非法字符）。
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from douyin2md.sources import EXTRACTION_FULL, WEIXIN_CHANNELS, meta_id  # noqa: E402

UNSAFE = r'[\\/:*?"<>|\r\n\t]'

MISSING_LABELS = {
    "video_stream": "视频流（mp4 / 音频）",
    "asr": "语音转写",
    "subtitles": "字幕",
    "timestamps": "视频内时间戳",
}

# 超过该秒数的段落间隔视为时间轴空白（可能是静音、纯画面或 VAD 判停）
GAP_SEC = 20.0
# 单条要点超过该字数时提示压缩（总结不应退化为复述）
POINT_MAX_CHARS = 150

TRANSCRIPT_SUFFIX = "逐字稿"
SUMMARY_SUFFIX = "总结"


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


def parse_ts(value):
    """把 "00:12" / "1:02:03" / 数值秒 解析成秒；无法解析返回 None。"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    m = re.fullmatch(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})", s)
    if m:
        hours = int(m.group(1) or 0)
        minutes, seconds = int(m.group(2)), int(m.group(3))
        if minutes >= 60 or seconds >= 60:
            return None
        return hours * 3600 + minutes * 60 + seconds
    try:
        return float(s)
    except ValueError:
        return None


def _cell(s) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


# ---------------------------------------------------------------------------
# 旧单文件渲染（保持逐字兼容，不要改这里的输出顺序与措辞）
# ---------------------------------------------------------------------------

def build(meta: dict, transcript: dict, with_ts: bool = True,
          frontmatter: bool = True, summary: str = "",
          appendices: str = "") -> str:
    source = meta.get("source") or "douyin"
    is_weixin = source == WEIXIN_CHANNELS
    title = meta.get("title") or meta.get("desc") or ("微信视频号内容" if is_weixin else "抖音视频")
    author = meta.get("author") or "-"
    url = meta.get("webpage_url") or "-"
    vid = meta_id(meta)
    dur = meta.get("duration_text") or (fmt_ts(meta.get("duration_sec")) if meta.get("duration_sec") else "-")
    tags = meta.get("tags") or []
    text = (transcript or {}).get("text") or ""
    segments = (transcript or {}).get("segments") or []
    missing = list(meta.get("missing") or [])
    evidence = list(meta.get("evidence") or [])
    declared = meta.get("extraction_status") or EXTRACTION_FULL
    # 传入非空转写说明内容已由用户补齐（方案 Tier 3），此时不再按降级输出
    degraded = declared != EXTRACTION_FULL and not text
    if degraded:
        doc_type = f"{source}-summary"
    elif source == "douyin":
        doc_type = "douyin-transcript"
    else:
        doc_type = f"{source}-transcript"

    out = []
    if frontmatter:
        out.append("---")
        out.append(f"title: {json.dumps(title, ensure_ascii=False)}")
        out.append(f"author: {json.dumps(author, ensure_ascii=False)}")
        out.append(f"source: {url}")
        out.append(f"aweme_id: \"{vid}\"")
        out.append(f"date: {fmt_date(meta.get('upload_date'))}")
        out.append(f"duration: {dur}")
        out.append(f"type: {doc_type}")
        # 旧抖音 meta 不新增任何字段，保证既有产物逐字兼容
        if source != "douyin":
            out.append(f"platform: {json.dumps(source, ensure_ascii=False)}")
            out.append(f"content_id: {json.dumps(vid, ensure_ascii=False)}")
        if degraded:
            out.append(f"extraction_status: {declared}")
            if missing:
                out.append("missing:")
                for item in missing:
                    out.append(f"  - {item}")
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

    if degraded:
        out.append("## 摘要说明（请先读）")
        out.append("")
        out.append("**本次未取得视频流，因此没有语音转写、字幕和视频内时间点。** "
                   "下文仅使用可直接验证的公开页面信息，不臆造视频内容。")
        out.append("")
        if missing:
            out.append("| 缺失内容 | 状态 |")
            out.append("| --- | --- |")
            for item in missing:
                out.append(f"| {MISSING_LABELS.get(item, item)} | 未取得 |")
            out.append("")
        for line in evidence:
            out.append(f"> 依据：{line}")
        out.append("")

    out.append("| 项目 | 值 |")
    out.append("| --- | --- |")
    out.append(f"| 作者 | {author} |")
    out.append(f"| {'内容 ID' if is_weixin else '视频 ID'} | `{vid}` |")
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
    if desc and (desc != title or degraded):
        out.append("## 视频文案")
        out.append("")
        out.append(desc)
        out.append("")

    # P2-1：封面 OCR 只是画面文字证据，绝不写进转写正文或时间戳。
    # 旧抖音 meta 没有 cover_ocr 字段，本节不会出现，产物保持逐字兼容。
    ocr = meta.get("cover_ocr") or {}
    ocr_lines = ocr.get("lines") or []
    if ocr.get("available") and ocr_lines:
        out.append("## 封面文字（OCR，须人工核对）")
        out.append("")
        out.append(f"> {ocr.get('note') or '机器识别结果，须人工核对。'}")
        out.append("")
        for line in ocr_lines:
            mark = "  ⚠️ 低置信度" if line.get("low_confidence") else ""
            out.append(f"- {line.get('text', '').strip()}{mark}")
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

    # 附录插在文末生成说明之前；appendices 为空时产物与旧版逐字一致
    if appendices:
        out.append(appendices.strip())
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"> 本文稿由 douyin2md 自动生成于 "
               f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
               + (f"，转写引擎：{transcript['engine']}" if (transcript or {}).get("engine") else "")
               + "。内容版权归原作者所有。")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 标注：专名校正
# ---------------------------------------------------------------------------

def load_annotations(path: str) -> dict:
    """读取 agent 写的标注 JSON；格式错误直接失败，不静默降级。"""
    if not path:
        return {}
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"[FAIL] 标注文件不存在: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[FAIL] 标注文件不是合法 JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("[FAIL] 标注文件顶层必须是 JSON 对象")
    return data


def apply_corrections(transcript: dict, corrections) -> tuple:
    """把专名校正应用到转写文本。

    返回 ``(transcript, rows)``；rows 每项含
    ``original / corrected / evidence / locations(秒) / applied / reason``。
    未命中的条目不会被静默丢弃：附录 A 标「未命中」，附录 B 逐条列出。
    """
    tr = dict(transcript or {})
    segs = [dict(s) for s in (tr.get("segments") or [])]
    text = tr.get("text") or ""
    rows = []
    for item in corrections or []:
        if not isinstance(item, dict):
            continue
        orig = str(item.get("original") or "").strip()
        new = str(item.get("corrected") or "").strip()
        row = {
            "original": orig,
            "corrected": new,
            "evidence": str(item.get("evidence") or "").strip(),
            "locations": [],
            "applied": False,
            "reason": "",
        }
        if not orig or not new:
            row["reason"] = "条目缺少 original 或 corrected"
        elif orig == new:
            row["reason"] = "校正结果与原识别相同"
        else:
            hits = 0
            for seg in segs:
                body = seg.get("text") or ""
                if orig in body:
                    hits += body.count(orig)
                    seg["text"] = body.replace(orig, new)
                    start = parse_ts(seg.get("start"))
                    if start is not None:
                        row["locations"].append(start)
            if not hits and not segs and orig in text:
                hits = text.count(orig)
                text = text.replace(orig, new)
            if hits:
                row["applied"] = True
            else:
                row["reason"] = "未在转写文本中命中"
        rows.append(row)

    if segs:
        tr["segments"] = segs
        tr["text"] = "\n".join((s.get("text") or "").strip() for s in segs).strip()
    else:
        tr["text"] = text
    return tr, rows


# ---------------------------------------------------------------------------
# 章节定位与覆盖率
# ---------------------------------------------------------------------------

def _section_marks(summary: dict) -> list:
    """从总结的核心方法里取 (起始秒, 方法名) 作为章节锚点。"""
    marks = []
    for m in (summary or {}).get("methods") or []:
        if not isinstance(m, dict):
            continue
        name = str(m.get("name") or "").strip()
        sec = parse_ts(m.get("at"))
        if name and sec is not None:
            marks.append((sec, name))
    return sorted(marks)


def _section_at(marks, sec):
    """返回 sec 所属（最近的前置）章节名；无匹配返回空串。"""
    if not marks or sec is None:
        return ""
    label = ""
    for start, name in marks:
        if sec + 1e-6 >= start:
            label = name
    return label


def _coverage(segments, duration) -> dict:
    """统计转写的时间覆盖与段落空白；没有可用时间戳时返回 None。

    引擎只给 ``start`` 不给 ``end`` 时不推算覆盖率与空白区间（``ends_known=False``），
    避免把「没有结束时间」误报成「没覆盖到」。
    """
    segs, ends_known = [], True
    for s in segments or []:
        start = parse_ts(s.get("start"))
        if start is None:
            continue
        end = parse_ts(s.get("end"))
        if end is None:
            ends_known = False
        segs.append((start, end))
    if not segs:
        return None
    segs.sort(key=lambda x: x[0])
    first = segs[0][0]
    last = max(en if en is not None else st for st, en in segs)
    gaps, prev_end = [], None
    if ends_known:
        for start, end in segs:
            if prev_end is not None and start - prev_end > GAP_SEC:
                gaps.append((prev_end, start))
            prev_end = max(prev_end if prev_end is not None else end, end)
    dur = parse_ts(duration)
    ratio = None
    if ends_known and dur and dur > 0:
        ratio = min(1.0, max(0.0, (last - first) / dur))
    return {"n": len(segs), "first": first, "last": last, "gaps": gaps,
            "duration": dur, "ratio": ratio, "ends_known": ends_known}


# ---------------------------------------------------------------------------
# 总结渲染
# ---------------------------------------------------------------------------

def _point_text(raw) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        return str(raw.get("text") or "").strip()
    return ""


def _render_points(points, duration, marks, problems, context: str = "") -> tuple:
    """要点 → Markdown 列表项；返回 (lines, 带位置条数)。

    ``context`` 是当前所在的小节名，要点落在同一小节内时不再重复标注章节名。
    """
    lines, positioned = [], 0
    for raw in points or []:
        if isinstance(raw, str):
            p = {"text": raw}
        elif isinstance(raw, dict):
            p = raw
        else:
            continue
        text = _point_text(p)
        if not text:
            continue
        at = parse_ts(p.get("at"))
        section = str(p.get("section") or "").strip()
        if not section and at is not None:
            section = _section_at(marks, at)
        if context and section == context:
            section = ""
        label = str(p.get("label") or "").strip()
        if at is None and not section:
            problems["no_position"] += 1
            suffix = "（未标注章节/时间节点 ⚠️）"
        else:
            bits = []
            if at is not None:
                bits.append(f"[{fmt_ts(at)}]")
                if duration and at > duration + 2:
                    problems["out_of_range"] += 1
            if section:
                bits.append(section)
            suffix = "（" + " · ".join(bits) + "）"
            positioned += 1
        if len(text) > POINT_MAX_CHARS:
            problems["too_long"] += 1
        head = f"- **{label}**：" if label else "- "
        lines.append(f"{head}{text}{suffix}")
    return lines, positioned


def _summary_status(stats: dict) -> tuple:
    missing = []
    if not stats.get("topic"):
        missing.append("视频主题")
    if not stats.get("methods"):
        missing.append("核心方法")
    if not missing:
        return "ok", ""
    return "pending", "缺少" + "、".join(missing) + "部分的要点"


def _pending_body(reason: str) -> list:
    return [
        f"> **本文件尚待补全**：{reason}。`dy_tomd.py` 只做渲染，不做语义归纳；"
        "请依据同目录逐字稿写出标注 JSON（`summary` 至少含 `topic` 与 `methods`），"
        "再用 `to-md --annotations <文件>` 重新渲染。",
        "",
        "## 视频主题",
        "",
        "- **核心话题**：（待补充，句末标注时间节点，如 `（[00:42]）`）",
        "- **核心观点**：（待补充，句末标注时间节点）",
        "",
        "## 核心方法",
        "",
        "### 1. （方法名） · [00:00]",
        "",
        "- （待补充：关键技术 / 实现思路 / 论证方式，一条一行，句末标注时间节点）",
        "",
    ]


def _render_summary_body(summary: dict, duration, marks) -> tuple:
    """渲染总结正文；返回 (lines, stats, problems)。"""
    problems = {"no_position": 0, "out_of_range": 0, "too_long": 0}
    summary = summary or {}
    lines = []

    one_line = str(summary.get("one_line") or "").strip()
    if one_line:
        lines += [f"> {one_line}", ""]

    lines += ["## 视频主题", ""]
    topic = summary.get("topic") or []
    topic_lines, topic_pos = _render_points(topic, duration, marks, problems)
    lines += topic_lines or ["- （未提供）"]
    lines.append("")

    lines += ["## 核心方法", ""]
    methods = [m for m in (summary.get("methods") or []) if isinstance(m, dict)]
    method_points, method_pos = 0, 0
    if not methods:
        lines += ["- （未提供）", ""]
    for i, m in enumerate(methods, 1):
        name = str(m.get("name") or "").strip() or f"方法 {i}"
        at = parse_ts(m.get("at"))
        section = str(m.get("section") or "").strip()
        if at is not None:
            head = f"### {i}. {name} · [{fmt_ts(at)}]"
            if section:
                head += f"（{section}）"
            if duration and at > duration + 2:
                problems["out_of_range"] += 1
        elif section:
            head = f"### {i}. {name}（{section}）"
        else:
            problems["no_position"] += 1
            head = f"### {i}. {name}（未标注时间节点 ⚠️）"
        lines += [head, ""]
        pts = m.get("points") or []
        method_points += len([1 for x in pts if _point_text(x)])
        p_lines, p_pos = _render_points(pts, duration, marks, problems, context=name)
        method_pos += p_pos
        lines += p_lines or ["- （未提供要点）"]
        lines.append("")

    stats = {
        "topic": len([1 for x in topic if _point_text(x)]),
        "methods": len(methods),
        "method_points": method_points,
        "positioned": topic_pos + method_pos,
    }
    return lines, stats, problems


def build_summary(meta: dict, body: list, status: str, base_name: str = "",
                  frontmatter: bool = True) -> str:
    source = meta.get("source") or "douyin"
    is_weixin = source == WEIXIN_CHANNELS
    title = meta.get("title") or meta.get("desc") or ("微信视频号内容" if is_weixin else "抖音视频")
    author = meta.get("author") or "-"
    url = meta.get("webpage_url") or "-"
    vid = meta_id(meta)
    dur = meta.get("duration_text") or (fmt_ts(meta.get("duration_sec")) if meta.get("duration_sec") else "-")
    tags = meta.get("tags") or []
    doc_type = "douyin-digest" if source == "douyin" else f"{source}-digest"

    out = []
    if frontmatter:
        out.append("---")
        out.append(f"title: {json.dumps(title, ensure_ascii=False)}")
        out.append(f"author: {json.dumps(author, ensure_ascii=False)}")
        out.append(f"source: {url}")
        out.append(f"aweme_id: \"{vid}\"")
        out.append(f"date: {fmt_date(meta.get('upload_date'))}")
        out.append(f"duration: {dur}")
        out.append(f"type: {doc_type}")
        out.append(f"doc: {SUMMARY_SUFFIX}")
        out.append(f"summary_status: {status}")
        if source != "douyin":
            out.append(f"platform: {json.dumps(source, ensure_ascii=False)}")
            out.append(f"content_id: {json.dumps(vid, ensure_ascii=False)}")
        out.append(f"generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if tags:
            out.append("tags:")
            for t in tags[:15]:
                out.append(f"  - {t}")
        out.append("---")
        out.append("")

    out.append(f"# {title}（总结）")
    out.append("")
    out.extend(body)
    out.append("---")
    out.append("")
    if base_name:
        out.append(f"> 逐字全文、专名校正对照表与可靠性说明见《{base_name}-{TRANSCRIPT_SUFFIX}.md》。")
    out.append(f"> 本文件由 douyin2md 依据逐字稿渲染于 "
               f"{datetime.now().strftime('%Y-%m-%d %H:%M')}；"
               "要点为归纳结果，时间节点用于回溯原文，不替代逐字稿。")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 附录
# ---------------------------------------------------------------------------

def appendix_corrections(rows, marks=None) -> list:
    out = ["## 附录 A 语音识别专名校正对照表", ""]
    if not rows:
        out += ["本次未做专名校正：标注文件未提供 `corrections`，或无需校正。", ""]
        return out
    out += ["| # | 原识别结果 | 校正结果 | 出现位置 |",
            "| --- | --- | --- | --- |"]
    for i, row in enumerate(rows, 1):
        if row["applied"]:
            locs = []
            for sec in row["locations"]:
                tag = f"[{fmt_ts(sec)}]"
                name = _section_at(marks or [], sec)
                locs.append(f"{tag}（{name}）" if name else tag)
            if len(locs) > 4:
                loc = "、".join(locs[:4]) + f" 等 {len(locs)} 处"
            else:
                loc = "、".join(locs)
            if not loc:
                loc = "全文（无时间戳）"
        else:
            loc = f"未命中（{row['reason'] or '未命中'}）"
        out.append(f"| {i} | {_cell(row['original'])} | {_cell(row['corrected'])} | {_cell(loc)} |")
    out.append("")
    evidence = [r for r in rows if r.get("evidence")]
    if evidence:
        out += ["核对来源（外部资料仅用于确认专名拼写，不用于推断内容）：", ""]
        for r in evidence:
            out.append(f"- {_cell(r['original'])} → {_cell(r['corrected'])}："
                       f"{_cell(r['evidence'])}")
        out.append("")
    unmatched = [r for r in rows if not r["applied"]]
    if unmatched:
        out += [f"> {len(unmatched)} 条校正未在转写文本中命中，已在附录 B 逐条列出，须人工确认。", ""]
    return out


def appendix_reliability(meta: dict, transcript: dict, rows, stats, problems,
                         status: str, reason: str, notes: dict, marks=None) -> list:
    notes = notes or {}
    out = ["## 附录 B 可靠性说明", "", "### 客观依据", ""]
    facts = []

    src = str(meta.get("extractor") or "").strip()
    if meta.get("capture_fallback"):
        facts.append("素材来源：抖音直连受风控拦截，改由浏览器拦截 `aweme/detail` 取得画面与音频"
                     "（与 yt-dlp 同一 meta 契约，文稿格式不受影响）")
    elif src:
        facts.append(f"素材来源：{src}")
    else:
        facts.append("素材来源：yt-dlp 直连（元数据未注明 extractor）")

    declared = meta.get("extraction_status") or EXTRACTION_FULL
    if declared != EXTRACTION_FULL:
        missing = "、".join(MISSING_LABELS.get(m, m) for m in (meta.get("missing") or []))
        facts.append(f"元数据状态：{declared}" + (f"；平台未提供：{missing}" if missing else ""))

    eng = (transcript or {}).get("engine") or "未注明"
    lang = (transcript or {}).get("language") or "未注明"
    facts.append(f"转写引擎：{eng}；语言：{lang}")

    duration = parse_ts(meta.get("duration_sec")) or parse_ts(meta.get("duration_text"))
    cov = _coverage((transcript or {}).get("segments"), duration)
    if cov:
        if cov["ends_known"]:
            line = (f"转写覆盖：{cov['n']} 段，时间轴 "
                    f"[{fmt_ts(cov['first'])}]–[{fmt_ts(cov['last'])}]")
            if cov["ratio"] is not None:
                line += f"，占视频时长（{fmt_ts(cov['duration'])}）的 {cov['ratio']:.0%}"
        else:
            line = f"转写覆盖：{cov['n']} 段，起点 [{fmt_ts(cov['first'])}]（引擎未提供结束时间）"
        facts.append(line)
        if not cov["ends_known"]:
            facts.append("时间轴终点：转写结果未提供段落结束时间，覆盖率与空白区间不做推算")
        elif cov["gaps"]:
            gaps = "、".join(f"[{fmt_ts(a)}]–[{fmt_ts(b)}]" for a, b in cov["gaps"][:5])
            more = f" 等 {len(cov['gaps'])} 处" if len(cov["gaps"]) > 5 else ""
            facts.append(f"时间轴空白：{gaps}{more}（超过 {int(GAP_SEC)} 秒无语音段，"
                         "可能是静音、纯画面或 VAD 判停）")
        else:
            facts.append(f"时间轴连续性：未发现超过 {int(GAP_SEC)} 秒的段落空白")
        if cov["n"] == 1:
            facts.append("时间戳粒度：转写仅 1 段、无细分时间轴，章节定位精度受限")
    else:
        facts.append("转写覆盖：转写结果没有可用的分段与时间戳，正文按整段呈现")

    applied = [r for r in rows if r["applied"]]
    unmatched = [r for r in rows if not r["applied"]]
    if rows:
        line = f"专名校正：{len(applied)}/{len(rows)} 条已应用到正文"
        if unmatched:
            line += f"，{len(unmatched)} 条未命中（见附录 A）"
        facts.append(line)
    else:
        facts.append("专名校正：未提供校正条目")

    ext = [str(s).strip() for s in (notes.get("external_sources") or []) if str(s).strip()]
    if ext:
        facts.append("逐字稿之外的核对来源：" + "；".join(ext))

    if stats is not None:
        facts.append(f"总结要点：视频主题 {stats['topic']} 条、核心方法 {stats['methods']} 节 "
                     f"{stats['method_points']} 条；其中 {stats['positioned']} 条带章节或时间节点")
        if status != "ok":
            facts.append(f"总结状态：{status}（{reason}）")

    out += [f"- {f}" for f in facts]
    out.append("")

    out += ["### 结论支撑", ""]
    conclusions = [c for c in (notes.get("conclusions") or []) if _point_text(c)]
    if conclusions:
        lines, _ = _render_points(conclusions, duration, marks or [], {"no_position": 0,
                                                                      "out_of_range": 0,
                                                                      "too_long": 0})
        out += lines
    else:
        out.append("- 未逐条列出对应关系；每条总结要点末尾的 `[mm:ss]` 即回溯位置。")
    out.append("")

    out += ["### 需解释 / 澄清 / 特别说明", ""]
    items = []
    if status != "ok":
        items.append(f"总结不完整：{reason}（summary_status: {status}），"
                     "现有要点不足以覆盖全片，需补全后重新渲染。")
    for r in unmatched:
        items.append(f"专名校正未命中：「{r['original']}」→「{r['corrected']}」"
                     f"{r['reason']}；可能是识别写法不同或已被其他条目覆盖，须人工确认。")
    if problems.get("no_position"):
        items.append(f"有 {problems['no_position']} 条要点未标注章节或时间节点，无法回溯"
                     "（总结文件内已标 ⚠️）。")
    if problems.get("out_of_range"):
        items.append(f"有 {problems['out_of_range']} 处时间节点超出视频时长，可能标注有误，"
                     "已按原文保留，须复核。")
    if problems.get("too_long"):
        items.append(f"有 {problems['too_long']} 条要点超过 {POINT_MAX_CHARS} 字，"
                     "可能已接近复述，建议压缩为一句。")
    for n in notes.get("notes") or []:
        if isinstance(n, str):
            text = n.strip()
            if text:
                items.append(text)
            continue
        if not isinstance(n, dict):
            continue
        text = str(n.get("text") or "").strip()
        if not text:
            continue
        kind = str(n.get("kind") or "").strip()
        at = parse_ts(n.get("at"))
        suffix = f"（[{fmt_ts(at)}]）" if at is not None else ""
        items.append(f"{kind}：{text}{suffix}" if kind else f"{text}{suffix}")
    out += [f"- {i}" for i in items] if items else ["- 无。"]
    out.append("")
    return out


# ---------------------------------------------------------------------------
# 两文件交付
# ---------------------------------------------------------------------------

def build_bundle(meta: dict, transcript: dict, annotations: dict = None,
                 with_ts: bool = True, frontmatter: bool = True,
                 base_name: str = "") -> dict:
    """渲染两个交付文件；返回 transcript / summary 两段 Markdown 与统计。"""
    ann = annotations or {}
    corrected, rows = apply_corrections(transcript, ann.get("corrections"))
    summary = ann.get("summary") if isinstance(ann.get("summary"), dict) else {}
    notes = ann.get("reliability") if isinstance(ann.get("reliability"), dict) else {}
    duration = parse_ts(meta.get("duration_sec")) or parse_ts(meta.get("duration_text"))
    marks = _section_marks(summary)

    body, stats, problems = _render_summary_body(summary, duration, marks)
    status, reason = _summary_status(stats)
    if status != "ok":
        if not stats["topic"] and not stats["methods"]:
            body = _pending_body(reason)
        else:
            body = [f"> ⚠️ 本文件不完整：{reason}。补全 `summary` 后用 `--annotations` "
                    "重新渲染。", ""] + body

    appendix_a = appendix_corrections(rows, marks)
    appendix_b = appendix_reliability(meta, corrected, rows, stats, problems,
                                      status, reason, notes, marks)
    transcript_md = build(meta, corrected, with_ts=with_ts, frontmatter=frontmatter,
                          appendices="\n".join(appendix_a + appendix_b))
    summary_md = build_summary(meta, body, status, base_name=base_name,
                              frontmatter=frontmatter)
    return {"transcript": transcript_md, "summary": summary_md,
            "summary_status": status, "summary_reason": reason,
            "stats": stats, "problems": problems, "corrections": rows}


def _warn_bundle(problems, rows, status, reason) -> None:
    for r in rows:
        if not r["applied"]:
            print(f"[warn] 专名校正未命中：「{r['original']}」→「{r['corrected']}」"
                  f"（{r['reason']}），已写入附录 A/B", file=sys.stderr)
    if problems.get("no_position"):
        print(f"[warn] {problems['no_position']} 条要点缺章节/时间节点，无法回溯",
              file=sys.stderr)
    if problems.get("out_of_range"):
        print(f"[warn] {problems['out_of_range']} 处时间节点超出视频时长，请复核",
              file=sys.stderr)
    if status != "ok":
        print(f"[warn] 总结未定稿（{reason}）：先写标注 JSON，再 "
              "`to-md --annotations` 重新渲染", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 Markdown 交付物（逐字稿 + 总结）")
    ap.add_argument("--meta", required=True, help="dy_fetch.py 输出的元数据 JSON")
    ap.add_argument("--transcript", help="dy_transcribe.py 输出的转写 JSON")
    ap.add_argument("-o", "--output-dir", default="./notes", help="输出目录")
    ap.add_argument("--filename", help="自定义输出文件名前缀（不含扩展名与 -逐字稿/-总结）")
    ap.add_argument("--no-timestamps", action="store_true", help="正文不带时间戳")
    ap.add_argument("--no-frontmatter", action="store_true", help="不加 YAML frontmatter")
    ap.add_argument("--summary", help="仅 --single-file 模式生效：追加一段摘要")
    ap.add_argument("--annotations", help="标注 JSON：专名校正 / 总结要点 / 可靠性说明")
    ap.add_argument("--single-file", action="store_true",
                    help="旧行为：只输出一篇合并文稿（不拆总结、不带附录）")
    ap.add_argument("--stdout", action="store_true", help="打印到标准输出（隐含 --single-file）")
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    transcript = None
    if args.transcript:
        p = Path(args.transcript)
        transcript = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    annotations = load_annotations(args.annotations)
    out_dir = Path(args.output_dir).expanduser()
    base = args.filename or f"{safe_name(meta.get('author') or '')}-{safe_name(meta.get('title') or '')}"
    base = base.strip("-") or "untitled"
    text = (transcript or {}).get("text") or ""

    # 旧行为：--stdout / --single-file 走单文件渲染，产物与历史版本逐字一致
    if args.stdout or args.single_file:
        if args.annotations and not args.stdout:
            print("[提示] --annotations 在 --single-file 模式下不生效", file=sys.stderr)
        md = build(meta, transcript, with_ts=not args.no_timestamps,
                   frontmatter=not args.no_frontmatter, summary=args.summary or "")
        if args.stdout:
            sys.stdout.write(md)
            return 0
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{base}.md"
        path.write_text(md, encoding="utf-8")
        print(f"[OK] {path}")
        print(f"     字数: {len(md)}  转写正文: {len(text)} 字")
        return 0

    if args.summary:
        print("[提示] --summary 仅在 --single-file / --stdout 模式生效，本次忽略",
              file=sys.stderr)

    # 无转写正文：保持既有降级单文件产物，不臆造总结
    if not text:
        md = build(meta, transcript, with_ts=not args.no_timestamps,
                   frontmatter=not args.no_frontmatter)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{base}.md"
        path.write_text(md, encoding="utf-8")
        print(f"[OK] {path}")
        print("     提示: 无转写正文，本次只产出元数据文稿，未生成总结（不臆造内容）")
        return 0

    bundle = build_bundle(meta, transcript, annotations,
                          with_ts=not args.no_timestamps,
                          frontmatter=not args.no_frontmatter, base_name=base)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_path = out_dir / f"{base}-{TRANSCRIPT_SUFFIX}.md"
    s_path = out_dir / f"{base}-{SUMMARY_SUFFIX}.md"
    t_path.write_text(bundle["transcript"], encoding="utf-8")
    s_path.write_text(bundle["summary"], encoding="utf-8")
    print(f"[OK] {t_path}")
    print(f"[OK] {s_path}")
    print(f"     字数: 逐字稿 {len(bundle['transcript'])}  总结 {len(bundle['summary'])}  "
          f"转写正文 {len(text)} 字  summary_status={bundle['summary_status']}")
    _warn_bundle(bundle["problems"], bundle["corrections"],
                 bundle["summary_status"], bundle["summary_reason"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
