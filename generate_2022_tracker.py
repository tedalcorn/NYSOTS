#!/usr/bin/env python3

import csv
import re
import subprocess
from pathlib import Path


SOURCE_PDF = Path(
    "/Users/tedalcorn/Documents/*Resumes/ -Job Applications/2026 01 Hochul Policy Shop/-SOTS/2022StateoftheStateBook.pdf"
)
OUTPUT_CSV = Path(
    "/Users/tedalcorn/Desktop/codex-projects/NYSOTS/2022-first-pass-inventory.csv"
)


SECTION_MAP = {
    "SECTION I: REBUILD OUR HEALTHCARE ECONOMY TO PROVIDE CARE FOR": "Health care",
    "SECTION II: PROTECT PUBLIC SAFETY AND TAKE STRONG ACTION AGAINST": "Public safety / gun violence",
    "SECTION III: INVEST IN NEW YORK’S PEOPLE": "People / workforce / reentry / food systems",
    "SECTION IV: INVEST IN NEW YORK’S COMMUNITIES": "Communities / infrastructure / economic development",
    "SECTION V: MAKE NEW YORK’S HOUSING SYSTEM MORE AFFORDABLE, EQUITABLE,": "Housing / homelessness",
    "SECTION VI: MAKE NEW YORK A NATIONAL LEADER IN CLIMATE ACTION AND": "Climate / energy / environment",
    "SECTION VII: REBUILD NEW YORK’S SCHOOL SYSTEM AND REIMAGINE HIGHER": "Schools / higher education",
    "SECTION VIII: ADVANCE NEW YORK’S PLACE AS A NATIONAL EQUITY MODEL": "Equity / inclusion / veterans / immigrants",
    "SECTION IX: MAKE CRITICAL REFORMS TO RESTORE NEW YORKERS’ FAITH IN": "Government reform",
}

NUMBER_WORDS = {
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
    "hundred",
    "thousand",
    "million",
    "billion",
    "percent",
    "double",
    "triple",
}


def extract_rows():
    text = subprocess.check_output(
        ["pdftotext", "-f", "11", "-l", "19", "-layout", str(SOURCE_PDF), "-"],
        text=True,
        errors="ignore",
    )

    rows = []
    section = None
    part = None
    current = None

    for line in text.splitlines():
        collapsed = " ".join(line.split())
        if not collapsed or collapsed == "2022 STATE OF THE STATE":
            continue

        if collapsed.startswith("SECTION "):
            if current:
                rows.append((section, part, current.strip()))
                current = None
            section = re.sub(r"\.{2,}.*$", "", collapsed).strip()
            continue

        if collapsed.startswith("Part "):
            if current:
                rows.append((section, part, current.strip()))
                current = None
            part = re.sub(r"\.{2,}.*$", "", collapsed).strip()
            continue

        if collapsed.startswith("•"):
            if current:
                rows.append((section, part, current.strip()))
            current = re.sub(r"\.{2,}\s*\d+\s*$", "", collapsed[1:].strip()).strip()
            continue

        if current and not re.match(r"^(TABLE OF CONTENTS|FOREWORD|END NOTES|\d+)$", collapsed):
            cont = re.sub(r"\.{2,}\s*\d+\s*$", "", collapsed).strip()
            if cont and cont != "2022 STATE OF THE STATE":
                current += " " + cont

    if current:
        rows.append((section, part, current.strip()))

    cleaned = []
    for section, part, title in rows:
        title = title.replace(" 2022 STATE OF THE STATE", "").strip()
        cleaned.append((SECTION_MAP.get(section, section), part or "", title))
    return cleaned


def detect_quantified(title):
    tokens = set(title.lower().replace("%", " percent ").split())
    if re.search(r"\d", title):
        return "yes"
    if NUMBER_WORDS & tokens:
        return "yes"
    return "no"


def metric_from_title(title):
    patterns = [
        r"\$[\d\.,]+\s*(?:million|billion)",
        r"\d[\d,\.]*\s*(?:percent|families|students|businesses|workers|homes|units|gigawatts|schools|years?)",
        r"\b(?:double|triple)\b",
        r"by\s+20\d{2}",
        r"no later than\s+20\d{2}",
        r"at least\s+\d[\d,\.]*\s*\w+",
        r"\b100%\b",
        r"\bone-third\b",
        r"\btwo-term\b",
    ]
    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, title, flags=re.IGNORECASE):
            value = match.group(0)
            if value not in matches:
                matches.append(value)
    return "; ".join(matches)


