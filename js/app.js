// DevOps Scroll — a doomscrolling course from absolute beginner to DevOps engineer, built around the
// open-source Memos app as the worked example. Content is generated from content/*.md by scripts/build_content.py.
(() => {
  "use strict";

  const CUR = window.CURRICULUM || [];
  const MCQ = window.MCQ || [];
  const SCEN = window.SCEN || [];
  const LAB = window.LAB || [];
  const MODULES = CUR;
  const STORE_KEY = "devopsscroll:v2";

  const $ = (s, r = document) => r.querySelector(s);
  const el = (tag, cls, html) => { const n = document.createElement(tag); if (cls) n.className = cls; if (html != null) n.innerHTML = html; return n; };
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const shuffle = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const plain = (h) => String(h || "").replace(/<[^>]+>/g, "");

  // ---------------------------------------------------------------- progress (this device only)
  const S = (() => { try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch { return {}; } })();
  S.learn ||= {}; S.quiz ||= {}; S.scen ||= {}; S.lab ||= {}; S.ui ||= {};
  let saveT = null;
  const save = () => { clearTimeout(saveT); saveT = setTimeout(() => { try { localStorage.setItem(STORE_KEY, JSON.stringify(S)); } catch {} }, 150); };

  // ---------------------------------------------------------------- diagrams (Mermaid, loaded on first use)
  const dark = matchMedia("(prefers-color-scheme: dark)").matches;
  const diagrams = {
    loading: null, n: 0,
    load() {
      return (this.loading ||= new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = "vendor/mermaid.min.js";
        s.onload = () => {
          window.mermaid.initialize({
            startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "neutral",
            fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", fontSize: 14,
            flowchart: { htmlLabels: true, curve: "basis", padding: 8, nodeSpacing: 28, rankSpacing: 34, useMaxWidth: true },
            sequence: { useMaxWidth: true, mirrorActors: false, boxMargin: 6, messageFontSize: 13 },
            themeVariables: dark ? { primaryColor: "#1b2230", primaryBorderColor: "#4fd1a5", lineColor: "#8b95a7", primaryTextColor: "#e6e9ef" }
              : { primaryColor: "#eef7f3", primaryBorderColor: "#0f9d74", lineColor: "#5d6677" },
          });
          resolve(window.mermaid);
        };
        s.onerror = reject;
        document.head.appendChild(s);
      }));
    },
    async render(node) {
      if (node.dataset.done) return;
      node.dataset.done = "1";
      try {
        const m = await this.load();
        const { svg } = await m.render("dg" + ++this.n, node.dataset.code);
        node.querySelector(".dg").innerHTML = svg;
      } catch (e) {
        node.querySelector(".dg").innerHTML = `<pre><code>${esc(node.dataset.code)}</code></pre>`;
      }
    },
    near(cardNode) {
      // render diagrams in this card and the next two, so they're ready before you get there
      let c = cardNode;
      for (let k = 0; k < 3 && c; k++, c = c.nextElementSibling) c.querySelectorAll?.(".diagram:not([data-done])").forEach((d) => this.render(d));
    },
  };

  // ---------------------------------------------------------------- blocks
  function renderBlocks(blocks, ctx = {}) { return (blocks || []).map((b, i) => renderBlock(b, ctx, i)).join(""); }
  function renderBlock(b, ctx, i) {
    switch (b.type) {
      case "html": return `<div class="md">${b.html}</div>`;
      case "p": return `<p>${b.html}</p>`;
      case "note": return `<div class="note ${b.kind}">${b.html}</div>`;
      case "pre": return `<pre><code>${esc(b.text)}</code></pre>`;
      case "callout": return `<div class="callout ${b.kind}">${renderBlocks(b.blocks)}</div>`;
      case "diagram":
        return `<figure class="diagram" data-code="${esc(b.code)}"><div class="dg"><div class="dg-wait">drawing diagram…</div></div>${b.caption ? `<figcaption>${esc(b.caption)}</figcaption>` : ""}</figure>`;
      case "code":
        return `<div class="code">${b.file ? `<div class="code-head">${b.href ? `<a href="${esc(b.href)}" target="_blank" rel="noopener">📄 ${esc(b.file)}</a>` : `📄 ${esc(b.file)}`}<button type="button" class="copy" aria-label="Copy code">Copy</button></div>` : `<button type="button" class="copy floating" aria-label="Copy code">Copy</button>`}<pre><code>${esc(b.code)}</code></pre></div>`;
      case "output": return `<pre class="out"><code>${esc(b.text)}</code></pre>`;
      case "term": return `<div class="term" data-i="${i}"></div>`;
      case "check": return `<div class="inline-check" data-i="${i}"></div>`;
      case "list": {
        const heads = b.items.map((x) => /^<b>\d+\.\s/.test(x));
        if (b.ordered && heads.some(Boolean)) return `<ul class="plain">${b.items.map((x, k) => `<li class="${heads[k] ? "lh" : ""}">${x}</li>`).join("")}</ul>`;
        const tag = b.ordered ? "ol" : "ul";
        return `<${tag}${b.ordered && b.start > 1 ? ` start="${b.start}"` : ""}>${b.items.map((x) => `<li>${x}</li>`).join("")}</${tag}>`;
      }
      case "table": {
        const rows = b.rows.slice(); const head = b.head ? rows.shift() : null;
        return `<div class="tbl"><table>${head ? `<thead><tr>${head.map((c) => `<th>${c}</th>`).join("")}</tr></thead>` : ""}<tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
      }
      default: return "";
    }
  }
  // Wire up interactive pieces inside a rendered node.
  function hydrate(node, blocks, hooks = {}) {
    node.querySelectorAll(".md table").forEach((t) => { if (!t.parentElement.classList.contains("tbl")) { const w = el("div", "tbl"); t.replaceWith(w); w.appendChild(t); } });
    node.querySelectorAll(".copy").forEach((b) => b.onclick = async () => {
      const code = b.closest(".code").querySelector("pre").innerText;
      try { await navigator.clipboard.writeText(code); b.textContent = "Copied ✓"; } catch { b.textContent = "Select & copy"; }
      setTimeout(() => (b.textContent = "Copy"), 1500);
    });
    node.querySelectorAll(".term").forEach((t) => terminal(t, blocks[+t.dataset.i], hooks.onTerm));
    node.querySelectorAll(".inline-check").forEach((t) => t.appendChild(mcqEl(blocks[+t.dataset.i].mcq, { onAnswer: hooks.onCheck })));
  }

  // ---------------------------------------------------------------- multiple choice
  // q: {q:[blocks], options:[{t, ok, why?}], explain?}. Options are shuffled each time.
  function mcqEl(q, { onAnswer, letters = true, previous } = {}) {
    const wrap = el("div", "mcq");
    wrap.innerHTML = `<div class="mcq-q">${renderBlocks(q.q)}</div><div class="opts"></div><div class="mcq-after" hidden></div>`;
    hydrate(wrap.querySelector(".mcq-q"), q.q);
    const order = shuffle(q.options.map((_, i) => i));
    const opts = wrap.querySelector(".opts");
    order.forEach((oi, k) => {
      const o = q.options[oi];
      const b = el("button", "opt", `<span class="key">${"ABCDEF"[k]}</span><span class="t">${o.t}</span>`);
      b.type = "button"; b.dataset.oi = oi;
      b.onclick = () => choose(oi);
      opts.appendChild(b);
    });
    wrap._choose = (k) => { const b = opts.children[k]; if (b) b.click(); };
    function choose(oi) {
      if (wrap.dataset.answered) return;
      wrap.dataset.answered = "1";
      const right = q.options[oi].ok;
      [...opts.children].forEach((b) => {
        const o = q.options[+b.dataset.oi];
        b.disabled = true;
        if (o.ok) b.classList.add("right");
        if (+b.dataset.oi === oi && !o.ok) b.classList.add("wrong");
        if (+b.dataset.oi === oi) b.classList.add("chosen");
        if (o.why) b.insertAdjacentHTML("beforeend", `<span class="why">${o.why}</span>`);
      });
      const after = wrap.querySelector(".mcq-after");
      after.innerHTML = `<div class="verdict ${right ? "good" : "bad"}">${right ? "✓ Correct" : "✗ Not quite"}</div>${q.explain ? `<div class="md explain">${q.explain}</div>` : ""}`;
      after.hidden = false;
      onAnswer && onAnswer(right, wrap);
    }
    if (previous != null) { /* show history marker only */ }
    return wrap;
  }

  // ---------------------------------------------------------------- practice terminal
  const norm = (s) => s.trim().replace(/\s+/g, " ").replace(/\s*\\\s*/g, " ");
  function terminal(node, b, onRun) {
    node.innerHTML = `
      <div class="term-bar"><i></i><i></i><i></i><span>bash — practice terminal</span></div>
      <div class="term-task">Type this command:<code>${esc(b.cmd)}</code></div>
      <div class="term-body" aria-live="polite"><label class="term-line"><span class="ps">$</span><input autocapitalize="off" autocomplete="off" autocorrect="off" spellcheck="false" aria-label="Type the command"></label></div>
      <div class="term-actions"><button type="button" class="btn small" data-run>▶ Run it for me</button><span class="term-msg"></span></div>`;
    const input = node.querySelector("input"), body = node.querySelector(".term-body"), msg = node.querySelector(".term-msg");
    let done = false;
    const finish = async (typed) => {
      if (done) return; done = true;
      input.disabled = true;
      if (typed !== true) {
        for (const ch of b.cmd) { input.value += ch; await new Promise((r) => setTimeout(r, 12)); }
      }
      const out = el("pre", "term-out");
      body.appendChild(out);
      const lines = (b.output || "").split("\n");
      for (const line of lines) { out.textContent += line + "\n"; await new Promise((r) => setTimeout(r, Math.min(60, 400 / lines.length))); }
      body.insertAdjacentHTML("beforeend", `<div class="term-line done"><span class="ps">$</span><span class="cursor"></span></div>`);
      node.classList.add("ran");
      msg.textContent = "✓ done";
      onRun && onRun();
    };
    input.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      e.preventDefault();
      if (norm(input.value) === norm(b.cmd)) { finish(true); }
      else if (!input.value.trim()) { msg.textContent = "Type the command above, then press Enter"; }
      else {
        const a = norm(input.value), x = norm(b.cmd);
        let k = 0; while (k < a.length && a[k] === x[k]) k++;
        msg.innerHTML = `Not quite: check from “<b>${esc(x.slice(k, k + 12) || "end")}</b>”`;
      }
    });
    node.querySelector("[data-run]").onclick = () => { input.value = ""; finish(false); };
  }

  // ---------------------------------------------------------------- shared feed helpers
  function card(innerHTML, cls = "") { const c = el("article", "card " + cls); c.appendChild(el("div", "card-inner", innerHTML)); return c; }
  function watchCurrent(feed, onShow) {
    let raf = 0;
    const check = () => {
      raf = 0;
      const mid = feed.scrollTop + feed.clientHeight / 2;
      for (const c of feed.children) {
        if (c.offsetTop <= mid && c.offsetTop + c.offsetHeight > mid) {
          if (feed._current !== c) { feed._current = c; diagrams.near(c); onShow && onShow(c); }
          break;
        }
      }
      if (feed._more) feed._more();
    };
    feed.addEventListener("scroll", () => { if (!raf) raf = requestAnimationFrame(check); }, { passive: true });
    feed._check = check;
  }
  const toolbar = $("#toolbar");
  function chips(defs, active, onPick) {
    return defs.map((d) => {
      const b = el("button", "chip" + (d.wide ? " wide" : ""), esc(d.label) + (d.n != null ? `<span class="n">${d.n}</span>` : ""));
      b.type = "button"; b.setAttribute("aria-pressed", String(d.id === active)); b.onclick = () => onPick(d.id);
      return b;
    });
  }
  const stat = (id, text) => { const s = el("span", "stat", text); s.id = id; return s; };
  function step(feed, dir) { feed.scrollBy({ top: dir * feed.clientHeight, behavior: "smooth" }); }
  const levelBadge = (lv) => lv ? `<span class="badge lv-${esc(String(lv).toLowerCase())}">${esc(lv)}</span>` : "";

  // ================================================================= LEARN
  const learn = {
    feed: $("#view-learn"),
    module: MODULES.find((m) => m.id === S.ui.module) || MODULES[0],
    flat(m) { const out = []; m.lessons.forEach((l, li) => l.cards.forEach((c, ci) => out.push({ l, li, c, ci }))); return out; },
    prog(m) { return (S.learn[m.id] ||= { seen: {}, last: 0 }); },
    pct(m) { const n = this.flat(m).length; return n ? Math.round((Object.keys(this.prog(m).seen).length / n) * 100) : 0; },

    toolbar() {
      const m = this.module;
      toolbar.replaceChildren(...chips([{ id: "m", label: `${m.icon} ${m.title}`, wide: true }], "m", () => this.openSheet()),
        ...chips([{ id: "list", label: "☰ All modules" }], "", () => this.openSheet()));
    },
    open(m, idx) { this.module = m; S.ui.module = m.id; save(); this.render(idx); },
    render(startIdx) {
      this.toolbar();
      const f = this.feed, m = this.module, flat = this.flat(m);
      f.replaceChildren(); f._current = null;
      f.appendChild(this.cover(m, flat.length));
      flat.forEach((x, i) => f.appendChild(this.cardEl(m, x, i, flat.length)));
      f.appendChild(this.endCard(m));
      const idx = startIdx ?? this.prog(m).last ?? 0;
      requestAnimationFrame(() => { const t = idx > 0 ? f.children[idx + 1] : f.children[0]; f.scrollTop = t ? t.offsetTop : 0; f._check(); });
    },
    cover(m, n) {
      const pct = this.pct(m);
      const lessons = m.lessons.map((l, i) => `<li>${esc(l.title)}</li>`).join("");
      const c = card(`
        <div class="meta">${levelBadge(m.level)}<span>${m.lessons.length} lesson${m.lessons.length > 1 ? "s" : ""} · ${n} cards · ~${Math.max(2, Math.round(n * 0.5))} min</span></div>
        <div class="big">${m.icon}</div>
        <h2>${esc(m.title)}</h2>
        ${m.summary ? `<p class="muted">${esc(m.summary)}</p>` : ""}
        <div class="progress"><i style="width:${pct}%"></i></div><p class="muted small">${pct}% seen</p>
        <div class="lbl">Lessons</div><ol class="lessons">${lessons}</ol>
        ${m.links && m.links.length ? `<div class="lbl">Files in the example project</div><div class="links">${m.links.map((l) => `<span class="chip-file">📄 ${esc(l.label)}</span>`).join("")}</div>` : ""}
        <p class="muted">Swipe up to start ↑</p>`, "cover");
      c._learn = { m, i: -1 };
      return c;
    },
    cardEl(m, x, i, n) {
      const { l, c } = x;
      const head = `<div class="meta"><span class="badge accent">${m.icon} ${esc(m.title)}</span><span>${i + 1}/${n}</span></div>
        <div class="progress"><i style="width:${((i + 1) / n) * 100}%"></i></div>
        <div class="lesson">${esc(l.title)}</div>`;
      let node;
      if (c.type === "check") {
        node = card(head + `<h2>🧩 Quick check</h2><div class="slot"></div>`, "check");
        node.querySelector(".slot").appendChild(mcqEl(c.mcq, { onAnswer: (ok) => {
          const r = (S.quiz[c.mcq.id || plain(JSON.stringify(c.mcq.q)).slice(0, 60)] ||= { r: 0, w: 0 }); r[ok ? "r" : "w"]++; save();
        } }));
      } else {
        node = card(head + `<h2>${esc(c.title)}</h2><div class="body">${renderBlocks(c.blocks)}</div>`);
        hydrate(node, c.blocks);
      }
      node._learn = { m, i };
      return node;
    },
    endCard(m) {
      const i = MODULES.indexOf(m), next = MODULES[i + 1];
      const node = card(`
        <div class="big center">✅</div><h2 class="center">Module complete</h2>
        <p class="muted center">${esc(m.title)}</p>
        ${next ? `<button type="button" class="btn primary" data-next>Next: ${next.icon} ${esc(next.title)} →</button>` : ""}
        <button type="button" class="btn" data-quiz>🧠 Quiz me on ${esc(m.topic)}</button>
        <button type="button" class="btn" data-lab>🛠️ Go to the Build Lab</button>
        <button type="button" class="btn" data-list>☰ All modules</button>`);
      node.querySelector(".card-inner").classList.add("center-col");
      if (next) node.querySelector("[data-next]").onclick = () => this.open(next, 0);
      node.querySelector("[data-quiz]").onclick = () => { quiz.setFilter(quiz.hasTopic(m.topic) ? "t:" + m.topic : "all"); tabs.show("quiz"); };
      node.querySelector("[data-lab]").onclick = () => tabs.show("lab");
      node.querySelector("[data-list]").onclick = () => this.openSheet();
      return node;
    },
    onShow(c) {
      if (!c._learn || c._learn.i < 0) return;
      const p = this.prog(c._learn.m); p.seen[c._learn.i] = 1; p.last = c._learn.i; save();
    },
    openSheet() {
      openSheet("Modules", (body) => {
        let last = "";
        MODULES.forEach((m, idx) => {
          const group = m.level;
          if (group !== last) { body.appendChild(el("h3", "", esc(group))); last = group; }
          const pct = this.pct(m);
          const b = el("button", "mod", `<span class="num">${m.icon}</span><span>${esc(m.title)}</span><span class="pct">${pct}%</span><div class="progress"><i style="width:${pct}%"></i></div>`);
          b.type = "button"; b.setAttribute("aria-current", String(m === this.module));
          b.onclick = () => { sheet.close(); this.open(m); };
          body.appendChild(b);
        });
      });
    },
  };

  // ================================================================= QUIZ (multiple choice)
  const quiz = {
    feed: $("#view-quiz"),
    filter: S.ui.quiz || "all",
    session: { r: 0, n: 0 },
    deck: [], pos: 0,
    topics() { const c = {}; MCQ.forEach((q) => { c[q.topic] = (c[q.topic] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1]); },
    hasTopic(t) { return MCQ.some((q) => q.topic === t); },
    rec(q) { return S.quiz[q.id]; },
    pool(f = this.filter) {
      if (f === "all") return MCQ;
      if (f === "missed") return MCQ.filter((q) => { const r = this.rec(q); return r && r.w > r.r; });
      if (f === "new") return MCQ.filter((q) => !this.rec(q));
      if (f.startsWith("t:")) return MCQ.filter((q) => q.topic === f.slice(2));
      if (f.startsWith("l:")) return MCQ.filter((q) => (q.level || "") === f.slice(2));
      if (f.startsWith("s:")) return MCQ.filter((q) => (q.source || "").toLowerCase().includes(f.slice(2)));
      return MCQ;
    },
    toolbar() {
      const missed = this.pool("missed").length;
      const defs = [{ id: "all", label: "All", n: MCQ.length }, ...(missed ? [{ id: "missed", label: "❌ Missed", n: missed }] : []),
        { id: "new", label: "🆕 New", n: this.pool("new").length },
        { id: "s:tech-vault", label: "tech-vault", n: this.pool("s:tech-vault").length }, { id: "s:revision", label: "Revision notes", n: this.pool("s:revision").length },
        ...["Beginner", "Intermediate", "Advanced"].map((l) => ({ id: "l:" + l, label: l, n: this.pool("l:" + l).length })),
        ...this.topics().map(([t, n]) => ({ id: "t:" + t, label: t, n }))];
      toolbar.replaceChildren(stat("quizStat", `✓ ${this.session.r}/${this.session.n}`), ...chips(defs, this.filter, (id) => this.setFilter(id)));
      toolbar.querySelector('[aria-pressed="true"]')?.scrollIntoView({ inline: "center", block: "nearest" });
    },
    setFilter(f) { this.filter = S.ui.quiz = f; save(); if (tabs.current === "quiz") this.render(); else this.dirty = true; },
    buildDeck() {
      const score = (q) => { const r = this.rec(q); if (!r) return Math.random(); if (r.w > r.r) return 0.4 + Math.random(); return 1.5 + r.r - r.w + Math.random(); };
      this.deck = this.pool().map((q) => [score(q), q]).sort((a, b) => a[0] - b[0]).map((x) => x[1]);
      this.pos = 0;
    },
    render() {
      this.dirty = false; this.toolbar();
      const f = this.feed; f.replaceChildren(); f._current = null;
      this.buildDeck();
      if (!this.deck.length) { f.appendChild(card(`<h2 class="center">Nothing here yet 🎉</h2><p class="muted center">Pick another filter above.</p>`)); return; }
      this.more(); f.scrollTop = 0; requestAnimationFrame(() => f._check());
    },
    more() { for (let k = 0; k < 10; k++) { if (this.pos >= this.deck.length) this.buildDeck(); this.feed.appendChild(this.cardEl(this.deck[this.pos++])); } },
    cardEl(q) {
      const r = this.rec(q);
      const node = card(`<div class="meta"><span class="badge accent">${esc(q.topic)}</span>${levelBadge(q.level)}<span>${esc(q.source || "")}</span>${r ? `<span>${r.r}✓ ${r.w}✗</span>` : `<span class="badge warn">new</span>`}</div><div class="slot"></div>`, "quiz");
      node._q = q;
      const m = mcqEl(q, { onAnswer: (ok, w) => this.answer(node, ok) });
      node.querySelector(".slot").appendChild(m);
      node._mcq = m;
      return node;
    },
    answer(node, ok) {
      const q = node._q, r = (S.quiz[q.id] ||= { r: 0, w: 0 });
      r[ok ? "r" : "w"]++; r.t = Date.now(); save();
      this.session.n++; if (ok) this.session.r++;
      const s = $("#quizStat"); if (s) s.textContent = `✓ ${this.session.r}/${this.session.n}`;
      if (!ok) { const again = this.cardEl(q); const at = [...this.feed.children].indexOf(node) + 6; this.feed.insertBefore(again, this.feed.children[at] || null); }
      const nx = el("button", "btn primary next", "Next question ↓"); nx.type = "button"; nx.onclick = () => step(this.feed, 1);
      node.querySelector(".mcq-after").appendChild(nx);
    },
  };

  // ================================================================= SCENARIOS (multiple choice)
  const scen = {
    feed: $("#view-scen"),
    filter: S.ui.scen || "all",
    pool(f = this.filter) {
      if (f === "all") return SCEN;
      if (f === "todo") return SCEN.filter((s) => !S.scen[s.id]);
      if (f.startsWith("t:")) return SCEN.filter((s) => s.topic === f.slice(2));
      if (f.startsWith("l:")) return SCEN.filter((s) => s.level === f.slice(2));
      if (f.startsWith("s:")) return SCEN.filter((s) => (s.source || "").toLowerCase().includes(f.slice(2)));
      return SCEN;
    },
    toolbar() {
      const c = {}; SCEN.forEach((s) => (c[s.topic] = (c[s.topic] || 0) + 1));
      const done = SCEN.filter((s) => S.scen[s.id]).length;
      const defs = [{ id: "all", label: "All", n: SCEN.length }, { id: "todo", label: "Not done", n: SCEN.length - done },
        { id: "s:example", label: "🔧 Example project", n: this.pool("s:example").length },
        ...["Junior", "Mid", "Senior"].map((l) => ({ id: "l:" + l, label: l, n: this.pool("l:" + l).length })),
        ...Object.entries(c).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({ id: "t:" + t, label: t, n }))];
      toolbar.replaceChildren(stat("scenStat", `🎯 ${done}/${SCEN.length}`), ...chips(defs, this.filter, (id) => { this.filter = S.ui.scen = id; save(); this.render(); }));
      toolbar.querySelector('[aria-pressed="true"]')?.scrollIntoView({ inline: "center", block: "nearest" });
    },
    render() {
      this.toolbar();
      const f = this.feed; f.replaceChildren(); f._current = null;
      const list = this.pool();
      if (!list.length) f.appendChild(card(`<h2 class="center">All done 🎉</h2><p class="muted center">Pick another filter above.</p>`));
      list.forEach((s, i) => f.appendChild(this.cardEl(s, i, list.length)));
      f.scrollTop = 0; requestAnimationFrame(() => f._check());
    },
    cardEl(s, i, n) {
      const prev = S.scen[s.id];
      const node = card(`
        <div class="meta"><span class="badge ${/example/i.test(s.source) ? "accent" : "blue"}">${/example/i.test(s.source) ? "🔧 Example project" : esc(s.topic)}</span>${s.level ? `<span class="badge">${esc(s.level)}</span>` : ""}<span>${esc(/example/i.test(s.source) ? s.topic : s.source)}</span><span>${i + 1}/${n}</span>${prev ? `<span class="badge ${prev === "r" ? "good" : "warn"}">${prev === "r" ? "got it" : "review"}</span>` : ""}</div>
        <h2>${esc(s.title)}</h2>
        <div class="body situation">${renderBlocks(s.situation)}</div>
        <div class="slot"></div>
        ${s.links && s.links.length ? `<div class="links-after" hidden><div class="lbl">Files involved</div><div class="links">${s.links.map((l) => `<span class="chip-file">📄 ${esc(l.label)}</span>`).join("")}</div></div>` : ""}`, "scen");
      hydrate(node.querySelector(".situation"), s.situation);
      const m = mcqEl(s, { onAnswer: (ok) => {
        S.scen[s.id] = ok ? "r" : "w"; save();
        const la = node.querySelector(".links-after"); if (la) la.hidden = false;
        const st = $("#scenStat"); if (st) st.textContent = `🎯 ${SCEN.filter((x) => S.scen[x.id]).length}/${SCEN.length}`;
        const nx = el("button", "btn primary next", "Next scenario ↓"); nx.type = "button"; nx.onclick = () => step(this.feed, 1);
        node.querySelector(".mcq-after").appendChild(nx);
      } });
      node.querySelector(".slot").appendChild(m);
      node._mcq = m;
      return node;
    },
  };

  // ================================================================= BUILD LAB (several tracks)
  const lab = {
    feed: $("#view-lab"),
    track: LAB.find((t) => t.id === S.ui.labTrack) || LAB[0],
    get stages() { return this.track ? this.track.stages : []; },
    stage: 0,
    // The first track keeps the original "stage.step" keys so earlier progress isn't lost.
    key(si, i, t = this.track) { return t === LAB[0] ? `${si}.${i}` : `${t.id}:${si}.${i}`; },
    stageDone(si, t = this.track) { return t.stages[si].steps.filter((_, i) => S.lab[this.key(si, i, t)]).length; },
    total(t = this.track) { return t.stages.reduce((a, s) => a + s.steps.length, 0); },
    doneAll(t = this.track) { return t.stages.reduce((a, s, si) => a + this.stageDone(si, t), 0); },
    toolbar() {
      const s = this.stages[this.stage];
      if (!s) { toolbar.replaceChildren(); return; }
      toolbar.replaceChildren(stat("labStat", `🛠️ ${this.doneAll()}/${this.total()}`),
        ...chips(LAB.map((t) => ({ id: t.id, label: `${t.icon} ${t.title}` })), this.track.id, (id) => this.setTrack(id)),
        ...chips([{ id: "s", label: `${this.stage + 1}. ${s.title}`, wide: true }], "", () => this.openSheet()));
    },
    setTrack(id) {
      const t = LAB.find((x) => x.id === id);
      if (!t || t === this.track) { this.openSheet(); return; }
      this.track = t; S.ui.labTrack = id; save();
      this.stage = Math.min((S.ui.labStage || {})[id] || 0, t.stages.length - 1);
      this.render();
    },
    open(si, stepIdx) {
      this.stage = si; (S.ui.labStage ||= {})[this.track.id] = si; save();
      this.render(stepIdx);
    },
    render(stepIdx) {
      this.toolbar();
      const f = this.feed; f.replaceChildren(); f._current = null;
      const s = this.stages[this.stage];
      if (!s) { f.appendChild(card(`<h2>Lab coming soon</h2>`)); return; }
      f.appendChild(this.cover(s));
      s.steps.forEach((st, i) => f.appendChild(this.stepEl(s, st, i)));
      f.appendChild(this.endCard());
      const first = stepIdx ?? s.steps.findIndex((_, i) => !S.lab[this.key(this.stage, i)]);
      requestAnimationFrame(() => { const t = first > 0 ? f.children[first + 1] : f.children[0]; f.scrollTop = t ? t.offsetTop : 0; f._check(); });
    },
    cover(s) {
      const si = this.stage, done = this.stageDone(si);
      const node = card(`
        <div class="meta"><span class="badge accent">${this.track.icon} ${esc(this.track.title)} · Stage ${si + 1} of ${this.stages.length}</span>${s.time ? `<span>⏱ ${esc(s.time)}</span>` : ""}<span>${done}/${s.steps.length} steps done</span></div>
        <div class="big">${s.icon}</div><h2>${esc(s.title)}</h2>
        <div class="body">${renderBlocks(s.intro)}</div>
        <div class="lbl">Steps</div><ol class="lessons">${s.steps.map((st, i) => `<li class="${S.lab[this.key(si, i)] ? "ticked" : ""}">${esc(st.title)}</li>`).join("")}</ol>
        <p class="muted">Swipe up to start ↑</p>`, "cover");
      hydrate(node, s.intro);
      return node;
    },
    stepEl(s, st, i) {
      const si = this.stage, k = this.key(si, i), done = !!S.lab[k];
      const node = card(`
        <div class="meta"><span class="badge accent">${s.icon} Stage ${si + 1}</span><span>Step ${i + 1}/${s.steps.length}</span>${done ? `<span class="badge good">done</span>` : ""}</div>
        <div class="progress"><i style="width:${((i + 1) / s.steps.length) * 100}%"></i></div>
        <h2>${esc(st.title)}</h2>
        <div class="body">${renderBlocks(st.blocks)}</div>
        <button type="button" class="btn ${done ? "" : "primary"} mark">${done ? "✓ Step done" : "Mark step done ✓"}</button>`, "lab");
      const mark = node.querySelector(".mark");
      const setDone = () => { S.lab[k] = 1; save(); mark.textContent = "✓ Step done"; mark.classList.remove("primary"); const st2 = $("#labStat"); if (st2) st2.textContent = `🛠️ ${this.doneAll()}/${this.total()}`; };
      const needs = st.blocks.filter((b) => b.type === "term" || b.type === "check").length;
      let got = 0;
      const progress = () => { got++; if (got >= needs) setDone(); };
      hydrate(node, st.blocks, { onTerm: progress, onCheck: progress });
      mark.onclick = () => { setDone(); setTimeout(() => step(this.feed, 1), 250); };
      return node;
    },
    endCard() {
      const si = this.stage, next = this.stages[si + 1];
      const other = LAB.find((t) => t !== this.track);
      const node = card(`<div class="big center">🎉</div><h2 class="center">Stage ${si + 1} complete</h2>
        ${next ? `<button type="button" class="btn primary" data-next>Next stage: ${next.icon} ${esc(next.title)} →</button>` : `<p class="center">You've finished the ${esc(this.track.title)} track. ${esc(this.track.summary || "")}</p>${other ? `<button type="button" class="btn primary" data-track>Try the ${other.icon} ${esc(other.title)} track →</button>` : ""}`}
        <button type="button" class="btn" data-list>☰ All stages</button>`);
      node.querySelector(".card-inner").classList.add("center-col");
      if (next) node.querySelector("[data-next]").onclick = () => this.open(si + 1, 0);
      const tb = node.querySelector("[data-track]"); if (tb) tb.onclick = () => this.setTrack(other.id);
      node.querySelector("[data-list]").onclick = () => this.openSheet();
      return node;
    },
    openSheet() {
      openSheet("Build Lab", (body) => {
        LAB.forEach((t) => {
          body.appendChild(el("h3", "", `${t.icon} ${esc(t.title)} · ${this.doneAll(t)}/${this.total(t)} steps`));
          if (t.summary) body.appendChild(el("p", "muted small", esc(t.summary)));
          t.stages.forEach((s, si) => {
            const d = this.stageDone(si, t), pct = Math.round((d / s.steps.length) * 100);
            const b = el("button", "mod", `<span class="num">${s.icon}</span><span>${si + 1}. ${esc(s.title)}</span><span class="pct">${d}/${s.steps.length}</span><div class="progress"><i style="width:${pct}%"></i></div>`);
            b.type = "button"; b.setAttribute("aria-current", String(t === this.track && si === this.stage));
            b.onclick = () => { sheet.close(); if (t !== this.track) { this.track = t; S.ui.labTrack = t.id; } this.open(si); };
            body.appendChild(b);
          });
        });
      });
    },
  };
  lab.stage = lab.track ? Math.min(((S.ui.labStage || {})[lab.track.id] ?? (lab.track === LAB[0] ? S.ui.stage : 0)) || 0, lab.stages.length - 1) : 0;

  // ================================================================= NEWS
  const news = {
    loaded: false,
    render() {
      toolbar.replaceChildren(el("span", "stat", "Live posts from dev.to and Hacker News"));
      if (this.loaded) return;
      const f = document.createElement("iframe"); f.src = "feed/index.html"; f.title = "DevOps news feed";
      $("#view-news").appendChild(f); this.loaded = true;
    },
  };

  // ================================================================= sheet, tabs, keys
  const sheet = $("#sheet");
  sheet.addEventListener("click", (e) => { if (e.target === sheet || e.target.closest("[data-close]")) sheet.close(); });
  function openSheet(title, fill) {
    $("#sheetTitle").textContent = title;
    const body = $("#sheetBody"); body.replaceChildren(); fill(body);
    sheet.showModal();
    body.querySelector('[aria-current="true"]')?.scrollIntoView({ block: "center" });
  }

  const views = { learn, lab, quiz, scen, news };
  const rendered = {};
  const tabs = {
    current: null,
    show(name) {
      this.current = name; S.ui.tab = name; save();
      document.querySelectorAll(".view").forEach((v) => (v.hidden = v.dataset.tab !== name));
      document.querySelectorAll(".tabbar button").forEach((b) => b.setAttribute("aria-current", b.dataset.tab === name ? "page" : "false"));
      const v = views[name];
      if (!rendered[name] || v.dirty) { v.render(); rendered[name] = true; } else if (v.toolbar) v.toolbar(); else v.render();
      if (v.feed) { v.feed.focus({ preventScroll: true }); v.feed._current && diagrams.near(v.feed._current); }
    },
  };
  document.querySelectorAll(".tabbar button").forEach((b) => (b.onclick = () => tabs.show(b.dataset.tab)));

  watchCurrent(learn.feed, (c) => learn.onShow(c));
  watchCurrent(lab.feed);
  watchCurrent(scen.feed);
  watchCurrent(quiz.feed);
  quiz.feed._more = () => { const f = quiz.feed; if (f.scrollTop + f.clientHeight * 4 > f.scrollHeight) quiz.more(); };

  document.addEventListener("keydown", (e) => {
    if (sheet.open || e.metaKey || e.ctrlKey || e.altKey || e.target.matches("input, textarea, select")) return;
    const v = views[tabs.current], feed = v && v.feed;
    if (!feed) return;
    const cur = feed._current;
    const key = e.key.toLowerCase();
    if (["a", "b", "c", "d"].includes(key)) {
      const m = cur && (cur._mcq || cur.querySelector(".mcq"));
      const mm = m && (m._choose ? m : m.closest?.(".mcq"));
      if (mm && mm._choose) { mm._choose("abcd".indexOf(key)); return; }
    }
    switch (e.key) {
      case "j": case "ArrowDown": case " ": e.preventDefault(); step(feed, 1); break;
      case "k": case "ArrowUp": e.preventDefault(); step(feed, -1); break;
      case "m": tabs.current === "lab" ? lab.openSheet() : learn.openSheet(); break;
      case "1": tabs.show("learn"); break;
      case "2": tabs.show("lab"); break;
      case "3": tabs.show("quiz"); break;
      case "4": tabs.show("scen"); break;
      case "5": tabs.show("news"); break;
      default: return;
    }
  });

  tabs.show(S.ui.tab && views[S.ui.tab] ? S.ui.tab : "learn");
  if ("serviceWorker" in navigator && /^https:|^http:\/\/localhost/.test(location.href)) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
