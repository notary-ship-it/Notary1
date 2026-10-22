#!/usr/bin/env python3
"""Deterministic checks for a grant application package.

This is the arithmetic layer of the DMS Grant Desk, ported from the
page so it can run anywhere: a budget either foots or it does not, and
that answer should not depend on a model.

Every finding this module returns is computed. Nothing here is a
judgment call. Claude reads the same document afterwards for what
arithmetic cannot decide, and those findings are reported separately.

    python3 grant_checks.py budget BUDGET.csv --cap 10 --match 25 \
        --ceiling 500000 --floor 150000
    python3 grant_checks.py narrative NARRATIVE.txt --page-limit 30 --spacing double
"""

import argparse
import csv
import io
import json
import re
import sys

SEVERITY_ORDER = {"blocker": 0, "fix": 1, "note": 2, "clean": 3}


# ---------------------------------------------------------------- helpers

def to_num(v):
    """Parse a spreadsheet money cell. Returns None when it is not a number."""
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str):
        return None
    s = v.strip()
    if not s:
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.replace("$", "").replace(",", "").replace("(", "").replace(")", "").strip()
    s = s.rstrip("%")
    if not re.fullmatch(r"-?\d*\.?\d+", s):
        return None
    try:
        n = float(s)
    except ValueError:
        return None
    return -n if negative else n


def pct(n):
    """Percentages read as people write them: 10%, not 10.0%."""
    if n is None:
        return "—"
    return f"{n:g}%"


def money(n):
    if n is None:
        return "—"
    sign = "-$" if n < 0 else "$"
    return f"{sign}{abs(n):,.0f}" if abs(n) >= 1000 else f"{sign}{abs(n):,.2f}".rstrip("0").rstrip(".")


