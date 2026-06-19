"""
PREDIKTA — Multi-ball lotto analyzer (Cash 5, Fantasy 5, Take 5, etc.)
Handles games where 5 (or N) distinct numbers are drawn from a pool (e.g. 1-43).
Numbers are unordered and without replacement — position analysis doesn't apply.

Algorithms:
  - Frequency / hot-cold (last 30 vs. full history)
  - Gap / overdue bonus (draws since last appearance)
  - Pair co-occurrence matrix
  - Weighted suggestion: top-5 by freq + gap + pair signal
  - Backtest track record (hit_5, hit_4, hit_3 counts)
"""

from collections import Counter, defaultdict


# ── Utilities ─────────────────────────────────────────────────────────────

def _pool_size(draws: list[dict]) -> int:
    """Infer the pool ceiling from draw history (max number seen)."""
    return max(int(n) for d in draws for n in d["nums"] if n.isdigit())


def _pick_n(draws: list[dict]) -> int:
    """
    Infer how many numbers are drawn per draw.
    Uses the minimum observed draw length — some scrapers merge two draws
    into one row, doubling the count (e.g. NC cash5: 5→10). The minimum
    length is always the true pick-N.
    """
    if not draws:
        return 5
    lengths = [len(d["nums"]) for d in draws if d["nums"]]
    return min(lengths) if lengths else 5


def _normalize_draws(draws: list[dict]) -> list[dict]:
    """
    Truncate draw nums to the expected pick_n.
    Handles cases where scraper merges two draws into one row.
    """
    n = _pick_n(draws)
    return [{**d, "nums": d["nums"][:n]} for d in draws]


# ── Core statistics ───────────────────────────────────────────────────────

def number_frequencies(draws: list[dict], window: int = None) -> dict:
    """
    How often each number appears.
    Returns {num_str: {"count": int, "pct": float}} for all numbers in history.
    """
    subset = draws[:window] if window else draws
    counter = Counter()
    for d in subset:
        for n in d["nums"]:
            counter[n] += 1
    total_draws = len(subset) or 1
    pick_n = _pick_n(subset)
    return {
        k: {"count": counter[k], "pct": round(counter[k] / total_draws * 100, 2)}
        for k in sorted(counter, key=lambda x: int(x))
    }


def hot_cold(draws: list[dict], window: int = 30) -> dict:
    """Mark each number HOT / COLD / NEUTRAL vs. its long-term average."""
    recent = number_frequencies(draws, window=window)
    overall = number_frequencies(draws)
    avg_pct = sum(v["pct"] for v in recent.values()) / len(recent) if recent else 1
    result = {}
    for num, data in overall.items():
        r = recent.get(num, {"pct": 0})
        status = ("HOT" if r["pct"] > avg_pct * 1.2
                  else "COLD" if r["pct"] < avg_pct * 0.8
                  else "NEUTRAL")
        result[num] = {**data, "recent_pct": r["pct"], "status": status}
    return result


def gap_analysis(draws: list[dict]) -> dict:
    """
    For each number, compute draws since last appearance and average gap.
    Higher overdue_ratio = more 'due' to appear.
    """
    last_seen = {}
    gap_sums = defaultdict(int)
    gap_counts = defaultdict(int)

    for i, d in enumerate(reversed(draws)):
        for num in d["nums"]:
            if num not in last_seen:
                last_seen[num] = i
            else:
                gap = i - last_seen[num]
                gap_sums[num] += gap
                gap_counts[num] += 1
                last_seen[num] = i

    result = {}
    for num in last_seen:
        avg_gap = round(gap_sums[num] / gap_counts[num], 1) if gap_counts[num] else None
        current_gap = len(draws) - 1 - last_seen[num]
        overdue_ratio = (current_gap / avg_gap) if avg_gap else 0
        result[num] = {
            "current_gap": current_gap,
            "avg_gap": avg_gap,
            "overdue": current_gap > (avg_gap or 0),
            "overdue_ratio": round(min(overdue_ratio, 4.0), 2),
        }
    return result


def pair_frequencies(draws: list[dict], top_n: int = 20) -> list[dict]:
    """Top-N most frequent pairs of numbers drawn together."""
    counter = Counter()
    for d in draws:
        nums = sorted(d["nums"], key=lambda x: int(x))
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                counter[(nums[i], nums[j])] += 1
    total = len(draws) or 1
    return [
        {
            "pair": f"{p[0]}-{p[1]}",
            "nums": list(p),
            "count": c,
            "pct": round(c / total * 100, 2),
        }
        for p, c in counter.most_common(top_n)
    ]


