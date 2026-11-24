"""两文件交付契约单测：逐字稿（附录 A/B）与总结（要点式 + 时间节点）。

不联网、不调用子进程；全部走 dy_tomd 的渲染函数与 main()。
"""

import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("dy_tomd_bundle", ROOT / "scripts" / "dy_tomd.py")
tomd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tomd)

META = {
    "aweme_id": "7653031071289773355", "title": "测试视频", "desc": "测试描述文案",
    "author": "某作者", "webpage_url": "https://www.douyin.com/video/7653031071289773355",
    "duration_sec": 90, "upload_date": "20260204", "like_count": 100, "tags": ["知识"],
    "extractor": "douyin (yt-dlp)",
}
WX_META = {
    "source": "weixin-channels", "source_id": "AiQ59Q9O3y",
    "title": "元数据摘要", "desc": "官方描述", "author": "某作者",
    "webpage_url": "https://weixin.qq.com/sph/AiQ59Q9O3y",
    "extraction_status": "metadata_only", "playability": "client_only",
    "missing": ["video_stream", "asr", "subtitles", "timestamps"],
}
TRANSCRIPT = {
    "text": "第一段 桑德voice 很好用\n第二段 阿格斯 风控",
    "engine": "sherpa:sense-voice-int8", "language": "zh",
    "segments": [
        {"start": 0.0, "end": 3.0, "text": "第一段 桑德voice 很好用"},
        {"start": 8.5, "end": 12.0, "text": "第二段 阿格斯 风控"},
    ],
}
ANNOTATIONS = {
    "corrections": [
        {"original": "桑德voice", "corrected": "SenseVoice", "evidence": "官方仓库 README"},
        {"original": "阿格斯", "corrected": "Argus"},
    ],
    "summary": {
        "one_line": "一句话概括。",
        "topic": [
            {"label": "核心话题", "text": "转写工具的交付形态", "at": "00:00"},
            {"label": "核心观点", "text": "逐字稿与总结必须分开", "at": "00:08"},
        ],
        "methods": [
            {"name": "专名三级校验", "at": "00:08",
             "points": [{"text": "换模型交叉校验后抽帧定案", "at": "00:08"}]},
        ],
    },
    "reliability": {
        "conclusions": [{"text": "双文件契约", "at": "00:08"}],
        "notes": [{"kind": "需澄清", "text": "同音误识已校正", "at": "00:00"}],
    },
}


def bundle(**over):
    ann = json.loads(json.dumps(ANNOTATIONS, ensure_ascii=False))
    ann.update(over.pop("annotations", {}))
    return tomd.build_bundle(META, TRANSCRIPT, ann, base_name="某作者-测试视频", **over)


class TwoFileContractTest(unittest.TestCase):
    def test_main_writes_two_files(self):
        with tempfile.TemporaryDirectory() as td:
            meta_path = Path(td) / "meta.json"
            tr_path = Path(td) / "tr.json"
            ann_path = Path(td) / "ann.json"
            meta_path.write_text(json.dumps(META, ensure_ascii=False), encoding="utf-8")
            tr_path.write_text(json.dumps(TRANSCRIPT, ensure_ascii=False), encoding="utf-8")
            ann_path.write_text(json.dumps(ANNOTATIONS, ensure_ascii=False), encoding="utf-8")
            out = Path(td) / "notes"
            argv = ["dy_tomd.py", "--meta", str(meta_path), "--transcript", str(tr_path),
                    "--annotations", str(ann_path), "-o", str(out)]
            with mock.patch.object(sys, "argv", argv), \
                 contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                rc = tomd.main()
            self.assertEqual(rc, 0)
            names = sorted(p.name for p in out.glob("*.md"))
            self.assertEqual(names, ["某作者-测试视频-总结.md", "某作者-测试视频-逐字稿.md"])

    def test_summary_pending_without_annotations(self):
        doc = bundle(annotations={"summary": {}, "corrections": []})
        self.assertEqual(doc["summary_status"], "pending")
        self.assertIn("summary_status: pending", doc["summary"])
        self.assertIn("本文件尚待补全", doc["summary"])
        # 骨架仍保留两部分结构，避免下游读到残缺文档
        self.assertIn("## 视频主题", doc["summary"])
        self.assertIn("## 核心方法", doc["summary"])
        # 逐字稿即使没有总结也必须带两份附录
        self.assertIn("## 附录 A 语音识别专名校正对照表", doc["transcript"])
        self.assertIn("## 附录 B 可靠性说明", doc["transcript"])

    def test_summary_link_points_to_transcript_file(self):
        doc = bundle()
        self.assertIn("《某作者-测试视频-逐字稿.md》", doc["summary"])

    def test_metadata_only_does_not_invent_summary(self):
        """无转写正文时只产出元数据文稿，不生成总结。"""
        with tempfile.TemporaryDirectory() as td:
            meta_path = Path(td) / "wx.json"
            meta_path.write_text(json.dumps(WX_META, ensure_ascii=False), encoding="utf-8")
            out = Path(td) / "notes"
            argv = ["dy_tomd.py", "--meta", str(meta_path), "-o", str(out)]
            buf = io.StringIO()
            with mock.patch.object(sys, "argv", argv), \
                 contextlib.redirect_stdout(buf), \
                 contextlib.redirect_stderr(io.StringIO()):
                rc = tomd.main()
            self.assertEqual(rc, 0)
            self.assertEqual([p.name for p in out.glob("*.md")], ["某作者-元数据摘要.md"])
            self.assertIn("未生成总结", buf.getvalue())


