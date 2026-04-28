import pandas as pd
import pytest

from alphasift.snapshot import _normalize, fetch_snapshot_with_fallback


def test_normalize_efinance_maps_pb_ratio():
    df = pd.DataFrame(
        [
            {
                "股票代码": "000001",
                "股票名称": "平安银行",
                "最新价": "10.00",
                "涨跌幅": "1.23",
                "成交额": "123456789",
                "总市值": "1000000000",
                "流通市值": "800000000",
                "动态市盈率": "5.2",
                "市净率": "0.8",
                "量比": "1.1",
                "换手率": "2.5",
                "所属行业": "银行",
                "概念题材": "中特估,低估值",
            }
        ]
    )

    normalized = _normalize(df, source="efinance")

    assert normalized.loc[0, "pb_ratio"] == 0.8
    assert normalized.loc[0, "pe_ratio"] == 5.2
    assert normalized.loc[0, "industry"] == "银行"
    assert normalized.loc[0, "concepts"] == "中特估,低估值"


def test_fetch_snapshot_with_fallback_attaches_source_errors(monkeypatch):
    def fake_fetch(source):
        if source == "bad":
            raise RuntimeError("bad source")
        return pd.DataFrame([{"code": "000001", "name": "示例", "price": 10.0}])

    monkeypatch.setattr("alphasift.snapshot.fetch_cn_snapshot", fake_fetch)

    df = fetch_snapshot_with_fallback(["bad", "good"])

    assert df.attrs["source_errors"] == ["bad: bad source"]


def test_fetch_snapshot_with_fallback_raises_all_errors(monkeypatch):
    monkeypatch.setattr(
        "alphasift.snapshot.fetch_cn_snapshot",
        lambda source: (_ for _ in ()).throw(RuntimeError(source)),
    )

    with pytest.raises(RuntimeError, match="a: a; b: b"):
        fetch_snapshot_with_fallback(["a", "b"])
