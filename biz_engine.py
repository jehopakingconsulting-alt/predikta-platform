"""
PREDIKTA BUSINESS AI — Project Analysis Engine
Generates a complete 12-section business intelligence report
from a structured project questionnaire.
"""

import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASES
# ═══════════════════════════════════════════════════════════════════════════

INDUSTRIES = {
    "tech":          {"label":"Technologie / SaaS",        "market":"$5.2T",  "growth":"8.0%",  "competition":"Élevée",       "trend":"↗ Forte croissance"},
    "health":        {"label":"Santé / Bien-être",          "market":"$4.5T",  "growth":"7.2%",  "competition":"Moyenne-haute","trend":"↗ Forte croissance"},
    "education":     {"label":"Éducation / Formation",      "market":"$6.0T",  "growth":"10.0%", "competition":"Moyenne",      "trend":"↗↗ Boom e-learning"},
    "food":          {"label":"Alimentation / Restauration","market":"$8.0T",  "growth":"3.5%",  "competition":"Très élevée",  "trend":"→ Stable"},
    "retail":        {"label":"Commerce / Vente au détail", "market":"$26T",   "growth":"5.0%",  "competition":"Très élevée",  "trend":"↗ Omnicanal"},
    "finance":       {"label":"Finance / Fintech",          "market":"$22T",   "growth":"6.0%",  "competition":"Élevée",       "trend":"↗ Disruption fintech"},
    "services":      {"label":"Services aux entreprises",   "market":"$10T",   "growth":"6.0%",  "competition":"Moyenne",      "trend":"↗ Outsourcing"},
    "fashion":       {"label":"Mode / Vêtements",           "market":"$1.7T",  "growth":"7.0%",  "competition":"Élevée",       "trend":"↗ Durable & digital"},
    "real_estate":   {"label":"Immobilier",                 "market":"$3.7T",  "growth":"4.0%",  "competition":"Moyenne",      "trend":"→ Cyclique"},
    "travel":        {"label":"Voyage / Tourisme",          "market":"$1.2T",  "growth":"12.0%", "competition":"Élevée",       "trend":"↗↗ Reprise post-COVID"},
    "entertainment": {"label":"Divertissement / Médias",    "market":"$2.3T",  "growth":"9.0%",  "competition":"Élevée",       "trend":"↗ Streaming & gaming"},
    "beauty":        {"label":"Beauté / Cosmétiques",       "market":"$560B",  "growth":"7.0%",  "competition":"Moyenne",      "trend":"↗ Influenceurs"},
    "fitness":       {"label":"Sport / Fitness",            "market":"$96B",   "growth":"9.0%",  "competition":"Moyenne",      "trend":"↗ Apps & coaching"},
    "agriculture":   {"label":"Agriculture / Agritech",     "market":"$3.3T",  "growth":"4.0%",  "competition":"Faible-moy.",  "trend":"↗ Agritech"},
    "construction":  {"label":"Construction / BTP",         "market":"$13T",   "growth":"5.0%",  "competition":"Moyenne",      "trend":"→ Infrastructure"},
    "logistics":     {"label":"Logistique / Transport",     "market":"$8.4T",  "growth":"7.0%",  "competition":"Moyenne-haute","trend":"↗ E-commerce"},
    "consulting":    {"label":"Conseil / Consulting",       "market":"$1.0T",  "growth":"8.5%",  "competition":"Moyenne",      "trend":"↗ Digital advisory"},
    "creative":      {"label":"Création / Design / Art",    "market":"$2.5T",  "growth":"6.0%",  "competition":"Faible",       "trend":"↗ Économie créative"},
    "social":        {"label":"Impact social / ONG",        "market":"$300B",  "growth":"5.0%",  "competition":"Faible",       "trend":"↗ ESG & impact"},
    "other":         {"label":"Autre / Mixte",              "market":"—",      "growth":"—",     "competition":"Variable",     "trend":"À analyser"},
}

