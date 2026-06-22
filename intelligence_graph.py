"""
ZYNORIQ INTELLIGENCE GRAPH™ — Knowledge Graph Engine v1.0
Connects all platform entities: states, games, models, draws, predictions, users.
Read-only layer — never modifies existing engines.
"""
import os, json, time
from datetime import datetime, date, timedelta
from collections import Counter, defaultdict


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH NODE TYPES
# ═══════════════════════════════════════════════════════════════════════════
# Nodes: State, Game, Model, Digit, Draw, Prediction, User
# Edges: has_game, uses_model, drew_digit, predicted, analyzed_by, favorite_of

def build_state_graph(state_code, draws, report=None):
    """Build a knowledge graph for a state from real data."""
    graph = {
        "state": state_code,
        "nodes": [],
        "edges": [],
        "insights": [],
        "generated_at": datetime.utcnow().isoformat(),
    }

    if not draws:
        return graph

    # State node
    graph["nodes"].append({"id": f"state_{state_code}", "type": "state", "label": state_code})

    # Digit frequency analysis
    digit_freq = defaultdict(lambda: {"total": 0, "p1": 0, "p2": 0, "p3": 0})
    tod_counts = Counter()
    recent_draws = draws[:30]

    for d in recent_draws:
        for pos in ["d1", "d2", "d3"]:
            digit = str(d.get(pos, ""))
            if digit:
                digit_freq[digit]["total"] += 1
                digit_freq[digit][pos] += 1
        tod_counts[d.get("tod", "unknown")] += 1

    # Digit nodes
    for digit, freq in sorted(digit_freq.items(), key=lambda x: x[1]["total"], reverse=True):
        pct = round(freq["total"] / (len(recent_draws) * 3) * 100, 1) if recent_draws else 0
        status = "hot" if pct > 12 else "cold" if pct < 8 else "neutral"
        graph["nodes"].append({
            "id": f"digit_{digit}",
            "type": "digit",
            "label": digit,
            "frequency_pct": pct,
            "status": status,
            "positions": {"p1": freq["p1"], "p2": freq["p2"], "p3": freq["p3"]},
        })
        graph["edges"].append({
            "from": f"state_{state_code}",
            "to": f"digit_{digit}",
            "type": "draws_digit",
            "weight": pct,
        })

    # TOD nodes
    for tod, count in tod_counts.items():
        graph["nodes"].append({"id": f"tod_{tod}", "type": "tod", "label": tod, "draws": count})
        graph["edges"].append({"from": f"state_{state_code}", "to": f"tod_{tod}", "type": "has_tod"})

    # Model nodes (always the same 7)
    models = ["XGBoost", "Random Forest", "Gradient Boosting", "Markov", "Monte Carlo", "Fourier", "Gap Analysis"]
    for m in models:
        mid = f"model_{m.lower().replace(' ','_')}"
        graph["nodes"].append({"id": mid, "type": "model", "label": m})
        graph["edges"].append({"from": f"state_{state_code}", "to": mid, "type": "uses_model"})

    # Prediction nodes (from report cache)
    if report and isinstance(report, dict):
        top = report.get("top", [])[:5]
        for i, pred in enumerate(top):
            combo = pred.get("combo", "?")
            pct = pred.get("pct", 0)
            pid = f"pred_{state_code}_{i}"
            graph["nodes"].append({
                "id": pid, "type": "prediction", "label": combo,
                "confidence": round(pct, 1), "rank": i + 1,
            })
            graph["edges"].append({"from": f"state_{state_code}", "to": pid, "type": "predicted", "rank": i + 1})

    # ── Generate insights ──
    hot_digits = [n for n in graph["nodes"] if n.get("type") == "digit" and n.get("status") == "hot"]
    cold_digits = [n for n in graph["nodes"] if n.get("type") == "digit" and n.get("status") == "cold"]

    if hot_digits:
        graph["insights"].append({
            "type": "hot_digits",
            "text": f"Chiffres chauds (>12%): {', '.join(d['label'] for d in hot_digits)}",
            "severity": "info",
        })
    if cold_digits:
        graph["insights"].append({
            "type": "cold_digits",
            "text": f"Chiffres froids (<8%): {', '.join(d['label'] for d in cold_digits)}",
            "severity": "warning",
        })

    # Position dominance
    for digit, freq in digit_freq.items():
        total = freq["total"]
        if total >= 3:
            for pos in ["p1", "p2", "p3"]:
                pos_pct = freq[pos] / total * 100 if total else 0
                if pos_pct > 60:
                    graph["insights"].append({
                        "type": "position_dominance",
                        "text": f"Digit {digit} appears {round(pos_pct)}% in {pos.upper()} — strong position bias",
                        "severity": "insight",
                    })

    return graph


