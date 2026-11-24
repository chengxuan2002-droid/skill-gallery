"""来源判定与状态契约的零依赖单测（不联网、不执行 scripts）。"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from douyin2md.sources import (  # noqa: E402
    ALL_STATUSES, DOUYIN, STATUS_MEDIA_BLOCKED, STATUS_METADATA_ONLY,
    STATUS_NEED_LOGIN, STATUS_OK, STATUS_UNSUPPORTED, SUPPORTED_SOURCES,
    UNSUPPORTED, WEIXIN_CHANNELS, detect_source, extract_url, meta_id,
    source_advice, status_advice,
)


class DetectSourceTest(unittest.TestCase):
    def test_douyin_forms(self):
        for text in (
            "https://v.douyin.com/abc123/",
            "https://www.douyin.com/video/7653031071289773355",
            "7.43 xxx:/ 复制打开抖音 https://v.douyin.com/xx/ 看看",
            "https://www.douyin.com/video/123?modal_id=456",
        ):
            with self.subTest(text=text):
                self.assertEqual(detect_source(text), DOUYIN)

    def test_weixin_channels_forms(self):
        for text in (
            "https://weixin.qq.com/sph/AiQ59Q9O3y",
            "视频号视频:https://weixin.qq.com/sph/AiQ59Q9O3y",
            "https://channels.weixin.qq.com/finder-preview/pages/sph?id=AbC",
        ):
            with self.subTest(text=text):
                self.assertEqual(detect_source(text), WEIXIN_CHANNELS)

    def test_unsupported_forms(self):
        for text in (
            "https://example.invalid/x",
            "https://mp.weixin.qq.com/s/xxxx",   # 公众号文章，不是视频号
            "./local.mp4",
            "",
            "没有链接的一段文字",
        ):
            with self.subTest(text=text):
                self.assertEqual(detect_source(text), UNSUPPORTED)

    def test_extract_url_strips_trailing_punctuation(self):
        self.assertEqual(
            extract_url("看这个 https://weixin.qq.com/sph/AiQ59Q9O3y）。"),
            "https://weixin.qq.com/sph/AiQ59Q9O3y",
        )
        with self.assertRaises(ValueError):
            extract_url("纯文字")


class ContractTest(unittest.TestCase):
    def test_supported_sources(self):
        self.assertEqual(set(SUPPORTED_SOURCES), {DOUYIN, WEIXIN_CHANNELS})

    def test_all_statuses(self):
        self.assertEqual(set(ALL_STATUSES), {
            STATUS_OK, STATUS_METADATA_ONLY, STATUS_MEDIA_BLOCKED,
            STATUS_NEED_LOGIN, STATUS_UNSUPPORTED,
        })
        for status in (*ALL_STATUSES, "unknown"):
            self.assertTrue(status_advice(status))

    def test_source_advice_mentions_fallback(self):
        self.assertIn("transcribe", source_advice(WEIXIN_CHANNELS))
        self.assertIn("transcribe", source_advice(UNSUPPORTED))
        self.assertTrue(source_advice(DOUYIN))

    def test_meta_id_priority_and_fallback(self):
        self.assertEqual(meta_id({"aweme_id": "7653", "source_id": "x"}), "7653")
        self.assertEqual(meta_id({"source_id": "AiQ59Q9O3y"}), "AiQ59Q9O3y")
        self.assertEqual(meta_id({"id": "abc"}), "abc")
        fallback = meta_id({"webpage_url": "https://example.invalid/x"})
        self.assertEqual(len(fallback), 16)
        self.assertNotIn("None", fallback)
        self.assertEqual(meta_id({}), "unknown")


if __name__ == "__main__":
    unittest.main()
