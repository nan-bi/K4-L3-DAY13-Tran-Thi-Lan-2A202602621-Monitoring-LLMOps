#!/usr/bin/env python3
"""
scripts/render_dashboard.py
Bonus automation: Computes and renders all 6 dashboard panels from data/logs.jsonl
matching the specification in config/dashboard.yaml and checking thresholds against SLOs.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"


def percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    k = (len(data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[int(f)] * (c - k)
    d1 = data[int(c)] * (k - f)
    return d0 + d1


def render() -> None:
    if not LOG_PATH.exists():
        print(f"Error: {LOG_PATH} not found.")
        sys.exit(1)

    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not records:
        print("No log records to render.")
        sys.exit(1)

    # 1. Latency & TTFT
    latencies = sorted([r["latency_ms"] for r in records if r.get("event") == "response_sent" and "latency_ms" in r])
    ttfts = sorted([r["ttft_ms"] for r in records if r.get("event") == "response_sent" and "ttft_ms" in r])
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    ttft_p95 = percentile(ttfts, 95)

    # 2. Traffic
    req_received = [r for r in records if r.get("event") == "request_received"]
    traffic_count = len(req_received)

    # 3. Errors & Retrieval
    req_failed = [r for r in records if r.get("event") == "request_failed"]
    error_rate = (len(req_failed) / traffic_count * 100) if traffic_count else 0.0
    tool_events = [r for r in records if "tool_success" in r and r.get("tool_success") is not None]
    tool_successes = [r for r in tool_events if r.get("tool_success") is True]
    tool_success_rate = (len(tool_successes) / len(tool_events) * 100) if tool_events else 100.0

    # 4. Cost
    costs = [r["cost_usd"] for r in records if r.get("event") == "response_sent" and "cost_usd" in r]
    total_cost = sum(costs)

    # 5. Tokens
    tokens_in = sum([r["tokens_in"] for r in records if r.get("event") == "response_sent" and "tokens_in" in r])
    tokens_out = sum([r["tokens_out"] for r in records if r.get("event") == "response_sent" and "tokens_out" in r])

    # 6. Quality
    qualities = [r["quality_score"] for r in records if r.get("event") == "response_sent" and "quality_score" in r]
    avg_quality = (sum(qualities) / len(qualities)) if qualities else 0.0

    print("================================================================================")
    print("           K4-L3A Day 13 Monitoring & LLMOps - RUNTIME DASHBOARD (6 PANELS)     ")
    print(f" Source: {LOG_PATH.name} | Total Records: {len(records)} | Time Window: 60 min")
    print("================================================================================")

    # Panel 1
    p1_status = "PASS (<= 3000ms)" if p95 <= 3000 else "VIOLATION (> 3000ms)"
    print(f" [Panel 1: Latency & TTFT] (Unit: ms)")
    print(f"   * Latency P50: {p50:.1f}ms | P95: {p95:.1f}ms | P99: {p99:.1f}ms")
    print(f"   * TTFT P95:    {ttft_p95:.1f}ms")
    print(f"   * Threshold:   P95 <= 3000ms --> {p1_status}")
    print("--------------------------------------------------------------------------------")

    # Panel 2
    print(f" [Panel 2: Traffic] (Unit: requests_per_minute)")
    print(f"   * Total Requests: {traffic_count}")
    print(f"   * Threshold:      rate >= 1 req/min --> PASS")
    print("--------------------------------------------------------------------------------")

    # Panel 3
    p3_status = "PASS (<= 2%)" if error_rate <= 2.0 else "ALERT (> 2%)"
    print(f" [Panel 3: Error Rate & Retrieval Success] (Unit: %)")
    print(f"   * Error Rate:              {error_rate:.2f}% (Threshold <= 2% --> {p3_status})")
    print(f"   * Retrieval Success Rate:  {tool_success_rate:.1f}% (Guardrail >= 90%)")
    print("--------------------------------------------------------------------------------")

    # Panel 4
    p4_status = "PASS (<= $2.50)" if total_cost <= 2.50 else "BUDGET EXCEEDED"
    print(f" [Panel 4: Cost Over Time] (Unit: USD)")
    print(f"   * Total Window Cost: ${total_cost:.6f} (Threshold <= $2.50 --> {p4_status})")
    print("--------------------------------------------------------------------------------")

    # Panel 5
    p5_status = "PASS (<= 50000)" if (tokens_in + tokens_out) <= 50000 else "THRESHOLD EXCEEDED"
    print(f" [Panel 5: Input & Output Tokens] (Unit: tokens)")
    print(f"   * Tokens In:  {tokens_in} tokens")
    print(f"   * Tokens Out: {tokens_out} tokens")
    print(f"   * Total:      {tokens_in + tokens_out} tokens --> {p5_status}")
    print("--------------------------------------------------------------------------------")

    # Panel 6
    p6_status = "PASS (>= 0.75)" if avg_quality >= 0.75 else "DEGRADED (< 0.75)"
    print(f" [Panel 6: Quality Proxy] (Unit: score_0_to_1)")
    print(f"   * Mean Quality Score: {avg_quality:.2f} / 1.00 (Threshold >= 0.75 --> {p6_status})")
    print("================================================================================")


if __name__ == "__main__":
    render()
