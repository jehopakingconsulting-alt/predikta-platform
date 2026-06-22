"""
ZYNORIQ STUDIO™ — Content Creation Engine v1.0
Generate shareable content from platform data: summaries, social posts, newsletters.
Read-only — uses existing data without modification.
"""
import os, json, time
from datetime import datetime
from zoneinfo import ZoneInfo

# ═══════════════════════════════════════════════════════════════════════════
# CONTENT TYPES
# ═══════════════════════════════════════════════════════════════════════════
CONTENT_TYPES = {
    "daily_summary": {
        "name": {"fr": "Resume du jour", "en": "Daily Summary", "es": "Resumen del dia", "pt": "Resumo do dia", "ht": "Rezime jounen an"},
        "icon": "📋",
    },
    "social_post": {
        "name": {"fr": "Post reseaux sociaux", "en": "Social Media Post", "es": "Post redes sociales", "pt": "Post redes sociais", "ht": "Pos rezo sosyal"},
        "icon": "📱",
    },
    "state_spotlight": {
        "name": {"fr": "Spotlight Etat", "en": "State Spotlight", "es": "Spotlight Estado", "pt": "Spotlight Estado", "ht": "Spotlight Eta"},
        "icon": "🔦",
    },
    "weekly_digest": {
        "name": {"fr": "Digest hebdomadaire", "en": "Weekly Digest", "es": "Resumen semanal", "pt": "Resumo semanal", "ht": "Rezime semenn lan"},
        "icon": "📰",
    },
    "prediction_card": {
        "name": {"fr": "Carte de prediction", "en": "Prediction Card", "es": "Tarjeta de prediccion", "pt": "Cartao de previsao", "ht": "Kat prediksyon"},
        "icon": "🎴",
    },
    "analysis_brief": {
        "name": {"fr": "Brief d'analyse", "en": "Analysis Brief", "es": "Resumen de analisis", "pt": "Resumo de analise", "ht": "Rezime analiz"},
        "icon": "📊",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE ENGINE
# ═══════════════════════════════════════════════════════════════════════════

_TEMPLATES = {
    "daily_summary": {
        "fr": """📊 **ZYNORIQ — Resume du {date}**

🎯 **Top predictions du jour:**
{predictions}

🔥 **Chiffres chauds:** {hot_digits}
❄️ **Chiffres froids:** {cold_digits}

📈 **Etats les plus actifs:** {active_states}

💡 *Les analyses ZYNORIQ sont statistiques et educatives. La loterie reste un jeu de hasard.*

🔗 zynoriq.com""",
        "en": """📊 **ZYNORIQ — Summary for {date}**

🎯 **Today's top predictions:**
{predictions}

🔥 **Hot digits:** {hot_digits}
❄️ **Cold digits:** {cold_digits}

📈 **Most active states:** {active_states}

💡 *ZYNORIQ analyses are statistical and educational. Lottery remains a game of chance.*

🔗 zynoriq.com""",
    },

    "social_post": {
        "fr": """🎯 ZYNORIQ Intelligence™

{state} {tod} — Top 3 Predictions:
1️⃣ {pred1} ({conf1}%)
2️⃣ {pred2} ({conf2}%)
3️⃣ {pred3} ({conf3}%)

7 modeles ML · {draws_analyzed} tirages analyses
Score de confiance: {confidence}%

⚠️ Analyse statistique educative uniquement.
Aucun gain garanti.

👉 zynoriq.com/analyze?state={state_code}
#ZYNORIQ #Pick3 #{state} #Lottery""",
        "en": """🎯 ZYNORIQ Intelligence™

{state} {tod} — Top 3 Predictions:
1️⃣ {pred1} ({conf1}%)
2️⃣ {pred2} ({conf2}%)
3️⃣ {pred3} ({conf3}%)

7 ML models · {draws_analyzed} draws analyzed
Confidence score: {confidence}%

⚠️ Statistical educational analysis only.
No guaranteed winnings.

👉 zynoriq.com/analyze?state={state_code}
#ZYNORIQ #Pick3 #{state} #Lottery""",
    },

    "state_spotlight": {
        "fr": """🔦 **ZYNORIQ Spotlight — {state_name}**

📊 **Statistiques cles:**
• Tirages analyses: {total_draws}
• Tirages/jour: {draws_per_day}
• Dernier tirage: {last_draw_date} {last_draw_numbers}

🔥 **Chiffres chauds:** {hot_digits}
❄️ **Chiffres froids:** {cold_digits}

🎯 **Prediction consensus:**
{top_prediction} — Confiance {confidence}%

📈 **Tendance:** {trend}

💡 *Analyse statistique educative — zynoriq.com*""",
        "en": """🔦 **ZYNORIQ Spotlight — {state_name}**

📊 **Key stats:**
• Draws analyzed: {total_draws}
• Draws/day: {draws_per_day}
• Last draw: {last_draw_date} {last_draw_numbers}

🔥 **Hot digits:** {hot_digits}
❄️ **Cold digits:** {cold_digits}

🎯 **Consensus prediction:**
{top_prediction} — Confidence {confidence}%

📈 **Trend:** {trend}

💡 *Statistical educational analysis — zynoriq.com*""",
    },

    "prediction_card": {
        "fr": """🎴 **ZYNORIQ Prediction Card**
━━━━━━━━━━━━━━━━━━━
🏛️ {state_name} · {tod}
📅 {date}
━━━━━━━━━━━━━━━━━━━

🥇 **#{rank} — {combo}**
Confiance: {confidence}%
Type: {play_type}

📊 Modeles: {models_agree}/7 en accord
🔥 Chiffres: {digit_status}
📈 Tendance: {trend_note}

━━━━━━━━━━━━━━━━━━━
⚠️ Statistique educative uniquement
🔗 zynoriq.com""",
        "en": """🎴 **ZYNORIQ Prediction Card**
━━━━━━━━━━━━━━━━━━━
🏛️ {state_name} · {tod}
📅 {date}
━━━━━━━━━━━━━━━━━━━

🥇 **#{rank} — {combo}**
Confidence: {confidence}%
Type: {play_type}

📊 Models: {models_agree}/7 agree
🔥 Digits: {digit_status}
📈 Trend: {trend_note}

━━━━━━━━━━━━━━━━━━━
⚠️ Statistical educational only
🔗 zynoriq.com""",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# CONTENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_content(content_type, lang, data, use_ai=False):
    """Generate content from template + optional AI enhancement."""
    if content_type not in CONTENT_TYPES:
        return {"error": f"Unknown content type: {content_type}"}

    template = (_TEMPLATES.get(content_type) or {}).get(lang)
    if not template:
        template = (_TEMPLATES.get(content_type) or {}).get("en", "")
    if not template:
        return {"error": "No template available for this content type"}

    # Fill template with data
    content = _fill_template(template, data)

    result = {
        "type": content_type,
        "lang": lang,
        "content": content,
        "generated_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
        "ai_enhanced": False,
    }

    # AI enhancement if requested
    if use_ai and os.environ.get("ANTHROPIC_API_KEY"):
        enhanced = _ai_enhance(content, content_type, lang)
        if enhanced:
            result["content"] = enhanced
            result["ai_enhanced"] = True

    return result


def _fill_template(template, data):
    """Fill template placeholders with data, handling missing values gracefully."""
    d = data or {}
    # Build prediction lines
    preds = d.get("predictions", [])
    pred_lines = ""
    for i, p in enumerate(preds[:5]):
        combo = p.get("combo", "?")
        conf = p.get("confidence", 0)
        pred_lines += f"  #{i+1} {combo} ({conf}%)\n"

    fills = {
        "date": d.get("date", datetime.now(ZoneInfo("America/New_York")).strftime("%d/%m/%Y")),
        "predictions": pred_lines.strip() or "Pas de predictions disponibles",
        "hot_digits": d.get("hot_digits", "—"),
        "cold_digits": d.get("cold_digits", "—"),
        "active_states": d.get("active_states", "NY, FL, GA, TX, CA"),
        "state": d.get("state", ""),
        "state_code": d.get("state_code", d.get("state", "")),
        "state_name": d.get("state_name", d.get("state", "")),
        "tod": d.get("tod", ""),
        "pred1": preds[0].get("combo", "?") if len(preds) > 0 else "?",
        "conf1": str(round(preds[0].get("confidence", 0))) if len(preds) > 0 else "?",
        "pred2": preds[1].get("combo", "?") if len(preds) > 1 else "?",
        "conf2": str(round(preds[1].get("confidence", 0))) if len(preds) > 1 else "?",
        "pred3": preds[2].get("combo", "?") if len(preds) > 2 else "?",
        "conf3": str(round(preds[2].get("confidence", 0))) if len(preds) > 2 else "?",
        "confidence": str(round(preds[0].get("confidence", 0))) if preds else "—",
        "draws_analyzed": str(d.get("total_draws", "?")),
        "total_draws": str(d.get("total_draws", "?")),
        "draws_per_day": str(d.get("draws_per_day", "2")),
        "last_draw_date": d.get("last_draw_date", "—"),
        "last_draw_numbers": d.get("last_draw_numbers", ""),
        "top_prediction": preds[0].get("combo", "?") if preds else "?",
        "trend": d.get("trend", "stable"),
        "combo": d.get("combo", preds[0].get("combo", "?") if preds else "?"),
        "rank": str(d.get("rank", 1)),
        "play_type": d.get("play_type", "Box 6-way"),
        "models_agree": str(d.get("models_agree", "5")),
        "digit_status": d.get("digit_status", "mixed"),
        "trend_note": d.get("trend_note", "stable"),
    }

    result = template
    for k, v in fills.items():
        result = result.replace("{" + k + "}", str(v))
    return result


def _ai_enhance(content, content_type, lang):
    """Use Claude to polish the content."""
    try:
        import httpx
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        prompts = {
            "fr": f"Ameliore ce contenu pour le rendre plus engageant et professionnel. Garde le format, les emojis et la structure. Max 300 mots. Reponds en francais:\n\n{content}",
            "en": f"Improve this content to make it more engaging and professional. Keep the format, emojis and structure. Max 300 words:\n\n{content}",
        }
        prompt = prompts.get(lang, prompts["en"])

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 500,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("content", [{}])[0].get("text", "")
    except Exception:
        pass
    return None


def get_content_types(lang="fr"):
    """Return available content types for the frontend."""
    return [
        {
            "id": cid,
            "name": ct["name"].get(lang, ct["name"].get("en", cid)),
            "icon": ct["icon"],
        }
        for cid, ct in CONTENT_TYPES.items()
    ]
