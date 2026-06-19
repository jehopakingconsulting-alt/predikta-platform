"""
PREDIKTA — Live Track Record (prospectif)

Flux :
  1. PRÉ-TIRAGE  (5-10 min avant)  → save_prediction()  sauvegarde le Top 10 ML
  2. POST-TIRAGE (résultat connu)  → record_result()    compare et logue le hit/miss
  3. N'importe quand               → get_stats()        retourne les stats cumulées

Stockage : data/live_predictions.json  (prédictions en attente)
           data/live_track_record.json (résultats vérifiés, cumulatif)

Différence avec backtest :
  • Backtest   = "qu'aurait-on prédit si on avait rejoué le passé ?"
  • Live TR    = "qu'avons-NOUS prédit AVANT ce tirage, et avions-nous raison ?"
"""

import json
import os
import threading
from datetime import datetime, timezone, timedelta

_DIR  = os.path.join(os.path.dirname(__file__), "data")
_PRED = os.path.join(_DIR, "live_predictions.json")   # prédictions en attente
_LOG  = os.path.join(_DIR, "live_track_record.json")  # résultats vérifiés

_lock = threading.Lock()

# ── I/O helpers ───────────────────────────────────────────────────────────

def _read(path: str) -> dict | list:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {} if path.endswith("predictions.json") else []


