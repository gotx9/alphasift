import pandas as pd

from alphasift.config import Config
from alphasift.evaluate import evaluate_result_against_snapshot, evaluate_saved_runs
from alphasift.models import Pick, ScreenResult
from alphasift.store import load_screen_result, save_screen_result, screen_result_to_jsonl


def test_save_and_load_screen_result(tmp_path):
    result = ScreenResult(
        strategy="dual_low",
        market="cn",
        run_id="run123",
        picks=[Pick(rank=1, code="000001", name="平安银行", final_score=80, screen_score=80, price=10)],
    )

    path = save_screen_result(result, data_dir=tmp_path)
    loaded = load_screen_result("run123", data_dir=tmp_path)

    assert path.name == "run123.json"
    assert loaded.picks[0].code == "000001"
    assert loaded.saved_path == str(path)


def test_screen_result_jsonl_contains_run_and_pick_lines():
    result = ScreenResult(
        strategy="dual_low",
        market="cn",
        run_id="run123",
        picks=[Pick(rank=1, code="000001", name="平安银行", final_score=80, screen_score=80)],
    )

    lines = screen_result_to_jsonl(result)

    assert '"type": "run"' in lines[0]
    assert '"type": "pick"' in lines[1]


def test_evaluate_result_against_snapshot_computes_returns():
    run = ScreenResult(
        strategy="dual_low",
        market="cn",
        run_id="run123",
        picks=[
            Pick(rank=1, code="000001", name="平安银行", final_score=80, screen_score=80, price=10),
            Pick(rank=2, code="600000", name="浦发银行", final_score=70, screen_score=70, price=20),
        ],
    )
    snapshot = pd.DataFrame([
        {"code": "000001", "price": 11},
        {"code": "600000", "price": 18},
    ])
    snapshot.attrs["snapshot_source"] = "test"

    result = evaluate_result_against_snapshot(run, snapshot)

    assert result.average_return_pct == 0.0
    assert result.win_rate == 50.0
    assert result.picks[0].return_pct == 10.0
    assert result.picks[1].return_pct == -10.0


def test_evaluate_result_normalizes_snapshot_and_pick_codes():
    run = ScreenResult(
        strategy="dual_low",
        market="cn",
        run_id="run123",
        picks=[Pick(rank=1, code="SZ000001", name="平安银行", final_score=80, screen_score=80, price=10)],
    )
    snapshot = pd.DataFrame([{"code": 1.0, "price": 11}])

    result = evaluate_result_against_snapshot(run, snapshot)

    assert result.picks[0].status == "ok"
    assert result.picks[0].return_pct == 10.0


def test_evaluate_result_against_snapshot_subtracts_cost_bps():
    run = ScreenResult(
        strategy="dual_low",
        market="cn",
        run_id="run123",
        picks=[Pick(rank=1, code="000001", name="平安银行", final_score=80, screen_score=80, price=10)],
    )
    snapshot = pd.DataFrame([{"code": "000001", "price": 11}])

    result = evaluate_result_against_snapshot(run, snapshot, cost_bps=10)

    assert result.picks[0].return_pct == 9.9


def test_evaluate_result_marks_breakout_follow_through_and_failure():
    run = ScreenResult(
        strategy="volume_breakout",
        market="cn",
        run_id="run123",
        picks=[
            Pick(
                rank=1,
                code="000001",
                name="平安银行",
                final_score=80,
                screen_score=80,
                price=10,
                breakout_20d_pct=0.5,
                consolidation_days_20d=10,
            ),
            Pick(
                rank=2,
                code="600000",
                name="浦发银行",
                final_score=70,
                screen_score=70,
                price=20,
                breakout_20d_pct=0.2,
            ),
        ],
    )
    snapshot = pd.DataFrame([
        {"code": "000001", "price": 10.4},
        {"code": "600000", "price": 19.0},
    ])

    result = evaluate_result_against_snapshot(
        run,
        snapshot,
        follow_through_pct=3.0,
        failed_breakout_pct=-3.0,
    )

    assert result.picks[0].shape_status == "breakout_follow_through"
    assert "consolidation_setup" in result.picks[0].shape_tags
    assert result.picks[1].shape_status == "failed_breakout"


