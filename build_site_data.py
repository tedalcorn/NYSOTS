#!/usr/bin/env python3

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
SITE_ROOT = ROOT / "site"
DATA_DIR = SITE_ROOT / "data"

INPUTS = [
    ROOT / "2022-enriched-inventory.csv",
    ROOT / "2023-cleaned-enriched-inventory.csv",
    ROOT / "2024-cleaned-enriched-inventory.csv",
    ROOT / "2025-cleaned-enriched-inventory.csv",
    ROOT / "2026-cleaned-enriched-inventory.csv",
]

SOURCE_MAP = {
    "2022StateoftheStateBook.pdf": {
        "label": "2022 State of the State Book",
        "url": "https://www.governor.ny.gov/sites/default/files/2022-01/2022StateoftheStateBook.pdf",
        "landing_url": "https://www.governor.ny.gov/programs/2022-state-state",
    },
    "2023SOTSBook.pdf": {
        "label": "2023 State of the State Book",
        "url": "https://www.governor.ny.gov/sites/default/files/2023-01/2023SOTSBook.pdf",
        "landing_url": "https://www.governor.ny.gov/programs/2023-state-state",
    },
    "2024-SOTS-Book-Online.pdf": {
        "label": "2024 State of the State Book",
        "url": "https://www.governor.ny.gov/sites/default/files/2024-01/2024-SOTS-Book-Online.pdf",
        "landing_url": "https://www.governor.ny.gov/programs/2024-state-state",
    },
    "2025StateoftheStateBook.pdf": {
        "label": "2025 State of the State Book",
        "url": "https://www.governor.ny.gov/sites/default/files/2025-01/2025StateoftheStateBook.pdf",
        "landing_url": "https://www.governor.ny.gov/programs/2025-state-state",
    },
    "2026StateoftheStateBook.pdf": {
        "label": "2026 State of the State Book",
        "url": "https://www.governor.ny.gov/sites/default/files/2026-01/2026StateoftheStateBook.pdf",
        "landing_url": "https://www.governor.ny.gov/keywords/2026-state-state",
    },
}

THEME_LABELS = {
    "aging_master_plan": "Aging Master Plan",
    "aging_long_term_care": "Aging and Long-Term Care",
    "transit_oriented_housing": "Transit-Oriented Housing",
    "office_conversion": "Office and Hotel Conversion",
    "basement_apartments": "Basement Apartments",
    "mental_health_supportive_housing": "Mental Health Supportive Housing",
    "housing_supply": "Housing Supply",
    "tenant_protection": "Tenant Protection",
    "housing_planning_governance": "Housing Planning and Governance",
    "lead_remediation_housing": "Lead Remediation and Housing",
    "mental_health_youth": "Youth Mental Health",
    "mental_health_insurance": "Mental Health Insurance",
    "psychiatric_capacity": "Psychiatric Capacity",
    "alternatives_reentry": "Alternatives to Incarceration and Reentry",
    "gun_violence": "Gun Violence",
    "state_police_capacity": "State Police Capacity",
    "discovery_bail": "Discovery and Bail",
    "cyber_emergency_response": "Cyber and Emergency Response",
    "health_system_planning": "Health System Planning",
    "health_care_capital": "Health Care Capital",
    "health_care_workforce_regulation": "Health Care Workforce and Regulation",
    "medicaid_coverage": "Medicaid and Coverage",
    "primary_care_and_ems": "Primary Care and EMS",
    "opioid_response": "Opioid Response",
    "public_health_readiness": "Public Health Readiness",
    "cap_and_invest": "Cap-and-Invest",
    "energy_affordability": "Energy Affordability",
    "building_decarbonization": "Building Decarbonization",
    "transport_electrification": "Transportation Electrification",
    "recycling_waste": "Recycling and Waste",
    "water_quality": "Water Quality",
    "minimum_wage": "Minimum Wage",
    "public_education_funding": "Public Education Funding",
    "tutoring_learning_loss": "Tutoring and Learning Loss",
    "college_workforce_pathways": "College and Workforce Pathways",
    "semiconductor_economic_development": "Semiconductors",
    "technology_innovation_economic_development": "Technology and Innovation",
    "food_access_agriculture": "Food Access and Agriculture",
    "reproductive_rights": "Reproductive Rights",
    "disability_inclusion": "Disability Inclusion",
    "immigrant_support": "Immigrant Support",
    "older_lgbtq_housing": "Older LGBTQ+ Housing",
    "veterans_services": "Veterans Services",
    "child_care_access": "Child Care Access",
    "mta_service_and_finance": "MTA Service and Finance",
    "street_safety": "Street Safety",
    "digital_government": "Digital Government",
    "housing_general": "Housing",
    "mental_health_general": "Mental Health",
    "public_safety_general": "Public Safety",
    "health_care_general": "Health Care",
    "climate_general": "Climate and Environment",
    "labor_affordability_general": "Labor and Affordability",
    "education_general": "Education",
    "economic_development_general": "Economic Development",
    "agriculture_general": "Agriculture",
    "equity_general": "Equity and Inclusion",
    "government_general": "Government",
    "transportation_general": "Transportation",
    "government_operations_general": "Government Operations",
    "unclear": "Unclear",
}

