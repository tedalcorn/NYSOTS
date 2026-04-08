#!/usr/bin/env python3

import csv
from pathlib import Path

import build_analysis_outputs as bao


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
FILES = {
    "2022": ROOT / "2022-enriched-inventory.csv",
    "2023": ROOT / "2023-cleaned-enriched-inventory.csv",
    "2024": ROOT / "2024-cleaned-enriched-inventory.csv",
    "2025": ROOT / "2025-cleaned-enriched-inventory.csv",
    "2026": ROOT / "2026-cleaned-enriched-inventory.csv",
}


def read_rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    enriched_by_year = {}
    title_maps = {}

    for year, path in FILES.items():
        rows = read_rows(path)
        for row in rows:
            bao.infer_agencies_with_text(row)
            row["overlap_theme"] = bao.infer_theme(row)
            override = bao.MANUAL_ROW_OVERRIDES.get(row["proposal_title"])
            if override:
                if "lead_agency" in override:
                    row["lead_agency"] = override["lead_agency"]
                    row["lead_agency_standardized"] = bao.standardize_agencies(row["lead_agency"])
                if "supporting_agencies" in override:
                    row["supporting_agencies"] = override["supporting_agencies"]
                    row["supporting_agencies_standardized"] = bao.standardize_agencies(row["supporting_agencies"])
                if "overlap_theme" in override:
                    row["overlap_theme"] = override["overlap_theme"]
        enriched_by_year[year] = rows
        title_maps[year] = {row["proposal_title"]: row for row in rows}

    ordered_years = sorted(enriched_by_year)
    for year in ordered_years:
        for row in enriched_by_year[year]:
            row["continuity_to_prior_year"] = ""
            row["matched_prior_commitment_id"] = ""
            row["matched_prior_title"] = ""
            row["match_basis"] = ""

    for year in ordered_years[1:]:
        prior_year = str(int(year) - 1)
        for row in enriched_by_year[year]:
            manual = bao.MANUAL_MATCHES.get(row["proposal_title"])
            if manual:
                match = title_maps[prior_year].get(manual["prior_title"])
                if match:
                    row["continuity_to_prior_year"] = manual["relation"]
                    row["matched_prior_commitment_id"] = match["commitment_id"]
                    row["matched_prior_title"] = match["proposal_title"]
                    row["match_basis"] = manual["basis"]
                    continue
            match, relation, basis = bao.choose_best_match(row, enriched_by_year[prior_year])
            if match is None:
                row["continuity_to_prior_year"] = "new"
                continue
            row["continuity_to_prior_year"] = relation
            row["matched_prior_commitment_id"] = match["commitment_id"]
            row["matched_prior_title"] = match["proposal_title"]
            row["match_basis"] = basis

    for year, rows in enriched_by_year.items():
        bao.write_csv(FILES[year], rows)
    for year in ordered_years[1:]:
        crosswalk_path = ROOT / f"{int(year)-1}-{year}-crosswalk.csv"
        bao.write_crosswalk(crosswalk_path, enriched_by_year[year])

    print("Re-ran agency/theme inference using commitment text")


if __name__ == "__main__":
    main()