def test_evaluate_result_computes_price_path_metrics():
    run = ScreenResult(
        strategy="dual_low",
        market="cn",
        run_id="run123",
        created_at="2026-04-01T09:30:00",
        picks=[Pick(rank=1, code="000001", name="平安银行", final_score=80, screen_score=80, price=10)],
    )
    snapshot = pd.DataFrame([{"code": "000001", "price": 11}])
    path = pd.DataFrame([
        {"日期": "2026-03-31", "收盘": 9.5, "最高": 9.8, "最低": 9.2},
        {"日期": "2026-04-01", "收盘": 10.2, "最高": 10.5, "最低": 9.7},
        {"日期": "2026-04-02", "收盘": 11.0, "最高": 11.5, "最低": 10.1},
    ])

    result = evaluate_result_against_snapshot(
        run,
        snapshot,
        price_paths={"SZ000001": path},
    )

    pick = result.picks[0]
    assert pick.path_status == "ok"
    assert pick.path_days == 2
    assert pick.path_end_return_pct == 10.0
    assert pick.max_drawdown_pct == -3.0
    assert pick.max_runup_pct == 15.0


def test_evaluate_saved_runs_aggregates_by_strategy(tmp_path, monkeypatch):
    def fake_fetch_daily_history(code, **kwargs):
        if code == "600000":
            return pd.DataFrame([
                {"日期": "2026-04-01", "收盘": 20.0, "最高": 20.5, "最低": 18.0},
                {"日期": "2026-04-02", "收盘": 18.0, "最高": 21.0, "最低": 19.0},
            ])
        return pd.DataFrame([
            {"日期": "2026-04-01", "收盘": 10.0, "最高": 10.5, "最低": 9.5},
            {"日期": "2026-04-02", "收盘": 11.0, "最高": 11.5, "最低": 10.0},
        ])

    monkeypatch.setattr("alphasift.evaluate.fetch_daily_history", fake_fetch_daily_history)
    save_screen_result(
        ScreenResult(
            strategy="dual_low",
            market="cn",
            run_id="run_a",
            created_at="2026-04-01T09:30:00",
            picks=[
                Pick(
                    rank=1,
                    code="000001",
                    name="平安银行",
                    final_score=80,
                    screen_score=80,
                    price=10,
                    llm_sector="银行",
                    llm_theme="低估值修复",
                    llm_tags=["价值"],
                    risk_flags=["低波动"],
                    breakout_20d_pct=0.3,
                )
            ],
        ),
        data_dir=tmp_path,
    )
    save_screen_result(
        ScreenResult(
            strategy="volume_breakout",
            market="cn",
            run_id="run_b",
            created_at="2026-04-01T09:30:00",
            picks=[Pick(rank=1, code="600000", name="浦发银行", final_score=70, screen_score=70, price=20)],
        ),
        data_dir=tmp_path,
    )
    snapshot = pd.DataFrame([
        {"code": "000001", "price": 11},
        {"code": "600000", "price": 18},
    ])
    snapshot.attrs["snapshot_source"] = "test"

    result = evaluate_saved_runs(
        config=Config(llm_api_key="", data_dir=tmp_path),
        current_snapshot=snapshot,
        limit=10,
        cost_bps=0,
        with_price_path=True,
    )

    assert result["summary"]["run_count"] == 2
    assert result["summary"]["win_rate"] == 50.0
    assert result["summary"]["average_return_pct"] == 0.0
    assert result["by_strategy"]["dual_low"]["average_return_pct"] == 10.0
    assert result["by_strategy"]["volume_breakout"]["average_return_pct"] == -10.0
    assert result["portfolio_summary"]["evaluated_run_count"] == 2
    assert result["portfolio_summary"]["average_portfolio_return_pct"] == 0.0
    assert result["portfolio_summary"]["portfolio_win_rate"] == 50.0
    assert result["portfolio_summary"]["average_portfolio_max_drawdown_pct"] == -7.5
    assert result["portfolio_by_strategy"]["dual_low"]["average_portfolio_return_pct"] == 10.0
    assert result["dimensions"]["by_sector"]["银行"]["average_return_pct"] == 10.0
    assert result["dimensions"]["by_theme"]["低估值修复"]["win_rate"] == 100.0
    assert result["dimensions"]["by_tag"]["价值"]["pick_count"] == 1
    assert result["dimensions"]["by_risk_flag"]["低波动"]["average_return_pct"] == 10.0
    assert result["dimensions"]["by_holding_period"]["T+20_plus"]["pick_count"] == 2
    assert result["dimensions"]["by_shape_status"]["breakout_follow_through"]["pick_count"] == 1
    assert result["dimensions"]["by_shape_tag"]["breakout_setup"]["pick_count"] == 1
    assert result["dimensions"]["by_path_status"]["ok"]["pick_count"] == 2
    assert result["summary"]["path_pick_count"] == 2
    assert result["summary"]["average_max_drawdown_pct"] == -7.5
    assert result["cost_bps"] == 0.0
