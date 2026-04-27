import re
import json
import os
import sys
import pdfplumber
from pathlib import Path
from tqdm import tqdm

# ── Path setup ────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

# ── Regex patterns ────────────────────────────────────────────────────────────

SUMMARY_RE = re.compile(r"SUMMARY\s+OF", re.IGNORECASE)
END_OF_STANDARD_RE = re.compile(r"For detailed information.*refer to", re.IGNORECASE)

IS_CODE_EXTRACT_RE = re.compile(
    r"(IS\s+\d+(?:\s*\([Pp][Aa][Rr][Tt]\s*\d+\))?\s*:\s*\d{4})", re.IGNORECASE
)
IS_NUMBER_ONLY_RE = re.compile(r"^(IS\s+\d+)\s*$", re.IGNORECASE)
IS_CODE_NO_YEAR_RE = re.compile(r"^(IS\s+\d+)\s*:", re.IGNORECASE)
IS_PART_CONTINUATION_RE = re.compile(
    r"^(\([Pp][Aa][Rr][Tt]\s*\d+\)\s*:\s*\d{4})", re.IGNORECASE
)

YEAR_RE = re.compile(r":\s*(\d{4})\s*")
SECTION_HEADER_RE = re.compile(r"^SECTION\s+(\d+)\s*$", re.IGNORECASE)
SUBCATEGORY_RE = re.compile(r"^[A-Z][A-Z\s\(\)\/&,\-]+$")
REVISION_RE = re.compile(r"^\(.*[Rr]evision\)$")
CLAUSE_START_RE = re.compile(r"^\d+[\.\s]")

# ── Section map ───────────────────────────────────────────────────────────────

SECTION_MAP = {
    1:  "Cement and Concrete",
    2:  "Building Limes",
    3:  "Stones",
    4:  "Wood Products for Building",
    5:  "Gypsum Building Materials",
    6:  "Timber",
    7:  "Bitumen and Tar Products",
    8:  "Floor, Wall, Roof Coverings and Finishes",
    9:  "Water Proofing and Damp Proofing Materials",
    10: "Sanitary Appliances and Water Fittings",
    11: "Builder's Hardware",
    12: "Wood Products",
    13: "Doors, Windows and Shutters",
    14: "Concrete Reinforcement",
    15: "Structural Steels",
    16: "Light Metal and Their Alloys",
    17: "Structural Shapes",
    18: "Welding Electrodes and Wires",
    19: "Threaded Fasteners and Rivets",
    20: "Wire Ropes and Wire Products",
    21: "Glass",
    22: "Fillers, Stoppers and Putties",
    23: "Thermal Insulation Materials",
    24: "Plastics",
    25: "Conductors and Cables",
    26: "Wiring Accessories",
    27: "General",
}

# ── Manual scope overrides ────────────────────────────────────────────────────
# For standards where PDF extraction consistently fails due to layout issues

