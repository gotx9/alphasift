# -*- coding: utf-8 -*-
"""L2 LLM ranker — relative ranking of shortlisted candidates."""

import json
import logging

from alphasift.models import Pick

logger = logging.getLogger(__name__)


def rank_candidates(
    candidates: list[Pick],
    ranking_hints: str,
    llm_api_key: str,
    llm_model: str,
    llm_base_url: str = "",
) -> list[Pick]:
    """Use LLM to re-rank candidates and add ranking_reason / risk_summary.

    Falls back to screen_score order if LLM call fails.
    """
    if not llm_api_key or not candidates:
        return candidates

    prompt = _build_ranking_prompt(candidates, ranking_hints)

    try:
        response = _call_llm(prompt, llm_api_key, llm_model, llm_base_url)
        ranked = _parse_ranking_response(response, candidates)
        for i, pick in enumerate(ranked):
            pick.rank = i + 1
            pick.llm_score = 100.0 - i * (100.0 / max(len(ranked), 1))
            pick.final_score = (pick.screen_score + (pick.llm_score or 0)) / 2
        return ranked
    except Exception as e:
        logger.warning("LLM ranking failed, falling back to screen_score: %s", e)
        return candidates


def _build_ranking_prompt(candidates: list[Pick], hints: str) -> str:
    candidates_text = "\n".join(
        f"- {p.code} {p.name}: 价格={p.price}, 涨跌幅={p.change_pct}%, "
        f"screen_score={p.screen_score:.1f}, PE={p.pe_ratio}, PB={p.pb_ratio}"
        for p in candidates
    )
    return f"""你是一个专业的股票分析师。请对以下候选股票进行相对排序。

## 排序依据
{hints}

## 候选列表
{candidates_text}

## 输出要求
返回 JSON 数组，按推荐程度从高到低排列，每个元素包含：
- code: 股票代码
- reason: 排序理由（一句话）
- risk: 主要风险（一句话）
"""


def _call_llm(prompt: str, api_key: str, model: str, base_url: str) -> str:
    """Call LLM via litellm."""
    import litellm

    kwargs = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url

    response = litellm.completion(**kwargs)
    return response.choices[0].message.content or ""


def _parse_ranking_response(response: str, candidates: list[Pick]) -> list[Pick]:
    """Parse LLM response and reorder candidates."""
    import re

    # Extract JSON array from response (may be wrapped in markdown code block)
    cleaned = re.sub(r"```(?:json)?\s*", "", response)
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start < 0 or end <= start:
        logger.warning("No JSON array found in LLM response")
        return candidates

    try:
        items = json.loads(cleaned[start:end])
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM ranking JSON: %s", e)
        return candidates
    code_to_pick = {p.code: p for p in candidates}

    ranked = []
    for item in items:
        code = item.get("code", "")
        if code in code_to_pick:
            pick = code_to_pick.pop(code)
            pick.ranking_reason = item.get("reason", "")
            pick.risk_summary = item.get("risk", "")
            ranked.append(pick)

    # Append any candidates not mentioned by LLM
    ranked.extend(code_to_pick.values())
    return ranked
