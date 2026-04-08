#!/usr/bin/env python3

import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
INPUT_2022 = ROOT / "2022-first-pass-inventory.csv"
INPUT_2023 = ROOT / "2023-first-pass-inventory.csv"
OUTPUT_2022 = ROOT / "2022-enriched-inventory.csv"
OUTPUT_2023 = ROOT / "2023-cleaned-enriched-inventory.csv"
OUTPUT_CROSSWALK = ROOT / "2022-2023-crosswalk.csv"
OUTPUT_MEMO = ROOT / "analysis-update.txt"

HEADERISH_2023 = {
    "THE NEW YORK HOUSING COMPACT",
    "FOR MENTAL HEALTH",
    "SYSTEM FOR NEW YORK’S FUTURE",
    "AND ENVIRONMENTAL FUTURE",
    "WITH THE COST OF LIVING",
    "EDUCATION",
    "NEW YORK STATE BUSINESSES",
    "AGRICULTURAL SECTOR",
    "EQUITABLE CHILD CARE SYSTEM",
    "TRANSPORTATION SAFETY, EQUITY, AND EFFICIENCY",
    "GOVERNMENT: THE CUSTOMER EXPERIENCE",
}

TITLE_FIXES_2023 = {
    "Create Greater Opportunities toConvert Office Spaces to Residential Housing": "Create Greater Opportunities to Convert Office Spaces to Residential Housing",
    "IncreaseOperationalCapacityforInpatient Psychiatric Treatment By 1,000 Beds": "Increase Operational Capacity for Inpatient Psychiatric Treatment by 1,000 Beds",
    "Create 3,500 New HousingUnits for Individuals with Mental Illness": "Create 3,500 New Housing Units for Individuals with Mental Illness",
    "Expand the Medicaid Buy-in Program for New Yorkers withDisabilities": "Expand the Medicaid Buy-In Program for New Yorkers with Disabilities",
    "Strengthen New York’s Public Health Emergency ReadinessCapacity": "Strengthen New York’s Public Health Emergency Readiness Capacity",
    "Meet New York’s Climate Goals with a “Cap-and- Invest” Program That Prioritizes Affordability": "Meet New York’s Climate Goals with a \"Cap-and-Invest\" Program That Prioritizes Affordability",
    "MatchFederal Technology Innovation Funding": "Match Federal Technology Innovation Funding",
    "Support “Scratch” Cooking Facilities forSchool Food": "Support \"Scratch\" Cooking Facilities for School Food",
    "Reinvigorate the Interagency Coordinating Council forServices to Persons whoare Deaf, Deafblind, or Hard of Hearing": "Reinvigorate the Interagency Coordinating Council for Services to Persons Who Are Deaf, Deafblind, or Hard of Hearing",
    "SpurTransportation Innovation Upstate": "Spur Transportation Innovation Upstate",
    "Clean Up “Forever Chemicals": "Clean Up \"Forever Chemicals\"",
}

AGENCY_FIXES = {
    "Department of Health": "DOH",
    "Department of Transportation": "DOT",
    "Department of Labor": "DOL",
    "Department of Environmental Conservation": "DEC",
    "Homes and Community Renewal": "HCR",
    "State Education Department": "SED",
}