UNKNOWN_AGENCY = "Not yet identified"


def split_multi(value):
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def read_rows():
    rows = []
    for path in INPUTS:
        with path.open(newline="") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def normalize_theme(theme):
    if theme == "unclear":
        return "Not yet identified"
    return THEME_LABELS.get(theme, theme.replace("_", " ").title())


def extract_subgoals(text):
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    pattern = re.compile(
        r"((?:Governor Hochul|New York State|The State|New York|OCFS|SED|SUNY|CUNY|DOH|OMH|DOL|DFS|DOT|DMV|DOCCS|NYSERDA|Empire State Development|The Governor|Blue Buffers)\s+(?:will|is proposing to|proposes to)\s+.*?[.!?])",
        flags=re.IGNORECASE,
    )
    seen = []
    for match in pattern.findall(cleaned):
        sentence = re.sub(r"\s+", " ", match).strip()
        sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
        if sentence not in seen:
            seen.append(sentence)
    if len(seen) < 8:
        follow_up_pattern = re.compile(
            r"((?:In its first year of operation|Initially|To launch the program|To improve|To address this|To bolster these efforts|To meet growing need)\b.*?[.!?])",
            flags=re.IGNORECASE,
        )
        for match in follow_up_pattern.findall(cleaned):
            sentence = re.sub(r"\s+", " ", match).strip()
            if sentence not in seen:
                seen.append(sentence)
    return seen[:8]


def build_commitment(row):
    year = int(row["year"])
    source = SOURCE_MAP.get(row["source_document"], {"label": row["source_document"], "url": "", "landing_url": ""})
    lead = split_multi(row["lead_agency_standardized"] or row["lead_agency"])
    supporting = split_multi(row["supporting_agencies_standardized"] or row["supporting_agencies"])
    agencies = []
    for agency in lead + supporting:
        if agency not in agencies:
            agencies.append(agency)

    theme_key = row.get("overlap_theme", "unclear") or "unclear"
    continuity = row.get("continuity_to_prior_year", "") if year > 2022 else ""
    progress_status = "not_assessed"
    progress_label = "Not yet assessed"

    return {
        "id": row["commitment_id"],
        "year": year,
        "title": row["proposal_title"],
        "commitment_text": row.get("commitment_text", ""),
        "text_capture_confidence": row.get("text_capture_confidence", ""),
        "subgoals": extract_subgoals(row.get("commitment_text", "")),
        "section_bucket": row["section_bucket"],
        "subsection": row["subsection"],
        "source_page": row.get("source_page", ""),
        "source_page_end": row.get("source_page_end", ""),
        "commitment_type": row.get("item_type_clean") or row.get("commitment_type"),
        "implementation_pathway": row.get("implementation_pathway_clean") or row.get("implementation_pathway"),
        "quantified": row["quantified"],
        "indicator": row["metric_or_target"],
        "metric_or_target": row["metric_or_target"],
        "binary_evaluable": row["binary_evaluable"],
        "binary_unit": row["binary_unit"],
        "lead_agencies": lead,
        "supporting_agencies": supporting,
        "all_agencies": agencies,
        "theme_keys": [theme_key],
        "theme_labels": [normalize_theme(theme_key)],
        "continuity_to_prior_year": continuity,
        "matched_prior_commitment_id": row.get("matched_prior_commitment_id", ""),
        "matched_prior_title": row.get("matched_prior_title", ""),
        "status_evidence_needed": row.get("status_evidence_needed", ""),
        "source_quality": row.get("source_quality", ""),
        "notes": row["notes"],
        "source": {
            "document": row["source_document"],
            "label": source["label"],
            "url": source["url"],
            "landing_url": source["landing_url"],
        },
        "progress": {
            "status": progress_status,
            "label": progress_label,
            "summary": "",
            "last_updated": "",
            "evidence_items": [],
        },
    }


