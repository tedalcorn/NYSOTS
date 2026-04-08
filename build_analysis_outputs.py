#!/usr/bin/env python3

import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
INPUT_FILES = {
    "2022": ROOT / "2022-first-pass-inventory.csv",
    "2023": ROOT / "2023-first-pass-inventory.csv",
    "2024": ROOT / "2024-first-pass-inventory.csv",
    "2025": ROOT / "2025-first-pass-inventory.csv",
    "2026": ROOT / "2026-first-pass-inventory.csv",
}
OUTPUT_FILES = {
    "2022": ROOT / "2022-enriched-inventory.csv",
    "2023": ROOT / "2023-cleaned-enriched-inventory.csv",
    "2024": ROOT / "2024-cleaned-enriched-inventory.csv",
    "2025": ROOT / "2025-cleaned-enriched-inventory.csv",
    "2026": ROOT / "2026-cleaned-enriched-inventory.csv",
}
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

TITLE_FIXES_LATER = {
    "2024 State of the State Reduce Gun Violence Through a Public Health Approach": "Reduce Gun Violence Through a Public Health Approach",
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
    ("labor_affordability_general", ["inflation rebate", "inflation rebates", "inflation refund", "salt deduction", "federal tax relief", "child tax credit", "tips", "student loan refinancing", "student loans", "wage theft", "workers' compensation fraud"]),
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
    ("public_education_funding", ["public education", "prekindergarten", "foundation aid", "universal school meals", "school meals", "free breakfast and lunch"]),
    ("tutoring_learning_loss", ["tutoring", "learning loss"]),
    ("college_workforce_pathways", ["early college", "p-tech", "community colleges", "high school-college-workforce", "suny", "tuition assistance program", "tap eligibility", "state longitudinal data system", "education and workforce outcomes", "apprenticeships", "pre-apprenticeships", "high-demand occupations"]),
    ("semiconductor_economic_development", ["semiconductor"]),
    ("technology_innovation_economic_development", ["technology innovation", "cell and gene therapy", "supply chain resiliency", "artificial intelligence technical assistance", "artificial intelligence pipeline", "startups", "underrepresented startups"]),
    ("food_access_agriculture", ["food access", "urban agriculture", "school food", "agriculture", "food banks", "pantries", "snap", "summer meal", "maple industry", "dairy industry", "fiber production"]),
    ("reproductive_rights", ["reproductive", "abortion", "contraception", "equal rights amendment"]),
    ("disability_inclusion", ["disabilities", "deaf", "deafblind", "hard of hearing"]),
    ("immigrant_support", ["new americans", "refugee", "immigrants"]),
    ("older_lgbtq_housing", ["older lgbtq"]),
    ("veterans_services", ["veterans", "military cultural competency"]),
    ("child_care_access", ["child care", "early childhood", "child and dependent care tax credit", "early education", "playgrounds", "get offline get outside", "ny swims", "learn-to-swim", "child drowning", "books from dolly parton", "imagination library"]),
    ("mta_service_and_finance", ["mta", "city ticket", "interborough express", "subway", "platform edge barriers", "police on platforms"]),
    ("street_safety", ["speed limit", "high risk drivers", "dangerous vehicles", "secondary crashes", "dwi", "drugged driving", "bike lanes", "e-bikes", "crosswalks", "school intersections", "work zones", "motorcycle licensing"]),
    ("digital_government", ["customer experience", "benefits participation", "e-signature", "one id", "call wait times", "digital and design teams", "digital innovation", "smart technology", "ai-generated content", "private data", "elections from misleading or deceptive ai content"]),
    ("public_safety_general", ["law enforcement technology", "crime analysis centers", "crime labs", "police training academies", "mass violence events", "violent crime", "victim compensation", "orders of protection", "child victims of crime", "child advocacy centers", "first responders", "firefighters", "protective gear", "justice system", "community-led violence prevention"]),
    ("equity_general", ["sexual assault", "gender-based violence", "survivor-led victim assistance", "safe access to worship", "safe access to healthcare", "constitutional violations", "federal officers"]),
    ("tenant_protection", ["rent-regulated tenants", "rent-regulated housing", "home appraisal discrimination", "institutional investor", "security deposit protections", "algorithm-enabled rent price fixing", "captive insurance", "mitchell-lama", "elder financial exploitation"]),
    ("housing_supply", ["down payment assistance", "homebuyer tax incentive", "pro-housing", "mixed-income revolving loan fund", "low income housing credits", "historic tax credits", "vacant properties into housing", "land banks", "manufactured homes park", "let them build", "build housing we need", "underutilized sites"]),
    ("building_decarbonization", ["empower+", "weatherization assistance program", "energy efficiency", "upgrade homes", "utilities omnibus", "utility regulation", "ratepayers", "energy affordability program", "electric grid", "data centers", "interconnections", "utility shutoffs", "energy cost burden", "utility bills"]),
    ("climate_general", ["parks", "high falls state park", "niagara gorge", "world cup legacy investment fund", "community centers", "lead out"]),
    ("economic_development_general", ["local economic development", "downtown revitalization", "new york forward", "authorities budget office", "idas"]),
    ("government_operations_general", ["critical infrastructure projects", "faster decisions", "clear timelines", "environmental impact statements", "review timelines", "permitting processes", "permitting academy", "government work better", "outdated and burdensome regulations", "streamlining public procurement", "expediting major state infrastructure projects", "making every new yorker count"]),
    ("government_general", ["algorithmic price discrimination", "returns and refunds", "buy now pay later", "subscription cancellation", "subscription renewal", "overdraft", "non-sufficient funds fees", "energy service companies", "misleading discounts", "misleading discount", "illegal vape enforcement"]),
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

MANUAL_ROW_OVERRIDES = {
    "Reimagining Jamaica Station for the Millions of Commuters Who Depend on It": {
        "lead_agency": "DOT",
        "supporting_agencies": "MTA",
        "overlap_theme": "transportation_general",
    },
    "Invest in New York State's Recreation Infrastructure": {
        "lead_agency": "DEC",
        "supporting_agencies": "",
        "overlap_theme": "climate_general",
    },
    "Provide $100 Million of Relief for 195,000 Small Businesses": {
        "overlap_theme": "economic_development_general",
    },
    "Accelerate $1.2 Billion in Middle-Class Tax Cuts for 6 Million New Yorkers": {
        "overlap_theme": "labor_affordability_general",
    },
    "Deliver a $1 Billion Property Tax Rebate for More Than 2 Million New York Families": {
        "overlap_theme": "labor_affordability_general",
    },
    "Expand the State’s Technology Talent Pipeline": {
        "overlap_theme": "technology_innovation_economic_development",
    },
    "Refocus Parole Officers on Career Planning and Job Placement": {
        "overlap_theme": "alternatives_reentry",
    },
    "Enable Voluntary, Private-Sector, In-Prison Employment Opportunities that Pay a Good Wage": {
        "overlap_theme": "alternatives_reentry",
    },
    "Expand Vocational, Job Readiness, and Re-Entry Programs": {
        "overlap_theme": "alternatives_reentry",
    },
    "Allow for Educational Release as an Earned, Re-Entry Opportunity": {
        "overlap_theme": "alternatives_reentry",
    },
    "Pass the Clean Slate Act": {
        "overlap_theme": "alternatives_reentry",
    },
    "Pilot a New Approach to Transitional Housing for Post-Incarceration Individuals": {
        "overlap_theme": "alternatives_reentry",
    },
    "Eliminate Outdated Supervision Fees to Reduce Barriers for Individuals Returning to Society After Incarceration": {
        "overlap_theme": "alternatives_reentry",
    },
    "Fully Staff the Parole Board and Prohibit Outside Employment for Board Members": {
        "overlap_theme": "alternatives_reentry",
    },
    "Facilitate Access to ID Cards and Other Vital Records to Enhance Opportunities for Released Persons": {
        "overlap_theme": "alternatives_reentry",
    },
    "Automate Debt Forgiveness for State Employees": {
        "overlap_theme": "labor_affordability_general",
    },
    "Protect Consumers from Healthcare Provider Misinformation": {
        "overlap_theme": "health_care_general",
    },
    "Create the Pharmacy Benefits Bureau to Lower the Cost of Prescription Drugs": {
        "overlap_theme": "health_care_general",
    },
    "Strengthen the Statewide Office of Financial Inclusion and Empowerment": {
        "overlap_theme": "government_general",
    },
    "Enhance the UI Benefit Banking Program to Help New Yorkers Receive Their Unemployment Insurance Benefits": {
        "overlap_theme": "labor_affordability_general",
    },
    "Create the Conditions to Attract and Grow Businesses": {
        "overlap_theme": "economic_development_general",
    },
    "Invest in Shovel-Ready Sites to Attract Businesses": {
        "overlap_theme": "economic_development_general",
    },
    "Create One Network for Regional Advanced Manufacturing Partnerships (ON-RAMP)": {
        "overlap_theme": "college_workforce_pathways",
    },
    "Transform Blighted Communities": {
        "overlap_theme": "economic_development_general",
    },
    "Expand Localities' Access to DASNY Construction Services": {
        "overlap_theme": "government_operations_general",
    },
    "Empower Small Business": {
        "overlap_theme": "economic_development_general",
    },
    "Help Small Businesses Navigate Environmental Regulations": {
        "overlap_theme": "economic_development_general",
    },
    "Create New Avenues for Immigrant Entrepreneurs": {
        "overlap_theme": "immigrant_support",
    },
    "Require Paid Breaks for Breast Milk Expression in the Workplace": {
        "overlap_theme": "labor_affordability_general",
    },
    "Promote Economic Growth Through Investment in the Arts": {
        "overlap_theme": "economic_development_general",
    },
    "Bolster Workforce Development": {
        "overlap_theme": "college_workforce_pathways",
    },
    "Establish an Office of Workforce Data and Research": {
        "overlap_theme": "college_workforce_pathways",
    },
    "Expand the Teacher Ambassador Program": {
        "overlap_theme": "education_general",
    },
    "Protect New York's Workers": {
        "overlap_theme": "labor_affordability_general",
    },
    "Create and Distribute a Youth Workers Bill of Rights": {
        "overlap_theme": "labor_affordability_general",
    },
    "Expand Recovery of Stolen Wages": {
        "overlap_theme": "labor_affordability_general",
    },
    "Protect Outdoor Workers from Extreme Weather Hazards": {
        "overlap_theme": "labor_affordability_general",
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


def clean_later_year_rows(rows, year):
    cleaned = []
    dropped = []
    exact_heading_titles = {
        "Standing up for New Yorkers",
        "Increasing Speed, Equity, and Efficiency in Capital Project Delivery",
        "Improving Efficiency of Government Processes",
        "Strengthening Our Digital Infrastructure",
        "Supporting the Youngest New Yorkers and their Families",
        "Protecting Workers",
        "Cutting Auto Insurance Costs",
        "Tackling Rising Home Insurance Costs",
        "Building Opportunities for Homeownership",
        "Unlocking Local Development",
        "Strengthening Investment in Communities",
        "Protecting Housing Affordability",
        "Advancing Student Learning and Supports",
        "Connecting Higher Education and Opportunity",
        "Strengthening Our Supports",
        "Building a More Inclusive State",
        "Protect Vulnerable Populations from Cyber Crime",
        "Protecting Renters and Rent-Stabilized Housing",
        "Building More Housing",
        "Promoting Youth Mental Health",
        "Improving Healthcare Coverage, Access, and Affordability",
        "Improving Equity in Public Health",
    }
    for row in rows:
        title = normalize_whitespace(row["proposal_title"])
        row = dict(row)
        row["proposal_title"] = TITLE_FIXES_LATER.get(title, title)
        row["subsection"] = normalize_whitespace(row["subsection"])
        normalized_title = row["proposal_title"]
        if not normalized_title:
            dropped.append((title, f"{year} empty row"))
            continue
        if normalized_title.startswith(f"{year} State of the State"):
            dropped.append((title, f"{year} source header"))
            continue
        if normalized_title.startswith("Chapter "):
            dropped.append((title, f"{year} chapter heading"))
            continue
        if normalized_title in exact_heading_titles:
            dropped.append((title, f"{year} subsection header"))
            continue
        if len(normalized_title) > 450:
            dropped.append((title, f"{year} foreword or intro spill"))
            continue
        if normalized_title.isupper() and len(normalized_title.split()) <= 8:
            dropped.append((title, f"{year} all-caps heading"))
            continue
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
    body = normalize_whitespace(row.get("commitment_text", "")).lower()
    joined = f"{title} {subsection} {body}"
    for theme, needles in THEME_RULES:
        if any(contains_phrase(joined, needle) for needle in needles):
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
        "Communities / infrastructure": "transportation_general",
        "Parks / recreation": "climate_general",
    }
    if section in fallback:
        return fallback[section]
    section_lower = section.lower()
    if "economic development" in section_lower or "business" in section_lower:
        return "economic_development_general"
    if "student" in section_lower or "education" in section_lower or "learn and thrive" in section_lower:
        return "education_general"
    if "child care" in section_lower or "families" in section_lower:
        return "child_care_access"
    if "health" in section_lower:
        return "health_care_general"
    if "government" in section_lower or "capital project delivery" in section_lower:
        return "government_operations_general"
    if "making new york more affordable" in section_lower:
        return "labor_affordability_general"
    if "helping our children thrive" in section_lower:
        return "education_general"
    if "investing in safety" in section_lower or "keeping new yorkers safe" in section_lower:
        return "public_safety_general"
    if "bringing jobs to new york" in section_lower or "building an economy that works for all" in section_lower:
        return "economic_development_general"
    if "growing housing to drive affordability" in section_lower:
        return "housing_general"
    if "cutting commutes" in section_lower:
        return "transportation_general"
    if "critical infrastructure" in section_lower:
        return "transportation_general"
    if "protecting consumers and workers" in section_lower:
        return "labor_affordability_general"
    if "protecting new york's consumers and workers" in section_lower:
        return "labor_affordability_general"
    if "supporting survivors" in section_lower:
        return "equity_general"
    if "energy future" in section_lower:
        return "energy_affordability"
    return "unclear"


def infer_agencies_with_text(row):
    title = row["proposal_title"].lower()
    subsection = row["subsection"].lower()
    body = normalize_whitespace(row.get("commitment_text", "")).lower()
    joined = f"{title} {subsection} {body}"
    section_bucket = row["section_bucket"]

    lead = []
    support = []

    def add(values, item):
        if item and item not in values:
            values.append(item)

    if any(contains_phrase(joined, token) for token in ["housing", "tenant", "eviction", "voucher", "rent", "homeless", "basement apartment", "office conversion"]):
        add(lead, "HCR")
    if any(contains_phrase(joined, token) for token in ["mental health", "psychiatric", "behavioral health", "suicide"]):
        add(lead, "OMH")
    if any(contains_phrase(joined, token) for token in ["opioid", "substance use", "addiction", "recovery housing"]):
        lead[:] = ["OASAS"]
    if any(contains_phrase(joined, token) for token in ["medicaid", "health care", "hospital", "maternal", "public health", "ombudsman", "long-term care", "wic"]):
        if not lead:
            add(lead, "DOH")
    if any(contains_phrase(joined, token) for token in ["older adults", "older new yorkers", "age in place", "master plan for aging", "long-term care"]):
        add(support, "NYS Office for the Aging")
    if any(contains_phrase(joined, token) for token in ["child care", "children and family", "parent partnership", "foster", "ocfs", "early childhood"]):
        add(lead, "OCFS")
    if any(contains_phrase(joined, token) for token in ["school", "teacher", "literacy", "math", "student", "education department", "educator"]):
        if not lead:
            add(lead, "SED")
    if contains_phrase(joined, "suny"):
        if "community college" in joined or "microcredential" in joined or "student challenge" in joined:
            add(support, "SUNY")
        elif not lead:
            add(lead, "SUNY")
    if contains_phrase(joined, "cuny"):
        if not lead:
            add(lead, "CUNY")
        else:
            add(support, "CUNY")
    if any(contains_phrase(joined, token) for token in ["state police", "nysp"]):
        add(lead, "New York State Police")
    if any(contains_phrase(joined, token) for token in ["gun violence", "crime", "prosecutor", "district attorney", "violence prevention", "dcjs"]):
        if not lead:
            add(lead, "DCJS")
    if any(contains_phrase(joined, token) for token in ["dmv", "driver", "motor vehicle", "non-driver id"]):
        add(support, "DMV")
    if any(contains_phrase(joined, token) for token in ["doccs", "parole", "released persons", "re-entry", "incarcerated"]):
        add(support, "DOCCS")
    if any(contains_phrase(joined, token) for token in ["transportation", "mta", "road", "highway", "traffic", "transit", "commute"]):
        if not lead:
            add(lead, "DOT")
        add(support, "MTA")
    if any(contains_phrase(joined, token) for token in ["climate", "energy", "emission", "electric", "decarbonization", "nyserda"]):
        if not lead:
            add(lead, "NYSERDA")
    if any(contains_phrase(joined, token) for token in ["water", "recycling", "waste", "environment", "parks", "flood", "dec"]):
        if not lead:
            add(lead, "DEC")
    if any(contains_phrase(joined, token) for token in ["labor", "worker", "wage", "apprenticeship", "employment", "workforce", "warn"]):
        if not lead:
            add(lead, "DOL")
    if any(contains_phrase(joined, token) for token in ["insurance", "insurer", "fraud bureau", "workers compensation", "workers’ compensation"]):
        add(support, "DFS")
    if any(contains_phrase(joined, token) for token in ["economic development", "business", "downtown revitalization", "new york forward", "ida", "authorities budget office", "empire state development", "local economic development project tracking"]):
        if section_bucket.lower().find("economic development") != -1:
            lead[:] = ["Empire State Development"]
        elif not lead:
            add(lead, "Empire State Development")
    if any(contains_phrase(joined, token) for token in ["agriculture", "farm", "food supply chain", "farmer"]):
        if not lead:
            add(lead, "Agriculture & Markets")

    if not lead:
        section_defaults = {
            "Housing / homelessness": "HCR",
            "Mental health": "OMH",
            "Health care": "DOH",
            "Public safety / justice": "DCJS",
            "Public safety / gun violence": "DCJS",
            "Schools / higher education": "SED",
            "Economic development / business": "Empire State Development",
            "Agriculture / food systems": "Agriculture & Markets",
            "Labor / affordability": "DOL",
            "Climate / energy / environment": "NYSERDA",
            "Transportation / infrastructure": "DOT",
            "Government operations / customer experience": "",
            "Government workforce / operations": "",
            "Parks / recreation": "DEC",
        }
        add(lead, section_defaults.get(section_bucket, ""))

    row["lead_agency"] = "; ".join(lead)
    row["supporting_agencies"] = "; ".join(support)
    row["lead_agency_standardized"] = standardize_agencies(row["lead_agency"])
    row["supporting_agencies_standardized"] = standardize_agencies(row["supporting_agencies"])
    return row


def contains_phrase(text, needle):
    pattern = r"(?<![a-z0-9])" + re.escape(needle).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


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


def choose_best_match(current_row, prior_rows):
    theme = current_row["overlap_theme"]
    related_themes = {
        "aging_long_term_care": {"aging_long_term_care", "aging_master_plan"},
        "office_conversion": {"office_conversion", "housing_general"},
        "housing_planning_governance": {"housing_planning_governance", "housing_general"},
        "mental_health_supportive_housing": {"mental_health_supportive_housing", "housing_supply"},
    }
    candidates = [
        r for r in prior_rows if r["overlap_theme"] in related_themes.get(theme, {theme})
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
            "Communities / infrastructure": {"Communities / infrastructure / economic development", "Transportation / infrastructure", "Housing / homelessness"},
            "Parks / recreation": {"Communities / infrastructure / economic development", "Climate / energy / environment"},
        }
        candidates = [
            r for r in prior_rows if r["section_bucket"] in section_pairs.get(current_row["section_bucket"], set())
        ]

    title_tokens = tokenize(current_row["proposal_title"])
    best = None
    best_score = 0.0
    for candidate in candidates:
        candidate_tokens = tokenize(candidate["proposal_title"])
        if not candidate_tokens:
            continue
        score = len(title_tokens & candidate_tokens) / len(title_tokens | candidate_tokens)
        if candidate["overlap_theme"] == theme:
            score += 0.35
        if current_row["lead_agency_standardized"] and current_row["lead_agency_standardized"] == candidate["lead_agency_standardized"]:
            score += 0.15
        if score > best_score:
            best = candidate
            best_score = score

    shared = tokenize(best["proposal_title"]) & title_tokens if best else set()
    exact_or_related = best and best["overlap_theme"] in related_themes.get(theme, {theme})
    if best_score < 0.45 and not (exact_or_related and shared and best_score >= 0.35):
        return None, "", ""

    relation = "continuation"
    lowered = current_row["proposal_title"].lower()
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
        override = MANUAL_ROW_OVERRIDES.get(out["proposal_title"])
        if override:
            if "lead_agency" in override:
                out["lead_agency"] = override["lead_agency"]
                out["lead_agency_standardized"] = standardize_agencies(out["lead_agency"])
            if "supporting_agencies" in override:
                out["supporting_agencies"] = override["supporting_agencies"]
                out["supporting_agencies_standardized"] = standardize_agencies(out["supporting_agencies"])
            if "overlap_theme" in override:
                out["overlap_theme"] = override["overlap_theme"]
        enriched.append(out)
    return enriched


def write_csv(path, rows):
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_crosswalk(path, rows):
    fieldnames = [
        "commitment_id",
        "proposal_title",
        "overlap_theme",
        "continuity_to_prior_year",
        "matched_prior_commitment_id",
        "matched_prior_title",
        "match_basis",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "commitment_id": row["commitment_id"],
                    "proposal_title": row["proposal_title"],
                    "overlap_theme": row["overlap_theme"],
                    "continuity_to_prior_year": row["continuity_to_prior_year"],
                    "matched_prior_commitment_id": row["matched_prior_commitment_id"],
                    "matched_prior_title": row["matched_prior_title"],
                    "match_basis": row["match_basis"],
                }
            )


def write_memo(path, dropped_by_year, enriched_by_year):
    lines = [
        "Analysis update",
        "",
        "Outputs created:",
    ]
    for year in sorted(OUTPUT_FILES):
        lines.append(f"- {OUTPUT_FILES[year].name}")
    for year in ["2023", "2024", "2025", "2026"]:
        lines.append(f"- {year}-crosswalk.csv")
    lines.extend(["", "Year summaries:"])
    for year in sorted(enriched_by_year):
        rows = enriched_by_year[year]
        raw_count = len(read_csv(INPUT_FILES[year]))
        lines.append(f"- {year}: {raw_count} raw rows, {len(dropped_by_year[year])} dropped, {len(rows)} kept")
    lines.extend(
        [
            "",
            "Important caution:",
            "- 2024-2026 imports are first-pass TOC extractions and still include some subgroup noise.",
            "- Continuity links beyond 2023 are structured first passes and will need manual review.",
        ]
    )

    path.write_text("\n".join(lines) + "\n")


def main():
    dropped_by_year = defaultdict(list)
    cleaned_rows = {}
    enriched_by_year = {}
    title_maps = {}

    for year, path in INPUT_FILES.items():
        raw_rows = read_csv(path)
        if year == "2023":
            cleaned, dropped = clean_2023_rows(raw_rows)
        elif year in {"2024", "2025", "2026"}:
            cleaned, dropped = clean_later_year_rows(raw_rows, year)
        else:
            cleaned, dropped = raw_rows, []
        cleaned_rows[year] = cleaned
        dropped_by_year[year] = dropped
        enriched_by_year[year] = enrich_rows(cleaned, year)
        title_maps[year] = {row["proposal_title"]: row for row in enriched_by_year[year]}

    ordered_years = sorted(enriched_by_year)
    for year in ordered_years[1:]:
        prior_year = str(int(year) - 1)
        if prior_year not in enriched_by_year:
            continue
        for row in enriched_by_year[year]:
            manual = MANUAL_MATCHES.get(row["proposal_title"])
            if manual:
                match = title_maps[prior_year].get(manual["prior_title"])
                if match:
                    row["continuity_to_prior_year"] = manual["relation"]
                    row["matched_prior_commitment_id"] = match["commitment_id"]
                    row["matched_prior_title"] = match["proposal_title"]
                    row["match_basis"] = manual["basis"]
                    continue
            match, relation, basis = choose_best_match(row, enriched_by_year[prior_year])
            if match is None:
                row["continuity_to_prior_year"] = "new"
                continue
            row["continuity_to_prior_year"] = relation
            row["matched_prior_commitment_id"] = match["commitment_id"]
            row["matched_prior_title"] = match["proposal_title"]
            row["match_basis"] = basis

    for year, rows in enriched_by_year.items():
        write_csv(OUTPUT_FILES[year], rows)
    for year in ordered_years[1:]:
        crosswalk_path = ROOT / f"{int(year)-1}-{year}-crosswalk.csv"
        write_crosswalk(crosswalk_path, enriched_by_year[year])
    write_memo(OUTPUT_MEMO, dropped_by_year, enriched_by_year)

    print("Wrote enriched inventories and pairwise crosswalks for 2022-2026")


if __name__ == "__main__":
    main()
