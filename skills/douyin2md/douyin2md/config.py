"""统一配置读取。

优先级（高 → 低）::

    1. 环境变量 ``DOUYIN2MD_*``
    2. 命令行 ``--config`` / 环境变量 ``DOUYIN2MD_CONFIG`` 指定的 JSON 文件
    3. ``~/.douyin2md/config.json``
    4. 仓库根 ``config.json``（通常不存在，用 ``config.example.json`` 复制）
    5. 内置默认值

配置文件只放非敏感项。API Key 一律通过 ``SILICONFLOW_API_KEY`` /
``OPENAI_API_KEY`` 环境变量提供，绝不写入仓库或配置文件。
本模块不访问网络、不安装依赖、不执行 ``scripts/`` 下的任何脚本。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()

DEFAULTS: Dict[str, Any] = {
    "home": "~/.douyin2md",
    "output_dir": "./notes",
    "engine": "auto",
    "model": "",
    "language": "zh",
    "device": "auto",
    "provider": "",
    "cookies": "",
    "cookies_from_browser": "",
    "api_base": "",
    "keep_audio": False,
    "no_timestamps": False,
    "no_frontmatter": False,
}

STRING_ENV = {
    "DOUYIN2MD_HOME": "home",
    "DOUYIN2MD_OUTPUT_DIR": "output_dir",
    "DOUYIN2MD_ENGINE": "engine",
    "DOUYIN2MD_MODEL": "model",
    "DOUYIN2MD_LANGUAGE": "language",
    "DOUYIN2MD_DEVICE": "device",
    "DOUYIN2MD_PROVIDER": "provider",
    "DOUYIN2MD_COOKIES": "cookies",
    "DOUYIN2MD_COOKIES_FROM_BROWSER": "cookies_from_browser",
    "DOUYIN2MD_API_BASE": "api_base",
}

BOOL_ENV = {
    "DOUYIN2MD_KEEP_AUDIO": "keep_audio",
    "DOUYIN2MD_NO_TIMESTAMPS": "no_timestamps",
    "DOUYIN2MD_NO_FRONTMATTER": "no_frontmatter",
}

SECRET_ENV = ("SILICONFLOW_API_KEY", "OPENAI_API_KEY")


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _candidates(explicit: Optional[str]) -> list[Path]:
    items = [
        explicit,
        os.environ.get("DOUYIN2MD_CONFIG"),
        str(HOME / ".douyin2md" / "config.json"),
        str(ROOT / "config.json"),
    ]
    return [Path(item).expanduser() for item in items if item]


def config_path(explicit: Optional[str] = None) -> Optional[Path]:
    """返回第一个真实存在的配置文件路径；都不存在时返回 None。"""
    for path in _candidates(explicit):
        if path.is_file():
            return path
    return None


def load_config(explicit: Optional[str] = None) -> Dict[str, Any]:
    """加载生效配置。未知字段会被忽略，不会污染子脚本参数。"""
    cfg = dict(DEFAULTS)
    path = config_path(explicit)
    if path is not None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"配置文件无法解析: {path} ({exc.__class__.__name__})") from exc
        if isinstance(data, dict):
            for key, value in data.items():
                if key in cfg:
                    cfg[key] = value

    for env_name, key in STRING_ENV.items():
        value = os.environ.get(env_name)
        if value:
            cfg[key] = value
    for env_name, key in BOOL_ENV.items():
        value = os.environ.get(env_name)
        if value:
            cfg[key] = _truthy(value)
    return cfg


def redacted(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """返回可安全打印的配置（不输出任何密钥值）。"""
    safe = dict(cfg)
    for env_name in SECRET_ENV:
        safe[env_name] = "set" if os.environ.get(env_name) else "not set"
    return safe


def pick(value: Any, key: str, cfg: Dict[str, Any]) -> Any:
    """命令行显式值优先，否则回落到配置。"""
    return value if value is not None else cfg[key]
