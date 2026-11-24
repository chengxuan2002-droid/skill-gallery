"""dy_fetch.py 浏览器拦截自动兜底的离线单测（不联网、不启动真实浏览器）。

覆盖：
  - aweme/detail -> 与 yt-dlp slim() 一致的字段契约
  - capture_fallback() 成功/降级/失败路径
  - main() 在直连失败时自动兜底、--no-capture-fallback 保持旧行为、
    --force-capture 跳过 yt-dlp、直连成功时绝不触发兜底
  - CLI / dy.py 的参数透传与旧配置字典兼容
"""

import argparse
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "dy_fetch_fb", ROOT / "scripts" / "dy_fetch.py")
dyfetch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dyfetch)

_spec_dy = importlib.util.spec_from_file_location("dy_fb", ROOT / "scripts" / "dy.py")
dy = importlib.util.module_from_spec(_spec_dy)
_spec_dy.loader.exec_module(dy)

from douyin2md import cli as climod  # noqa: E402
from douyin2md.cli import build_parser, _pipeline_args  # noqa: E402
from douyin2md.config import DEFAULTS  # noqa: E402

LONG = "https://www.douyin.com/video/7707996226502888740/"
VID = "7707996226502888740"


def detail_fixture() -> dict:
    return {
        "aweme_detail": {
            "aweme_id": VID,
            "desc": "做AI短剧，用Grok Bot\n#AI短剧 #Grok",
            "create_time": 1767225600,
            "author": {"nickname": "黄益贺", "uid": "123456"},
            "statistics": {"digg_count": 100, "comment_count": 20,
                           "share_count": 5, "collect_count": 8, "play_count": 999},
            "video": {
                "duration": 377700,
                "cover": {"url_list": ["https://example.invalid/cover.jpg"]},
                "play_addr": {"url_list": ["https://example.invalid/a.mp4"]},
            },
            "text_extra": [{"hashtag_name": "AI短剧"}, {"hashtag_name": "Grok"}],
        }
    }


def completed(rc=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=rc,
                                       stdout=stdout, stderr=stderr)


class SlimFromDetailTest(unittest.TestCase):
    def test_all_slim_keys_present(self):
        meta = dyfetch.slim_from_detail(detail_fixture(), LONG, None)
        slim_keys = set(dyfetch.slim({}, LONG).keys())
        missing = slim_keys - set(meta.keys())
        self.assertEqual(missing, set(), "兜底 meta 必须覆盖 yt-dlp 契约的全部字段")

    def test_field_mapping(self):
        m = dyfetch.slim_from_detail(detail_fixture(), LONG, None)
        self.assertEqual(m["aweme_id"], VID)
        self.assertEqual(m["author"], "黄益贺")
        self.assertEqual(m["author_id"], "123456")
        self.assertEqual(m["title"], "做AI短剧，用Grok Bot")
        self.assertEqual(m["desc"], "做AI短剧，用Grok Bot\n#AI短剧 #Grok")
        self.assertEqual(m["duration_sec"], 378)
        self.assertEqual(m["duration_text"], "06:18")
        self.assertEqual(m["like_count"], 100)
        self.assertEqual(m["comment_count"], 20)
        self.assertEqual(m["repost_count"], 5)
        self.assertEqual(m["save_count"], 8)
        self.assertEqual(m["view_count"], 999)
        self.assertEqual(m["tags"], ["AI短剧", "Grok"])
        self.assertEqual(m["webpage_url"], LONG)
        self.assertRegex(str(m["upload_date"]), r"^\d{8}$")
        self.assertEqual(m["thumbnail"], "https://example.invalid/cover.jpg")

    def test_capture_marker_only_in_fallback_meta(self):
        self.assertTrue(dyfetch.slim_from_detail(detail_fixture(), LONG, None)["capture_fallback"])
        self.assertNotIn("capture_fallback", dyfetch.slim({}, LONG))

    def test_audio_path_recorded(self):
        m = dyfetch.slim_from_detail(detail_fixture(), LONG, Path("/tmp/x.mp4"))
        self.assertEqual(m["audio_path"], "/tmp/x.mp4")

    def test_empty_detail_returns_empty(self):
        self.assertEqual(dyfetch.slim_from_detail({}, LONG, None), {})
        self.assertEqual(dyfetch.slim_from_detail({"status_code": 0}, LONG, None), {})

    def test_aweme_detail_camel_case_variant(self):
        d = {"awemeDetail": detail_fixture()["aweme_detail"]}
        self.assertEqual(dyfetch.slim_from_detail(d, LONG, None)["aweme_id"], VID)

    def test_missing_duration_is_none(self):
        d = detail_fixture()
        d["aweme_detail"]["video"].pop("duration")
        m = dyfetch.slim_from_detail(d, LONG, None)
        self.assertIsNone(m["duration_sec"])
        self.assertIsNone(m["duration_text"])

    def test_missing_desc_falls_back_to_id(self):
        d = detail_fixture()
        d["aweme_detail"]["desc"] = ""
        m = dyfetch.slim_from_detail(d, LONG, None)
        self.assertEqual(m["title"], VID)


