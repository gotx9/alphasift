---
name: alphasift
description: "自动选股 Skill。Use when: 用户要按策略筛选 A 股、列出可用策略、运行双低/放量突破等选股。通过 alphasift CLI 或 Python 接口输出候选股票列表。"
---

# alphasift — 自动选股 Skill

按策略筛选、评分并排序 A 股候选股票。

## Use When

- 用户要列出当前可用策略
- 用户要按 `dual_low`、`volume_breakout` 这类策略筛选 A 股
- 用户要拿到结构化 JSON 结果，供后续 agent 继续分析

## Preconditions

- 当前只支持 `market="cn"`
- 需要先在仓库根目录安装包：`pip install -e .`
- 如需 LLM 排序，设置环境变量或项目根目录 `.env` 中的 `LLM_API_KEY`
- 如需 L3 深度分析，设置 `DSA_API_URL`；这里的 `DSA` 指外部项目 `daily_stock_analysis`，默认调用 `POST /api/v1/analysis/analyze`

## Operations

### 1. 列出策略

```bash
alphasift strategies
```

### 2. 执行选股

```bash
alphasift screen dual_low --no-llm
alphasift screen volume_breakout --max-output 10
alphasift screen dual_low --deep-analysis
```

### 3. Python 调用

```python
from alphasift import list_strategies, screen

list_strategies()
screen("dual_low", market="cn", use_llm=False)
```

## Output

返回 `ScreenResult` JSON，核心字段有：
- `strategy`
- `market`
- `snapshot_count`
- `after_filter_count`
- `picks`
- `llm_ranked`
- `degradation`

每个 `Pick` 包含：
- `rank`
- `code`
- `name`
- `final_score`
- `screen_score`
- `ranking_reason`
- `risk_summary`
- `price`
- `change_pct`
- `amount`
- `pe_ratio`
- `pb_ratio`
- `deep_analysis_status`
- `deep_analysis_summary`
- `deep_analysis_result`
- `deep_analysis_signal_score`
- `deep_analysis_sentiment_score`
- `deep_analysis_operation_advice`
- `deep_analysis_trend_prediction`
- `deep_analysis_risk_flags`

## Boundaries

- 当前没有实现 `get_result`
- L3 `deep_analysis` 依赖外部 `daily_stock_analysis`/DSA 服务可用
- DSA 只在最终入围候选上调用，用于最后阶段的风险覆盖与名次修正，不参与全市场初筛
- 依赖日 K 的策略暂未开放，关键快照字段缺失时会直接失败，避免静默偏离策略定义