PLATFORMS = {
    "facebook":    {
        "name":"Facebook / Meta Ads","icon":"📘",
        "reach":"3,0 milliards",
        "best_age":"25–55 ans","best_for":["B2C","local","e-commerce","events","food","services","retail","health"],
        "cpc":"$0.50–$2.00","monthly_min":200,
        "strengths":["Ciblage démographique ultra-précis","Lookalike audiences","Retargeting","Excellente pour awareness et conversions"],
        "weaknesses":["Coût en hausse","Reach organique faible","Jeunes migrent vers TikTok"],
        "best_countries":["USA","France","Brésil","Mexique","Inde","Philippines"],
        "score_b2c":90,"score_b2b":40,"score_young":30,"score_senior":90,"score_budget_low":60,"score_brand":85,
    },
    "instagram":   {
        "name":"Instagram / Reels","icon":"📸",
        "reach":"2,0 milliards",
        "best_age":"18–35 ans","best_for":["fashion","beauty","food","lifestyle","travel","fitness","creative","entertainment"],
        "cpc":"$0.70–$2.50","monthly_min":200,
        "strengths":["Visuel fort","Reels viral","Shopping intégré","Influenceurs"],
        "weaknesses":["Moins efficace B2B","Contenu visuel exigé"],
        "best_countries":["USA","Brésil","Inde","Turquie","France","Mexique"],
        "score_b2c":85,"score_b2b":25,"score_young":90,"score_senior":40,"score_budget_low":55,"score_brand":90,
    },
    "tiktok":      {
        "name":"TikTok Ads","icon":"🎵",
        "reach":"1,5 milliard",
        "best_age":"16–35 ans","best_for":["entertainment","fashion","beauty","food","education","fitness","creative","tech"],
        "cpc":"$0.20–$1.00","monthly_min":50,
        "strengths":["Reach viral organique","Coût faible","Jeune audience","Contenu authentique"],
        "weaknesses":["Public très jeune","Restrictions dans certains pays","ROI difficile à mesurer"],
        "best_countries":["USA","Indonésie","Brésil","Mexique","Vietnam","Thaïlande"],
        "score_b2c":80,"score_b2b":15,"score_young":98,"score_senior":10,"score_budget_low":90,"score_brand":80,
    },
    "google":      {
        "name":"Google Ads (Search/Display)","icon":"🔍",
        "reach":"8,5 milliards recherches/jour",
        "best_age":"Tous âges (intention d'achat)","best_for":["services","e-commerce","B2B","local","health","finance","consulting","logistics"],
        "cpc":"$1.00–$10.00","monthly_min":300,
        "strengths":["Intention d'achat forte","Ciblage par mots-clés","Réseau Display","Tracking précis"],
        "weaknesses":["Coût élevé","Expertise requise","Concurrence intense sur mots-clés"],
        "best_countries":["Mondial","USA","Europe","Australie"],
        "score_b2c":80,"score_b2b":90,"score_young":70,"score_senior":80,"score_budget_low":30,"score_brand":70,
    },
    "linkedin":    {
        "name":"LinkedIn Ads","icon":"💼",
        "reach":"930 millions de professionnels",
        "best_age":"25–55 ans professionnels","best_for":["B2B","SaaS","consulting","finance","tech","education","logistics","real_estate"],
        "cpc":"$5.00–$15.00","monthly_min":500,
        "strengths":["Audience professionnelle","Ciblage par titre/secteur","Génération de leads B2B","Crédibilité"],
        "weaknesses":["Très cher","Faible ROI B2C","Interface publicitaire complexe"],
        "best_countries":["USA","Canada","UK","France","Allemagne","Australie"],
        "score_b2c":20,"score_b2b":98,"score_young":50,"score_senior":70,"score_budget_low":10,"score_brand":85,
    },
    "youtube":     {
        "name":"YouTube Ads","icon":"▶️",
        "reach":"2,7 milliards",
        "best_age":"18–50 ans","best_for":["brand awareness","education","tech","entertainment","fitness","services","consulting"],
        "cpc":"$0.01–$0.05/vue","monthly_min":200,
        "strengths":["Vidéo = format le plus engageant","SEO Google","Awareness massive","Tutoriels"],
        "weaknesses":["Création vidéo requise","Skip après 5s","ROI lent"],
        "best_countries":["USA","Inde","Brésil","Mexique","Indonésie"],
        "score_b2c":75,"score_b2b":60,"score_young":80,"score_senior":65,"score_budget_low":60,"score_brand":90,
    },
    "pinterest":   {
        "name":"Pinterest Ads","icon":"📌",
        "reach":"465 millions",
        "best_age":"25–50 ans (75% femmes)","best_for":["fashion","beauty","food","home_decor","DIY","wedding","travel","creative"],
        "cpc":"$0.10–$1.50","monthly_min":100,
        "strengths":["Intention d'achat élevée","Durée de vie longue","Niche très précise"],
        "weaknesses":["Audience limitée","Majorité féminine","Moins adapté B2B"],
        "best_countries":["USA","UK","Canada","France","Australie"],
        "score_b2c":70,"score_b2b":10,"score_young":60,"score_senior":50,"score_budget_low":75,"score_brand":70,
    },
    "twitter_x":   {
        "name":"X (Twitter) Ads","icon":"𝕏",
        "reach":"350 millions",
        "best_age":"18–45 ans","best_for":["tech","media","finance","entertainment","consulting","social","creative"],
        "cpc":"$0.50–$3.00","monthly_min":200,
        "strengths":["Conversations en temps réel","Thought leadership","Viral organique","Tech & fintech"],
        "weaknesses":["Portée réduite","Controverse plateforme","ROI incertain"],
        "best_countries":["USA","Japon","UK","Brésil","Inde"],
        "score_b2c":45,"score_b2b":65,"score_young":70,"score_senior":40,"score_budget_low":50,"score_brand":60,
    },
    "email":       {
        "name":"Email Marketing","icon":"📧",
        "reach":"ROI moyen 42:1",
        "best_age":"25–65 ans","best_for":["e-commerce","SaaS","consulting","finance","education","services","health","retail"],
        "cpc":"$0.01–$0.05/email","monthly_min":30,
        "strengths":["ROI le plus élevé de tous les canaux","Aucun algorithme","Audience captive","Automatisation"],
        "weaknesses":["Construction de liste longue","Délivrabilité","Spam"],
        "best_countries":["Mondial"],
        "score_b2c":85,"score_b2b":90,"score_young":65,"score_senior":80,"score_budget_low":95,"score_brand":80,
    },
    "seo":         {
        "name":"SEO / Content Marketing","icon":"🔎",
        "reach":"Trafic organique illimité",
        "best_age":"Tous âges","best_for":["services","e-commerce","SaaS","consulting","education","health","finance"],
        "cpc":"Investissement temps/rédaction","monthly_min":100,
        "strengths":["Trafic gratuit à long terme","Crédibilité","Evergreen","Effet composé"],
        "weaknesses":["Résultats à 3–12 mois","Expertise requise","Compétition forte"],
        "best_countries":["Mondial"],
        "score_b2c":80,"score_b2b":85,"score_young":70,"score_senior":75,"score_budget_low":70,"score_brand":75,
    },
    "influencer":  {
        "name":"Marketing d'influence","icon":"🌟",
        "reach":"Variable selon influenceur",
        "best_age":"16–35 ans","best_for":["fashion","beauty","food","fitness","gaming","travel","entertainment","creative"],
        "cpc":"$0.01–$0.20/vue","monthly_min":500,
        "strengths":["Authenticité","Niche précise","Trust élevé","Viralité"],
        "weaknesses":["ROI difficile à mesurer","Risque image","Coût nano/macro"],
        "best_countries":["USA","France","UK","Brésil","Inde"],
        "score_b2c":80,"score_b2b":20,"score_young":90,"score_senior":30,"score_budget_low":50,"score_brand":85,
    },
    "whatsapp":    {
        "name":"WhatsApp Business","icon":"💬",
        "reach":"2,0 milliards",
        "best_age":"18–55 ans","best_for":["local","services","retail","food","health","social"],
        "cpc":"Gratuit / faible coût","monthly_min":0,
        "strengths":["Taux d'ouverture >90%","Gratuit","Relation client directe","Marchés émergents"],
        "weaknesses":["Pas d'ads directes","Liste manuelle","RGPD complexe"],
        "best_countries":["Brésil","Inde","Mexique","Afrique","Europe du Sud","Haiti","Caraïbes"],
        "score_b2c":85,"score_b2b":50,"score_young":80,"score_senior":70,"score_budget_low":100,"score_brand":60,
    },
}

