"""统一入口的只读单测。

只验证参数解析、配置注入与 doctor/config 两个只读子命令；
不调用任何会联网、下载或打开浏览器的子命令。
"""

import contextlib
import io
import json
import os
import unittest
from unittest import mock

from douyin2md import __version__
from douyin2md.cli import build_parser, main


class CliTest(unittest.TestCase):
    def test_parser_has_all_commands(self):
        parser = build_parser()
        names = set(parser._subparsers._group_actions[0].choices)
        self.assertEqual(
            names,
            {"url", "batch", "transcribe", "to-md", "capture", "model", "cookie", "doctor", "config"},
        )

    def test_config_flag_accepted_after_subcommand(self):
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("douyin2md.config.config_path", return_value=None):
                with contextlib.redirect_stdout(buf):
                    rc = main(["config", "--json", "--config", "/nonexistent/config.json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["language"], "zh")
        self.assertIn("SILICONFLOW_API_KEY", data)

    def test_doctor_is_read_only(self):
        buf = io.StringIO()
        with mock.patch("douyin2md.cli.subprocess.run") as run:
            with contextlib.redirect_stdout(buf):
                rc = main(["doctor", "--json"])
            run.assert_not_called()
        self.assertEqual(rc, 0)
        report = json.loads(buf.getvalue())
        self.assertEqual(report["status"] in {"ok", "degraded"}, True)
        self.assertIn("modules", report)
        self.assertNotIn("sk-", json.dumps(report, ensure_ascii=False))

    def test_version_string(self):
        self.assertTrue(__version__)

    def test_pipeline_args_inject_config(self):
        from douyin2md.cli import _pipeline_args
        ns = build_parser().parse_args(["url", "https://example.invalid/x"])
        cfg = {
            "output_dir": "./custom", "engine": "sherpa", "model": "sense-voice-int8",
            "language": "zh", "device": "", "provider": "", "cookies": "",
            "cookies_from_browser": "", "no_timestamps": True,
            "no_frontmatter": False, "keep_audio": False,
        }
        args = _pipeline_args(ns, cfg)
        self.assertIn("-o", args)
        self.assertIn("./custom", args)
        self.assertIn("--engine", args)
        self.assertIn("sherpa", args)
        self.assertIn("--no-timestamps", args)
        self.assertNotIn("--no-frontmatter", args)


if __name__ == "__main__":
    unittest.main()
