"""
ZYNORIQ — Ensemble Weight Auto-Calibrator
==========================================
For each state + TOD, backtests the ensemble components (ML, Markov,
Product-Dist, Fourier, Gap) against real draws and adjusts weights
proportionally to each component's predictive performance.

Runs automatically every RECALIBRATE_EVERY new draws (detected via
draw count change). Weights saved to data/ensemble_weights/.

This calibrates the *consensus* weights (ml_engine.ensemble_consensus),
separate from the analyzer-level freq/gap/markov weights.
"""

import json
import os
import math
from collections import defaultdict, Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "ensemble_weights")
os.makedirs(DATA_DIR, exist_ok=True)

DIGITS = list(range(10))

DEFAULT_WEIGHTS = {
    "ml": 0.30,
    "markov": 0.25,
    "product_dist": 0.20,
    "fourier": 0.10,
    "gap": 0.05,
    "lstm": 0.10,
}

MIN_WEIGHT = 0.05
CALIB_WINDOW = 30
RECALIBRATE_EVERY = 10
MIN_HISTORY = 80


def _weights_path(state_code: str, tod: str) -> str:
    tod_slug = (tod or "all").replace(" ", "_").lower()
    return os.path.join(DATA_DIR, f"{state_code.upper()}_{tod_slug}_ensemble.json")


def load_ensemble_weights(state_code: str, tod: str = None) -> dict:
    path = _weights_path(state_code, tod or "all")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                w = data.get("weights", {})
                if w and all(k in w for k in DEFAULT_WEIGHTS):
                    return w
        except Exception:
            pass
    return DEFAULT_WEIGHTS.copy()


