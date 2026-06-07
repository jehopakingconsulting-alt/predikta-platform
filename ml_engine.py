"""
Ultra-advanced ML prediction engine for Cash3/Pick3.
Models: Random Forest, Gradient Boosting, XGBoost, Markov (orders 1-3),
        Fourier cycle analysis, Monte Carlo simulation, Ensemble consensus.
"""

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
from scipy.fft import fft
from scipy.stats import chi2_contingency, entropy

DIGITS = list(range(10))


# ─── Feature Engineering ───────────────────────────────────────────────────

def build_features(draws: list[dict], window: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """
    Build feature matrix X and target y for ML models.
    Features per sample (window of past draws):
      - last N digits per position (d1, d2, d3)
      - rolling frequency of each digit (0-9) over window
      - sum of last draw, parity pattern, gap since last seen
      - Markov-1 probabilities for each digit
    """
    if len(draws) < window + 5:
        return np.array([]), np.array([])

    data = [(int(d["d1"]), int(d["d2"]), int(d["d3"])) for d in reversed(draws)]
    X, y = [], []

    freq_window = max(window, 20)

    for i in range(window, len(data) - 1):
        past = data[i - window:i]
        target = data[i]

        feats = []

        # Last N draws flattened
        for draw in past[-5:]:
            feats.extend(draw)

        # Digit frequency over window (per position)
        for pos in range(3):
            cnt = Counter(d[pos] for d in data[max(0, i-freq_window):i])
            feats.extend([cnt.get(d, 0) / freq_window for d in DIGITS])

        # Sum, parity, high-low of last draw
        last = past[-1]
        feats.append(sum(last))
        feats.append(sum(1 for x in last if x % 2 == 0))  # even count
        feats.append(sum(1 for x in last if x >= 5))       # high count

        # Gap (draws since each digit last appeared across all positions)
        all_digits_flat = [d for draw in data[max(0, i-50):i] for d in draw]
        for dig in DIGITS:
            try:
                gap = len(all_digits_flat) - 1 - next(
                    j for j, v in enumerate(reversed(all_digits_flat)) if v == dig
                )
            except StopIteration:
                gap = 99
            feats.append(gap)

        # Markov-1: transition probability from last digit (per position)
        for pos in range(3):
            last_dig = past[-1][pos]
            trans = Counter(
                data[j][pos]
                for j in range(max(0, i-50), i - 1)
                if data[j][pos] == last_dig
            )
            total = sum(trans.values()) or 1
            # probability of each next digit given last
            feats.extend([trans.get(d, 0) / total for d in DIGITS])

        X.append(feats)
        # Target: each position as separate label (we train 3 models)
        y.append(target)

    return np.array(X, dtype=np.float32), np.array(y)


# ─── Markov Chains (orders 1, 2, 3) ───────────────────────────────────────

def markov_predict(draws: list[dict], position: str, order: int = 1) -> dict[int, float]:
    """Return probability distribution for next digit at given position."""
    seq = [int(d[position]) for d in reversed(draws)]
    if len(seq) < order + 2:
        return {d: 0.1 for d in DIGITS}

    transitions = defaultdict(Counter)
    for i in range(order, len(seq)):
        key = tuple(seq[i - order:i])
        transitions[key][seq[i]] += 1

    last_key = tuple(seq[-order:])
    counts = transitions.get(last_key, Counter())

    if not counts:
        # fall back to lower order
        return markov_predict(draws, position, max(1, order - 1)) if order > 1 else {d: 0.1 for d in DIGITS}

    total = sum(counts.values())
    # Laplace smoothing
    return {d: (counts.get(d, 0) + 1) / (total + 10) for d in DIGITS}


def markov_matrix(draws: list[dict], position: str) -> dict:
    """Full transition matrix for display."""
    seq = [int(d[position]) for d in reversed(draws)]
    matrix = defaultdict(Counter)
    for i in range(1, len(seq)):
        matrix[seq[i-1]][seq[i]] += 1
    result = {}
    for from_d, counts in matrix.items():
        total = sum(counts.values())
        result[str(from_d)] = {str(k): round(v / total * 100, 1) for k, v in counts.items()}
    return result


# ─── Fourier Cycle Analysis ────────────────────────────────────────────────

def fourier_cycles(draws: list[dict], position: str) -> dict:
    """
    Detect repeating cycles in digit sequence using FFT.
    Returns dominant cycle length and predicted next digit.
    """
    seq = np.array([int(d[position]) for d in reversed(draws)], dtype=float)
    if len(seq) < 20:
        return {"cycle": None, "prediction": None}

    # Normalize
    seq_norm = seq - seq.mean()
    spectrum = np.abs(fft(seq_norm))
    freqs = np.fft.fftfreq(len(seq_norm))

    # Find dominant frequency (ignore DC component)
    pos_freqs = spectrum[1:len(spectrum)//2]
    dominant_idx = np.argmax(pos_freqs) + 1
    dominant_period = int(round(1 / abs(freqs[dominant_idx]))) if freqs[dominant_idx] != 0 else None

    # Predict based on cycle: look back `period` steps
    predicted = None
    if dominant_period and dominant_period < len(seq):
        cycle_vals = seq[-dominant_period:]
        predicted = int(round(np.mean(cycle_vals))) % 10

    return {
        "cycle_length": dominant_period,
        "predicted_digit": predicted,
        "spectrum_peak": float(pos_freqs[dominant_idx - 1]),
    }


# ─── Monte Carlo Simulation ────────────────────────────────────────────────

def monte_carlo(draws: list[dict], n_simulations: int = 50000) -> list[dict]:
    """
    Simulate N future draws using empirical per-position distributions.
    Returns top combos by frequency.
    """
    if not draws:
        return []

    # Build empirical distribution per position
    dists = {}
    for pos in ["d1", "d2", "d3"]:
        cnt = Counter(int(d[pos]) for d in draws)
        total = sum(cnt.values())
        dists[pos] = np.array([cnt.get(d, 0) / total for d in DIGITS])

    results = Counter()
    rng = np.random.default_rng(42)

    for _ in range(n_simulations):
        combo = tuple(
            rng.choice(DIGITS, p=dists[pos])
            for pos in ["d1", "d2", "d3"]
        )
        results[combo] += 1

    top = results.most_common(20)
    total = sum(results.values())
    return [
        {
            "combo": f"{c[0]}-{c[1]}-{c[2]}",
            "digits": list(c),
            "mc_probability": round(count / total * 100, 3),
        }
        for c, count in top
    ]


# ─── ML Models (Random Forest + GBM + XGBoost) ────────────────────────────

class MLPredictor:
    def __init__(self):
        self.models = {
            "rf":  [RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1) for _ in range(3)],
            "gbm": [GradientBoostingClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42) for _ in range(3)],
            "xgb": [XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, verbosity=0, random_state=42) for _ in range(3)],
        }
        self.trained = False
        self.feature_count = 0

    def train(self, X: np.ndarray, y: np.ndarray):
        if len(X) < 30:
            return False
        self.feature_count = X.shape[1]
        for name, model_list in self.models.items():
            for pos in range(3):
                model_list[pos].fit(X, y[:, pos])
        self.trained = True
        return True

    def predict_proba_position(self, X_last: np.ndarray, position: int) -> dict[int, float]:
        """Ensemble probability for one position."""
        if not self.trained:
            return {d: 0.1 for d in DIGITS}

        probas = []
        weights = {"rf": 0.35, "gbm": 0.30, "xgb": 0.35}

        for name, model_list in self.models.items():
            model = model_list[position]
            classes = list(model.classes_)
            proba = model.predict_proba(X_last)[0]
            prob_dict = {cls: p for cls, p in zip(classes, proba)}
            weighted = {d: prob_dict.get(d, 0.0) * weights[name] for d in DIGITS}
            probas.append(weighted)

        # Average across models
        ensemble = {}
        for d in DIGITS:
            ensemble[d] = sum(p[d] for p in probas)

        # Normalize
        total = sum(ensemble.values()) or 1
        return {d: v / total for d, v in ensemble.items()}

    def predict_top(self, X_last: np.ndarray, top_n: int = 10) -> list[dict]:
        """Generate top N combos from ensemble probabilities."""
        proba = [self.predict_proba_position(X_last, pos) for pos in range(3)]

        scores = {}
        for d1 in DIGITS:
            for d2 in DIGITS:
                for d3 in DIGITS:
                    scores[(d1, d2, d3)] = proba[0][d1] * proba[1][d2] * proba[2][d3]

        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        max_score = top[0][1] if top else 1

        return [
            {
                "combo": f"{c[0]}-{c[1]}-{c[2]}",
                "digits": list(c),
                "ml_score": round(s * 1000, 4),
                "ml_probability": round(s / max_score * 100, 2),
            }
            for c, s in top
        ]


