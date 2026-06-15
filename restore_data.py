"""
PREDIKTA — one-time data restoration script.

Run this on the production instance (Render Web Shell, in ~/project/src).
It merges the deep draw history committed in git (main branch on GitHub)
into the persistent disk's data/ files, without removing anything already
on disk (union by date+tod, newest first).

Only touches:
  - data/<state>.csv  (2-letter state Pick3/Cash3 history)
  - data/games/<STATE>/<slug>.json  (multi-game history)

Does NOT touch data/contacts.json, data/subscribers.json, vapid keys, etc.
"""
import csv
import io
import json
import os
import re
import urllib.request

REPO = "jehopakingconsulting-alt/predikta-platform"
BRANCH = "main"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
TREE_API = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "predikta-restore"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def merge_csv(path: str, remote_text: str) -> int:
    remote_rows = list(csv.DictReader(io.StringIO(remote_text)))
    if not remote_rows:
        return 0
    local_rows = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            local_rows = list(csv.DictReader(f))

    merged = {}
    for r in remote_rows + local_rows:
        merged[f"{r['date']}_{r['tod']}"] = r

    out = sorted(merged.values(), key=lambda r: (r["date"], r["tod"]), reverse=True)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=remote_rows[0].keys())
        w.writeheader()
        w.writerows(out)
    return len(out)


def merge_json(path: str, remote_text: str) -> int:
    remote_data = json.loads(remote_text)
    if isinstance(remote_data, dict):
        remote_data = list(remote_data.values())
    if not remote_data:
        return 0

    local_data = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            local_data = json.load(f)
    if isinstance(local_data, dict):
        local_data = list(local_data.values())

    merged = {}
    for d in remote_data + local_data:
        merged[f"{d.get('date','')}_{d.get('tod','')}"] = d

    out = sorted(merged.values(), key=lambda d: d.get("date", ""), reverse=True)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return len(out)


def main():
    tree = json.loads(fetch(TREE_API))["tree"]
    paths = [t["path"] for t in tree if t["type"] == "blob"]

    state_csv = [p for p in paths if re.fullmatch(r"data/[a-z]{2}\.csv", p)]
    games_json = [p for p in paths if p.startswith("data/games/") and p.endswith(".json")]

    print(f"Restoring {len(state_csv)} state CSVs + {len(games_json)} game JSON files...")

    for path in state_csv:
        try:
            remote_text = fetch(RAW + path)
            total = merge_csv(path, remote_text)
            print(f"  {path} -> {total} draws")
        except Exception as e:
            print(f"  {path}: ERROR {e}")

    for path in games_json:
        try:
            remote_text = fetch(RAW + path)
            total = merge_json(path, remote_text)
            print(f"  {path} -> {total} entries")
        except Exception as e:
            print(f"  {path}: ERROR {e}")

    print("Done.")


if __name__ == "__main__":
    main()