def commitment_type(title):
    lowered = title.lower()
    if any(token in lowered for token in ["pass ", "enact ", "authorize ", "ban ", "require ", "codify "]):
        return "legislation/regulation"
    if any(token in lowered for token in ["create ", "establish ", "launch ", "pilot ", "develop ", "designate "]):
        return "program/governance"
    if any(
        token in lowered
        for token in [
            "invest ",
            "fund ",
            "provide $",
            "deliver $",
            "increase funding",
            "make a $",
            "tax credit",
            "tax cuts",
            "rebate",
            "support wages",
        ]
    ):
        return "funding/tax/benefit"
    if any(
        token in lowered
        for token in [
            "build ",
            "replace ",
            "modernize ",
            "reconstructing ",
            "reimagine ",
            "complete ",
            "weatherize",
            "electrify",
        ]
    ):
        return "capital/infrastructure"
    if any(
        token in lowered
        for token in [
            "recruit ",
            "hire ",
            "training ",
            "workforce ",
            "teacher residency",
            "apprenticeships",
            "staff the parole board",
        ]
    ):
        return "staffing/workforce"
    if any(
        token in lowered
        for token in [
            "protect ",
            "strengthen ",
            "stop ",
            "combat ",
            "improve ",
            "expand ",
            "promote ",
            "facilitate ",
            "overhaul ",
            "refocus ",
            "ease restrictions",
        ]
    ):
        return "program/policy"
    return "other"


