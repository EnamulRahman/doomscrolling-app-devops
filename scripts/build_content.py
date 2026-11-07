#!/usr/bin/env python3
"""Build the app's data files from the hand-written content in content/.

  content/learn/*.md      → data/curriculum.js   (modules → lessons → cards, with diagrams and checks)
  content/quiz/*.md       → data/mcq.js          (multiple-choice quiz bank; lesson checks are added too)
  content/scenarios/*.md  → data/scen.js         (multiple-choice interview scenarios)
  content/lab.md          → data/lab.js          (the step-by-step build of the Memos project)

Content format (see content/README.md for the full guide):
  ```mermaid fences  → diagrams     ```lang file=path fences → code with a filename
  ? question / - [ ] wrong / - [x] right / "  > why" per option / "> explanation"
  $ command + ```output fence → an interactive terminal step (lab only)

usage: build_content.py
"""
import glob, html, json, os, re, sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*$", re.M | re.S)
errors = []


def md(text):
    h = markdown.markdown(text.strip(), extensions=["tables", "sane_lists"], tab_length=2)
    h = re.sub(r"<a (?![^>]*target=)", '<a target="_blank" rel="noopener" ', h)
    return h


def segments(text):
    """Split markdown into blocks: html, diagram (mermaid) and code (with optional file name)."""
    out, pos = [], 0
    for m in FENCE.finditer(text):
        before = text[pos:m.start()]
        if before.strip():
            out.append({"type": "html", "html": md(before)})
        info, body = m.group(1).strip(), m.group(2).rstrip("\n")
        lang = info.split()[0] if info else ""
        fm = re.search(r"file=(\S+)", info)
        if lang == "mermaid":
            cap = re.search(r'caption="([^"]+)"', info)
            out.append({"type": "diagram", "code": body, **({"caption": cap.group(1)} if cap else {})})
        elif lang == "output":
            out.append({"type": "output", "text": body})
        else:
            blk = {"type": "code", "lang": lang, "code": body}
            if fm:
                blk["file"] = fm.group(1)
            out.append(blk)
        pos = m.end()
    rest = text[pos:]
    if rest.strip():
        out.append({"type": "html", "html": md(rest)})
    return out


def parse_meta(line):
    """'@ topic: Linux · level: Beginner' → dict"""
    meta = {}
    for part in re.split(r"\s*·\s*|\s*\|\s*", line.lstrip("@").strip()):
        if ":" in part:
            k, v = part.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta


