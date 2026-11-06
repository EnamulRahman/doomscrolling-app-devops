#!/usr/bin/env python3
"""Build the guides reference library (data/learn.js) from the two revision-guide PDFs.

Originally this built every content file from:

  - the DevOps Revision Guide and AWS From Zero PDFs (via extract_guide.py)
  - the tech-vault interview question bank (github.com/moabukar/tech-vault, Apache-2.0)
  - content/memos-scenarios.md (hand-written scenarios about the memos-aws-infra project)

usage: build_data.py DEVOPS_GUIDE.pdf AWS_GUIDE.pdf TECH_VAULT_DIR
"""
import difflib, html, json, os, re, sys

import markdown

sys.path.insert(0, os.path.dirname(__file__))
from extract_guide import build as extract  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/EnamulRahman/memos-aws-infra/blob/main/"
TECH_VAULT = "https://github.com/moabukar/tech-vault"
CARD_BUDGET = 640  # rough "characters" that fit one phone screen (iPhone-sized)

# ---------------------------------------------------------------- helpers

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", s).lower()).strip("-")[:60]


def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h))


def clean_title(t):
    return re.sub(r"\s*[🧠⚠️⚡🔧]+\s*", " ", t).replace("️", "").strip()


def weight(blk):
    t = blk["type"]
    if t == "p" or t == "note":
        return len(text_of(blk["html"])) + 60
    if t == "list":
        return sum(len(text_of(i)) + 30 for i in blk["items"]) + 20
    if t == "table":
        return sum(max(60, sum(len(text_of(c)) for c in r) * 1.4) for r in blk["rows"]) + 40
    if t == "pre":
        return len(blk["text"].splitlines()) * 55 + 30
    if t == "callout":
        return sum(weight(b) for b in blk["blocks"]) + 60
    return 100


def split_block(blk, budget):
    """Split one oversized list/table into pieces that each fit a card."""
    if blk["type"] == "list":
        pieces, cur, w, start = [], [], 0, blk.get("start", 1)
        for it in blk["items"]:
            iw = len(text_of(it)) + 30
            if cur and w + iw > budget:
                pieces.append({**blk, "items": cur, "start": start})
                start += len(cur)
                cur, w = [], 0
            cur.append(it)
            w += iw
        pieces.append({**blk, "items": cur, "start": start})
        return pieces
    if blk["type"] == "table":
        head = blk["rows"][0] if blk.get("head") else None
        body = blk["rows"][1:] if head else blk["rows"]
        pieces, cur, w = [], [], 0
        for r in body:
            rw = max(60, sum(len(text_of(c)) for c in r) * 1.4)
            if cur and w + rw > budget:
                pieces.append({**blk, "rows": ([head] if head else []) + cur})
                cur, w = [], 0
            cur.append(r)
            w += rw
        pieces.append({**blk, "rows": ([head] if head else []) + cur})
        return pieces
    if blk["type"] == "callout" and weight(blk) > budget:
        return [{**blk, "blocks": part} for part in paginate(blk["blocks"], budget - 60)]
    return [blk]


def paginate(blocks, budget=CARD_BUDGET):
    pages, cur, w = [], [], 0
    for blk in blocks:
        for piece in (split_block(blk, budget) if weight(blk) > budget else [blk]):
            pw = weight(piece)
            if cur and w + pw > budget:
                pages.append(cur)
                cur, w = [], 0
            cur.append(piece)
            w += pw
    if cur:
        pages.append(cur)
    return pages


def dedupe_table_headers(blocks):
    """Tables that ran over a page repeat their header row mid-table; drop the repeats."""
    for blk in blocks:
        if blk["type"] == "table" and blk.get("head") and blk["rows"]:
            h = blk["rows"][0]
            blk["rows"] = [h] + [r for r in blk["rows"][1:] if r != h]
        elif blk["type"] == "callout":
            dedupe_table_headers(blk["blocks"])
    # merge a table that was split by a page break into the previous one
    out = []
    for blk in blocks:
        if (blk["type"] == "table" and out and out[-1]["type"] == "table"
                and len(blk["rows"][0]) == len(out[-1]["rows"][0])):
            rows = blk["rows"][1:] if blk.get("head") and blk["rows"][0] == out[-1]["rows"][0] else blk["rows"]
            out[-1]["rows"] += rows
        else:
            out.append(blk)
    return out


