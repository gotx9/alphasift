import pandas as pd

from alphasift.snapshot import _normalize


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
            }
        ]
    )

    normalized = _normalize(df, source="efinance")

    assert normalized.loc[0, "pb_ratio"] == 0.8
    assert normalized.loc[0, "pe_ratio"] == 5.2
