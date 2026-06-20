"""
ZYNORIQ — Dynamic Weight Calibrator for Pick 4
Per state + time-of-day, backtests the last N draws and measures how well
each scoring component (freq, gap, markov) ranks real combos vs. random.
Weights are saved to data/weights4/{STATE}_{TOD}.json and consumed by
ml_engine4 / analyzer4 via load_weights4().

Auto-recalibrates every RECALIBRATE_EVERY draws.
"""

import json
import os
from collections import defaultdict, Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "weights4")
os.makedirs(DATA_DIR, exist_ok=True)

DIGITS = [str(i) for i in range(10)]
POSITIONS = ["d1", "d2", "d3", "d4"]

DEFAULT_WEIGHTS = {"freq": 0.34, "gap": 0.28, "markov": 0.38}
MIN_WEIGHT = 0.10
CALIB_WINDOW = 40
RECALIBRATE_EVERY = 10


# ── Weight persistence ────────────────────────────────────────────────────

def _weights_path(state_code: str, tod: str) -> str:
    tod_slug = (tod or "all").replace(" ", "_").lower()
    return os.path.join(DATA_DIR, f"{state_code.upper()}_{tod_slug}.json")


def load_weights4(state_code: str, tod: str = None) -> dict:
    """Load saved weights for a state+tod, or return defaults."""
    path = _weights_path(state_code, tod or "all")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("weights", DEFAULT_WEIGHTS)
        except Exception:
            pass
    return DEFAULT_WEIGHTS.copy()


