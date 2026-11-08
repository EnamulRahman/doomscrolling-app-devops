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
| 📚 **Learn** | 21 modules from **Beginner → Intermediate → Advanced**: 96 lessons and ~400 short cards, one idea each, with ~110 diagrams, real code and a quick check after every lesson. Includes a four-module **Kubernetes** track (core → workloads → config & networking → EKS, Helm, GitOps & monitoring) |
| 🛠️ **Lab** | Two hands-on tracks with a practice terminal and checkpoint questions:<br>**🐳 ECS on AWS** (15 stages): Dockerise the Memos example → Terraform (VPC, ALB, ECS Fargate) → GitHub Actions → break-it drills → production upgrades.<br>**☸️ EKS assignment** (15 stages): complete the [CoderCo EKS assignment](https://github.com/CoderCo-Learning/eks-assignment-v1): the 2048 game on EKS with Terraform modules, the NGINX Ingress Controller, Prometheus and Grafana, a Terraform pipeline and a Checkov/Trivy/ECR/deploy pipeline, plus Helm, cert-manager, ExternalDNS, Argo CD and clean-up |
| 🧠 **Quiz** | ~280 multiple-choice questions from [tech-vault](https://github.com/moabukar/tech-vault) and revision notes, plus every lesson check. Explanations after each answer; missed questions come back |
| 🎯 **Scenarios** | 47 interview scenarios as multiple choice with feedback on every option: 21 set in the ECS example project, 12 on Kubernetes and EKS |
| 📰 **News** | Live DevOps posts from dev.to and Hacker News (`feed/`) |

## Use your own values

The example uses placeholders: `your-username` (GitHub), `example.com` / `memos.example.com` (domain), `memos-tfstate-example` (state bucket) and `123456789012` (AWS account). Swap in your own when you build it for real.

> ⚠️ Building either Lab track for real creates billable AWS resources (NAT gateways, load balancers and, for EKS, the control plane cost money every hour). Set a budget alert first and run the clean-up steps when you finish practising.

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
