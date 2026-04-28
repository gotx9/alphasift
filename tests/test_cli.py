import json

from alphasift.cli import _append_industry_cache_history, _write_industry_cache_metadata


def test_write_industry_cache_metadata_supports_output_without_suffix(tmp_path):
    output = tmp_path / "industry_map"

    metadata_path = _write_industry_cache_metadata(
        output,
        provider="akshare",
        max_boards=3,
        rows=12,
        notes=["ok"],
        generated_at="2026-04-28T10:00:00",
        history_path=tmp_path / "industry_map.history.jsonl",
    )

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata_path.name == "industry_map.meta.json"
    assert data["provider"] == "akshare"
    assert data["max_boards"] == 3
    assert data["rows"] == 12
    assert data["history_path"].endswith("industry_map.history.jsonl")


def test_append_industry_cache_history_groups_board_summaries(tmp_path):
    output = tmp_path / "industry_map.csv"

    history_path = _append_industry_cache_history(
        output,
        mapping={
            "000001": {"board_heat_summary": "银行:+1.20%:rank=3", "board_heat_score": 72.5},
            "600000": {"board_heat_summary": "银行:+1.20%:rank=3", "board_heat_score": 70.0},
            "000002": {"board_heat_summary": "地产:+0.50%:rank=8", "board_heat_score": 55.0},
        },
        generated_at="2026-04-28T10:00:00",
    )

    rows = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_board = {row["board"]: row for row in rows}
    assert history_path.name == "industry_map.csv.history.jsonl"
    assert by_board["银行"]["code_count"] == 2
    assert by_board["银行"]["max_board_heat_score"] == 72.5
    assert by_board["地产"]["code_count"] == 1
