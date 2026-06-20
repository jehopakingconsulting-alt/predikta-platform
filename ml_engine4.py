"""
ZYNORIQ — Ultra-advanced ML prediction engine for Pick 4 / Cash 4 / Win 4 / Daily 4.
Models: Random Forest, Gradient Boosting, XGBoost, Markov (orders 1-3),
        Fourier cycle analysis, Monte Carlo simulation, Ensemble consensus.
Adapted from ml_engine.py for 4-digit draws (10 000 possible combos).
"""

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from collections import Counter, defaultdict

# ─── Lazy-loaded heavy ML/scientific libraries ─────────────────────────────
_RF_CLS = _GBM_CLS = _XGB_CLS = None
_FFT_FN = None
_ENTROPY_FN = None


def _ensure_sklearn_models():
    global _RF_CLS, _GBM_CLS, _XGB_CLS
    if _RF_CLS is None:
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from xgboost import XGBClassifier
        _RF_CLS, _GBM_CLS, _XGB_CLS = RandomForestClassifier, GradientBoostingClassifier, XGBClassifier
    return _RF_CLS, _GBM_CLS, _XGB_CLS


def _ensure_fft():
    global _FFT_FN
    if _FFT_FN is None:
        from scipy.fft import fft
        _FFT_FN = fft
    return _FFT_FN


def _ensure_entropy():
    global _ENTROPY_FN
    if _ENTROPY_FN is None:
        from scipy.stats import entropy
        _ENTROPY_FN = entropy
    return _ENTROPY_FN


DIGITS = list(range(10))
POSITIONS = ["d1", "d2", "d3", "d4"]


# ─── Pick 4 Bet Recommendation ────────────────────────────────────────────

def bet_recommendation4(digits: list, confidence: str) -> dict:
    """
    Recommend the optimal Pick 4 bet type based on combo structure.
    Odds reference:
      Straight   : 1/10 000  — exact order
      Box 24-way : 1/417     — 4 different digits
      Box 12-way : 1/833     — one pair (e.g. 1-1-2-3)
      Box 6-way  : 1/1 667   — two pairs (e.g. 1-1-2-2)
      Box 4-way  : 1/2 500   — one triplet (e.g. 1-1-1-2)
    """
    counts = Counter(str(d) for d in digits)
    unique = len(counts)
    max_cnt = max(counts.values())
    high_conf = confidence in ("Tendance très forte ★★★★★", "Tendance forte ★★★★",
                               "Tendance très forte", "Tendance forte")

    if unique == 1:
        return {
            "bet_type": "Straight",
            "odds": "1/10 000",
            "reason": "Quadruplet — Straight uniquement",
            "payout_note": "Payout max si exact",
            "combo_type": "Quadruplet",
        }
    elif unique == 4:
        bt = "Box 24-way + Straight" if high_conf else "Box 24-way"
        return {
            "bet_type": bt,
            "odds": "1/417 + 1/10 000" if high_conf else "1/417",
            "reason": "4 chiffres différents — meilleure couverture Box",
            "payout_note": "Box si ordre incorrect, Straight si exact" if high_conf else "Meilleur rapport risque/rendement",
            "combo_type": "4 chiffres différents",
        }
    elif unique == 3:
        bt = "Box 12-way + Straight" if high_conf else "Box 12-way"
        return {
            "bet_type": bt,
            "odds": "1/833 + 1/10 000" if high_conf else "1/833",
            "reason": "1 paire — Box 12-way recommandé",
            "payout_note": "Box si ordre incorrect, Straight si exact" if high_conf else "Protège contre l'ordre",
            "combo_type": "1 paire",
        }
    else:  # unique == 2
        if max_cnt == 3:
            return {
                "bet_type": "Box 4-way",
                "odds": "1/2 500",
                "reason": "Triplet + 1 — Box 4-way uniquement",
                "payout_note": "4 arrangements possibles",
                "combo_type": "Triplet",
            }
        else:  # two pairs
            return {
                "bet_type": "Box 6-way",
                "odds": "1/1 667",
                "reason": "2 paires — Box 6-way",
                "payout_note": "6 arrangements possibles",
                "combo_type": "2 paires",
            }


# ─── Feature Engineering ───────────────────────────────────────────────────

