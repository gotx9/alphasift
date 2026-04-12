# -*- coding: utf-8 -*-
"""Strategy YAML loader."""

import logging
from pathlib import Path

import yaml

from alphasift.models import (
    HardFilterConfig,
    ScreeningConfig,
    Strategy,
    StrategyInfo,
)

logger = logging.getLogger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BUNDLED_STRATEGIES_DIR = Path(__file__).resolve().parent / "strategies"
_TOP_LEVEL_KEYS = {"name", "display_name", "description", "category", "screening"}
_SCREENING_KEYS = {"enabled", "market_scope", "hard_filters", "tech_weight", "ranking_hints", "max_output"}
_HARD_FILTER_KEYS = set(HardFilterConfig.__dataclass_fields__.keys())


def load_strategy(filepath: Path) -> Strategy:
    """Load a screening strategy from a YAML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid strategy file: {filepath}")

    _raise_unknown_keys(data, _TOP_LEVEL_KEYS, f"strategy file {filepath.name}")

    screening_data = data.get("screening", {})
    if not isinstance(screening_data, dict):
        raise ValueError(f"Invalid screening section in strategy file: {filepath}")
    _raise_unknown_keys(screening_data, _SCREENING_KEYS, f"screening section of {filepath.name}")

    hf_data = screening_data.get("hard_filters", {})
    if not isinstance(hf_data, dict):
        raise ValueError(f"Invalid hard_filters section in strategy file: {filepath}")
    _raise_unknown_keys(hf_data, _HARD_FILTER_KEYS, f"hard_filters section of {filepath.name}")

    hard_filters = HardFilterConfig(**hf_data)

    screening = ScreeningConfig(
        enabled=screening_data.get("enabled", False),
        market_scope=screening_data.get("market_scope", ["cn"]),
        hard_filters=hard_filters,
        tech_weight=screening_data.get("tech_weight", 0.35),
        ranking_hints=screening_data.get("ranking_hints", ""),
        max_output=screening_data.get("max_output", 5),
    )

    return Strategy(
        name=data.get("name", filepath.stem),
        display_name=data.get("display_name", data.get("name", filepath.stem)),
        description=data.get("description", ""),
        category=data.get("category", "trend"),
        screening=screening,
    )


def load_all_strategies(strategies_dir: Path) -> dict[str, Strategy]:
    """Load all strategies from a directory."""
    _validate_strategy_dir_sync(strategies_dir)
    strategies = {}
    if not strategies_dir.is_dir():
        return strategies
    for f in sorted(strategies_dir.glob("*.yaml")):
        try:
            s = load_strategy(f)
            if s.screening.enabled:
                strategies[s.name] = s
        except Exception as e:
            logger.warning("Failed to load strategy %s: %s", f.name, e)
            continue
    return strategies


def list_strategies(strategies_dir: Path | None = None) -> list[StrategyInfo]:
    """List available screening strategies."""
    from alphasift.config import Config

    if strategies_dir is None:
        strategies_dir = Config.from_env().strategies_dir

    strategies = load_all_strategies(strategies_dir)
    return [
        StrategyInfo(
            name=s.name,
            display_name=s.display_name,
            description=s.description,
            category=s.category,
            market_scope=s.screening.market_scope,
        )
        for s in strategies.values()
    ]


def _validate_strategy_dir_sync(strategies_dir: Path) -> None:
    """Fail fast if bundled strategy mirrors drift apart from built-in repo files."""
    resolved = strategies_dir.resolve()
    repo_dir = (_PROJECT_ROOT / "strategies").resolve()
    bundled_dir = _BUNDLED_STRATEGIES_DIR.resolve()
    if resolved != repo_dir or not bundled_dir.is_dir():
        return

    repo_files = {f.name: f for f in repo_dir.glob("*.yaml")}
    bundled_files = {f.name: f for f in bundled_dir.glob("*.yaml")}
    missing_from_repo = bundled_files.keys() - repo_files.keys()
    if missing_from_repo:
        raise RuntimeError(
            "Strategy directories are out of sync: bundled strategies are missing from "
            f"strategies/: {', '.join(sorted(missing_from_repo))}."
        )

    for name, bundled_file in bundled_files.items():
        repo_file = repo_files[name]
        if repo_file.read_bytes() != bundled_files[name].read_bytes():
            raise RuntimeError(
                "Strategy directories are out of sync: "
                f"strategies/{name} does not match alphasift/strategies/{name}."
            )


def _raise_unknown_keys(data: dict, allowed_keys: set[str], context: str) -> None:
    unknown_keys = sorted(set(data.keys()) - allowed_keys)
    if unknown_keys:
        raise ValueError(
            f"Unknown keys in {context}: {', '.join(unknown_keys)}"
        )
