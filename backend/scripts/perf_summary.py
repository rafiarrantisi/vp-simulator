"""Perf sink summary CLI (Phase-1 voice foundation, ADR §4.5).

Reads the append-only JSONL sink (backend/data/perf/) and prints per-route
p50/p90/p95 (nearest-rank, the ADR §7 estimator lock-in) plus N, outcome
mix, attempt counts and error/hedge-adjacent rates. Timing/IDs/lengths only
— the sink never contains prompts, transcripts, keys or audio.

Usage:
    cd backend && python -m scripts.perf_summary
    cd backend && python -m scripts.perf_summary --days 3 --route v2_turn_stream
    cd backend && python -m scripts.perf_summary --perf-dir /tmp/qora_perf --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Summarize the Phase-1 perf sink per route.")
    p.add_argument("--perf-dir", default="",
                   help="Sink directory (default: backend/data/perf).")
    p.add_argument("--days", type=int, default=7,
                   help="How many daily files per kind to read (default 7).")
    p.add_argument("--route", default="",
                   help="Only include this route (default: all).")
    p.add_argument("--json", action="store_true",
                   help="Emit machine-readable JSON instead of text.")
    return p.parse_args(argv)


def _num(value):
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
    except Exception:
        pass
    return None


def _pct(sorted_vals: list[float], pct: float):
    from app.shared.perf_sink import nearest_rank
    return nearest_rank(sorted_vals, pct)


def summarize_turns(records: list[dict], route_filter: str = "") -> dict:
    """Group turn_perf records by route → latency quantiles + outcome mix."""
    from collections import Counter
    groups: dict[str, dict] = {}
    for r in records:
        try:
            route = str(r.get("route") or "")
        except Exception:
            continue
        if route_filter and route != route_filter:
            continue
        g = groups.setdefault(route, {
            "n": 0, "ttft": [], "total": [], "outcomes": Counter(),
            "missing_first_token": 0,
        })
        g["n"] += 1
        try:
            g["outcomes"][str(r.get("outcome") or "?")] += 1
        except Exception:
            pass
        marks = r.get("marks_ms") or {}
        try:
            t = _num((marks or {}).get("llm_first_token"))
            if t is not None:
                g["ttft"].append(t)
            else:
                g["missing_first_token"] += 1
            start = _num((marks or {}).get("request_received"))
            end = _num((marks or {}).get("request_complete"))
            if start is not None and end is not None and end >= start:
                g["total"].append(end - start)
        except Exception:
            continue
    out: dict[str, dict] = {}
    for route, g in sorted(groups.items()):
        ttft = sorted(g["ttft"])
        total = sorted(g["total"])
        out[route] = {
            "n": g["n"],
            "ttft_ms": {f"p{p}": _pct(ttft, p) for p in (50, 90, 95)},
            "turn_total_ms": {f"p{p}": _pct(total, p) for p in (50, 90, 95)},
            "outcomes": dict(g["outcomes"]),
            "missing_first_token": g["missing_first_token"],
        }
    return out


def summarize_attempts(records: list[dict], route_filter: str = "") -> dict:
    """Group patient_attempt records by route → attempt/error tallies."""
    from collections import Counter
    groups: dict[str, dict] = {}
    for r in records:
        try:
            route = str(r.get("route") or "")
        except Exception:
            continue
        if route_filter and route != route_filter:
            continue
        g = groups.setdefault(route, {
            "n": 0, "events": Counter(), "retries": 0, "errors": 0,
            "ttft": [], "total": [], "out_chars": [],
        })
        g["n"] += 1
        try:
            g["events"][str(r.get("event") or "?")] += 1
        except Exception:
            pass
        if r.get("event") == "retry_started":
            g["retries"] += 1
        if r.get("error"):
            g["errors"] += 1
        for key, bucket in (("ttft_ms", "ttft"), ("total_ms", "total"),
                            ("output_chars", "out_chars")):
            v = _num(r.get(key))
            if v is not None:
                g[bucket].append(v)
    out: dict[str, dict] = {}
    for route, g in sorted(groups.items()):
        out[route] = {
            "n": g["n"],
            "events": dict(g["events"]),
            "retry_started": g["retries"],
            "with_error": g["errors"],
            "ttft_ms": {f"p{p}": _pct(sorted(g["ttft"]), p)
                        for p in (50, 90, 95)},
            "attempt_total_ms": {f"p{p}": _pct(sorted(g["total"]), p)
                                 for p in (50, 90, 95)},
            "output_chars": {f"p{p}": _pct(sorted(g["out_chars"]), p)
                             for p in (50, 90, 95)},
        }
    return out


def main(argv=None) -> int:
    args = _parse_args(argv)
    from app.shared.perf_sink import iter_records, perf_dir
    directory = Path(args.perf_dir) if args.perf_dir else perf_dir()
    turns = iter_records("turn_perf", days=args.days, directory=directory)
    attempts = iter_records("patient_attempt", days=args.days,
                            directory=directory)
    payload = {
        "perf_dir": str(directory),
        "turn_files_n": len(turns),
        "attempt_files_n": len(attempts),
        "by_route_turns": summarize_turns(turns, args.route),
        "by_route_attempts": summarize_attempts(attempts, args.route),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1,
                         sort_keys=True))
    else:
        print(f"perf_dir={directory} "
              f"turn_rows={len(turns)} attempt_rows={len(attempts)}")
        for route, g in payload["by_route_turns"].items():
            print(f"[{route}] n={g['n']} "
                  f"ttft_ms={g['ttft_ms']} total_ms={g['turn_total_ms']} "
                  f"outcomes={g['outcomes']}")
        for route, g in payload["by_route_attempts"].items():
            print(f"[{route}/attempts] n={g['n']} events={g['events']} "
                  f"retries={g['retry_started']} errors={g['with_error']} "
                  f"ttft_ms={g['ttft_ms']}")
        if not payload["by_route_turns"] and not payload["by_route_attempts"]:
            print("(sink empty — no turn_perf/patient_attempt rows found)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
