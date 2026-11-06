#!/usr/bin/env python3
"""Turn one of the revision-guide PDFs into structured JSON (parts > sections > subsections > blocks).

The guides were printed from HTML by Chromium, so structure is recoverable from font sizes:
  20pt part · 14.5pt section/chapter · 11pt subsection · 9.6pt body · 8.6pt table · mono = code.
Bold comes from pdfplumber's font names (PyMuPDF only sees Type3 fonts); text comes from PyMuPDF,
which decodes every glyph correctly.

usage: extract_guide.py GUIDE.pdf OUT.json
"""
import html, json, logging, re, sys

import pdfplumber
import pymupdf

logging.disable(logging.WARNING)

PART, H1, H2, BODY_MIN, TABLE, FOOTER = 20.0, 14.5, 11.0, 9.0, 8.6, 7.5
RECALL_FILL = (1.0, 0.97, 0.88)
CODE_FILL = (0.96, 0.96, 0.98)
LIST_MARK = re.compile(r"^(\d+)\.\s+")
CALLOUT = {"⚡": "recall", "⚠": "warn", "🔧": "memos", "🧠": "memorise", "🔗": "link"}
PARA_GAP = 14.6  # line gap above which a new paragraph or list item starts


def close(a, b, tol=0.6):
    return abs(a - b) <= tol


def fill_key(f):
    return tuple(round(c, 2) for c in f) if f else None


def bold_lookup(plumber_page):
    chars = [(c["x0"], c["x1"], c["top"], c["bottom"], "Bold" in c["fontname"] or "ExtraBold" in c["fontname"])
             for c in plumber_page.chars]

    def is_bold(bbox):
        x0, y0, x1, y1 = bbox
        hits = [b for (cx0, cx1, ct, cb, b) in chars
                if cx0 >= x0 - 1 and cx1 <= x1 + 1 and (ct + cb) / 2 >= y0 - 2 and (ct + cb) / 2 <= y1 + 2]
        return bool(hits) and sum(hits) > len(hits) / 2
    return is_bold


def span_html(span, is_bold):
    text = span["text"]
    if not text:
        return ""
    esc = html.escape(text, quote=False)
    if "Mono" in span["font"]:
        return f"<code>{esc}</code>"
    if text.strip() and is_bold(span["bbox"]):
        return f"<b>{esc}</b>"
    return esc


def merge_tags(h):
    # Adjacent spans of the same style come out as </b><b>; join them.
    h = re.sub(r"</b>(\s*)<b>", r"\1", h)
    h = re.sub(r"</code><code>", "", h)
    return h


def read_lines(pdf_path):
    doc = pymupdf.open(pdf_path)
    plumber = pdfplumber.open(pdf_path)
    out = []
    for pno, page in enumerate(doc):
        is_bold = bold_lookup(plumber.pages[pno])
        boxes = []
        for d in page.get_drawings():
            r, f = d["rect"], fill_key(d.get("fill"))
            if f == RECALL_FILL and r.height > 20:
                boxes.append(("recall", r))
            elif f == CODE_FILL and r.height > 14 and r.width > 150:
                boxes.append(("code", r))
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"]]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans)
                if not text.strip():
                    continue
                x0, y0, x1, y1 = line["bbox"]
                # Position lines by baseline: inline-code backgrounds make bboxes taller than the text.
                base = next(sp["origin"][1] for sp in spans if sp["text"].strip())
                size = max(s["size"] for s in spans if s["text"].strip()) if text.strip() else spans[0]["size"]
                first = next(s for s in spans if s["text"].strip())
                container = None
                for kind, r in boxes:
                    if r.x0 - 2 <= x0 and x1 <= r.x1 + 2 and r.y0 - 2 <= y0 and y1 <= r.y1 + 2:
                        container = (kind, round(r.y0, 1), pno)
                mono = all("Mono" in s["font"] for s in spans if s["text"].strip())
                out.append(dict(page=pno, x0=x0, top=base, bottom=y1, size=round(size, 1), text=text,
                                html=merge_tags("".join(span_html(s, is_bold) for s in spans)),
                                bold=is_bold(first["bbox"]), mono=mono, container=container))
    # Sort into reading order: PyMuPDF blocks are mostly ordered, but table cells come out per block.
    out.sort(key=lambda l: (l["page"], round(l["top"]), l["x0"]))
    return out, len(doc)