def build_features4(draws: list[dict], window: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """
    Build feature matrix X and target y for ML models (4-digit version).
    Features per sample:
      - last N draws per position (d1-d4)
      - rolling frequency of each digit over window (per position)
      - sum of last draw, parity, high-low count
      - gap since last seen per digit
      - Markov-1 probabilities per position
    """
    if len(draws) < window + 5:
        return np.array([]), np.array([])

    data = [(int(d["d1"]), int(d["d2"]), int(d["d3"]), int(d["d4"])) for d in reversed(draws)]
    X, y = [], []
    freq_window = max(window, 20)

    for i in range(window, len(data) - 1):
        past = data[i - window:i]
        target = data[i]
        feats = []

        # Last 5 draws flattened (4 positions each)
        for draw in past[-5:]:
            feats.extend(draw)

        # Digit frequency over window (per position)
        for pos in range(4):
            cnt = Counter(d[pos] for d in data[max(0, i-freq_window):i])
            feats.extend([cnt.get(d, 0) / freq_window for d in DIGITS])

        # Sum, parity, high-low of last draw
        last = past[-1]
        feats.append(sum(last))
        feats.append(sum(1 for x in last if x % 2 == 0))
        feats.append(sum(1 for x in last if x >= 5))

        # Gap per digit across all positions
        all_digits_flat = [d for draw in data[max(0, i-50):i] for d in draw]
        for dig in DIGITS:
            try:
                gap = len(all_digits_flat) - 1 - next(
                    j for j, v in enumerate(reversed(all_digits_flat)) if v == dig
                )
            except StopIteration:
                gap = 99
            feats.append(gap)

        # Markov-1 transition proba per position
        for pos in range(4):
            last_dig = past[-1][pos]
            trans = Counter(
                data[j][pos]
                for j in range(max(0, i-50), i - 1)
                if data[j][pos] == last_dig
            )
            total = sum(trans.values()) or 1
            feats.extend([trans.get(d, 0) / total for d in DIGITS])

        X.append(feats)
        y.append(target)

    return np.array(X, dtype=np.float32), np.array(y)


# ─── Markov Chains (orders 1, 2, 3) ───────────────────────────────────────

def markov_predict4(draws: list[dict], position: str, order: int = 1) -> dict[int, float]:
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
        return markov_predict4(draws, position, max(1, order - 1)) if order > 1 else {d: 0.1 for d in DIGITS}

    total = sum(counts.values())
    return {d: (counts.get(d, 0) + 1) / (total + 10) for d in DIGITS}


def markov_matrix4(draws: list[dict], position: str) -> dict:
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

def fourier_cycles4(draws: list[dict], position: str) -> dict:
    """Detect repeating cycles in digit sequence using FFT (Pick 4 version)."""
    seq = np.array([int(d[position]) for d in reversed(draws)], dtype=float)
    if len(seq) < 20:
        return {"cycle_length": None, "predicted_digit": None}

    seq_norm = seq - seq.mean()
    spectrum = np.abs(_ensure_fft()(seq_norm))
    freqs = np.fft.fftfreq(len(seq_norm))

    pos_freqs = spectrum[1:len(spectrum)//2]
    dominant_idx = np.argmax(pos_freqs) + 1
    dominant_period = int(round(1 / abs(freqs[dominant_idx]))) if freqs[dominant_idx] != 0 else None

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

def monte_carlo4(draws: list[dict], n_simulations: int = 50000) -> list[dict]:
    """
    Simulate N future draws using empirical per-position distributions.
    Vectorized with numpy for 4 positions.
    """
    if not draws:
        return []

    dists = {}
    for pos in POSITIONS:
        cnt = Counter(int(d[pos]) for d in draws)
        total = sum(cnt.values())
        dists[pos] = np.array([cnt.get(d, 0) / total for d in DIGITS])

    rng = np.random.default_rng(42)
    samples = {pos: rng.choice(DIGITS, size=n_simulations, p=dists[pos]) for pos in POSITIONS}
    results = Counter(zip(
        samples["d1"].tolist(), samples["d2"].tolist(),
        samples["d3"].tolist(), samples["d4"].tolist()
    ))

    top = results.most_common(20)
    total = sum(results.values())
    return [
        {
            "combo": f"{c[0]}-{c[1]}-{c[2]}-{c[3]}",
            "digits": list(c),
            "mc_probability": round(count / total * 100, 3),
        }
        for c, count in top
    ]


# ─── ML Models (Random Forest + GBM + XGBoost) ────────────────────────────

class MLPredictor4:
    def __init__(self):
        RF, GBM, XGB = _ensure_sklearn_models()
        # 4 models (one per position), 3 algorithm families
        self.models = {
            "rf":  [RF(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1) for _ in range(4)],
            "gbm": [GBM(n_estimators=80, max_depth=4, learning_rate=0.05, random_state=42) for _ in range(4)],
            "xgb": [XGB(n_estimators=80, max_depth=5, learning_rate=0.05, verbosity=0, random_state=42, n_jobs=-1) for _ in range(4)],
        }
        self.trained = False

    def train(self, X: np.ndarray, y: np.ndarray):
        if len(X) < 30:
            return False
        for name, model_list in self.models.items():
            for pos in range(4):
                model_list[pos].fit(X, y[:, pos])
        self.trained = True
        return True

    def predict_proba_position(self, X_last: np.ndarray, position: int) -> dict[int, float]:
        if not self.trained:
            return {d: 0.1 for d in DIGITS}

        probas = []
        weights = {"rf": 0.35, "gbm": 0.30, "xgb": 0.35}
        for name, model_list in self.models.items():
            model = model_list[position]
            classes = list(model.classes_)
            proba = model.predict_proba(X_last)[0]
            prob_dict = {cls: p for cls, p in zip(classes, proba)}
            probas.append({d: prob_dict.get(d, 0.0) * weights[name] for d in DIGITS})

        ensemble = {d: sum(p[d] for p in probas) for d in DIGITS}
        total = sum(ensemble.values()) or 1
        return {d: v / total for d, v in ensemble.items()}

    def predict_top(self, X_last: np.ndarray, top_n: int = 15) -> list[dict]:
        """Generate top N combos from ensemble probabilities across 4 positions."""
        proba = [self.predict_proba_position(X_last, pos) for pos in range(4)]

        # Score top candidates: take top-5 per position to reduce search space
        # from 10^4=10000 to 5^4=625 — fast enough while keeping quality
        top5 = [sorted(p.items(), key=lambda x: x[1], reverse=True)[:5] for p in proba]

        scores = {}
        for d1, p1 in top5[0]:
            for d2, p2 in top5[1]:
                for d3, p3 in top5[2]:
                    for d4, p4 in top5[3]:
                        scores[(d1, d2, d3, d4)] = p1 * p2 * p3 * p4

        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        max_score = top[0][1] if top else 1
        return [
            {
                "combo": f"{c[0]}-{c[1]}-{c[2]}-{c[3]}",
                "digits": list(c),
                "ml_score": round(s * 10000, 4),
                "ml_probability": round(s / max_score * 100, 2),
            }
            for c, s in top
        ]


# ─── Advanced Statistics ───────────────────────────────────────────────────

def sum_analysis4(draws: list[dict]) -> dict:
    """Distribution of digit sums (0-36 for Pick 4)."""
    sums = [int(d["d1"]) + int(d["d2"]) + int(d["d3"]) + int(d["d4"]) for d in draws]
    cnt = Counter(sums)
    total = len(sums) or 1
    all_sums = list(range(37))
    return {
        "distribution": {str(s): {"count": cnt.get(s, 0), "pct": round(cnt.get(s, 0)/total*100, 2)} for s in all_sums},
        "last_sum": sums[0] if sums else None,
        "most_common_sum": cnt.most_common(1)[0][0] if cnt else None,
    }


def parity_analysis4(draws: list[dict]) -> dict:
    """Odd/Even pattern (EEEE, OOOO, OEOE, etc.) for 4 digits."""
    patterns = []
    for d in draws:
        p = "".join("E" if int(d[k]) % 2 == 0 else "O" for k in POSITIONS)
        patterns.append(p)
    cnt = Counter(patterns)
    total = len(patterns) or 1
    return {p: {"count": c, "pct": round(c/total*100, 2)} for p, c in cnt.most_common(10)}


def repeat_analysis4(draws: list[dict]) -> dict:
    """Classify draws by repeated-digit pattern for Pick 4."""
    counts = Counter()
    last_seen = {}
    for i, d in enumerate(draws):
        nums = [d[p] for p in POSITIONS]
        unique = len(set(nums))
        if unique == 4:
            label = "all_diff"
        elif unique == 3:
            label = "one_pair"
        elif unique == 2:
            c = Counter(nums)
            label = "triplet" if max(c.values()) == 3 else "two_pairs"
        else:
            label = "quadruplet"
        counts[label] += 1
        if label not in last_seen:
            last_seen[label] = i

    total = len(draws) or 1
    return {
        label: {
            "count": counts.get(label, 0),
            "pct": round(counts.get(label, 0) / total * 100, 2),
            "last_seen_draws_ago": last_seen.get(label),
        }
        for label in ["all_diff", "one_pair", "two_pairs", "triplet", "quadruplet"]
    }


def digit_gap_analysis4(draws: list[dict]) -> dict:
    """Per-digit gap stats for Pick 4."""
    digit_appearances = defaultdict(list)
    for i, d in enumerate(draws):
        for pos in POSITIONS:
            digit_appearances[int(d[pos])].append(i)

    result = {}
    for dig in DIGITS:
        appearances = digit_appearances[dig]
        if not appearances:
            result[str(dig)] = {"current_gap": len(draws), "avg_gap": None, "overdue": True, "due_prob": 0.99}
            continue
        gaps = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
        avg_gap = np.mean(gaps) if gaps else None
        current_gap = appearances[0]
        overdue = current_gap > (avg_gap or 0)
        due_prob = min(0.99, current_gap / (avg_gap or max(current_gap, 1)))
        result[str(dig)] = {
            "current_gap": current_gap,
            "avg_gap": round(avg_gap, 1) if avg_gap else None,
            "overdue": overdue,
            "due_prob": round(due_prob, 3),
        }
    return result


def hot_cold_stats4(draws: list[dict], window: int = 30) -> dict:
    """Hot/cold digit stats per position for Pick 4."""
    recent = draws[:window]
    result = {}
    for pos in POSITIONS:
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


# ─── Ensemble Consensus ────────────────────────────────────────────────────

def ensemble_consensus4(
    markov1: list[dict],
    markov2: list[dict],
    markov3: list[dict],
    ml_preds: list[dict],
    mc_preds: list[dict],
    fourier_hints: dict,
    draws: list[dict],
    hot_cold: dict = None,
    top_n: int = 10,
    lstm_preds: list[dict] = None,
) -> list[dict]:
    """
    Combine all models into a final weighted consensus score for Pick 4.
    Weights: ML=28%, LSTM=10%, Markov(1+2+3)=30%, MonteCarlo=20%, Fourier=7%, Gap=5%
    """
    gaps = digit_gap_analysis4(draws)
    combo_scores = defaultdict(float)
    combo_components = defaultdict(lambda: {
        "ml": 0.0, "lstm": 0.0, "markov1": 0.0, "markov2": 0.0, "markov3": 0.0,
        "monte_carlo": 0.0, "fourier": 0.0, "gap": 0.0,
    })

    def idx_score(pred_list: list[dict], combo: str, weight: float, component: str):
        for i, p in enumerate(pred_list):
            if p.get("combo") == combo:
                rank_bonus = (len(pred_list) - i) / len(pred_list)
                contrib = weight * rank_bonus
                combo_scores[combo] += contrib
                combo_components[combo][component] += contrib
                break

    lstm_preds = lstm_preds or []
    all_combos = set()
    for p in markov1 + markov2 + markov3 + ml_preds + mc_preds + lstm_preds:
        all_combos.add(p["combo"])

    # Fourier hint combo
    f_digits = {}
    for pos in POSITIONS:
        pred = fourier_hints.get(pos, {}).get("predicted_digit")
        if pred is not None:
            f_digits[pos] = pred

    if len(f_digits) == 4:
        fc = f"{f_digits['d1']}-{f_digits['d2']}-{f_digits['d3']}-{f_digits['d4']}"
        all_combos.add(fc)

    for combo in all_combos:
        idx_score(ml_preds,   combo, 0.28, "ml")
        idx_score(lstm_preds, combo, 0.10, "lstm")
        idx_score(markov1,    combo, 0.12, "markov1")
        idx_score(markov2, combo, 0.10, "markov2")
        idx_score(markov3, combo, 0.08, "markov3")
        idx_score(mc_preds, combo, 0.20, "monte_carlo")

        # Fourier bonus
        parts = combo.split("-")
        if len(parts) == 4 and len(f_digits) == 4:
            matches = sum(1 for pos, key in zip(POSITIONS, range(4)) if f_digits.get(pos) == int(parts[key]))
            fourier_contrib = 0.07 * (matches / 4)
            combo_scores[combo] += fourier_contrib
            combo_components[combo]["fourier"] += fourier_contrib

        # Gap/overdue bonus
        gap_contrib = sum(0.05 * gaps.get(part, {}).get("due_prob", 0) / 4 for part in parts)
        combo_scores[combo] += gap_contrib
        combo_components[combo]["gap"] += gap_contrib

    top = sorted(combo_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    max_score = top[0][1] if top else 1

    result = [
        {
            "combo": combo,
            "digits": [int(x) for x in combo.split("-")],
            "consensus_score": round(score, 4),
            "confidence_pct": round(score / max_score * 100, 1),
            "confidence_label": _conf_label4(score / max_score),
            "breakdown": _consensus_breakdown4(combo, combo_components[combo], gaps, hot_cold),
        }
        for combo, score in top
    ]

    # Attach Pick 4 bet recommendation
    for item in result:
        digits = [str(d) for d in item["digits"]]
        item["bet"] = bet_recommendation4(digits, item.get("confidence_label", ""))

    return result


def _consensus_breakdown4(combo: str, components: dict, gaps: dict, hot_cold: dict = None) -> dict:
    parts = combo.split("-")
    digits_info = []
    for part, pos in zip(parts, POSITIONS):
        g = gaps.get(part, {})
        hc = (hot_cold or {}).get(pos, {}).get(part, {})
        digits_info.append({
            "position": pos,
            "digit": int(part),
            "current_gap": g.get("current_gap"),
            "avg_gap": g.get("avg_gap"),
            "overdue": g.get("overdue", False),
            "hot_cold": hc.get("status", "NEUTRAL"),
            "freq_pct": hc.get("pct", 0),
        })

    total = sum(components.values()) or 1
    return {
        "digits": digits_info,
        "model_contributions": {
            "ml_pct": round(components["ml"] / total * 100, 1),
            "lstm_pct": round(components["lstm"] / total * 100, 1),
            "markov_pct": round((components["markov1"] + components["markov2"] + components["markov3"]) / total * 100, 1),
            "monte_carlo_pct": round(components["monte_carlo"] / total * 100, 1),
            "fourier_pct": round(components["fourier"] / total * 100, 1),
            "gap_pct": round(components["gap"] / total * 100, 1),
        },
    }


def _conf_label4(ratio: float) -> str:
    if ratio >= 0.95: return "Tendance très forte ★★★★★"
    if ratio >= 0.85: return "Tendance forte ★★★★"
    if ratio >= 0.70: return "Tendance moyenne ★★★"
    if ratio >= 0.55: return "Tendance légère ★★"
    return "Tendance faible ★"


# ─── Top-level runner ──────────────────────────────────────────────────────

def run_all_models4(draws: list[dict]) -> dict:
    """Run every model for Pick 4 and return combined results."""
    if not draws:
        return {"error": "Pas de données Pick 4. Lancez le scraper d'abord."}

    # Markov chains (orders 1, 2, 3)
    def markov_top4(order: int, n: int = 15) -> list[dict]:
        proba = [markov_predict4(draws, pos, order) for pos in POSITIONS]
        # Top-5 per position → 5^4 = 625 candidates (fast, covers top combos)
        top5 = [sorted(p.items(), key=lambda x: x[1], reverse=True)[:5] for p in proba]
        scores = {}
        for d1, p1 in top5[0]:
            for d2, p2 in top5[1]:
                for d3, p3 in top5[2]:
                    for d4, p4 in top5[3]:
                        scores[(d1, d2, d3, d4)] = p1 * p2 * p3 * p4
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        return [{"combo": f"{c[0]}-{c[1]}-{c[2]}-{c[3]}", "digits": list(c), "score": round(s, 8)} for c, s in top]

    m1 = markov_top4(1)
    m2 = markov_top4(2)
    m3 = markov_top4(3)

    # ML models
    X, y = build_features4(draws, window=10)
    predictor = MLPredictor4()
    ml_preds = []
    if len(X) >= 30:
        try:
            predictor.train(X, y)
            X_last = X[-1:].reshape(1, -1)
            ml_preds = predictor.predict_top(X_last, top_n=15)
        except Exception:
            pass

    # Monte Carlo
    mc_preds = monte_carlo4(draws, n_simulations=50000)

    # Fourier
    fourier = {pos: fourier_cycles4(draws, pos) for pos in POSITIONS}

    # LSTM sequential engine
    lstm_preds = []
    try:
        import lstm_engine
        lstm_preds = lstm_engine.train_and_predict(draws, positions=POSITIONS, top_n=15)
    except Exception as _le:
        print(f"  [lstm4] skipped: {_le}")

    # Hot/cold
    hc30 = hot_cold_stats4(draws, 30)

    # Ensemble consensus
    consensus = ensemble_consensus4(m1, m2, m3, ml_preds, mc_preds, fourier, draws,
                                    hot_cold=hc30, lstm_preds=lstm_preds)

    return {
        "markov_order1_top": m1[:10],
        "markov_order2_top": m2[:10],
        "markov_order3_top": m3[:10],
        "markov_matrix_d1": markov_matrix4(draws, "d1"),
        "ml_predictions": ml_preds[:10],
        "ml_trained": predictor.trained,
        "monte_carlo_top": mc_preds[:10],
        "fourier": fourier,
        "consensus": consensus,
        "sum_analysis": sum_analysis4(draws),
        "parity": parity_analysis4(draws),
        "repeat_patterns": repeat_analysis4(draws),
        "hot_cold_30": hc30,
        "gap_analysis": digit_gap_analysis4(draws),
    }
