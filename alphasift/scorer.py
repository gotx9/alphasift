# -*- coding: utf-8 -*-
"""screen_score calculation."""

import pandas as pd

from alphasift.models import ScreeningConfig


def compute_screen_scores(df: pd.DataFrame, config: ScreeningConfig) -> pd.DataFrame:
    """Compute screen_score for each candidate row.

    Adds a 'screen_score' column (0-100). Higher is better.
    """
    result = df.copy()
    result["screen_score"] = 0.0

    snapshot_score = _compute_snapshot_score(result)
    tech_score = _compute_tech_score(result)

    tw = config.tech_weight
    result["screen_score"] = snapshot_score * (1 - tw) + tech_score * tw

    return result


def _compute_snapshot_score(df: pd.DataFrame) -> pd.Series:
    """Score based on snapshot fundamentals (0-100).

    Components:
    - PE ratio: lower is better (for value), normalized
    - PB ratio: lower is better, normalized
    - Turnover rate: moderate is best
    - Amount (liquidity): higher is better, log-scaled
    - Change pct: near zero or moderate positive preferred
    """
    score = pd.Series(50.0, index=df.index)
    n = len(df)
    if n == 0:
        return score

    # PE score: lower PE (positive PE) is better — rank-based
    if "pe_ratio" in df.columns:
        pe = pd.to_numeric(df["pe_ratio"], errors="coerce")
        # Only score positive PE (profitable companies)
        valid_pe = pe[(pe > 0) & (pe < 500)]
        if len(valid_pe) > 0:
            pe_rank = pe.rank(ascending=True, na_option="bottom", pct=True)
            # Lower PE = higher rank pct = higher score
            pe_score = pe_rank * 100
            pe_score = pe_score.where(pe > 0, 30)  # penalize negative PE
            score = score * 0.7 + pe_score * 0.3

    # PB score: lower PB is better
    if "pb_ratio" in df.columns:
        pb = pd.to_numeric(df["pb_ratio"], errors="coerce")
        valid_pb = pb[(pb > 0) & (pb < 50)]
        if len(valid_pb) > 0:
            pb_rank = pb.rank(ascending=True, na_option="bottom", pct=True)
            pb_score = pb_rank * 100
            pb_score = pb_score.where(pb > 0, 30)
            score = score * 0.8 + pb_score * 0.2

    # Amount (liquidity) score: log-scaled, higher is better
    if "amount" in df.columns:
        amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        amt_positive = amt[amt > 0]
        if len(amt_positive) > 0:
            import numpy as np
            log_amt = np.log10(amt.clip(lower=1))
            amt_rank = log_amt.rank(ascending=True, pct=True)
            score = score * 0.85 + amt_rank * 100 * 0.15

    # Turnover score: moderate turnover (1-8%) is ideal
    if "turnover_rate" in df.columns:
        tr = pd.to_numeric(df["turnover_rate"], errors="coerce").fillna(0)
        # Bell curve around 3-5%
        tr_score = pd.Series(50.0, index=df.index)
        tr_score = tr_score.where(tr <= 0, 100 - ((tr - 4).abs() * 8).clip(upper=60))
        score = score * 0.9 + tr_score * 0.1

    return score.clip(0, 100)


def _compute_tech_score(df: pd.DataFrame) -> pd.Series:
    """Score based on technical features (0-100).

    Uses available columns like volume_ratio, change_pct patterns.
    Full tech scoring (MA structure, MACD/RSI) needs daily data,
    which is not in the snapshot — scored conservatively here.
    """
    score = pd.Series(50.0, index=df.index)
    n = len(df)
    if n == 0:
        return score

    # Volume ratio: moderate expansion is positive (1.0 - 3.0)
    if "volume_ratio" in df.columns:
        vr = pd.to_numeric(df["volume_ratio"], errors="coerce").fillna(1.0)
        vr_score = pd.Series(50.0, index=df.index)
        # 1.0-3.0 is good, >5 is excessive
        vr_score = vr_score.where(
            vr <= 0,
            (100 - ((vr - 2.0).abs() * 15).clip(upper=50))
        )
        score = score * 0.6 + vr_score * 0.4

    # Change pct: moderate positive is better than extreme
    if "change_pct" in df.columns:
        chg = pd.to_numeric(df["change_pct"], errors="coerce").fillna(0)
        # Moderate positive change (0-5%) scores highest
        chg_score = pd.Series(50.0, index=df.index)
        chg_score = chg_score.where(
            chg.isna(),
            (70 + chg * 3).clip(lower=20, upper=95)
        )
        score = score * 0.7 + chg_score * 0.3

    return score.clip(0, 100)
