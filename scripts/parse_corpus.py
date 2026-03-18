#!/usr/bin/env python3
"""
parse_corpus.py — Convert LinearAInscriptions.js to canonical JSON + CSV + INVENTORY.md

Reads the JavaScript Map declaration, extracts 1,722 inscription records,
and outputs:
  - data/corpus/canonical_corpus.json
  - data/corpus/canonical_corpus.csv
  - data/corpus/INVENTORY.md
  - errors/ERRORS.md (if any parsing errors)

Usage:
    python3 scripts/parse_corpus.py
"""

import json
import csv
import re
import os
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_JS = BASE_DIR / "data" / "corpus" / "LinearAInscriptions.js"
OUTPUT_JSON = BASE_DIR / "data" / "corpus" / "canonical_corpus.json"
OUTPUT_CSV = BASE_DIR / "data" / "corpus" / "canonical_corpus.csv"
OUTPUT_INVENTORY = BASE_DIR / "data" / "corpus" / "INVENTORY.md"
OUTPUT_ERRORS = BASE_DIR / "errors" / "ERRORS.md"

# Linear A Unicode block: U+10600–U+1077F
LINEAR_A_RANGE = (0x10600, 0x1077F)

# Aegean Numbers block: U+10100–U+1013F
AEGEAN_NUMBERS_RANGE = (0x10100, 0x1013F)

# Word divider sign
WORD_DIVIDER = "\U00010101"  # 𐄁 Aegean word separator


def is_linear_a_sign(ch: str) -> bool:
    """Check if a character is in the Linear A Unicode block."""
    cp = ord(ch)
    return LINEAR_A_RANGE[0] <= cp <= LINEAR_A_RANGE[1]


def count_linear_a_signs(text: str) -> int:
    """Count Linear A sign characters in a string."""
    return sum(1 for ch in text if is_linear_a_sign(ch))


def is_number_token(token: str) -> bool:
    """Check if a transliterated token is a number (pure digits, possibly with fractions)."""
    if not token:
        return False
    t = token.strip()
    # Match integers, decimals, fractions (ASCII)
    if re.match(r'^[\d]+([./][\d]+)?$', t):
        return True
    # Match Unicode fraction characters (vulgar fractions, superscript/subscript combos)
    # e.g. ¹⁄₂, ³⁄₄, ¹⁄₁₆, etc.
    if re.match(r'^[¹²³⁴⁵⁶⁷⁸⁹⁰⁄₀₁₂₃₄₅₆₇₈₉]+$', t):
        return True
    # Match combined: "5 ³⁄₄" (number + space + fraction) — these come as separate tokens
    return False


# Fragment/editorial markers to exclude from word lists
FRAGMENT_CHARS = {
    "\U0001076B",  # 𐝫 EDITORIAL MARK (broken/fragmentary)
    "\U00010764",  # Other editorial marks if any
}

# Dash/separator tokens
DASH_TOKEN = "\u2014"  # em dash


def is_number_or_fraction(token: str) -> bool:
    """Check if token is a number, fraction, or numeric notation."""
    t = token.strip()
    if not t:
        return False
    if is_number_token(t):
        return True
    # Approximation signs with fractions: "≈ ¹⁄₆"
    clean = t.replace("\u2248", "").strip()  # remove ≈
    if clean and re.match(r'^[¹²³⁴⁵⁶⁷⁸⁹⁰⁄₀₁₂₃₄₅₆₇₈₉]+$', clean):
        return True
    return False


def is_fragment_or_editorial(token: str) -> bool:
    """Check if token is a fragment marker or editorial notation."""
    t = token.strip()
    if not t:
        return False
    # Pure fragment markers
    if all(ch in FRAGMENT_CHARS for ch in t):
        return True
    return False


def is_newline_or_divider(token: str) -> bool:
    """Check if a token is a newline marker or word divider."""
    if token == "\n":
        return True
    if token.strip() == WORD_DIVIDER:
        return True
    if token.strip() == "\U00010101":  # 𐄁 Aegean word separator
        return True
    return False


def extract_inscriptions_js(js_text: str) -> str:
    """Extract just the inscriptions Map content from the full JS file."""
    # Find the first `var inscriptions = new Map([` and its closing `]);`
    start_marker = "var inscriptions = new Map(["
    start_idx = js_text.index(start_marker)

    # Find the matching ]);
    # We need to find the FIRST ]); after the opening
    # The inscriptions section ends before `var lexicon`
    end_marker = "]);"
    # Search for the first ]); that's on its own line after the start
    search_from = start_idx + len(start_marker)

    # Find "var lexicon" which marks the end of inscriptions
    lexicon_idx = js_text.index("var lexicon", search_from)
    # The ]); before lexicon
    end_idx = js_text.rindex(end_marker, search_from, lexicon_idx)

    # Extract just the array contents (between [ and ])
    content = js_text[start_idx + len(start_marker):end_idx]
    return content


