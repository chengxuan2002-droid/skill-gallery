"""来源判定与提取状态契约。

这是接口层（``douyin2md/cli.py``）与实现层（``scripts/*.py``）共用的**唯一判定源**。
纯逻辑模块：不联网、不读文件、不依赖第三方库，可离线单测。

设计要点：
- 旧行为完全保留：判定为 ``douyin`` 的链接仍走原 yt-dlp 三段式流水线。
- 微信视频号预览页只做「元数据 + 高清封面」的只读提取，状态为 ``metadata_only``。
- 未知来源给出可解释的 ``unsupported_source``，不再把链接丢给 yt-dlp 换一句
  ``Unsupported URL``。
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

DOUYIN = "douyin"
WEIXIN_CHANNELS = "weixin-channels"
UNSUPPORTED = "unsupported"
SUPPORTED_SOURCES = (DOUYIN, WEIXIN_CHANNELS)

# 结果状态（dy.py 批量清单与分级提示使用）
STATUS_OK = "ok"
STATUS_METADATA_ONLY = "metadata_only"
STATUS_MEDIA_BLOCKED = "media_blocked_by_platform"
STATUS_NEED_LOGIN = "need_login"
STATUS_UNSUPPORTED = "unsupported_source"
ALL_STATUSES = (
    STATUS_OK,
    STATUS_METADATA_ONLY,
    STATUS_MEDIA_BLOCKED,
    STATUS_NEED_LOGIN,
    STATUS_UNSUPPORTED,
)

# 模板层使用的提取契约：ok 表示内容完整，其余为降级/受阻状态
EXTRACTION_FULL = "ok"
EXTRACTION_METADATA_ONLY = "metadata_only"
EXTRACTION_NEED_LOGIN = "need_login"

# 排除汉字、CJK 标点与全角字符，避免分享文案尾随的「。）」被吞进 URL
_URL_RE = re.compile(r"https?://[^\s\u3000-\u303f\uff00-\uffef\u4e00-\u9fff]+")
_TRAILING = ".,;:!?)]}>\"'。，；：！？、）】》"
_DOUYIN_HOSTS = {
    "v.douyin.com", "www.douyin.com", "douyin.com", "m.douyin.com",
    "www.iesdouyin.com", "iesdouyin.com",
}
_CHANNELS_HOSTS = {"channels.weixin.qq.com"}


def extract_url(text) -> str:
    """从分享文案里抽出第一条 URL；找不到时抛 ValueError。"""
    m = _URL_RE.search(str(text or "").strip())
    if not m:
        raise ValueError("未在输入中找到链接")
    return m.group(0).rstrip(_TRAILING)


def detect_source(text) -> str:
    """判定输入属于哪种来源。``text`` 可以是链接，也可以是整段分享文案。"""
    try:
        url = extract_url(text)
    except ValueError:
        return UNSUPPORTED
    try:
        parsed = urlparse(url)
    except ValueError:
        return UNSUPPORTED
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()
    if host in _DOUYIN_HOSTS or host.endswith(".douyin.com"):
        return DOUYIN
    if host in _CHANNELS_HOSTS:
        return WEIXIN_CHANNELS
    # weixin.qq.com/sph/<id> 是视频号短链；其它 weixin.qq.com 路径不属于本适配器
    if host == "weixin.qq.com" and path.startswith("/sph/"):
        return WEIXIN_CHANNELS
    return UNSUPPORTED


def source_advice(source: str) -> str:
    """面向用户的来源级提示。"""
    return {
        DOUYIN: "按抖音链路处理（元数据 + 音频 + 转写）。",
        WEIXIN_CHANNELS: "微信视频号预览页仅提供元数据与封面，将输出 metadata-only 文稿；"
                         "如需逐字稿，请在微信客户端保存视频/录屏后用 transcribe 处理本地文件。",
        UNSUPPORTED: "不支持的链接来源。本地音视频请改用 `transcribe` 子命令；"
                     "本技能仅支持抖音链接与微信视频号预览链接。",
    }.get(source, "未知来源。")


def status_advice(status: str) -> str:
    """批量清单里的分级提示。"""
    return {
        STATUS_OK: "完整产物（含转写）",
        STATUS_METADATA_ONLY: "元数据 + 封面摘要（无音视频，平台侧限制）",
        STATUS_MEDIA_BLOCKED: "平台限制媒体获取，仅元数据",
        STATUS_NEED_LOGIN: "需要浏览器上下文/登录态，或内容不可访问",
        STATUS_UNSUPPORTED: "来源不支持，未处理",
    }.get(status, "未知状态")


def meta_id(meta: dict) -> str:
    """统一取内容 ID。

    抖音旧 meta 用 ``aweme_id``；新适配器用 ``source_id``。两者都没有时，
    用链接哈希兜底，避免批量流程里出现 ``None`` 文件名。
    """
    for key in ("aweme_id", "source_id", "id"):
        value = meta.get(key)
        if value and str(value) not in {"None", "-", ""}:
            return str(value)
    url = str(meta.get("webpage_url") or meta.get("resolved_url") or "")
    if url:
        return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return "unknown"
