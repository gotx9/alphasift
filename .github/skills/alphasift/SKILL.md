---
name: alphasift
description: "自动选股 Skill。Use when: 用户要按策略筛选 A 股、列出可用策略、运行双低/缩量回踩/放量突破等选股。通过 alphasift CLI 或 Python 接口输出候选股票列表。"
---

# alphasift — 自动选股 Skill

按策略筛选、评分并排序 A 股候选股票。

## Use When

- 用户要列出当前可用策略
- 用户要按 `dual_low`、`shrink_pullback`、`volume_breakout` 这类策略筛选 A 股
- 用户要拿到结构化 JSON 结果，供后续 agent 继续分析

## Preconditions

alphasift 包已安装在当前 Python 环境中。如未安装，先执行：

```bash
pip install -e .
```

如需 LLM 排序，需要设置环境变量或项目根目录 `.env` 中的 `LLM_API_KEY`。

## Operations

### 1. 查看可用策略

```bash
alphasift strategies
```

### 2. 执行选股

```bash
alphasift screen dual_low --no-llm
alphasift screen shrink_pullback --no-llm
alphasift screen volume_breakout --max-output 10
```

### 3. 通过 Python 调用

```python
from alphasift import screen, list_strategies

list_strategies()
screen("dual_low", market="cn", use_llm=False)
```

## Output

返回 `ScreenResult` JSON，核心字段有：
- `strategy`: 策略名
- `market`: 市场
- `snapshot_count`: 全市场股票数
- `after_filter_count`: 硬筛后剩余数量
- `picks`: 推荐列表
- `llm_ranked`: 是否经过 LLM 排序
- `degradation`: 降级信息

## Boundaries

- 当前只支持 `market="cn"`
- 当前没有实现 `get_result`
- 当前没有实现 L3 `deep_analysis`
- 部分依赖日 K 的条件会被跳过，详见仓库根目录 [README.md](../../../README.md)
