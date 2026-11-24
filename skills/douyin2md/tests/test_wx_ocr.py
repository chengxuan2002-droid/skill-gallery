"""P2-1 封面 OCR 适配器离线单测（不依赖 macOS Vision / tesseract 是否安装）。"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("wx_ocr", ROOT / "scripts" / "wx_ocr.py")
ocr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ocr)


class ParseTest(unittest.TestCase):
    def test_vision_tsv_parses_confidence_and_text(self):
        got = ocr._parse_vision_output("1.000\t华为如何用\n0.500\t破解大棋型幻觉\nERR noise\n")
        self.assertEqual(got, [("华为如何用", 1.0), ("破解大棋型幻觉", 0.5)])

    def test_tesseract_tsv_parses_conf_percent(self):
        line = "5\t1\t1\t1\t1\t0\t0\t0\t100\t50.000\t50\t工业知识图谱"
        got = ocr._parse_tesseract_tsv("level\tpage_num\tblock_num\tpar_num\tline_num\t"
                                       "word_num\tleft\ttop\twidth\theight\tconf\ttext\n" + line)
        self.assertEqual(got, [("工业知识图谱", 0.5)])


class ContractTest(unittest.TestCase):
    def test_result_marks_low_confidence(self):
        r = ocr._result("macos-vision", [("华为如何用", 1.0), ("破解大棋型幻觉", 0.5)], 0.8)
        self.assertTrue(r["available"])
        self.assertEqual(r["backend"], "macos-vision")
        self.assertEqual(r["low_confidence"], ["破解大棋型幻觉"])
        self.assertTrue(r["lines"][1]["low_confidence"])
        self.assertFalse(r["lines"][0]["low_confidence"])
        self.assertIn("须人工核对", r["note"])
        self.assertIn("不得作为", r["note"])

    def test_backend_none_is_unavailable_without_raising(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
            r = ocr.ocr_image(f.name, "none")
        self.assertFalse(r["available"])
        self.assertEqual(r["text"], "")
        self.assertEqual(r["lines"], [])

    def test_missing_image_is_unavailable(self):
        r = ocr.ocr_image("/tmp/definitely-not-here.jpg", "auto")
        self.assertFalse(r["available"])
        self.assertIn("封面图片不存在", r["reason"])

    def test_unknown_backend_is_unavailable(self):
        r = ocr.ocr_image("/tmp/x.jpg", "magic")
        self.assertFalse(r["available"])
        self.assertIn("未知 OCR 后端", r["reason"])

    def test_all_backends_failing_still_degrades(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f, \
             mock.patch.object(ocr, "_run_macos_vision", side_effect=RuntimeError("no swift")), \
             mock.patch.object(ocr, "_run_tesseract", side_effect=RuntimeError("no tesseract")):
            r = ocr.ocr_image(f.name, "auto")
        self.assertFalse(r["available"])
        self.assertIn("no swift", r["reason"])
        self.assertIn("no tesseract", r["reason"])

    def test_mocked_backend_produces_result(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f, \
             mock.patch.object(ocr, "_run_macos_vision",
                               return_value=[("华为如何用", 1.0)]):
            r = ocr.ocr_image(f.name, "auto")
        self.assertTrue(r["available"])
        self.assertEqual(r["text"], "华为如何用")


if __name__ == "__main__":
    unittest.main()