THEME_RULES = [
    ("aging_master_plan", ["master plan for aging"]),
    ("aging_long_term_care", ["aging services", "long-term care", "older new yorkers", "age with dignity", "aging"]),
    ("transit_oriented_housing", ["near transit", "transit-oriented"]),
    ("office_conversion", ["office spaces to residential", "office conversion", "hotel conversion", "offices to residential"]),
    ("basement_apartments", ["basement apartments"]),
    ("mental_health_supportive_housing", ["mental illness", "supportive housing"]),
    ("housing_supply", ["housing compact", "home construction", "build and rehabilitate housing", "new housing", "residential capacity"]),
    ("tenant_protection", ["tenant protection"]),
    ("housing_planning_governance", ["housing planning office", "statewide database to promote transparency", "planning and infrastructure needs", "remove obstacles to housing approvals"]),
    ("lead_remediation_housing", ["lead poisoning", "lead remediation"]),
    ("mental_health_youth", ["school-aged children", "youth mental health"]),
    ("mental_health_insurance", ["mental health services", "insurance coverage for mental health"]),
    ("psychiatric_capacity", ["psychiatric treatment", "inpatient psychiatric", "beds"]),
    ("alternatives_reentry", ["alternatives to incarceration", "reentry"]),
    ("gun_violence", ["gun violence", "gun involved violence", "violent crime"]),
    ("state_police_capacity", ["state police", "academy classes", "prosecutors", "task forces"]),
    ("discovery_bail", ["discovery reform", "bail laws"]),
    ("cyber_emergency_response", ["cyber", "fire service", "emergency response"]),
    ("health_system_planning", ["commission on the future of health care", "health care technology capital program"]),
    ("health_care_capital", ["health care capital", "wadsworth laboratories"]),
    ("health_care_workforce_regulation", ["traveling nurse", "approval processes of health care projects", "allow health care providers to do more"]),
    ("medicaid_coverage", ["medicaid", "essential plan"]),
    ("primary_care_and_ems", ["primary care", "emergency medical services", "medical transportation"]),
    ("opioid_response", ["opioid"]),
    ("public_health_readiness", ["public health emergency readiness", "health reporting systems"]),
    ("cap_and_invest", ["cap-and-invest"]),
    ("energy_affordability", ["energy more affordable", "just energy transition"]),
    ("building_decarbonization", ["buildings more sustainable", "building emissions", "energy-independent"]),
    ("transport_electrification", ["transportation electrification", "ev charging", "school buses"]),
    ("recycling_waste", ["recycling", "waste", "toxics in packaging"]),
    ("water_quality", ["water quality", "clean water"]),
    ("minimum_wage", ["minimum wage"]),
    ("public_education_funding", ["public education", "prekindergarten", "foundation aid"]),
    ("tutoring_learning_loss", ["tutoring", "learning loss"]),
    ("college_workforce_pathways", ["early college", "p-tech", "community colleges", "high school-college-workforce", "suny"]),
    ("semiconductor_economic_development", ["semiconductor"]),
    ("technology_innovation_economic_development", ["technology innovation", "cell and gene therapy", "supply chain resiliency"]),
    ("food_access_agriculture", ["food access", "urban agriculture", "school food", "agriculture"]),
    ("reproductive_rights", ["reproductive", "abortion", "contraception", "equal rights amendment"]),
    ("disability_inclusion", ["disabilities", "deaf", "deafblind", "hard of hearing"]),
    ("immigrant_support", ["new americans", "refugee", "immigrants"]),
    ("older_lgbtq_housing", ["older lgbtq"]),
    ("veterans_services", ["veterans", "military cultural competency"]),
    ("child_care_access", ["child care"]),
    ("mta_service_and_finance", ["mta", "city ticket", "interborough express"]),
    ("street_safety", ["speed limit", "high risk drivers", "dangerous vehicles", "secondary crashes", "dwi"]),
    ("digital_government", ["customer experience", "benefits participation", "e-signature", "one id", "call wait times", "digital and design teams"]),
]

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "our", "new", "york",
    "state", "with", "all", "that", "through", "into", "from", "by", "at", "as", "up",
    "make", "create", "establish", "launch", "expand", "improve", "support", "provide",
    "increase", "ensure", "build", "develop", "advance", "protect", "continue", "allow",
}

BINARY_PREFIXES = {
    "establish": "established",
    "create": "created",
    "launch": "launched",
    "authorize": "authorized",
    "allow": "authorized",
    "adopt": "adopted",
    "designate": "designated",
    "enact": "enacted",
    "issue": "issued",
    "reinvigorate": "reinvigorated",
    "directly admit": "implemented",
}

MANUAL_MATCHES = {
    "Ensure Access to Aging Services and High-Quality Long-Term Care": {
        "prior_title": "Establish a State Master Plan for Aging",
        "relation": "follow_on",
        "basis": "manual override: 2023 text explicitly references the statewide Master Plan for Aging launched in 2022",
    },
}


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text or "").strip()


