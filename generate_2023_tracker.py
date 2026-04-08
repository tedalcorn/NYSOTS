#!/usr/bin/env python3

import csv
import re
import subprocess
from pathlib import Path


SOURCE_PDF = Path(
    "/Users/tedalcorn/Documents/*Resumes/ -Job Applications/2026 01 Hochul Policy Shop/-SOTS/2023SOTSBook.pdf"
)
OUTPUT_CSV = Path(
    "/Users/tedalcorn/Desktop/codex-projects/NYSOTS/2023-first-pass-inventory.csv"
)


SECTION_MAP = {
    "SECTION I: BUILDING 800,000 NEW HOMES:": "Housing / homelessness",
    "SECTION II: FIXING THE CONTINUUM OF CARE": "Mental health",
    "SECTION III: KEEPING NEW YORKERS SAFE": "Public safety / justice",
    "SECTION IV: BUILDING A HEALTH CARE": "Health care",
    "SECTION V: SAFEGUARDING OUR CLIMATE": "Climate / energy / environment",
    "SECTION VI: HELPING WORKERS KEEP UP": "Labor / affordability",
    "SECTION VII: PROVIDING HIGH-QUALITY": "Schools / higher education",
    "SECTION VIII: ATTRACTING AND GROWING": "Economic development / business",
    "SECTION IX: GROWING NEW YORK’S": "Agriculture / food systems",
    "SECTION X: LIFTING UP ALL NEW YORKERS": "Equity / inclusion / social policy",
    "SECTION XI: BUILDING A STRONG,": "Government / democracy",
    "SECTION XII: PRIORITIZING": "Transportation / infrastructure",
    "SECTION XIII: IMPROVING STATE": "Government operations / customer experience",
    "SECTION XIV: IMPROVING STATE": "Government workforce / operations",
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
        ["pdftotext", "-f", "12", "-l", "20", "-raw", str(SOURCE_PDF), "-"],
        text=True,
        errors="ignore",
    )

    rows = []
    section = None
    part = None
    current_lines = []

    for line in text.splitlines():
        collapsed = " ".join(line.split()).replace("STATE OFTHE STATE", "STATE OF THE STATE")
        if not collapsed or collapsed == "2023 STATE OF THE STATE":
            continue

        if re.fullmatch(r"\d+", collapsed):
            continue

        if collapsed.startswith("SECTION "):
            if current_lines:
                rows.append((section, part, " ".join(current_lines).strip()))
                current_lines = []
            section = re.sub(r"\.{2,}\s*\d+$", "", collapsed).strip()
            continue

        if collapsed.startswith("Part "):
            if current_lines:
                rows.append((section, part, " ".join(current_lines).strip()))
                current_lines = []
            part = re.sub(r"\.{2,}\s*\d+$", "", collapsed).strip()
            continue

        if collapsed in {"TABLE OF CONTENTS", "FOREWORD"}:
            continue

        if re.search(r"\.{2,}\s*\d+$", collapsed):
            item = re.sub(r"\.{2,}\s*\d+$", "", collapsed).strip()
            if current_lines:
                current_lines.append(item)
                rows.append((section, part, " ".join(current_lines).strip()))
                current_lines = []
            else:
                rows.append((section, part, item))
            continue

        current_lines.append(collapsed)

    if current_lines:
        rows.append((section, part, " ".join(current_lines).strip()))

    cleaned = []
    for section, part, title in rows:
        title = title.replace(" 2023 STATE OF THE STATE", "").strip()
        title = re.sub(r"\s+", " ", title).strip()
        if title in {"January 2023", "FOREWORD"}:
            continue
        bucket = None
        for prefix, mapped in SECTION_MAP.items():
            if (section or "").startswith(prefix):
                bucket = mapped
                break
        cleaned.append((bucket or section, part or "", title))
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
        r"\d[\d,\.]*\s*(?:beds|homes|communities|years?|units|funding)",
        r"\b(?:double|triple)\b",
        r"by\s+20\d{2}",
        r"\b800,000\b",
        r"\b1,000 beds\b",
        r"\b3,500\b",
        r"\b25 communities\b",
        r"\bfour new\b",
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
    if any(token in lowered for token in ["pass ", "enact ", "authorize ", "safeguard ", "require ", "reform ", "modernize "]):
        return "legislation/regulation"
    if any(token in lowered for token in ["create ", "establish ", "launch ", "initiate ", "reinvigorate "]):
        return "program/governance"
    if any(token in lowered for token in ["invest ", "provide ", "funding", "matching fund", "tax credit", "reimbursement rates"]):
        return "funding/tax/benefit"
    if any(token in lowered for token in ["build ", "rebuild ", "expand ", "improve ", "support ", "advance ", "ensure "]):
        return "program/policy"
    return "other"