def infer_agencies(section_bucket, title):
    lowered = title.lower()
    lead = []
    support = []

    def add(values, item):
        if item and item not in values:
            values.append(item)

    if section_bucket == "Health care":
        if any(token in lowered for token in ["opioid", "addiction", "recovery housing"]):
            add(lead, "OASAS")
        elif any(token in lowered for token in ["mental health", "suicide", "gender-based violence"]):
            add(lead, "OMH")
        else:
            add(lead, "DOH")
        if "insurers" in lowered:
            add(support, "DFS")
        if any(token in lowered for token in ["aging", "seniors", "ombudsman"]):
            add(support, "NYS Office for the Aging")
        if "suny" in lowered:
            add(support, "SUNY")
        if "cuny" in lowered:
            add(support, "CUNY")
        if "immigrant" in lowered:
            add(support, "ONA")

    elif section_bucket == "Public safety / gun violence":
        if any(token in lowered for token in ["state police", "gun-tracing", "red flag", "law enforcement"]):
            add(lead, "New York State Police")
        else:
            add(lead, "DCJS")
        add(support, "Local law enforcement")
        if any(token in lowered for token in ["forensic", "cryptocurrency", "social media analysis"]):
            add(support, "Division of Homeland Security and Emergency Services")

    elif section_bucket == "People / workforce / reentry / food systems":
        if any(token in lowered for token in ["farm", "food", "nourish", "hemp", "agribusiness", "urban farms", "snap"]):
            add(lead, "Agriculture & Markets")
            add(support, "OTDA")
        elif any(token in lowered for token in ["tax cuts", "property tax rebate", "tax credits"]):
            add(lead, "Department of Taxation and Finance")
        elif any(token in lowered for token in ["parole", "in-prison", "re-entry", "clean slate", "supervision fees", "incarcerated"]):
            add(lead, "DOCCS")
        elif any(token in lowered for token in ["id cards", "vital records"]):
            add(lead, "DMV")
        elif any(token in lowered for token in ["transcript", "loan forgiveness", "student debt"]):
            add(lead, "Higher Education Services Corporation")
        else:
            add(lead, "Department of Labor")
        if "suny" in lowered:
            add(support, "SUNY")
        if "cuny" in lowered:
            add(support, "CUNY")
        if any(token in lowered for token in ["small businesses", "technology talent"]):
            add(support, "Empire State Development")

    elif section_bucket == "Communities / infrastructure / economic development":
        if any(
            token in lowered
            for token in ["lirr", "railroad bridge", "route 17", "roads and bridges", "interchange", "expressway", "merge", "skyway"]
        ):
            add(lead, "Department of Transportation")
        elif any(token in lowered for token in ["venture competitions", "north country", "adirondacks", "economic"]):
            add(lead, "Empire State Development")
        else:
            add(lead, "Department of Transportation")
        if "orda" in lowered:
            add(support, "Olympic Regional Development Authority")

    elif section_bucket == "Housing / homelessness":
        add(lead, "Homes and Community Renewal")
        if any(token in lowered for token in ["supportive housing", "street homelessness", "homelessness"]):
            add(support, "OMH")
            add(support, "OTDA")
        if "transit-oriented" in lowered:
            add(support, "Department of Transportation")
            add(support, "MTA")
        if "new york city" in lowered:
            add(support, "New York City")

    elif section_bucket == "Climate / energy / environment":
        if any(token in lowered for token in ["clean water", "air monitoring", "extreme heat", "brownfield", "recycling", "toxics", "water resources", "forest preserve"]):
            add(lead, "Department of Environmental Conservation")
        else:
            add(lead, "NYSERDA")
        add(support, "Public Service Commission / DPS")
        if any(token in lowered for token in ["school buses", "state fleet"]):
            add(support, "Office of General Services")
            add(support, "Department of Transportation")
        if "schools" in lowered:
            add(support, "State Education Department")
        if any(token in lowered for token in ["clean water", "air"]):
            add(support, "Environmental Facilities Corporation")

    elif section_bucket == "Schools / higher education":
        if any(token in lowered for token in ["suny"]):
            add(lead, "SUNY")
        elif any(token in lowered for token in ["cuny"]):
            add(lead, "CUNY")
        elif any(token in lowered for token in ["tuition assistance", "financial aid"]):
            add(lead, "Higher Education Services Corporation")
        else:
            add(lead, "State Education Department")
        if "suny" in lowered:
            add(support, "SUNY")
        if "cuny" in lowered:
            add(support, "CUNY")
        if "childcare" in lowered:
            add(support, "OCFS")

    elif section_bucket == "Equity / inclusion / veterans / immigrants":
        if any(token in lowered for token in ["mwbe"]):
            add(lead, "Empire State Development")
        elif any(token in lowered for token in ["office for new americans", "immigrant"]):
            add(lead, "Office for New Americans")
        elif any(token in lowered for token in ["veterans", "military-to-civilian"]):
            add(lead, "Department of Veterans’ Services")
        elif any(token in lowered for token in ["anti-discrimination", "reproductive", "equal rights", "hate and bias", "lgbtqia+", "gender “x”", "language access"]):
            add(lead, "Division of Human Rights")
        else:
            add(lead, "Executive Chamber / cross-agency")
        if any(token in lowered for token in ["correctional facilities", "gender-affirming treatment"]):
            add(support, "DOCCS")
        if "language access" in lowered:
            add(support, "Office of General Services / cross-agency")

    elif section_bucket == "Government reform":
        add(lead, "Executive Chamber / Legislature")
        if any(token in lowered for token in ["jcope", "ethics"]):
            add(support, "State ethics bodies")
        if any(token in lowered for token in ["voting", "registration", "polling"]):
            add(support, "State Board of Elections")

    return "; ".join(lead), "; ".join(support)


def implementation_pathway(title, kind):
    lowered = title.lower()
    if kind == "legislation/regulation":
        return "legislation_required"
    if any(token in lowered for token in ["tax cuts", "tax credit", "rebate", "fully funding", "invest ", "fund "]):
        return "executive_budget"
    return "mixed"


def main():
    rows = extract_rows()
    with OUTPUT_CSV.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "year",
                "source_document",
                "section_bucket",
                "subsection",
                "proposal_title",
                "lead_agency",
                "supporting_agencies",
                "commitment_type",
                "quantified",
                "metric_or_target",
                "implementation_pathway",
                "notes",
            ]
        )
        for section_bucket, subsection, title in rows:
            kind = commitment_type(title)
            lead, support = infer_agencies(section_bucket, title)
            writer.writerow(
                [
                    "2022",
                    SOURCE_PDF.name,
                    section_bucket,
                    subsection,
                    title,
                    lead,
                    support,
                    kind,
                    detect_quantified(title),
                    metric_from_title(title),
                    implementation_pathway(title, kind),
                    "First-pass coding from 2022 SOTS table of contents.",
                ]
            )

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
