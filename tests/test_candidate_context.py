import pandas as pd

from alphasift.candidate_context import (
    classify_announcement_categories,
    classify_negative_events,
    collect_candidate_context,
)


def test_collect_candidate_context_uses_requested_providers(monkeypatch):
    class FakeAkshare:
        @staticmethod
        def stock_news_em(symbol):
            return pd.DataFrame([
                {"发布时间": "2026-04-28", "文章来源": "测试", "新闻标题": f"{symbol} 获资金关注"},
            ])

        @staticmethod
        def stock_individual_fund_flow(stock, market):
            return pd.DataFrame([
                {"日期": "2026-04-28", "主力净流入-净额": "1000万", "主力净流入-净占比": "3.5%"},
            ])

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    candidates = pd.DataFrame([{"code": 1.0, "name": "平安银行"}])

    rows, errors = collect_candidate_context(
        candidates,
        providers=["news", "fund_flow"],
    )

    assert errors == []
    assert rows[0]["code"] == "000001"
    assert "获资金关注" in rows[0]["news"]
    assert "主力净流入" in rows[0]["fund_flow"]
    assert rows[0]["source_count"] == 2
    assert rows[0]["source_confidence"] == 1.0
    assert rows[0]["source_weight_score"] == 1.0
    assert "新闻:" in rows[0]["context_summary"]
    assert isinstance(rows[0]["event_tags"], list)
    assert isinstance(rows[0]["negative_event_flags"], list)


def test_collect_candidate_context_records_row_errors(monkeypatch):
    class FakeAkshare:
        @staticmethod
        def stock_news_em(symbol):
            raise ConnectionError("disconnect")

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    candidates = pd.DataFrame([{"code": "000001", "name": "平安银行"}])

    rows, errors = collect_candidate_context(candidates, providers=["news"])

    assert rows == []
    assert "000001 news" in errors[0]


def test_collect_candidate_context_uses_cache(monkeypatch, tmp_path):
    class FakeAkshare:
        calls = 0

        @staticmethod
        def stock_news_em(symbol):
            FakeAkshare.calls += 1
            return pd.DataFrame([
                {"发布时间": "2026-04-28", "新闻标题": f"{symbol} 首次抓取"},
            ])

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    candidates = pd.DataFrame([{"code": "000001", "name": "平安银行"}])

    first, _ = collect_candidate_context(
        candidates,
        providers=["news"],
        cache_dir=tmp_path,
    )
    second, _ = collect_candidate_context(
        candidates,
        providers=["news"],
        cache_dir=tmp_path,
    )

    assert FakeAkshare.calls == 1
    assert second == first


def test_collect_candidate_context_enriches_legacy_cache(tmp_path):
    cache = tmp_path / "000001_news.json"
    cache.write_text(
        """
        {
          "cached_at": "2999-01-01T00:00:00",
          "row": {
            "code": "000001",
            "name": "平安银行",
            "news": "公司公告回购计划，收到监管问询函",
            "context_summary": "新闻:旧摘要"
          }
        }
        """,
        encoding="utf-8",
    )
    candidates = pd.DataFrame([{"code": "000001", "name": "平安银行"}])

    rows, errors = collect_candidate_context(
        candidates,
        providers=["news"],
        cache_dir=tmp_path,
    )

    assert errors == []
    assert "回购增持" in rows[0]["event_tags"]
    assert "监管" in rows[0]["negative_event_flags"]
    assert "负面风险:监管" in rows[0]["context_summary"]


def test_collect_candidate_context_partial_sources_have_partial_confidence(monkeypatch):
    class FakeAkshare:
        @staticmethod
        def stock_news_em(symbol):
            return pd.DataFrame([
                {"发布时间": "2026-04-28", "新闻标题": f"{symbol} 获资金关注"},
            ])

        @staticmethod
        def stock_individual_fund_flow(stock, market):
            return pd.DataFrame()

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    candidates = pd.DataFrame([{"code": "000001", "name": "平安银行"}])

    rows, errors = collect_candidate_context(
        candidates,
        providers=["news", "fund_flow"],
    )

    assert errors == []
    assert rows[0]["source_count"] == 1
    assert rows[0]["source_confidence"] == 0.5
    assert rows[0]["source_weight_score"] == 0.4643


def test_collect_candidate_context_accepts_custom_source_weights(monkeypatch):
    class FakeAkshare:
        @staticmethod
        def stock_news_em(symbol):
            return pd.DataFrame([
                {"发布时间": "2026-04-28", "新闻标题": f"{symbol} 获资金关注"},
            ])

        @staticmethod
        def stock_zh_a_disclosure_report_cninfo(**kwargs):
            return pd.DataFrame()

    monkeypatch.setitem(__import__("sys").modules, "akshare", FakeAkshare)
    candidates = pd.DataFrame([{"code": "000001", "name": "平安银行"}])

    rows, errors = collect_candidate_context(
        candidates,
        providers=["news", "announcement"],
        source_weights={"news": 0.5, "announcement": 2.0},
    )

    assert errors == []
    assert rows[0]["source_confidence"] == 0.5
    assert rows[0]["source_weight_score"] == 0.2


def test_classify_negative_events_from_announcement_text():
    row = {
        "code": "000001",
        "announcement": "股东拟减持股份，公司收到监管问询函",
        "news": "公司公告回购计划",
    }

    flags = classify_negative_events(row)

    assert "减持" in flags
    assert "监管" in flags


def test_classify_announcement_categories_from_announcement_text():
    row = {
        "code": "000001",
        "announcement": "公司发布年度业绩预增公告，并披露股份回购方案",
    }

    categories = classify_announcement_categories(row)

    assert "业绩" in categories
    assert "回购增持" in categories