class Builder:
    def __init__(self):
        self.parts, self.part, self.section, self.sub = [], None, None, None
        self.cur = None          # current text block being extended
        self.table = None        # current table being built
        self.code = None         # current code block
        self.last = None         # last body line placed
        self.callout = None      # (key, block) for recall boxes

    # ----- structure -----
    def new_part(self, title):
        self.flush()
        self.part = {"title": title, "sections": []}
        self.parts.append(self.part)
        self.section = self.sub = None

    def new_section(self, title):
        self.flush()
        if self.part is None:
            self.new_part("")
        self.section = {"title": title, "subsections": []}
        self.part["sections"].append(self.section)
        self.sub = None

    def new_sub(self, title):
        self.flush()
        if self.section is None:
            self.new_section("")
        self.sub = {"title": title, "blocks": []}
        self.section["subsections"].append(self.sub)

    def blocks(self):
        if self.sub is None:
            self.new_sub("")
        return self.sub["blocks"]

    def flush(self):
        self.cur = self.table = self.code = self.last = self.callout = None

    # ----- content -----
    def target(self, line):
        """Where body content goes: a recall box's own block list or the subsection."""
        c = line["container"]
        if c and c[0] == "recall":
            if not self.callout or self.callout[0] != c:
                box = {"type": "callout", "kind": "recall", "blocks": []}
                self.blocks().append(box)
                self.callout = (c, box)
                self.cur = self.last = None
            return self.callout[1]["blocks"]
        if self.callout:
            self.callout = None
            self.cur = self.last = None
        return self.blocks()

    def add_code(self, line):
        self.cur = self.table = None
        dest = self.target(line)
        if self.code is None or self.code["dest"] is not dest or line["top"] - self.code["last_top"] > 16 \
                and line["page"] == self.code["page"]:
            blk = {"type": "pre", "lines": []}
            dest.append(blk)
            self.code = {"blk": blk, "dest": dest, "minx": line["x0"], "last_top": line["top"], "page": line["page"]}
        c = self.code
        c["minx"] = min(c["minx"], line["x0"])
        c["blk"]["lines"].append((line["x0"], line["text"].rstrip(), line["size"]))
        c["last_top"], c["page"] = line["top"], line["page"]
        self.last = line

    def add_table_line(self, line):
        self.cur = self.code = None
        dest = self.target(line)
        t = self.table
        if t is None or t["dest"] is not dest:
            blk = {"type": "table", "cells": []}
            dest.append(blk)
            t = self.table = {"blk": blk, "dest": dest, "row_top": None, "last_top": None, "page": line["page"]}
        new_page = line["page"] != t["page"]
        if t["row_top"] is None or (not new_page and line["top"] - t["last_top"] > 16.5 and
                                     not close(line["top"], t["last_top"], 2)) or new_page and t["last_top"] is not None:
            if not (t["last_top"] is not None and close(line["top"], t["last_top"], 2) and not new_page):
                t["blk"]["cells"].append([])
                t["row_top"] = line["top"]
        t["blk"]["cells"][-1].append((line["x0"], line["html"], line["bold"]))
        t["last_top"], t["page"] = line["top"], line["page"]
        self.last = line

    def add_body(self, line, margin):
        self.table = self.code = None
        dest = self.target(line)
        text = line["text"].strip()
        prev = self.last
        same_flow = (prev is not None and self.cur is not None and self.cur in dest)
        if same_flow:
            if prev["page"] == line["page"]:
                gap = line["top"] - prev["top"]
                same_flow = gap <= PARA_GAP and line["x0"] >= self.cur["_x"] - 1
            else:  # page break: continue only if the sentence clearly runs on
                same_flow = (not LIST_MARK.match(text) and text[:1] not in CALLOUT
                             and (text[:1].islower() or not re.search(r"[.:!?”\"]$", prev["text"].strip())))
        h = line["html"].strip()
        if same_flow and not LIST_MARK.match(text):
            sep = "" if self.cur["html"].endswith("-") else " "
            self.cur["html"] += sep + h
        else:
            m = LIST_MARK.match(text)
            emoji = text[:1]
            if m:
                h = LIST_MARK.sub("", h, count=1) if LIST_MARK.match(h) else re.sub(r"^\d+\.\s+", "", h)
                blk = {"type": "li", "ordered": True, "n": int(m.group(1)), "html": h}
            elif emoji in CALLOUT and not line["container"]:
                blk = {"type": "note", "kind": CALLOUT[emoji], "html": h}
            elif line["x0"] > margin + 8:
                blk = {"type": "li", "ordered": False, "html": h}
            else:
                blk = {"type": "p", "html": h}
            blk["_x"] = line["x0"]
            dest.append(blk)
            self.cur = blk
        self.last = line