COUNTRIES_DATA = {
    "USA":          {"pop":"340M","gdp_pc":"$63K","internet":"93%","ecommerce":"$1.1T","language":["en"],"risk":"Faible","opportunity":"Très haute"},
    "Canada":       {"pop":"38M","gdp_pc":"$52K","internet":"92%","ecommerce":"$36B","language":["en","fr"],"risk":"Faible","opportunity":"Haute"},
    "France":       {"pop":"68M","gdp_pc":"$44K","internet":"88%","ecommerce":"$150B","language":["fr"],"risk":"Faible","opportunity":"Haute"},
    "Brésil":       {"pop":"215M","gdp_pc":"$8K","internet":"81%","ecommerce":"$41B","language":["pt"],"risk":"Moyenne","opportunity":"Très haute"},
    "Mexique":      {"pop":"130M","gdp_pc":"$10K","internet":"72%","ecommerce":"$26B","language":["es"],"risk":"Moyenne","opportunity":"Haute"},
    "Inde":         {"pop":"1.4B","gdp_pc":"$2.5K","internet":"62%","ecommerce":"$84B","language":["hi","en"],"risk":"Moyenne","opportunity":"Très haute"},
    "UK":           {"pop":"67M","gdp_pc":"$45K","internet":"96%","ecommerce":"$170B","language":["en"],"risk":"Faible","opportunity":"Haute"},
    "Allemagne":    {"pop":"84M","gdp_pc":"$50K","internet":"93%","ecommerce":"$141B","language":["de"],"risk":"Faible","opportunity":"Haute"},
    "Espagne":      {"pop":"47M","gdp_pc":"$30K","internet":"93%","ecommerce":"$59B","language":["es"],"risk":"Faible","opportunity":"Moyenne"},
    "Italie":       {"pop":"60M","gdp_pc":"$35K","internet":"88%","ecommerce":"$45B","language":["it"],"risk":"Faible","opportunity":"Moyenne"},
    "Australie":    {"pop":"26M","gdp_pc":"$55K","internet":"91%","ecommerce":"$35B","language":["en"],"risk":"Faible","opportunity":"Haute"},
    "Japon":        {"pop":"125M","gdp_pc":"$42K","internet":"93%","ecommerce":"$160B","language":["ja"],"risk":"Faible","opportunity":"Moyenne"},
    "Chine":        {"pop":"1.4B","gdp_pc":"$12K","internet":"73%","ecommerce":"$2.2T","language":["zh"],"risk":"Élevée","opportunity":"Variable"},
    "Nigeria":      {"pop":"220M","gdp_pc":"$2K","internet":"42%","ecommerce":"$12B","language":["en"],"risk":"Élevée","opportunity":"Émergente"},
    "Afrique du Sud":{"pop":"60M","gdp_pc":"$6K","internet":"68%","ecommerce":"$4B","language":["en","af"],"risk":"Moyenne","opportunity":"Émergente"},
    "Haïti":        {"pop":"11M","gdp_pc":"$1.5K","internet":"38%","ecommerce":"$0.2B","language":["ht","fr"],"risk":"Élevée","opportunity":"Émergente"},
    "Caraïbes":     {"pop":"45M","gdp_pc":"$7K","internet":"70%","ecommerce":"$2B","language":["en","fr","es","ht"],"risk":"Moyenne","opportunity":"Émergente"},
    "Colombie":     {"pop":"52M","gdp_pc":"$6K","internet":"72%","ecommerce":"$14B","language":["es"],"risk":"Moyenne","opportunity":"Haute"},
    "Argentine":    {"pop":"46M","gdp_pc":"$10K","internet":"83%","ecommerce":"$8B","language":["es"],"risk":"Élevée","opportunity":"Haute"},
    "Portugal":     {"pop":"10M","gdp_pc":"$24K","internet":"88%","ecommerce":"$5B","language":["pt"],"risk":"Faible","opportunity":"Moyenne"},
    "Sénégal":      {"pop":"17M","gdp_pc":"$1.6K","internet":"46%","ecommerce":"$0.5B","language":["fr","wolof"],"risk":"Moyenne","opportunity":"Émergente"},
    "Maroc":        {"pop":"37M","gdp_pc":"$3.5K","internet":"88%","ecommerce":"$2B","language":["fr","ar"],"risk":"Faible","opportunity":"Émergente"},
    "Côte d'Ivoire":{"pop":"27M","gdp_pc":"$2.3K","internet":"46%","ecommerce":"$0.4B","language":["fr"],"risk":"Moyenne","opportunity":"Émergente"},
    "Suisse":       {"pop":"9M","gdp_pc":"$90K","internet":"96%","ecommerce":"$12B","language":["fr","de","it"],"risk":"Faible","opportunity":"Haute"},
    "Belgique":     {"pop":"11M","gdp_pc":"$47K","internet":"93%","ecommerce":"$12B","language":["fr","nl"],"risk":"Faible","opportunity":"Haute"},
}

# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def analyze_project(data: dict) -> dict:
    """
    Main analysis function.
    Input: dict with all wizard answers
    Output: complete 12-section report dict
    """
    industry    = data.get("industry", "other")
    model       = data.get("model", "B2C")        # B2C | B2B | Both
    stage       = data.get("stage", "idea")        # idea | mvp | early | growth
    prod_type   = data.get("prod_type", "service") # product | digital | service | saas | app | consulting
    budget_tier = data.get("budget_tier", "low")   # low(<1K) | mid(1K-5K) | high(5K-20K) | premium(20K+)
    target_ages = data.get("target_ages", ["25-35"])
    geo_scope   = data.get("geo_scope", "national") # local | national | international
    geo_countries = data.get("geo_countries", ["USA"])
    timeline    = data.get("timeline", "6-12")     # 1-3 | 3-6 | 6-12 | 12+
    goal        = data.get("goal", "sales")        # awareness | leads | sales | downloads | community
    usp         = data.get("usp", "")
    competitors = data.get("competitors", [])
    project_name= data.get("project_name", "Votre Projet")
    description = data.get("description", "")
    price_range = data.get("price_range", "medium")# free | low | medium | high | premium
    languages   = data.get("languages", ["fr"])

    ind_data = INDUSTRIES.get(industry, INDUSTRIES["other"])
    is_b2b   = model in ("B2B", "Both")
    is_b2c   = model in ("B2C", "Both")
    is_young = any(a in target_ages for a in ["13-18","18-25","18-35"])
    is_senior= any(a in target_ages for a in ["45-55","55+"])
    has_budget = budget_tier in ("high","premium")
    is_local = geo_scope == "local"
    is_intl  = geo_scope == "international"

    # ── 1. VIABILITY SCORE ────────────────────────────────────────────────
    viability = _viability_score(data, ind_data, is_b2b, is_b2c, has_budget)

    # ── 2. MARKET OPPORTUNITY ─────────────────────────────────────────────
    market = _market_analysis(data, ind_data, geo_scope, geo_countries)

    # ── 3. TARGET AUDIENCE ───────────────────────────────────────────────
    audience = _audience_analysis(data, is_b2b, is_b2c, target_ages, geo_countries)

    # ── 4. COMPETITIVE LANDSCAPE ─────────────────────────────────────────
    competition = _competitive_analysis(data, ind_data, competitors, usp)

    # ── 5. PRODUCT/SERVICE RECOMMENDATIONS ───────────────────────────────
    product_recs = _product_recommendations(data, ind_data, prod_type, price_range, stage)

    # ── 6. LAUNCH STRATEGY ───────────────────────────────────────────────
    launch = _launch_strategy(data, stage, timeline, goal, budget_tier)

    # ── 7. MARKETING CHANNELS ────────────────────────────────────────────
    channels = _recommend_channels(data, industry, model, target_ages, budget_tier, is_b2b, is_b2c, is_young, is_senior)

    # ── 8. PLATFORM PRIORITIES ───────────────────────────────────────────
    platforms = _platform_priorities(channels, budget_tier)

    # ── 9. GEOGRAPHIC EXPANSION ──────────────────────────────────────────
    geo = _geo_analysis(data, geo_scope, geo_countries, languages, industry)

    # ── 10. BUDGET ALLOCATION ────────────────────────────────────────────
    budget = _budget_allocation(data, channels, budget_tier, goal)

    # ── 11. RISK ASSESSMENT ──────────────────────────────────────────────
    risks = _risk_assessment(data, ind_data, stage, budget_tier, competitors)

    # ── 12. ACTION PLAN 30-60-90 ─────────────────────────────────────────
    action_plan = _action_plan(data, stage, channels, goal, geo_scope, timeline)

    return {
        "project_name":  project_name,
        "industry_label":ind_data["label"],
        "model":         model,
        "generated_at":  datetime.now().strftime("%d %b %Y à %H:%M"),
        "viability":     viability,
        "market":        market,
        "audience":      audience,
        "competition":   competition,
        "product_recs":  product_recs,
        "launch":        launch,
        "channels":      channels,
        "platforms":     platforms,
        "geo":           geo,
        "budget":        budget,
        "risks":         risks,
        "action_plan":   action_plan,
    }


