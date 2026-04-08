#!/usr/bin/env python3

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path("/Users/tedalcorn/Desktop/codex-projects/NYSOTS")
SOURCE_ROOT = Path("/Users/tedalcorn/Documents/*Resumes/ -Job Applications/2026 01 Hochul Policy Shop/-SOTS")

YEAR_CONFIGS = {
    "2022": {
        "pdf": SOURCE_ROOT / "2022StateoftheStateBook.pdf",
        "inventory": ROOT / "2022-enriched-inventory.csv",
        "body_start": 20,
    },
    "2023": {
        "pdf": SOURCE_ROOT / "2023SOTSBook.pdf",
        "inventory": ROOT / "2023-cleaned-enriched-inventory.csv",
        "body_start": 21,
    },
    "2024": {
        "pdf": SOURCE_ROOT / "2024-SOTS-Book-Online.pdf",
        "inventory": ROOT / "2024-cleaned-enriched-inventory.csv",
        "body_start": 15,
    },
    "2025": {
        "pdf": SOURCE_ROOT / "2025StateoftheStateBook.pdf",
        "inventory": ROOT / "2025-cleaned-enriched-inventory.csv",
        "body_start": 13,
    },
    "2026": {
        "pdf": SOURCE_ROOT / "2026StateoftheStateBook.pdf",
        "inventory": ROOT / "2026-cleaned-enriched-inventory.csv",
        "body_start": 17,
    },
}

HEADER_PATTERNS = (
    re.compile(r"^\d{4}\s+STATE OF THE STATE$", re.IGNORECASE),
    re.compile(r"^STATE OF THE STATE$", re.IGNORECASE),
    re.compile(r"^Governor Kathy Hochul$", re.IGNORECASE),
    re.compile(r"^January\s+\d{4}$", re.IGNORECASE),
)


def normalize_space(text):
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_quotes(text):
    return (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00a0", " ")
    )


def strip_footnote_markers(text):
    text = re.sub(r"(?<=[A-Za-z%])\d{1,3}(?=[\s\.,;:])", "", text)
    text = re.sub(r"(?<=[\.\)])\d{1,3}(?=\s)", "", text)
    return normalize_space(text)


def looks_like_heading(text):
    cleaned = normalize_space(text)
    if not cleaned:
        return False
    if cleaned.startswith(("Part ", "SECTION ", "Chapter ")):
        return True
    if len(cleaned) > 140:
        return False
    if any(mark in cleaned for mark in [".", "?", "!", ";", ":"]) and not cleaned.startswith("Part "):
        return False
    words = cleaned.split()
    if len(words) > 18:
        return False
    capitalized = sum(1 for word in words if word[:1].isupper() or word.isupper())
    return capitalized >= max(2, int(len(words) * 0.7))


def normalize_for_match(text):
    text = normalize_quotes(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return normalize_space(text)


def clean_page_lines(page_text):
    lines = []
    for raw in page_text.splitlines():
        line = normalize_quotes(raw.rstrip())
        collapsed = normalize_space(line)
        if not collapsed:
            lines.append("")
            continue
        if re.fullmatch(r"\d+", collapsed):
            lines.append("")
            continue
        if any(pattern.match(collapsed) for pattern in HEADER_PATTERNS):
            lines.append("")
            continue
        lines.append(line.strip())
    return lines


def page_blocks(pdf_path, body_start):
    text = subprocess.check_output(
        ["pdftotext", "-f", str(body_start), "-layout", str(pdf_path), "-"],
        text=True,
        errors="ignore",
    )
    blocks = []
    for page_offset, page_text in enumerate(text.split("\f")):
        page_number = body_start + page_offset
        lines = clean_page_lines(page_text)
        current = []
        for line in lines:
            if line:
                current.append(line)
                continue
            if current:
                text_block = strip_footnote_markers(" ".join(current))
                if text_block:
                    blocks.append({"page": page_number, "text": text_block, "match": normalize_for_match(text_block), "is_heading": looks_like_heading(text_block)})
                current = []
        if current:
            text_block = strip_footnote_markers(" ".join(current))
            if text_block:
                blocks.append({"page": page_number, "text": text_block, "match": normalize_for_match(text_block), "is_heading": looks_like_heading(text_block)})
    return blocks


def read_rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path, rows):
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_match(title_norm, block_norm):
    return block_norm == title_norm


def is_soft_match(title_norm, block_norm):
    return title_norm in block_norm or block_norm in title_norm


def attach_text(rows, blocks):
    title_norms = [normalize_for_match(row["proposal_title"]) for row in rows]
    matched_indices = []
    cursor = 0

    for title_norm in title_norms:
        found = None
        confidence = ""
        for idx in range(cursor, len(blocks)):
            block_norm = blocks[idx]["match"]
            if is_match(title_norm, block_norm):
                found = idx
                confidence = "high"
                break
        if found is None:
            for idx in range(cursor, len(blocks)):
                block_norm = blocks[idx]["match"]
                if is_soft_match(title_norm, block_norm):
                    found = idx
                    confidence = "medium"
                    break
        matched_indices.append((found, confidence))
        if found is not None:
            cursor = found + 1

    for row_index, row in enumerate(rows):
        match_index, confidence = matched_indices[row_index]
        next_match = next((idx for idx, _ in matched_indices[row_index + 1 :] if idx is not None), None)
        row["commitment_text"] = ""
        row["source_page"] = ""
        row["source_page_end"] = ""
        row["text_capture_confidence"] = ""
        if match_index is None:
            continue

        start = match_index + 1
        end = next_match if next_match is not None else len(blocks)
        for idx in range(start, end):
            if blocks[idx]["is_heading"]:
                end = idx
                break
        text_blocks = [block["text"] for block in blocks[start:end]]
        row["commitment_text"] = "\n\n".join(text_blocks).strip()
        row["source_page"] = str(blocks[match_index]["page"])
        row["source_page_end"] = str(blocks[end - 1]["page"]) if end > start else str(blocks[match_index]["page"])
        row["text_capture_confidence"] = confidence

    return rows


def ensure_columns(rows):
    for row in rows:
        row.setdefault("commitment_text", "")
        row.setdefault("source_page", "")
        row.setdefault("source_page_end", "")
        row.setdefault("text_capture_confidence", "")


def main():
    for year, config in YEAR_CONFIGS.items():
        rows = read_rows(config["inventory"])
        ensure_columns(rows)
        blocks = page_blocks(config["pdf"], config["body_start"])
        attach_text(rows, blocks)
        write_rows(config["inventory"], rows)

        total = len(rows)
        high = sum(1 for row in rows if row["text_capture_confidence"] == "high")
        medium = sum(1 for row in rows if row["text_capture_confidence"] == "medium")
        missing = sum(1 for row in rows if not row["text_capture_confidence"])
        print(f"{year}: high={high} medium={medium} missing={missing} total={total}")


if __name__ == "__main__":
    main()
