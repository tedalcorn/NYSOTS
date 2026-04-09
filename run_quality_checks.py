#!/usr/bin/env python3

import csv
import json
import re
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
SITE_DATA = ROOT / "site" / "data" / "site-data.json"
HEADER_AUDIT = ROOT / "header-audit.csv"
AGENCY_AUDIT = ROOT / "agency-plausibility-flags.csv"
LOW_TEXT_AUDIT = ROOT / "low-text-audit.csv"

ACTION_PREFIXES = (
    "create",
    "expand",
    "increase",
    "improve",
    "protect",
    "reduce",
    "provide",
    "establish",
    "launch",
    "support",
    "fund",
    "build",
    "develop",
    "modernize",
    "reform",
    "invest",
    "promote",
    "strengthen",
    "advance",
    "secure",
    "allow",
    "pass",
    "implement",
    "combat",
    "open",
    "double",
    "triple",
    "deliver",
    "ensure",
)

AGENCY_KEYWORDS = {
    "DMV": ["dmv", "driver's license", "drivers license", "vehicle", "moped", "road test", "traffic safety", "registration", "drugged driving", "dwi"],
    "DFS": ["insurance", "insurer", "premium", "bank", "banking", "loan", "financial", "fraud", "pharmacy benefit manager", "pbm"],
    "HCR": ["housing", "tenant", "rent", "homeless", "shelter", "homeownership", "starter home", "basement apartment", "office conversion", "rebuild homes", "disaster recovery", "resiliency"],
    "OCFS": ["child care", "children", "family", "youth", "foster", "child welfare", "early childhood"],
    "DOH": ["health", "medicaid", "hospital", "medical", "public health", "care", "patient", "vital records", "aging", "women, infants and children", "wic", "contraception", "pharmacist"],
    "DEC": ["water", "parks", "environment", "flood", "dam", "pfas", "lake", "drinking water", "conservation", "recycling", "circular economy"],
    "DOT": ["transportation", "transit", "road", "bridge", "highway", "rail", "bike", "pedestrian", "subway", "commute", "route", "expressway", "skyway", "corridor", "interchange"],
    "Empire State Development": ["economic development", "small business", "downtown", "manufacturing", "innovation", "startup", "mwbe", "site", "semiconductor", "arts", "business"],
}


def load_commitments():
    return json.loads(SITE_DATA.read_text())["commitments"]


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def is_header_like(commitment):
    title = commitment["title"]
    normalized_title = normalize(title)
    text = normalize(commitment.get("commitment_text", ""))
    subgoals = commitment.get("subgoals") or []
    reasons = []

    word_count = len(title.split())
    action_like = normalized_title.startswith(ACTION_PREFIXES)
    has_future_action = any(token in text for token in ["governor hochul will", "new york will", "the state will", "she will", "governor hochul is launching", "governor hochul is proposing"])

    if word_count <= 2:
        reasons.append("very_short_title")
    if not text:
        reasons.append("no_body_text")
    if word_count <= 4 and not action_like:
        reasons.append("short_non_action_title")
    if commitment.get("text_capture_confidence") == "medium":
        reasons.append("medium_text_match")
    if not subgoals and not has_future_action:
        reasons.append("no_detected_commitment_language")

    return reasons


def agency_mismatch_reasons(commitment):
    text = normalize(" ".join([commitment["title"], commitment.get("commitment_text", ""), " ".join(commitment.get("theme_labels", []))]))
    reasons = []
    for agency in commitment.get("all_agencies", []):
        keywords = AGENCY_KEYWORDS.get(agency)
        if not keywords:
            continue
        if not any(keyword in text for keyword in keywords):
            reasons.append(f"{agency}:no_keyword_overlap")
    return reasons


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    commitments = load_commitments()

    header_rows = []
    agency_rows = []
    low_text_rows = []

    for commitment in commitments:
        header_reasons = is_header_like(commitment)
        if header_reasons:
            header_rows.append(
                {
                    "id": commitment["id"],
                    "year": commitment["year"],
                    "title": commitment["title"],
                    "lead_agencies": "; ".join(commitment.get("lead_agencies", [])),
                    "text_capture_confidence": commitment.get("text_capture_confidence", ""),
                    "subgoal_count": len(commitment.get("subgoals") or []),
                    "reasons": "; ".join(header_reasons),
                }
            )

        agency_reasons = agency_mismatch_reasons(commitment)
        if agency_reasons:
            agency_rows.append(
                {
                    "id": commitment["id"],
                    "year": commitment["year"],
                    "title": commitment["title"],
                    "lead_agencies": "; ".join(commitment.get("lead_agencies", [])),
                    "supporting_agencies": "; ".join(commitment.get("supporting_agencies", [])),
                    "reasons": "; ".join(agency_reasons),
                }
            )

        word_count = len((commitment.get("commitment_text") or "").split())
        if word_count <= 40:
            low_text_rows.append(
                {
                    "id": commitment["id"],
                    "year": commitment["year"],
                    "title": commitment["title"],
                    "word_count": word_count,
                    "text_capture_confidence": commitment.get("text_capture_confidence", ""),
                    "lead_agencies": "; ".join(commitment.get("lead_agencies", [])),
                    "supporting_agencies": "; ".join(commitment.get("supporting_agencies", [])),
                    "subgoal_count": len(commitment.get("subgoals") or []),
                }
            )

    write_csv(
        HEADER_AUDIT,
        header_rows,
        ["id", "year", "title", "lead_agencies", "text_capture_confidence", "subgoal_count", "reasons"],
    )
    write_csv(
        AGENCY_AUDIT,
        agency_rows,
        ["id", "year", "title", "lead_agencies", "supporting_agencies", "reasons"],
    )
    write_csv(
        LOW_TEXT_AUDIT,
        low_text_rows,
        ["id", "year", "title", "word_count", "text_capture_confidence", "lead_agencies", "supporting_agencies", "subgoal_count"],
    )
    print(f"Wrote {HEADER_AUDIT.name}, {AGENCY_AUDIT.name}, and {LOW_TEXT_AUDIT.name}")


if __name__ == "__main__":
    main()