def _viability_score(data, ind, is_b2b, is_b2c, has_budget):
    score = 50
    bonuses = []
    warnings = []

    if data.get("usp","").strip(): score += 10; bonuses.append("USP clairement définie (+10)")
    if len(data.get("competitors",[])) > 0: score += 5; bonuses.append("Marché existant validé (+5)")
    if data.get("stage") in ("mvp","early","growth"): score += 8; bonuses.append("Avancement du projet (+8)")
    if has_budget: score += 10; bonuses.append("Budget de lancement solide (+10)")
    if data.get("timeline","") in ("6-12","12+"): score += 5; bonuses.append("Timeline réaliste (+5)")

    ind_growth = float(ind.get("growth","5.0%").replace("%","").replace("—","5.0") or 5.0)
    if ind_growth >= 8: score += 8; bonuses.append(f"Secteur en forte croissance {ind['growth']} (+8)")
    elif ind_growth >= 5: score += 4; bonuses.append(f"Secteur en croissance {ind['growth']} (+4)")

    comp = ind.get("competition","")
    if "Faible" in comp: score += 8; bonuses.append("Faible concurrence (+8)")
    elif "Très élevée" in comp: score -= 8; warnings.append("Concurrence très intense (-8)")

    if data.get("budget_tier","low") == "low" and not data.get("usp",""):
        score -= 5; warnings.append("Budget limité sans différentiation (-5)")

    if data.get("stage","idea") == "idea" and data.get("budget_tier") == "low":
        warnings.append("Phase d'idée + budget faible → valider d'abord le marché")

    score = max(10, min(99, score))
    label = ("Très Prometteur 🚀" if score>=80 else "Prometteur ✅" if score>=65 else "Modéré ⚠️" if score>=45 else "À Retravailler 🔄")
    color = ("#22e87a" if score>=80 else "#88cc22" if score>=65 else "#ffcc22" if score>=45 else "#ff6644")

    return {"score":score,"label":label,"color":color,"bonuses":bonuses,"warnings":warnings}


def _market_analysis(data, ind, geo_scope, geo_countries):
    segments = []
    niches = []
    industry = data.get("industry","other")
    model = data.get("model","B2C")

    niche_map = {
        "tech":["SaaS B2B","Apps mobiles","IA / Automatisation","Cybersécurité","Cloud computing"],
        "health":["Télémédecine","Bien-être mental","Nutrition personnalisée","FitTech","Silver economy"],
        "education":["E-learning","Micro-certifications","Upskilling professionnel","EdTech enfants","Langues en ligne"],
        "food":["Alimentation saine","Livraison rapide","Dark kitchens","Végétalien","Produits locaux"],
        "retail":["D2C (Direct-to-consumer)","Niche spécialisée","Abonnement box","Marketplace","Recommerce"],
        "finance":["Fintech inclusif","Crypto/DeFi","Micro-assurance","Épargne automatique","Transferts diaspora"],
        "services":["Freelance premium","Maintenance","Nettoyage entreprises","Événementiel","RH externalisée"],
        "fashion":["Mode durable","Seconde main","Mode inclusive","Vêtements personnalisés","Accessoires niche"],
        "real_estate":["Location courte durée","Coliving","PropTech","Investissement fractionné","Gestion locative"],
        "travel":["Tourisme local","Expériences authentiques","Slow travel","Tourisme médical","Aventure extrême"],
        "beauty":["Beauté naturelle","Cosmétiques ethniques","Soins masculins","Abonnement beauté","Dermato online"],
        "consulting":["Stratégie digitale","Transformation IA","Développement RH","Compliance","Impact ESG"],
        "entertainment":["Streaming niche","Gaming communautaire","Live events","Podcast premium","NFT & Web3"],
        "fitness":["Coaching online","Fitness à domicile","Wearables","Communauté sportive","Sport seniors"],
        "social":["Impact communautaire","ESG pour PME","Économie solidaire","Financement participatif","Diaspora"],
        "creative":["Design-as-a-service","Motion design","Branding PME","NFT art","Économie créatrice"],
    }
    niches = niche_map.get(industry, ["Niche à identifier via étude de marché","Validation par tests MVP"])

    opp_score = (80 if ind.get("competition","") == "Faible" else
                 60 if "Moyenne" in ind.get("competition","") else
                 40)

    tam_sam = {
        "local":  {"tam":"$1–50M","sam":"$100K–$5M",   "hint":"Focus local d'abord, expansion progressive"},
        "national":{"tam":"$50M–$5B","sam":"$1M–$100M","hint":"1% de part de marché = objectif réaliste an 1"},
        "international":{"tam":ind.get("market","—"),"sam":"$10M–$1B","hint":"Commencer par 2–3 pays cibles"},
    }
    sizing = tam_sam.get(geo_scope, tam_sam["national"])

    return {
        "industry_label": ind["label"],
        "market_size":    ind["market"],
        "growth_rate":    ind["growth"],
        "trend":          ind["trend"],
        "competition":    ind["competition"],
        "opportunity_score": opp_score,
        "niches":         niches[:5],
        "tam":            sizing["tam"],
        "sam":            sizing["sam"],
        "sizing_hint":    sizing["hint"],
    }