def parse_entries(content: str) -> list:
    """
    Parse the inscription entries from the JS Map content.

    Each entry is: ["ID", { ... }],
    We split on the entry boundaries and parse each object.
    """
    entries = []
    errors = []

    # Strategy: Find each entry by matching ["ID",{ pattern
    # Then find the matching closing }],
    # The JS objects are almost-JSON — we need to handle trailing commas

    # Split into individual entries using the pattern: ["...",{
    entry_pattern = re.compile(r'\["([^"]+)",\{')

    matches = list(entry_pattern.finditer(content))

    for i, match in enumerate(matches):
        entry_id = match.group(1)
        obj_start = match.start() + len(match.group(0)) - 1  # Position of {

        # Find the end of this entry: }], or }]\n for the last one
        if i + 1 < len(matches):
            search_end = matches[i + 1].start()
        else:
            search_end = len(content)

        # Find the closing }] within this range
        segment = content[obj_start:search_end]

        # Find the last }] in the segment
        close_idx = segment.rfind("}]")
        if close_idx == -1:
            errors.append(f"Could not find closing '}}]' for entry {entry_id}")
            continue

        obj_text = segment[:close_idx + 1]  # Include the }

        # Convert JS object to valid JSON
        try:
            obj = js_object_to_dict(obj_text, entry_id)
            entries.append((entry_id, obj))
        except Exception as e:
            errors.append(f"Failed to parse entry {entry_id}: {e}")

    return entries, errors


def js_object_to_dict(obj_text: str, entry_id: str) -> dict:
    """
    Convert a JavaScript object literal to a Python dict.
    Handles:
    - Trailing commas in arrays and objects
    - Already-escaped quotes in strings
    - ES6 Unicode escapes: \\u{XXXXX} -> actual Unicode character
    """
    # Convert ES6 \u{XXXXX} escapes to actual Unicode characters
    # JSON only supports \uXXXX (4-digit), so we replace the ES6 form
    def replace_es6_unicode(m):
        codepoint = int(m.group(1), 16)
        return chr(codepoint)

    cleaned = re.sub(r'\\u\{([0-9a-fA-F]+)\}', replace_es6_unicode, obj_text)

    # Remove trailing commas before ] or }
    # Match: comma, optional whitespace/newlines, then ] or }
    cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

    # Parse as JSON
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Try harder: some entries might have other JS-isms
        raise ValueError(f"JSON parse failed for {entry_id}: {e}\nFirst 200 chars: {cleaned[:200]}")


def build_record(entry_id: str, obj: dict) -> dict:
    """Build a canonical record from a parsed JS object."""
    # Extract words, filtering newlines, dividers, and fragment markers
    raw_words = obj.get("words", [])
    words_unicode = [w for w in raw_words
                     if not is_newline_or_divider(w)
                     and not is_fragment_or_editorial(w)]

    # Extract transliterated words, separating words from numbers
    raw_translit = obj.get("transliteratedWords", [])
    words_translit = []
    numbers = []
    for token in raw_translit:
        if is_newline_or_divider(token):
            continue
        if is_fragment_or_editorial(token):
            continue
        if token.strip() == DASH_TOKEN:
            continue
        if is_number_or_fraction(token):
            numbers.append(token)
        else:
            words_translit.append(token)

    # Extract translated words, separating words from numbers
    raw_translated = obj.get("translatedWords", [])
    words_translated = []
    for token in raw_translated:
        if is_newline_or_divider(token):
            continue
        if is_fragment_or_editorial(token):
            continue
        if token.strip() == DASH_TOKEN:
            continue
        if is_number_or_fraction(token):
            continue  # Already captured from transliterated
        words_translated.append(token)

    # Parsed inscription
    parsed = obj.get("parsedInscription", "")

    # Count lines (newlines + 1, but handle empty)
    if parsed.strip():
        line_count = parsed.count("\n") + 1
    else:
        line_count = 0

    # Count Linear A signs
    sign_count = count_linear_a_signs(parsed)

    return {
        "id": entry_id,
        "site": obj.get("site", ""),
        "context": obj.get("context", ""),
        "support": obj.get("support", ""),
        "scribe": obj.get("scribe", ""),
        "findspot": obj.get("findspot", ""),
        "signs_unicode": parsed,
        "words_unicode": words_unicode,
        "words_transliterated": words_translit,
        "words_translated": words_translated,
        "numbers": numbers,
        "line_count": line_count,
        "sign_count": sign_count,
        "word_count": len(words_unicode),
    }


