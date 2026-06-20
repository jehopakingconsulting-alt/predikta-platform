"""
ZYNORIQ — one-time data restoration script.

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
import shutil
import subprocess
import tempfile

REPO_URL = "https://github.com/jehopakingconsulting-alt/predikta-platform.git"


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
    clone_dir = tempfile.mkdtemp(prefix="predikta-restore-")
    print(f"Cloning {REPO_URL} into {clone_dir} ...")
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, clone_dir],
        check=True,
    )

    remote_data_dir = os.path.join(clone_dir, "data")

    state_csv = []
    games_json = []
    for root, _dirs, files in os.walk(remote_data_dir):
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, clone_dir).replace(os.sep, "/")
            if re.fullmatch(r"data/[a-z]{2}\.csv", rel):
                state_csv.append(rel)
            elif rel.startswith("data/games/") and rel.endswith(".json"):
                games_json.append(rel)

    print(f"Restoring {len(state_csv)} state CSVs + {len(games_json)} game JSON files...")

    for path in state_csv:
        try:
            with open(os.path.join(clone_dir, path), encoding="utf-8") as f:
                remote_text = f.read()
            total = merge_csv(path, remote_text)
            print(f"  {path} -> {total} draws")
        except Exception as e:
            print(f"  {path}: ERROR {e}")

    for path in games_json:
        try:
            with open(os.path.join(clone_dir, path), encoding="utf-8") as f:
                remote_text = f.read()
            total = merge_json(path, remote_text)
            print(f"  {path} -> {total} entries")
        except Exception as e:
            print(f"  {path}: ERROR {e}")

    shutil.rmtree(clone_dir, ignore_errors=True)
    print("Done.")


if __name__ == "__main__":
    main()
