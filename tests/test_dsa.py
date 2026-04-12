from alphasift.dsa import (
    analyze_picks_with_dsa,
    build_dsa_analyze_url,
    extract_deep_analysis_summary,
)
from alphasift.models import Pick


def test_build_dsa_analyze_url_accepts_base_or_full_endpoint():
    assert build_dsa_analyze_url("http://localhost:8000") == (
        "http://localhost:8000/api/v1/analysis/analyze"
    )
    assert build_dsa_analyze_url("http://localhost:8000/api/v1/analysis/analyze") == (
        "http://localhost:8000/api/v1/analysis/analyze"
    )


def test_extract_deep_analysis_summary_prefers_report_summary_operation_advice():
    result = {
        "query_id": "q1",
        "report": {
            "summary": {
                "operation_advice": "继续观察，等待更好的风险收益比"
            }
        },
    }

    assert extract_deep_analysis_summary(result) == "继续观察，等待更好的风险收益比"


def test_analyze_picks_with_dsa_attaches_results(monkeypatch):
    picks = [
        Pick(rank=1, code="600519", name="贵州茅台", final_score=90, screen_score=90),
        Pick(rank=2, code="000858", name="五粮液", final_score=88, screen_score=88),
    ]

    def fake_call(endpoint, **kwargs):
        return {
            "query_id": f"query-{kwargs['stock_code']}",
            "report": {"summary": {"operation_advice": f"关注 {kwargs['stock_code']}"}},
        }

    monkeypatch.setattr("alphasift.dsa.call_dsa_analysis", fake_call)

    analyzed, degradation = analyze_picks_with_dsa(
        picks,
        run_id="run123",
        api_url="http://localhost:8000",
        max_picks=1,
    )

    assert degradation == []
    assert analyzed[0].deep_analysis_status == "completed"
    assert analyzed[0].deep_analysis_query_id == "query-600519"
    assert analyzed[0].deep_analysis_summary == "关注 600519"
    assert analyzed[1].deep_analysis_status == "skipped"
