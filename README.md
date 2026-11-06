# DevOps Scroll

A doomscrolling DevOps course. It takes you from an absolute beginner to someone who can build, explain and defend a production AWS platform, one swipe at a time. Everything is built around my own project, [memos-aws-infra](https://github.com/EnamulRahman/memos-aws-infra).

It's a static web app with no backend and no accounts, and it works offline once installed. Progress is saved on each device.

## Five tabs

| Tab | What it is |
| --- | --- |
| 📚 **Learn** | 18 modules from **Beginner → Intermediate → Advanced**: 80 lessons and ~310 short cards, one idea each, with ~80 diagrams, real code from the Memos repo and a quick check after every lesson |
| 🛠️ **Lab** | The **Build Lab**: 15 stages and 58 steps that rebuild Memos from an empty laptop to `tm.myegh.com`, with a practice terminal (type the command or tap "Run it for me"), the real Terraform, Dockerfile and workflows, and checkpoint questions |
| 🧠 **Quiz** | ~220 multiple-choice questions drawn from [tech-vault](https://github.com/moabukar/tech-vault) and my revision guides, plus every lesson check. Explanations after each answer; missed questions come back. Filter by topic, level or source |
| 🎯 **Scenarios** | 35 interview scenarios as multiple choice with feedback on **every** option: 21 about my Memos project, the rest from tech-vault's scenario questions |
| 📰 **News** | Live DevOps posts from dev.to and Hacker News (`feed/`) |

The original two guides (*DevOps Revision Guide* and *AWS From Zero*) are still in the module list under **📖 Reference**. The course itself is written fresh, using the guides as one source among several, checked against the real repo and AWS behaviour.

## Curriculum

**Beginner:** Start here · How computers & the internet work · Linux · Bash · Networking · Git & GitHub · Docker · Cloud & AWS foundations (IAM)
**Intermediate:** Compute, storage & databases · VPC · Load balancers, DNS & certificates · ECR/ECS/Fargate · Terraform · CI/CD & OIDC
**Advanced:** Monitoring & troubleshooting · Security, reliability & cost · Kubernetes essentials · Interview mastery

## Run it

```bash
python3 -m http.server 8000      # then open http://localhost:8000
```
On a phone: host it with GitHub Pages, open the URL and choose **Add to Home Screen**.
Keyboard: `j`/`k` scroll · `a`–`d` answer · `m` menu · `1`–`5` switch tab.

## Editing content

All content is Markdown in `content/` (see [content/README.md](content/README.md)):

```bash
pip install -r scripts/requirements.txt
python3 scripts/build_content.py
```
`scripts/build_data.py` rebuilds the guides' reference library from the PDFs (they aren't committed).

## Credits

Questions adapted from [tech-vault](https://github.com/moabukar/tech-vault) (Apache-2.0). Diagrams by [Mermaid](https://mermaid.js.org) (MIT, bundled in `vendor/`).