def _audience_analysis(data, is_b2b, is_b2c, target_ages, geo_countries):
    personas = []
    pain_points_map = {
        "tech":    ["Manque de temps","Processus inefficaces","Coût des solutions actuelles","Sécurité des données"],
        "health":  ["Accès aux soins","Coût médical","Prévention négligée","Manque d'information fiable"],
        "education":["Compétences obsolètes","Coût des formations","Manque de flexibilité","Accès limité"],
        "food":    ["Manque de temps","Alimentation saine difficile","Praticité","Gaspillage alimentaire"],
        "retail":  ["Prix","Qualité","Livraison","Service après-vente","Authenticité"],
        "finance": ["Frais bancaires","Accès au crédit","Épargne difficile","Complexité financière"],
        "services":["Fiabilité prestataires","Délais","Coût","Qualité variable","Manque de transparence"],
        "fashion": ["Prix","Durabilité","Taille inclusive","Originalité","Impact environnemental"],
        "consulting":["ROI difficile à mesurer","Coût des consultants","Mise en œuvre lente","Manque de suivi"],
    }
    industry = data.get("industry","other")
    pain_points = pain_points_map.get(industry, ["Identifier via entretiens clients","Analyse des avis concurrents"])

    if is_b2c:
        for age in target_ages[:2]:
            personas.append({
                "type": "B2C",
                "age": age,
                "name": f"Persona {age} ans",
                "behavior": _persona_behavior(age, industry),
                "channels": _persona_channels(age),
                "motivation": _persona_motivation(industry),
            })
    if is_b2b:
        personas.append({
            "type": "B2B",
            "age": "25–50 ans",
            "name": "Décideur entreprise",
            "behavior": "Recherche ROI, lit des études de cas, préfère LinkedIn et email",
            "channels": ["LinkedIn","Email","Google Search","Webinaires"],
            "motivation": "Réduire les coûts, améliorer l'efficacité, innover",
        })

    return {
        "model":       data.get("model","B2C"),
        "age_groups":  target_ages,
        "personas":    personas,
        "pain_points": pain_points[:4],
        "buying_triggers": _buying_triggers(industry, data.get("model","B2C")),
        "retention_tips":  _retention_tips(industry),
    }


def _persona_behavior(age, industry):
    behaviors = {
        "13-18": "Sur TikTok/Snapchat 3h+/jour, réactif aux tendances virales, budget limité mais influenceur potentiel",
        "18-25": "Digital native, cherche authenticité, compare sur Instagram, sensible aux avis",
        "25-35": "Actif sur Instagram/YouTube, revenu disponible, cherche qualité et praticité",
        "35-45": "Sur Facebook/LinkedIn, revenu confortable, valeurs familiales, fidèle aux marques",
        "45-55": "Email et Facebook, pouvoir d'achat élevé, cherche fiabilité",
        "55+":   "Utilise surtout Facebook et email, préfère le téléphone, très fidèle",
    }
    return behaviors.get(age, "Comportement à analyser via sondages et data")


def _persona_channels(age):
    channels_map = {
        "13-18": ["TikTok","Instagram","Snapchat","YouTube"],
        "18-25": ["Instagram","TikTok","YouTube","Twitter/X"],
        "25-35": ["Instagram","Facebook","YouTube","Google"],
        "35-45": ["Facebook","YouTube","Google","Email"],
        "45-55": ["Facebook","Email","Google","LinkedIn"],
        "55+":   ["Facebook","Email","WhatsApp","Google"],
    }
    return channels_map.get(age, ["Facebook","Google","Email"])


def _persona_motivation(industry):
    motivations = {
        "tech":       "Gagner du temps, améliorer la productivité, rester compétitif",
        "health":     "Vivre mieux, prévenir les maladies, économiser sur la santé",
        "education":  "Progresser, changer de carrière, rester à jour",
        "food":       "Manger sainement sans effort, découvrir de nouvelles saveurs",
        "retail":     "Prix, qualité, praticité, originalité",
        "finance":    "Économiser, investir, sécurité financière",
        "consulting": "Croître, résoudre un problème précis, optimiser",
    }
    return motivations.get(industry, "À valider avec des entretiens clients (5 à 10 interviews)")


def _buying_triggers(industry, model):
    triggers_b2c = {
        "tech":    ["Promotion limitée","Preuve sociale","Essai gratuit","Recommandation ami"],
        "health":  ["Événement déclencheur","Recommandation médicale","Avant/après visibles"],
        "food":    ["Praticité","Goût/avis","Promo découverte","Localisation"],
        "fashion": ["Tendance virale","Soldes","Influenceur","Événement social"],
    }
    triggers_b2b = ["Étude de cas ROI","Démo personnalisée","Période d'essai","Référence client","Conférence/Webinar"]
    if model == "B2B": return triggers_b2b
    return triggers_b2c.get(industry, ["Essai gratuit","Avis clients","Preuve sociale","Offre de lancement"])


def _retention_tips(industry):
    tips = {
        "tech":    ["Onboarding fluide <5min","Emails d'activation","Score d'usage","Feature requests réguliers"],
        "health":  ["Suivi de progression","Rappels personnalisés","Communauté support","Contenu éducatif"],
        "food":    ["Programme de fidélité","Abonnement","Nouveautés régulières","Service client rapide"],
        "retail":  ["Fidélité par points","Exclusivités membres","Personnalisation","SAV excellent"],
        "education":["Certifications","Communauté d'apprenants","Mentorat","Nouveau contenu mensuel"],
    }
    return tips.get(industry, ["Programme de fidélité","Contenu de valeur régulier","Support réactif","Surprises client"])


