"""视频号只读元数据适配器的离线单测。

用 mock 替换浏览器渲染与封面下载，不联网、不启动 Chrome。
覆盖方案第 6 节的契约验收与「空 feedInfo 不得产出看似完整的文稿」。
"""

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("wx_fetch", ROOT / "scripts" / "wx_fetch.py")
wx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wx)

SHORT = "https://weixin.qq.com/sph/AiQ59Q9O3y"
COVER = ("https://finder.video.qq.com/251/20304/stodownload?"
         "encfilekey=ABC&wxampicformat=503&picformat=200&token=xyz")


def payload(description="华为通过iDME.X构建工业增强知识图谱，从源头减少工业AI幻觉。",
             cover=COVER, createtime=1770189765):
    return {
        "errCode": 0,
        "data": {
            "authorInfo": {"nickname": "云知大道"},
            "feedInfo": {
                "picInfo": [], "description": description, "jumpInfo": {},
                "favCountFmt": "25", "likeCountFmt": "1331",
                "forwardCountFmt": "223", "commentCountFmt": "252",
                "createtime": createtime, "isHardAd": False, "coverUrl": cover,
            },
            "errMsg": "",
            "sceneInfo": {"dynamicExportId": "export/UzFfA", "expiredTime": 1770190000},
        },
    }


class UrlHelpersTest(unittest.TestCase):
    def test_short_link_to_preview_page(self):
        url, sid = wx.preview_url_of(SHORT)
        self.assertEqual(sid, "AiQ59Q9O3y")
        self.assertEqual(
            url, "https://channels.weixin.qq.com/finder-preview/pages/sph?id=AiQ59Q9O3y")

    def test_channels_url_passthrough(self):
        url = "https://channels.weixin.qq.com/finder-preview/pages/sph?id=AbC"
        got, sid = wx.preview_url_of(url)
        self.assertEqual(got, url)
        self.assertEqual(sid, "AbC")

    def test_hd_cover_keeps_other_params(self):
        hd = wx.hd_cover_url(COVER)
        self.assertNotIn("wxampicformat", hd)
        self.assertNotIn("picformat", hd)
        self.assertIn("encfilekey=ABC", hd)
        self.assertIn("token=xyz", hd)

    def test_stream_field_scan(self):
        self.assertEqual(wx.scan_stream_fields(payload()), [])
        with_stream = payload()
        with_stream["data"]["feedInfo"]["videoUrl"] = "https://x/y.mp4"
        self.assertIn("videoUrl", wx.scan_stream_fields(with_stream))


class BuildMetaTest(unittest.TestCase):
    def test_contract(self):
        meta = wx.build_meta(payload(), "可扫码前往微信观看此内容",
                             SHORT, "https://channels.weixin.qq.com/x", "AiQ59Q9O3y")
        self.assertEqual(meta["source"], "weixin-channels")
        self.assertEqual(meta["source_id"], "AiQ59Q9O3y")
        self.assertEqual(meta["extraction_status"], "metadata_only")
        self.assertEqual(meta["playability"], "client_only")
        self.assertEqual(meta["missing"],
                         ["video_stream", "asr", "subtitles", "timestamps"])
        self.assertTrue(meta["evidence"])
        self.assertTrue(any("页面图标顺序" in e for e in meta["evidence"]))
        self.assertLessEqual(len(meta["title"]), 31)
        self.assertEqual(meta["author"], "云知大道")
        self.assertEqual(meta["desc"], "华为通过iDME.X构建工业增强知识图谱，从源头减少工业AI幻觉。")
        self.assertNotEqual(meta["title"], meta["desc"])
        self.assertIsNone(meta["duration_sec"])
        self.assertIsNone(meta["audio_path"])
        self.assertNotIn("wxampicformat", meta["cover_url"])
        self.assertTrue(meta["upload_date"])

    def test_empty_feed_is_need_login(self):
        empty = {"data": {"feedInfo": {}}, "errCode": -1}
        with self.assertRaises(RuntimeError) as ctx:
            wx.build_meta(empty, "", SHORT, SHORT, "x")
        self.assertIn("need_login", str(ctx.exception))

    def test_no_stream_fields_is_client_only_even_without_hint(self):
        # 接口不下发任何流字段，本身就是「仅客户端可播」的证据
        meta = wx.build_meta(payload(), "", SHORT, SHORT, "x")
        self.assertEqual(meta["playability"], "client_only")

    def test_unknown_playability_when_stream_field_appears(self):
        with_stream = payload()
        with_stream["data"]["feedInfo"]["videoUrl"] = "https://x/y.mp4"
        meta = wx.build_meta(with_stream, "", SHORT, SHORT, "x")
        self.assertEqual(meta["playability"], "unknown")
        self.assertTrue(any("接口出现流字段名" in e for e in meta["evidence"]))