def parse_mcq(lines, where):
    """lines start at '? ...'. Returns question dict."""
    i, n = 0, len(lines)
    qlines = [lines[0][2:]]
    i = 1
    in_fence = False
    while i < n:
        l = lines[i]
        if l.startswith("```"):
            in_fence = not in_fence
        if not in_fence and re.match(r"^- \[( |x|X)\] ", l):
            break
        qlines.append(l)
        i += 1
    opts = []
    while i < n and re.match(r"^- \[( |x|X)\] ", lines[i]):
        ok = lines[i][3] in "xX"
        opt = {"t": md(lines[i][6:]).removeprefix("<p>").removesuffix("</p>"), "ok": ok}
        i += 1
        why = []
        while i < n and re.match(r"^\s{2,}(> ?|\S)", lines[i]) and lines[i].strip():
            why.append(re.sub(r"^\s{2,}> ?", "", lines[i]).rstrip())
            i += 1
        if why:
            opt["why"] = md("\n".join(why))
        opts.append(opt)
    explain = []
    while i < n:
        l = lines[i]
        if l.startswith(">"):
            explain.append(l[1:].lstrip() if l.startswith("> ") else l[1:])
        elif l.strip() and not l.startswith("@"):
            explain.append(l)
        i += 1
    q = {"q": segments("\n".join(qlines)), "options": opts}
    if explain:
        q["explain"] = md("\n".join(explain))
    if sum(o["ok"] for o in opts) != 1 or len(opts) < 2:
        errors.append(f"{where}: question needs ≥2 options and exactly one [x]: {qlines[0][:60]}")
    return q


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def split_on(text, prefix):
    """Split text into (title, body) chunks on lines starting with prefix (outside code fences)."""
    chunks, cur_title, cur, in_fence = [], None, [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith(prefix) and not line.startswith(prefix + "#"):
            if cur_title is not None or "".join(cur).strip():
                chunks.append((cur_title, "\n".join(cur)))
            cur_title, cur = line[len(prefix):].strip(), []
        else:
            cur.append(line)
    if cur_title is not None or "".join(cur).strip():
        chunks.append((cur_title, "\n".join(cur)))
    return chunks


def mcqs_in(text, where, defaults):
    """Every '? ' question in a block of text (questions separated by the next '? ' or '@ ' line)."""
    out, lines, start, meta = [], text.split("\n"), None, {}
    in_fence = False
    pending_meta = {}
    blocks = []
    for idx, l in enumerate(lines):
        if l.startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        if l.startswith("@ "):
            if start is not None:
                blocks.append((start, idx, meta)); start = None
            pending_meta = parse_meta(l)
        elif l.startswith("? "):
            if start is not None:
                blocks.append((start, idx, meta))
            start, meta, pending_meta = idx, pending_meta, {}
    if start is not None:
        blocks.append((start, len(lines), meta))
    for s, e, meta in blocks:
        q = parse_mcq([l for l in lines[s:e]], where)
        q.update({**defaults, **meta})
        out.append(q)
    return out


# ---------------------------------------------------------------- learn
def build_learn():
    modules, checks = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "learn", "*.md"))):
        meta, body = split_frontmatter(open(path, encoding="utf-8").read())
        mod = {"id": meta.get("id") or os.path.basename(path)[3:-3], "title": meta.get("title", ""),
               "level": meta.get("level", "Beginner"), "icon": meta.get("icon", "📘"),
               "summary": meta.get("summary", ""), "topic": meta.get("topic", meta.get("title", "")),
               "lessons": []}
        for ltitle, lbody in split_on(body, "## "):
            if ltitle is None:
                continue
            lesson = {"title": ltitle, "cards": []}
            for ctitle, cbody in split_on(lbody, "### "):
                if ctitle is None:
                    continue
                if ctitle.lower().startswith("check"):
                    for q in mcqs_in(cbody, f"{path}:{ltitle}", {"topic": mod["topic"], "source": "Lesson check",
                                                                  "level": mod["level"]}):
                        lesson["cards"].append({"type": "check", "title": "Quick check", "mcq": q})
                        checks.append(q)
                else:
                    lesson["cards"].append({"type": "card", "title": ctitle, "blocks": segments(cbody)})
            mod["lessons"].append(lesson)
        modules.append(mod)
    return modules, checks


# ---------------------------------------------------------------- quiz
def build_quiz():
    qs = []
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "quiz", "*.md"))):
        meta, body = split_frontmatter(open(path, encoding="utf-8").read())
        qs += mcqs_in(body, path, {"topic": meta.get("topic", ""), "source": meta.get("source", ""),
                                   "level": meta.get("level", "Beginner")})
    return qs


# ---------------------------------------------------------------- scenarios
def build_scenarios():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "scenarios", "*.md"))):
        fmeta, body = split_frontmatter(open(path, encoding="utf-8").read())
        for title, chunk in split_on(body, "## "):
            if title is None:
                continue
            lines = chunk.strip("\n").split("\n")
            meta = dict(fmeta)
            if lines and lines[0].startswith("@ "):
                meta.update(parse_meta(lines.pop(0)))
            qi = next((i for i, l in enumerate(lines) if l.startswith("? ")), None)
            if qi is None:
                errors.append(f"{path}: scenario '{title}' has no question")
                continue
            situation = segments("\n".join(lines[:qi]))
            q = parse_mcq(lines[qi:], f"{path}:{title}")
            files = [f.strip() for f in meta.pop("files", "").split(",") if f.strip()]
            out.append({"title": title, "situation": situation, **q, "topic": meta.get("topic", ""),
                        "level": meta.get("level", ""), "source": meta.get("source", ""),
                        "links": [{"label": f} for f in files]})
    return out


