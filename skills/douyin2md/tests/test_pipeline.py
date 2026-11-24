"""dy.py 来源分流与批量状态机的离线单测（不联网、不调用真实子进程）。"""

import argparse
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("dy", ROOT / "scripts" / "dy.py")
dy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dy)

WX = "https://weixin.qq.com/sph/AiQ59Q9O3y"
DOUYIN = "https://v.douyin.com/abc123/"


def args(output_dir="/tmp/pipeline-out"):
    return argparse.Namespace(output_dir=output_dir, cookies=None,
                              cookies_from_browser=None, quiet=False)


def completed(rc=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


class ClassifyTest(unittest.TestCase):
    def test_douyin_is_ok(self):
        self.assertEqual(dy.classify({"source": "douyin", "aweme_id": "1"}, None),
                         dy.STATUS_OK)

    def test_legacy_meta_without_source_is_ok(self):
        self.assertEqual(dy.classify({"aweme_id": "1"}, None), dy.STATUS_OK)

    def test_client_only_is_media_blocked(self):
        meta = {"source": "weixin-channels", "extraction_status": "metadata_only",
                "playability": "client_only"}
        self.assertEqual(dy.classify(meta, None), dy.STATUS_MEDIA_BLOCKED)

    def test_unknown_playability_is_metadata_only(self):
        meta = {"source": "weixin-channels", "extraction_status": "metadata_only",
                "playability": "unknown"}
        self.assertEqual(dy.classify(meta, None), dy.STATUS_METADATA_ONLY)

    def test_need_login_propagates(self):
        meta = {"source": "weixin-channels", "extraction_status": "need_login"}
        self.assertEqual(dy.classify(meta, None), dy.STATUS_NEED_LOGIN)


class FetchOneTest(unittest.TestCase):
    def test_unsupported_source_never_invokes_subprocess(self):
        err = io.StringIO()
        with mock.patch.object(dy, "run") as run, contextlib.redirect_stderr(err):
            got = dy.fetch_one("https://example.invalid/x", Path("/tmp/work"), args(), False)
        run.assert_not_called()
        self.assertEqual(got, (None, None, dy.STATUS_UNSUPPORTED))
        self.assertIn("unsupported_source", err.getvalue())

    def test_weixin_routes_to_wx_fetch_with_cover_dir(self):
        meta = {"source": "weixin-channels", "source_id": "AiQ59Q9O3y",
                "extraction_status": "metadata_only", "playability": "client_only",
                "audio_path": None}
        with mock.patch.object(dy, "run", return_value=completed(
                stdout=json.dumps(meta, ensure_ascii=False))) as run:
            got = dy.fetch_one(WX, Path("/tmp/work"), args(), True)
        cmd = run.call_args[0][0]
        self.assertTrue(any("wx_fetch.py" in str(part) for part in cmd))
        self.assertIn("--cover-dir", cmd)
        self.assertIn("/tmp/pipeline-out", cmd)
        self.assertIn("-q", cmd)          # quiet=True 透传给适配器
        self.assertEqual(got[0]["source"], "weixin-channels")
        self.assertIsNone(got[1])
        self.assertEqual(got[2], dy.STATUS_MEDIA_BLOCKED)

    def test_douyin_still_routes_to_dy_fetch(self):
        meta = {"aweme_id": "7653", "audio_path": None}
        with mock.patch.object(dy, "run", return_value=completed(
                stdout=json.dumps(meta))) as run:
            got = dy.fetch_one(DOUYIN, Path("/tmp/work"), args(), False)
        cmd = run.call_args[0][0]
        self.assertTrue(any("dy_fetch.py" in str(part) for part in cmd))
        self.assertEqual(got[2], dy.STATUS_OK)

    def test_need_login_error_maps_to_status(self):
        with mock.patch.object(dy, "run", return_value=completed(
                rc=2, stderr="[FAIL] [need_login] 缺少 playwright")):
            got = dy.fetch_one(WX, Path("/tmp/work"), args(), False)
        self.assertIsNone(got[0])
        self.assertEqual(got[2], dy.STATUS_NEED_LOGIN)

    def test_bad_json_is_failed(self):
        with mock.patch.object(dy, "run", return_value=completed(stdout="not-json")):
            got = dy.fetch_one(DOUYIN, Path("/tmp/work"), args(), False)
        self.assertIsNone(got[0])
        self.assertEqual(got[2], "failed")


class SingleModeTranscribeTest(unittest.TestCase):
    """回归：旧代码 `if audio and batch:` 让单条抖音链接跳过转写。"""

    def _run_pipeline(self, links, use_links_file=False):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            audio = out / "sample.mp3"
            audio.write_bytes(b"fake-audio")
            metas = [{"aweme_id": str(7653 + i), "title": "测试", "author": "某作者",
                      "audio_path": str(audio)} for i in range(len(links))]
            calls = []

            def fake_fetch(link, work, args, quiet):
                return metas[links.index(link)], audio, dy.STATUS_OK

            def fake_run(cmd, desc, quiet=False):
                calls.append(list(cmd))
                return completed()

            if use_links_file:
                lf = out / "urls.txt"
                lf.write_text("\n".join(links) + "\n", encoding="utf-8")
                link_args = ["--links-file", str(lf)]
            else:
                link_args = [links[0]]
            argv = ["dy.py", *link_args, "-o", str(out)]
            if use_links_file:
                argv.append("--keep-audio")   # 保留暂存目录以便断言
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(dy, "fetch_one", side_effect=fake_fetch), \
                 mock.patch.object(dy, "run", side_effect=fake_run), \
                 contextlib.redirect_stderr(io.StringIO()):
                rc = dy.main()
            tr = [c for c in calls if any("dy_transcribe.py" in str(p) for p in c)]
            md = [c for c in calls if any("dy_tomd.py" in str(p) for p in c)]
            staging = list((out / ".artifacts" / "audio_batch").glob("*.mp3"))
            return rc, tr, md, staging, audio

    def test_single_link_runs_transcribe(self):
        rc, tr, md, staging, audio = self._run_pipeline([DOUYIN])
        self.assertEqual(rc, 0)
        self.assertEqual(len(tr), 1, "单条模式必须调用 dy_transcribe.py")
        self.assertIn(str(audio), tr[0])
        self.assertTrue(tr[0][tr[0].index("-o") + 1].endswith("7653.json"))
        self.assertEqual(len(md), 1)
        self.assertEqual(staging, [], "单条模式不应复制到批量暂存目录")

    def test_batch_still_uses_staging_and_single_transcribe_call(self):
        second = "https://v.douyin.com/def456/"
        rc, tr, md, staging, audio = self._run_pipeline(
            [DOUYIN, second], use_links_file=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(tr), 1, "批量模式模型只加载一次")
        self.assertTrue(any("audio_batch" in str(p) for p in tr[0]))
        self.assertEqual(len(staging), 2)
        self.assertEqual(len(md), 2)


class BundleFlagTest(unittest.TestCase):
    """两文件交付：默认不加 --single-file；标注 JSON 只在单条模式透传。"""

    def _md_cmd(self, extra):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            audio = out / "sample.mp3"
            audio.write_bytes(b"fake-audio")
            meta = {"aweme_id": "7653", "title": "测试", "author": "某作者",
                    "audio_path": str(audio)}
            calls = []

            def fake_run(cmd, desc, quiet=False):
                calls.append(list(cmd))
                return completed()

            argv = ["dy.py", DOUYIN, "-o", str(out), *extra]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(dy, "fetch_one",
                                   return_value=(meta, audio, dy.STATUS_OK)), \
                 mock.patch.object(dy, "run", side_effect=fake_run), \
                 contextlib.redirect_stderr(io.StringIO()):
                rc = dy.main()
            self.assertEqual(rc, 0)
            md = [c for c in calls if any("dy_tomd.py" in str(p) for p in c)]
            self.assertEqual(len(md), 1)
            return md[0]

    def test_default_uses_two_file_output(self):
        cmd = self._md_cmd([])
        self.assertNotIn("--single-file", cmd)
        self.assertNotIn("--annotations", cmd)

    def test_single_file_flag_forwarded(self):
        self.assertIn("--single-file", self._md_cmd(["--single-file"]))

    def test_annotations_forwarded_in_single_mode(self):
        cmd = self._md_cmd(["--annotations", "/tmp/ann.json"])
        self.assertIn("--annotations", cmd)
        self.assertIn("/tmp/ann.json", cmd)

    def test_batch_rejects_annotations(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            lf = Path(td) / "urls.txt"
            lf.write_text(DOUYIN + "\nhttps://v.douyin.com/def456/\n", encoding="utf-8")
            argv = ["dy.py", "--links-file", str(lf), "--annotations", "/tmp/ann.json"]
            err = io.StringIO()
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(dy, "run") as run, \
                 contextlib.redirect_stderr(err):
                rc = dy.main()
        run.assert_not_called()
        self.assertEqual(rc, 2)
        self.assertIn("--annotations", err.getvalue())


class SummaryAndLinksTest(unittest.TestCase):
    def test_status_summary_groups(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            dy._print_status_summary({
                WX: dy.STATUS_MEDIA_BLOCKED,
                DOUYIN: dy.STATUS_OK,
                "https://example.invalid/x": dy.STATUS_UNSUPPORTED,
            }, quiet=False)
        text = err.getvalue()
        self.assertIn("[状态清单]", text)
        self.assertIn("media_blocked_by_platform", text)
        self.assertIn("unsupported_source", text)
        self.assertIn("ok", text)

    def test_extract_links_dedup_and_comments(self):
        with mock.patch.object(Path, "is_file", return_value=True), \
             mock.patch.object(Path, "read_text", return_value="# 注释\nA\nA\nB\n"):
            links = dy.extract_links(None, "/tmp/urls.txt")
        self.assertEqual(links, ["A", "B"])


_spec_fetch = importlib.util.spec_from_file_location(
    "dy_fetch", ROOT / "scripts" / "dy_fetch.py")
dyfetch = importlib.util.module_from_spec(_spec_fetch)
_spec_fetch.loader.exec_module(dyfetch)


class NormalizeInputTest(unittest.TestCase):
    def test_trailing_cjk_punctuation_is_stripped(self):
        self.assertEqual(
            dyfetch.normalize_input("复制打开抖音 https://v.douyin.com/abc/）。"),
            "https://v.douyin.com/abc/",
        )

    def test_missing_link_raises(self):
        with self.assertRaises(ValueError):
            dyfetch.normalize_input("纯文字没有链接")

    def test_douyin_ytdlp_command_unchanged(self):
        cmd = dyfetch.build_cmd(DOUYIN, Path("/tmp/out"), None, None, True, False)
        self.assertIn("-m", cmd)
        self.assertIn("yt_dlp", cmd)
        self.assertIn("--write-info-json", cmd)
        self.assertIn("-x", cmd)
        self.assertIn("--audio-format", cmd)
        self.assertEqual(cmd[-1], DOUYIN)

    def test_short_url_resolved_to_douyin_long_url(self):
        fake = completed(stdout="HTTP/2 302\r\n"
                                "location: https://www.iesdouyin.com/share/video/7707996226502888740/?x=1\r\n")
        with mock.patch.object(dyfetch.subprocess, "run", return_value=fake):
            got = dyfetch.resolve_short_url("https://v.douyin.com/lCU-HSvIPdA/")
        self.assertEqual(got, "https://www.douyin.com/video/7707996226502888740/")

    def test_short_url_falls_back_to_original_on_failure(self):
        with mock.patch.object(dyfetch.subprocess, "run", side_effect=OSError("no curl")):
            got = dyfetch.resolve_short_url(DOUYIN)
        self.assertEqual(got, DOUYIN)

    def test_long_url_bypasses_resolution(self):
        long = "https://www.douyin.com/video/7653/"
        with mock.patch.object(dyfetch.subprocess, "run") as run:
            got = dyfetch.resolve_short_url(long)
        run.assert_not_called()
        self.assertEqual(got, long)

    def test_tls_error_has_actionable_diagnosis(self):
        advice = dyfetch.diagnose("[generic] Unable to download webpage: "
                                  "[SSL: UNEXPECTED_EOF_WHILE_READING]")
        self.assertIn("TLS", advice)
        self.assertIn("capture", advice)

    def test_fresh_cookies_diagnosis_mentions_argus_and_capture(self):
        advice = dyfetch.diagnose("ERROR: [Douyin] Fresh cookies (not necessarily logged in) are needed")
        self.assertIn("a_bogus", advice)
        self.assertIn("capture", advice)


if __name__ == "__main__":
    unittest.main()
