import pandas as pd
import pytest

from alphasift.daily import compute_daily_features, enrich_daily_features, fetch_daily_history


def test_compute_daily_features_adds_trend_fields():
    closes = [10 + i * 0.1 for i in range(80)]
    hist = pd.DataFrame({
        "日期": pd.date_range("2026-01-01", periods=80).astype(str),
        "开盘": [value - 0.1 for value in closes],
        "最高": [value + 0.2 for value in closes],
        "最低": [value - 0.2 for value in closes],
        "收盘": closes,
        "成交量": [1000] * 79 + [1800],
    })

    features = compute_daily_features(hist)

    assert features["daily_data_points"] == 80
    assert features["change_60d"] > 0
    assert features["ma_bullish"] is True
    assert features["price_above_ma20"] is True
    assert features["signal_score"] >= 65
    assert -1.0 <= features["breakout_20d_pct"] <= 0.0
    assert features["range_20d_pct"] < 20
    assert features["volume_ratio_20d"] == 1.8
    assert features["body_pct"] > 0
    assert features["pullback_to_ma20_pct"] > 0
    assert features["consolidation_days_20d"] >= 8


def test_fetch_daily_history_retries_transient_source_errors(monkeypatch):
    calls = {"count": 0}

    class FakeAkshare:
        @staticmethod
        def stock_zh_a_hist(**kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise ConnectionError("temporary disconnect")
            return pd.DataFrame({
                "日期": pd.date_range("2026-01-01", periods=40).astype(str),
                "收盘": [10 + i * 0.1 for i in range(40)],
            })

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    monkeypatch.setattr("alphasift.daily.time.sleep", lambda seconds: None)

    result = fetch_daily_history("000001", retries=1)

    assert calls["count"] == 2
    assert len(result) == 40


def test_fetch_daily_history_reports_retry_count(monkeypatch):
    class FakeAkshare:
        @staticmethod
        def stock_zh_a_hist(**kwargs):
            raise ConnectionError("temporary disconnect")

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    monkeypatch.setattr("alphasift.daily.time.sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="after 2 attempts"):
        fetch_daily_history("000001", retries=1)


def test_enrich_daily_features_keeps_successful_rows_when_one_fetch_fails(monkeypatch):
    candidates = pd.DataFrame([
        {"code": "000001", "name": "平安银行"},
        {"code": "600000", "name": "浦发银行"},
    ])

    def fake_fetch_daily_history(code, **kwargs):
        if code == "600000":
            raise ConnectionError("remote disconnected")
        return pd.DataFrame({
            "日期": pd.date_range("2026-01-01", periods=80).astype(str),
            "收盘": [10 + i * 0.1 for i in range(80)],
        })

    monkeypatch.setattr("alphasift.daily.fetch_daily_history", fake_fetch_daily_history)

    result = enrich_daily_features(candidates, max_rows=2)

    assert result.attrs["daily_success_count"] == 1
    assert len(result.attrs["daily_errors"]) == 1
    assert "600000" in result.attrs["daily_errors"][0]
    assert result.loc[0, "daily_data_points"] == 80
    assert pd.isna(result.loc[1, "daily_data_points"])
