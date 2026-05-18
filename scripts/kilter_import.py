#!/usr/bin/env python3
"""Convert a Kilter Board JSON export (Aurora app export) into a CSV that
matches the schema used by logbook.csv (Tension). Derived fields
(sessions_count, tries_total, is_repeat) are computed per-climb in
chronological order across the events in the export."""

import argparse
import csv
import json
from pathlib import Path

# Map French grade -> "French/V" string, aligned with GRADE_ORDER in logbook.html
GRADE_MAP = {
    "4a": "4a/V0", "4b": "4b/V0", "4c": "4c/V0",
    "5a": "5a/V1", "5b": "5b/V1", "5c": "5c/V2",
    "6a": "6a/V3", "6a+": "6a+/V3",
    "6b": "6b/V4", "6b+": "6b+/V4",
    "6c": "6c/V5", "6c+": "6c+/V5",
    "7a": "7a/V6", "7a+": "7a+/V7",
    "7b": "7b/V8", "7b+": "7b+/V8",
    "7c": "7c/V9", "7c+": "7c+/V10",
    "8a": "8a/V11",
}

ATTEMPT_STR = {"Flash": 1, "2 tries": 2, "3 tries": 3, "4 tries": 4, "5 tries": 5}


def normalize_grade(g):
    if not g:
        return ""
    return GRADE_MAP.get(g, g)


def parse_tries(s):
    if not s:
        return 1
    if s in ATTEMPT_STR:
        return ATTEMPT_STR[s]
    if isinstance(s, str) and s.endswith(" tries"):
        try:
            return int(s.split()[0])
        except ValueError:
            return 1
    return 1


def clean(s):
    return (s or "").replace("\r", " ").replace("\n", " ").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="path to the Kilter export JSON")
    ap.add_argument("output", type=Path, help="path to write kilter.csv")
    ap.add_argument("--board", default="kilter")
    args = ap.parse_args()

    raw = json.loads(args.input.read_text(encoding="utf-8"))

    events = []
    for a in raw.get("ascents", []):
        events.append({
            "is_ascent": True,
            "climb": a.get("climb", ""),
            "angle": a.get("angle", ""),
            "date": a.get("climbed_at", ""),
            "tries": parse_tries(a.get("attempts")),
            "grade": normalize_grade(a.get("grade", "")),
            "comment": clean(a.get("comment", "")),
        })
    for b in raw.get("attempts", []):
        events.append({
            "is_ascent": False,
            "climb": b.get("climb", ""),
            "angle": b.get("angle", ""),
            "date": b.get("climbed_at", ""),
            "tries": int(b.get("count", 1) or 1),
            "grade": "",
            "comment": clean(b.get("comment", "")),
        })

    events.sort(key=lambda e: e["date"])

    session_days = {}     # climb -> set of YYYY-MM-DD
    cum_tries = {}        # climb -> running sum of tries
    sent_before = set()   # climbs successfully ascended at least once

    rows = []
    for e in events:
        climb = e["climb"]
        day = e["date"][:10]
        session_days.setdefault(climb, set()).add(day)
        cum_tries[climb] = cum_tries.get(climb, 0) + e["tries"]
        is_repeat = climb in sent_before
        if e["is_ascent"]:
            sent_before.add(climb)
        rows.append({
            "board": args.board,
            "angle": e["angle"],
            "climb_name": climb,
            "date": e["date"],
            "logged_grade": e["grade"],
            "displayed_grade": e["grade"],
            "is_benchmark": "False",
            "tries": e["tries"],
            "is_mirror": "False",
            "sessions_count": len(session_days[climb]),
            "tries_total": cum_tries[climb],
            "is_repeat": "True" if is_repeat else "False",
            "is_ascent": "True" if e["is_ascent"] else "False",
            "comment": e["comment"],
        })

    fields = ["board", "angle", "climb_name", "date", "logged_grade",
              "displayed_grade", "is_benchmark", "tries", "is_mirror",
              "sessions_count", "tries_total", "is_repeat", "is_ascent",
              "comment"]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()
