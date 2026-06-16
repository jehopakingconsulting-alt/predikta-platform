"""
Statistical analysis engine for Pick4 / Cash4 / Win4 / Daily4 draws.
All 7 algorithms from analyzer.py adapted for 4-digit draw games.
"""

import math
from collections import Counter, defaultdict
from scraper4 import load_csv4

DIGITS = [str(i) for i in range(10)]
POSITIONS = ["d1", "d2", "d3", "d4"]


def load_draws4(state_code: str) -> list[dict]:
    return load_csv4(state_code)


def digit_frequencies4(draws: list[dict], position: str = None) -> dict:
    """Count how often each digit 0-9 appears, optionally by position."""
    counter = Counter()
    for d in draws:
        if position:
            counter[d[position]] += 1
        else:
            for pos in POSITIONS:
                counter[d[pos]] += 1
    total = sum(counter.values()) or 1
    return {k: {"count": counter[k], "pct": round(counter[k] / total * 100, 2)} for k in DIGITS}


def hot_cold4(draws: list[dict], window: int = 30) -> dict:
    """Hot/cold digits over last `window` draws."""
    recent = draws[:window]
    freq = digit_frequencies4(recent)
    avg = sum(v["pct"] for v in freq.values()) / 10
    return {
        k: {**v, "status": "HOT" if v["pct"] > avg * 1.2 else ("COLD" if v["pct"] < avg * 0.8 else "NEUTRAL")}
        for k, v in freq.items()
    }


def gap_analysis4(draws: list[dict]) -> dict:
    """For each digit, compute draws since last appearance (gap) and average gap."""
    last_seen = {}
    gap_sums = defaultdict(int)
    gap_counts = defaultdict(int)

    for i, d in enumerate(reversed(draws)):
        for pos in POSITIONS:
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


def markov_transitions4(draws: list[dict], position: str = "d1") -> dict:
    """Markov transition matrix for a given position."""
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


def pair_frequencies4(draws: list[dict]) -> dict:
    """Most common pairs across all positions (6 pairs per draw for 4-digit)."""
    counter = Counter()
    for d in draws:
        nums = [d[p] for p in POSITIONS]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair = tuple(sorted([nums[i], nums[j]]))
                counter[pair] += 1
    total = len(draws) or 1
    return {
        f"{p[0]}-{p[1]}": {"count": c, "pct": round(c / total * 100, 2)}
        for p, c in counter.most_common(20)
    }


def weighted_suggestions4(draws: list[dict], top_n: int = 5) -> list[dict]:
    """
    Generate top N suggested 4-digit combinations using:
    - Per-position frequency weight
    - Overdue (gap) bonus
    - Markov next-state probability
    Iterates all 10^4 = 10,000 combinations.
    """
    if not draws:
        return []

    last = draws[0]

    freq = {pos: digit_frequencies4(draws, pos) for pos in POSITIONS}
    gaps = gap_analysis4(draws)
    markov = {pos: markov_transitions4(draws, pos) for pos in POSITIONS}
    hc = hot_cold4(draws, 30)

    scores = {}
    for d1 in DIGITS:
        for d2 in DIGITS:
            for d3 in DIGITS:
                for d4 in DIGITS:
                    score = 0.0
                    combo = [d1, d2, d3, d4]

                    for digit, pos in zip(combo, POSITIONS):
                        score += freq[pos][digit]["pct"] / 10

                        g = gaps[digit]
                        if g["avg_gap"] and g["current_gap"] > g["avg_gap"]:
                            overdue_ratio = g["current_gap"] / g["avg_gap"]
                            score += min(overdue_ratio, 3.0)

                        last_digit = last[pos]
                        mk = markov[pos].get(last_digit, {})
                        score += mk.get(digit, 0) / 100 * 5

                    scores[(d1, d2, d3, d4)] = score

    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [
        {
            "combo": f"{c[0]}-{c[1]}-{c[2]}-{c[3]}",
            "digits": list(c),
            "score": round(s, 3),
            "confidence": confidence_label4(s, top[0][1]),
            "breakdown": _suggestion_breakdown4(c, freq, gaps, markov, hc, last),
        }
        for c, s in top
    ]


def _suggestion_breakdown4(combo, freq, gaps, markov, hot_cold_map, last_draw):
    out = []
    for digit, pos in zip(combo, POSITIONS):
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


def confidence_label4(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.95:
        return "Tendance très forte"
    elif ratio >= 0.85:
        return "Tendance forte"
    elif ratio >= 0.70:
        return "Tendance moyenne"
    else:
        return "Tendance faible"


def backtest_suggestions4(draws: list[dict], n: int = 15, min_history: int = 60) -> list[dict]:
    """
    Replay the last `n` draws: for each, compute the TOP PICK using only
    data available before that draw (no lookahead), then compare.
    4-digit straight: 1:10,000 odds. Box: varies by digit pattern.
    """
    results = []
    for i in range(min(n, len(draws))):
        history = draws[i + 1:]
        if len(history) < min_history:
            break
        actual = draws[i]
        sugg = weighted_suggestions4(history, top_n=1)
        if not sugg:
            continue
        top = sugg[0]
        actual_digits = [actual["d1"], actual["d2"], actual["d3"], actual["d4"]]
        results.append({
            "date": actual["date"],
            "tod": actual.get("tod", ""),
            "predicted": top["combo"],
            "confidence": top["confidence"],
            "actual": f"{actual['d1']}{actual['d2']}{actual['d3']}{actual['d4']}",
            "hit_straight": top["digits"] == actual_digits,
            "hit_box": sorted(top["digits"]) == sorted(actual_digits),
        })
    return results


def full_report4(state_code: str, draws: list[dict] = None) -> dict:
    if draws is None:
        draws = load_draws4(state_code)
    if not draws:
        return {"error": f"No Pick4 data for {state_code}. Run scraper4 first."}

    return {
        "state": state_code,
        "total_draws": len(draws),
        "last_draw": draws[0] if draws else None,
        "freq_all": digit_frequencies4(draws),
        "freq_by_position": {pos: digit_frequencies4(draws, pos) for pos in POSITIONS},
        "hot_cold_30": hot_cold4(draws, 30),
        "hot_cold_60": hot_cold4(draws, 60),
        "gaps": gap_analysis4(draws),
        "pairs": pair_frequencies4(draws),
        "markov_d1": markov_transitions4(draws, "d1"),
        "suggestions": weighted_suggestions4(draws, top_n=10),
    }


if __name__ == "__main__":
    import sys
    state = sys.argv[1].upper() if len(sys.argv) > 1 else "NY"
    report = full_report4(state)
    if "error" in report:
        print(report["error"])
    else:
        print(f"\n=== {state} Pick4 Analysis ===")
        print(f"Total draws: {report['total_draws']}")
        print(f"Last draw: {report['last_draw']}")
        print(f"\nTop suggestions:")
        for i, s in enumerate(report["suggestions"], 1):
            print(f"  #{i}: {s['combo']}  (score: {s['score']}, confidence: {s['confidence']})")
