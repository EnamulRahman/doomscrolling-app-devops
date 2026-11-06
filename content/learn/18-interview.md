---
id: interview
title: Interview mastery: Memos
level: Advanced
icon: 🎤
topic: Memos
summary: Your 60-second pitch, how to tell project stories, the improvements roadmap and how to handle questions you can't answer.
---

## Your pitch

### The 60-second version
Say this out loud until it's natural:

> “I deployed the open-source **Memos** app to AWS at **tm.myegh.com**. It runs on **ECS Fargate in private subnets** across **two AZs**, behind a public **ALB** that redirects HTTP to HTTPS using an **ACM** certificate validated automatically through **Route 53**. The image is a **three-stage Docker build**, 2.79 GB down to 75.8 MB, and runs as a non-root user. Everything is **Terraform**: a bootstrap stack for state and OIDC, then seven modules, with **S3 remote state and native locking**. **GitHub Actions** builds and deploys with **OIDC**, so there are no stored AWS keys. tfsec scans every run, a post-deploy check hits **/healthz**, and I can **roll back** by redeploying any previous commit SHA.”

### The diagram you should be able to draw
```mermaid
flowchart TB
  U([User]) --> R53[Route 53 alias] --> ALB["ALB · public subnets<br/>80→301→443 · ACM"]
  ALB -->|8081 · SG→SG| T["ECS Fargate task · private subnets<br/>non-root · 0.25 vCPU / 512 MB"]
  T --> NAT[NAT per AZ] --> ECR[(ECR · immutable SHA tags)]
  T --> CW[CloudWatch /ecs/memos]
  GH["GitHub Actions · OIDC"] -->|push image| ECR
  GH -->|terraform apply| TF[(S3 state + lockfile)]
```
> 🔧 **Tip:** practise drawing it on paper in under two minutes. Whiteboard rounds often start with "draw me your project".

### Know your known limits
Say these **before** the interviewer finds them. It shows maturity:
1. SQLite data lives **inside** the container, so it's lost when the task is replaced.
2. **One task**: not truly highly available.
3. The OIDC role is **admin**, and the trust allows any branch.
4. The target group checks `/`, not `/healthz`.
5. No alarms, flow logs or WAF yet (cost trade-offs, documented).

## Telling stories

### The story structure
Use **Situation → Problem → How I found it → Fix → Lesson**. Keep each to about 90 seconds.

```mermaid
flowchart LR
  S[Situation] --> P[Problem] --> F[How I found it] --> X[Fix] --> L["Lesson ⭐<br/>(what you do differently now)"]
```
The **lesson** is what interviewers remember. It shows you learn.

### Your eight stories
| # | Story | Lesson |
|---|---|---|
| 1 | OIDC wouldn't authenticate | the trust policy `sub` must match exactly |
| 2 | `.gitignore` hid `cmd/memos/main.go` | anchor patterns: `/memos` |
| 3 | Go 1.23 image vs newer `go.mod` | match toolchain versions |
| 4 | Port drift 5230 ↔ 8081 | define the port once |
| 5 | CGO needed C libraries | `CGO_ENABLED=0` → static binary |
| 6 | 2.79 GB image | multi-stage → 75.8 MB |
| 7 | Immutable tags broke re-runs | check ECR first, reuse the image |
| 8 | ACM records already existed | `import` blocks |

Learn 1, 2 and 6 really well.

### Example: story 1
- **Situation:** first pipeline run deploying Memos with GitHub Actions.
- **Problem:** the AWS login step failed. The role couldn't be assumed.
- **Found it:** tried several "Test OIDC" commits and a downgrade of the action, which didn't help. I briefly used static keys **only** to unblock the rest of the pipeline.
- **Fix:** the trust policy's `sub` didn't match the renamed repo. I rebuilt the provider and role with `aud = sts.amazonaws.com` and `sub` like `repo:EnamulRahman/memos-aws-infra:*`, then moved it into the bootstrap stack and removed the static keys.
- **Lesson:** OIDC failures are almost always the trust policy, so check `sub`/`aud` against the token's claims first.

### Check
? In a project story, which part do interviewers value most?
- [ ] How long it took
- [ ] Which tools you used
- [x] What you learned and now do differently
- [ ] Who caused the problem
> The **lesson** shows judgement and growth, and stops the story being just a list of facts.

## The roadmap: what you'd improve

### Ordered by impact
```mermaid
flowchart LR
  A["1. Data tier<br/>RDS Postgres Multi-AZ<br/>(or EFS)"] --> B["2. HA<br/>desired_count ≥ 2<br/>+ autoscaling"]
  B --> C["3. Safety<br/>circuit breaker rollback<br/>TG → /healthz"]
  C --> D["4. Least privilege<br/>scoped CI role<br/>sub → main / env"]
  D --> E["5. Delivery<br/>plan on PR<br/>prod approval"]
  E --> F["6. Ops<br/>alarms · dashboards<br/>ECR in bootstrap"]
```

### How to answer "what would you improve?"
Pick **one**, explain **why first**, and say **how**:
> “First I'd move the data out of the container. Memos supports Postgres, so I'd add RDS in Multi-AZ, pass the DSN from Secrets Manager through the task definition, and allow 5432 only from the ECS security group. That makes the tasks stateless, which unlocks running two or more across both AZs.”

## Handling hard questions

### When you don't know
Don't bluff. Bridge from what you **do** know:
> “I haven't used Datadog hands-on yet, but I understand it's an observability platform for metrics, logs, traces and APM. I've used CloudWatch Logs and metrics for Memos, so the troubleshooting principles carry over, and I'd expect to pick it up quickly.”

### Think out loud
For scenario questions:
1. **Clarify:** "Is this production? Did anything change recently?"
2. **Structure:** "I'd work outside in: DNS, load balancer, targets, the task, then the logs."
3. **Prioritise:** "If users are affected, I'd roll back first."
4. **Close:** "Then I'd add an alarm so we catch it sooner next time."

### Questions to ask them
- "What does the deployment pipeline look like today, and what would you most like to improve?"
- "How do you handle on-call and post-mortems?"
- "What would success look like in my first six months?"
- "Which skills are essential from day one, and which would I be supported to grow?"

### Check
? An interviewer asks about a tool you've never used. What's the best approach?
- [ ] Pretend you've used it
- [ ] Say "I don't know" and stop
- [x] Be honest, explain what you understand it does, and link it to similar tools you have used
- [ ] Change the subject to Memos
> Honesty plus a bridge to related experience shows you can learn, which is what they're really testing.
