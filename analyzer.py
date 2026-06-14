"""
Statistical analysis engine for Cash3 / Pick3 draws.
Computes frequency, gaps, Markov transitions, and weighted probability suggestions.
"""

import json
import math
from collections import Counter, defaultdict
from scraper import load_csv

DIGITS = [str(i) for i in range(10)]


def load_draws(state_code: str) -> list[dict]:
    return load_csv(state_code)


def digit_frequencies(draws: list[dict], position: str = None) -> dict:
    """Count how often each digit 0-9 appears, optionally by position (d1/d2/d3)."""
    counter = Counter()
    for d in draws:
        if position:
            counter[d[position]] += 1
        else:
            counter[d["d1"]] += 1
            counter[d["d2"]] += 1
            counter[d["d3"]] += 1
    total = sum(counter.values()) or 1
    return {k: {"count": counter[k], "pct": round(counter[k] / total * 100, 2)} for k in DIGITS}


def hot_cold(draws: list[dict], window: int = 30) -> dict:
    """Hot/cold digits over last `window` draws."""
    recent = draws[:window]
    freq = digit_frequencies(recent)
    avg = sum(v["pct"] for v in freq.values()) / 10
    return {
        k: {**v, "status": "HOT" if v["pct"] > avg * 1.2 else ("COLD" if v["pct"] < avg * 0.8 else "NEUTRAL")}
        for k, v in freq.items()
    }


def gap_analysis(draws: list[dict]) -> dict:
    """For each digit, compute draws since last appearance (gap) and average gap."""
    last_seen = {}
    gap_sums = defaultdict(int)
    gap_counts = defaultdict(int)

    for i, d in enumerate(reversed(draws)):
        for pos in ["d1", "d2", "d3"]:
            digit = d[pos]
            if digit not in last_seen:
                last_seen[digit] = i
            else:
                gap = i - last_seen[digit]
                gap_sums[digit] += gap
                gap_counts[digit] += 1
                last_seen[digit] = i

    result = {}
    for digit in DIGITS:
        avg_gap = round(gap_sums[digit] / gap_counts[digit], 1) if gap_counts[digit] else None
        current_gap = len(draws) - 1 - last_seen.get(digit, len(draws) - 1)
        result[digit] = {
            "current_gap": current_gap,
            "avg_gap": avg_gap,
            "overdue": current_gap > (avg_gap or 0),
        }
    return result


def markov_transitions(draws: list[dict], position: str = "d1") -> dict:
    """
    Build a Markov transition matrix: given digit X appeared last draw,
    what digit is most likely next draw at the same position?
    """
    matrix = defaultdict(Counter)
    prev = None
    for d in reversed(draws):
        curr = d[position]
        if prev is not None:
            matrix[prev][curr] += 1
        prev = curr

    result = {}
    for from_digit, transitions in matrix.items():
        total = sum(transitions.values())
        result[from_digit] = {
            to: round(count / total * 100, 1)
            for to, count in transitions.items()
        }
    return result


def pair_frequencies(draws: list[dict]) -> dict:
    """Most common pairs across positions."""
    counter = Counter()
    for d in draws:
        nums = [d["d1"], d["d2"], d["d3"]]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair = tuple(sorted([nums[i], nums[j]]))
                counter[pair] += 1
    total = len(draws) or 1
    return {
        f"{p[0]}-{p[1]}": {"count": c, "pct": round(c / total * 100, 2)}
        for p, c in counter.most_common(20)
    }


def weighted_suggestions(draws: list[dict], top_n: int = 5) -> list[dict]:
    """
    Generate top N suggested combinations using:
    - Per-position frequency weight
    - Overdue (gap) bonus
    - Markov next-state probability
    """
    if not draws:
        return []

    last = draws[0]  # most recent draw

    scores = {}
    freq = {pos: digit_frequencies(draws, pos) for pos in ["d1", "d2", "d3"]}
    gaps = gap_analysis(draws)
    markov = {pos: markov_transitions(draws, pos) for pos in ["d1", "d2", "d3"]}
    hc = hot_cold(draws, 30)

    for d1 in DIGITS:
        for d2 in DIGITS:
            for d3 in DIGITS:
                score = 0.0
                combo = [d1, d2, d3]
                positions = ["d1", "d2", "d3"]

                for i, (digit, pos) in enumerate(zip(combo, positions)):
                    # frequency score (0-10)
                    score += freq[pos][digit]["pct"] / 10

                    # gap bonus: overdue digit gets a boost
                    g = gaps[digit]
                    if g["avg_gap"] and g["current_gap"] > g["avg_gap"]:
                        overdure_ratio = g["current_gap"] / g["avg_gap"]
                        score += min(overdure_ratio, 3.0)

                    # Markov: probability digit follows last draw's digit at same position
                    last_digit = last[pos]
                    mk = markov[pos].get(last_digit, {})
                    score += mk.get(digit, 0) / 100 * 5

                scores[(d1, d2, d3)] = score

    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [
        {
            "combo": f"{c[0]}-{c[1]}-{c[2]}",
            "digits": list(c),
            "score": round(s, 3),
            "confidence": confidence_label(s, top[0][1]),
            "breakdown": _suggestion_breakdown(c, freq, gaps, markov, hc, last),
        }
        for c, s in top
    ]


