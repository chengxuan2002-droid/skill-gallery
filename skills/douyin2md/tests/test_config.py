"""配置优先级与脱敏的零依赖单测（不执行 scripts/ 下任何脚本）。"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from douyin2md.config import DEFAULTS, load_config, redacted


class ConfigTest(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("douyin2md.config.config_path", return_value=None):
                cfg = load_config()
        self.assertEqual(cfg["language"], "zh")
        self.assertEqual(cfg["engine"], "auto")
        self.assertEqual(cfg["output_dir"], "./notes")
        self.assertFalse(cfg["keep_audio"])

    def test_file_then_env_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"engine": "sherpa", "language": "zh"}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"DOUYIN2MD_ENGINE": "openai"}, clear=True):
                cfg = load_config(str(path))
        self.assertEqual(cfg["engine"], "openai")   # 环境变量优先
        self.assertEqual(cfg["language"], "zh")

    def test_bool_env(self):
        with mock.patch.dict(os.environ, {"DOUYIN2MD_KEEP_AUDIO": "yes"}, clear=True):
            with mock.patch("douyin2md.config.config_path", return_value=None):
                cfg = load_config()
        self.assertTrue(cfg["keep_audio"])

    def test_unknown_keys_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"_comment": "hi", "bogus": 1}), encoding="utf-8")
            cfg = load_config(str(path))
        self.assertEqual(set(cfg), set(DEFAULTS))
        self.assertNotIn("bogus", cfg)

    def test_secrets_never_appear_as_values(self):
        with mock.patch.dict(os.environ, {"SILICONFLOW_API_KEY": "YOUR_SILICONFLOW_API_KEY_HERE"}, clear=True):
            with mock.patch("douyin2md.config.config_path", return_value=None):
                safe = redacted(load_config())
        self.assertNotIn("YOUR_SILICONFLOW_API_KEY_HERE", json.dumps(safe, ensure_ascii=False))
        self.assertEqual(safe["SILICONFLOW_API_KEY"], "set")


if __name__ == "__main__":
    unittest.main()
