from pathlib import Path

from alphasift.strategy import list_strategies, load_all_strategies


def test_disabled_strategies_are_not_listed():
    strategies = load_all_strategies(Path("strategies"))

    assert "dual_low" in strategies
    assert "volume_breakout" in strategies
    assert "shrink_pullback" not in strategies


def test_list_strategies_returns_enabled_strategies_only():
    names = [item.name for item in list_strategies(Path("strategies"))]

    assert names == ["dual_low", "volume_breakout"]
