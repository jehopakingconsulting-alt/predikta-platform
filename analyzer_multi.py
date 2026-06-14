"""
PREDIKTA — Generic digit-game analyzer (Pick3 / Pick4 / Pick5).

Generalizes the statistical engine from analyzer.py (frequency, hot/cold,
gaps, Markov transitions, weighted suggestions) to an arbitrary number of
digit positions, operating on the games/*.json draw format:
    {"date": "...", "tod": "...", "nums": ["6","2","7", ...], "extra": []}
"""

from collections import Counter, defaultdict

DIGITS = [str(i) for i in range(10)]


def digit_frequencies(draws: list[dict], pos: int = None, n: int = None) -> dict:
    """Count how often each digit 0-9 appears, optionally at a single position `pos`."""
    counter = Counter()
    for d in draws:
        nums = d["nums"][:n] if n else d["nums"]
        if pos is not None:
            counter[nums[pos]] += 1
        else:
            for v in nums:
                counter[v] += 1
    total = sum(counter.values()) or 1
    return {k: {"count": counter[k], "pct": round(counter[k] / total * 100, 2)} for k in DIGITS}


def hot_cold(draws: list[dict], window: int = 30, n: int = None) -> dict:
    recent = draws[:window]
    freq = digit_frequencies(recent, n=n)
    avg = sum(v["pct"] for v in freq.values()) / 10
    return {
        k: {**v, "status": "HOT" if v["pct"] > avg * 1.2 else ("COLD" if v["pct"] < avg * 0.8 else "NEUTRAL")}
        for k, v in freq.items()
    }


def gap_analysis(draws: list[dict], n: int) -> dict:
    """For each digit, draws since last appearance (across all positions)."""
    last_seen = {}
    gap_sums = defaultdict(int)
    gap_counts = defaultdict(int)

    for i, d in enumerate(reversed(draws)):
        for digit in d["nums"][:n]:
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


def markov_transitions(draws: list[dict], pos: int) -> dict:
    """Given digit X appeared last draw at `pos`, what's the next-draw distribution?"""
    matrix = defaultdict(Counter)
    prev = None
    for d in reversed(draws):
        curr = d["nums"][pos]
        if prev is not None:
            matrix[prev][curr] += 1
        prev = curr

    result = {}
    for from_digit, transitions in matrix.items():
        total = sum(transitions.values())
        result[from_digit] = {to: round(c / total * 100, 1) for to, c in transitions.items()}
    return result


def pair_frequencies(draws: list[dict], n: int) -> dict:
    counter = Counter()
    for d in draws:
        nums = d["nums"][:n]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair = tuple(sorted([nums[i], nums[j]]))
                counter[pair] += 1
    total = len(draws) or 1
    return {
        f"{p[0]}-{p[1]}": {"count": c, "pct": round(c / total * 100, 2)}
        for p, c in counter.most_common(20)
    }


def confidence_label(score: float, max_score: float) -> str:
    """Relative statistical signal vs. the top combo — not a win probability."""
    ratio = score / max_score if max_score else 0
    if ratio >= 0.95:
        return "Tendance très forte"
    elif ratio >= 0.85:
        return "Tendance forte"
    elif ratio >= 0.70:
        return "Tendance moyenne"
    else:
        return "Tendance faible"


def weighted_suggestions(draws: list[dict], n: int, top_n: int = 5) -> list[dict]:
    """
    Generate top N suggested combinations of `n` digits using:
    - Per-position frequency weight
    - Overdue (gap) bonus
    - Markov next-state probability
    """
    if not draws:
        return []

    last = draws[0]["nums"]
    freq = [digit_frequencies(draws, pos=p, n=n) for p in range(n)]
    gaps = gap_analysis(draws, n)
    markov = [markov_transitions(draws, p) for p in range(n)]

    def score_combo(combo: tuple) -> float:
        score = 0.0
        for i, digit in enumerate(combo):
            score += freq[i][digit]["pct"] / 10
            g = gaps[digit]
            if g["avg_gap"] and g["current_gap"] > g["avg_gap"]:
                score += min(g["current_gap"] / g["avg_gap"], 3.0)
            last_digit = last[i]
            mk = markov[i].get(last_digit, {})
            score += mk.get(digit, 0) / 100 * 5
        return score

    # Build candidate combos: for n<=4 enumerate exhaustively (≤10000),
    # for n==5 (100000 combos) restrict each position to its top-6 digits
    # by score contribution to keep the search tractable.
    if n <= 4:
        positions_digits = [DIGITS] * n
    else:
        positions_digits = []
        for i in range(n):
            ranked = sorted(DIGITS, key=lambda dg: (
                freq[i][dg]["pct"]
                + (min(gaps[dg]["current_gap"] / gaps[dg]["avg_gap"], 3.0) if gaps[dg]["avg_gap"] and gaps[dg]["current_gap"] > gaps[dg]["avg_gap"] else 0)
            ), reverse=True)
            positions_digits.append(ranked[:6])

    scores = {}

    def build(prefix, depth):
        if depth == n:
            scores[tuple(prefix)] = score_combo(tuple(prefix))
            return
        for dg in positions_digits[depth]:
            prefix.append(dg)
            build(prefix, depth + 1)
            prefix.pop()

    build([], 0)

    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [
        {
            "combo": "-".join(c),
            "digits": list(c),
            "score": round(s, 3),
            "confidence": confidence_label(s, top[0][1]),
        }
        for c, s in top
    ]


def full_report(draws: list[dict], n: int) -> dict:
    if not draws:
        return {"error": "No data"}

    return {
        "total_draws": len(draws),
        "last_draw": draws[0],
        "num_positions": n,
        "freq_all": digit_frequencies(draws, n=n),
        "freq_by_position": {f"p{p}": digit_frequencies(draws, pos=p, n=n) for p in range(n)},
        "hot_cold_30": hot_cold(draws, 30, n=n),
        "hot_cold_60": hot_cold(draws, 60, n=n),
        "gaps": gap_analysis(draws, n),
        "pairs": pair_frequencies(draws, n),
        "markov_p0": markov_transitions(draws, 0),
        "suggestions": weighted_suggestions(draws, n, top_n=10),
    }
