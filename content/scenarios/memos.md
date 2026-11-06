---
source: Your Memos project
---

## Every note disappeared overnight
@ topic: Reliability · level: Mid · files: Dockerfile, infra/modules/ecs/main.tf
The Memos ECS task was replaced overnight after a deploy. When users log back in, **all their notes are gone**. The Dockerfile sets `MEMOS_DATA=/var/opt/memos`, and the task definition has no volumes.
? What happened, and what's the best long-term fix?
- [ ] The ALB cached old responses: clear the cache
  > The ALB doesn't cache. Data loss after a task replacement points at the task's own storage.
- [x] SQLite lived on the task's temporary storage, which is deleted with the task. Move the data to RDS Postgres (MEMOS_DRIVER/MEMOS_DSN) or mount EFS
  > Correct. Containers are disposable, so state must live outside them. RDS Multi-AZ with the DSN from Secrets Manager is the strongest fix; EFS is the quick one.
- [ ] Increase task memory so the database fits in RAM
  > More memory doesn't make data survive a replacement.
- [ ] Turn on ECR scan-on-push
  > Image scanning has nothing to do with runtime data.
> **Takeaway:** stateless vs stateful containers. Raise this limitation yourself before the interviewer does.

## Is Memos highly available?
@ topic: Reliability · level: Mid · files: infra/main.tf, infra/modules/vpc/main.tf
The interviewer says: "Your VPC spans two AZs with a NAT gateway in each. So Memos is highly available, right?"
? What's the most accurate answer?
- [ ] Yes: two AZs means HA
  > The **network** is multi-AZ, but there's only one task, so the **application** isn't.
- [x] Not yet: `desired_count = 1` means one task in one AZ, and data is in-task SQLite. Fix the data tier, then run 2+ tasks across AZs with autoscaling
  > Right. A multi-AZ network is necessary but not enough. You need redundancy at every layer.
- [ ] Yes, because ECS restarts failed tasks
  > Restarting takes minutes and, here, loses the data. That's recovery, not HA.
- [ ] No, because ALBs only work in one AZ
  > ALBs actually require subnets in at least two AZs.
> **Takeaway:** HA means no single point of failure: network, compute **and** data.

## Pipeline says healthy, ALB says unhealthy
@ topic: Troubleshooting · level: Mid · files: infra/modules/alb/main.tf, .github/workflows/deploy.yml
`deploy.yml` curls `https://tm.myegh.com/healthz` and passes. But the target group marked the task unhealthy last week while the app was clearly up.
? Why can they disagree, and what would you change?
- [x] They check different things: the TG requests `/` every 30 s (200–399, 2 failures = unhealthy), while CI hits `/healthz` once. Point the TG at `/healthz` and add a health-check grace period
  > Correct. `/` is the whole web UI. `/healthz` is the dedicated liveness endpoint in `server/server.go`.
- [ ] The ACM certificate is invalid for health checks
  > Health checks go from the ALB to the task over HTTP on 8081, not through the certificate.
- [ ] CloudWatch is delaying the results
  > CloudWatch doesn't run the checks. The ALB does.
- [ ] GitHub Actions uses a different DNS server
  > DNS isn't involved in the ALB's own health checks.
> **Takeaway:** the ALB decides health. Make the ALB and the pipeline use the same signal.

## 503 straight after a deploy
@ topic: Troubleshooting · level: Junior · files: infra/modules/security/main.tf, infra/modules/ecs/main.tf
Right after a deploy, `tm.myegh.com` returns **503 Service Temporarily Unavailable**.
? What should you check first?
- [ ] The Route 53 TTL
  > DNS is fine: the request reached the ALB, which is what answered 503.
- [x] Whether any targets are registered: ECS service events and the task's stopped reason, then logs, port 8081 everywhere and the SG chain
  > Correct. A 503 from an ALB means no registered targets, so the task isn't running or never registered.
- [ ] Renew the ACM certificate
  > A certificate problem fails the TLS handshake. It wouldn't produce a 503.
- [ ] Restart the NAT gateway
  > NAT only affects outbound traffic from the task (e.g. image pulls). Check ECS first.
> **Takeaway:** 502 = bad reply · **503 = no targets** · 504 = timeout. And if a release broke things, roll back first.

## Roll back a bad release fast
@ topic: CI/CD · level: Mid · files: .github/workflows/deploy.yml, infra/modules/ecr/main.tf
A release is live and users are seeing errors. You need the previous version back **now**.
? What's the fastest safe rollback with this pipeline?
- [ ] `git revert`, then wait for the full build and deploy
  > It works, but it rebuilds an image and takes much longer. Use it to fix forward afterwards.
