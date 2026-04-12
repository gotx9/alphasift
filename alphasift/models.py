# -*- coding: utf-8 -*-
"""Data models."""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HardFilterConfig:
    exclude_st: bool = True
    price_min: float | None = None
    price_max: float | None = None
    amount_min: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    pe_ttm_min: float | None = None
    pe_ttm_max: float | None = None
    pb_min: float | None = None
    pb_max: float | None = None
    volume_ratio_min: float | None = None
    turnover_rate_min: float | None = None
    change_pct_min: float | None = None
    change_pct_max: float | None = None
    change_60d_min: float | None = None
    change_60d_max: float | None = None
    require_ma_bullish: bool = False
    require_price_above_ma20: bool = False
    signal_score_min: int | None = None
    macd_status_whitelist: list[str] | None = None
    rsi_status_whitelist: list[str] | None = None


@dataclass
class ScreeningConfig:
    enabled: bool = False
    market_scope: list[str] = field(default_factory=lambda: ["cn"])
    hard_filters: HardFilterConfig = field(default_factory=HardFilterConfig)
    tech_weight: float = 0.35
    ranking_hints: str = ""
    max_output: int = 5


@dataclass
class Strategy:
    name: str
    display_name: str
    description: str
    category: str = "trend"
    screening: ScreeningConfig = field(default_factory=ScreeningConfig)


@dataclass
class StrategyInfo:
    """Strategy metadata for list_strategies()."""
    name: str
    display_name: str
    description: str
    category: str
    market_scope: list[str]


@dataclass
class Pick:
    rank: int
    code: str
    name: str
    final_score: float
    screen_score: float
    llm_score: float | None = None
    ranking_reason: str = ""
    risk_summary: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    amount: float = 0.0
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    deep_analysis_status: str = "not_requested"
    deep_analysis_query_id: str = ""
    deep_analysis_summary: str = ""
    deep_analysis_error: str = ""
    deep_analysis_result: dict[str, Any] | None = None
    deep_analysis_signal_score: int | None = None
    deep_analysis_sentiment_score: int | None = None
    deep_analysis_operation_advice: str = ""
    deep_analysis_trend_prediction: str = ""
    deep_analysis_risk_flags: list[str] = field(default_factory=list)


@dataclass
class ScreenResult:
    strategy: str
    market: str
    snapshot_count: int = 0
    after_filter_count: int = 0
    picks: list[Pick] = field(default_factory=list)
    run_id: str = ""
    llm_ranked: bool = False
    degradation: list[str] = field(default_factory=list)
    deep_analysis_requested: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
