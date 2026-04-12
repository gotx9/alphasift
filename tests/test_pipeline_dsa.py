from pathlib import Path

import pandas as pd
import pytest

from alphasift.config import Config
from alphasift.pipeline import screen


def _make_config() -> Config:
    return Config(
        llm_api_key="",
        llm_model="gemini/gemini-2.5-flash",
        llm_base_url="",
        snapshot_source_priority=["em_datacenter"],
        strategies_dir=Path("strategies"),
        dsa_api_url="http://localhost:8000",
        dsa_report_type="detailed",
        dsa_max_picks=2,
        dsa_timeout_sec=120.0,
        dsa_force_refresh=False,
        dsa_notify=False,
    )


def test_screen_requires_dsa_url_when_deep_analysis_enabled(monkeypatch):
    config = _make_config()
    config.dsa_api_url = ""

    df = pd.DataFrame(
        [
            {
                "code": "600519",
                "name": "贵州茅台",
                "price": 10.0,
                "change_pct": 1.0,
                "amount": 200_000_000,
                "total_mv": 10_000_000_000,
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "screen_score": 88.0,
            }
        ]
    )
    monkeypatch.setattr("alphasift.pipeline.fetch_snapshot_with_fallback", lambda sources: df)
    monkeypatch.setattr("alphasift.pipeline.apply_hard_filters", lambda frame, filters: frame)
    monkeypatch.setattr("alphasift.pipeline.compute_screen_scores", lambda frame, cfg: frame)

    with pytest.raises(ValueError):
        screen("dual_low", deep_analysis=True, config=config)


def test_screen_runs_optional_dsa_analysis(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "code": "600519",
                "name": "贵州茅台",
                "price": 10.0,
                "change_pct": 1.0,
                "amount": 200_000_000,
                "total_mv": 10_000_000_000,
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "screen_score": 88.0,
            },
            {
                "code": "000858",
                "name": "五粮液",
                "price": 20.0,
                "change_pct": 2.0,
                "amount": 250_000_000,
                "total_mv": 11_000_000_000,
                "pe_ratio": 11.0,
                "pb_ratio": 1.2,
                "screen_score": 86.0,
            },
        ]
    )

    monkeypatch.setattr("alphasift.pipeline.fetch_snapshot_with_fallback", lambda sources: df)
    monkeypatch.setattr("alphasift.pipeline.apply_hard_filters", lambda frame, filters: frame)
    monkeypatch.setattr("alphasift.pipeline.compute_screen_scores", lambda frame, cfg: frame)

    def fake_analyze(picks, **kwargs):
        picks[0].deep_analysis_status = "completed"
        picks[0].deep_analysis_summary = "建议继续跟踪"
        picks[1].deep_analysis_status = "skipped"
        return picks, []

    monkeypatch.setattr("alphasift.pipeline.analyze_picks_with_dsa", fake_analyze)

    result = screen("dual_low", deep_analysis=True, config=_make_config())

    assert result.deep_analysis_requested is True
    assert result.picks[0].deep_analysis_status == "completed"
    assert result.picks[0].deep_analysis_summary == "建议继续跟踪"
