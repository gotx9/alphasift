from alphasift.dsa import (
    apply_dsa_overlay,
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


def test_extract_deep_analysis_summary_prefers_analysis_summary_over_operation_advice():
    result = {
        "query_id": "q1",
        "report": {
            "summary": {
                "analysis_summary": "这是更完整的分析摘要",
                "operation_advice": "继续观察，等待更好的风险收益比"
            }
        },
    }

    assert extract_deep_analysis_summary(result) == "这是更完整的分析摘要"


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
    assert analyzed[0].deep_analysis_operation_advice == "关注 600519"
    assert analyzed[1].deep_analysis_status == "skipped"


def test_apply_dsa_overlay_uses_structured_scores_for_final_rerank():
    picks = [
        Pick(rank=1, code="AAA", name="A", final_score=80, screen_score=80),
        Pick(rank=2, code="BBB", name="B", final_score=82, screen_score=82),
    ]

    picks[0].deep_analysis_status = "completed"
    picks[0].deep_analysis_signal_score = 82
    picks[0].deep_analysis_sentiment_score = 88
    picks[0].deep_analysis_operation_advice = "买入"
    picks[0].deep_analysis_trend_prediction = "看多"

    picks[1].deep_analysis_status = "completed"
    picks[1].deep_analysis_signal_score = 40
    picks[1].deep_analysis_sentiment_score = 38
    picks[1].deep_analysis_operation_advice = "观望"
    picks[1].deep_analysis_trend_prediction = "震荡"
    picks[1].deep_analysis_risk_flags = ["乖离率过高"]

    reranked = apply_dsa_overlay(picks)

    assert reranked[0].code == "AAA"
    assert reranked[0].rank == 1
    assert reranked[1].code == "BBB"
    assert reranked[1].rank == 2
    assert reranked[0].final_score > reranked[1].final_score