# ─── Advanced Statistics ───────────────────────────────────────────────────

def sum_analysis(draws: list[dict]) -> dict:
    """Distribution of digit sums (0-27 for Pick3)."""
    sums = [int(d["d1"]) + int(d["d2"]) + int(d["d3"]) for d in draws]
    cnt = Counter(sums)
    total = len(sums) or 1
    last_sum = sums[0] if sums else None

    # Most overdue sums
    all_sums = list(range(28))
    overdue = sorted(all_sums, key=lambda s: -sums[::-1].index(s) if s in sums else 9999)

    return {
        "distribution": {str(s): {"count": cnt.get(s, 0), "pct": round(cnt.get(s, 0)/total*100, 2)} for s in all_sums},
        "last_sum": last_sum,
        "most_common_sum": cnt.most_common(1)[0][0] if cnt else None,
        "overdue_sums": overdue[:5],
    }


def parity_analysis(draws: list[dict]) -> dict:
    """Odd/Even patterns (EEE, OOO, OEO, etc.)"""
    patterns = []
    for d in draws:
        p = "".join("E" if int(d[k]) % 2 == 0 else "O" for k in ["d1", "d2", "d3"])
        patterns.append(p)
    cnt = Counter(patterns)
    total = len(patterns) or 1
    return {p: {"count": c, "pct": round(c/total*100, 2)} for p, c in cnt.most_common()}


