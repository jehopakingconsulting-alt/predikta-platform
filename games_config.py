"""
PREDIKTA AI — Complete Games Registry
All lottery games per state from lotterypost.com
"""

# Game type definitions
# num_balls: count of main numbers drawn
# extra_balls: count of bonus/extra balls (Powerball, Mega Ball, etc.)
# extra_name: name of the bonus ball

GAME_TYPES = {
    "pick2":     {"label": "Pick 2",         "num_balls": 2, "extra_balls": 0, "icon": "2️⃣"},
    "pick3":     {"label": "Pick 3",         "num_balls": 3, "extra_balls": 0, "icon": "3️⃣"},
    "pick4":     {"label": "Pick 4",         "num_balls": 4, "extra_balls": 0, "icon": "4️⃣"},
    "pick5":     {"label": "Pick 5",         "num_balls": 5, "extra_balls": 0, "icon": "5️⃣"},
    "pick6":     {"label": "Lotto (6)",      "num_balls": 6, "extra_balls": 0, "icon": "🎱"},
    "multi5p1":  {"label": "5+1 Ball",       "num_balls": 5, "extra_balls": 1, "icon": "⚡"},
    "multi5p2":  {"label": "5+2 Ball",       "num_balls": 5, "extra_balls": 2, "icon": "🌟"},
}

