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


def test_apply_hard_filters_drops_rows_with_unverifiable_numeric_values():
    df = pd.DataFrame(
        [
            {"name": "示例A", "price": 10.0, "amount": 100_000_000, "pb_ratio": None},
            {"name": "示例B", "price": 10.0, "amount": 100_000_000, "pb_ratio": 1.5},
        ]
    )

    filtered = apply_hard_filters(df, HardFilterConfig(pb_max=2.0))

    assert filtered["name"].tolist() == ["示例B"]
