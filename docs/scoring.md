# 评分体系

## screen_score 组成

`screen_score` 是选股专用的横向评分，用于在 L1 筛选后对候选进行排序。

| 子分数 | 说明 | 示例因子 |
|---|---|---|
| `snapshot_score` | 快照特征归一化 | 估值、流动性、涨跌幅、换手率、市值 |
| `tech_feature_score` | 技术特征 | 均线结构、MACD/RSI 状态、趋势得分 |
| `strategy_bonus` | 策略特定加分 | 价值/动量/反转偏好 |
| `risk_penalty` | 风险扣分 | 高波动、字段缺失、异常成交 |

### 权重

各子分数权重由策略 YAML 中的 `tech_weight` 控制：

```
final_screen_score = snapshot_score × (1 - tech_weight)
                   + tech_feature_score × tech_weight
                   + strategy_bonus
                   - risk_penalty
```

## 与单股分析分数的关系

| 分数 | 来源 | 用途 |
|---|---|---|
| `signal_score` | DSA 技术分析 | 单股趋势评判 |
| `sentiment_score` | DSA LLM 分析 | 单股综合判断 |
| `screen_score` | alphasift | 全市场横向筛选排序 |

`signal_score` 可以作为 `tech_feature_score` 的输入之一，但不能直接等于 `screen_score`。

当前实现中，DSA 不参与 L1 全市场初筛；它只在最终入围候选上调用，并在最后阶段作为 overlay 使用：
- `screen_score` 仍决定进入最终名单前的主排序
- DSA 返回的 `signal_score`、`sentiment_score`、`operation_advice`、趋势判断和风险因子会对最终 `final_score` 做修正
- 因此 DSA 更适合作为低频、高成本的终审层，而不是高频主链评分器

## LLM 排序 (L2)

LLM 只在 Top K 候选上做相对排序，输入为：

1. 候选的 screen_score 和关键指标
2. 策略 YAML 中的 `ranking_hints`
3. 新闻/情报摘要（如有）

LLM 输出：

1. 重排后的排名
2. 每个候选的排序理由
3. 风险摘要

## 风险覆盖层

风险覆盖独立于评分，作为 veto 或 penalty 施加：

| 检查项 | 行为 |
|---|---|
| 流动性不足 | veto（直接排除） |
| ST / 退市风险 | veto |
| 连板过热 / 涨停不可买 | veto |
| 财报/公告窗口 | penalty（扣分） |
| 板块过度集中 | penalty（同板块限数量） |