def save_weights4(state_code: str, tod: str, weights: dict, meta: dict = None):
    """Persist calibrated weights with metadata."""
    path = _weights_path(state_code, tod or "all")
    payload = {"weights": weights, "meta": meta or {}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def needs_recalibration4(state_code: str, tod: str, current_draw_count: int) -> bool:
    """Return True if enough new draws have arrived since last calibration."""
    path = _weights_path(state_code, tod or "all")
    if not os.path.exists(path):
        return True
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        last_count = data.get("meta", {}).get("draw_count", 0)
        return (current_draw_count - last_count) >= RECALIBRATE_EVERY
    except Exception:
        return True


# ── Per-component scoring (isolated) ─────────────────────────────────────

def _freq_scores(draws: list[dict]) -> dict[str, dict[str, float]]:
    """Per-position frequency score for each digit (0-10 scale)."""
    result = {}
    for pos in POSITIONS:
        counter = Counter(d[pos] for d in draws)
        total = sum(counter.values()) or 1
        result[pos] = {digit: (counter[digit] / total * 10) for digit in DIGITS}
    return result


def _gap_scores(draws: list[dict]) -> dict[str, float]:
    """Gap/overdue score for each digit (bonus when overdue)."""
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

    scores = {}
    for digit in DIGITS:
        avg_gap = gap_sums[digit] / gap_counts[digit] if gap_counts[digit] else None
        current_gap = len(draws) - 1 - last_seen.get(digit, len(draws) - 1)
        if avg_gap and current_gap > avg_gap:
            scores[digit] = min(current_gap / avg_gap, 3.0)
        else:
            scores[digit] = 0.0
    return scores


def _markov_scores(draws: list[dict]) -> dict[str, dict[str, float]]:
    """Markov transition score per position: P(next | last)."""
    if not draws:
        return {pos: {d: 0.0 for d in DIGITS} for pos in POSITIONS}

    last_draw = draws[0]
    result = {}
    for pos in POSITIONS:
        matrix = defaultdict(Counter)
        prev = None
        for d in reversed(draws):
            curr = d[pos]
            if prev is not None:
                matrix[prev][curr] += 1
            prev = curr

        last_digit = last_draw[pos]
        transitions = matrix.get(last_digit, Counter())
        total = sum(transitions.values()) or 1
        result[pos] = {digit: (transitions[digit] / total * 5) for digit in DIGITS}
    return result


def _score_combo_by_component(combo, freq, gaps, markov):
    """Return (freq_score, gap_score, markov_score) for a given 4-digit combo."""
    f_score = g_score = m_score = 0.0
    for digit, pos in zip(combo, POSITIONS):
        f_score += freq[pos][digit]
        g_score += gaps[digit]
        m_score += markov[pos][digit]
    return f_score, g_score, m_score


def _rank_score_for_actual(draws, actual_combo, component) -> float:
    """
    Rank the actual combo among all 10,000 using one component only.
    Returns percentile: 1.0 = top rank, 0.0 = bottom.
    """
    freq = _freq_scores(draws)
    gaps = _gap_scores(draws)
    markov = _markov_scores(draws)

    actual_f, actual_g, actual_m = _score_combo_by_component(actual_combo, freq, gaps, markov)
    actual_score = actual_f if component == "freq" else (actual_g if component == "gap" else actual_m)

    beaten = 0
    total = 0
    for d1 in DIGITS:
        for d2 in DIGITS:
            for d3 in DIGITS:
                for d4 in DIGITS:
                    f, g, m = _score_combo_by_component((d1, d2, d3, d4), freq, gaps, markov)
                    s = f if component == "freq" else (g if component == "gap" else m)
                    if s < actual_score:
                        beaten += 1
                    total += 1

    return beaten / (total - 1) if total > 1 else 0.5


# ── Calibration ───────────────────────────────────────────────────────────

def calibrate4(state_code: str, tod: str, draws: list[dict],
               window: int = CALIB_WINDOW) -> dict:
    """
    Rank-based calibration over the last `window` draws.
    Each component earns weight proportional to how consistently it ranks
    real draws near the top of 10,000 candidates.
    """
    min_history = 60
    rank_sums = {"freq": 0.0, "gap": 0.0, "markov": 0.0}
    tested = 0

    for i in range(min(window, len(draws))):
        history = draws[i + 1:]
        if len(history) < min_history:
            break

        actual = draws[i]
        actual_combo = (actual["d1"], actual["d2"], actual["d3"], actual["d4"])

        for component in rank_sums:
            rank_sums[component] += _rank_score_for_actual(history, actual_combo, component)

        tested += 1

    if tested == 0:
        return DEFAULT_WEIGHTS.copy()

    avg_ranks = {k: v / tested for k, v in rank_sums.items()}
    floored = {k: max(v, MIN_WEIGHT) for k, v in avg_ranks.items()}
    total = sum(floored.values())
    weights = {k: round(v / total, 4) for k, v in floored.items()}

    meta = {
        "state": state_code,
        "tod": tod,
        "draw_count": len(draws),
        "window": tested,
        "avg_rank_percentile": {k: round(v, 4) for k, v in avg_ranks.items()},
    }

    save_weights4(state_code, tod, weights, meta)
    print(f"  [calibrator4] {state_code} {tod}: freq={weights['freq']} gap={weights['gap']} markov={weights['markov']} (tested {tested} draws)")
    return weights


def calibrate4_if_needed(state_code: str, tod: str, draws: list[dict]) -> dict:
    """Calibrate only if enough new draws arrived since last calibration."""
    if not draws:
        return DEFAULT_WEIGHTS.copy()
    if needs_recalibration4(state_code, tod, len(draws)):
        return calibrate4(state_code, tod, draws)
    return load_weights4(state_code, tod)


# ── Combined score ────────────────────────────────────────────────────────

def combo_score4(combo, freq, gaps, markov, weights):
    """Unified score using dynamic weights for a 4-digit combo."""
    f, g, m = _score_combo_by_component(combo, freq, gaps, markov)
    return (weights["freq"] * f) + (weights["gap"] * g) + (weights["markov"] * m)


# ── Bulk recalibration ────────────────────────────────────────────────────

def recalibrate_all4(states_draws: dict):
    """
    Recalibrate all states. states_draws: {state_code: draws_list}
    Call from app.py after auto-update scraping.
    """
    for state_code, draws in states_draws.items():
        if not draws:
            continue
        tods = list({d.get("tod", "Evening") for d in draws})
        for tod in tods:
            tod_draws = [d for d in draws if d.get("tod", "Evening") == tod]
            if len(tod_draws) >= 70:
                calibrate4_if_needed(state_code, tod, tod_draws)


if __name__ == "__main__":
    import sys
    from scraper4 import load_csv4
    state = sys.argv[1].upper() if len(sys.argv) > 1 else "NY"
    draws = load_csv4(state)
    if not draws:
        print(f"No Pick 4 data for {state}")
    else:
        tods = list({d.get("tod", "Evening") for d in draws})
        for tod in tods:
            tod_draws = [d for d in draws if d.get("tod", "Evening") == tod]
            if len(tod_draws) >= 70:
                w = calibrate4(state, tod, tod_draws)
                print(f"  → {tod}: {w}")
