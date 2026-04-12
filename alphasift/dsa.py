# -*- coding: utf-8 -*-
"""Optional DSA integration for L3 deep analysis."""

from __future__ import annotations

import json
import logging
from urllib.parse import urlparse

import requests

from alphasift.models import Pick

logger = logging.getLogger(__name__)
_DEFAULT_ANALYZE_PATH = "/api/v1/analysis/analyze"


def analyze_picks_with_dsa(
    picks: list[Pick],
    *,
    run_id: str,
    api_url: str,
    report_type: str = "detailed",
    max_picks: int = 3,
    timeout_sec: float = 120.0,
    force_refresh: bool = False,
    notify: bool = False,
) -> tuple[list[Pick], list[str]]:
    """Run DSA deep analysis for the top picks and attach results in place."""
    if not api_url:
        raise ValueError("DSA_API_URL is required when deep_analysis=True")
    if max_picks <= 0:
        return picks, []

    analyze_count = min(max_picks, len(picks))
    degradation: list[str] = []
    endpoint = build_dsa_analyze_url(api_url)

    for idx, pick in enumerate(picks):
        if idx >= analyze_count:
            pick.deep_analysis_status = "skipped"
            continue

        try:
            result = call_dsa_analysis(
                endpoint,
                stock_code=pick.code,
                stock_name=pick.name,
                report_type=report_type,
                query_id=f"{run_id}-{pick.rank}-{pick.code}",
                timeout_sec=timeout_sec,
                force_refresh=force_refresh,
                notify=notify,
            )
            pick.deep_analysis_status = "completed"
            pick.deep_analysis_query_id = str(result.get("query_id", ""))
            pick.deep_analysis_result = result
            pick.deep_analysis_summary = extract_deep_analysis_summary(result)
        except Exception as exc:
            logger.warning("DSA deep analysis failed for %s: %s", pick.code, exc)
            pick.deep_analysis_status = "failed"
            pick.deep_analysis_error = str(exc)
            degradation.append(f"DSA deep analysis failed for {pick.code}: {exc}")

    return picks, degradation


def build_dsa_analyze_url(api_url: str) -> str:
    """Accept a base URL or a full endpoint URL."""
    stripped = api_url.rstrip("/")
    parsed = urlparse(stripped)
    if parsed.path and parsed.path not in ("", "/"):
        return stripped
    return f"{stripped}{_DEFAULT_ANALYZE_PATH}"


def call_dsa_analysis(
    endpoint: str,
    *,
    stock_code: str,
    stock_name: str = "",
    report_type: str = "detailed",
    query_id: str = "",
    timeout_sec: float = 120.0,
    force_refresh: bool = False,
    notify: bool = False,
) -> dict:
    """Call the DSA sync analysis endpoint and return parsed JSON."""
    payload = {
        "stock_code": stock_code,
        "report_type": report_type,
        "force_refresh": force_refresh,
        "async_mode": False,
        "stock_name": stock_name or None,
        "original_query": stock_code,
        "selection_source": "import",
        "notify": notify,
    }
    if query_id:
        # The current DSA public API does not require query_id,
        # but we keep it in the payload for forward compatibility.
        payload["query_id"] = query_id

    response = requests.post(endpoint, json=payload, timeout=timeout_sec)
    response.raise_for_status()
    try:
        body = response.json()
    except ValueError:
        return {"raw_text": response.text}
    if not isinstance(body, dict):
        return {"raw_result": body}
    return body


def extract_deep_analysis_summary(result: dict) -> str:
    """Best-effort extraction of a short summary from a DSA response."""
    if not isinstance(result, dict):
        return ""

    for key in ("summary", "analysis_summary", "conclusion", "message"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    report = result.get("report")
    if isinstance(report, dict):
        summary = report.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        if isinstance(summary, dict):
            for key in ("operation_advice", "conclusion", "recommendation", "signal_level"):
                value = summary.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            rendered = json.dumps(summary, ensure_ascii=False)
            return rendered[:280]

    rendered = json.dumps(result, ensure_ascii=False)
    return rendered[:280]