class AppendixATest(unittest.TestCase):
    def test_corrections_replace_body_and_record_location(self):
        doc = bundle()
        self.assertIn("**[00:00]** 第一段 SenseVoice 很好用", doc["transcript"])
        self.assertIn("**[00:08]** 第二段 Argus 风控", doc["transcript"])
        self.assertIn("| 1 | 桑德voice | SenseVoice | [00:00]", doc["transcript"])
        self.assertIn("| 2 | 阿格斯 | Argus | [00:08]", doc["transcript"])

    def test_evidence_listed_when_given(self):
        doc = bundle()
        self.assertIn("核对来源", doc["transcript"])
        self.assertIn("桑德voice → SenseVoice：官方仓库 README", doc["transcript"])

    def test_unmatched_correction_is_not_silently_dropped(self):
        doc = bundle(annotations={"corrections": [
            {"original": "桑德voice", "corrected": "SenseVoice"},
            {"original": "不存在的词", "corrected": "X"},
        ]})
        self.assertIn("未命中", doc["transcript"])
        self.assertIn("不存在的词", doc["transcript"])
        # 附录 B 必须逐条解释未命中原因
        self.assertIn("专名校正未命中：「不存在的词」→「X」", doc["transcript"])
        self.assertEqual(doc["summary_status"], "ok")

    def test_corrections_without_segments_fall_back_to_text(self):
        tr = {"text": "桑德voice 很好用", "engine": "cloud:m"}
        corrected, rows = tomd.apply_corrections(
            tr, [{"original": "桑德voice", "corrected": "SenseVoice"}])
        self.assertEqual(corrected["text"], "SenseVoice 很好用")
        self.assertTrue(rows[0]["applied"])
        doc = tomd.build_bundle(META, tr, {"corrections": [
            {"original": "桑德voice", "corrected": "SenseVoice"}]},
            base_name="x")
        self.assertIn("全文（无时间戳）", doc["transcript"])

    def test_empty_or_identical_correction_is_flagged(self):
        _, rows = tomd.apply_corrections(TRANSCRIPT, [
            {"original": "", "corrected": "x"},
            {"original": "同词", "corrected": "同词"},
        ])
        for row in rows:
            self.assertFalse(row["applied"])
            self.assertTrue(row["reason"])


class AppendixBTest(unittest.TestCase):
    def test_objective_facts_present(self):
        doc = bundle()
        text = doc["transcript"]
        self.assertIn("### 客观依据", text)
        self.assertIn("素材来源：douyin (yt-dlp)", text)
        self.assertIn("转写引擎：sherpa:sense-voice-int8；语言：zh", text)
        self.assertIn("转写覆盖：2 段", text)
        self.assertIn("专名校正：2/2 条已应用到正文", text)
        self.assertIn("视频主题 2 条、核心方法 1 节 1 条", text)

    def test_coverage_ratio_and_gap_reported(self):
        tr = {"text": "a\nb", "engine": "e", "segments": [
            {"start": 0.0, "end": 3.0, "text": "a"},
            {"start": 60.0, "end": 62.0, "text": "b"}]}
        doc = tomd.build_bundle(META, tr, {}, base_name="x")
        self.assertIn("占视频时长（01:30）的 69%", doc["transcript"])
        self.assertIn("时间轴空白：[00:03]–[01:00]", doc["transcript"])

    def test_single_segment_warns_about_timestamp_granularity(self):
        tr = {"text": "整段", "engine": "cloud:m",
              "segments": [{"start": 0.0, "end": None, "text": "整段"}]}
        doc = tomd.build_bundle(META, tr, {}, base_name="x")
        self.assertIn("时间戳粒度：转写仅 1 段", doc["transcript"])
        # 引擎没给结束时间时不得推算覆盖率，否则会把「无结束时间」误报成「没覆盖」
        self.assertIn("引擎未提供结束时间", doc["transcript"])
        self.assertNotIn("占视频时长", doc["transcript"])

    def test_no_notes_still_explicit(self):
        doc = tomd.build_bundle(META, TRANSCRIPT, {"summary": ANNOTATIONS["summary"]},
                                base_name="x")
        self.assertEqual(doc["summary_status"], "ok")
        self.assertIn("### 需解释 / 澄清 / 特别说明", doc["transcript"])
        self.assertIn("- 无。", doc["transcript"])