def _competitive_analysis(data, ind, competitors, usp):
    gaps = []
    differentiation = []
    industry = data.get("industry","other")

    gap_map = {
        "tech":    ["Simplicité d'utilisation","Prix accessible PME","Support en langue locale","Intégrations natives"],
        "health":  ["Accessibilité financière","Approche holistique","Suivi personnalisé","Temps de réponse"],
        "food":    ["Diététique & goût","Origine traçable","Livraison rapide","Personnalisation"],
        "retail":  ["Service après-vente","Authenticité","Personnalisation","Prix transparent"],
        "education":["Résultats mesurables","Flexibilité","Prix","Accompagnement humain"],
        "consulting":["Prix SME-friendly","ROI mesurable","Exécution pas seulement conseil","Secteur de niche"],
        "fashion": ["Inclusion de taille","Durabilité","Prix équitable","Histoire de marque"],
    }
    gaps = gap_map.get(industry, ["Valider en analysant les avis négatifs 1 étoile des concurrents","Price gap","Service gap","Geographic gap"])

    diff_map = {
        "tech":    ["Algorithmes intégrés","No-code","API ouverte","Pricing transparent"],
        "health":  ["Approche préventive","Expertise spécialisée","Communauté support","Accessibilité"],
        "food":    ["Local & artisanal","Transparence ingrédients","Diététicien intégré","Impact environnemental 0"],
        "consulting":["Résultats garantis","Accompagnement implémentation","Secteur ultra-niche","Pricing à la performance"],
    }
    differentiation = diff_map.get(industry, ["Prix","Qualité supérieure","Service client","Niche très précise","Expérience unique"])

    comp_level = ind.get("competition","")
    strategy = ("Différenciation forte et niche précise indispensable" if "Très élevée" in comp_level else
                "Positionnement clair suffit" if "Faible" in comp_level else
                "Focus sur 1–2 avantages distinctifs")

    return {
        "known_competitors": competitors[:5] if competitors else ["À identifier via Google, App stores, forums"],
        "market_gaps":       gaps[:4],
        "differentiation_ideas": differentiation[:4],
        "usp_analysis":      _analyze_usp(usp),
        "strategy_hint":     strategy,
        "competition_level": comp_level,
    }


def _analyze_usp(usp):
    if not usp or len(usp.strip()) < 10:
        return {"quality":"À définir","feedback":"❌ Aucune USP fournie — c'est CRITIQUE. Complétez : 'Nous aidons [qui] à [résultat] grâce à [différentiation]'","score":0}
    words = len(usp.split())
    if words < 5:
        return {"quality":"Trop vague","feedback":"⚠️ USP trop courte. Précisez le bénéfice et la cible.","score":40}
    if words <= 20:
        return {"quality":"Bonne","feedback":"✅ USP concise et claire. Testez-la avec 10 clients potentiels.","score":75}
    return {"quality":"Détaillée","feedback":"✅ USP complète. Réduisez à 1 phrase percutante pour la pub.","score":85}


def _product_recommendations(data, ind, prod_type, price_range, stage):
    positioning_map = {
        ("product","premium"): "Luxe & exclusivité — storytelling de marque, packaging premium, distribution sélective",
        ("product","medium"):  "Rapport qualité-prix — comparatifs, avis, garantie satisfaction",
        ("digital","low"):     "Freemium — gratuit pour acquérir, payant pour retenir (modèle Spotify)",
        ("saas","medium"):     "PLG (Product-Led Growth) — essai gratuit, expansion par usage",
        ("saas","high"):       "Enterprise — démo + POC + contrat annuel",
        ("service","medium"):  "Expertise visible — cas d'étude, certifications, témoignages",
        ("consulting","high"): "Premium positioning — thought leadership, conférences, publications",
        ("app","low"):         "Freemium — in-app purchases, abonnement premium",
    }
    positioning = positioning_map.get((prod_type, price_range),
        "Positionnement à affiner selon la cible et la concurrence")

    pricing_recs = {
        "free":    ["Monétisation par pub ou data","Freemium → Premium","Sponsoring"],
        "low":     ["Prix d'entrée attractif","Upsell vers premium","Volume > marge"],
        "medium":  ["Abonnement mensuel/annuel","Packages","Essai gratuit"],
        "high":    ["Valeur perçue > coût","ROI démontrable","Paiement échelonné"],
        "premium": ["Luxury pricing","Exclusivité","Service white-glove","Lifetime deal"],
    }
    pricing = pricing_recs.get(price_range, pricing_recs["medium"])

    mvp_recs = {
        "idea":   ["Valider avec 10 entretiens clients","Landing page + liste d'attente","Prototype Figma","Pré-ventes"],
        "mvp":    ["Beta fermée 50–100 utilisateurs","Collecter avis hebdo","Itérer vite","NPS tracking"],
        "early":  ["Product-market fit score","Expansion canal principal","First 100 clients","Referral program"],
        "growth": ["Automatisation acquisition","Scale du canal qui fonctionne","Expansion géo","Upsell/Cross-sell"],
    }
    mvp = mvp_recs.get(stage, mvp_recs["idea"])

    return {
        "prod_type":   prod_type,
        "price_range": price_range,
        "positioning": positioning,
        "pricing_recs":pricing,
        "mvp_steps":   mvp,
        "key_metrics": _key_metrics(prod_type, data.get("goal","sales")),
    }


def _key_metrics(prod_type, goal):
    metrics = {
        "saas":      ["MRR/ARR","Churn rate","CAC","LTV","NPS","Activation rate"],
        "app":       ["DAU/MAU","Retention D1/D7/D30","ARPU","Reviews","Crash rate"],
        "product":   ["Ventes/mois","Panier moyen","Taux de retour","NPS","Repeat purchase"],
        "service":   ["Nouveaux clients/mois","Taux de fidélisation","Marge","Satisfaction","Referrals"],
        "consulting":["Revenue/consultant","Utilisation","NPS","Durée contrats","Upsell rate"],
        "digital":   ["Téléchargements","Utilisateurs actifs","Taux conversion","ARPU","Churn"],
    }
    return metrics.get(prod_type, ["Revenu mensuel","Coût d'acquisition","Taux de rétention","NPS","ROI marketing"])


