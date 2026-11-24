"""dy_tomd.build() 的降级契约与抖音链路回归单测。

重点验收：旧抖音 meta 输出**逐字不变**；metadata-only 文稿自动声明缺失，
且绝不伪造时间戳或转写正文。
"""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("dy_tomd", ROOT / "scripts" / "dy_tomd.py")
tomd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tomd)

OLD_META = {
    "aweme_id": "7653031071289773355",
    "title": "测试视频", "desc": "测试描述文案", "author": "某作者",
    "webpage_url": "https://www.douyin.com/video/7653031071289773355",
    "duration_sec": 90, "upload_date": "20260204",
    "like_count": 100, "tags": ["知识"],
}
WX_META = {
    "source": "weixin-channels", "source_id": "AiQ59Q9O3y",
    "title": "华为工业增强知识图谱（元数据摘要）",
    "desc": "华为通过iDME.X构建工业增强知识图谱。",
    "author": "云知大道", "webpage_url": "https://weixin.qq.com/sph/AiQ59Q9O3y",
    "upload_date": "2026-02-04 17:22:45", "tags": [],
    "extraction_status": "metadata_only", "playability": "client_only",
    "missing": ["video_stream", "asr", "subtitles", "timestamps"],
    "evidence": ["get_feed_info 完整响应扫描未发现视频流字段"],
}
TRANSCRIPT = {
    "text": "这是转写正文", "engine": "sherpa",
    "segments": [{"start": 0.0, "text": "这是转写正文"}],
}


class DouyinRegressionTest(unittest.TestCase):
    def test_old_meta_keeps_original_frontmatter(self):
        md = tomd.build(OLD_META, TRANSCRIPT)
        self.assertIn("type: douyin-transcript", md)
        self.assertIn('aweme_id: "7653031071289773355"', md)
        self.assertIn("| 视频 ID |", md)
        self.assertIn("## 转写正文", md)
        self.assertIn("**[00:00]** 这是转写正文", md)
        self.assertIn("asr_engine: sherpa", md)
        # 新增字段不得污染旧产物
        for field in ("platform:", "content_id:", "extraction_status:", "missing:",
                      "## 摘要说明"):
            self.assertNotIn(field, md)

    def test_old_meta_without_transcript_still_plain(self):
        md = tomd.build(OLD_META, None)
        self.assertIn("type: douyin-transcript", md)
        self.assertNotIn("## 摘要说明", md)
        self.assertNotIn("## 转写正文", md)

    def test_no_frontmatter_flag(self):
        md = tomd.build(OLD_META, None, frontmatter=False)
        self.assertNotIn("type: douyin-transcript", md)
        self.assertTrue(md.startswith("# 测试视频"))


class DegradationTest(unittest.TestCase):
    def test_metadata_only_declares_gaps(self):
        md = tomd.build(WX_META, None)
        self.assertIn("type: weixin-channels-summary", md)
        self.assertIn("platform: \"weixin-channels\"", md)
        self.assertIn("content_id: \"AiQ59Q9O3y\"", md)
        self.assertIn("extraction_status: metadata_only", md)
        self.assertIn("missing:", md)
        for item in WX_META["missing"]:
            self.assertIn(f"  - {item}", md)
        self.assertIn("## 摘要说明（请先读）", md)
        self.assertIn("| 缺失内容 | 状态 |", md)
        self.assertIn("视频流（mp4 / 音频）", md)
        self.assertIn("> 依据：get_feed_info 完整响应扫描未发现视频流字段", md)
        self.assertIn("| 内容 ID |", md)
        self.assertIn("## 视频文案", md)   # 官方描述必须保留

    def test_never_fabricates_transcript_or_timestamps(self):
        md = tomd.build(WX_META, None)
        self.assertNotIn("## 转写正文", md)
        self.assertNotIn("**[", md)
        self.assertNotIn("asr_engine", md)
        self.assertNotIn("转写引擎：", md)

    def test_transcript_supplied_upgrades_to_full(self):
        md = tomd.build(WX_META, TRANSCRIPT)
        self.assertNotIn("## 摘要说明", md)
        self.assertNotIn("extraction_status: metadata_only", md)
        self.assertIn("type: weixin-channels-transcript", md)
        self.assertIn("## 转写正文", md)
        self.assertIn("**[00:00]** 这是转写正文", md)

    def test_meta_id_fallback_no_none_filename(self):
        thin = {"source": "weixin-channels", "webpage_url": "https://example.invalid/x"}
        md = tomd.build(thin, None)
        self.assertNotIn("`None`", md)
        self.assertNotIn('aweme_id: "None"', md)

    def test_cover_ocr_section_is_evidence_not_transcript(self):
        meta = dict(WX_META)
        meta["cover_ocr"] = {
            "available": True, "backend": "macos-vision",
            "text": "华为如何用\n破解大棋型幻觉",
            "lines": [
                {"text": "华为如何用", "confidence": 1.0, "low_confidence": False},
                {"text": "破解大棋型幻觉", "confidence": 0.5, "low_confidence": True},
            ],
            "low_confidence": ["破解大棋型幻觉"],
            "note": "封面文字为 OCR 机器识别结果，须人工核对；不得作为视频口播内容或时间戳依据。",
        }
        md = tomd.build(meta, None)
        self.assertIn("## 封面文字（OCR，须人工核对）", md)
        self.assertIn("- 华为如何用", md)
        self.assertIn("- 破解大棋型幻觉  ⚠️ 低置信度", md)
        self.assertIn("不得作为视频口播内容", md)
        # OCR 只是画面文字证据，绝不变成转写正文或时间戳
        self.assertNotIn("## 转写正文", md)
        self.assertNotIn("**[", md)
        self.assertNotIn("asr_engine", md)

    def test_unavailable_ocr_adds_no_section(self):
        meta = dict(WX_META)
        meta["cover_ocr"] = {"available": False, "reason": "未安装 tesseract",
                             "lines": [], "text": "", "note": "须人工核对"}
        md = tomd.build(meta, None)
        self.assertNotIn("## 封面文字", md)

    def test_old_douyin_meta_has_no_ocr_section(self):
        md = tomd.build(OLD_META, TRANSCRIPT)
        self.assertNotIn("## 封面文字", md)


if __name__ == "__main__":
    unittest.main()