def _suggestion_breakdown(combo, freq, gaps, markov, hot_cold_map, last_draw):
    """
    Per-digit explanation of why a suggested combo was chosen ("Mode
    Transparence"): historical frequency, gap/overdue status, recent
    hot/cold trend, and Markov transition weight from the last draw.
    """
    positions = ["d1", "d2", "d3"]
    out = []
    for digit, pos in zip(combo, positions):
        g = gaps[digit]
        overdue = bool(g["avg_gap"] and g["current_gap"] > g["avg_gap"])
        last_digit = last_draw[pos]
        markov_pct = round(markov[pos].get(last_digit, {}).get(digit, 0), 2)
        out.append({
            "position": pos,
            "digit": digit,
            "freq_pct": freq[pos][digit]["pct"],
            "current_gap": g["current_gap"],
            "avg_gap": round(g["avg_gap"], 1) if g["avg_gap"] else 0,
            "overdue": overdue,
            "hot_cold": hot_cold_map.get(digit, {}).get("status", "NEUTRAL"),
            "markov_pct": markov_pct,
            "markov_from": last_digit,
        })
    return out


def confidence_label(score: float, max_score: float) -> str:
    """
    Labels the *relative statistical signal* of a combo vs. the top-scoring
    one for this draw — NOT a probability of winning (which stays ~0.1%
    straight / ~0.6% box regardless of this label).
    """
    ratio = score / max_score if max_score else 0
    if ratio >= 0.95:
        return "Tendance très forte"
    elif ratio >= 0.85:
        return "Tendance forte"
    elif ratio >= 0.70:
        return "Tendance moyenne"
    else:
        return "Tendance faible"


def backtest_suggestions(draws: list[dict], n: int = 15, min_history: int = 60) -> list[dict]:
    """
    Replay the last `n` draws: for each one, compute the TOP PICK that
    weighted_suggestions() would have produced using only the draws that
    happened BEFORE it (no lookahead), then compare to what actually came out.
    Returns the most recent results first.
    """
    results = []
    for i in range(min(n, len(draws))):
        history = draws[i + 1:]
        if len(history) < min_history:
            break
        actual = draws[i]
        sugg = weighted_suggestions(history, top_n=1)
        if not sugg:
            continue
        top = sugg[0]
        actual_digits = [actual["d1"], actual["d2"], actual["d3"]]
        results.append({
            "date": actual["date"],
            "tod": actual.get("tod", ""),
            "predicted": top["combo"],
            "confidence": top["confidence"],
            "actual": f"{actual['d1']}{actual['d2']}{actual['d3']}",
            "hit_straight": top["digits"] == actual_digits,
            "hit_box": sorted(top["digits"]) == sorted(actual_digits),
        })
    return results


def full_report(state_code: str) -> dict:
    draws = load_draws(state_code)
    if not draws:
        return {"error": f"No data for {state_code}. Run scraper first."}

    return {
        "state": state_code,
        "total_draws": len(draws),
        "last_draw": draws[0] if draws else None,
        "freq_all": digit_frequencies(draws),
        "freq_by_position": {
            "d1": digit_frequencies(draws, "d1"),
            "d2": digit_frequencies(draws, "d2"),
            "d3": digit_frequencies(draws, "d3"),
        },
        "hot_cold_30": hot_cold(draws, 30),
        "hot_cold_60": hot_cold(draws, 60),
        "gaps": gap_analysis(draws),
        "pairs": pair_frequencies(draws),
        "markov_d1": markov_transitions(draws, "d1"),
        "suggestions": weighted_suggestions(draws, top_n=10),
    }


if __name__ == "__main__":
    import sys
    state = sys.argv[1].upper() if len(sys.argv) > 1 else "NY"
    report = full_report(state)
    if "error" in report:
        print(report["error"])
    else:
        print(f"\n=== {state} Cash3 Analysis ===")
        print(f"Total draws: {report['total_draws']}")
        print(f"Last draw: {report['last_draw']}")
        print(f"\nTop suggestions for today:")
        for i, s in enumerate(report["suggestions"], 1):
            print(f"  #{i}: {s['combo']}  (score: {s['score']}, confidence: {s['confidence']})")