def high_low_analysis(draws: list[dict]) -> dict:
    """High (5-9) vs Low (0-4) patterns."""
    patterns = []
    for d in draws:
        p = "".join("H" if int(d[k]) >= 5 else "L" for k in ["d1", "d2", "d3"])
        patterns.append(p)
    cnt = Counter(patterns)
    total = len(patterns) or 1
    return {p: {"count": c, "pct": round(c/total*100, 2)} for p, c in cnt.most_common()}


def consecutive_analysis(draws: list[dict]) -> dict:
    """How often consecutive digits appear (e.g. 1-2-3, 4-5-6)."""
    consec = 0
    for d in draws:
        nums = sorted([int(d["d1"]), int(d["d2"]), int(d["d3"])])
        if nums[1] - nums[0] == 1 and nums[2] - nums[1] == 1:
            consec += 1
    total = len(draws) or 1
    return {"consecutive_count": consec, "pct": round(consec/total*100, 2)}


def digit_gap_analysis(draws: list[dict]) -> dict:
    """Per-digit gap stats: current gap, avg gap, overdue status, due probability."""
    positions = ["d1", "d2", "d3"]
    digit_appearances = defaultdict(list)

    for i, d in enumerate(draws):
        for pos in positions:
            digit_appearances[int(d[pos])].append(i)

    result = {}
    for dig in DIGITS:
        appearances = digit_appearances[dig]
        if not appearances:
            result[str(dig)] = {"current_gap": len(draws), "avg_gap": None, "overdue": True, "due_prob": 0.99}
            continue

        gaps = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
        avg_gap = np.mean(gaps) if gaps else None
        current_gap = appearances[0]  # draws since last seen

        overdue = current_gap > (avg_gap or 0)
        due_prob = min(0.99, current_gap / (avg_gap or max(current_gap, 1)))

        result[str(dig)] = {
            "current_gap": current_gap,
            "avg_gap": round(avg_gap, 1) if avg_gap else None,
            "min_gap": int(min(gaps)) if gaps else None,
            "max_gap": int(max(gaps)) if gaps else None,
            "overdue": overdue,
            "due_prob": round(due_prob, 3),
        }
    return result