class CaptureFallbackTest(unittest.TestCase):
    def _prepare(self, td, with_mp4=True):
        cap = Path(td) / "capture"
        cap.mkdir(exist_ok=True)
        (cap / f"{VID}.detail.json").write_text(
            json.dumps(detail_fixture(), ensure_ascii=False), encoding="utf-8")
        if with_mp4:
            (cap / f"{VID}.mp4").write_bytes(b"0" * 2048)
        return cap

    def test_success_returns_meta_with_audio(self):
        with tempfile.TemporaryDirectory() as td:
            self._prepare(td)
            with mock.patch.object(dyfetch.subprocess, "run",
                                   return_value=completed(stdout="ok")) as run:
                meta, err = dyfetch.capture_fallback(LONG, Path(td), None, True)
            self.assertEqual(err, "")
            self.assertEqual(meta["aweme_id"], VID)
            self.assertTrue(meta["audio_path"].endswith(".mp4"))
            self.assertTrue(meta["capture_fallback"])
            cmd = run.call_args[0][0]
            self.assertTrue(any("dy_browser_capture.py" in str(p) for p in cmd))
            self.assertNotIn("--no-download", cmd)
            self.assertIn("--fresh", cmd, "无人值守应默认用全新游客会话避开验证码中间页")

    def test_explicit_cookies_are_respected_first(self):
        with tempfile.TemporaryDirectory() as td:
            self._prepare(td)
            with mock.patch.object(dyfetch.subprocess, "run",
                                   return_value=completed()) as run:
                dyfetch.capture_fallback(LONG, Path(td), "/tmp/ck.txt", True)
            cmd = run.call_args[0][0]
            self.assertNotIn("--fresh", cmd)
            self.assertIn("--cookies", cmd)
            self.assertIn("/tmp/ck.txt", cmd)

    def test_fresh_failure_retries_with_normal_session(self):
        with tempfile.TemporaryDirectory() as td:
            self._prepare(td)
            with mock.patch.object(dyfetch.subprocess, "run", side_effect=[
                    completed(rc=3, stdout="[risk] 命中验证码中间页"),
                    completed(stdout="ok")]) as run:
                meta, err = dyfetch.capture_fallback(LONG, Path(td), None, True)
            self.assertEqual(err, "")
            self.assertEqual(meta["aweme_id"], VID)
            self.assertEqual(run.call_count, 2)
            first = run.call_args_list[0][0][0]
            second = run.call_args_list[1][0][0]
            self.assertIn("--fresh", first)
            self.assertNotIn("--fresh", second)

    def test_no_audio_uses_no_download(self):
        with tempfile.TemporaryDirectory() as td:
            self._prepare(td, with_mp4=False)
            with mock.patch.object(dyfetch.subprocess, "run",
                                   return_value=completed()) as run:
                meta, err = dyfetch.capture_fallback(LONG, Path(td), None, False)
            self.assertEqual(err, "")
            self.assertIsNone(meta["audio_path"])
            self.assertIn("--no-download", run.call_args[0][0])

    def test_cookies_forwarded(self):
        with tempfile.TemporaryDirectory() as td:
            self._prepare(td)
            with mock.patch.object(dyfetch.subprocess, "run",
                                   return_value=completed()) as run:
                dyfetch.capture_fallback(LONG, Path(td), "/tmp/cookies.txt", False)
            cmd = run.call_args[0][0]
            self.assertIn("--cookies", cmd)
            self.assertIn("/tmp/cookies.txt", cmd)

    def test_capture_process_failure(self):
        with mock.patch.object(dyfetch.subprocess, "run",
                               return_value=completed(rc=3, stderr="chrome missing")):
            meta, err = dyfetch.capture_fallback(LONG, Path("/tmp/x"), None, True)
        self.assertIsNone(meta)
        self.assertIn("chrome missing", err)

    def test_capture_process_exception(self):
        with mock.patch.object(dyfetch.subprocess, "run", side_effect=OSError("boom")):
            meta, err = dyfetch.capture_fallback(LONG, Path("/tmp/x"), None, True)
        self.assertIsNone(meta)
        self.assertIn("boom", err)

    def test_no_detail_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(dyfetch.subprocess, "run", return_value=completed()):
                meta, err = dyfetch.capture_fallback(LONG, Path(td), None, True)
        self.assertIsNone(meta)
        self.assertIn("aweme/detail", err)

    def test_detail_without_media_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            self._prepare(td, with_mp4=False)
            with mock.patch.object(dyfetch.subprocess, "run", return_value=completed()):
                meta, err = dyfetch.capture_fallback(LONG, Path(td), None, True)
        self.assertIsNone(meta)
        self.assertIn("可转写的媒体", err)

    def test_broken_detail_json_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            cap = Path(td) / "capture"
            cap.mkdir()
            (cap / f"{VID}.detail.json").write_text("{not json", encoding="utf-8")
            with mock.patch.object(dyfetch.subprocess, "run", return_value=completed()):
                meta, err = dyfetch.capture_fallback(LONG, Path(td), None, True)
        self.assertIsNone(meta)
        self.assertIn("无法解析", err)