def clean_2023_rows(rows):
    cleaned = []
    dropped = []
    for row in rows:
        title = normalize_whitespace(row["proposal_title"])
        if not row["section_bucket"]:
            dropped.append((title, "foreword/empty section"))
            continue
        if title in HEADERISH_2023:
            dropped.append((title, "section header"))
            continue
        if title == "deliver care":
            dropped.append((title, "wrapped subsection fragment"))
            continue
        row = dict(row)
        row["proposal_title"] = TITLE_FIXES_2023.get(title, title)
        row["subsection"] = normalize_whitespace(row["subsection"])
        if row["subsection"] == "Part IV-A: Transform how we pay for and":
            row["subsection"] = "Part IV-A: Transform how we pay for and deliver care"
        cleaned.append(row)
    return cleaned, dropped


def standardize_agencies(value):
    agencies = []
    for part in (value or "").split(";"):
        name = normalize_whitespace(part)
        if not name:
            continue
        agencies.append(AGENCY_FIXES.get(name, name))
    return "; ".join(agencies)


def infer_item_type(row):
    current = row["commitment_type"]
    title = row["proposal_title"].lower()
    if current == "other":
        if any(token in title for token in ["double ", "triple ", "increase ", "expand "]):
            return "program/policy"
        if any(token in title for token in ["secure the mta", "take high risk drivers off the road", "protect new yorkers from predatory banking fees"]):
            return "program/policy"
    return current


def infer_pathway(row):
    title = row["proposal_title"].lower()
    item_type = row["item_type_clean"]
    if item_type == "legislation/regulation":
        return "legislation_required"
    if any(token in title for token in ["tax credit", "funding", "grant", "capital", "investment", "reimbursement", "$"]):
        return "executive_budget"
    if any(token in title for token in ["establish", "create", "launch", "reinvigorate", "streamline and centralize", "simplify"]):
        return "executive_action"
    if any(token in title for token in ["authorize", "allow new york city", "enact", "index the minimum wage", "close the dwi loophole"]):
        return "legislation_required"
    return row["implementation_pathway"]


def infer_binary(title):
    lowered = title.lower()
    for prefix, unit in BINARY_PREFIXES.items():
        if lowered.startswith(prefix):
            return "yes", unit
    if any(lowered.startswith(prefix) for prefix in ["streamline", "simplify", "modernize", "protect", "expand", "improve", "increase", "reduce", "support", "secure", "strengthen"]):
        return "no", ""
    if any(token in lowered for token in ["master plan", "commission", "office of", "database", "program", "navigator", "one id"]):
        return "mixed", "implemented"
    return "no", ""


def infer_theme(row):
    title = row["proposal_title"].lower()
    subsection = row["subsection"].lower()
    joined = f"{title} {subsection}"
    for theme, needles in THEME_RULES:
        if any(needle in joined for needle in needles):
            return theme

    section = row["section_bucket"]
    fallback = {
        "Housing / homelessness": "housing_general",
        "Mental health": "mental_health_general",
        "Public safety / justice": "public_safety_general",
        "Public safety / gun violence": "public_safety_general",
        "Health care": "health_care_general",
        "Climate / energy / environment": "climate_general",
        "Labor / affordability": "labor_affordability_general",
        "Schools / higher education": "education_general",
        "Economic development / business": "economic_development_general",
        "Agriculture / food systems": "agriculture_general",
        "Equity / inclusion / social policy": "equity_general",
        "Equity / inclusion / veterans / immigrants": "equity_general",
        "Government / democracy": "government_general",
        "Transportation / infrastructure": "transportation_general",
        "Government operations / customer experience": "government_operations_general",
    }
    return fallback.get(section, "unclear")


def infer_status_evidence(row):
    title = row["proposal_title"].lower()
    item_type = row["item_type_clean"]
    binary = row["binary_evaluable"]
    if binary == "yes":
        if item_type == "legislation/regulation":
            return "statute, enacted bill, or chapter law"
        if row["implementation_pathway_clean"] == "executive_budget":
            return "budget appropriation or program line"
        return "executive order, agency launch, or official announcement"
    if any(token in title for token in ["funding", "grant", "investment", "tax credit", "reimbursement"]):
        return "budget appropriation, program awards, or fiscal documents"
    if any(token in title for token in ["expand", "improve", "increase", "reduce", "support", "strengthen"]):
        return "implementation metrics, agency reports, or budget plus rollout evidence"
    return "agency report or official implementation evidence"