def build_cross_state_graph(states_data):
    """Build a graph comparing multiple states."""
    graph = {
        "type": "cross_state",
        "states": [],
        "common_hot": [],
        "common_cold": [],
        "insights": [],
        "generated_at": datetime.utcnow().isoformat(),
    }

    all_hot = defaultdict(list)
    all_cold = defaultdict(list)

    for code, data in (states_data or {}).items():
        draws = data.get("draws", [])
        if not draws:
            continue

        freq = Counter()
        for d in draws[:30]:
            for pos in ["d1", "d2", "d3"]:
                v = str(d.get(pos, ""))
                if v:
                    freq[v] += 1

        total = sum(freq.values()) or 1
        for digit, count in freq.items():
            pct = count / total * 100
            if pct > 12:
                all_hot[digit].append(code)
            elif pct < 8:
                all_cold[digit].append(code)

        graph["states"].append({"code": code, "draws_count": len(draws)})

    # Digits hot in multiple states
    for digit, states in all_hot.items():
        if len(states) >= 3:
            graph["common_hot"].append({"digit": digit, "states": states, "count": len(states)})
            graph["insights"].append({
                "type": "cross_state_hot",
                "text": f"Digit {digit} is HOT in {len(states)} states: {', '.join(states[:5])}",
                "severity": "insight",
            })

    for digit, states in all_cold.items():
        if len(states) >= 3:
            graph["common_cold"].append({"digit": digit, "states": states, "count": len(states)})

    return graph


def get_entity_connections(entity_type, entity_id, draws=None, report=None):
    """Get all connections for a specific entity."""
    connections = []

    if entity_type == "digit":
        if draws:
            positions = {"p1": 0, "p2": 0, "p3": 0}
            last_seen = None
            gap = 0
            for i, d in enumerate(draws[:100]):
                for pos in ["d1", "d2", "d3"]:
                    if str(d.get(pos, "")) == entity_id:
                        positions[pos] += 1
                        if last_seen is None:
                            last_seen = i
            if last_seen is not None:
                gap = last_seen

            connections.append({
                "type": "positions",
                "data": positions,
                "gap": gap,
                "total_appearances": sum(positions.values()),
            })

    elif entity_type == "model":
        connections.append({
            "type": "description",
            "data": _MODEL_INFO.get(entity_id, {}),
        })

    return connections


_MODEL_INFO = {
    "xgboost": {"name": "XGBoost", "type": "Gradient Boosting", "strength": "Non-linear patterns", "speed": "Fast"},
    "random_forest": {"name": "Random Forest", "type": "Ensemble", "strength": "Robust, low overfitting", "speed": "Fast"},
    "gradient_boosting": {"name": "Gradient Boosting", "type": "Sequential Boosting", "strength": "Complex patterns", "speed": "Medium"},
    "markov": {"name": "Markov 1/2/3", "type": "Transition Chains", "strength": "Sequential dependencies", "speed": "Fast"},
    "monte_carlo": {"name": "Monte Carlo 50K", "type": "Simulation", "strength": "Probability estimation", "speed": "Slow"},
    "fourier": {"name": "Fourier Analysis", "type": "Cycle Detection", "strength": "Periodic patterns", "speed": "Fast"},
    "gap_analysis": {"name": "Gap Analysis", "type": "Statistical", "strength": "Overdue detection", "speed": "Fast"},
}
