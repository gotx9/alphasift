# alphasift

从全市场中按策略筛选、评分、排序，输出值得关注的候选股票。

为 AI Agent 设计的自动选股 Skill。

## 免责声明

- 本项目仅用于学习、研究与工程实验，不构成任何投资建议、收益承诺或买卖指引。
- 项目输出依赖第三方行情数据、外部模型与策略参数，可能存在延迟、缺失、错误或不符合实际交易条件的情况。
- LLM 生成的排序理由、风险摘要等内容仅供参考，不能替代人工研究、合规审查与独立投资判断。
- 使用者应自行评估策略风险、交易成本、流动性、公告时点与市场环境，并对自己的决策与结果负责。

## 快速开始

```bash
# 安装
pip install -e .

# 配置（必须）
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY（LLM 排序需要）

# 列出可用策略
alphasift strategies

# 执行选股（不使用 LLM 排序）
alphasift screen dual_low --no-llm

# 执行选股（使用 LLM 排序，需要配置 LLM_API_KEY）
alphasift screen dual_low

# 执行选股后调用 DSA 做深度分析（需要配置 DSA_API_URL）
alphasift screen dual_low --deep-analysis

# Python 调用
from alphasift import screen
result = screen("dual_low", use_llm=False)
for p in result.picks:
    print(f"{p.rank}. {p.code} {p.name} score={p.final_score:.1f}")
```

## 环境变量

| 变量 | 必须 | 说明 | 默认值 |
|------|------|------|--------|
| `LLM_API_KEY` | LLM 排序时必须 | litellm 支持的 API Key | - |
| `LLM_MODEL` | 否 | LLM 模型名 | `gemini/gemini-2.5-flash` |
| `LLM_BASE_URL` | 否 | 自定义 API 地址 | - |
| `SNAPSHOT_SOURCE_PRIORITY` | 否 | 数据源优先级（逗号分隔） | `efinance,akshare_em,em_datacenter` |
| `DSA_API_URL` | 深度分析时必须 | DSA 服务地址或完整分析端点 | - |
| `DSA_REPORT_TYPE` | 否 | DSA 报告类型 | `detailed` |
| `DSA_MAX_PICKS` | 否 | 最多对前 N 只候选做深度分析 | `3` |
| `DSA_TIMEOUT_SEC` | 否 | DSA 单次请求超时秒数 | `120` |
| `DSA_FORCE_REFRESH` | 否 | 是否强制 DSA 忽略缓存 | `false` |
| `DSA_NOTIFY` | 否 | 是否允许 DSA 发送外部通知 | `false` |
| `STRATEGIES_DIR` | 否 | 策略目录路径 | 自动查找 |

## 项目结构

```
alphasift/
├── SKILL.md                # Skill 描述（AI Agent 读这个）
├── strategies/             # 选股策略 YAML
├── docs/
│   ├── design.md           # 设计原则
│   ├── scoring.md          # 评分体系
│   └── strategy-guide.md   # 策略编写指南
└── alphasift/              # Python 包
    ├── __init__.py
    ├── cli.py              # CLI 入口
    ├── config.py           # 环境配置
    ├── models.py           # 数据模型
    ├── snapshot.py         # 全市场快照（3 种数据源 + 自动降级）
    ├── filter.py           # L1 硬筛
    ├── scorer.py           # 评分计算
    ├── ranker.py           # L2 LLM 排序
    ├── dsa.py              # 可选 DSA 深度分析接入
    ├── pipeline.py         # 主流程编排
    └── strategy.py         # 策略 YAML 加载
```

## 核心思路

- **三层漏斗**：L1 代码硬筛 → L2 LLM 排序 → L3 深度分析（可选，调用外部系统）
- **策略即 YAML**：所有选股逻辑通过 YAML 文件定义，不写死代码
- **为 Agent 设计**：SKILL.md 描述能力和接口，任何支持 Skill 协议的 Agent 都能调用

## 数据源

支持三种 A 股全市场快照数据源，自动按优先级降级：

