#!/usr/bin/env python3

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
SOURCE_ROOT = Path("/Users/tedalcorn/Documents/*Resumes/ -Job Applications/2026 01 Hochul Policy Shop/-SOTS")


YEAR_CONFIGS = {
    "2024": {
        "source_pdf": SOURCE_ROOT / "2024-SOTS-Book-Online.pdf",
        "output_csv": ROOT / "2024-first-pass-inventory.csv",
        "toc_start": 8,
        "toc_end": 14,
        "heading_mode": "section",
        "section_map": {
            "SECTION 1: TACKLING THE MENTAL HEALTH CRISIS": "Mental health",
            "SECTION 2: KEEPING NEW YORKERS SAFE": "Public safety / justice",
            "SECTION 3: PROTECTING CONSUMERS AND THEIR POCKETBOOKS": "Labor / affordability",
            "SECTION 4: LEADING ON INNOVATION": "Economic development / business",
            "SECTION 5: CREATING HOUSING TO DELIVER AFFORDABILITY": "Housing / homelessness",
            "SECTION 6: IMPROVING MATERNAL AND INFANT MATERNAL HEALTH": "Health care",
            "SECTION 7: GETTING BACK TO BASICS ON READING": "Schools / higher education",
            "SECTION 8: EXTENDING OPPORTUNITY TO OUR STUDENTS": "Schools / higher education",
            "SECTION 9: STRENGTHENING SERVICE AND CIVIC ENGAGEMENT": "Government / democracy",
            "SECTION 10: EXPAND SWIMMING ACCESS AND SAFETY": "Parks / recreation",
            "SECTION 11: PROTECTING NEW YORKERS FROM EXTREME WEATHER": "Climate / energy / environment",
            "SECTION 12: ACHIEVING A MORE SUSTAINABLE FUTURE": "Climate / energy / environment",
            "SECTION 13: MAKING NEW YORK A GREAT PLACE TO WORK AND DO BUSINESS": "Economic development / business",
            "SECTION 14: IMPROVING THE HEALTH OF NEW YORKERS": "Health care",
            "SECTION 15: ADVANCING EQUITY AND WELLBEING": "Equity / inclusion / social policy",
            "SECTION 16: MAKING GOVERNMENT WORK BETTER": "Government operations / customer experience",
            "SECTION 17: GROWING NEW OPPORTUNITIES FOR AGRICULTURE": "Agriculture / food systems",
            "SECTION 18: FIGHTING CYBER CRIME": "Government operations / customer experience",
            "SECTION 19: BUILDING OUR TRANSPORTATION FUTURE": "Transportation / infrastructure",
        },
    },
    "2025": {
        "source_pdf": SOURCE_ROOT / "2025StateoftheStateBook.pdf",
        "output_csv": ROOT / "2025-first-pass-inventory.csv",
        "toc_start": 5,
        "toc_end": 12,
        "heading_mode": "chapter",
        "section_map": {
            "Chapter 1: Putting Money Back in New Yorkers’ Pockets": "Labor / affordability",
            "Chapter 2: Supporting the Youngest New Yorkers and their Families": "Equity / inclusion / social policy",
            "Chapter 3: Helping Our Children Thrive": "Schools / higher education",
            "Chapter 4: Investing in Safety": "Public safety / justice",
            "Chapter 5: Bringing Jobs to New York": "Economic development / business",
            "Chapter 6: Building an Economy that Works for All": "Labor / affordability",
            "Chapter 7: Making Government Work Better": "Government operations / customer experience",
            "Chapter 8: Growing Housing to Drive Affordability": "Housing / homelessness",
            "Chapter 9: Cutting Commutes": "Transportation / infrastructure",
            "Chapter 10: Protecting Consumers": "Labor / affordability",
            "Chapter 11: Supporting Survivors of Sexual Assault, Gender-Based Violence, and Sex Trafficking": "Equity / inclusion / social policy",
            "Chapter 12: Investing in Mental Health": "Mental health",
            "Chapter 13: Investing in Health": "Health care",
            "Chapter 14: Investing in Social Services and Equity": "Equity / inclusion / social policy",
            "Chapter 15: Building a Sustainable Future": "Climate / energy / environment",
        },
    },
    "2026": {
        "source_pdf": SOURCE_ROOT / "2026StateoftheStateBook.pdf",
        "output_csv": ROOT / "2026-first-pass-inventory.csv",
        "toc_start": 6,
        "toc_end": 16,
        "heading_mode": "chapter",
        "section_map": {
            "Chapter 1: Making New York More Affordable": "Labor / affordability",
            "Chapter 2: Keeping New Yorkers Safe": "Public safety / justice",
            "Chapter 3: Investing in Critical Infrastructure New Yorkers Need": "Communities / infrastructure",
            "Chapter 4: Cutting Red Tape to Better Serve New Yorkers": "Government operations / customer experience",
            "Chapter 5: Protecting New York’s Consumers and Workers": "Labor / affordability",
            "Chapter 6: Driving Innovation and Economic Development by and for New Yorkers": "Economic development / business",
            "Chapter 7: Helping New York’s Students Learn and Thrive": "Schools / higher education",
            "Chapter 8: Keeping New Yorkers Healthy": "Health care",
            "Chapter 9: Securing New York’s Energy Future": "Climate / energy / environment",
            "Chapter 10: Protecting New York’s Environment": "Climate / energy / environment",
            "Chapter 11: Building Resilient Communities for New Yorkers": "Equity / inclusion / social policy",
        },
    },
}


NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "twenty", "twenty-five",
    "thirty", "forty", "fifty", "hundred", "thousand", "million", "billion", "percent",
    "double", "triple",
}


def normalize_line(line):
    return " ".join(line.split()).replace("\u2019", "'").strip()


def is_heading(line, mode):
    if mode == "section":
        return line.startswith("SECTION ")
    return line.startswith("Chapter ")


def clean_heading(line):
    return re.sub(r"\.{2,}\s*\d+\s*$", "", line).strip()


def extract_rows(config):
    text = subprocess.check_output(
        [
            "pdftotext",
            "-f",
            str(config["toc_start"]),
            "-l",
            str(config["toc_end"]),
            "-raw",
            str(config["source_pdf"]),
            "-",
        ],
        text=True,
        errors="ignore",
    )

    rows = []
    section = None
    current_lines = []
    page_re = re.compile(r"(.*?)(?:\.{2,}|\s)(\d+)\s*$")

    for raw in text.splitlines():
        line = normalize_line(raw)
        if not line:
            continue
        if line in {"TABLE OF CONTENTS", "Table of Contents", "FOREWORD", "Foreword"}:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if line.startswith(config["source_pdf"].stem.replace(".pdf", "")):
            continue
        if line.lower().startswith(("governor kathy hochul", "january 2024", "january 2025", "january 2026")):
            continue

        if is_heading(line, config["heading_mode"]):
            if current_lines and section:
                rows.append((section, " ".join(current_lines).strip()))
                current_lines = []
            section = clean_heading(line)
            continue

        match = page_re.match(line)
        if match:
            title = match.group(1).strip()
            if current_lines:
                title = " ".join(current_lines + [title]).strip()
                current_lines = []
            rows.append((section, title))
            continue

        current_lines.append(line)

    return rows


def detect_quantified(title):
    lowered = title.lower().replace("%", " percent ")
    if re.search(r"\d", title):
        return "yes"
    if NUMBER_WORDS & set(lowered.split()):
        return "yes"
    return "no"