def save_ensemble_weights(state_code: str, tod: str, weights: dict, meta: dict = None):
    path = _weights_path(state_code, tod or "all")
    payload = {"weights": weights, "meta": meta or {}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def needs_recalibration(state_code: str, tod: str, current_draw_count: int) -> bool:
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


def _product_dist_rank(draws, actual_combo):
    """Rank actual combo by product-distribution score (higher = better)."""
    dists = {}
    for pos in ["d1", "d2", "d3"]:
        cnt = Counter(int(d[pos]) for d in draws)
        total = sum(cnt.values()) or 1
        dists[pos] = {d: cnt.get(d, 0) / total for d in DIGITS}

    actual_score = (dists["d1"].get(actual_combo[0], 0) *
                    dists["d2"].get(actual_combo[1], 0) *
                    dists["d3"].get(actual_combo[2], 0))

    beaten = 0
    for a in DIGITS:
        for b in DIGITS:
            for c in DIGITS:
                s = dists["d1"].get(a, 0) * dists["d2"].get(b, 0) * dists["d3"].get(c, 0)
                if s < actual_score:
                    beaten += 1
    return beaten / 999


def _markov_rank(draws, actual_combo):
    """Rank actual combo by Markov-1 transition probability."""
    if len(draws) < 2:
        return 0.5

    last_draw = draws[0]
    trans_scores = {}
    for i, pos in enumerate(["d1", "d2", "d3"]):
        matrix = defaultdict(Counter)
        prev = None
        for d in reversed(draws):
            curr = int(d[pos])
            if prev is not None:
                matrix[prev][curr] += 1
            prev = curr
        last_digit = int(last_draw[pos])
        transitions = matrix.get(last_digit, Counter())
        total = sum(transitions.values()) or 1
        trans_scores[pos] = {d: transitions.get(d, 0) / total for d in DIGITS}

    actual_score = 1.0
    for i, pos in enumerate(["d1", "d2", "d3"]):
        actual_score *= trans_scores[pos].get(actual_combo[i], 0.001)

    beaten = 0
    for a in DIGITS:
        for b in DIGITS:
            for c in DIGITS:
                s = (trans_scores["d1"].get(a, 0.001) *
                     trans_scores["d2"].get(b, 0.001) *
                     trans_scores["d3"].get(c, 0.001))
                if s < actual_score:
                    beaten += 1
    return beaten / 999


def _gap_rank(draws, actual_combo):
    """Rank actual combo by gap/overdue scores."""
    last_seen = {}
    gap_sums = defaultdict(int)
    gap_counts = defaultdict(int)

    for i, d in enumerate(reversed(draws)):
        for pos in ["d1", "d2", "d3"]:
            digit = int(d[pos])
            if digit not in last_seen:
                last_seen[digit] = i
            else:
                gap = i - last_seen[digit]
                gap_sums[digit] += gap
                gap_counts[digit] += 1
                last_seen[digit] = i

    due_scores = {}
    for dig in DIGITS:
        avg_gap = gap_sums[dig] / gap_counts[dig] if gap_counts[dig] else None
        current_gap = len(draws) - 1 - last_seen.get(dig, -1)
        due_scores[dig] = min(0.99, current_gap / avg_gap) if avg_gap else 0.5

    actual_score = sum(due_scores.get(actual_combo[i], 0) for i in range(3))

    beaten = 0
    for a in DIGITS:
        for b in DIGITS:
            for c in DIGITS:
                s = due_scores.get(a, 0) + due_scores.get(b, 0) + due_scores.get(c, 0)
                if s < actual_score:
                    beaten += 1
    return beaten / 999


def _ml_rank(draws, actual_combo):
    """Rank actual combo by ML ensemble (RF+GBM+XGB) probability."""
    try:
        from ml_engine import MLPredictor, build_features
        import numpy as np

        X, y = build_features(draws[1:])
        if len(X) < 30:
            return 0.5

        predictor = MLPredictor()
        predictor.train(X, y)
        proba = predictor.predict_proba_position(X[-1:])

        actual_score = 1.0
        for i, pos in enumerate(["d1", "d2", "d3"]):
            actual_score *= proba[pos].get(actual_combo[i], 0.001)

        beaten = 0
        for a in DIGITS:
            for b in DIGITS:
                for c in DIGITS:
                    s = (proba["d1"].get(a, 0.001) *
                         proba["d2"].get(b, 0.001) *
                         proba["d3"].get(c, 0.001))
                    if s < actual_score:
                        beaten += 1
        return beaten / 999
    except Exception:
        return 0.5


def calibrate_ensemble(state_code: str, tod: str, draws: list[dict],
                       window: int = CALIB_WINDOW) -> dict:
    """
    Backtest each ensemble component independently over the last `window`
    draws. Measure how well each ranks the actual result. Set weights
    proportional to average ranking performance.
    """
    if len(draws) < MIN_HISTORY:
        return DEFAULT_WEIGHTS.copy()

    # Components to test (skip ML for speed — it's expensive to retrain per step)
    components = {
        "product_dist": _product_dist_rank,
        "markov": _markov_rank,
        "gap": _gap_rank,
    }

    rank_sums = {k: 0.0 for k in components}
    tested = 0

    for i in range(min(window, len(draws) - MIN_HISTORY)):
        actual = draws[i]
        history = draws[i + 1:]
        actual_combo = (int(actual["d1"]), int(actual["d2"]), int(actual["d3"]))

        for name, rank_fn in components.items():
            try:
                rank_sums[name] += rank_fn(history, actual_combo)
            except Exception:
                rank_sums[name] += 0.5

        tested += 1

    if tested == 0:
        return DEFAULT_WEIGHTS.copy()

    avg_ranks = {k: v / tested for k, v in rank_sums.items()}

    # ML and LSTM get fixed shares (too expensive to backtest per-draw)
    # but scale slightly based on how well the fast components perform
    total_fast = sum(avg_ranks.values()) or 1.0

    weights = {}
    weights["ml"] = 0.30
    weights["lstm"] = 0.10
    weights["fourier"] = 0.08

    remaining = 1.0 - weights["ml"] - weights["lstm"] - weights["fourier"]
    for k in ["product_dist", "markov", "gap"]:
        raw = avg_ranks[k] / total_fast * remaining
        weights[k] = max(MIN_WEIGHT, raw)

    # Normalize to sum to 1.0
    total_w = sum(weights.values())
    weights = {k: round(v / total_w, 4) for k, v in weights.items()}

    save_ensemble_weights(state_code, tod, weights, meta={
        "draw_count": len(draws),
        "tested": tested,
        "avg_ranks": {k: round(v, 4) for k, v in avg_ranks.items()},
    })

    return weights


def calibrate_if_needed(state_code: str, tod: str, draws: list[dict]) -> dict:
    """Load cached weights or recalibrate if enough new draws arrived."""
    if not needs_recalibration(state_code, tod, len(draws)):
        return load_ensemble_weights(state_code, tod)
    return calibrate_ensemble(state_code, tod, draws)
