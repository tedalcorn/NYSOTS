# 2022 Pilot Summary

Source used:
- `2022StateoftheStateBook.pdf`
- Row-level first pass: `2022-first-pass-inventory.csv`

Why 2022 works as a pilot:
- The table of contents breaks the book into discrete proposal lines.
- Most proposals are stated in a way that can be coded as commitments.
- Many proposals are explicitly quantified, which will help later evaluation.

Important caveat:
- The State of the State book should be treated as the Governor's agenda, not as proof that every item was enacted, funded, or completed.

## 2022 agenda shape

Total proposal lines identified from the table of contents: `220`

By top-level section:

| Section | Proposal count | Likely lead agency families |
| --- | ---: | --- |
| Health care | 34 | DOH, OMH, OASAS, OPWDD, OCFS, DFS |
| Public safety / gun violence | 13 | State Police, DCJS, Division of Homeland Security and Emergency Services, local law enforcement partners |
| People / workforce / reentry / food systems | 39 | DOL, DOCCS, DMV, HESC, Agriculture & Markets, ESD, SUNY, CUNY |
| Communities / infrastructure / economic development | 41 | DOT, MTA, ESD, ORDA, OGS, local development entities |
| Housing / homelessness | 20 | Homes and Community Renewal, OMH, OTDA, local housing actors |
| Climate / energy / environment | 27 | NYSERDA, DEC, PSC/DPS, DOT, state agencies with fleet/building responsibilities |
| Schools / higher education | 23 | State Education Department, SUNY, CUNY, HESC, OCFS |
| Equity / inclusion / veterans / immigrants | 22 | Division of Human Rights, ONA, ESD, DOCCS, veterans agencies, public-facing state agencies |
| Government reform | 1 | Executive Chamber, Legislature, ethics and elections bodies |

## Early read on concentration

The 2022 agenda appears highly concentrated. A relatively small set of agency clusters likely covers most of the book:

1. Health and human services: DOH, OMH, OASAS, OPWDD, OCFS
2. Housing and homelessness: HCR, OMH, OTDA
3. Public safety and justice: State Police, DCJS, DOCCS
4. Education and higher ed: SED, SUNY, CUNY, HESC
5. Infrastructure and economic development: DOT, MTA, ESD
6. Climate, energy, and environment: NYSERDA, DEC, PSC/DPS

For scoping purposes, these clusters likely cover a clear majority of the Governor's 2022 agenda.

## Issues to resolve before scaling

1. Multi-agency ownership
Some items are plainly shared across agencies and should not be forced into one-agency coding only.

2. Repeated or overlapping items
Some commitments recur in more than one policy context. We should preserve the item once in the master inventory and track cross-references in notes.

3. Truncated table-of-contents lines
Some proposal titles wrap in the PDF extraction. Those will need cleanup against the body text or official web versions.

4. Commitment type distinctions
The inventory should distinguish between legislation, budget asks, program launches, staffing goals, and capital commitments.

## Recommended next step

Build the 2022 commitment-level tracker with one row per proposal and these minimum fields:
- year
- section_bucket
- subsection
- proposal_title
- lead_agency
- supporting_agencies
- commitment_type
- quantified
- metric_or_target
- implementation_pathway
