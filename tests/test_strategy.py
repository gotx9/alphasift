from pathlib import Path

import pytest

from alphasift.strategy import list_strategies, load_all_strategies, load_strategy


def test_disabled_strategies_are_not_listed():
    strategies = load_all_strategies(Path("strategies"))

    assert "dual_low" in strategies
    assert "volume_breakout" in strategies
    assert "shrink_pullback" not in strategies


def test_list_strategies_returns_enabled_strategies_only():
    names = [item.name for item in list_strategies(Path("strategies"))]

    assert names == ["dual_low", "volume_breakout"]


def test_load_all_strategies_allows_repo_local_custom_strategy(tmp_path):
    repo_dir = Path("strategies")
    for src in repo_dir.glob("*.yaml"):
        (tmp_path / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    (tmp_path / "custom_alpha.yaml").write_text(
        "\n".join([
            "name: custom_alpha",
            "display_name: 自定义策略",
            "description: demo",
            "screening:",
            "  enabled: true",
            "  market_scope: [cn]",
        ]),
        encoding="utf-8",
    )

    strategies = load_all_strategies(tmp_path)

    assert "custom_alpha" in strategies


def test_load_strategy_rejects_unknown_hard_filter_key(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text(
        "\n".join([
            "name: broken",
            "display_name: 破损策略",
            "description: demo",
            "screening:",
            "  enabled: true",
            "  market_scope: [cn]",
            "  hard_filters:",
            "    pb_mx: 2.0",
        ]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown keys"):
        load_strategy(path)
