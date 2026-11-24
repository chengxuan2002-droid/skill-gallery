"""P2-2 带会话差异验证的离线单测（不联网、不启动浏览器）。"""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "wx_session_check", ROOT / "scripts" / "wx_session_check.py")
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


def payload(extra=None):
    feed = {"description": "文案", "coverUrl": "https://x/c.jpg"}
    if extra:
        feed.update(extra)
    return {"data": {"feedInfo": feed, "authorInfo": {"nickname": "云知大道"}}}


class ReportTest(unittest.TestCase):
    def info(self, weixin=True):
        return {"cookie_file": "cookies.txt", "cookie_count": 3,
                "cookie_domains": ["channels.weixin.qq.com"] if weixin else ["example.com"],
                "session_looks_like_weixin": weixin}

    def test_no_new_stream_fields_supports_platform_limit(self):
        r = sc.build_report(payload(), "可扫码前往微信观看此内容",
                            payload(), "可扫码前往微信观看此内容", self.info())
        self.assertEqual(r["new_stream_fields"], [])
        self.assertIn("平台侧客户端能力限制", r["conclusion"])
        self.assertEqual(r["before"]["feed_keys"], r["after"]["feed_keys"])
        self.assertEqual(r["after"]["page_hint"], "扫码前往微信观看")

    def test_new_stream_field_changes_conclusion(self):
        r = sc.build_report(payload(), "", payload({"videoUrl": "https://x/v.mp4"}), "",
                            self.info())
        self.assertEqual(r["new_stream_fields"], ["videoUrl"])
        self.assertIn("会话可能参与", r["conclusion"])

    def test_new_key_is_reported(self):
        r = sc.build_report(payload(), "", payload({"duration": 120}), "", self.info())
        self.assertIn("duration", r["new_keys"])

    def test_missing_feed_info_is_inconclusive(self):
        r = sc.build_report({}, "", payload(), "", self.info())
        self.assertFalse(r["before"]["has_feed_info"])
        self.assertIn("未验证", r["conclusion"])

    def test_report_never_contains_cookie_values(self):
        secret = "YOUR_SESSION_VALUE_HERE"
        info = self.info()
        r = sc.build_report(payload(), "", payload(), "", info)
        blob = json.dumps(r, ensure_ascii=False)
        self.assertNotIn(secret, blob)
        self.assertTrue(r["redacted"])
        self.assertIn("不输出 cookie 值", r["compliance"])

    def test_non_weixin_cookies_are_flagged_as_connectivity_only(self):
        r = sc.build_report(payload(), "", payload(), "", self.info(weixin=False))
        self.assertFalse(r["session_looks_like_weixin"])
        self.assertTrue(any("不能用于判定" in w for w in r["warnings"]))


class CookieTest(unittest.TestCase):
    def test_load_netscape_ignores_comments_and_bad_lines(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("broken line\n")
            f.write(".weixin.qq.com\tTRUE\t/\tTRUE\t0\tsessionid\tVALUE\n")
            p = Path(f.name)
        try:
            cookies = sc.load_netscape(p)
            self.assertEqual(len(cookies), 1)
            self.assertEqual(cookies[0]["name"], "sessionid")
            self.assertEqual(cookies[0]["domain"], "weixin.qq.com")
            self.assertTrue(sc.looks_like_weixin_session(sc.cookie_domains(cookies)))
        finally:
            p.unlink()

    def test_douyin_domains_are_not_weixin_session(self):
        self.assertFalse(sc.looks_like_weixin_session([".douyin.com", "www.douyin.com"]))


class AuthorizationTest(unittest.TestCase):
    def test_refuses_without_authorize_and_never_touches_network(self):
        argv = ["wx_session_check.py", "https://weixin.qq.com/sph/AiQ59Q9O3y",
                "--cookies", "/tmp/fake-cookies.txt"]
        err = io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(sc, "capture_once") as cap, \
             contextlib.redirect_stderr(err):
            rc = sc.main()
        self.assertEqual(rc, 2)
        cap.assert_not_called()
        self.assertIn("refused", err.getvalue())


if __name__ == "__main__":
    unittest.main()