def _launch_strategy(data, stage, timeline, goal, budget_tier):
    phases = {
        "idea": [
            {"phase":"Phase 0 — Validation (Sem. 1–4)","actions":["10 entretiens clients","Landing page + waitlist","Analyse concurrents","Définir MVP minimum"],"kpi":"50+ inscrits waitlist"},
            {"phase":"Phase 1 — MVP (Mois 2–4)","actions":["Développer MVP core","Beta test 20 utilisateurs","Itérer rapidement","Documenter le feedback"],"kpi":"NPS > 40"},
            {"phase":"Phase 2 — Lancement (Mois 4–6)","actions":["Lancement public","Campagne acquisition","PR & médias","Optimiser conversion"],"kpi":"100 premiers clients"},
        ],
        "mvp": [
            {"phase":"Phase 1 — Beta (Mois 1–2)","actions":["Finir le MVP","Beta fermée 50 users","Corriger les bugs critiques","Collecter NPS"],"kpi":"NPS > 40, 0 bugs bloquants"},
            {"phase":"Phase 2 — Lancement (Mois 3–4)","actions":["Lancement public","Activation des canaux","Offre de lancement -30%","Partenariats locaux"],"kpi":"500 utilisateurs"},
            {"phase":"Phase 3 — Scale (Mois 5+)","actions":["Automatiser l'acquisition","Affiner le canal principal","Expansion géo","Upsell"],"kpi":"10% MoM growth"},
        ],
        "early": [
            {"phase":"Phase 1 — Optimisation (Mois 1–2)","actions":["Identifier le canal #1","Doubler dessus","Réduire le CAC","Programme referral"],"kpi":"CAC < LTV/3"},
            {"phase":"Phase 2 — Scale (Mois 3–6)","actions":["Équipe marketing","Contenu SEO","Partenariats stratégiques","Levée de fonds si nécessaire"],"kpi":"10% MoM revenue"},
            {"phase":"Phase 3 — Expansion (Mois 7+)","actions":["Nouveau marché géo","Nouveau segment","M&A éventuel","Brand building"],"kpi":"Leader de niche local"},
        ],
        "growth": [
            {"phase":"Phase 1 — Consolidation","actions":["Optimiser la rentabilité","Renforcer la culture","Automatiser les process","Data-driven decision making"],"kpi":"Marge brute > 60%"},
            {"phase":"Phase 2 — Diversification","actions":["Nouveau produit / vertical","Acquisition stratégique","Expansion internationale","Développer la marque employeur"],"kpi":"Nouveau revenue stream > 20% CA"},
        ],
    }

    go_to_market = {
        "awareness": "Stratégie Brand First — contenu viral + influenceurs + PR",
        "leads":     "Stratégie Lead Gen — SEO + Google Ads + Landing pages + Email",
        "sales":     "Stratégie Conversion — tests A/B + retargeting + offres limitées + témoignages",
        "downloads": "Stratégie App Growth — ASO + TikTok + influenceurs + reviews",
        "community": "Stratégie Community-Led — Discord/Slack + ambassadeurs + événements",
    }

    return {
        "phases":        phases.get(stage, phases["idea"]),
        "go_to_market":  go_to_market.get(goal, go_to_market["sales"]),
        "launch_checklist": [
            "✅ Landing page avec CTA clair",
            "✅ Pixel tracking (Meta + Google) installé",
            "✅ Email de bienvenue automatisé",
            "✅ CGV + politique de confidentialité en ligne",
            "✅ Témoignages / preuve sociale visibles",
            "✅ Page FAQ complète",
            "✅ Support client configuré (chat/email)",
            "✅ Analytics (GA4) installé et testé",
            "✅ Page 404 personnalisée",
            "✅ Backup et sécurité en place",
        ],
    }


def _recommend_channels(data, industry, model, target_ages, budget_tier, is_b2b, is_b2c, is_young, is_senior):
    scored = {}
    for key, p in PLATFORMS.items():
        score = 0
        if is_b2b:   score += p.get("score_b2b",0) * 0.4
        if is_b2c:   score += p.get("score_b2c",0) * 0.4
        if is_young: score += p.get("score_young",0) * 0.15
        if is_senior:score += p.get("score_senior",0) * 0.15

        budget_ok = (p.get("monthly_min",0) <= 100 if budget_tier == "low" else
                     p.get("monthly_min",0) <= 500 if budget_tier == "mid" else True)
        if budget_ok: score += 10

        # industry bonus
        ind_match = any(industry in pf for pf in p.get("best_for",[]))
        if ind_match: score += 15

        scored[key] = round(score)

    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    return [
        {
            "key": k,
            "name": PLATFORMS[k]["name"],
            "icon": PLATFORMS[k]["icon"],
            "score": s,
            "reach": PLATFORMS[k]["reach"],
            "cpc":   PLATFORMS[k].get("cpc","Variable"),
            "strengths": PLATFORMS[k]["strengths"][:2],
            "best_for":  PLATFORMS[k]["best_for"][:3],
            "monthly_min": PLATFORMS[k].get("monthly_min",0),
        }
        for k, s in ranked[:8]
    ]


def _platform_priorities(channels, budget_tier):
    top3 = channels[:3]
    budget_split = {
        "low":     [60, 30, 10],
        "mid":     [50, 30, 20],
        "high":    [40, 35, 25],
        "premium": [35, 35, 30],
    }
    splits = budget_split.get(budget_tier, [50,30,20])
    result = []
    for i, ch in enumerate(top3):
        result.append({
            **ch,
            "budget_pct": splits[i],
            "priority": ["#1 Prioritaire","#2 Secondaire","#3 Complémentaire"][i],
        })
    return result


def _geo_analysis(data, geo_scope, geo_countries, languages, industry):
    primary = []
    secondary = []
    emerging = []

    for country in geo_countries:
        cd = COUNTRIES_DATA.get(country, {})
        if cd:
            primary.append({"country": country, **cd})

    # Auto-suggest secondary markets based on language
    lang_markets = {
        "fr": ["France","Canada","Belgique","Suisse","Sénégal","Côte d'Ivoire","Maroc","Haïti"],
        "en": ["USA","UK","Canada","Australie","Nigeria","Afrique du Sud"],
        "es": ["Mexique","Colombie","Argentine","Espagne"],
        "pt": ["Brésil","Portugal"],
        "ht": ["Haïti","Caraïbes"],
    }
    suggested = []
    for lang in languages:
        for market in lang_markets.get(lang,[]):
            if market not in geo_countries:
                suggested.append(market)

    for m in suggested[:4]:
        cd = COUNTRIES_DATA.get(m,{})
        if cd:
            risk = cd.get("risk","Moyenne")
            opp  = cd.get("opportunity","Haute")
            if "Faible" in risk:   secondary.append({"country":m,**cd})
            else:                  emerging.append({"country":m,**cd})

    return {
        "scope":     geo_scope,
        "primary":   primary[:3],
        "secondary": secondary[:3],
        "emerging":  emerging[:3],
        "expansion_tip": (
            "Focus sur 1 marché principal d'abord → maîtriser → expanser" if geo_scope == "local" else
            "Tester 2–3 marchés secondaires simultanément avec budget mini" if geo_scope == "national" else
            "Localisation (langue, paiement, réglementation) indispensable par marché"
        ),
    }


