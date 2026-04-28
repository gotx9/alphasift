import pandas as pd
import pytest

from alphasift.filter import SnapshotFieldMissingError, apply_hard_filters
from alphasift.models import HardFilterConfig


def test_apply_hard_filters_fails_when_required_snapshot_field_is_missing():
    df = pd.DataFrame(
        [
            {"name": "示例A", "price": 10.0, "amount": 100_000_000, "pe_ratio": 12.0},
        ]
    )

    with pytest.raises(SnapshotFieldMissingError):
        apply_hard_filters(df, HardFilterConfig(pb_max=2.0))


def test_apply_hard_filters_accepts_empty_frame_without_name_column():
    filtered = apply_hard_filters(pd.DataFrame(), HardFilterConfig())

    assert filtered.empty


def test_apply_hard_filters_drops_rows_with_unverifiable_numeric_values():
    df = pd.DataFrame(
        [
            {"name": "示例A", "price": 10.0, "amount": 100_000_000, "pb_ratio": None},
            {"name": "示例B", "price": 10.0, "amount": 100_000_000, "pb_ratio": 1.5},
        ]
    )

    filtered = apply_hard_filters(df, HardFilterConfig(pb_max=2.0))

    assert filtered["name"].tolist() == ["示例B"]


def test_apply_hard_filters_returns_empty_before_later_missing_fields():
    df = pd.DataFrame(
        [
            {"name": "示例A", "price": 10.0, "amount": 1},
        ]
    )

    filtered = apply_hard_filters(
        df,
        HardFilterConfig(amount_min=100_000_000, pb_max=2.0),
    )

    assert filtered.empty


def test_apply_hard_filters_fails_when_required_daily_features_are_missing():
    df = pd.DataFrame(
        [
            {"name": "示例A", "price": 10.0, "amount": 100_000_000},
        ]
    )

    with pytest.raises(SnapshotFieldMissingError, match="daily feature"):
        apply_hard_filters(df, HardFilterConfig(require_ma_bullish=True))


def test_apply_hard_filters_uses_daily_features_when_present():
    df = pd.DataFrame(
        [
            {"name": "示例A", "price": 10.0, "amount": 100_000_000, "ma_bullish": True, "signal_score": 70},
            {"name": "示例B", "price": 11.0, "amount": 100_000_000, "ma_bullish": False, "signal_score": 80},
        ]
    )

    result = apply_hard_filters(
        df,
        HardFilterConfig(require_ma_bullish=True, signal_score_min=65),
    )

    assert result["name"].tolist() == ["示例A"]


def test_apply_hard_filters_uses_daily_shape_features_when_present():
    df = pd.DataFrame(
        [
            {
                "name": "突破A",
                "price": 10.0,
                "amount": 100_000_000,
                "breakout_20d_pct": 0.8,
                "range_20d_pct": 18,
                "volume_ratio_20d": 1.8,
                "body_pct": 1.2,
                "pullback_to_ma20_pct": 4.0,
                "consolidation_days_20d": 10,
            },
            {
                "name": "伪突破B",
                "price": 11.0,
                "amount": 100_000_000,
                "breakout_20d_pct": -3.5,
                "range_20d_pct": 42,
                "volume_ratio_20d": 0.8,
                "body_pct": -0.5,
                "pullback_to_ma20_pct": 14.0,
                "consolidation_days_20d": 3,
            },
        ]
    )

    result = apply_hard_filters(
        df,
        HardFilterConfig(
            breakout_20d_pct_min=-1.0,
            range_20d_pct_max=30,
            volume_ratio_20d_min=1.2,
            body_pct_min=0,
            pullback_to_ma20_pct_max=8,
            consolidation_days_20d_min=8,
        ),
    )

    assert result["name"].tolist() == ["突破A"]