- [x] Run **Deploy** manually (`workflow_dispatch`) with the previous good commit SHA. Its immutable image is still in ECR
  > Correct. Immutable SHA tags guarantee you get exactly the old image, and Terraform rolls the ECS service back.
- [ ] Push the old image again as `latest`
  > Memos doesn't deploy `latest`, and ECR tags are immutable, so this fails.
- [ ] Delete the ECS service
  > That's a full outage, not a rollback.
> **Takeaway:** immutable SHA tags make rollback safe. Next step: the ECS deployment circuit breaker for **automatic** rollback.

## The CI role has AdministratorAccess
@ topic: Security · level: Mid · files: bootstrap/oidc.tf
A reviewer points out that `github-actions-role` has **AdministratorAccess**, and its trust policy allows `repo:EnamulRahman/memos-aws-infra:*`.
? Which response is the best improvement?
- [ ] Switch back to static access keys, which are easier to control
  > Long-lived keys are worse: they can leak and never expire.
- [ ] It's fine because OIDC is secure
  > OIDC removes stored keys, but whatever assumes the role still gets **admin**.
- [x] Narrow `sub` to `ref:refs/heads/main` or `environment:production`, replace admin with least-privilege policies, and split a read-only plan role from the apply role
  > Correct. Limit **who** can assume it and **what** they can do.
- [ ] Delete the OIDC provider
  > That breaks the pipeline without improving anything.
> **Takeaway:** OIDC is a strength of the project. Knowing its weak point (trust scope plus permissions) shows real understanding.

## The AWS bill is higher than expected
@ topic: Cost · level: Mid · files: infra/modules/vpc/main.tf
One small Fargate task, yet the monthly bill is much higher than you expected.
? What's the biggest likely driver, and a sensible saving?
- [ ] The Fargate task: switch to Lambda
  > 0.25 vCPU / 512 MB is cheap. The always-on networking costs far more.
- [x] Two NAT gateways (per hour + per GB), plus the ALB and public IPv4. Use one NAT in non-prod, an S3 gateway endpoint (free), and `destroy.yml` when idle
  > Correct. NAT gateways are the classic hidden cost. Note the trade-off: one NAT is a single point of failure.
- [ ] ECR storage of one image
  > Pennies.
- [ ] CloudWatch with 7-day retention
  > Small at this scale.
> **Takeaway:** know where cloud money goes, and say the trade-off out loud.

## Two applies at once
@ topic: Terraform · level: Junior · files: infra/provider.tf, bootstrap/state.tf
You and a colleague run `terraform apply` on Memos at exactly the same time.
? What happens?
- [ ] Both succeed and the results merge
  > Terraform never merges concurrent applies.
- [ ] The state file gets corrupted
  > Locking exists to prevent exactly this.
- [x] The second run fails with "Error acquiring the state lock", because `use_lockfile = true` created a `.tflock` object in S3
  > Correct. When the first apply finishes, the second person should plan again against the new state.
- [ ] The newest apply overwrites the first
  > Not with locking enabled.
> **Takeaway:** remote state + locking (S3 native, Terraform 1.10+). Use `force-unlock` only when you're sure nothing is running.

## Someone opened port 22 in the console
@ topic: Terraform · level: Junior · files: infra/modules/security/main.tf
During an incident, someone added an SSH rule to the ECS security group by hand in the console.
? What's the right way to handle it?
- [x] Detect the drift with `terraform plan -refresh-only`, then remove it (or import it if it should stay). Prevent repeats: changes only via PRs, CloudTrail/Config alerts
  > Correct. Code is the source of truth. Memos uses separate SG rule resources, so a hand-made rule may not even be in state.
- [ ] Leave it: Terraform will never notice
  > That's an unreviewed hole in your security group.
- [ ] Destroy and recreate the whole VPC
  > A massive overreaction that causes an outage.
- [ ] Commit the state file to Git
  > Never commit state.
> **Takeaway:** drift detection, plus a culture of "no console changes".

## Infra change merged, nothing deployed
@ topic: CI/CD · level: Mid · files: .github/workflows/build.yml, .github/workflows/deploy.yml
You change `infra/modules/alb/main.tf`, merge to `main`… and nothing deploys.
? Why?
- [ ] tfsec silently blocked it
  > tfsec would fail the run loudly. Here, no run started at all.
- [x] `build.yml` only triggers on `app/**`, `Dockerfile` and `.dockerignore`, and `deploy.yml` only runs after a build (or manually)
  > Correct. Run Deploy by hand with the live SHA, or add an infra trigger plus a PR plan.
- [ ] Terraform needs a pull request to apply
  > Terraform doesn't know about PRs.
- [ ] The OIDC role can't modify ALBs
  > It's admin, so it can, and anyway the pipeline never ran.