# ── Suggestions ───────────────────────────────────────────────────────────

def markov_next(draws: list[dict]) -> dict:
    """
    Which numbers tend to appear in the draw AFTER a given number appeared?
    Returns {num: {next_num: transition_prob}}.
    """
    matrix = defaultdict(Counter)
    for i in range(len(draws) - 1):
        curr_nums = set(draws[i]["nums"])
        next_nums = set(draws[i + 1]["nums"])
        for cn in curr_nums:
            for nn in next_nums:
                matrix[cn][nn] += 1
    result = {}
    for num, transitions in matrix.items():
        total = sum(transitions.values())
        result[num] = {k: round(v / total, 4) for k, v in transitions.items()}
    return result


def monte_carlo_scores(draws: list[dict], n_sim: int = 5000) -> dict:
    """
    Simulate n_sim random draws using historical frequency as weights.
    Return {num: appearance_rate} — numbers that appear more in simulations
    than expected are statistically 'favored' by recent patterns.
    """
    import random as _rnd
    freq = number_frequencies(draws)
    pool = sorted(freq.keys(), key=lambda x: int(x))
    weights = [freq[n]["count"] for n in pool]
    pick_n = _pick_n(draws)
    total_w = sum(weights)
    probs = [w / total_w for w in weights]

    counter = Counter()
    rng = _rnd.Random(42)
    for _ in range(n_sim):
        sample = rng.choices(pool, weights=probs, k=pick_n * 3)
        seen = []
        for s in sample:
            if s not in seen:
                seen.append(s)
            if len(seen) == pick_n:
                break
        for n in seen:
            counter[n] += 1

    mx = max(counter.values()) if counter else 1
    return {n: counter.get(n, 0) / mx for n in pool}


def _number_scores(draws: list[dict], weights: dict = None) -> dict:
    """
    Composite score per number: weighted freq + gap/overdue + pair-affinity
    + Markov next-draw tendency + Monte Carlo simulation signal.
    weights: dict with keys freq, gap, pair (from calibrator); defaults used if None.
    """
    W = weights or {"freq": 0.30, "gap": 0.25, "pair": 0.20}
    # Remaining weight split between Markov and MC
    w_markov = 0.15
    w_mc = 0.10

    freq = number_frequencies(draws)
    gaps = gap_analysis(draws)
    mc = monte_carlo_scores(draws, n_sim=3000)
    mkv = markov_next(draws)
    last_nums = set(draws[0]["nums"]) if draws else set()

    # Pair affinity
    pair_counter = Counter()
    for d in draws:
        nums = sorted(d["nums"], key=lambda x: int(x))
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair_counter[(nums[i], nums[j])] += 1
    max_pair = max(pair_counter.values()) if pair_counter else 1
    pair_aff = defaultdict(float)
    for (a, b), cnt in pair_counter.items():
        v = cnt / max_pair
        pair_aff[a] += v
        pair_aff[b] += v

    max_freq = max((v["pct"] for v in freq.values()), default=1) or 1
    max_pair_aff = max(pair_aff.values()) if pair_aff else 1

    # Markov: how much is this number favored by the previous draw?
    markov_aff = defaultdict(float)
    for prev_num in last_nums:
        transitions = mkv.get(prev_num, {})
        for nxt, prob in transitions.items():
            markov_aff[nxt] += prob
    max_mkv = max(markov_aff.values()) if markov_aff else 1

    scores = {}
    for num in freq:
        f = freq[num]["pct"] / max_freq
        g = gaps.get(num, {}).get("overdue_ratio", 0) / 4.0
        p = pair_aff.get(num, 0) / max_pair_aff
        m = mc.get(num, 0)
        mk = markov_aff.get(num, 0) / max_mkv
        scores[num] = (W["freq"] * f + W["gap"] * g + W["pair"] * p
                       + w_markov * mk + w_mc * m)
    return scores