def generate_csv(records: list, output_path: Path):
    """Generate canonical CSV from records."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "site", "context", "support",
            "sign_count", "word_count", "line_count", "transliteration"
        ])
        for rec in records:
            # Build transliteration: words joined by spaces, lines by |
            translit_parts = rec.get("words_transliterated", [])
            # Reconstruct with line breaks from original
            # We need to go back to the raw data for line structure
            transliteration = " ".join(translit_parts) if translit_parts else ""

            writer.writerow([
                rec["id"],
                rec["site"],
                rec["context"],
                rec["support"],
                rec["sign_count"],
                rec["word_count"],
                rec["line_count"],
                transliteration,
            ])


def generate_csv_with_lines(records: list, raw_entries: dict, output_path: Path):
    """Generate CSV with line-break-aware transliteration."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "site", "context", "support",
            "sign_count", "word_count", "line_count", "transliteration"
        ])
        for rec in records:
            entry_id = rec["id"]
            obj = raw_entries.get(entry_id, {})
            raw_translit = obj.get("transliteratedWords", [])

            # Rebuild transliteration preserving line structure
            lines = []
            current_line = []
            for token in raw_translit:
                if token == "\n":
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = []
                elif token.strip() == "𐄁":
                    current_line.append("|")
                else:
                    current_line.append(token)
            if current_line:
                lines.append(" ".join(current_line))

            transliteration = " | ".join(lines)

            writer.writerow([
                rec["id"],
                rec["site"],
                rec["context"],
                rec["support"],
                rec["sign_count"],
                rec["word_count"],
                rec["line_count"],
                transliteration,
            ])


