import pandas as pd

from alphasift.models import ScreeningConfig
from alphasift.scorer import compute_screen_scores


def test_value_factor_favors_lower_positive_pe_and_pb():
    df = pd.DataFrame(
        [
            {
                "code": "low",
                "pe_ratio": 5.0,
                "pb_ratio": 0.6,
                "amount": 100_000_000,
                "turnover_rate": 3.0,
                "volume_ratio": 1.2,
                "change_pct": 0.0,
            },
            {
                "code": "high",
                "pe_ratio": 15.0,
                "pb_ratio": 2.0,
                "amount": 100_000_000,
                "turnover_rate": 3.0,
                "volume_ratio": 1.2,
                "change_pct": 0.0,
            },
        ]
    )

    scored = compute_screen_scores(
        df,
        ScreeningConfig(factor_weights={"value": 1.0}),
    ).set_index("code")

    assert scored.loc["low", "screen_score"] > scored.loc["high", "screen_score"]
    assert scored.loc["low", "factor_value_score"] > scored.loc["high", "factor_value_score"]


def test_scoring_profile_can_tighten_intraday_chase_penalty():
    df = pd.DataFrame([{"code": "hot", "change_pct": 6.0}])

    default_score = compute_screen_scores(
        df,
        ScreeningConfig(factor_weights={"momentum": 1.0}),
    ).loc[0, "factor_momentum_score"]
    stricter_score = compute_screen_scores(
        df,
        ScreeningConfig(
            factor_weights={"momentum": 1.0},
            scoring_profile={
                "momentum_chase_start_pct": 1.0,
                "momentum_chase_penalty_slope": 40.0,
            },
        ),
    ).loc[0, "factor_momentum_score"]

    assert stricter_score < default_score


def test_theme_heat_factor_uses_board_heat_score_when_available():
    df = pd.DataFrame([
        {"code": "hot", "board_heat_score": 82},
        {"code": "cold", "board_heat_score": 35},
    ])

    scored = compute_screen_scores(
        df,
        ScreeningConfig(factor_weights={"theme_heat": 1.0}),
    ).set_index("code")

    assert scored.loc["hot", "factor_theme_heat_score"] > scored.loc["cold", "factor_theme_heat_score"]
    assert scored.loc["hot", "screen_score"] > scored.loc["cold", "screen_score"]


def test_theme_heat_factor_uses_reliable_trend_and_cooling_signal():
    df = pd.DataFrame([
        {
            "code": "warming",
            "board_heat_score": 60,
            "board_heat_trend_score": 10,
            "board_heat_persistence_score": 100,
            "board_heat_cooling_score": 0,
            "board_heat_observations": 2,
        },
        {
            "code": "cooling",
            "board_heat_score": 60,
            "board_heat_trend_score": -10,
            "board_heat_persistence_score": 40,
            "board_heat_cooling_score": 8,
            "board_heat_observations": 2,
        },
        {
            "code": "thin",
            "board_heat_score": 60,
            "board_heat_trend_score": 10,
            "board_heat_persistence_score": 100,
            "board_heat_cooling_score": 0,
            "board_heat_observations": 1,
        },
    ])

    scored = compute_screen_scores(
        df,
        ScreeningConfig(factor_weights={"theme_heat": 1.0}),
    ).set_index("code")

    assert scored.loc["warming", "factor_theme_heat_score"] > scored.loc["thin", "factor_theme_heat_score"]
    assert scored.loc["thin", "factor_theme_heat_score"] > scored.loc["cooling", "factor_theme_heat_score"]