def build_indexes(commitments):
    agency_index = defaultdict(lambda: {"id": "", "name": "", "commitment_ids": [], "years": Counter(), "themes": Counter(), "lead_count": 0, "support_count": 0})
    theme_index = defaultdict(lambda: {"id": "", "label": "", "commitment_ids": [], "years": Counter(), "agencies": Counter()})
    year_index = defaultdict(lambda: {"year": 0, "commitment_ids": [], "agencies": Counter(), "themes": Counter(), "types": Counter(), "quantified_yes": 0, "binary_yes": 0})

    for commitment in commitments:
        year = commitment["year"]
        year_info = year_index[year]
        year_info["year"] = year
        year_info["commitment_ids"].append(commitment["id"])
        year_info["types"][commitment["commitment_type"]] += 1
        if commitment["quantified"] == "yes":
            year_info["quantified_yes"] += 1
        if commitment["binary_evaluable"] == "yes":
            year_info["binary_yes"] += 1

        agencies_for_index = commitment["all_agencies"] or [UNKNOWN_AGENCY]

        for agency in agencies_for_index:
            agency_info = agency_index[agency]
            agency_info["id"] = agency.lower().replace(" ", "-").replace("/", "-").replace("&", "and")
            agency_info["name"] = agency
            agency_info["commitment_ids"].append(commitment["id"])
            agency_info["years"][year] += 1
            year_info["agencies"][agency] += 1
        for agency in commitment["lead_agencies"]:
            agency_index[agency]["lead_count"] += 1
        for agency in commitment["supporting_agencies"]:
            agency_index[agency]["support_count"] += 1

        for theme_key, theme_label in zip(commitment["theme_keys"], commitment["theme_labels"]):
            theme_info = theme_index[theme_key]
            theme_info["id"] = theme_key
            theme_info["label"] = theme_label
            theme_info["commitment_ids"].append(commitment["id"])
            theme_info["years"][year] += 1
            year_info["themes"][theme_label] += 1
            for agency in agencies_for_index:
                theme_info["agencies"][agency] += 1
                agency_index[agency]["themes"][theme_label] += 1

    agencies = []
    for agency in sorted(agency_index.values(), key=lambda item: (-len(item["commitment_ids"]), item["name"])):
        agencies.append(
            {
                "id": agency["id"],
                "name": agency["name"],
                "commitment_count": len(agency["commitment_ids"]),
                "lead_count": agency["lead_count"],
                "support_count": agency["support_count"],
                "years": dict(sorted(agency["years"].items())),
                "top_themes": [
                    {"label": label, "count": count}
                    for label, count in agency["themes"].most_common(6)
                ],
                "commitment_ids": agency["commitment_ids"],
            }
        )

    themes = []
    for theme in sorted(theme_index.values(), key=lambda item: (-len(item["commitment_ids"]), item["label"])):
        themes.append(
            {
                "id": theme["id"],
                "label": theme["label"],
                "commitment_count": len(theme["commitment_ids"]),
                "years": dict(sorted(theme["years"].items())),
                "top_agencies": [
                    {"name": name, "count": count}
                    for name, count in theme["agencies"].most_common(6)
                ],
                "commitment_ids": theme["commitment_ids"],
            }
        )

    years = []
    for year in sorted(year_index):
        info = year_index[year]
        total = len(info["commitment_ids"])
        years.append(
            {
                "year": year,
                "commitment_count": total,
                "quantified_share": round(info["quantified_yes"] / total, 3) if total else 0,
                "binary_share": round(info["binary_yes"] / total, 3) if total else 0,
                "top_agencies": [
                    {"name": name, "count": count}
                    for name, count in info["agencies"].most_common(6)
                ],
                "top_themes": [
                    {"label": label, "count": count}
                    for label, count in info["themes"].most_common(6)
                ],
                "types": dict(info["types"]),
                "commitment_ids": info["commitment_ids"],
            }
        )

    return agencies, themes, years


def build_analysis(commitments, agencies, themes, years):
    type_counts = Counter(item["commitment_type"] for item in commitments)
    pathway_counts = Counter(item["implementation_pathway"] for item in commitments)
    continuity_counts = Counter(item["continuity_to_prior_year"] or "base_year" for item in commitments)
    progress_counts = Counter(item["progress"]["status"] for item in commitments)

    return {
        "totals": {
            "commitments": len(commitments),
            "years": len(years),
            "agencies": len(agencies),
            "themes": len(themes),
        },
        "type_counts": dict(type_counts),
        "pathway_counts": dict(pathway_counts),
        "continuity_counts": dict(continuity_counts),
        "progress_counts": dict(progress_counts),
        "coded_shares": {
            "quantified_yes": round(sum(1 for item in commitments if item["quantified"] == "yes") / len(commitments), 3),
            "binary_yes": round(sum(1 for item in commitments if item["binary_evaluable"] == "yes") / len(commitments), 3),
        },
    }


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    commitments = [build_commitment(row) for row in read_rows()]
    commitments.sort(key=lambda item: (item["year"], item["title"]))

    agencies, themes, years = build_indexes(commitments)
    analysis = build_analysis(commitments, agencies, themes, years)

    payload = {
        "meta": {
            "title": "Hochul State of the State Tracker",
            "description": "First-pass tracker of commitments from Governor Hochul's State of the State books.",
            "years_covered": [year["year"] for year in years],
            "source_documents": list(SOURCE_MAP.values()),
            "generated_at_iso": datetime.now().astimezone().isoformat(timespec="seconds"),
            "generated_at_label": datetime.now().astimezone().strftime("%-m/%-d/%y %-I:%M%p").lower(),
        },
        "commitments": commitments,
        "agencies": agencies,
        "themes": themes,
        "years": years,
        "analysis": analysis,
    }

    (DATA_DIR / "site-data.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {(DATA_DIR / 'site-data.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