def weighted_suggestions(draws: list[dict], pick_n: int = None, top_n: int = 10,
                          state_code: str = None, slug: str = None) -> list[dict]:
    """
    Return top-N suggested combinations of `pick_n` numbers.
    Uses dynamically calibrated weights when state_code+slug provided.
    """
    if not draws or len(draws) < 20:
        return []
    draws = _normalize_draws(draws)
    if pick_n is None:
        pick_n = _pick_n(draws)

    # Load calibrated weights if available
    cal_weights = None
    if state_code and slug:
        try:
            from weight_calibrator_lotto import calibrate_lotto_if_needed
            cal_weights = calibrate_lotto_if_needed(state_code, slug, draws)
        except Exception:
            pass

    scores = _number_scores(draws, weights=cal_weights)
    freq = number_frequencies(draws)
    gaps = gap_analysis(draws)
    hc = hot_cold(draws)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    pool = [num for num, _ in ranked]

    # Generate top_n combos by sliding window through ranked pool
    suggestions = []
    max_score = None
    for start in range(min(top_n * 2, len(pool) - pick_n + 1)):
        combo = sorted(pool[start:start + pick_n], key=lambda x: int(x))
        combo_score = sum(scores.get(n, 0) for n in combo)
        if max_score is None:
            max_score = combo_score
        ratio = combo_score / max_score if max_score else 0
        confidence = (
            "Tendance très forte" if ratio >= 0.98 else
            "Tendance forte" if ratio >= 0.90 else
            "Tendance moyenne" if ratio >= 0.78 else
            "Tendance faible"
        )
        suggestions.append({
            "combo": "-".join(combo),
            "nums": combo,
            "score": round(combo_score, 4),
            "confidence": confidence,
            "breakdown": [
                {
                    "num": n,
                    "freq_pct": freq.get(n, {}).get("pct", 0),
                    "current_gap": gaps.get(n, {}).get("current_gap", 0),
                    "avg_gap": gaps.get(n, {}).get("avg_gap", 0),
                    "overdue": gaps.get(n, {}).get("overdue", False),
                    "hot_cold": hc.get(n, {}).get("status", "NEUTRAL"),
                    "score": round(scores.get(n, 0), 4),
                }
                for n in combo
            ],
        })
        if len(suggestions) >= top_n:
            break

    return suggestions


# ── Backtest ──────────────────────────────────────────────────────────────

def backtest(draws: list[dict], n: int = 15, min_history: int = 60) -> list[dict]:
    """
    Replay the last `n` draws: for each, compute our TOP PICK using only
    data available before that draw, then compare to actual result.
    Records hit_5 (jackpot), hit_4, hit_3 counts.
    """
    draws = _normalize_draws(draws)
    pick_n = _pick_n(draws)
    results = []
    for i in range(min(n, len(draws))):
        history = draws[i + 1:]
        if len(history) < min_history:
            break
        actual_set = set(draws[i]["nums"])
        sugg = weighted_suggestions(history, pick_n=pick_n, top_n=1)
        if not sugg:
            continue
        top = sugg[0]
        predicted_set = set(top["nums"])
        matched = len(actual_set & predicted_set)
        results.append({
            "date": draws[i]["date"],
            "tod": draws[i].get("tod", ""),
            "predicted": top["combo"],
            "actual": "-".join(sorted(draws[i]["nums"], key=lambda x: int(x))),
            "matched": matched,
            "hit_5": matched == pick_n,
            "hit_4": matched >= 4,
            "hit_3": matched >= 3,
        })
    return results


# ── Full report ───────────────────────────────────────────────────────────

def full_report(draws: list[dict], state_code: str = "", slug: str = "") -> dict:
    if not draws:
        return {"error": "No data"}
    draws = _normalize_draws(draws)
    pick_n = _pick_n(draws)
    pool = _pool_size(draws)
    return {
        "state": state_code,
        "slug": slug,
        "total_draws": len(draws),
        "last_draw": draws[0],
        "pick_n": pick_n,
        "pool_size": pool,
        "frequencies": number_frequencies(draws),
        "hot_cold_30": hot_cold(draws, 30),
        "hot_cold_60": hot_cold(draws, 60),
        "gaps": gap_analysis(draws),
        "pairs": pair_frequencies(draws, top_n=20),
        "markov_next": {k: dict(list(v.items())[:5]) for k, v in markov_next(draws).items()},
        "suggestions": weighted_suggestions(draws, pick_n=pick_n, top_n=10,
                                            state_code=state_code, slug=slug),
    }
