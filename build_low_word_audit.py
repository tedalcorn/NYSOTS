#!/usr/bin/env python3

import csv
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
INPUTS = [
    ROOT / "2022-enriched-inventory.csv",
    ROOT / "2023-cleaned-enriched-inventory.csv",
    ROOT / "2024-cleaned-enriched-inventory.csv",
    ROOT / "2025-cleaned-enriched-inventory.csv",
    ROOT / "2026-cleaned-enriched-inventory.csv",
]
OUTPUT = ROOT / "low-word-count-audit.csv"


def read_rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    rows_out = []
    for path in INPUTS:
        for row in read_rows(path):
            text = row.get("commitment_text", "") or ""
            word_count = len(text.split())
            if word_count < 20:
                rows_out.append(
                    {
                        "year": row["year"],
                        "commitment_id": row["commitment_id"],
                        "proposal_title": row["proposal_title"],
                        "word_count": word_count,
                        "source_page": row.get("source_page", ""),
                        "text_capture_confidence": row.get("text_capture_confidence", ""),
                        "commitment_text": text,
                    }
                )

    rows_out.sort(key=lambda row: (int(row["year"]), int(row["word_count"]), row["commitment_id"]))
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "year",
                "commitment_id",
                "proposal_title",
                "word_count",
                "source_page",
                "text_capture_confidence",
                "commitment_text",
            ],
        )
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"Wrote {OUTPUT.name} with {len(rows_out)} rows")


if __name__ == "__main__":
    main()