def infer_agencies(section_bucket, title):
    lowered = title.lower()
    lead = []
    support = []

    def add(values, item):
        if item and item not in values:
            values.append(item)

    if section_bucket == "Housing / homelessness":
        add(lead, "Homes and Community Renewal")
        if "transit" in lowered:
            add(support, "Department of Transportation")
            add(support, "MTA")
        if "child care" in lowered:
            add(support, "OCFS")
        if "new york city" in lowered:
            add(support, "New York City")

    elif section_bucket == "Mental health":
        add(lead, "OMH")
        if "insurance" in lowered:
            add(support, "DFS")
        if "housing" in lowered:
            add(support, "Homes and Community Renewal")

    elif section_bucket == "Public safety / justice":
        if any(token in lowered for token in ["state police", "academy classes", "nysp"]):
            add(lead, "New York State Police")
        elif any(token in lowered for token in ["reentry", "parole", "alternatives to incarceration"]):
            add(lead, "DOCCS")
            add(support, "DCJS")
        elif "prosecutors" in lowered:
            add(lead, "DCJS")
        else:
            add(lead, "DCJS")
        if any(token in lowered for token in ["cyber", "emergency response", "fire service"]):
            add(support, "Division of Homeland Security and Emergency Services")

    elif section_bucket == "Health care":
        if any(token in lowered for token in ["opioid addiction", "opioid"]):
            add(lead, "OASAS")
        else:
            add(lead, "DOH")
        if any(token in lowered for token in ["aging", "long-term care"]):
            add(support, "NYS Office for the Aging")

    elif section_bucket == "Climate / energy / environment":
        if any(token in lowered for token in ["water quality", "forever chemicals", "recycling", "parks"]):
            add(lead, "Department of Environmental Conservation")
        else:
            add(lead, "NYSERDA")
        add(support, "Public Service Commission / DPS")

    elif section_bucket == "Labor / affordability":
        add(lead, "Department of Labor")

    elif section_bucket == "Schools / higher education":
        if any(token in lowered for token in ["suny"]):
            add(lead, "SUNY")
        elif any(token in lowered for token in ["cuny"]):
            add(lead, "CUNY")
        else:
            add(lead, "State Education Department")
        if any(token in lowered for token in ["community colleges", "college", "high school-college-workforce"]):
            add(support, "SUNY")

    elif section_bucket == "Economic development / business":
        add(lead, "Empire State Development")
        if "training and employment" in lowered:
            add(support, "Department of Labor")

    elif section_bucket == "Agriculture / food systems":
        add(lead, "Agriculture & Markets")
        if "school food" in lowered:
            add(support, "State Education Department")

    elif section_bucket == "Equity / inclusion / social policy":
        if any(token in lowered for token in ["reproductive", "abortion", "contraception", "equal rights"]):
            add(lead, "Department of Health")
            add(support, "Division of Human Rights")
        elif any(token in lowered for token in ["gender-based violence"]):
            add(lead, "Office for the Prevention of Domestic Violence")
        elif any(token in lowered for token in ["disabilities", "deaf", "deafblind", "hard of hearing"]):
            add(lead, "Office for People With Developmental Disabilities")
        else:
            add(lead, "Executive Chamber / cross-agency")

    elif section_bucket == "Government / democracy":
        add(lead, "Executive Chamber / Legislature")

    elif section_bucket == "Transportation / infrastructure":
        add(lead, "Department of Transportation")
        if any(token in lowered for token in ["mta", "transit"]):
            add(support, "MTA")

    elif section_bucket == "Government operations / customer experience":
        add(lead, "Office of Information Technology Services")

    elif section_bucket == "Government workforce / operations":
        add(lead, "Department of Civil Service")

    return "; ".join(lead), "; ".join(support)


def implementation_pathway(title, kind):
    lowered = title.lower()
    if kind == "legislation/regulation":
        return "legislation_required"
    if any(token in lowered for token in ["provide ", "invest ", "funding", "tax credit", "reimbursement"]):
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
                    "2023",
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
                    "First-pass coding from 2023 SOTS table of contents.",
                ]
            )
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