def tokenize(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def choose_best_match(row_2023, rows_2022):
    theme = row_2023["overlap_theme"]
    related_themes = {
        "aging_long_term_care": {"aging_long_term_care", "aging_master_plan"},
        "office_conversion": {"office_conversion", "housing_general"},
        "housing_planning_governance": {"housing_planning_governance", "housing_general"},
        "mental_health_supportive_housing": {"mental_health_supportive_housing", "housing_supply"},
    }
    candidates = [
        r for r in rows_2022 if r["overlap_theme"] in related_themes.get(theme, {theme})
    ]
    if not candidates:
        section_pairs = {
            "Housing / homelessness": {"Housing / homelessness", "Communities / infrastructure / economic development"},
            "Mental health": {"Mental health", "Health care"},
            "Public safety / justice": {"Public safety / justice", "Public safety / gun violence", "People / workforce / reentry / food systems"},
            "Health care": {"Health care"},
            "Climate / energy / environment": {"Climate / energy / environment"},
            "Labor / affordability": {"People / workforce / reentry / food systems"},
            "Schools / higher education": {"Schools / higher education"},
            "Economic development / business": {"Communities / infrastructure / economic development", "People / workforce / reentry / food systems"},
            "Agriculture / food systems": {"People / workforce / reentry / food systems"},
            "Equity / inclusion / social policy": {"Equity / inclusion / veterans / immigrants", "Health care", "Housing / homelessness"},
            "Government / democracy": {"Government reform", "People / workforce / reentry / food systems"},
            "Transportation / infrastructure": {"Communities / infrastructure / economic development", "Climate / energy / environment"},
            "Government operations / customer experience": {"Government reform", "People / workforce / reentry / food systems"},
        }
        candidates = [
            r for r in rows_2022 if r["section_bucket"] in section_pairs.get(row_2023["section_bucket"], set())
        ]

    title_tokens = tokenize(row_2023["proposal_title"])
    best = None
    best_score = 0.0
    for candidate in candidates:
        candidate_tokens = tokenize(candidate["proposal_title"])
        if not candidate_tokens:
            continue
        score = len(title_tokens & candidate_tokens) / len(title_tokens | candidate_tokens)
        if candidate["overlap_theme"] == theme:
            score += 0.35
        if row_2023["lead_agency_standardized"] and row_2023["lead_agency_standardized"] == candidate["lead_agency_standardized"]:
            score += 0.15
        if score > best_score:
            best = candidate
            best_score = score

    shared = tokenize(best["proposal_title"]) & title_tokens if best else set()
    exact_or_related = best and best["overlap_theme"] in related_themes.get(theme, {theme})
    if best_score < 0.45 and not (exact_or_related and shared and best_score >= 0.35):
        return None, "", ""

    relation = "continuation"
    lowered = row_2023["proposal_title"].lower()
    if any(token in lowered for token in ["double ", "triple ", "increase ", "expand ", "provide $", "250 million"]):
        relation = "expansion"
    elif any(token in lowered for token in ["ensure access", "improve ", "modernize ", "secure the mta", "move forward"]):
        relation = "follow_on"

    basis = f"theme={theme}; shared_terms={', '.join(sorted(tokenize(best['proposal_title']) & title_tokens)[:6])}"
    return best, relation, basis


def enrich_rows(rows, year):
    enriched = []
    for index, row in enumerate(rows, start=1):
        out = dict(row)
        out["commitment_id"] = f"{year}-{index:03d}"
        out["proposal_title"] = normalize_whitespace(out["proposal_title"])
        out["lead_agency_standardized"] = standardize_agencies(out["lead_agency"])
        out["supporting_agencies_standardized"] = standardize_agencies(out["supporting_agencies"])
        out["item_type_clean"] = infer_item_type(out)
        out["implementation_pathway_clean"] = infer_pathway(out)
        out["binary_evaluable"], out["binary_unit"] = infer_binary(out["proposal_title"])
        out["overlap_theme"] = infer_theme(out)
        out["status_evidence_needed"] = infer_status_evidence(out)
        out["source_quality"] = "cleaned_toc_pass" if year == "2023" else "first_pass_toc"
        out["continuity_to_prior_year"] = ""
        out["matched_prior_commitment_id"] = ""
        out["matched_prior_title"] = ""
        out["match_basis"] = ""
        enriched.append(out)
    return enriched


def write_csv(path, rows):
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_crosswalk(path, rows_2023):
    fieldnames = [
        "commitment_id_2023",
        "proposal_title_2023",
        "overlap_theme",
        "continuity_to_prior_year",
        "matched_commitment_id_2022",
        "matched_title_2022",
        "match_basis",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_2023:
            writer.writerow(
                {
                    "commitment_id_2023": row["commitment_id"],
                    "proposal_title_2023": row["proposal_title"],
                    "overlap_theme": row["overlap_theme"],
                    "continuity_to_prior_year": row["continuity_to_prior_year"],
                    "matched_commitment_id_2022": row["matched_prior_commitment_id"],
                    "matched_title_2022": row["matched_prior_title"],
                    "match_basis": row["match_basis"],
                }
            )


def write_memo(path, dropped_rows, rows_2022, rows_2023):
    relation_counts = defaultdict(int)
    binary_counts = defaultdict(int)
    for row in rows_2023:
        relation_counts[row["continuity_to_prior_year"] or "blank"] += 1
        binary_counts[row["binary_evaluable"]] += 1

    lines = [
        "Analysis update",
        "",
        "Outputs created:",
        f"- {OUTPUT_2022.name}",
        f"- {OUTPUT_2023.name}",
        f"- {OUTPUT_CROSSWALK.name}",
        "",
        "2023 cleanup summary:",
        f"- Started from {len(read_csv(INPUT_2023))} rows.",
        f"- Dropped {len(dropped_rows)} obvious non-commitment rows.",
        f"- Cleaned output now has {len(rows_2023)} rows.",
        "",
        "Rows dropped from 2023:",
    ]
    for title, reason in dropped_rows:
        lines.append(f"- {title} [{reason}]")

    lines.extend(
        [
            "",
            "2023 binary evaluability:",
            f"- yes: {binary_counts['yes']}",
            f"- mixed: {binary_counts['mixed']}",
            f"- no: {binary_counts['no']}",
            "",
            "2023 continuity to 2022:",
            f"- continuation: {relation_counts['continuation']}",
            f"- expansion: {relation_counts['expansion']}",
            f"- follow_on: {relation_counts['follow_on']}",
            f"- new: {relation_counts['new']}",
            "",
            "Important caution:",
            "- The continuity crosswalk is a structured first pass based on theme and title overlap.",
            "- It is useful for review and triage, but some rows will still need manual confirmation.",
        ]
    )

    path.write_text("\n".join(lines) + "\n")


def main():
    rows_2022 = read_csv(INPUT_2022)
    rows_2023_raw = read_csv(INPUT_2023)
    rows_2023, dropped_rows = clean_2023_rows(rows_2023_raw)

    enriched_2022 = enrich_rows(rows_2022, "2022")
    enriched_2023 = enrich_rows(rows_2023, "2023")
    title_to_2022 = {row["proposal_title"]: row for row in enriched_2022}

    by_theme_2022 = defaultdict(list)
    for row in enriched_2022:
        by_theme_2022[row["overlap_theme"]].append(row)

    for row in enriched_2023:
        manual = MANUAL_MATCHES.get(row["proposal_title"])
        if manual:
            match = title_to_2022.get(manual["prior_title"])
            if match:
                row["continuity_to_prior_year"] = manual["relation"]
                row["matched_prior_commitment_id"] = match["commitment_id"]
                row["matched_prior_title"] = match["proposal_title"]
                row["match_basis"] = manual["basis"]
                continue
        match, relation, basis = choose_best_match(row, enriched_2022)
        if match is None:
            row["continuity_to_prior_year"] = "new"
            continue
        row["continuity_to_prior_year"] = relation
        row["matched_prior_commitment_id"] = match["commitment_id"]
        row["matched_prior_title"] = match["proposal_title"]
        row["match_basis"] = basis

    write_csv(OUTPUT_2022, enriched_2022)
    write_csv(OUTPUT_2023, enriched_2023)
    write_crosswalk(OUTPUT_CROSSWALK, enriched_2023)
    write_memo(OUTPUT_MEMO, dropped_rows, enriched_2022, enriched_2023)

    print(f"Wrote {OUTPUT_2022.name}, {OUTPUT_2023.name}, {OUTPUT_CROSSWALK.name}, and {OUTPUT_MEMO.name}")


if __name__ == "__main__":
    main()