# Repo files that each Learn module maps onto, for the "In your repo" links.
REPO_LINKS = [
    (r"\bdocker\b|container", [("Dockerfile", "Dockerfile (3 stages)"), ("Dockerfile.single-stage", "Dockerfile.single-stage")]),
    (r"\bvpc\b|network", [("infra/modules/vpc/main.tf", "modules/vpc"), ("infra/modules/security/main.tf", "modules/security")]),
    (r"iam|identity", [("infra/modules/iam/main.tf", "modules/iam"), ("bootstrap/oidc.tf", "bootstrap/oidc.tf")]),
    (r"load balanc|dns|route 53|certificat", [("infra/modules/alb/main.tf", "modules/alb"), ("infra/modules/acm/main.tf", "modules/acm"), ("infra/main.tf", "infra/main.tf (Route 53 record)")]),
    (r"terraform|infrastructure as code", [("infra/main.tf", "infra/main.tf"), ("infra/provider.tf", "infra/provider.tf (S3 backend)"), ("bootstrap/state.tf", "bootstrap/state.tf")]),
    (r"ci/cd|github actions", [(".github/workflows/build.yml", "build.yml"), (".github/workflows/deploy.yml", "deploy.yml"), (".github/workflows/destroy.yml", "destroy.yml")]),
    (r"containers on aws|containers and serverless|ecs", [("infra/modules/ecs/main.tf", "modules/ecs"), ("infra/modules/ecr/main.tf", "modules/ecr")]),
    (r"cloudwatch|monitoring|troubleshoot", [("infra/modules/ecs/main.tf", "modules/ecs (log group, 7-day retention)")]),
    (r"s3\b|storage", [("bootstrap/state.tf", "bootstrap/state.tf (state bucket)")]),
    (r"memos project", [("README.md", "README"), ("infra/main.tf", "infra/main.tf")]),
]


def repo_links(title):
    seen, out = set(), []
    for pat, links in REPO_LINKS:
        if re.search(pat, title, re.I):
            for path, label in links:
                if path not in seen:
                    seen.add(path)
                    out.append({"href": REPO + path, "label": label})
    return out[:4]


# ---------------------------------------------------------------- Learn

DEVOPS_SKIP = re.compile(r"^(0\.|15\.|18\.)")  # how-to-use, Q&A list (→ quiz), glossary (→ quiz)
AWS_SKIP = re.compile(r"^(How to use|Check yourself|Glossary|Interview practice)")


def learn_modules(guide_parts, guide_id, guide_title, skip):
    modules = []
    for part in guide_parts:
        ptitle = part["title"]
        if guide_id == "devops" and not ptitle.upper().startswith("PART 1"):
            continue
        if guide_id == "aws" and ptitle.startswith("Answer key"):
            continue
        for sec in part["sections"]:
            title = sec["title"] or ptitle
            if skip.match(title):
                continue
            cards = []
            for sub in sec["subsections"]:
                blocks = dedupe_table_headers(sub["blocks"])
                if not blocks:
                    continue
                pages = paginate(blocks)
                for i, page in enumerate(pages):
                    cards.append({"title": clean_title(sub["title"]) or ("Quick recall" if page[0]["type"] == "callout" else clean_title(title)),
                                  "part": f"{i + 1}/{len(pages)}" if len(pages) > 1 else "",
                                  "blocks": page})
            if not cards:
                continue
            m = re.match(r"(?:Chapter\s+)?(\d+)[.:]?\s*(.*)", title)
            num, name = (m.group(1), m.group(2)) if m else ("", title)
            modules.append({
                "id": f"{guide_id}-{slug(title)}",
                "guide": guide_id, "guideTitle": guide_title,
                "part": re.sub(r"^(PART|Part)\s+\d+:\s*", "", ptitle),
                "num": num, "title": clean_title(name) or clean_title(title),
                "key": "🧠" in title,
                "links": repo_links(title),
                "cards": cards,
            })
    return modules