def entropy_analysis(draws: list[dict]) -> dict:
    """Shannon entropy of digit distribution per position (randomness measure)."""
    result = {}
    for pos in ["d1", "d2", "d3"]:
        cnt = Counter(int(d[pos]) for d in draws)
        total = sum(cnt.values()) or 1
        probs = [cnt.get(d, 0) / total for d in DIGITS]
        ent = entropy(probs, base=10)
        result[pos] = {
            "entropy": round(ent, 4),
            "max_entropy": round(np.log10(10), 4),
            "uniformity_pct": round(ent / np.log10(10) * 100, 1),
        }
    return result


def chi_square_test(draws: list[dict]) -> dict:
    """Chi-square test for uniformity of digit distribution."""
    result = {}
    for pos in ["d1", "d2", "d3"]:
        cnt = Counter(int(d[pos]) for d in draws)
        observed = [cnt.get(d, 0) for d in DIGITS]
        expected = [len(draws) / 10] * 10
        chi2 = sum((o - e)**2 / e for o, e in zip(observed, expected) if e > 0)
        result[pos] = {
            "chi2": round(chi2, 3),
            "interpretation": "Distribution uniforme" if chi2 < 16.92 else "Biais détecté (p<0.05)",
        }
    return result


def hot_cold_stats(draws: list[dict], window: int = 30) -> dict:
    recent = draws[:window]
    result = {}
    for pos in ["d1", "d2", "d3"]:
        cnt = Counter(int(d[pos]) for d in recent)
        total = sum(cnt.values()) or 1
        avg = total / 10
        result[pos] = {}
        for d in DIGITS:
            c = cnt.get(d, 0)
            result[pos][str(d)] = {
                "count": c,
                "pct": round(c / total * 100, 2),
                "status": "HOT" if c > avg * 1.3 else ("COLD" if c < avg * 0.7 else "NEUTRAL"),
            }
    return result


def pair_frequencies(draws: list[dict]) -> dict:
    counter = Counter()
    for d in draws:
        nums = [d["d1"], d["d2"], d["d3"]]
        for i in range(3):
            for j in range(i+1, 3):
                pair = tuple(sorted([nums[i], nums[j]]))
                counter[pair] += 1
    total = len(draws) or 1
    return {
        f"{p[0]}-{p[1]}": {"count": c, "pct": round(c / total * 100, 2)}
        for p, c in counter.most_common(20)
    }


# ─── Ensemble Consensus ────────────────────────────────────────────────────