# Full game registry per state
# Each game: slug, label, game_type, draws_per_day
STATE_GAMES = {

    "NY": [
        {"slug": "numbers",              "label": "Numbers (Pick 3)",       "type": "pick3",    "dpd": 2},
        {"slug": "midday-numbers",       "label": "Numbers Midday",         "type": "pick3",    "dpd": 1},
        {"slug": "win4",                 "label": "Win 4",                  "type": "pick4",    "dpd": 2},
        {"slug": "midday-win4",          "label": "Win 4 Midday",           "type": "pick4",    "dpd": 1},
        {"slug": "take5",                "label": "Take 5",                 "type": "pick5",    "dpd": 2},
        {"slug": "take5-midday",         "label": "Take 5 Midday",          "type": "pick5",    "dpd": 1},
        {"slug": "lotto",                "label": "Lotto",                  "type": "pick6",    "dpd": 1},
        {"slug": "pick10",               "label": "Pick 10",                "type": "pick5",    "dpd": 1},  # 20 balls pick 10
        {"slug": "cash4life",            "label": "Cash4Life",              "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "GA": [
        {"slug": "cash3",                "label": "Cash 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "cash3-midday",         "label": "Cash 3 Midday",         "type": "pick3",    "dpd": 1},
        {"slug": "cash4",                "label": "Cash 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "cash4-midday",         "label": "Cash 4 Midday",         "type": "pick4",    "dpd": 1},
        {"slug": "fantasy5",             "label": "Fantasy 5",              "type": "pick5",    "dpd": 1},
        {"slug": "jumbo-bucks-lotto",    "label": "Jumbo Bucks Lotto",      "type": "pick6",    "dpd": 1},
        {"slug": "cash4life",            "label": "Cash4Life",              "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "TX": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 4},
        {"slug": "daily4",               "label": "Daily 4",                "type": "pick4",    "dpd": 4},
        {"slug": "cash5",                "label": "Cash 5",                 "type": "pick5",    "dpd": 1},
        {"slug": "allornothing",         "label": "All or Nothing",         "type": "pick5",    "dpd": 2},
        {"slug": "lotto-texas",          "label": "Lotto Texas",            "type": "pick6",    "dpd": 1},
        {"slug": "texastwostep",         "label": "Texas Two Step",         "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "FL": [
        {"slug": "pick2",                "label": "Pick 2",                 "type": "pick2",    "dpd": 2},
        {"slug": "pick2-midday",         "label": "Pick 2 Midday",         "type": "pick2",    "dpd": 1},
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick3-midday",         "label": "Pick 3 Midday",         "type": "pick3",    "dpd": 1},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "pick4-midday",         "label": "Pick 4 Midday",         "type": "pick4",    "dpd": 1},
        {"slug": "pick5",                "label": "Pick 5",                 "type": "pick5",    "dpd": 2},
        {"slug": "pick5-midday",         "label": "Pick 5 Midday",         "type": "pick5",    "dpd": 1},
        {"slug": "fantasy5",             "label": "Fantasy 5",              "type": "pick5",    "dpd": 1},
        {"slug": "lotto",                "label": "Florida Lotto",          "type": "pick6",    "dpd": 1},
        {"slug": "cash4life",            "label": "Cash4Life",              "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "CA": [
        {"slug": "daily3",               "label": "Daily 3",                "type": "pick3",    "dpd": 2},
        {"slug": "daily4",               "label": "Daily 4",                "type": "pick4",    "dpd": 2},
        {"slug": "daily-derby",          "label": "Daily Derby",            "type": "pick5",    "dpd": 1},
        {"slug": "fantasy5",             "label": "Fantasy 5",              "type": "pick5",    "dpd": 1},
        {"slug": "superlottoplus",        "label": "SuperLotto Plus",        "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "PA": [
        {"slug": "pick2",                "label": "Pick 2",                 "type": "pick2",    "dpd": 2},
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "pick5",                "label": "Pick 5",                 "type": "pick5",    "dpd": 2},
        {"slug": "cash5",                "label": "Cash 5",                 "type": "pick5",    "dpd": 1},
        {"slug": "match6lotto",          "label": "Match 6 Lotto",          "type": "pick6",    "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "NJ": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "cash5",                "label": "Cash 5",                 "type": "pick5",    "dpd": 1},
        {"slug": "jersey-cash-5",        "label": "Jersey Cash 5",          "type": "pick5",    "dpd": 1},
        {"slug": "pick6",                "label": "Pick 6",                 "type": "pick6",    "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "IL": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "lotto",                "label": "Lotto",                  "type": "pick6",    "dpd": 1},
        {"slug": "lucky-day-lotto",      "label": "Lucky Day Lotto",        "type": "pick5",    "dpd": 2},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "OH": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "pick5",                "label": "Pick 5",                 "type": "pick5",    "dpd": 2},
        {"slug": "rolling-cash-5",       "label": "Rolling Cash 5",         "type": "pick5",    "dpd": 1},
        {"slug": "classic-lotto",        "label": "Classic Lotto",          "type": "pick6",    "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "NC": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "cash5",                "label": "Cash 5",                 "type": "pick5",    "dpd": 1},
        {"slug": "lucky-for-life",       "label": "Lucky For Life",         "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "VA": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "cash5",                "label": "Cash 5",                 "type": "pick5",    "dpd": 1},
        {"slug": "bank-a-million",       "label": "Bank a Million",         "type": "pick5",    "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "MA": [
        {"slug": "numbers",              "label": "Numbers",                "type": "pick3",    "dpd": 2},
        {"slug": "masscash",             "label": "Mass Cash",              "type": "pick5",    "dpd": 1},
        {"slug": "megabucks",            "label": "Megabucks",              "type": "pick6",    "dpd": 1},
        {"slug": "lucky-for-life",       "label": "Lucky For Life",         "type": "multi5p1", "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "MD": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "bonus-match-5",        "label": "Bonus Match 5",          "type": "pick5",    "dpd": 1},
        {"slug": "multimatch",           "label": "MultiMatch",             "type": "pick6",    "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],

    "MI": [
        {"slug": "pick3",                "label": "Pick 3",                 "type": "pick3",    "dpd": 2},
        {"slug": "pick4",                "label": "Pick 4",                 "type": "pick4",    "dpd": 2},
        {"slug": "fantasy5",             "label": "Fantasy 5",              "type": "pick5",    "dpd": 1},
        {"slug": "lotto47",              "label": "Lotto 47",               "type": "pick6",    "dpd": 1},
        {"slug": "megamillions",         "label": "Mega Millions",          "type": "multi5p1", "dpd": 1},
        {"slug": "powerball",            "label": "Powerball",              "type": "multi5p1", "dpd": 1},
    ],
}

# Shared national games (all states that participate)
NATIONAL_GAMES = {
    "powerball":     {"label": "Powerball",      "type": "multi5p1", "slug": "powerball",    "icon": "🔴", "draw_days": "Mon/Wed/Sat"},
    "megamillions":  {"label": "Mega Millions",  "type": "multi5p1", "slug": "megamillions", "icon": "🔵", "draw_days": "Tue/Fri"},
    "cash4life":     {"label": "Cash4Life",       "type": "multi5p1", "slug": "cash4life",    "icon": "💚", "draw_days": "Daily"},
    "lucky-for-life":{"label": "Lucky For Life", "type": "multi5p1", "slug": "lucky-for-life","icon": "🍀","draw_days": "Mon/Thu"},
}
