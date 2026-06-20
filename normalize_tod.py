"""
ZYNORIQ — one-time data normalization script.

Several states (CT, DE, ID, ME, NC, NH, NM, PA, PR, VA, VT, TX) have their
midday/afternoon draw session labeled "Day" in DRAW_SCHEDULE (app.py) and in
older history, but the lotteryusa.com scraper (added later) tags that same
session "Midday". The mismatch means recently-scraped rows don't match
DRAW_SCHEDULE's "tod", so home.html can't find a draw time for them and
duplicate rows (same date, same numbers, "Day" vs "Midday") pile up.

This script renames tod "Day" -> "Midday" in:
  - data/<state>.csv
  - data/games/<STATE>/*.json
for the affected states, then de-duplicates rows that now share the same
date+tod (keeping one).

Run locally AND on production (Render Web Shell, in ~/project/src), same as
restore_data.py.
"""
import csv
import glob
import json
import os

AFFECTED = ["CT", "DE", "ID", "ME", "NC", "NH", "NM", "PA", "PR", "VA", "VT", "TX"]


def normalize_csv(path: str) -> tuple[int, int]:
    if not os.path.exists(path):
        return 0, 0
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 0, 0

    renamed = 0
    for r in rows:
        if r.get("tod") == "Day":
            r["tod"] = "Midday"
            renamed += 1

    merged = {}
    for r in rows:
        merged[f"{r['date']}_{r['tod']}"] = r
    out = sorted(merged.values(), key=lambda r: (r["date"], r["tod"]), reverse=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(out)

    return renamed, len(rows) - len(out)


def normalize_json(path: str) -> tuple[int, int]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return 0, 0

    renamed = 0
    for d in data:
        if d.get("tod") == "Day":
            d["tod"] = "Midday"
            renamed += 1

    merged = {}
    for d in data:
        merged[f"{d.get('date','')}_{d.get('tod','')}"] = d
    out = sorted(merged.values(), key=lambda d: d.get("date", ""), reverse=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    return renamed, len(data) - len(out)


def main():
    for code in AFFECTED:
        path = f"data/{code.lower()}.csv"
        renamed, removed = normalize_csv(path)
        if renamed or removed:
            print(f"  {path}: renamed {renamed} 'Day'->'Midday', removed {removed} duplicate(s)")

        for path in glob.glob(f"data/games/{code}/*.json"):
            renamed, removed = normalize_json(path)
            if renamed or removed:
                print(f"  {path}: renamed {renamed} 'Day'->'Midday', removed {removed} duplicate(s)")

    print("Done.")


if __name__ == "__main__":
    main()
