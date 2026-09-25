
External agenda crosswalks (`crosswalks/`):
- Purpose: test an outside policy agenda against (a) what Hochul has committed to in the SOTS books and (b) what New York has actually implemented. Extends the project from an internal continuity tracker to a gap-finder.
- `northwell-gvp-playbook-2026-ny-crosswalk.csv` — **NOT COMMITTED; local only.** Held out of the public repo pending agency verification, because it scores New York implementation status from desk research alone (including "promised, not delivered" calls). Do not publish until confirmed with DOH/OGVP. Northwell Center for Gun Violence Prevention, *Leveraging Health Policy to Prevent Gun Violence: A Playbook for State and Federal Leaders* (2026). 32 state-level measures scored: `ny_status` (GAP / PARTIAL / PARTIAL_PILOT / PARTIAL_REGRESSED / PROMISED_NOT_DELIVERED / SUBSTANTIALLY_DONE / DONE_WITH_CAVEAT), `sots_evidence`, `real_world_evidence`, `opportunity_rank`. Source: https://onwardpublishing.com/nh/NHGVPPPlaybook/ (22pp; page images resolve to online.fliphtml5.com/onward/ddtg/).
- `sots-gun-violence-commitments-2022-2026.csv` — all 34 gun-related SOTS commitments 2022–2026 with a `health_framed` flag.
- Caveat: `real_world_evidence` is desk research as of 2026-09-15, not FOIL-verified. Confirm with DOH/OGVP before publishing any "not delivered" claim.

Extraction bug fixed 2026-09-24 (`generate_later_year_trackers.py`):
- `toc_end` was set short for 2025 (12, should be 14) and 2026 (16, should be 18), so the TOC parse stopped before the last chapters and their proposals never entered the inventory. 2024's range was correct; 2022/2023 use different generators and were unaffected.
- Recovered 81 commitments: 2025 168 -> 214 (Ch.14 Social Services & Equity, Ch.15 Building a Sustainable Future), 2026 176 -> 211 (Ch.10 Protecting NY's Environment, Ch.11 Building Resilient Communities). Corpus 916 -> 997.
- Consequence: any composition analysis run before this date understated climate/environment and equity in 2025-2026. The pre-fix numbers showed climate falling to 2.4% of 2025 items; corrected it is 6.1%.
- Lesson for new years: verify `max(source_page)` against the source PDF's last content page before trusting any trend.

Composition analysis (`crosswalks/build_composition.py`):
- `section_bucket` is NOT comparable across years (2022-2024 normalized buckets, 2025-2026 raw chapter headings) and `overlap_theme` is a hand-assigned lookup whose granularity drifts by year. Neither supports a trend. The script re-classifies all rows with one title-first ruleset so residual error is uniform.
- Outputs `composition-by-domain.csv` (share of items and share of words per domain per year) and `agenda-character-by-year.csv` (new vs continuation, quantification, dollar figures, median length).
- Accuracy: ~10% unclassified, and spot-checks still find occasional wrong-bucket calls. Good for direction of travel on large moves; do NOT quote single-year shares to a decimal as fact. An LLM classification pass over the 997 items is the real fix.
