# -*- coding: utf-8 -*-
"""Configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_DIR = Path(__file__).resolve().parent


def _load_env_file() -> None:
    """Load .env from cwd or project root if present."""
    candidates = [Path.cwd() / ".env", _PROJECT_ROOT / ".env"]
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _parse_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_strategies_dir() -> Path:
    """Find strategies directory: env var > project root > package bundled."""
    env_dir = os.getenv("STRATEGIES_DIR")
    if env_dir:
        return Path(env_dir)
    # Dev mode: project root
    project_dir = _PROJECT_ROOT / "strategies"
    if project_dir.is_dir():
        return project_dir
    # Installed: inside package
    return _PACKAGE_DIR / "strategies"


@dataclass
class Config:
    """Runtime configuration, loaded from env vars."""

    # LLM
    llm_api_key: str = ""
    llm_model: str = "gemini/gemini-2.5-flash"
    llm_base_url: str = ""

    # Snapshot data source priority
    snapshot_source_priority: list[str] = field(
        default_factory=lambda: ["efinance", "akshare_em", "em_datacenter"]
    )

    # Strategy directory
    strategies_dir: Path = field(default_factory=_default_strategies_dir)

    # Optional: DSA API for L3 deep analysis
    dsa_api_url: str = ""
    dsa_report_type: str = "detailed"
    dsa_max_picks: int = 3
    dsa_timeout_sec: float = 120.0
    dsa_force_refresh: bool = False
    dsa_notify: bool = False

    # Data directory
    data_dir: Path = _PROJECT_ROOT / "data"

    @classmethod
    def from_env(cls) -> "Config":
        _load_env_file()
        source_str = os.getenv("SNAPSHOT_SOURCE_PRIORITY", "efinance,akshare_em,em_datacenter")
        sources = [s.strip() for s in source_str.split(",") if s.strip()]
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash"),
            llm_base_url=os.getenv("LLM_BASE_URL", ""),
            snapshot_source_priority=sources,
            strategies_dir=_default_strategies_dir(),
            dsa_api_url=os.getenv("DSA_API_URL", ""),
            dsa_report_type=os.getenv("DSA_REPORT_TYPE", "detailed"),
            dsa_max_picks=max(1, int(os.getenv("DSA_MAX_PICKS", "3"))),
            dsa_timeout_sec=float(os.getenv("DSA_TIMEOUT_SEC", "120")),
            dsa_force_refresh=_parse_bool_env("DSA_FORCE_REFRESH", False),
            dsa_notify=_parse_bool_env("DSA_NOTIFY", False),
            data_dir=Path(os.getenv("ALPHASIFT_DATA_DIR", str(_PROJECT_ROOT / "data"))),
        )
