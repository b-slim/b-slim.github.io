#!/usr/bin/env python3
"""Convert logbook.csv to logbook.json for the GitHub Pages site."""
import csv
import json
import sys
from pathlib import Path

def main():
    csv_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logbook.csv")
    json_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("logbook.json")

    rows = []
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"), ensure_ascii=False)

    print(f"Wrote {len(rows)} rows → {json_path}")

if __name__ == "__main__":
    main()