def _write(path: str, data):
    os.makedirs(_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ── 1. Sauvegarder les prédictions avant le tirage ───────────────────────

def save_prediction(state: str, tod: str, report: dict, saved_at: str | None = None):
    """
    Sauvegarde le Top 10 Consensus + ML du rapport (généré avant le tirage).

    state    : ex "NY"
    tod      : ex "Midday"
    report   : data complet de run_all_models() — on extrait consensus + ml_predictions
    saved_at : ISO UTC string (None = now)
    """
    state = state.upper()
    key   = f"{state}_{tod}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    consensus = []
    for c in (report.get("consensus") or [])[:10]:
        if isinstance(c, dict):
            consensus.append(c.get("combo") or "-".join(c.get("digits", [])))
        elif isinstance(c, (list, tuple)):
            consensus.append("-".join(str(x) for x in c))
        else:
            consensus.append(str(c))

    ml_preds = []
    for c in (report.get("ml_predictions") or [])[:10]:
        if isinstance(c, dict):
            ml_preds.append(c.get("combo") or "-".join(str(x) for x in c.get("digits", [])))
        else:
            ml_preds.append(str(c))

    mc_top = []
    for c in (report.get("monte_carlo_top") or [])[:5]:
        if isinstance(c, dict):
            mc_top.append(c.get("combo") or str(c))
        else:
            mc_top.append(str(c))

    entry = {
        "state":      state,
        "tod":        tod,
        "date":       datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "saved_at":   saved_at or datetime.now(timezone.utc).isoformat(),
        "consensus":  consensus,
        "ml":         ml_preds,
        "monte_carlo": mc_top,
        "last_draw":  report.get("last_draw"),
        "total_draws": report.get("total_draws", 0),
        "verified":   False,
    }

    with _lock:
        preds = _read(_PRED)
        if not isinstance(preds, dict):
            preds = {}
        # On garde la dernière prédiction par key (écrase si régénérée)
        preds[key] = entry
        # Purge des prédictions de plus de 3 jours non vérifiées
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
        preds = {k: v for k, v in preds.items() if v.get("date", "") >= cutoff}
        _write(_PRED, preds)

    print(f"  [live-TR] prédiction sauvegardée: {key} — consensus={consensus[:3]}")
    return key


# ── 2. Vérifier après le tirage ──────────────────────────────────────────

def record_result(state: str, tod: str, actual_draw: dict, draw_date: str | None = None) -> dict | None:
    """
    Compare les prédictions sauvegardées avec le résultat réel.

    actual_draw : {"d1": "4", "d2": "8", "d3": "5", "date": "2026-06-19"}
    Retourne l'entrée de résultat logée (ou None si pas de prédiction trouvée).
    """
    state = state.upper()
    date  = draw_date or actual_draw.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key   = f"{state}_{tod}_{date}"

    with _lock:
        preds = _read(_PRED)
        if not isinstance(preds, dict):
            return None

        pred = preds.get(key)
        if not pred:
            # Chercher aussi par state+tod sans date exacte (draw le même jour)
            matches = [v for k, v in preds.items()
                       if v["state"] == state and v["tod"] == tod
                       and v["date"] == date and not v.get("verified")]
            if not matches:
                print(f"  [live-TR] aucune prédiction trouvée pour {key}")
                return None
            pred = matches[-1]

        # Résultat réel
        d1, d2, d3 = str(actual_draw["d1"]), str(actual_draw["d2"]), str(actual_draw["d3"])
        actual_str  = f"{d1}-{d2}-{d3}"
        actual_set  = tuple(sorted([d1, d2, d3]))

        def _check(combo_str: str) -> tuple[bool, bool]:
            parts = combo_str.replace(" ", "").split("-")
            if len(parts) != 3:
                return False, False
            straight = parts == [d1, d2, d3]
            box      = tuple(sorted(parts)) == actual_set
            return straight, box

        # Vérifier consensus
        consensus_rank = None   # rang du 1er hit straight (1-based)
        consensus_box_rank = None
        for i, combo in enumerate(pred.get("consensus", []), 1):
            s, b = _check(combo)
            if s and consensus_rank is None:
                consensus_rank = i
            if b and consensus_box_rank is None:
                consensus_box_rank = i

        # Vérifier ML
        ml_rank = None
        ml_box_rank = None
        for i, combo in enumerate(pred.get("ml", []), 1):
            s, b = _check(combo)
            if s and ml_rank is None:
                ml_rank = i
            if b and ml_box_rank is None:
                ml_box_rank = i

        result_entry = {
            "state":              state,
            "tod":                tod,
            "date":               date,
            "actual":             actual_str,
            "predicted_at":       pred.get("saved_at"),
            "verified_at":        datetime.now(timezone.utc).isoformat(),
            "consensus_top10":    pred.get("consensus", []),
            "ml_top10":           pred.get("ml", []),
            "monte_carlo_top5":   pred.get("monte_carlo", []),
            "consensus_straight_rank": consensus_rank,   # None = pas dans top 10
            "consensus_box_rank":      consensus_box_rank,
            "ml_straight_rank":        ml_rank,
            "ml_box_rank":             ml_box_rank,
            "hit_straight":            consensus_rank == 1,
            "hit_box":                 consensus_box_rank is not None,
            "total_draws_at_pred":     pred.get("total_draws", 0),
        }

        # Marquer comme vérifié dans les prédictions
        pred["verified"] = True
        _write(_PRED, preds)

        # Logger dans le track record cumulatif
        log = _read(_LOG)
        if not isinstance(log, list):
            log = []
        # Éviter les doublons
        log = [r for r in log if not (r["state"] == state and r["tod"] == tod and r["date"] == date)]
        log.insert(0, result_entry)
        # Garder 90 jours
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
        log = [r for r in log if r.get("date", "") >= cutoff]
        _write(_LOG, log)

    emoji = "✅" if result_entry["hit_straight"] else ("📦" if result_entry["hit_box"] else "❌")
    print(f"  [live-TR] {emoji} {state} {tod} {date}: prédit={pred.get('consensus',['?'])[0]} réel={actual_str} "
          f"straight_rank={consensus_rank} box_rank={consensus_box_rank}")
    return result_entry


# ── 3. Stats cumulées ────────────────────────────────────────────────────

def get_stats(state: str | None = None, days: int = 30) -> dict:
    """
    Retourne les statistiques du track record live sur les N derniers jours.
    state=None → tous les états confondus.
    """
    log = _read(_LOG)
    if not isinstance(log, list):
        return _empty_stats(state, days)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    entries = [r for r in log if r.get("date", "") >= cutoff]
    if state:
        entries = [r for r in entries if r["state"] == state.upper()]

    n = len(entries)
    if n == 0:
        return _empty_stats(state, days)

    straight = sum(1 for r in entries if r.get("hit_straight"))
    box      = sum(1 for r in entries if r.get("hit_box"))

    # Distribution des rangs (consensus)
    rank_dist = {}
    for r in entries:
        rk = r.get("consensus_straight_rank")
        if rk:
            rank_dist[rk] = rank_dist.get(rk, 0) + 1

    # Top 3 in Top 10 box
    in_top3_box  = sum(1 for r in entries if r.get("consensus_box_rank") and r["consensus_box_rank"] <= 3)
    in_top10_box = sum(1 for r in entries if r.get("consensus_box_rank"))

    # Par état
    by_state = {}
    for r in entries:
        st = r["state"]
        s  = by_state.setdefault(st, {"n": 0, "straight": 0, "box": 0, "recent": []})
        s["n"] += 1
        if r.get("hit_straight"):
            s["straight"] += 1
        if r.get("hit_box"):
            s["box"] += 1
        if len(s["recent"]) < 5:
            s["recent"].append({
                "date":   r["date"],
                "tod":    r["tod"],
                "actual": r["actual"],
                "pred":   r.get("consensus_top10", ["?"])[0] if r.get("consensus_top10") else "?",
                "hit_straight": r.get("hit_straight"),
                "hit_box":      r.get("hit_box"),
                "rank":         r.get("consensus_straight_rank"),
                "box_rank":     r.get("consensus_box_rank"),
            })

    return {
        "days":             days,
        "state_filter":     state,
        "n":                n,
        "straight_hits":    straight,
        "box_hits":         box,
        "in_top3_box":      in_top3_box,
        "in_top10_box":     in_top10_box,
        "straight_rate":    round(straight / n * 100, 1),
        "box_rate":         round(box / n * 100, 1),
        "top3_box_rate":    round(in_top3_box / n * 100, 1),
        "top10_box_rate":   round(in_top10_box / n * 100, 1),
        "rank_distribution": rank_dist,
        "by_state":          by_state,
        "recent":            entries[:20],
        "updated_at":        datetime.now(timezone.utc).isoformat(),
    }


def _empty_stats(state, days):
    return {
        "days": days, "state_filter": state, "n": 0,
        "straight_hits": 0, "box_hits": 0,
        "straight_rate": 0.0, "box_rate": 0.0,
        "top3_box_rate": 0.0, "top10_box_rate": 0.0,
        "rank_distribution": {}, "by_state": {}, "recent": [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_pending_predictions() -> list[dict]:
    """Retourne les prédictions sauvegardées non encore vérifiées."""
    preds = _read(_PRED)
    if not isinstance(preds, dict):
        return []
    return [v for v in preds.values() if not v.get("verified")]