# ---------------------------------------------------------------- lab
def build_lab():
    path = os.path.join(ROOT, "content", "lab.md")
    if not os.path.exists(path):
        return []
    stages = []
    for stitle, sbody in split_on(open(path, encoding="utf-8").read(), "# "):
        if stitle is None:
            continue
        lines = sbody.strip("\n").split("\n")
        meta = parse_meta(lines.pop(0)) if lines and lines[0].startswith("@ ") else {}
        chunks = split_on("\n".join(lines), "## ")
        intro = chunks[0][1] if chunks and chunks[0][0] is None else ""
        stage = {"title": stitle, "icon": meta.get("icon", "🧱"), "time": meta.get("time", ""),
                 "intro": segments(intro), "steps": []}
        for title, body in chunks:
            if title is None:
                continue
            step = {"title": title, "blocks": []}
            text, buf, in_fence = body.split("\n"), [], False
            i = 0
            while i < len(text):
                l = text[i]
                if l.startswith("```"):
                    in_fence = not in_fence
                if not in_fence and l.startswith("? "):
                    if "\n".join(buf).strip():
                        step["blocks"] += segments("\n".join(buf))
                    buf = []
                    step["blocks"].append({"type": "check", "mcq": parse_mcq(text[i:], f"lab:{title}")})
                    break
                if not in_fence and l.startswith("$ "):
                    if "\n".join(buf).strip():
                        step["blocks"] += segments("\n".join(buf))
                    buf = []
                    term = {"type": "term", "cmd": l[2:].strip()}
                    # an ```output fence straight after belongs to this command
                    j = i + 1
                    if j < len(text) and text[j].startswith("```output"):
                        k = j + 1
                        while k < len(text) and not text[k].startswith("```"):
                            k += 1
                        term["output"] = "\n".join(text[j + 1:k])
                        i = k
                    step["blocks"].append(term)
                else:
                    buf.append(l)
                i += 1
            if "\n".join(buf).strip():
                step["blocks"] += segments("\n".join(buf))
            stage["steps"].append(step)
        stages.append(stage)
    return stages


def write(name, var, data):
    with open(os.path.join(ROOT, "data", name), "w", encoding="utf-8") as f:
        f.write("// Generated by scripts/build_content.py from content/ — edit those files, not this one.\n")
        f.write(f"window.{var} = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))};\n")


def main():
    modules, checks = build_learn()
    quiz = build_quiz()
    scen = build_scenarios()
    lab = build_lab()
    # every lesson check also lives in the quiz bank
    for q in checks:
        q["fromLesson"] = True
    pool = quiz + checks  # same objects, so lesson cards and the quiz share ids
    for i, q in enumerate(pool):
        q["id"] = "m" + str(i) + "-" + re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", json.dumps(q["q"]))[:80].lower())[:30]
    for i, s in enumerate(scen):
        s["id"] = "s" + str(i) + "-" + re.sub(r"[^a-z0-9]+", "-", s["title"].lower())[:30]
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    write("curriculum.js", "CURRICULUM", modules)
    write("mcq.js", "MCQ", pool)
    write("scen.js", "SCEN", scen)
    write("lab.js", "LAB", lab)
    cards = sum(len(l["cards"]) for m in modules for l in m["lessons"])
    diagrams = json.dumps([modules, scen, lab, pool], separators=(',', ':')).count('"type":"diagram"')
    print(f"learn: {len(modules)} modules · {sum(len(m['lessons']) for m in modules)} lessons · {cards} cards · {len(checks)} checks")
    print(f"quiz: {len(pool)} questions ({len(quiz)} bank + {len(checks)} lesson checks)")
    print(f"scenarios: {len(scen)} · lab: {len(lab)} stages, {sum(len(s['steps']) for s in lab)} steps · diagrams: {diagrams}")
    if errors:
        print("\nPROBLEMS:", *errors, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