def metric_from_title(title):
    patterns = [
        r"\$[\d\.,]+\s*(?:million|billion)",
        r"\d[\d,\.]*\s*(?:beds|teachers|trees|units|sites|families|percent|million|billion|year|years)",
        r"\b(?:double|triple)\b",
        r"\bup to \d[\d,\.]*\b",
        r"\b\d{4}\b",
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
    if any(token in lowered for token in ["require ", "prohibit ", "mandate ", "reform ", "modernize ", "update ", "ban ", "outlaw ", "protecting elections"]):
        return "legislation/regulation"
    if any(token in lowered for token in ["create ", "establish ", "launch ", "convene ", "appoint ", "pilot "]):
        return "program/governance"
    if any(token in lowered for token in ["fund ", "invest ", "tax credit", "rebate", "reimburse", "incentive", "grant", "refund", "payment", "subsid"]):
        return "funding/tax/benefit"
    if any(token in lowered for token in ["build ", "repair ", "expand ", "improve ", "support ", "strengthen ", "deliver ", "protect ", "accelerat", "increase "]):
        return "program/policy"
    return "other"


def infer_agencies(section_bucket, title):
    lowered = title.lower()
    lead = []
    support = []

    def add(values, item):
        if item and item not in values:
            values.append(item)

    if "housing" in lowered or section_bucket == "Housing / homelessness":
        add(lead, "HCR")
        if "transit" in lowered or "subway" in lowered:
            add(support, "DOT")
            add(support, "MTA")
        if "basement" in lowered or "new york city" in lowered:
            add(support, "New York City")
        if "supportive housing" in lowered or "mental illness" in lowered:
            add(support, "OMH")
    elif section_bucket == "Mental health":
        add(lead, "OMH")
        if "insurance" in lowered:
            add(support, "DFS")
        if "youth" in lowered or "school" in lowered:
            add(support, "SED")
    elif section_bucket == "Health care":
        add(lead, "DOH")
        if "opioid" in lowered or "buprenorphine" in lowered:
            lead[:] = ["OASAS"]
        if "older" in lowered or "age in place" in lowered:
            add(support, "NYS Office for the Aging")
    elif section_bucket == "Public safety / justice":
        if any(token in lowered for token in ["state police", "police", "crime labs"]):
            add(lead, "New York State Police")
        else:
            add(lead, "DCJS")
        if any(token in lowered for token in ["subway", "commutes", "speed assistance", "bike lanes", "roads"]):
            add(support, "DOT")
            add(support, "MTA")
    elif section_bucket == "Labor / affordability":
        if any(token in lowered for token in ["tax", "rebate", "refund"]):
            add(lead, "Department of Taxation and Finance")
        elif any(token in lowered for token in ["child care", "summer meal", "food", "snap", "ebt"]):
            add(lead, "OCFS")
            add(support, "OTDA")
        else:
            add(lead, "DOL")
    elif section_bucket == "Schools / higher education":
        if "suny" in lowered:
            add(lead, "SUNY")
        elif "cuny" in lowered:
            add(lead, "CUNY")
        else:
            add(lead, "SED")
        if "mental health" in lowered:
            add(support, "OMH")
    elif section_bucket == "Economic development / business":
        if "farm" in lowered or "dairy" in lowered or "hemp" in lowered:
            add(lead, "Agriculture & Markets")
        else:
            add(lead, "Empire State Development")
        if "workforce" in lowered or "apprenticeship" in lowered:
            add(support, "DOL")
    elif section_bucket == "Government operations / customer experience":
        if "cyber" in lowered or "digital" in lowered or "design system" in lowered:
            add(lead, "Office of Information Technology Services")
        elif "civil service" in lowered or "state workforce" in lowered:
            add(lead, "Department of Civil Service")
        else:
            add(lead, "Executive Chamber / cross-agency")
    elif section_bucket == "Transportation / infrastructure":
        add(lead, "DOT")
        if any(token in lowered for token in ["subway", "mta", "jamaica station", "interborough"]):
            add(support, "MTA")
    elif section_bucket == "Climate / energy / environment":
        if any(token in lowered for token in ["water", "flood", "dam", "coastal", "resilien", "parks", "farmland", "open space"]):
            add(lead, "DEC")
        else:
            add(lead, "NYSERDA")
    elif section_bucket == "Agriculture / food systems":
        add(lead, "Agriculture & Markets")
    elif section_bucket == "Parks / recreation":
        add(lead, "Office of Parks, Recreation and Historic Preservation")
        if "suny" in lowered:
            add(support, "SUNY")
    elif section_bucket == "Equity / inclusion / social policy":
        if any(token in lowered for token in ["veteran"]):
            add(lead, "Department of Veterans' Services")
        elif any(token in lowered for token in ["disabilities", "asl", "deaf"]):
            add(lead, "Office for People With Developmental Disabilities")
        elif any(token in lowered for token in ["sexual assault", "gender-based violence", "trafficking"]):
            add(lead, "Office for the Prevention of Domestic Violence")
        else:
            add(lead, "Executive Chamber / cross-agency")
    elif section_bucket == "Government / democracy":
        add(lead, "Executive Chamber / cross-agency")
    elif section_bucket == "Communities / infrastructure":
        if "housing" in lowered:
            add(lead, "HCR")
        elif "water" in lowered or "park" in lowered:
            add(lead, "DEC")
        else:
            add(lead, "DOT")

    return "; ".join(lead), "; ".join(support)


def implementation_pathway(title, kind):
    lowered = title.lower()
    if kind == "legislation/regulation":
        return "legislation_required"
    if any(token in lowered for token in ["fund ", "invest ", "grant", "tax ", "rebate", "refund", "payment", "subsid"]):
        return "executive_budget"
    return "mixed"


def generate_year(year, config):
    rows = extract_rows(config)
    with config["output_csv"].open("w", newline="") as handle:
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
        for section, title in rows:
            bucket = config["section_map"].get(section, section)
            lead, support = infer_agencies(bucket, title)
            kind = commitment_type(title)
            writer.writerow(
                [
                    year,
                    config["source_pdf"].name,
                    bucket,
                    section,
                    title,
                    lead,
                    support,
                    kind,
                    detect_quantified(title),
                    metric_from_title(title),
                    implementation_pathway(title, kind),
                    f"First-pass coding from {year} SOTS table of contents.",
                ]
            )
    print(f"{year}: wrote {len(rows)} rows to {config['output_csv'].name}")


def main():
    for year, config in YEAR_CONFIGS.items():
        generate_year(year, config)


if __name__ == "__main__":
    main()