MANUAL_SCOPES = {
    "IS 12592 : 2002": (
        "Requirements for precast steel reinforced cement concrete manhole covers "
        "and frames intended for use in sewerage and water drainage."
    ),
    "IS 4985 : 1988": (
        "Requirements for plain end as well as socket end unplasticized PVC pipes "
        "including those for use with electronic sealing rings. This standard does "
        "not cover unplasticized PVC pipes used in suction and delivery lines of "
        "agricultural pumps."
    ),
    "IS 2556 (Part 3) : 1994": (
        "Requirements for patterns, sizes, construction, dimensions, finish, "
        "flushing tests, inspection and marking for vitreous china squatting pans."
    ),
    "IS 2556 (Part 5) : 1994": (
        "Requirements for sizes, dimensions, finish, and construction for the "
        "vitreous china laboratory sinks."
    ),
    "IS 2556 (Part 8) : 1995": (
        "Requirements for patterns, construction, dimensions, tolerances, finish "
        "and flushing tests for vitreous china pedestal close coupled washdown "
        "and syphonic water closets."
    ),
    "IS 2556 (Part 15) : 1995": (
        "Requirements for patterns, construction, dimensions, finish, flushing "
        "tests, inspection and marking for vitreous china universal water closets."
    ),
    "IS 6411 : 1985": (
        "Requirements for gel-coated glass fibre reinforced polyester resin bath "
        "tubs including performance requirements for impact resistance, hardness, "
        "water absorption, gel-coat thickness and tensile strength of laminates."
    ),
    "IS 9537 (Part 1) : 1980": (
        "This standard applies to conduits of circular cross section for the "
        "protection of conductors and/or cables in electrical installations."
    ),
    "IS 6746 : 1994": (
        "Requirements for materials, dimensions, workmanship and tests for "
        "unplasticized PVC fittings for use with PVC pipes for water supplies."
    ),
    "IS 1608 : 1995": (
        "Requirements for mechanical testing of metals including tensile testing "
        "at ambient temperature covering wrought metal products."
    ),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_is_code(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"^IS\s*", "IS ", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*[Pp][Aa][Rr][Tt]\s*(\d+)\s*\)", r"(Part \1)", s)
    s = re.sub(r"\s*:\s*", " : ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract_scope(text: str) -> str:
    """
    Final version — handles all SP 21 formatting variants.
    Collects lines after the scope trigger until a clause boundary is hit.
    """

    CLAUSE_BOUNDARY = re.compile(
        r"^\d+[\.\s]|^TABLE\s+\d+|^Note\s*[—–\-]|^For detailed",
        re.IGNORECASE
    )
    RIGHT_COLUMN_NOISE = re.compile(
        r"\s+\d+\.\s+[A-Z][a-zA-Z\s\—\-]+$"
    )

    def collect_multiline(text: str, start_pos: int) -> str:
        remaining = text[start_pos:]
        remaining = re.sub(r"^[—–\-:\s]+", "", remaining.strip())
        lines = remaining.split("\n")
        collected = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if CLAUSE_BOUNDARY.match(line):
                break
            line = RIGHT_COLUMN_NOISE.sub("", line).strip()
            if line:
                collected.append(line)
            if len(" ".join(collected)) > 200:
                break
        result = " ".join(collected).strip()
        result = re.sub(r"\s+", " ", result)
        return result

    # 1. Scope with delimiter — em dash, en dash, hyphen, colon
    m = re.search(r"(?:1\.\s+)?Scope\s*[—–\-:]\s*", text, re.IGNORECASE)
    if m:
        scope = collect_multiline(text, m.end())
        if len(scope) > 20:
            return scope[:800]

    # 2. "1. Scope " followed immediately by uppercase text (no delimiter)
    m = re.search(r"(?:1\.\s+)Scope\s+([A-Z][a-z])", text)
    if m:
        scope = collect_multiline(text, m.start(1))
        if len(scope) > 20:
            return scope[:800]

    # 3. Bare "1. Scope" then content on next line
    m = re.search(r"(?:1\.\s+)?Scope\s*\n", text, re.IGNORECASE)
    if m:
        scope = collect_multiline(text, m.end())
        if len(scope) > 20:
            return scope[:800]

    # 4. "1. Specification — text"
    m = re.search(r"(?:1\.\s+)?Specification\s*[—–\-:]\s*", text, re.IGNORECASE)
    if m:
        scope = collect_multiline(text, m.end())
        if len(scope) > 20:
            return scope[:800]

    # 5. 1.1 sub-clause with explicit scope keywords
    m = re.search(
        r"1[\.\s]1\s+(?:Requirements?\s+(?:for|of)|This\s+standard\s+covers?|Covers?|Lays?\s+down)\s*",
        text, re.IGNORECASE
    )
    if m:
        scope = collect_multiline(text, m.end())
        if len(scope) > 20:
            return scope[:800]

    # 6. Any 1.1 clause as absolute last resort
    m = re.search(r"1[\.\s]1\s+([A-Z])", text)
    if m:
        scope = collect_multiline(text, m.start(1))
        if len(scope) > 20:
            return scope[:800]

    return ""


def extract_keywords(title: str, scope: str, subcategory: str) -> list:
    STOPWORDS = {
        "and", "or", "for", "the", "of", "in", "to", "a", "an",
        "is", "are", "its", "be", "as", "by", "with", "from",
        "that", "this", "on", "at", "not", "shall", "used", "use",
        "part", "first", "second", "third", "fourth", "revision",
        "also", "when", "where", "which", "been", "has", "have",
        "may", "more", "than", "per", "cent", "such", "their"
    }
    combined = f"{title} {scope} {subcategory}".lower()
    combined = re.sub(r"[^\w\s\-]", " ", combined)
    words = combined.split()
    return list(dict.fromkeys(
        w for w in words if len(w) > 2 and w not in STOPWORDS
    ))[:30]


# ── Main Parser ───────────────────────────────────────────────────────────────

def parse_sp21(pdf_path: str, output_path: str = None) -> list:

    if output_path is None:
        output_path = os.path.join(DATA_DIR, "standards.json")

    standards = []

    # State
    current_section     = 1
    current_subcategory = ""
    in_summary          = False
    pending_is_number   = ""
    current_is_code     = ""
    current_title_lines = []
    current_title_done  = False
    current_text_lines  = []

    def flush_standard():
        nonlocal current_is_code, current_title_lines
        nonlocal current_title_done, current_text_lines

        if not current_is_code:
            return

        raw_text = "\n".join(current_text_lines).strip()
        title    = " ".join(current_title_lines).strip()
        title    = re.sub(r"\s*\(.*?[Rr]evision\)\s*", " ", title).strip()

        scope      = extract_scope(raw_text)

        # Apply manual override if extraction failed
        normalized_code = normalize_is_code(current_is_code)
        if not scope and normalized_code in MANUAL_SCOPES:
            scope = MANUAL_SCOPES[normalized_code]

        year_match = YEAR_RE.search(current_is_code)
        year       = int(year_match.group(1)) if year_match else None
        keywords   = extract_keywords(title, scope, current_subcategory)

        standards.append({
            "is_code":        normalized_code,
            "title":          title,
            "section_number": current_section,
            "section_name":   SECTION_MAP.get(current_section, "Unknown"),
            "subcategory":    current_subcategory.strip(),
            "scope":          scope,
            "keywords":       keywords,
            "year":           year,
            "raw_text":       raw_text[:2000],
        })

        current_is_code        = ""
        current_title_lines    = []
        current_title_done     = False
        current_text_lines     = []

    # ── PDF reading ───────────────────────────────────────────────────────────

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"📄 Opened PDF: {total_pages} pages")

        with tqdm(total=total_pages, desc="Parsing pages", unit="pg", ncols=80) as pbar:
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text(
                        x_tolerance=3,
                        y_tolerance=3,
                        layout=False,
                    )
                except Exception as e:
                    tqdm.write(f"  ⚠ Skipping page {page_num + 1}: {e}")
                    pbar.update(1)
                    continue

                pbar.set_postfix({"stds": len(standards), "sec": current_section})
                pbar.update(1)

                if not text or not text.strip():
                    continue

                lines = text.split("\n")

                for line in lines:
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue

                    # ── Section header ────────────────────────────────────────
                    sec_match = SECTION_HEADER_RE.match(line_stripped)
                    if sec_match:
                        num = int(sec_match.group(1))
                        if num in SECTION_MAP and num != current_section:
                            tqdm.write(f"  📌 Section {num}: {SECTION_MAP[num]}")
                            current_section = num
                        continue

                    # Skip SP 21 headers and bare page numbers like "1.5"
                    if re.match(r"^SP\s*21\s*:\s*2005$", line_stripped):
                        continue
                    if re.match(r"^\d+\.\d+$", line_stripped):
                        continue

                    # ── SUMMARY OF trigger ────────────────────────────────────
                    if SUMMARY_RE.search(line_stripped):
                        in_summary        = True
                        pending_is_number = ""
                        continue

                    # ── Inside summary block ──────────────────────────────────
                    if in_summary:

                        # Case 1: Full IS code with year
                        code_match = IS_CODE_EXTRACT_RE.search(line_stripped)
                        if code_match:
                            flush_standard()
                            current_is_code = code_match.group(1)
                            after = line_stripped[code_match.end():].strip()
                            if after and not REVISION_RE.match(after):
                                current_title_lines = [after]
                            in_summary         = False
                            pending_is_number  = ""
                            current_text_lines = [line_stripped]
                            continue

                        # Case 2: Bare "IS XXXX" — nothing after the number
                        bare_match = IS_NUMBER_ONLY_RE.match(line_stripped)
                        if bare_match:
                            pending_is_number = bare_match.group(1)
                            continue

                        # Case 3: "IS 1489 : Portland..." — colon but no year
                        no_year_match = IS_CODE_NO_YEAR_RE.match(line_stripped)
                        if no_year_match:
                            pending_is_number = no_year_match.group(1)
                            continue

                        # Case 4: "(Part N) : YYYY" continuation
                        if pending_is_number:
                            part_match = IS_PART_CONTINUATION_RE.match(line_stripped)
                            if part_match:
                                flush_standard()
                                current_is_code   = f"{pending_is_number} {part_match.group(1)}"
                                pending_is_number = ""
                                in_summary        = False
                                current_text_lines = [current_is_code]
                                continue

                        continue

                    # ── Multi-line title collection ───────────────────────────
                    if current_is_code and not current_title_done:
                        if (CLAUSE_START_RE.match(line_stripped)
                                or REVISION_RE.match(line_stripped)):
                            current_title_done = True
                            current_text_lines.append(line_stripped)
                        elif IS_CODE_EXTRACT_RE.search(line_stripped):
                            current_title_done = True
                            current_text_lines.append(line_stripped)
                        else:
                            current_title_lines.append(line_stripped)
                            current_text_lines.append(line_stripped)
                        continue

                    # ── Sub-category detection ────────────────────────────────
                    if not current_is_code:
                        if (
                            SUBCATEGORY_RE.match(line_stripped)
                            and 3 < len(line_stripped) < 60
                            and not IS_CODE_EXTRACT_RE.search(line_stripped)
                        ):
                            current_subcategory = line_stripped.title()
                            tqdm.write(f"  📂 [{current_section}] {current_subcategory}")
                        continue

                    # ── End of standard ───────────────────────────────────────
                    if END_OF_STANDARD_RE.search(line_stripped):
                        current_text_lines.append(line_stripped)
                        flush_standard()
                        in_summary = False
                        continue

                    # ── Accumulate body text ──────────────────────────────────
                    current_text_lines.append(line_stripped)

    flush_standard()

    print(f"\n✓ Raw parse: {len(standards)} standards found")

    # ── Deduplication ─────────────────────────────────────────────────────────
    print("🔄 Deduplicating...")
    seen = {}
    for s in standards:
        seen[s["is_code"]] = s
    standards = list(seen.values())
    print(f"✓ {len(standards)} unique standards")

    # ── Save ──────────────────────────────────────────────────────────────────
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saving to {output_path}...")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(standards, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(standards)} standards")

    return standards