class FetchMainFallbackTest(unittest.TestCase):
    """用长链避免 resolve_short_url 触发 subprocess.run，隔离被测分支。"""

    def _run_main(self, td, extra=(), *, ytdlp_rc=0, ytdlp_stderr="",
                  pick=None, cap_result=None):
        argv = ["dy_fetch.py", LONG, "-o", td, *extra]
        cap_result = cap_result if cap_result is not None else (
            {"aweme_id": VID, "audio_path": "/tmp/x.mp4", "capture_fallback": True}, "")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(dyfetch.subprocess, "run",
                               return_value=completed(rc=ytdlp_rc, stderr=ytdlp_stderr)) as run, \
             mock.patch.object(dyfetch, "pick_meta", return_value=pick), \
             mock.patch.object(dyfetch, "capture_fallback",
                               return_value=cap_result) as cap, \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = dyfetch.main()
        return rc, out.getvalue(), err.getvalue(), run, cap

    def test_direct_failure_triggers_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, err, run, cap = self._run_main(td, ytdlp_rc=1,
                                                    ytdlp_stderr="Fresh cookies are needed")
            self.assertEqual(rc, 0)
            cap.assert_called_once()
            self.assertTrue(cap.call_args[1]["want_audio"])
            self.assertEqual(json.loads(out)["aweme_id"], VID)
            self.assertIn("诊断建议", err)
            self.assertIn("自动切换浏览器拦截兜底", err)

    def test_no_capture_fallback_keeps_old_behavior(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, err, run, cap = self._run_main(
                td, ("--no-capture-fallback",), ytdlp_rc=1,
                ytdlp_stderr="Fresh cookies are needed")
            self.assertEqual(rc, 1)
            self.assertEqual(out, "")
            cap.assert_not_called()
            self.assertIn("a_bogus", err)

    def test_force_capture_skips_ytdlp(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(sys, "argv",
                                   ["dy_fetch.py", LONG, "-o", td, "--force-capture"]), \
                 mock.patch.object(dyfetch.subprocess, "run",
                                   return_value=completed(rc=1)) as run, \
                 mock.patch.object(dyfetch, "capture_fallback",
                                   return_value=({"aweme_id": VID}, "")), \
                 contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                rc = dyfetch.main()
            self.assertEqual(rc, 0)
            run.assert_not_called()

    def test_force_capture_no_audio_disables_media(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(sys, "argv",
                                   ["dy_fetch.py", LONG, "-o", td,
                                    "--force-capture", "--no-audio"]), \
                 mock.patch.object(dyfetch.subprocess, "run",
                                   return_value=completed(rc=1)), \
                 mock.patch.object(dyfetch, "capture_fallback",
                                   return_value=({"aweme_id": VID}, "")) as cap, \
                 contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                rc = dyfetch.main()
            self.assertEqual(rc, 0)
            self.assertFalse(cap.call_args[1]["want_audio"])

    def test_fallback_failure_returns_1(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, err, run, cap = self._run_main(
                td, ytdlp_rc=1, ytdlp_stderr="Fresh cookies",
                cap_result=(None, "浏览器未捕获 aweme/detail 响应"))
            self.assertEqual(rc, 1)
            self.assertEqual(out, "")
            self.assertIn("兜底也失败", err)

    def test_direct_success_never_fallbacks(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, err, run, cap = self._run_main(td, pick={"id": VID})
            self.assertEqual(rc, 0)
            cap.assert_not_called()
            self.assertEqual(json.loads(out)["aweme_id"], VID)
            self.assertNotIn("capture_fallback", json.loads(out))

    def test_missing_info_json_triggers_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, err, run, cap = self._run_main(td, pick=None)
            self.assertEqual(rc, 0)
            cap.assert_called_once()


class FlagPropagationTest(unittest.TestCase):
    def _cfg(self, **over):
        return dict(DEFAULTS, **over)

    def test_cli_flags_forwarded(self):
        ns = build_parser().parse_args(
            ["url", LONG, "--no-capture-fallback", "--force-capture"])
        args = _pipeline_args(ns, self._cfg())
        self.assertIn("--no-capture-fallback", args)
        self.assertIn("--force-capture", args)

    def test_default_has_no_flags(self):
        ns = build_parser().parse_args(["url", LONG])
        args = _pipeline_args(ns, self._cfg())
        self.assertNotIn("--no-capture-fallback", args)
        self.assertNotIn("--force-capture", args)

    def test_config_can_force_capture(self):
        ns = build_parser().parse_args(["url", LONG])
        self.assertIn("--force-capture", _pipeline_args(ns, self._cfg(force_capture=True)))
        self.assertIn("--no-capture-fallback",
                      _pipeline_args(ns, self._cfg(no_capture_fallback=True)))

    def test_legacy_cfg_without_new_keys(self):
        old = {k: v for k, v in DEFAULTS.items()
               if k not in ("no_capture_fallback", "force_capture")}
        ns = build_parser().parse_args(["url", LONG])
        args = _pipeline_args(ns, old)
        self.assertNotIn("--force-capture", args)
        self.assertNotIn("--no-capture-fallback", args)

    def test_dy_forwards_flags_to_dy_fetch(self):
        ns = argparse.Namespace(output_dir="/tmp/out", cookies=None,
                                cookies_from_browser=None, quiet=False,
                                no_capture_fallback=True, force_capture=True)
        with mock.patch.object(dy, "run", return_value=completed(
                stdout=json.dumps({"aweme_id": "1"}))) as run:
            dy.fetch_one("https://v.douyin.com/abc123/", Path("/tmp/work"), ns, False)
        cmd = run.call_args[0][0]
        self.assertIn("--no-capture-fallback", cmd)
        self.assertIn("--force-capture", cmd)

    def test_fallback_success_is_reported_in_log(self):
        ns = argparse.Namespace(output_dir="/tmp/out", cookies=None,
                                cookies_from_browser=None, quiet=False)
        meta = {"aweme_id": "1", "capture_fallback": True, "audio_path": None}
        err = io.StringIO()
        with mock.patch.object(dy, "run", return_value=completed(
                stdout=json.dumps(meta))), contextlib.redirect_stderr(err):
            dy.fetch_one(LONG, Path("/tmp/work"), ns, False)
        self.assertIn("兜底", err.getvalue())

    def test_normal_meta_has_no_fallback_log(self):
        ns = argparse.Namespace(output_dir="/tmp/out", cookies=None,
                                cookies_from_browser=None, quiet=False)
        err = io.StringIO()
        with mock.patch.object(dy, "run", return_value=completed(
                stdout=json.dumps({"aweme_id": "1"}))), \
             contextlib.redirect_stderr(err):
            dy.fetch_one(LONG, Path("/tmp/work"), ns, False)
        self.assertNotIn("兜底", err.getvalue())

    def test_capture_command_fresh_flag(self):
        ns = build_parser().parse_args(["capture", LONG, "--fresh"])
        with mock.patch.object(climod, "_exec", return_value=0) as ex:
            climod.cmd_capture(ns, dict(DEFAULTS))
        args = ex.call_args[0][0]
        self.assertIn("--fresh", args)
        self.assertNotIn("--cookies", args)

    def test_capture_command_default_keeps_cookies(self):
        cfg = dict(DEFAULTS, cookies="/tmp/ck.txt")
        ns = build_parser().parse_args(["capture", LONG])
        with mock.patch.object(climod, "_exec", return_value=0) as ex:
            climod.cmd_capture(ns, cfg)
        args = ex.call_args[0][0]
        self.assertNotIn("--fresh", args)
        self.assertIn("--cookies", args)

    def test_dy_without_flags_keeps_command_unchanged(self):
        ns = argparse.Namespace(output_dir="/tmp/out", cookies=None,
                                cookies_from_browser=None, quiet=False)
        with mock.patch.object(dy, "run", return_value=completed(
                stdout=json.dumps({"aweme_id": "1"}))) as run:
            dy.fetch_one("https://v.douyin.com/abc123/", Path("/tmp/work"), ns, False)
        cmd = run.call_args[0][0]
        self.assertNotIn("--no-capture-fallback", cmd)
        self.assertNotIn("--force-capture", cmd)


if __name__ == "__main__":
    unittest.main()
