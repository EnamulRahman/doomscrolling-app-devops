# DevOps Scroll

A doomscrolling DevOps course. It takes an absolute beginner to someone who can **containerise an app, build its cloud infrastructure with Terraform and automate every change with CI/CD**, one swipe at a time.

The whole course uses one worked example: **[Memos](https://github.com/usememos/memos)**, an open-source note-taking app. You learn the concepts with it, then build a production-style AWS platform for it yourself in the Build Lab:

```
Memos source → Docker (multi-stage image) → Terraform (VPC, ALB, ECS Fargate, ECR, ACM, Route 53)
            → GitHub Actions (build, scan, deploy with OIDC, health check, rollback)
```

All content is built into the app: no backend, no accounts and no project of your own needed to start. It works offline once installed, and progress is saved on each device.

## Five tabs

| Tab | What it is |
| --- | --- |
| 📚 **Learn** | 18 modules from **Beginner → Intermediate → Advanced**: 80 lessons and ~310 short cards, one idea each, with ~80 diagrams, real code from the example and a quick check after every lesson |
| 🛠️ **Lab** | The **Build Lab**: 15 stages and 58 steps from an empty laptop to the example app running on AWS: Docker → Terraform bootstrap → network → load balancer → ECS → GitHub Actions → break-it drills → production upgrades. Includes a practice terminal and checkpoint questions |
| 🧠 **Quiz** | ~220 multiple-choice questions from [tech-vault](https://github.com/moabukar/tech-vault) and revision notes, plus every lesson check. Explanations after each answer; missed questions come back |
| 🎯 **Scenarios** | 35 interview scenarios as multiple choice with feedback on every option. 21 are set in the example project |
| 📰 **News** | Live DevOps posts from dev.to and Hacker News (`feed/`) |

## Use your own values

The example uses placeholders: `your-username` (GitHub), `example.com` / `memos.example.com` (domain), `memos-tfstate-example` (state bucket) and `123456789012` (AWS account). Swap in your own when you build it for real.

> ⚠️ Building the Lab for real creates billable AWS resources (NAT gateways and the load balancer cost money every hour). Set a budget alert first and run `terraform destroy` when you finish practising.

## Run it

```bash
python3 -m http.server 8000      # then open http://localhost:8000
```
On a phone: host it (e.g. GitHub Pages), open the URL and choose **Add to Home Screen**.
Keyboard: `j`/`k` scroll · `a`–`d` answer · `m` menu · `1`–`5` switch tab.

## Editing content

All content is Markdown in `content/` (format: [content/README.md](content/README.md)):

```bash
pip install -r scripts/requirements.txt
python3 scripts/build_content.py
```

## Credits

[Memos](https://github.com/usememos/memos) is the example app (MIT). Questions adapted from [tech-vault](https://github.com/moabukar/tech-vault) (Apache-2.0). Diagrams by [Mermaid](https://mermaid.js.org) (MIT, bundled in `vendor/`).