def ensemble_consensus(
    markov1: list[dict],
    markov2: list[dict],
    markov3: list[dict],
    ml_preds: list[dict],
    mc_preds: list[dict],
    fourier_hints: dict,
    draws: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    Combine all models into a final weighted consensus score.
    Weights: ML=35%, Markov(1+2+3)=30%, MonteCarlo=20%, Fourier=10%, Gap=5%
    """
    gaps = digit_gap_analysis(draws)
    combo_scores = defaultdict(float)

    # Score from each source
    def idx_score(pred_list: list[dict], combo: str, weight: float, key: str = "score"):
        for i, p in enumerate(pred_list):
            if p.get("combo") == combo:
                rank_bonus = (len(pred_list) - i) / len(pred_list)
                combo_scores[combo] += weight * rank_bonus
                break

    all_combos = set()

    # Collect all candidate combos
    for p in markov1 + markov2 + markov3 + ml_preds + mc_preds:
        all_combos.add(p["combo"])

    # Add Fourier hint combos
    f_digits = {}
    for pos, key in [("d1", "d1"), ("d2", "d2"), ("d3", "d3")]:
        pred = fourier_hints.get(pos, {}).get("predicted_digit")
        if pred is not None:
            f_digits[pos] = pred

    if len(f_digits) == 3:
        fc = f"{f_digits['d1']}-{f_digits['d2']}-{f_digits['d3']}"
        all_combos.add(fc)

    for combo in all_combos:
        idx_score(ml_preds, combo, 0.35)
        idx_score(markov1, combo, 0.12)
        idx_score(markov2, combo, 0.10)
        idx_score(markov3, combo, 0.08)
        idx_score(mc_preds, combo, 0.20)

        # Fourier bonus
        parts = combo.split("-")
        if len(parts) == 3 and len(f_digits) == 3:
            matches = sum(1 for pos, key in [("d1",0),("d2",1),("d3",2)] if f_digits.get(pos) == int(parts[key]))
            combo_scores[combo] += 0.10 * (matches / 3)

        # Gap/overdue bonus
        for part in parts:
            g = gaps.get(part, {})
            combo_scores[combo] += 0.05 * g.get("due_prob", 0)

    top = sorted(combo_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    max_score = top[0][1] if top else 1

    return [
        {
            "combo": combo,
            "digits": [int(x) for x in combo.split("-")],
            "consensus_score": round(score, 4),
            "confidence_pct": round(score / max_score * 100, 1),
            "confidence_label": _conf_label(score / max_score),
        }
        for combo, score in top
    ]


def _conf_label(ratio: float) -> str:
    if ratio >= 0.95: return "Très Élevée ★★★★★"
    if ratio >= 0.85: return "Élevée ★★★★"
    if ratio >= 0.70: return "Moyenne ★★★"
    if ratio >= 0.55: return "Modérée ★★"
    return "Faible ★"


# ─── Top-level runner ──────────────────────────────────────────────────────

def run_all_models(draws: list[dict]) -> dict:
    """Run every model and return combined results."""
    if not draws:
        return {"error": "Pas de données. Lancez le scraper d'abord."}

    pos_labels = {"d1": "Position 1", "d2": "Position 2", "d3": "Position 3"}

    # Markov chains (orders 1, 2, 3) — generate top combos by product of proba
    def markov_top(order: int, n: int = 15) -> list[dict]:
        proba = [markov_predict(draws, pos, order) for pos in ["d1", "d2", "d3"]]
        scores = {}
        for d1 in DIGITS:
            for d2 in DIGITS:
                for d3 in DIGITS:
                    scores[(d1, d2, d3)] = proba[0][d1] * proba[1][d2] * proba[2][d3]
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        return [{"combo": f"{c[0]}-{c[1]}-{c[2]}", "digits": list(c), "score": round(s, 6)} for c, s in top]

    m1 = markov_top(1)
    m2 = markov_top(2)
    m3 = markov_top(3)

    # ML models
    X, y = build_features(draws, window=10)
    predictor = MLPredictor()
    ml_preds = []
    if len(X) >= 30:
        predictor.train(X, y)
        X_last = X[-1:].reshape(1, -1)
        ml_preds = predictor.predict_top(X_last, top_n=15)

    # Monte Carlo
    mc_preds = monte_carlo(draws, n_simulations=50000)

    # Fourier
    fourier = {pos: fourier_cycles(draws, pos) for pos in ["d1", "d2", "d3"]}

    # Ensemble consensus
    consensus = ensemble_consensus(m1, m2, m3, ml_preds, mc_preds, fourier, draws)

    return {
        "markov_order1_top": m1[:10],
        "markov_order2_top": m2[:10],
        "markov_order3_top": m3[:10],
        "markov_matrix_d1": markov_matrix(draws, "d1"),
        "ml_predictions": ml_preds[:10],
        "ml_trained": predictor.trained,
        "monte_carlo_top": mc_preds[:10],
        "fourier": fourier,
        "consensus": consensus,
        "sum_analysis": sum_analysis(draws),
        "parity": parity_analysis(draws),
        "high_low": high_low_analysis(draws),
        "consecutive": consecutive_analysis(draws),
        "gaps": digit_gap_analysis(draws),
        "entropy": entropy_analysis(draws),
        "chi_square": chi_square_test(draws),
        "hot_cold_30": hot_cold_stats(draws, 30),
        "hot_cold_60": hot_cold_stats(draws, 60),
        "pairs": pair_frequencies(draws),
        "total_draws": len(draws),
        "last_draw": draws[0] if draws else None,
    }