| 数据源 | 接口 | 特点 |
|--------|------|------|
| `efinance` | push2.eastmoney.com | 实时推送，交易时段最快 |
| `akshare_em` | 82.push2.eastmoney.com | 实时推送，备选 |
| `em_datacenter` | data.eastmoney.com | 选股器 API，**非交易时段可用** |

> 周末/节假日 push2 接口不可用，会自动降级到 em_datacenter。

## 内置策略

| 策略 | 类型 | 说明 |
|------|------|------|
| `dual_low` | 价值 | 低 PE + 低 PB，适合价值投资 |
| `volume_breakout` | 趋势 | 放量突破关键阻力位 |

`shrink_pullback` 设计仍保留在仓库中，但因当前版本未接入日 K 线特征校验，暂不开放，避免静默偏离策略定义。

### 自定义策略

在 `strategies/` 目录添加 YAML 文件即可。参考 [docs/strategy-guide.md](docs/strategy-guide.md)。

## 已知限制

- 当前版本不开放依赖日 K 线特征的策略；关键快照字段缺失时会直接失败，而不是静默跳过过滤条件
- `deep_analysis` 依赖外部 DSA 服务，当前按同步 REST 请求逐只调用，适合作为可选增强而不是高并发主链
- 评分基于快照横截面数据，不含趋势/技术分析的完整信号
- 仓库内同时保留 `strategies/` 与 `alphasift/strategies/` 两份策略镜像用于开发态和安装态；启动时会校验二者是否一致，发现漂移将直接报错

## 实测记录

### 2026-04-12（周六，非交易时段）

测试环境：Python 3.12，数据来源为上一交易日（2026-04-10）收盘数据。

- efinance / akshare 实时推送接口在非交易时段不可用，自动降级到 `em_datacenter`（东方财富选股器 API）
- 未启用 LLM 排序（`--no-llm`）

#### 双低选股（dual_low）

全市场 5190 只 → 硬筛后 337 只 → 输出 Top 5

| 排名 | 代码 | 名称 | 得分 | 价格 | 涨跌幅 | PE | PB |
|------|------|------|------|------|--------|-----|-----|
| 1 | 002039 | 黔源电力 | 72.7 | 20.72 | -2.49% | 14.76 | 1.99 |
| 2 | 002444 | 巨星科技 | 71.0 | 30.82 | +0.29% | 14.59 | 1.95 |
| 3 | 002128 | 电投能源 | 70.9 | 31.60 | -2.41% | 14.00 | 1.90 |
| 4 | 002236 | 大华股份 | 70.8 | 17.43 | +1.04% | 14.86 | 1.50 |
| 5 | 600583 | 海油工程 | 68.9 | 7.02 | +4.15% | 14.89 | 1.17 |

#### 放量突破（volume_breakout）

全市场 5190 只 → 硬筛后 126 只 → 输出 Top 5

| 排名 | 代码 | 名称 | 得分 | 价格 | 涨跌幅 |
|------|------|------|------|------|--------|
| 1 | 002837 | 英维克 | 74.0 | 99.05 | +6.40% |
| 2 | 688183 | 生益电子 | 73.8 | 95.30 | +7.09% |
| 3 | 300803 | 指南针 | 73.3 | 101.68 | +3.07% |
| 4 | 002384 | 东山精密 | 73.0 | 143.55 | +8.83% |
| 5 | 300277 | 汽轮科技 | 73.0 | 19.74 | +5.73% |

#### 数据源降级验证

| 数据源 | 状态 | 说明 |
|--------|------|------|
| efinance（push2.eastmoney.com） | 不可用 | 实时推送接口，非交易时段返回空响应 |
| akshare_em（82.push2.eastmoney.com） | 不可用 | 同上 |
| em_datacenter（data.eastmoney.com） | 可用 | 选股器 API，周末仍返回最近交易日数据 |

降级链路验证通过：efinance → akshare_em → em_datacenter，自动切换到可用数据源。

## 文档

- [SKILL.md](SKILL.md) — Skill 描述与函数接口
- [docs/design.md](docs/design.md) — 设计原则
- [docs/scoring.md](docs/scoring.md) — 评分体系详解
- [docs/strategy-guide.md](docs/strategy-guide.md) — 策略编写指南

## License

Apache License 2.0
