# -*- coding: utf-8 -*-
"""Main pipeline — orchestrates L1 → L2 → result."""

import logging
import uuid
from pathlib import Path

import pandas as pd

from alphasift.config import Config
from alphasift.dsa import analyze_picks_with_dsa, apply_dsa_overlay
from alphasift.filter import apply_hard_filters
from alphasift.models import Pick, ScreenResult
from alphasift.ranker import rank_candidates
from alphasift.scorer import compute_screen_scores
from alphasift.snapshot import fetch_snapshot_with_fallback
from alphasift.strategy import load_all_strategies

logger = logging.getLogger(__name__)


def screen(
    strategy: str,
    *,
    market: str = "cn",
    max_output: int | None = None,
    use_llm: bool = True,
    deep_analysis: bool = False,
    deep_analysis_max_picks: int | None = None,
    config: Config | None = None,
) -> ScreenResult:
    """Execute stock screening with the given strategy.

    Args:
        strategy: Strategy name (matches a YAML file in strategies/).
        market: Market scope, currently only "cn".
        max_output: Override max output count from strategy.
        use_llm: Whether to use LLM for L2 ranking.
        deep_analysis: Whether to call DSA for L3 deep analysis (requires dsa_api_url).
        deep_analysis_max_picks: Override max number of picks sent to DSA.
        config: Runtime config. Defaults to Config.from_env().

    Returns:
        ScreenResult with ranked picks.
    """
    if config is None:
        config = Config.from_env()

    if market != "cn":
        raise ValueError("Only market='cn' is currently supported")

    run_id = uuid.uuid4().hex[:12]
    degradation: list[str] = []

    # 1. Load strategy
    strategies = load_all_strategies(config.strategies_dir)
    if strategy not in strategies:
        available = ", ".join(strategies.keys()) or "(none)"
        raise ValueError(f"Strategy '{strategy}' not found. Available: {available}")

    strat = strategies[strategy]
    screening = strat.screening
    if market not in screening.market_scope:
        raise ValueError(
            f"Strategy '{strategy}' does not support market '{market}'. "
            f"Supported: {', '.join(screening.market_scope)}"
        )
    output_count = max_output or screening.max_output

    # 2. Fetch snapshot
    df = fetch_snapshot_with_fallback(config.snapshot_source_priority)
    snapshot_count = len(df)

    # 3. L1 hard filter
    df = apply_hard_filters(df, screening.hard_filters)
    after_filter_count = len(df)

    if df.empty:
        return ScreenResult(
            strategy=strategy,
            market=market,
            snapshot_count=snapshot_count,
            after_filter_count=0,
            run_id=run_id,
            degradation=["No candidates after hard filter"],
        )

    # 4. Compute screen_score
    df = compute_screen_scores(df, screening)
    df = df.sort_values("screen_score", ascending=False)

    # 5. Take Top K for LLM ranking
    top_k = min(output_count * 4, len(df))
    df_top = df.head(top_k)

    # 6. Build Pick list
    picks = _df_to_picks(df_top)

    # 7. L2 LLM ranking
    llm_ranked = False
    if use_llm and config.llm_api_key:
        picks = rank_candidates(
            picks,
            screening.ranking_hints,
            config.llm_api_key,
            config.llm_model,
            config.llm_base_url,
        )
        llm_ranked = any(p.llm_score is not None for p in picks)
        if not llm_ranked:
            degradation.append("LLM ranking failed: fell back to screen_score")
            for i, p in enumerate(picks):
                p.rank = i + 1
                p.final_score = p.screen_score
    else:
        if use_llm and not config.llm_api_key:
            degradation.append("LLM ranking skipped: no API key")
        for i, p in enumerate(picks):
            p.rank = i + 1
            p.final_score = p.screen_score

    # 8. Trim to max_output
    picks = picks[:output_count]

    # 9. Optional L3 deep analysis via DSA
    if deep_analysis:
        if not config.dsa_api_url:
            raise ValueError("deep_analysis requested but DSA_API_URL is not configured")
        picks, dsa_degradation = analyze_picks_with_dsa(
            picks,
            run_id=run_id,
            api_url=config.dsa_api_url,
            report_type=config.dsa_report_type,
            max_picks=deep_analysis_max_picks or config.dsa_max_picks,
            timeout_sec=config.dsa_timeout_sec,
            force_refresh=config.dsa_force_refresh,
            notify=config.dsa_notify,
        )
        picks = apply_dsa_overlay(picks)
        degradation.extend(dsa_degradation)

    return ScreenResult(
        strategy=strategy,
        market=market,
        snapshot_count=snapshot_count,
        after_filter_count=after_filter_count,
        picks=picks,
        run_id=run_id,
        llm_ranked=llm_ranked,
        degradation=degradation,
        deep_analysis_requested=deep_analysis,
    )


def _df_to_picks(df: pd.DataFrame) -> list[Pick]:
    """Convert DataFrame rows to Pick objects."""
    picks = []
    for i, (_, row) in enumerate(df.iterrows()):
        picks.append(Pick(
            rank=i + 1,
            code=str(row.get("code", row.get("代码", ""))),
            name=str(row.get("name", row.get("名称", row.get("股票名称", "")))),
            screen_score=float(row.get("screen_score", 0)),
            final_score=float(row.get("screen_score", 0)),
            price=float(row.get("price", row.get("最新价", 0)) or 0),
            change_pct=float(row.get("change_pct", row.get("涨跌幅", 0)) or 0),
            amount=float(row.get("amount", row.get("成交额", 0)) or 0),
            pe_ratio=_safe_float(row.get("pe_ratio", row.get("市盈率"))),
            pb_ratio=_safe_float(row.get("pb_ratio", row.get("市净率"))),
        ))
    return picks


def _safe_float(v) -> float | None:
    if v is None or v == "" or v == "-":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