> **Takeaway:** know your pipeline's triggers. This leads naturally to "plan on every PR".

## Critical CVE in the image
@ topic: Security · level: Junior · files: Dockerfile, infra/modules/ecr/main.tf
ECR scan-on-push reports a **critical** vulnerability in the latest Memos image.
? What's the best response?
- [ ] Turn off scan-on-push
  > That hides the problem rather than fixing it.
- [x] Find whether it's in the base image or a Go module, patch (newer `alpine:3.21` / `apk upgrade`, or bump `go.mod`), rebuild under a new SHA and deploy. Add a CI scan that fails on criticals
  > Correct. Immutable tags mean the fix ships as a new version.
- [ ] Overwrite the same tag with a rebuilt image
  > Tags are immutable, and you'd lose traceability.
- [ ] Ignore it, because the task is in a private subnet
  > Private subnets reduce exposure but don't remove the risk.
> **Takeaway:** small multi-stage images and a non-root user shrink the attack surface, but you still need a patching process.

## Giving Memos a database password
@ topic: Security · level: Mid · files: infra/modules/iam/main.tf, infra/modules/ecs/main.tf
You've added RDS and need to give Memos its DSN, which includes a password.
? Where should it go, and which role needs permission?
- [ ] In `terraform.tfvars`, committed to Git
  > Secrets in Git stay in the history forever.
- [ ] Baked into the Docker image as an ENV
  > Anyone who can pull the image can read it.
- [x] In Secrets Manager, referenced in the task definition's `secrets`. The **execution role** needs `secretsmanager:GetSecretValue` on it
  > Correct. ECS fetches it at start-up, before your code runs.
- [ ] In Secrets Manager, with the **task role** given read access
  > The task role is for your app's own AWS calls. Injection at start-up uses the execution role.
> **Takeaway:** execution role (ECS: pull, logs, secrets) vs task role (your code).

## Tasks stop with CannotPullContainerError
@ topic: Troubleshooting · level: Junior · files: infra/modules/vpc/main.tf, infra/modules/security/main.tf, infra/modules/iam/main.tf
New tasks keep stopping with **CannotPullContainerError**. They run in private subnets with no public IP.
? Which of these is **not** a plausible cause?
- [ ] The private route table has no route to the NAT gateway
  > Plausible: without NAT (or VPC endpoints) the task can't reach ECR.
- [ ] The execution role is missing ECR permissions
  > Plausible: pulling uses the execution role.
- [x] The ALB health check path is wrong
  > Correct, this one is **not** a cause. Health checks only matter once the container is running, and pulling happens before that.
- [ ] The SHA tag doesn't exist in ECR
  > Plausible: deploy.yml checks this, but a manual change could skip it.
> **Takeaway:** a private task reaching ECR needs routing + SG egress 443 + IAM + the image to exist.

## Re-run fails: tag already exists
@ topic: CI/CD · level: Junior · files: .github/workflows/build.yml
You re-run a failed pipeline on the same commit and the push fails because `memos:<sha>` already exists.
? What's the right fix?
- [ ] Make ECR tags mutable
  > That throws away the safety immutability gives you.
- [ ] Add a timestamp to every tag
  > Then the tag no longer maps cleanly to the commit.
- [x] Make the build idempotent: `describe-images` first, reuse the image if it exists, build only on `ImageNotFoundException`, and fail loudly on any other error
  > Correct. That's exactly what `build.yml` does now.
- [ ] Delete the old image before each push
  > You'd destroy rollback targets.
> **Takeaway:** keep the safety feature and make the automation safe to re-run.

## ECR is in the stack you destroy
@ topic: Terraform · level: Mid · files: infra/modules/ecr/main.tf, .github/workflows/destroy.yml
`destroy.yml` tears down `infra/`, which includes ECR with `force_delete = true`.
? What's the problem, and the fix?
- [x] Destroying wipes every image, including rollback targets. Move ECR to `bootstrap/` (long-lived), drop `force_delete` and add a lifecycle policy
  > Correct. Deployment artefacts have a longer lifecycle than the environment.
- [ ] No problem: images are rebuilt anyway
  > Rebuilding isn't guaranteed to be identical, and rollback needs the old artefacts.
- [ ] Turn off image scanning
  > Unrelated.
- [ ] Make ECR public
  > A security regression.
> **Takeaway:** group resources by **lifecycle**. This is the improvement from your prep doc.

## Logs from two weeks ago are gone
@ topic: Observability · level: Junior · files: infra/modules/ecs/main.tf
A user reports a problem from 14 days ago. CloudWatch shows nothing.
? Why?
- [ ] The awslogs driver was off
  > Recent logs exist, so the driver works.