def tidy(h):
    """Fix PDF-layout spacing around inline code and strip anything unsafe from rendered HTML."""
    h = re.sub(r"<code>\s+", "<code>", h)
    h = re.sub(r"\s+</code>", "</code>", h)
    h = re.sub(r"</code>\s+([.,;:)!?’”])", r"</code>\1", h)
    h = re.sub(r"([(“‘])\s+<code>", r"\1<code>", h)
    h = re.sub(r"(?is)<(script|style|iframe|object|embed)\b.*?</\1>", "", h)
    h = re.sub(r"(?i)\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", h)
    h = re.sub(r"(?i)(href|src)\s*=\s*([\"'])\s*javascript:[^\"']*\2", r"\1=\2#\2", h)
    h = re.sub(r"<a (?![^>]*target=)", '<a target="_blank" rel="noopener" ', h)
    return h


def tidy_all(obj):
    if isinstance(obj, dict):
        return {k: (tidy(v) if k in ("html", "q") and isinstance(v, str) else
                    [tidy(i) if isinstance(i, str) else tidy_all(i) for i in v] if k in ("items",) else
                    [[tidy(c) for c in r] for r in v] if k == "rows" else tidy_all(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [tidy_all(i) for i in obj]
    return obj


# ---------------------------------------------------------------- Quiz

TOPIC_RULES = [
    ("Kubernetes", r"kubernetes|k8s|\bpod|kubectl|helm"), ("Docker", r"docker|container|image|dockerfile"),
    ("Terraform", r"terraform|\bstate\b|hcl|\bmodule"), ("CI/CD", r"ci/cd|pipeline|github actions|workflow|deploy"),
    ("Git", r"\bgit\b|commit|branch|merge|rebase"), ("Networking", r"dns|tcp|udp|\bip\b|cidr|subnet|port|http|tls|osi|nat\b"),
    ("Linux", r"linux|bash|chmod|systemd|process|kernel|inode|shell|script"),
    ("AWS", r"aws|ec2|s3|iam|vpc|ecs|ecr|alb|route 53|lambda|cloudwatch|fargate|rds|acm|kms|region|az\b"),
]


def guess_topic(t, default="AWS"):
    for name, pat in TOPIC_RULES:
        if re.search(pat, t, re.I):
            return name
    return default


SECTION_TOPIC = {"19": "Linux", "20": "Networking", "21": "Git", "22": "AWS", "23": "Azure",
                 "24": "Terraform", "25": "Docker", "26": "CI/CD"}


def blocks_html(blocks):
    return [b for b in blocks]


def qa_from_part2(devops_parts):
    """§19–26: a bold question paragraph followed by its answer blocks."""
    items = []
    for part in devops_parts:
        if not part["title"].upper().startswith("PART 2"):
            continue
        for sec in part["sections"]:
            m = re.match(r"(\d+)\.", sec["title"])
            if not m:
                continue
            topic = SECTION_TOPIC.get(m.group(1), "DevOps")
            cur = None
            for sub in sec["subsections"]:
                for blk in sub["blocks"]:
                    q = None
                    if blk["type"] == "p":
                        mm = re.match(r"^<b>(.+?)</b>\s*(.*)$", blk["html"], re.S)
                        if mm and len(text_of(mm.group(1))) > 8 and re.search(r"[?.)]\s*$", text_of(mm.group(1)).strip()):
                            q, rest = mm.group(1), mm.group(2).strip()
                    if q:
                        cur = {"topic": topic, "q": q, "a": [], "source": "DevOps Revision Guide §" + m.group(1)}
                        rest = re.sub(r"^[🧠\s]+", "", rest)
                        if rest:
                            cur["a"].append({"type": "p", "html": rest})
                        if "🧠" in blk["html"]:
                            cur["key"] = True
                        items.append(cur)
                    elif cur:
                        cur["a"].append(blk)
    return [i for i in items if i["a"]]


def qa_from_out_loud(devops_parts):
    items = []
    for part in devops_parts:
        for sec in part["sections"]:
            if not sec["title"].startswith("15."):
                continue
            heading = "DevOps"
            for sub in sec["subsections"]:
                for blk in sub["blocks"]:
                    if blk["type"] == "p" and blk["html"].startswith("<b>"):
                        heading = text_of(blk["html"])
                    if blk["type"] != "list":
                        continue
                    for it in blk["items"]:
                        if "→" not in it:
                            continue
                        q, a = it.split("→", 1)
                        items.append({"topic": guess_topic(text_of(q), guess_topic(heading, "DevOps")),
                                      "q": q.strip(), "a": [{"type": "p", "html": a.strip()}],
                                      "source": "DevOps Revision Guide §15 · Questions to answer out loud",
                                      "quick": True})
    return items


def glossary_cards(parts, section_match, source):
    items = []
    for part in parts:
        for sec in part["sections"]:
            if not re.match(section_match, sec["title"]):
                continue
            for sub in sec["subsections"]:
                for blk in sub["blocks"]:
                    if blk["type"] != "table":
                        continue
                    for row in blk["rows"]:
                        if len(row) < 2 or not row[0] or not row[1]:
                            continue
                        term = text_of(row[0]).strip()
                        if term.lower() in ("term",):
                            continue
                        items.append({"topic": guess_topic(term + " " + text_of(row[1]), "AWS"),
                                      "kind": "definition", "term": term,
                                      "q": f"Define: <b>{html.escape(term)}</b>",
                                      "a": [{"type": "p", "html": row[1]}], "source": source})
    return items


def check_yourself(aws_parts):
    qs, ans = {}, {}
    for part in aws_parts:
        is_key = part["title"].startswith("Answer key")
        for sec in part["sections"]:
            if not is_key and not re.match(r"(Check yourself|Interview practice)", sec["title"]):
                continue
            for sub in sec["subsections"]:
                for blk in sub["blocks"]:
                    if blk["type"] != "list":
                        continue
                    for it in blk["items"]:
                        m = re.match(r"^<b>(P?\d+(?:\.\d+)?)\s*(.*?)</b>\s*(.*)$", it, re.S)
                        if not m:
                            continue
                        qid = m.group(1)
                        body = (f"<b>{m.group(2)}</b> " if m.group(2) else "") + m.group(3)
                        (ans if is_key else qs)[qid] = (body.strip(), sec["title"])
    for qid, (a, w) in list(ans.items()):  # "See answer 30.1." → copy that answer in
        m = re.fullmatch(r"See answer (\d+(?:\.\d+)?)\.?", text_of(a).strip())
        if m and m.group(1) in ans:
            ans[qid] = (ans[m.group(1)][0], w)
    items = []
    for qid, (q, where) in qs.items():
        if qid not in ans:
            continue
        practice = qid.startswith("P")
        memos = "(Memos)" in q
        items.append({"topic": "Memos" if memos else guess_topic(text_of(q), "AWS"),
                      "q": q.replace("(Memos) ", ""), "a": [{"type": "p", "html": ans[qid][0]}],
                      "source": "AWS From Zero · " + ("Interview practice " + qid if practice else f"Check yourself {qid}"),
                      "practice": practice})
    return items


def parse_tech_vault(tv_dir):
    s = open(os.path.join(tv_dir, "README.md"), encoding="utf-8").read()
    secs = re.split(r'<summary><h3 id="([^"]+)">([^<]+)</h3></summary>', s)
    out = []
    names = {"linux": "Linux", "networking": "Networking", "git": "Git", "aws": "AWS", "azure": "Azure",
             "terraform": "Terraform", "docker": "Docker", "k8s": "Kubernetes", "ansible": "Ansible", "cicd": "CI/CD"}
    for i in range(1, len(secs), 3):
        sid, body = secs[i], secs[i + 2]
        if sid not in names:
            continue
        # Everything after a "scenario" sub-heading in this topic is a scenario question.
        marker = re.search(r"\n(?:#+\s*|\*\*)[^\n]*scenario[^\n]*\n", body, re.I)
        for m in re.finditer(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", body, re.S):
            q, a = m.group(1).strip(), m.group(2).strip()
            if len(a) < 40:
                continue  # unanswered
            in_scen = bool(marker) and m.start() > marker.start()
            scen_words = re.search(r"\byou\b.*\b(notice|have|are|want)\b|how would you (investigate|troubleshoot|debug)|"
                                   r"troubleshoot|can't reach|fails|walk me through|step by step|best solution", q, re.I)
            out.append({"topic": names[sid], "q": q, "html": markdown.markdown(a, extensions=["fenced_code", "tables"]),
                        "scenario": bool(in_scen or scen_words)})
    return out


def norm(q):
    return re.sub(r"[^a-z0-9 ]", "", text_of(q).lower())


def attach_tech_vault(items, tv):
    """Give guide Q&A cards the full tech-vault answer as an optional deeper explanation."""
    pool = [(norm(t["q"]), t) for t in tv]
    used = set()
    for it in items:
        n = norm(it["q"])
        best, score = None, 0.0
        for tn, t in pool:
            r = difflib.SequenceMatcher(None, n, tn).ratio()
            if r > score:
                best, score = t, r
        if best and score >= 0.62:
            it["more"] = best["html"]
            used.add(id(best))
    return used


# ---------------------------------------------------------------- Scenarios

def memos_stories(devops_parts):
    stories = []
    for part in devops_parts:
        for sec in part["sections"]:
            if not sec["title"].startswith("14."):
                continue
            cur = None
            for sub in sec["subsections"]:
                for blk in sub["blocks"]:
                    if blk["type"] != "list":
                        continue
                    for it in blk["items"]:
                        m = re.match(r"^<b>(\d+)\.\s*(.+?)</b>\s*(.*)$", it, re.S)
                        if m:
                            cur = {"title": text_of(m.group(2)), "points": []}
                            if m.group(3).strip():
                                cur["points"].append(m.group(3).strip())
                            stories.append(cur)
                        elif cur:
                            cur["points"].append(it)
    out = []
    for s in stories:
        if not s["points"]:
            continue
        out.append({"topic": "Memos", "kind": "story", "source": "DevOps Revision Guide §14 · interview stories",
                    "q": f"“Tell me about a problem you hit on a project and how you solved it.” "
                         f"<span class='hint-chip'>Story: {html.escape(s['title'])}</span>",
                    "answer": [{"type": "list", "ordered": False, "items": s["points"]}],
                    "why": [{"type": "p", "html": "Tell it as <b>Situation → Problem → How I found it → Fix → Lesson</b>. "
                                                   "Stories 1, 2 and 6 are your strongest."}]})
    return out


def parse_memos_md(path):
    """content/memos-scenarios.md: '## title', 'Topic: x', then '### Answer' and '### Why it matters' sections."""
    txt = open(path, encoding="utf-8").read()
    out = []
    for chunk in re.split(r"^## ", txt, flags=re.M)[1:]:
        title, _, rest = chunk.partition("\n")
        meta = dict(re.findall(r"^(Topic|Level|Files):\s*(.+)$", rest, re.M))
        rest = re.sub(r"^(Topic|Level|Files):.*\n", "", rest, flags=re.M)
        parts = re.split(r"^### (.+)$", rest, flags=re.M)
        q = parts[0].strip()
        sec = {parts[i].strip().lower(): parts[i + 1].strip() for i in range(1, len(parts), 2)}
        md = lambda s: markdown.markdown(s, extensions=["fenced_code", "tables"], tab_length=2)
        files = [f.strip() for f in meta.get("Files", "").split(",") if f.strip()]
        out.append({"topic": meta.get("Topic", "Memos"), "level": meta.get("Level", ""),
                    "source": "Your Memos project", "title": title.strip(),
                    "q": md(q), "answer": [{"type": "html", "html": md(sec.get("answer", ""))}],
                    "why": [{"type": "html", "html": md(sec.get("why it matters", ""))}] if sec.get("why it matters") else [],
                    "links": [{"href": REPO + f, "label": f} for f in files]})
    return out


# ---------------------------------------------------------------- main

def main(devops_pdf, aws_pdf, tv_dir=None):
    """Only the guides' reference library (data/learn.js) is built here now. The course, quiz,
    scenarios and lab come from content/ via scripts/build_content.py."""
    devops, aws = extract(devops_pdf), extract(aws_pdf)
    learn = (learn_modules(devops, "devops", "DevOps Revision Guide", DEVOPS_SKIP)
             + learn_modules(aws, "aws", "AWS From Zero", AWS_SKIP))
    learn = tidy_all(learn)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "learn.js"), "w", encoding="utf-8") as f:
        f.write("// Generated by scripts/build_data.py from the two guide PDFs (reference library).\n")
        f.write(f"window.LEARN = {json.dumps(learn, ensure_ascii=False, separators=(',', ':'))};\n")
    print(f"guides reference: {len(learn)} modules, {sum(len(m['cards']) for m in learn)} cards")


if __name__ == "__main__":
    main(*sys.argv[1:3])