def _budget_allocation(data, channels, budget_tier, goal):
    budgets = {
        "low":     {"total":"$500–$1 000/mois",  "total_launch":"$1 000–$3 000"},
        "mid":     {"total":"$1 000–$5 000/mois", "total_launch":"$5 000–$15 000"},
        "high":    {"total":"$5 000–$20 000/mois","total_launch":"$20 000–$60 000"},
        "premium": {"total":"$20 000+/mois",      "total_launch":"$60 000+"},
    }
    alloc_map = {
        "awareness": {"Publicité payante":40,"Contenu/Créatif":25,"SEO/Blog":20,"Influenceurs":15},
        "leads":     {"Google Ads":35,"SEO/Content":25,"Email marketing":20,"LinkedIn/Ads":20},
        "sales":     {"Publicité payante":45,"Retargeting":20,"Email automatisé":20,"Créatif/Tests":15},
        "downloads": {"App Ads":40,"Influenceurs":25,"ASO":20,"Réseaux sociaux":15},
        "community": {"Contenu/Créatif":35,"Événements/Lives":25,"Email":20,"Social Ads":20},
    }
    alloc = alloc_map.get(goal, alloc_map["sales"])
    b = budgets.get(budget_tier, budgets["mid"])

    return {
        "budget_tier":    budget_tier,
        "monthly_budget": b["total"],
        "launch_budget":  b["total_launch"],
        "allocation":     alloc,
        "roi_expectation": (
            "ROI difficile à mesurer en phase 0 — focus sur apprentissages" if budget_tier == "low" else
            "ROI positif attendu en 3–6 mois" if budget_tier == "mid" else
            "ROI positif en 1–3 mois avec bonne exécution"
        ),
        "quick_wins": [
            "Email marketing (ROI 42:1 en moyenne)",
            "SEO — investissement durable",
            "Referral program — croissance organique",
            "Partenariats — coût faible, impact fort",
        ],
    }


def _risk_assessment(data, ind, stage, budget_tier, competitors):
    risks = []
    mitigations = []

    if stage == "idea":
        risks.append({"level":"Élevé","risk":"Absence de validation marché","impact":"Développer quelque chose que personne ne veut"})
        mitigations.append("Faire 10 entretiens clients AVANT de coder/produire")

    if budget_tier == "low":
        risks.append({"level":"Moyen","risk":"Budget insuffisant pour tester assez vite","impact":"Epuisement avant d'atteindre la rentabilité"})
        mitigations.append("Channels organiques en priorité (SEO, referral, contenu)")

    if "Très élevée" in ind.get("competition",""):
        risks.append({"level":"Élevé","risk":"Concurrence très intense","impact":"Difficile de se démarquer sans niche précise"})
        mitigations.append("Niche très précise + un seul avantage imbattable")

    if not data.get("usp","").strip():
        risks.append({"level":"Critique","risk":"Pas d'USP définie","impact":"Être perçu comme une copie, guerre des prix"})
        mitigations.append("Définir l'USP avant tout lancement marketing")

    if len(competitors) > 3:
        risks.append({"level":"Moyen","risk":"Marché saturé","impact":"CAC élevé, marges compressées"})
        mitigations.append("Sur-nicher : cibler un sous-segment ignoré par les leaders")

    risks.append({"level":"Faible","risk":"Dépendance à une seule plateforme","impact":"Changement d'algorithme = perte de trafic"})
    mitigations.append("Diversifier les canaux dès le début")

    risks.append({"level":"Faible","risk":"Réglementation (RGPD, CCPA, secteur)","impact":"Amendes, réputation"})
    mitigations.append("Consulter un juriste spécialisé avant le lancement")

    return {"risks": risks[:6], "mitigations": mitigations}


def _action_plan(data, stage, channels, goal, geo_scope, timeline):
    top_channel = channels[0]["name"] if channels else "Canal principal"
    second_channel = channels[1]["name"] if len(channels)>1 else "Canal secondaire"

    plans = {
        "idea": {
            "30": [
                f"Réaliser 10 entretiens clients (30 min chacun)",
                "Créer une landing page de pré-lancement (waitlist)",
                "Analyser les avis 1★ des concurrents sur Google/App Store",
                "Définir et valider votre USP en 1 phrase",
                "Rejoindre 3 communautés où se trouve votre cible",
                "Créer un prototype Figma ou maquette papier",
            ],
            "60": [
                "Lancer le MVP minimum fonctionnel",
                "Recruter 20 beta testeurs via votre réseau",
                f"Ouvrir un compte {top_channel} et publier 3x/semaine",
                "Mettre en place Google Analytics 4 + tracking conversions",
                "Définir les 3 métriques clés à suivre",
                "Créer la page About, FAQ, Contact de votre site",
            ],
            "90": [
                "Lancement public officiel avec campagne",
                f"Lancer la première campagne payante {top_channel}",
                "Activer un programme referral (parrainage)",
                "Viser les 100 premiers clients/utilisateurs",
                "Recueillir 10 témoignages clients",
                "Itérer le produit selon les feedbacks reçus",
            ],
        },
        "mvp": {
            "30": [
                "Finaliser et débugger le MVP",
                "Lancer une beta fermée à 50 utilisateurs",
                "Mesurer le NPS et la rétention hebdomadaire",
                f"Activer {top_channel} avec contenu organique",
                "Mettre en place l'email de bienvenue automatisé",
                "Créer 5 contenus de valeur (blog/vidéo/post)",
            ],
            "60": [
                "Lancement public avec offre -30%",
                f"Budget test {top_channel}: $200–500",
                "Activer le retargeting",
                "Lancer un programme affilié ou referral",
                "Viser 200 utilisateurs actifs",
                f"Explorer {second_channel}",
            ],
            "90": [
                "Atteindre 500 clients / utilisateurs",
                "Identifier et doubler le canal qui convertit le mieux",
                "Créer une étude de cas avec 3 clients témoins",
                "Lancer la version 2 du produit",
                "Rechercher 2 partenariats stratégiques",
                "Atteindre la rentabilité sur au moins 1 canal",
            ],
        },
    }

    default = plans.get(stage, plans["idea"])
    return {
        "day30": default["30"],
        "day60": default["60"],
        "day90": default["90"],
        "north_star": (
            "100 premiers clients payants" if goal=="sales" else
            "1 000 utilisateurs actifs" if goal=="downloads" else
            "500 leads qualifiés" if goal=="leads" else
            "100 000 impressions organiques" if goal=="awareness" else
            "1 000 membres actifs de communauté"
        ),
    }
