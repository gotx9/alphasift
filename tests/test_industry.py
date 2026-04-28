import pandas as pd

from alphasift.industry import enrich_industry_concepts, load_board_heat_trends, load_industry_map, save_industry_map


def test_load_industry_map_from_csv(tmp_path):
    path = tmp_path / "industry.csv"
    path.write_text(
        "code,industry,concepts,board_heat_score,board_heat_summary\n"
        "000001,银行,低估值,72.5,银行:+1.20%:rank=3\n",
        encoding="utf-8",
    )

    mapping = load_industry_map(path)

    assert mapping["000001"]["industry"] == "银行"
    assert mapping["000001"]["concepts"] == "低估值"
    assert mapping["000001"]["board_heat_score"] == 72.5
    assert mapping["000001"]["board_heat_summary"] == "银行:+1.20%:rank=3"


def test_load_industry_map_normalizes_numeric_and_suffixed_codes(tmp_path):
    path = tmp_path / "industry.json"
    path.write_text(
        """
        [
          {"code": 1.0, "industry": "银行"},
          {"code": "SZ000002", "concepts": "地产链"}
        ]
        """,
        encoding="utf-8",
    )

    mapping = load_industry_map(path)

    assert mapping["000001"]["industry"] == "银行"
    assert mapping["000002"]["concepts"] == "地产链"


def test_enrich_industry_concepts_from_file(tmp_path):
    path = tmp_path / "industry.csv"
    path.write_text(
        "code,industry,concepts,board_heat_score,board_heat_summary\n"
        "000001,银行,低估值,72.5,银行:+1.20%:rank=3\n"
        "600000,银行,中特估,61.0,银行:+0.20%:rank=12\n",
        encoding="utf-8",
    )
    df = pd.DataFrame([
        {"code": "000001", "name": "平安银行"},
        {"code": "600000", "name": "浦发银行", "concepts": "破净"},
    ])

    enriched, notes = enrich_industry_concepts(df, map_files=[path])

    assert enriched.loc[0, "industry"] == "银行"
    assert enriched.loc[0, "concepts"] == "低估值"
    assert enriched.loc[0, "board_heat_score"] == 72.5
    assert "银行:+1.20%" in enriched.loc[0, "board_heat_summary"]
    assert enriched.loc[1, "concepts"] == "破净,中特估"
    assert any("industry/concepts enrichment applied" in item for item in notes)


def test_enrich_industry_concepts_loads_companion_heat_history(tmp_path):
    path = tmp_path / "industry.csv"
    path.write_text(
        "code,industry,concepts,board_heat_score,board_heat_summary\n"
        "000001,银行,低估值,72.5,银行:+1.20%:rank=3\n",
        encoding="utf-8",
    )
    history = tmp_path / "industry.csv.history.jsonl"
    history.write_text(
        '{"generated_at":"2026-04-27T10:00:00","board":"银行","max_board_heat_score":60}\n'
        '{"generated_at":"2026-04-27T11:00:00","board":"银行","max_board_heat_score":999}\n'
        'not-json\n'
        '{"generated_at":"2026-04-28T10:00:00","board":"银行","max_board_heat_score":72.5}\n',
        encoding="utf-8",
    )

    trends = load_board_heat_trends(history)
    enriched, notes = enrich_industry_concepts(
        pd.DataFrame([{"code": "000001", "name": "平安银行"}]),
        map_files=[path],
    )

    assert trends["银行"]["board_heat_trend_score"] == 12.5
    assert trends["银行"]["board_heat_latest_score"] == 72.5
    assert trends["银行"]["board_heat_persistence_score"] == 100.0
    assert trends["银行"]["board_heat_state"] == "warming"
    assert enriched.loc[0, "board_heat_latest_score"] == 72.5
    assert enriched.loc[0, "board_heat_trend_score"] == 12.5
    assert enriched.loc[0, "board_heat_persistence_score"] == 100.0
    assert enriched.loc[0, "board_heat_observations"] == 2
    assert enriched.loc[0, "board_heat_state"] == "warming"
    assert any("board heat trends loaded" in item for item in notes)


def test_load_board_heat_trends_uses_rolling_window_and_cooling_signal(tmp_path):
    history = tmp_path / "industry.csv.history.jsonl"
    history.write_text(
        '{"generated_at":"2026-04-24T10:00:00","board":"AI算力","max_board_heat_score":82}\n'
        '{"generated_at":"2026-04-25T10:00:00","board":"AI算力","max_board_heat_score":78}\n'
        '{"generated_at":"2026-04-26T10:00:00","board":"AI算力","max_board_heat_score":70}\n'
        '{"generated_at":"2026-04-27T10:00:00","board":"AI算力","max_board_heat_score":62}\n'
        '{"generated_at":"2026-04-28T10:00:00","board":"AI算力","max_board_heat_score":55}\n',
        encoding="utf-8",
    )

    trends = load_board_heat_trends(history, window_size=3, hot_score=60, cooling_threshold=5)

    assert trends["AI算力"]["board_heat_latest_score"] == 55
    assert trends["AI算力"]["board_heat_trend_score"] == -15
    assert trends["AI算力"]["board_heat_cooling_score"] == 7
    assert trends["AI算力"]["board_heat_persistence_score"] == 66.6667
    assert trends["AI算力"]["board_heat_observations"] == 3
    assert trends["AI算力"]["board_heat_state"] == "cooling"


def test_save_industry_map_round_trips_csv(tmp_path):
    path = tmp_path / "industry_map.csv"

    save_industry_map(
        {
            "000001": {
                "industry": "银行",
                "concepts": "低估值",
                "board_heat_score": 70,
                "board_heat_latest_score": 71,
                "board_heat_persistence_score": 80,
                "board_heat_cooling_score": 2,
                "board_heat_summary": "银行:+1.00%:rank=5",
                "board_heat_state": "persistent_hot",
            }
        },
        path,
    )
    mapping = load_industry_map(path)

    assert mapping["000001"]["industry"] == "银行"
    assert mapping["000001"]["concepts"] == "低估值"
    assert mapping["000001"]["board_heat_score"] == 70
    assert mapping["000001"]["board_heat_latest_score"] == 71
    assert mapping["000001"]["board_heat_persistence_score"] == 80
    assert mapping["000001"]["board_heat_cooling_score"] == 2
    assert mapping["000001"]["board_heat_state"] == "persistent_hot"
