# Hochul SOTS Progress

This workspace tracks Governor Hochul's policy commitments using the annual State of the State books as the primary source.

Working assumptions:
- Primary source for commitments: State of the State books.
- Secondary source for validation and enrichment: Executive Budget materials.
- A State of the State item is treated as an agenda commitment, not automatically as an enacted or funded policy.
- A single commitment may have multiple agencies with ownership.

Current pilot:
- Year: 2022
- Source: `2022StateoftheStateBook.pdf`
- Extraction basis: table of contents proposal bullets
- Proposal count identified from the table of contents: 220
- Generator script: `generate_2022_tracker.py`
- First-pass tracker output: `2022-first-pass-inventory.csv`

Additional year in progress:
- Year: 2023
- Source: `2023SOTSBook.pdf`
- Generator script: `generate_2023_tracker.py`
- First-pass tracker output: `2023-first-pass-inventory.csv`
- Comparison memo: `2022-2023-comparison.md`

Current analysis outputs:
- Builder script: `build_analysis_outputs.py`
- 2022 enriched inventory: `2022-enriched-inventory.csv`
- 2023 cleaned and enriched inventory: `2023-cleaned-enriched-inventory.csv`
- 2022-2023 crosswalk: `2022-2023-crosswalk.csv`
- Plain-text status memo: `analysis-update.txt`

Prototype site:
- Site data builder: `build_site_data.py`
- Static site entrypoint: `site/index.html`
- Site script: `site/app.js`
- Site styles: `site/styles.css`
- Generated site data: `site/data/site-data.json`

Preview workflow:
- Rebuild analysis data: `python3 build_analysis_outputs.py`
- Rebuild site data: `python3 build_site_data.py`
- Preview locally from the project root: `python3 -m http.server 8000 --directory site`

Core fields for the eventual master inventory:
- year
- source_document
- section_bucket
- subsection
- proposal_title
- lead_agency
- supporting_agencies
- commitment_type
- quantified
- metric_or_target
- implementation_pathway
- notes

Suggested coding values:
- `commitment_type`: program, funding, legislation, regulation, capital project, staffing/workforce, tax/benefit, planning/governance, enforcement
- `implementation_pathway`: executive_action, executive_budget, legislation_required, mixed, unclear
- `quantified`: yes, no, mixed