# ── Validation ────────────────────────────────────────────────────────────────

def validate_output(standards: list):
    print("\n── Validation ──────────────────────────────────────")

    EXPECTED = [
        "IS 269 : 1989", "IS 383 : 1970", "IS 458 : 2003",
        "IS 2185 (Part 2) : 1983", "IS 459 : 1992", "IS 455 : 1989",
        "IS 1489 (Part 2) : 1991", "IS 3466 : 1988",
        "IS 6909 : 1990", "IS 8042 : 1989"
    ]

    all_codes = {s["is_code"] for s in standards}

    print("\n  Public test set coverage:")
    all_found = True
    for code in EXPECTED:
        found = code in all_codes
        if not found:
            all_found = False
        print(f"    {'✓' if found else '✗ MISSING'}  {code}")

    if all_found:
        print("\n  ✓ All 10 public test standards found")
    else:
        print("\n  ⚠ Some missing — Part standards found:")
        part_stds = sorted(c for c in all_codes if "(Part" in c)
        for c in part_stds[:20]:
            print(f"    {c}")

    no_scope = [s["is_code"] for s in standards if not s["scope"]]
    print(f"\n  Scope coverage: {len(standards) - len(no_scope)}/{len(standards)}")
    if no_scope:
        print(f"  ⚠ Missing scope ({len(no_scope)}):")
        for c in no_scope[:10]:
            print(f"    - {c}")

    from collections import Counter
    sec_counts = Counter(s["section_number"] for s in standards)
    print(f"\n  Section distribution:")
    for sec_num in sorted(sec_counts):
        print(f"    Section {sec_num:2d} ({SECTION_MAP.get(sec_num,'?'):40s}): {sec_counts[sec_num]}")

    print("────────────────────────────────────────────────────\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA_DIR, "SP21.pdf")

    if not os.path.exists(pdf_path):
        print(f"✗ PDF not found: {pdf_path}")
        print(f"  Usage: python src/parser.py /path/to/SP21.pdf")
        sys.exit(1)

    output_path = (
        sys.argv[2] if len(sys.argv) > 2
        else os.path.join(DATA_DIR, "standards.json")
    )

    print(f"📂 PDF    : {pdf_path}")
    print(f"📂 Output : {output_path}\n")

    standards = parse_sp21(pdf_path, output_path)
    validate_output(standards)

    print("── Sample: first 3 standards ───────────────────────")
    for s in standards[:3]:
        print(json.dumps(
            {k: v for k, v in s.items() if k != "raw_text"},
            indent=2, ensure_ascii=False
        ))