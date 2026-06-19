"""
PREDIKTA — Dynamic Weight Calibrator for multi-ball lotto games
(Cash 5, Fantasy 5, Take 5, etc.)

For each state+slug, runs a rank-based backtest over the last N draws and
measures how well each scoring component (freq, gap, pair) ranks real draws
vs. random. Weights saved to data/weights_lotto/{STATE}_{SLUG}.json.

Auto-recalibrates every RECALIBRATE_EVERY draws.
"""

import json
import os
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "weights_lotto")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_WEIGHTS = {"freq": 0.40, "gap": 0.35, "pair": 0.25}
MIN_WEIGHT = 0.10
CALIB_WINDOW = 30
RECALIBRATE_EVERY = 10


# ── Persistence ───────────────────────────────────────────────────────────

def _path(state: str, slug: str) -> str:
    return os.path.join(DATA_DIR, f"{state.upper()}_{slug}.json")


def load_weights_lotto(state: str, slug: str) -> dict:
    p = _path(state, slug)
    if os.path.exists(p):
        try:
            return json.load(open(p, "r", encoding="utf-8")).get("weights", DEFAULT_WEIGHTS)
        except Exception:
            pass
    return DEFAULT_WEIGHTS.copy()


def save_weights_lotto(state: str, slug: str, weights: dict, meta: dict = None):
    p = _path(state, slug)
    json.dump({"weights": weights, "meta": meta or {}}, open(p, "w", encoding="utf-8"), indent=2)


def needs_recalibration_lotto(state: str, slug: str, n_draws: int) -> bool:
    p = _path(state, slug)
    if not os.path.exists(p):
        return True
    try:
        last = json.load(open(p, "r", encoding="utf-8")).get("meta", {}).get("draw_count", 0)
        return (n_draws - last) >= RECALIBRATE_EVERY
    except Exception:
        return True


# ── Component scorers ─────────────────────────────────────────────────────

def _freq_scores(draws: list[dict]) -> dict:
    """Number → normalized frequency score (0-1)."""
    counter = Counter(n for d in draws for n in d["nums"])
    mx = max(counter.values()) if counter else 1
    return {k: v / mx for k, v in counter.items()}


def _gap_scores(draws: list[dict]) -> dict:
    """Number → overdue ratio (0-4 capped)."""
    last_seen, gap_sums, gap_counts = {}, defaultdict(int), defaultdict(int)
    for i, d in enumerate(reversed(draws)):
        for num in d["nums"]:
            if num not in last_seen:
                last_seen[num] = i
            else:
                gap = i - last_seen[num]
                gap_sums[num] += gap
                gap_counts[num] += 1
                last_seen[num] = i
    scores = {}
    for num in last_seen:
        avg = gap_sums[num] / gap_counts[num] if gap_counts[num] else None
        cur = len(draws) - 1 - last_seen[num]
        scores[num] = min(cur / avg, 4.0) if avg else 0.0
    mx = max(scores.values()) if scores else 1
    return {k: v / mx for k, v in scores.items()}


def _pair_scores(draws: list[dict]) -> dict:
    """Number → average pair co-occurrence score (0-1)."""
    pair_counter = Counter()
    for d in draws:
        nums = sorted(d["nums"])
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair_counter[(nums[i], nums[j])] += 1
    aff = defaultdict(float)
    mx_pair = max(pair_counter.values()) if pair_counter else 1
    for (a, b), cnt in pair_counter.items():
        v = cnt / mx_pair
        aff[a] += v
        aff[b] += v
    mx = max(aff.values()) if aff else 1
    return {k: v / mx for k, v in aff.items()}


def _combo_score(combo: list[str], freq: dict, gap: dict, pair: dict, W: dict) -> float:
    f = sum(freq.get(n, 0) for n in combo)
    g = sum(gap.get(n, 0) for n in combo)
    p = sum(pair.get(n, 0) for n in combo)
    return W["freq"] * f + W["gap"] * g + W["pair"] * p


def _rank_actual(draws: list[dict], actual: list[str], component: str) -> float:
    """
    Rank the actual drawn numbers among all numbers for one component.
    Returns percentile: 1.0 = top ranked, 0.0 = bottom.
    We compare the sum of component scores for actual numbers vs. all
    possible same-size combinations drawn from the pool.
    """
    freq = _freq_scores(draws)
    gap = _gap_scores(draws)
    pair = _pair_scores(draws)

    all_nums = list({n for d in draws for n in d["nums"]})
    pick_n = len(actual)

    W_single = {"freq": 0, "gap": 0, "pair": 0}
    W_single[component] = 1.0

    actual_score = _combo_score(actual, freq, gap, pair, W_single)

    # Monte Carlo sampling: compare against 2000 random combos from the pool
    import random
    rng = random.Random(42)
    beaten = 0
    trials = min(2000, len(all_nums) ** pick_n)
    for _ in range(trials):
        sample = rng.sample(all_nums, min(pick_n, len(all_nums)))
        s = _combo_score(sample, freq, gap, pair, W_single)
        if s < actual_score:
            beaten += 1

    return beaten / trials if trials else 0.5


# ── Calibration ───────────────────────────────────────────────────────────

def calibrate_lotto(state: str, slug: str, draws: list[dict],
                    window: int = CALIB_WINDOW) -> dict:
    """Rank-based calibration over the last `window` draws."""
    from analyzer_lotto import _normalize_draws
    draws = _normalize_draws(draws)
    min_history = 40
    rank_sums = {"freq": 0.0, "gap": 0.0, "pair": 0.0}
    tested = 0

    for i in range(min(window, len(draws))):
        history = draws[i + 1:]
        if len(history) < min_history:
            break
        actual = draws[i]["nums"]
        for comp in rank_sums:
            rank_sums[comp] += _rank_actual(history, actual, comp)
        tested += 1

    if tested == 0:
        return DEFAULT_WEIGHTS.copy()

    avg = {k: v / tested for k, v in rank_sums.items()}
    floored = {k: max(v, MIN_WEIGHT) for k, v in avg.items()}
    total = sum(floored.values())
    weights = {k: round(v / total, 4) for k, v in floored.items()}

    meta = {"state": state, "slug": slug, "draw_count": len(draws),
            "window": tested, "avg_rank": {k: round(v, 4) for k, v in avg.items()}}
    save_weights_lotto(state, slug, weights, meta)
    print(f"  [calibrator_lotto] {state}/{slug}: freq={weights['freq']} gap={weights['gap']} pair={weights['pair']} ({tested} draws tested)")
    return weights


def calibrate_lotto_if_needed(state: str, slug: str, draws: list[dict]) -> dict:
    if not draws:
        return DEFAULT_WEIGHTS.copy()
    if needs_recalibration_lotto(state, slug, len(draws)):
        return calibrate_lotto(state, slug, draws)
    return load_weights_lotto(state, slug)


if __name__ == "__main__":
    import sys, json as _json
    from games_scraper import load_game_results
    state = sys.argv[1].upper() if len(sys.argv) > 1 else "NC"
    slug  = sys.argv[2]         if len(sys.argv) > 2 else "cash5"
    draws = load_game_results(state, slug)
    if not draws:
        print(f"No data for {state}/{slug}")
    else:
        w = calibrate_lotto(state, slug, draws)
        print(f"  Result: {w}")