def parse_delimited(text):
    """Rows from CSV or TSV, blank rows dropped, cells stripped."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    if not text:
        return []
    first = text.split("\n", 1)[0]
    delim = "\t" if first.count("\t") > first.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    out = []
    for r in rows:
        cells = [c.strip() for c in r]
        if any(c for c in cells):
            out.append(cells)
    return out


def is_total_row(label):
    return bool(re.search(r"\b(total|subtotal|grand total|sum)\b", label or "", re.I))


def row_label(row):
    for cell in row:
        if cell and to_num(cell) is None:
            return cell
    return row[0] if row else "(unlabelled row)"


def numeric_columns(rows):
    """Columns where most filled data cells parse as numbers."""
    if len(rows) < 2:
        return []
    width = max(len(r) for r in rows)
    cols = []
    for c in range(width):
        filled = numeric = 0
        for r in rows[1:]:
            v = r[c] if c < len(r) else ""
            if not v:
                continue
            filled += 1
            if to_num(v) is not None:
                numeric += 1
        if filled >= 2 and numeric / filled >= 0.7:
            cols.append(c)
    return cols


def header_for(rows, c):
    if rows and c < len(rows[0]) and rows[0][c]:
        return rows[0][c]
    return f"column {c + 1}"


def find_col(rows, cols, pattern):
    for c in cols:
        if re.search(pattern, header_for(rows, c), re.I):
            return c
    return -1


def cell(rows, r, c):
    row = rows[r]
    return row[c] if 0 <= c < len(row) else ""


# ---------------------------------------------------------------- budget

def check_budget(rows, cap=None, match_pct=None, ceiling=None, floor=None,
                 match_required=None):
    out = []

    def add(sev, claim, where="", fix=""):
        out.append({"severity": sev, "claim": claim, "where": where, "fix": fix,
                    "source": "arithmetic"})

    if len(rows) < 2:
        add("note", "Not enough rows to check.", "",
            "Include the header row and one row per line item.")
        return out

    cols = numeric_columns(rows)
    if not cols:
        add("note", "No money columns found, so no arithmetic was run.", "",
            "Give each amount its own column, with a header such as "
            "Federal request, Match, Total.")
        return out

    total_col = -1
    for c in reversed(cols):
        if re.search(r"total", header_for(rows, c), re.I):
            total_col = c
            break
    fed_col = find_col(rows, cols, r"federal|request|grant|award")
    match_col = find_col(rows, cols, r"match|non-?federal|in-?kind|cost ?share|local")
    part_cols = [c for c in cols if c != total_col]

    # 1. each row's parts against its own total
    if total_col >= 0 and part_cols:
        for r in range(1, len(rows)):
            label = row_label(rows[r])
            stated = to_num(cell(rows, r, total_col))
            if stated is None:
                continue
            parts, any_part = 0.0, False
            for c in part_cols:
                v = to_num(cell(rows, r, c))
                if v is not None:
                    parts += v
                    any_part = True
            if not any_part:
                continue
            d = round(parts - stated, 2)
            if abs(d) >= 1:
                add("blocker" if is_total_row(label) else "fix",
                    "This row does not cross-foot: "
                    + " + ".join(header_for(rows, c) for c in part_cols)
                    + f" comes to {money(parts)}, but the {header_for(rows, total_col)}"
                    f" column says {money(stated)} — a difference of {money(abs(d))}.",
                    f"Row: {label}",
                    "Correct one of the two figures so the row adds up, then re-foot every column.")
            elif abs(d) > 0:
                add("note", f"Row is off by {money(abs(d))} — rounding, not an error.",
                    f"Row: {label}", "Leave it, or round consistently to whole dollars.")

    # 2. each column against its stated totals, block by block
    for c in cols:
        block = carried = 0.0
        saw_total = False
        for r in range(1, len(rows)):
            label = row_label(rows[r])
            v = to_num(cell(rows, r, c))
            if is_total_row(label):
                if v is None:
                    continue
                grand = re.search(r"grand|project|^total$", label, re.I) and saw_total
                expect = carried + block if grand else block
                d = round(expect - v, 2)
                if abs(d) >= 1:
                    add("blocker",
                        f"The {header_for(rows, c)} column does not foot to its stated total: "
                        f"the line items above add to {money(expect)}, but the row says "
                        f"{money(v)} — a difference of {money(abs(d))}.",
                        f"Row: {label} · column: {header_for(rows, c)}",
                        "Re-sum the column and correct the total. A budget that does not add "
                        "up is the most common reason a reviewer stops reading.")
                elif abs(d) > 0:
                    add("note",
                        f"The {header_for(rows, c)} column is off by {money(abs(d))} "
                        f"against {label} — rounding.",
                        f"Row: {label}", "Round consistently to whole dollars.")
                carried += v
                block = 0.0
                saw_total = True
            elif v is not None:
                block += v

    ref_col = fed_col if fed_col >= 0 else cols[0]

    # 3. a labelled percentage against the base it is drawn on
    for r in range(1, len(rows)):
        label = row_label(rows[r])
        m = re.search(r"(?:at|@)\s*([\d.]+)\s*%", label, re.I)
        if not m:
            continue
        rate = float(m.group(1))
        is_indirect = bool(re.search(r"indirect|f\s*&\s*a|overhead", label, re.I))
        is_fringe = bool(re.search(r"fringe|benefit", label, re.I))
        if not (is_indirect or is_fringe):
            continue
        mine = to_num(cell(rows, r, ref_col))
        if mine is None:
            continue
        base = 0.0
        for r2 in range(1, len(rows)):
            if r2 == r:
                continue
            l2 = row_label(rows[r2])
            if is_total_row(l2):
                continue
            text2 = l2 + " " + " ".join(rows[r2])
            if is_indirect and re.search(r"indirect|f\s*&\s*a|overhead", l2, re.I):
                continue
            if is_fringe:
                if not re.search(r"personnel|salar|wage|\bFTE\b", text2, re.I):
                    continue
                if re.search(r"travel|mileage|supplies|contractual|equipment|"
                             r"construction|indirect|rent|utilit", text2, re.I):
                    continue
            v2 = to_num(cell(rows, r2, ref_col))
            if v2 is not None:
                base += v2
        if base <= 0:
            continue
        expect = round(base * rate / 100, 2)
        if abs(round(expect - mine, 2)) >= 2:
            add("fix",
                f'"{label}" does not equal {pct(rate)} of its base: {pct(rate)} of {money(base)} '
                f"is {money(expect)}, but the row claims {money(mine)}.",
                f"Row: {label}",
                "Either correct the amount or state in the budget narrative which base "
                "the rate is applied to.")

    # 4. indirect against the notice's cap
    ind_row = -1
    for r in range(1, len(rows)):
        label = row_label(rows[r])
        if is_total_row(label):
            continue
        if re.search(r"indirect|f\s*&\s*a|overhead|administrative rate", label, re.I):
            ind_row = r
            break
    if ind_row > 0:
        ind_amt = to_num(cell(rows, ind_row, ref_col))
        direct_base = 0.0
        for r in range(1, len(rows)):
            if r == ind_row or is_total_row(row_label(rows[r])):
                continue
            v = to_num(cell(rows, r, ref_col))
            if v is not None:
                direct_base += v
        if ind_amt is not None and direct_base > 0:
            actual = round(ind_amt / direct_base * 100, 1)
            if cap is not None and actual > cap + 0.05:
                allowed = round(direct_base * cap / 100)
                add("blocker",
                    f"Indirect costs are {pct(actual)} of direct costs, above the {pct(cap)} this "
                    f"notice allows. That is {money(ind_amt - allowed)} of unallowable "
                    "indirect in the request.",
                    f"Row: {row_label(rows[ind_row])}",
                    f"Reduce indirect to {money(allowed)}, or attach a current negotiated "
                    "indirect cost rate agreement supporting the higher rate.")
            else:
                tail = (f", within the {pct(cap)} this notice allows."
                        if cap is not None
                        else ". The notice states no cap, so verify the funder's policy.")
                add("clean", f"Indirect costs are {pct(actual)} of direct costs{tail}",
                    f"Row: {row_label(rows[ind_row])}")
    elif cap is not None:
        add("note", f"No indirect cost line found. The notice allows up to {pct(cap)}.", "",
            "If the client is electing the de minimis rate, add the line and the written "
            "election statement the notice requires.")

    # 5. cost share against the requirement
    if match_col >= 0:
        match_total = fed_total = 0.0
        for r in range(1, len(rows)):
            if is_total_row(row_label(rows[r])):
                continue
            mv = to_num(cell(rows, r, match_col))
            if mv is not None:
                match_total += mv
            if fed_col >= 0:
                fv = to_num(cell(rows, r, fed_col))
                if fv is not None:
                    fed_total += fv
        project_total = match_total + fed_total
        if project_total > 0 and match_pct is not None:
            actual = round(match_total / project_total * 100, 1)
            if actual < match_pct - 0.05:
                needed = round(match_pct / 100 * fed_total / (1 - match_pct / 100))
                cut_to = round(match_total * (100 - match_pct) / match_pct)
                add("blocker",
                    f"The non-federal match is {money(match_total)}, which is {pct(actual)} of "
                    f"the {money(project_total)} total project cost. This notice requires "
                    f"{pct(match_pct)} of total approved project cost.",
                    f"Column: {header_for(rows, match_col)}",
                    f"Raise the match to about {money(needed)} against this federal request, "
                    f"or cut the federal request to {money(cut_to)}. Documented third-party "
                    "in-kind counts where the notice allows it.")
            else:
                add("clean",
                    f"The non-federal match is {pct(actual)} of total project cost, meeting the "
                    f"{pct(match_pct)} requirement.",
                    f"Column: {header_for(rows, match_col)}")
    elif match_required:
        add("blocker",
            "This notice requires a non-federal match, and the budget has no match or "
            "in-kind column.", "",
            "Add a non-federal column and document each match source in the budget narrative.")

    # 6. the federal request against ceiling and floor
    if fed_col >= 0:
        fed_ask = None
        for r in range(len(rows) - 1, 0, -1):
            if is_total_row(row_label(rows[r])):
                v = to_num(cell(rows, r, fed_col))
                if v is not None:
                    fed_ask = v
                    break
        if fed_ask is not None:
            if ceiling is not None and fed_ask > ceiling:
                add("blocker",
                    f"The federal request of {money(fed_ask)} is above this notice's award "
                    f"ceiling of {money(ceiling)}.", "Federal total",
                    "Cut the request to the ceiling or below. A request over the ceiling is "
                    "commonly rejected without review.")
            elif floor is not None and fed_ask < floor:
                add("fix",
                    f"The federal request of {money(fed_ask)} is below the award floor of "
                    f"{money(floor)}.", "Federal total",
                    "Raise the request above the floor or reconsider applying.")
            elif ceiling is not None:
                add("clean",
                    f"The federal request of {money(fed_ask)} sits inside the "
                    f"{money(floor or 0)}–{money(ceiling)} award range.", "Federal total")

    # 7. hygiene
    seen, blanks, negs = {}, [], []
    for r in range(1, len(rows)):
        label = row_label(rows[r])
        if is_total_row(label):
            continue
        key = label.lower()
        if key in seen:
            add("fix", f'Two line items share the label "{label}".', f"Row: {label}",
                "Rename one, or combine them if they are the same cost.")
        seen[key] = True
        if all(not cell(rows, r, c) for c in cols):
            blanks.append(label)
        for c in cols:
            v = to_num(cell(rows, r, c))
            if v is not None and v < 0:
                negs.append(f"{label} ({header_for(rows, c)})")
    if blanks:
        more = f" and {len(blanks) - 6} more" if len(blanks) > 6 else ""
        add("fix", "Line items with no amount in any money column: "
            + "; ".join(blanks[:6]) + more + ".", "",
            "Give every line an amount, or delete the row.")
    if negs:
        add("fix", "Negative amounts: " + "; ".join(negs[:6]) + ".", "",
            "Budgets are stated positive; show reductions in the narrative, not as "
            "negative lines.")

    return out


# ------------------------------------------------------------- narrative

def check_narrative(text, page_limit=None, spacing="double", font=None,
                    margins=None, sub_elements=None):
    out = []

    def add(sev, claim, where="", fix=""):
        out.append({"severity": sev, "claim": claim, "where": where, "fix": fix,
                    "source": "arithmetic"})

    words = len([w for w in re.split(r"\s+", text) if w])
    chars = len(text)
    per_page = 250 if re.search(r"double", spacing or "", re.I) else (
        500 if re.search(r"single", spacing or "", re.I) else 250)
    pages = -(-words // per_page) if words else 0

    add("clean",
        f"{words:,} words, {chars:,} characters — about {pages} page"
        f"{'' if pages == 1 else 's'} at {per_page} words per page"
        + (f" ({spacing.lower()})" if spacing else "") + ".")

    if page_limit is not None:
        if pages > page_limit:
            add("blocker",
                f"This runs about {pages} pages against a {page_limit}-page limit. Roughly "
                f"{(pages - page_limit) * per_page:,} words have to come out — and reviewers "
                "do not read past the limit.", "",
                f"Cut to about {page_limit * per_page:,} words, or move material the notice "
                "excludes from the count into its own attachment.")
        elif pages >= page_limit - 1:
            add("note",
                f"About {pages} pages against a {page_limit}-page limit — no room left for "
                "formatting drift.", "",
                "Leave a page of headroom; tables and headings expand once the real "
                "formatting is applied.")
        else:
            add("clean",
                f"About {pages} pages against a {page_limit}-page limit — "
                f"{page_limit - pages} pages of headroom.")

    if font or margins:
        req = ", ".join(x for x in (font, spacing, margins) if x)
        add("note", f"Formatting cannot be checked from extracted text. The notice "
            f"requires: {req}.", "",
            "Verify font, spacing, margins and page numbering in the final PDF.")

    placeholders = re.findall(r"\b(TBD|TODO|XXX+|lorem ipsum|\[insert[^\]]*\]|\[name\]|FIXME)\b",
                              text, re.I)
    if placeholders:
        uniq = sorted({p.upper() for p in placeholders})
        add("blocker", "Placeholder text is still in the draft: " + ", ".join(uniq[:6]) + ".",
            "", "Replace every placeholder. Reviewers read these as an unfinished application.")

    if sub_elements:
        low = text.lower()
        absent = []
        for se in sub_elements:
            words_in = re.findall(r"[a-z]{5,}", str(se).lower())
            if words_in and not any(w in low for w in words_in):
                absent.append(str(se))
        if absent:
            add("note",
                f"A word scan found nothing matching {len(absent)} of the "
                f"{len(sub_elements)} things this criterion asks for: "
                + "; ".join(absent[:5]) + ".", "",
                "Check each one is genuinely addressed. This is a word match, not a reading.")
    return out


# ------------------------------------------------------------------ PDF

def read_pdf_text(path):
    """Text from a PDF. Prefers pdfplumber; falls back to pypdf."""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n\n".join(pages).strip(), len(pages)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore
    reader = PdfReader(path)
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n\n".join(pages).strip(), len(pages)


# ------------------------------------------------------------------ CLI

def sort_findings(findings):
    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(f["severity"], 2))


def render(findings):
    labels = {"blocker": "BLOCKER", "fix": "FIX", "note": "NOTE", "clean": "OK"}
    lines = []
    for f in sort_findings(findings):
        lines.append(f"[{labels.get(f['severity'], 'NOTE')}] {f['claim']}")
        if f.get("where"):
            lines.append(f"         where: {f['where']}")
        if f.get("fix"):
            lines.append(f"         do: {f['fix']}")
        lines.append("")
    blockers = sum(1 for f in findings if f["severity"] == "blocker")
    fixes = sum(1 for f in findings if f["severity"] == "fix")
    lines.append(f"{blockers} blocker(s), {fixes} fix(es).")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    b = sub.add_parser("budget", help="check a budget spreadsheet (.csv/.tsv)")
    b.add_argument("path")
    b.add_argument("--cap", type=float, default=None, help="indirect cost cap, percent")
    b.add_argument("--match", type=float, default=None, help="required match, percent")
    b.add_argument("--match-required", action="store_true")
    b.add_argument("--ceiling", type=float, default=None)
    b.add_argument("--floor", type=float, default=None)

    n = sub.add_parser("narrative", help="check a narrative (.txt/.md/.pdf)")
    n.add_argument("path")
    n.add_argument("--page-limit", type=int, default=None)
    n.add_argument("--spacing", default="double")
    n.add_argument("--font", default=None)
    n.add_argument("--margins", default=None)
    n.add_argument("--sub-element", action="append", dest="sub_elements", default=None)

    p = sub.add_parser("pdf", help="extract text from a PDF")
    p.add_argument("path")

    for parser in (b, n, p):
        parser.add_argument("--json", action="store_true", help="emit JSON")

    a = ap.parse_args(argv)

    if a.mode == "pdf":
        text, pages = read_pdf_text(a.path)
        words = len([w for w in re.split(r"\s+", text) if w])
        if a.json:
            print(json.dumps({"pages": pages, "words": words, "text": text}))
        else:
            if words < 20:
                print(f"Read {pages} page(s) but found only {words} words — this is very "
                      "likely a scanned PDF. Run OCR first.", file=sys.stderr)
            print(text)
        return 0

    if a.mode == "budget":
        rows = parse_delimited(open(a.path, encoding="utf-8-sig").read())
        findings = check_budget(rows, cap=a.cap, match_pct=a.match, ceiling=a.ceiling,
                                floor=a.floor, match_required=a.match_required)
    else:
        if a.path.lower().endswith(".pdf"):
            text, _ = read_pdf_text(a.path)
        else:
            text = open(a.path, encoding="utf-8-sig").read()
        findings = check_narrative(text, page_limit=a.page_limit, spacing=a.spacing,
                                   font=a.font, margins=a.margins,
                                   sub_elements=a.sub_elements)

    print(json.dumps(sort_findings(findings), indent=2) if a.json else render(findings))
    return 1 if any(f["severity"] == "blocker" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