- [x] `/ecs/memos` has `retention_in_days = 7`, so older events were deleted. Raise retention or export to S3 for cheap long-term storage
  > Correct. It was a deliberate cost trade-off.
- [ ] CloudTrail deleted them
  > CloudTrail records API calls. It doesn't manage log retention.
- [ ] The NAT gateway dropped them
  > Logs go via the awslogs driver. Retention is the reason they're gone.
> **Takeaway:** know your retention settings, and add alarms so you hear about issues in time.

## Why all the tfsec ignores?
@ topic: Security · level: Mid · files: infra/modules/vpc/main.tf, infra/modules/ecs/main.tf, infra/modules/security/main.tf
"tfsec runs every pipeline, but you have several `tfsec:ignore` comments. Isn't that just hiding problems?"
? What's the strongest answer?
- [ ] "tfsec has too many false positives, so I ignore it"
  > Dismissive, and it sounds careless.
- [x] "Each ignore is a documented trade-off with a reason next to it: flow logs, Container Insights and customer KMS keys off for cost; a public ALB because it's a website; egress 443 for ECR via NAT. In a company I'd revisit them and track each as a ticket"
  > Correct. That's judgement, not silencing a tool.
- [ ] "I'll remove tfsec so there's no noise"
  > That removes a safety net.
- [ ] "The ignores were added by mistake"
  > Not true here, and it undermines your credibility.
> **Takeaway:** interviewers want to see that you make **documented** trade-offs.

## Container keeps dying with exit 137
@ topic: Troubleshooting · level: Junior · files: infra/main.tf
The Memos task stops every few hours with **exit code 137**.
? What's going on?
- [ ] The command wasn't found
  > That's 127.
- [x] SIGKILL, almost always out of memory against the 512 MB limit. Confirm in the stopped reason, raise the memory (a valid Fargate pair), find the leak and alarm on MemoryUtilization
  > Correct. 137 = 128 + 9.
- [ ] A normal shutdown
  > A graceful stop is 143 (SIGTERM).
- [ ] The health check port is wrong
  > That leads to the task being replaced, not exit 137.
> **Takeaway:** exit codes are quick wins: 0, 1, 127, 137, 143.

## Stand up a second region
@ topic: Terraform · level: Senior · files: infra/main.tf, infra/provider.tf, infra/terraform.tfvars
The business wants the platform in a new Region (e.g. me-central-1, UAE) alongside eu-west-1.
? What's the best approach with this Terraform?
- [ ] Add the new Region's resources to the existing state
  > One bad apply could then break both Regions.
- [x] Reuse the modules with per-Region tfvars and **separate state** (its own backend key), a non-overlapping CIDR, a regional ACM cert and ECR, Route 53 routing, and a per-Region data store for residency
  > Correct. Isolate the blast radius, reuse the code.
- [ ] Copy-paste the whole repo for the new Region
  > Duplicated code drifts apart. Modules exist to avoid this.
- [ ] Use the same VPC CIDR in both Regions
  > That blocks any future peering or Transit Gateway.
> **Takeaway:** state isolation, reusable modules and data residency. That matches the role you interviewed for.

## Auto-apply on main with no review
@ topic: CI/CD · level: Mid · files: .github/workflows/deploy.yml
`deploy.yml` runs `terraform apply -auto-approve tfplan` with no human review.
? How would you add control without losing speed?
- [ ] Run apply manually from your laptop instead
  > That loses automation and an audit trail.
- [x] Post `terraform plan` on every PR for review, use a protected `production` environment with required reviewers for apply, and alert or block on destroys of critical resources
  > Correct. People review the plan, and the gate is enforced by the platform.
- [ ] Remove `-out=tfplan`
  > The saved plan is good: it guarantees you apply exactly what was planned.
- [ ] Only deploy on Fridays
  > That doesn't add review, and Friday deploys are a meme for a reason.
> **Takeaway:** balance speed and safety. This pairs naturally with least-privilege OIDC.

## The .gitignore that broke the build
@ topic: Memos stories · level: Junior · files: .gitignore
CI fails with "no Go files in …/cmd/memos", but it builds fine on your laptop.
? What's the likely cause, based on a real Memos bug?
- [x] A `.gitignore` pattern `memos` (meant for the binary) also matched `cmd/memos/`, so `main.go` was never committed. Fix: `/memos`
  > Correct. A leading `/` anchors the pattern to the repo root.
- [ ] The Go version is wrong on the runner
  > That gives version errors, not missing files.
- [ ] CI doesn't support Go
  > It does.
- [ ] The Dockerfile is in the wrong folder
  > The file is missing from the repo itself.
> **Takeaway:** "works on my machine" often means files that exist locally but were never committed. Check `git status` and `git ls-files`.