def generate_inventory(records: list, output_path: Path):
    """Generate INVENTORY.md with corpus statistics."""
    total = len(records)
    total_signs = sum(r["sign_count"] for r in records)
    avg_signs = total_signs / total if total else 0

    # By site
    site_counts = Counter(r["site"] for r in records if r["site"])
    # By support
    support_counts = Counter(r["support"] for r in records if r["support"])
    # By context/period
    context_counts = Counter(r["context"] for r in records if r["context"])

    # Top transliterated words
    all_words = []
    for r in records:
        for w in r["words_transliterated"]:
            if w and w.strip():
                all_words.append(w.strip())
    word_freq = Counter(all_words)
    top_words = word_freq.most_common(10)

    # Length distribution
    lengths = [r["sign_count"] for r in records]
    length_buckets = Counter()
    for l in lengths:
        if l == 0:
            length_buckets["0 (empty)"] += 1
        elif l <= 5:
            length_buckets["1-5"] += 1
        elif l <= 10:
            length_buckets["6-10"] += 1
        elif l <= 20:
            length_buckets["11-20"] += 1
        elif l <= 50:
            length_buckets["21-50"] += 1
        elif l <= 100:
            length_buckets["51-100"] += 1
        else:
            length_buckets["100+"] += 1

    # Sort buckets by their lower bound
    bucket_order = ["0 (empty)", "1-5", "6-10", "11-20", "21-50", "51-100", "100+"]

    now = datetime.now().strftime("%Y-%m-%d")

    lines = []
    lines.append(f"""<system_meta>
  <id>signal-theory-anth-linear-a-inventory-001</id>
  <tags>
    <agent>signal-theory-anth</agent>
    <type>research</type>
    <status>verified</status>
    <project>linear-a</project>
    <time>{now}</time>
  </tags>
  <tldr>Corpus statistics for 1,722 Linear A inscriptions: sites, supports, periods, word frequencies, length distribution.</tldr>
</system_meta>

# Linear A Corpus Inventory

**Generated:** {now}
**Source:** `LinearAInscriptions.js` (John Younger / SigLA concordance)

---

## Summary

| Metric | Value |
|--------|-------|
| Total inscriptions | {total:,} |
| Total sign tokens | {total_signs:,} |
| Average signs/inscription | {avg_signs:.1f} |
| Distinct sites | {len(site_counts)} |
| Distinct support types | {len(support_counts)} |
| Distinct periods | {len(context_counts)} |
| Distinct transliterated words | {len(word_freq):,} |

---

## Inscriptions by Site

| Site | Count |
|------|-------|""")
    for site, count in site_counts.most_common():
        lines.append(f"| {site} | {count} |")

    lines.append("""
---

## Inscriptions by Support Type

| Support | Count |
|---------|-------|""")
    for support, count in support_counts.most_common():
        lines.append(f"| {support} | {count} |")

    lines.append("""
---

## Inscriptions by Period/Context

| Period | Count |
|--------|-------|""")
    for ctx, count in context_counts.most_common():
        lines.append(f"| {ctx} | {count} |")

    lines.append("""
---

## Top 10 Most Common Transliterated Words

| Rank | Word | Frequency |
|------|------|-----------|""")
    for rank, (word, freq) in enumerate(top_words, 1):
        lines.append(f"| {rank} | {word} | {freq} |")

    lines.append("""
---

## Distribution of Inscription Lengths (by sign count)

| Range | Count |
|-------|-------|""")
    for bucket in bucket_order:
        if bucket in length_buckets:
            lines.append(f"| {bucket} | {length_buckets[bucket]} |")

    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_errors(errors: list, output_path: Path):
    """Write parsing errors to ERRORS.md."""
    now = datetime.now().strftime("%Y-%m-%d")

    lines = [f"""<system_meta>
  <id>signal-theory-anth-linear-a-errors-001</id>
  <tags>
    <agent>signal-theory-anth</agent>
    <type>research</type>
    <status>draft</status>
    <project>linear-a</project>
    <time>{now}</time>
  </tags>
  <tldr>Parsing errors from LinearAInscriptions.js corpus conversion.</tldr>
</system_meta>

# Linear A Corpus — Parsing Errors

**Generated:** {now}
**Total errors:** {len(errors)}

---
"""]
    if errors:
        for i, err in enumerate(errors, 1):
            lines.append(f"{i}. {err}")
    else:
        lines.append("No parsing errors encountered.")

    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    print(f"Reading {INPUT_JS}...")
    js_text = INPUT_JS.read_text(encoding="utf-8")

    print("Extracting inscriptions section...")
    content = extract_inscriptions_js(js_text)

    print("Parsing entries...")
    entries, parse_errors = parse_entries(content)
    print(f"  Parsed {len(entries)} entries, {len(parse_errors)} errors")

    # Deduplicate: if same ID appears multiple times, keep the last (most complete) entry
    seen = {}
    dedup_count = 0
    for entry_id, obj in entries:
        if entry_id in seen:
            dedup_count += 1
        seen[entry_id] = obj
    if dedup_count:
        print(f"  Deduplicated {dedup_count} entries (kept last/most complete version)")
    deduped_entries = list(seen.items())

    # Build raw entries lookup for CSV generation
    raw_entries = {}

    print("Building canonical records...")
    records = []
    build_errors = []
    for entry_id, obj in deduped_entries:
        try:
            rec = build_record(entry_id, obj)
            records.append(rec)
            raw_entries[entry_id] = obj
        except Exception as e:
            build_errors.append(f"Error building record for {entry_id}: {e}")

    # Record deduplication as informational notes (not errors)
    dedup_notes = []
    if dedup_count:
        # Find which IDs were duplicated
        id_counts = Counter(eid for eid, _ in entries)
        for eid, cnt in id_counts.items():
            if cnt > 1:
                dedup_notes.append(
                    f"NOTE: {eid} appears {cnt} times in source — kept last (most complete) entry"
                )

    all_errors = parse_errors + build_errors + dedup_notes
    print(f"  Built {len(records)} records, {len(build_errors)} build errors")

    # Output JSON
    print(f"Writing {OUTPUT_JSON}...")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"  Wrote {len(records)} records to JSON ({OUTPUT_JSON.stat().st_size:,} bytes)")

    # Output CSV
    print(f"Writing {OUTPUT_CSV}...")
    generate_csv_with_lines(records, raw_entries, OUTPUT_CSV)
    print(f"  Wrote CSV ({OUTPUT_CSV.stat().st_size:,} bytes)")

    # Output INVENTORY
    print(f"Writing {OUTPUT_INVENTORY}...")
    generate_inventory(records, OUTPUT_INVENTORY)
    print(f"  Wrote INVENTORY.md")

    # Output ERRORS
    print(f"Writing {OUTPUT_ERRORS}...")
    OUTPUT_ERRORS.parent.mkdir(parents=True, exist_ok=True)
    generate_errors(all_errors, OUTPUT_ERRORS)
    print(f"  Wrote ERRORS.md ({len(all_errors)} errors)")

    # Summary
    print("\n=== CORPUS SUMMARY ===")
    print(f"  Inscriptions: {len(records)}")
    total_signs = sum(r['sign_count'] for r in records)
    print(f"  Total sign tokens: {total_signs:,}")
    print(f"  Avg signs/inscription: {total_signs/len(records):.1f}")

    sites = Counter(r['site'] for r in records if r['site'])
    print(f"  Top 5 sites: {', '.join(f'{s} ({c})' for s, c in sites.most_common(5))}")

    real_errors = parse_errors + build_errors
    if real_errors:
        print(f"\n  WARNING: {len(real_errors)} parsing errors — see errors/ERRORS.md")
        return 1

    if dedup_notes:
        print(f"\n  {len(dedup_notes)} dedup note(s) logged to errors/ERRORS.md. No parsing errors.")
    else:
        print("\n  No errors. Corpus is clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
