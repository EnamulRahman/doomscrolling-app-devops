# DevOps Scroll

A doomscrolling app for learning DevOps. You swipe up through one card at a time, the way you would on TikTok, but every card teaches you something, tests you or prepares you for an interview. Everything is built around my own project, [memos-aws-infra](https://github.com/EnamulRahman/memos-aws-infra).

It's a static web app: no backend, no build step to run it and no accounts. Progress is saved on each device.

## The four tabs

| Tab | What's in it | Where it comes from |
| --- | --- | --- |
| 📚 **Learn** | 48 modules broken into ~700 swipeable cards, with tables, code, ⚡ quick-recall boxes and links to the matching files in my repo | My **DevOps Revision Guide** (64 pages) and **AWS From Zero** (80 pages) |
| 🧠 **Quiz** | ~500 flashcards: tap to reveal, then mark ✓ Got it or ✗ Missed it. Missed cards come back later in the session and float to the top next time | The guides' tech-vault question bank, "Questions to answer out loud", "Check yourself" questions with answer keys and both glossaries, plus [tech-vault](https://github.com/moabukar/tech-vault)'s Kubernetes questions. 112 cards also carry tech-vault's full explanation |
| 🎯 **Scenarios** | 57 interview scenarios with model answers and "why it matters" | 21 written about **my Memos project** (`content/memos-scenarios.md`), my 8 interview stories, and tech-vault's scenario questions |
| 📰 **News** | Live DevOps posts from dev.to and Hacker News, with topics, muted words and pinned links you control | `feed/` (see `feed/README.md`) |

## Run it

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Keyboard: `j`/`k` or ↑/↓ to scroll · Space/Enter to reveal · `y` got it · `n` missed it · `m` modules · `1`–`4` switch tab.

## On your phone

1. Push to GitHub, then go to **Settings → Pages → Deploy from a branch → `main` / root**.
2. Open `https://enamulrahman.github.io/doomscrolling-app-devops/` on your phone.
3. **Add to Home Screen** (Safari: Share → Add to Home Screen; Chrome: ⋮ → Install app).
   It opens full-screen with its own icon and works offline once loaded.

On a free GitHub plan, Pages only works for **public** repositories, and the content of both guides is then public.

## Changing the content

The app reads `data/learn.js`, `data/quiz.js` and `data/scenarios.js`. They are generated, so edit the sources and rebuild:

- **Add or edit a Memos scenario:** edit `content/memos-scenarios.md` (the format is described at the top of the file).
- **Updated a guide?** Re-export the PDF and rebuild.

```bash
pip install -r scripts/requirements.txt
git clone --depth 1 https://github.com/moabukar/tech-vault /tmp/tech-vault
python3 scripts/build_data.py "DevOps Revision Guide.pdf" "AWS From Zero.pdf" /tmp/tech-vault
```

The PDFs aren't committed (`sources/` is ignored). Keep them locally and point the script at them.
`scripts/extract_guide.py` reads the guides' structure from the PDF's fonts (parts, sections, subsections, tables, code blocks and ⚡ boxes), so a guide printed the same way rebuilds cleanly. After changing any file, bump `VERSION` in `sw.js` so installed copies pick up the update.

## Credits

Interview questions and explanations from [tech-vault](https://github.com/moabukar/tech-vault) by moabukar and contributors, under the Apache-2.0 licence.
