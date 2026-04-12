# 策略编写指南

## 文件位置

策略文件放在 `strategies/` 目录下，文件名即策略标识（如 `dual_low.yaml`）。

## 最小示例

```yaml
name: my_strategy
display_name: 我的策略
description: 一句话描述策略目标
category: value     # trend / value / pattern / reversal

screening:
  enabled: true
  market_scope: [cn]
  hard_filters:
    exclude_st: true
    amount_min: 50000000
  max_output: 5
```

## 完整 Schema

```yaml
name: string              # 唯一标识（英文下划线）
display_name: string      # 显示名称
description: string       # 策略说明
category: string          # trend / value / pattern / reversal / framework

screening:
  enabled: bool            # 是否启用选股
  market_scope: [string]   # 适用市场，当前仅 [cn]

  hard_filters:            # L1 硬筛条件（全部可选，不填则不筛）
    exclude_st: bool       # 排除 ST
    price_min: float       # 最低价格
    price_max: float       # 最高价格
    amount_min: float      # 最低成交额（元）
    market_cap_min: float  # 最低总市值
    market_cap_max: float  # 最高总市值
    pe_ttm_min: float      # 最低 PE(TTM)
    pe_ttm_max: float      # 最高 PE(TTM)
    pb_min: float          # 最低 PB
    pb_max: float          # 最高 PB
    volume_ratio_min: float    # 最低量比
    turnover_rate_min: float   # 最低换手率
    change_pct_min: float      # 最低涨跌幅
    change_pct_max: float      # 最高涨跌幅
    change_60d_min: float      # 60 日最低涨幅
    change_60d_max: float      # 60 日最高涨幅
    require_ma_bullish: bool   # 要求均线多头排列
    require_price_above_ma20: bool  # 要求价格在 MA20 上方
    signal_score_min: int      # 最低信号得分
    macd_status_whitelist: [string]  # MACD 状态白名单
    rsi_status_whitelist: [string]   # RSI 状态白名单

  tech_weight: float       # 技术分数权重，0-1，默认 0.35
  ranking_hints: string    # 给 LLM 的排序提示（自然语言）
  max_output: int          # 最终输出数量，默认 5
```

## 策略分类说明

| 分类 | 适用场景 | 示例 |
|---|---|---|
| `trend` | 趋势确认与趋势延续 | 缩量回踩、放量突破、多头排列 |
| `value` | 估值驱动的价值筛选 | 双低、高股息、低 PEG |
| `pattern` | 技术形态识别 | 一阳穿三阴、底部放量 |
| `reversal` | 反转信号捕捉 | 超跌反弹、底背离 |

## ranking_hints 编写建议

`ranking_hints` 是发送给 LLM 的自然语言提示，用于指导候选间的相对排序。

好的写法：
- 明确列出优先关注的维度（1、2、3）
- 描述具体的偏好（如"缩量明显"而非"量能良好"）
- 提及风险排除条件

避免的写法：
- 让 LLM 自行发挥选股标准
- 包含精确数值阈值（这些应放在 hard_filters 中）
- 要求 LLM 给出目标价