class MainTest(unittest.TestCase):
    def _run_main(self, argv, captured=None):
        out, err = io.StringIO(), io.StringIO()
        target = captured if captured is not None else (payload(), "可扫码前往微信观看此内容")
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(wx, "capture", return_value=target), \
             mock.patch.object(wx, "download_cover", return_value=True), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = wx.main()
        return rc, out.getvalue(), err.getvalue()

    def test_success_prints_single_meta_json(self):
        rc, out, _ = self._run_main(["wx_fetch.py", SHORT, "-o", "/tmp/wxtest"])
        self.assertEqual(rc, 0)
        meta = json.loads(out)
        self.assertEqual(meta["extraction_status"], "metadata_only")
        self.assertTrue(meta["cover_local"])

    def test_empty_feed_stops_without_markdown(self):
        rc, out, err = self._run_main(
            ["wx_fetch.py", SHORT, "-o", "/tmp/wxtest"],
            captured=({"data": {"feedInfo": {}}}, ""),
        )
        self.assertEqual(rc, 2)
        self.assertIn("need_login", err)
        self.assertEqual(out.strip(), "")

    def test_unsupported_source_rejected(self):
        rc, out, err = self._run_main(["wx_fetch.py", "https://example.invalid/x"])
        self.assertEqual(rc, 2)
        self.assertIn("unsupported_source", err)
        self.assertEqual(out.strip(), "")

    def test_ocr_disabled_by_default(self):
        rc, out, _ = self._run_main(["wx_fetch.py", SHORT, "-o", "/tmp/wxtest"])
        self.assertEqual(rc, 0)
        self.assertNotIn("cover_ocr", json.loads(out))

    def test_ocr_opt_in_adds_contract_and_evidence(self):
        fake = {"available": True, "backend": "macos-vision", "text": "华为如何用",
                "lines": [{"text": "华为如何用", "confidence": 1.0, "low_confidence": False}],
                "low_confidence": [], "note": "须人工核对"}
        with mock.patch.object(wx, "ocr_image", return_value=fake) as m:
            rc, out, err = self._run_main(
                ["wx_fetch.py", SHORT, "-o", "/tmp/wxtest", "--ocr"])
        self.assertEqual(rc, 0)
        meta = json.loads(out)
        self.assertEqual(meta["cover_ocr"]["backend"], "macos-vision")
        self.assertTrue(any("封面本地 OCR" in e for e in meta["evidence"]))
        self.assertIn("封面 OCR", err)
        m.assert_called_once()

    def test_ocr_unavailable_does_not_break_metadata(self):
        fake = {"available": False, "backend": None, "reason": "未安装 tesseract",
                "text": "", "lines": [], "low_confidence": [], "note": "须人工核对"}
        with mock.patch.object(wx, "ocr_image", return_value=fake):
            rc, out, _ = self._run_main(
                ["wx_fetch.py", SHORT, "-o", "/tmp/wxtest", "--ocr"])
        self.assertEqual(rc, 0)
        meta = json.loads(out)
        self.assertFalse(meta["cover_ocr"]["available"])
        self.assertEqual(meta["extraction_status"], "metadata_only")


if __name__ == "__main__":
    unittest.main()
