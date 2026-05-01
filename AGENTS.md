# AlphaSift AGENTS.md

## Project Overview

AlphaSift is a Chinese stock screening tool ("自动选股 Skill") that filters, scores, and ranks A-share candidates from the entire market. It follows a 3-layer funnel architecture:
- **L1**: Hard filter via strategy YAML rules
- **L2**: LLM ranking with structured output
- **L3**: Optional post-analysis (builtin scorecard, optional DSA/external HTTP)

## CLI Commands

```bash
# Install
pip install -e .

# List available strategies
alphasift strategies

# Run screening (no LLM)
alphasift screen dual_low --no-llm

# Run screening (with LLM ranking)
alphasift screen balanced_alpha

# Run with market context
alphasift screen balanced_alpha --context "今日券商板块放量"

# Save run for later evaluation
alphasift screen dual_low --no-llm --save-run

# List saved runs
alphasift runs

# Evaluate a saved run (T+N evaluation)
alphasift evaluate <run_id> --explain

# Batch evaluate multiple runs
alphasift evaluate-batch --limit 20 --explain

# Audit strategy configuration
alphasift audit

# Build industry heat map cache
alphasift industry-cache --output data/industry_map.csv --explain
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline.py -v

# Run with coverage
pytest --cov=alphasift tests/
```

## Key Architecture Notes

- **Data Sources**: `efinance` → `akshare_em` → `em_datacenter` (automatic fallback)
- **Strategy Files**: Located in both `strategies/` (dev) and `alphasift/strategies/` (installed)
- **LLM Configuration**: Supports LiteLLM format; compatible with `daily_stock_analysis` env vars
- **Post-Analyzers**: `scorecard` (default), `dsa`, `external_http` — only run on final candidates

## Important Environment Variables

| Variable | Purpose |
|----------|---------|
| `LITELLM_MODEL` | Primary LLM model (e.g., `gemini/gemini-2.5-flash`) |
| `GEMINI_API_KEY` / `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` | LLM provider keys |
| `DSA_API_URL` | External DSA service for L3 analysis (optional) |
| `SNAPSHOT_SOURCE_PRIORITY` | Data source order (default: `efinance,akshare_em,em_datacenter`) |
| `POST_ANALYZERS` | L3 analyzers (default: `scorecard`) |
| `INDUSTRY_MAP_FILES` | Local industry/concept mapping CSV |

## Python API

```python
from alphasift import screen, list_strategies, evaluate_saved_run

# List strategies
list_strategies()

# Run screening
result = screen("dual_low", use_llm=False)
for p in result.picks:
    print(f"{p.rank}. {p.code} {p.name} score={p.final_score:.1f}")

# Evaluate saved run
evaluate_saved_run("<run_id>")
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `snapshot.py` | Fetch market data from 3 sources with fallback |
| `filter.py` | L1 hard filtering based on strategy YAML |
| `scorer.py` | Calculate factor scores |
| `ranker.py` | L2 LLM ranking with structured output |
| `risk.py` | Independent risk layer (overheat, low confidence penalties) |
| `post_analysis.py` | L3 pluggable analyzers |
| `store.py` | Save/load screening runs |
| `evaluate.py` | T+N backtesting evaluation |

## Known Quirks

- Data sources `efinance` and `akshare_em` are unavailable during non-trading hours (weekends/holidays); automatically falls back to `em_datacenter`
- LLM ranking is optional; use `--no-llm` for fast filtering
- DSA is an optional L3 analyzer, not a default dependency
- T+N evaluation uses saved snapshot price vs. latest price — not a rigorous backtest

## Key Files

- `SKILL.md` — Skill description for AI Agents
- `README.md` — Full documentation
- `docs/strategy-guide.md` — How to write custom strategies
- `.env.example` — Environment variable template