def build(pdf_path):
    lines, npages = read_lines(pdf_path)
    b = Builder()
    started = False
    for i, l in enumerate(lines):
        s, text = l["size"], l["text"].strip()
        if s <= FOOTER + 0.1 and l["top"] > 780:
            continue  # page footer
        if close(s, PART, 1):
            started = True
            prev = lines[i - 1] if i else None
            if prev and close(prev["size"], PART, 1) and prev["page"] == l["page"] and b.part \
                    and not b.part["sections"]:
                b.part["title"] += " " + re.sub(r"\s+", " ", text)  # heading wrapped onto two lines
            else:
                b.new_part(re.sub(r"\s+", " ", text))
            continue
        if not started:
            # Title page and contents come before the first part heading, except the AWS guide's
            # intro pages which open with 20pt headings too (handled above).
            continue
        if close(s, H1, 0.8):
            prev = lines[i - 1] if i else None
            if prev and close(prev["size"], H1, 0.8) and prev["page"] == l["page"] \
                    and l["top"] - prev["top"] < 24 and b.section and not b.section["subsections"]:
                b.section["title"] += ("" if b.section["title"].endswith("-") else " ") + re.sub(r"\s+", " ", text)  # long title wrapped
            else:
                b.new_section(re.sub(r"\s+", " ", text))
        elif close(s, H2, 0.5) and l["bold"]:
            b.new_sub(re.sub(r"\s+", " ", text))
        elif l["mono"] and l["container"] and l["container"][0] == "code":
            b.add_code(l)
        elif close(s, TABLE, 0.3):
            b.add_table_line(l)
        elif s >= BODY_MIN:
            margin = 42.8
            if l["container"] and l["container"][0] == "recall":
                margin = 57.1
            b.add_body(l, margin)
        else:
            b.add_body(l, 42.8)
    return finalize(b.parts)


def finalize(parts):
    def fix(blocks):
        out = []
        for blk in blocks:
            blk.pop("_x", None)
            t = blk["type"]
            if t == "pre":
                minx = min(x for x, _, _ in blk["lines"])
                rows = []
                for x, txt, size in blk["lines"]:
                    indent = int(round((x - minx) / (size * 0.6)))
                    rows.append(" " * indent + txt)
                blk = {"type": "pre", "text": "\n".join(rows)}
            elif t == "table":
                xs = sorted({round(x) for row in blk["cells"] for x, _, _ in row})
                cols = []
                for x in xs:  # cluster column starts
                    if not cols or x - cols[-1] > 12:
                        cols.append(x)
                rows = []
                for row in blk["cells"]:
                    r = [""] * len(cols)
                    for x, h, _ in sorted(row, key=lambda c: c[0]):
                        ci = max(i for i, c in enumerate(cols) if c <= round(x) + 12)
                        r[ci] = (r[ci] + " " + h).strip() if r[ci] else h
                    rows.append(r)
                head = bool(blk["cells"]) and all(bd for _, _, bd in blk["cells"][0])
                blk = {"type": "table", "head": head, "rows": rows}
            elif t == "callout":
                blk["blocks"] = fix(blk["blocks"])
            out.append(blk)
        # group consecutive list items
        grouped = []
        for blk in out:
            if blk["type"] == "li":
                if grouped and grouped[-1]["type"] == "list" and grouped[-1]["ordered"] == blk["ordered"]:
                    grouped[-1]["items"].append(blk["html"])
                else:
                    grouped.append({"type": "list", "ordered": blk["ordered"], "start": blk.get("n", 1),
                                    "items": [blk["html"]]})
            else:
                grouped.append(blk)
        return grouped

    for p in parts:
        for s in p["sections"]:
            for sub in s["subsections"]:
                sub["blocks"] = fix(sub["blocks"])
    return parts


if __name__ == "__main__":
    parts = build(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(parts, f, ensure_ascii=False, indent=1)
    for p in parts:
        print(f"[{p['title']}]")
        for s in p["sections"]:
            print(f"   {s['title']}  ({len(s['subsections'])} subsections)")