class SummaryShapeTest(unittest.TestCase):
    def test_each_point_is_one_line_with_position(self):
        doc = bundle()
        body = doc["summary"]
        topic_lines = [l for l in body.splitlines() if l.startswith("- **核心")]
        self.assertEqual(len(topic_lines), 2)
        for line in topic_lines:
            self.assertRegex(line, r"（\[00:0\d\]")

    def test_method_heading_and_points_carry_timestamps(self):
        doc = bundle()
        self.assertIn("### 1. 专名三级校验 · [00:08]", doc["summary"])
        self.assertIn("换模型交叉校验后抽帧定案（[00:08]）", doc["summary"])

    def test_position_is_mandatory(self):
        ann = {"summary": {"topic": [{"label": "核心话题", "text": "缺位置"}],
                           "methods": [{"name": "方法", "at": "00:05",
                                        "points": [{"text": "缺位置"}]}]}}
        doc = bundle(annotations=ann)
        self.assertEqual(doc["summary_status"], "ok")
        self.assertIn("（未标注章节/时间节点 ⚠️）", doc["summary"])
        self.assertIn("未标注章节或时间节点", doc["transcript"])

    def test_out_of_range_timestamp_is_flagged(self):
        ann = {"summary": {"topic": [{"text": "越界", "at": "09:99"}],
                           "methods": [{"name": "方法", "at": "01:00",
                                        "points": [{"text": "正常", "at": "01:00"}]}]}}
        doc = tomd.build_bundle(META, TRANSCRIPT, ann, base_name="x")
        # "09:99" 被 parse_ts 视为无法解析的分钟位，按「未标注」处理
        self.assertIn("未标注", doc["summary"])
        ann2 = {"summary": {"topic": [{"text": "越界", "at": "05:00"}],
                            "methods": [{"name": "方法", "at": "01:00",
                                         "points": [{"text": "正常", "at": "01:00"}]}]}}
        doc2 = tomd.build_bundle(META, TRANSCRIPT, ann2, base_name="x")
        self.assertEqual(doc2["problems"]["out_of_range"], 1)
        self.assertIn("超出视频时长", doc2["transcript"])

    def test_partial_summary_is_marked_incomplete(self):
        ann = {"summary": {"topic": [{"text": "只有主题", "at": "00:00"}], "methods": []}}
        doc = bundle(annotations=ann)
        self.assertEqual(doc["summary_status"], "pending")
        self.assertIn("本文件不完整", doc["summary"])
        self.assertIn("（未提供）", doc["summary"])

    def test_section_name_not_duplicated_inside_method(self):
        doc = bundle()
        # 方法小节内的要点不再重复所在小节名，跨小节的要点仍标章节以便回溯
        self.assertIn("- 换模型交叉校验后抽帧定案（[00:08]）", doc["summary"])
        self.assertIn("（[00:08] · 专名三级校验）", doc["summary"])


class LegacyCompatibilityTest(unittest.TestCase):
    def test_single_file_matches_legacy_build(self):
        with tempfile.TemporaryDirectory() as td:
            meta_path = Path(td) / "meta.json"
            tr_path = Path(td) / "tr.json"
            meta_path.write_text(json.dumps(META, ensure_ascii=False), encoding="utf-8")
            tr_path.write_text(json.dumps(TRANSCRIPT, ensure_ascii=False), encoding="utf-8")
            out = Path(td) / "notes"
            argv = ["dy_tomd.py", "--meta", str(meta_path), "--transcript", str(tr_path),
                    "--single-file", "-o", str(out)]
            with mock.patch.object(sys, "argv", argv), \
                 contextlib.redirect_stdout(io.StringIO()):
                rc = tomd.main()
            self.assertEqual(rc, 0)
            got = (out / "某作者-测试视频.md").read_text(encoding="utf-8")
            expect = tomd.build(META, TRANSCRIPT)
            strip = lambda s: re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", "T", s)
            self.assertEqual(strip(got), strip(expect))
            self.assertNotIn("附录", got)

    def test_stdout_keeps_single_document(self):
        with tempfile.TemporaryDirectory() as td:
            meta_path = Path(td) / "meta.json"
            meta_path.write_text(json.dumps(META, ensure_ascii=False), encoding="utf-8")
            buf = io.StringIO()
            argv = ["dy_tomd.py", "--meta", str(meta_path), "--stdout"]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buf):
                rc = tomd.main()
            self.assertEqual(rc, 0)
            self.assertIn("# 测试视频", buf.getvalue())
            self.assertNotIn("附录 A", buf.getvalue())


class AnnotationsLoadingTest(unittest.TestCase):
    def test_missing_file_fails_loudly(self):
        with self.assertRaises(SystemExit):
            tomd.load_annotations("/nonexistent/ann.json")

    def test_bad_json_fails_loudly(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ann.json"
            p.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(SystemExit):
                tomd.load_annotations(str(p))

    def test_non_object_top_level_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ann.json"
            p.write_text("[]", encoding="utf-8")
            with self.assertRaises(SystemExit):
                tomd.load_annotations(str(p))


class ParseTsTest(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(tomd.parse_ts("00:12"), 12)
        self.assertEqual(tomd.parse_ts("1:02:03"), 3723)
        self.assertEqual(tomd.parse_ts(65), 65.0)
        self.assertEqual(tomd.parse_ts("65"), 65.0)

    def test_invalid(self):
        for bad in (None, "", "abc", "09:99"):
            self.assertIsNone(tomd.parse_ts(bad))


if __name__ == "__main__":
    unittest.main()
