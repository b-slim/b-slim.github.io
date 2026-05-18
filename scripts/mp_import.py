#!/usr/bin/env python3
"""Fetch a Mountain Project user's tick export and emit mountainproject.json
for the outdoor section of the logbook.

The tick-export endpoint at
  https://www.mountainproject.com/user/<MP_USER_ID>/<slug>/tick-export
returns the full tick list as CSV with no authentication required, as long
as the profile is public. The slug is informational; MP only honors the
numeric user ID.

Usage:
  MP_USER_ID=107837713 python3 scripts/mp_import.py mountainproject.json
  python3 scripts/mp_import.py --input some_ticks.csv mountainproject.json
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


TICK_URL = "https://www.mountainproject.com/user/{uid}/{slug}/tick-export"
USER_AGENT = "Mozilla/5.0 (b-slim logbook sync)"


def fetch_csv(user_id: str, slug: str = "x") -> str:
    url = TICK_URL.format(uid=user_id, slug=slug)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        ctype = resp.headers.get("Content-Type", "")
        if "csv" not in ctype.lower():
            raise RuntimeError(f"Expected CSV, got Content-Type={ctype!r} from {url}")
        return resp.read().decode("utf-8")


def parse_v_grade(rating):
    """Map an MP boulder rating string to a base integer V-grade.

    Examples: 'V0' -> 0, 'V-easy' -> 0, 'V8+' -> 8, 'V2-3' -> 2,
    'V8+ PG13' -> 8, 'V7-' -> 7. Returns None if unparseable.
    """
    if not rating:
        return None
    s = rating.strip()
    if s.lower().startswith("v-easy"):
        return 0
    m = re.match(r"^[Vv](\d+)", s)
    if m:
        return int(m.group(1))
    return None


def is_ascent(style: str) -> bool:
    return (style or "").strip().lower() != "attempt"


def to_row(r: dict) -> dict:
    your_stars_raw = r.get("Your Stars", "").strip()
    try:
        your_stars = float(your_stars_raw)
        if your_stars < 0:
            your_stars = None
    except ValueError:
        your_stars = None
    try:
        avg_stars = float(r.get("Avg Stars", "").strip())
    except ValueError:
        avg_stars = None
    rating = r.get("Rating", "").strip()
    return {
        "board": "mountain-project",
        "climb_name": r.get("Route", "").strip(),
        "date": r.get("Date", "").strip(),
        "logged_grade": rating,
        "grade_v": parse_v_grade(rating),
        "is_ascent": is_ascent(r.get("Style", "")),
        "style": r.get("Style", "").strip(),
        "location": r.get("Location", "").strip(),
        "url": r.get("URL", "").strip(),
        "avg_stars": avg_stars,
        "your_stars": your_stars,
        "comment": (r.get("Notes") or "").replace("\r", " ").strip(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path, help="path to write mountainproject.json")
    ap.add_argument("--input", type=Path,
                    help="local CSV path (skip fetch; useful for testing)")
    ap.add_argument("--user-id", default=os.environ.get("MP_USER_ID"),
                    help="MP user id (default: $MP_USER_ID)")
    ap.add_argument("--slug", default=os.environ.get("MP_USER_SLUG", "x"),
                    help="MP profile slug (default: $MP_USER_SLUG or 'x')")
    args = ap.parse_args()

    if args.input:
        csv_text = args.input.read_text(encoding="utf-8")
    else:
        if not args.user_id:
            print("error: provide --user-id or set MP_USER_ID", file=sys.stderr)
            return 2
        try:
            csv_text = fetch_csv(args.user_id, args.slug)
        except urllib.error.HTTPError as e:
            print(f"error: MP returned HTTP {e.code} for user {args.user_id} — "
                  f"is the profile public?", file=sys.stderr)
            return 1

    reader = csv.DictReader(io.StringIO(csv_text))
    boulders = [r for r in reader if r.get("Route Type", "").strip() == "Boulder"]
    rows = [to_row(r) for r in boulders]
    rows.sort(key=lambda x: x["date"])

    args.output.write_text(
        json.dumps(rows, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )
    sends = sum(1 for r in rows if r["is_ascent"])
    print(f"Wrote {len(rows)} boulder ticks "
          f"({sends} sends, {len(rows)-sends} attempts) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
