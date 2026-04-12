# -*- coding: utf-8 -*-
"""L1 hard filter — apply strategy hard_filters to snapshot DataFrame."""

import logging

import pandas as pd

from alphasift.models import HardFilterConfig

logger = logging.getLogger(__name__)


class SnapshotFieldMissingError(ValueError):
    """Raised when a configured hard filter cannot be evaluated safely."""


def apply_hard_filters(df: pd.DataFrame, filters: HardFilterConfig) -> pd.DataFrame:
    """Filter snapshot DataFrame by hard conditions. Returns filtered copy."""
    result = df.copy()

    if filters.exclude_st:
        name_col = _find_col(result, ["name", "股票名称", "名称"])
        if not name_col:
            raise SnapshotFieldMissingError(
                "Missing required snapshot column for exclude_st filter: name"
            )
        result = result[~result[name_col].str.contains(r"ST|退", na=False)]

    # Numeric filters — each is optional
    _filter_min(result, ["amount", "成交额"], filters.amount_min)
    _filter_min(result, ["price", "最新价", "现价"], filters.price_min)
    _filter_max(result, ["price", "最新价", "现价"], filters.price_max)
    _filter_min(result, ["total_mv", "总市值"], filters.market_cap_min)
    _filter_max(result, ["total_mv", "总市值"], filters.market_cap_max)
    _filter_min(result, ["pe_ratio", "市盈率"], filters.pe_ttm_min)
    _filter_max(result, ["pe_ratio", "市盈率"], filters.pe_ttm_max)
    _filter_min(result, ["pb_ratio", "市净率"], filters.pb_min)
    _filter_max(result, ["pb_ratio", "市净率"], filters.pb_max)
    _filter_min(result, ["volume_ratio", "量比"], filters.volume_ratio_min)
    _filter_min(result, ["turnover_rate", "换手率"], filters.turnover_rate_min)
    _filter_min(result, ["change_pct", "涨跌幅"], filters.change_pct_min)
    _filter_max(result, ["change_pct", "涨跌幅"], filters.change_pct_max)

    # Warn about filters that require daily K-line data (not available in snapshot)
    _unsupported = []
    if filters.change_60d_min is not None or filters.change_60d_max is not None:
        _unsupported.append("change_60d")
    if filters.require_ma_bullish:
        _unsupported.append("require_ma_bullish")
    if filters.require_price_above_ma20:
        _unsupported.append("require_price_above_ma20")
    if filters.signal_score_min is not None:
        _unsupported.append("signal_score_min")
    if filters.macd_status_whitelist:
        _unsupported.append("macd_status_whitelist")
    if filters.rsi_status_whitelist:
        _unsupported.append("rsi_status_whitelist")
    if _unsupported:
        logger.warning(
            "Filters skipped (require daily K-line data, not available in snapshot): %s",
            ", ".join(_unsupported),
        )

    return result


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _filter_min(df: pd.DataFrame, col_names: list[str], value: float | None) -> None:
    if value is None:
        return
    col = _find_col(df, col_names)
    if not col:
        raise SnapshotFieldMissingError(
            f"Missing required snapshot column for min filter {col_names}: "
            f"configured value={value}"
        )
    series = pd.to_numeric(df[col], errors="coerce")
    df.drop(df[(series < value) | series.isna()].index, inplace=True)


def _filter_max(df: pd.DataFrame, col_names: list[str], value: float | None) -> None:
    if value is None:
        return
    col = _find_col(df, col_names)
    if not col:
        raise SnapshotFieldMissingError(
            f"Missing required snapshot column for max filter {col_names}: "
            f"configured value={value}"
        )
    series = pd.to_numeric(df[col], errors="coerce")
    df.drop(df[(series > value) | series.isna()].index, inplace=True)
