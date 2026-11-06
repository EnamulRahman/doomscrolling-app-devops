# Memos interview scenarios

Hand-written scenarios about github.com/EnamulRahman/memos-aws-infra. Each one is a question an
interviewer could ask about the project, a model answer, and why it matters. Every fact here matches
the code in that repo. Add your own: copy a block, keep the headings, then run scripts/build_data.py.

Format:  ## Title · Topic: · Level: · Files: (comma-separated repo paths) · question text ·
         ### Answer · ### Why it matters

## The task restarted and every note disappeared
Topic: Memos
Level: Mid
Files: Dockerfile, infra/modules/ecs/main.tf

The ECS task for Memos was replaced overnight (a deploy, or Fargate moved it). When users log back in, **all their notes are gone**. What happened, and how would you fix it?

### Answer
- Memos uses **SQLite by default**, and the Dockerfile sets `MEMOS_DATA=/var/opt/memos`. That folder lives on the task's **ephemeral storage**. The task definition mounts no volume.
- When a task stops, its storage is deleted. A new task starts with an empty database. **Every deploy wipes the data.**
- Fix, in order of preference:
  1. **Use a managed database.** Memos supports MySQL and Postgres through `MEMOS_DRIVER` and `MEMOS_DSN`. Run **RDS Postgres (Multi-AZ)** in private subnets, allow 5432 only from the ECS security group, and pass the DSN from **Secrets Manager** through the task definition's `secrets`.
  2. Or mount **EFS** at `/var/opt/memos` (an `efs_volume_configuration` in the task definition and a mount target in each private subnet). This is quick, but SQLite on a network file system must only ever have **one writer**.
- Add **backups**: RDS automated backups and snapshots, or AWS Backup for EFS.

### Why it matters
This is the biggest known limit in the project, and interviewers love it because it tests whether you understand **stateless vs stateful** containers. Say it before they find it: “containers are disposable, so state has to live outside them.”

## Make Memos highly available
Topic: AWS
Level: Mid
Files: infra/main.tf, infra/modules/ecs/main.tf, infra/modules/vpc/main.tf

The network already spans **two AZs**. Is Memos actually highly available? What would you change?

### Answer
- **No, not yet.** `desired_count = 1`, so there is one task in one AZ. If that task or AZ fails, the site is down until ECS starts a replacement (usually a minute or two, and the SQLite data is lost too).
- The network is ready for HA: two public and two private subnets, a NAT gateway in **each** AZ, and an ALB across both.
- Changes:
  1. Move the data out of the container (RDS Multi-AZ). Several tasks can't share one local SQLite file.
  2. Set `desired_count = 2` or more. ECS spreads tasks across the private subnets, so each AZ gets one.
  3. Add **ECS service auto scaling** (target tracking on CPU around 60–70%, or on ALB request count per target).
  4. Add the **deployment circuit breaker with rollback**, and set `minimum_healthy_percent = 100` so a deploy never drops below full capacity.

### Why it matters
It shows you know the difference between a multi-AZ **network** and a multi-AZ **application**. The network was already in place; the data layer and task count were not.

## The pipeline says healthy, but the target group says unhealthy
Topic: Troubleshooting
Level: Mid
Files: infra/modules/alb/main.tf, .github/workflows/deploy.yml

`deploy.yml` checks `https://tm.myegh.com/healthz` and passes, but last week the ALB marked the task unhealthy while the app was clearly running. Why can these disagree?

### Answer
- They check **different things**. The pipeline curls **`/healthz`** once, 60 seconds after the deploy. The target group's health check requests **`/`** on port 8081 every **30 s**, accepts **200–399**, and needs **2** failures to go unhealthy.
- `/` is the web UI. It can redirect or be slow while assets load, so it measures more than “is the app alive”. Memos has a real `GET /healthz` endpoint in `server/server.go`.
- Fix: point the target group's `health_check.path` at **`/healthz`** so the ALB and the pipeline agree. Also give a slow-starting task a **`health_check_grace_period_seconds`** on the ECS service.
- Debug order: target group health reason → ECS service events → task stopped reason → logs in `/ecs/memos`.

### Why it matters
It tests whether you know **who decides health**. The ALB does: it only sends traffic to healthy targets, and ECS replaces tasks the ALB reports as unhealthy.

## 503 from the load balancer right after a deploy
Topic: Troubleshooting
Level: Junior
Files: infra/modules/security/main.tf, infra/modules/ecs/main.tf, Dockerfile

Straight after a deploy, `tm.myegh.com` returns **503 Service Temporarily Unavailable**. Walk me through how you'd find the cause.

### Answer
- A 503 from an ALB means **no healthy targets are registered**. The ALB itself is fine. The task is either not running or failing health checks.
- Check, layer by layer:
  1. **ECS service events**: is the task starting and then stopping? Read the **stopped reason** (e.g. `CannotPullContainerError`, or exit code 137 for out of memory).
  2. **CloudWatch logs** `/ecs/memos`: did the app crash on start?
  3. **Port**: is it 8081 everywhere? That means `MEMOS_PORT` in the Dockerfile, `containerPort` in the task definition, the target group port and both security group rules. (I hit exactly this: 5230 vs 8081.)
  4. **Security groups**: the ECS SG must allow 8081 **from the ALB SG**, and the ALB SG must allow **egress** to the ECS SG on 8081.
- If the last version worked, **roll back first** (redeploy the previous SHA), then find the root cause.

### Why it matters
Knowing **502 vs 503 vs 504** quickly narrows the search: 502 is a bad reply from the target, 503 is no healthy targets, and 504 is the target taking too long to reply.

## Roll back a bad release in under five minutes
Topic: CI/CD
Level: Mid
Files: .github/workflows/deploy.yml, .github/workflows/build.yml, infra/modules/ecr/main.tf

A release has gone out and users are seeing errors. How do you roll back with this pipeline, and how would you make it automatic?

### Answer
- Every image is tagged with the **full commit SHA**, and ECR tags are **IMMUTABLE**, so an old tag always means exactly the same image.
- `deploy.yml` has a **`workflow_dispatch`** input, `image_tag`. Run it with the **previous good SHA**. It checks that the tag is 40 hex characters and exists in ECR, then runs `terraform plan/apply` with that `image_url`. ECS rolls the service back to the old image.
- To make it automatic, add `deployment_circuit_breaker { enable = true, rollback = true }` to the ECS service. If new tasks can't become healthy, ECS returns to the last working deployment by itself.
- Then fix forward in a normal PR.

### Why it matters
**“Roll back first, debug second”** is what interviewers want to hear. Immutable SHA tags are what make a rollback safe.

## Your OIDC role has AdministratorAccess
Topic: Security
Level: Mid
Files: bootstrap/oidc.tf

A security reviewer points out that `github-actions-role` has **AdministratorAccess**, and its trust policy allows `repo:EnamulRahman/memos-aws-infra:*`. What's the risk, and what would you change?

### Answer
- **Risk 1: too much permission.** Anything that runs in a workflow can do *anything* in the account, including deleting the state bucket or creating users.
- **Risk 2: a wide trust policy.** `:*` matches **any branch, tag, pull request or environment** in the repo. A workflow on any branch could assume an admin role.
- Fix:
  1. Narrow `sub` to `repo:EnamulRahman/memos-aws-infra:ref:refs/heads/main`, or better, `...:environment:production` with a protected GitHub environment.
  2. Replace AdministratorAccess with a **least-privilege policy**: ECR push to the `memos` repo, read/write on the state bucket key, and the specific ECS/ELB/EC2/IAM/ACM/Route 53 actions Terraform needs, scoped by tag or ARN where possible.
  3. Split roles: a **read-only plan role** for pull requests, and an **apply role** only for `main`.
- Keep what's already good: OIDC means **no long-lived keys**, and the `aud = sts.amazonaws.com` check is correct.

### Why it matters
OIDC is one of the strongest parts of the project. Showing you also know its **weak point** proves you understand it rather than having copied it.

## The AWS bill is higher than expected
Topic: AWS
Level: Mid
Files: infra/modules/vpc/main.tf, infra/modules/alb/main.tf

The Memos bill is much higher than you expected for one small Fargate task. Where is the money going, and what would you cut?

### Answer
- The biggest fixed cost is **two NAT gateways** (one per AZ). Each is charged **per hour plus per GB** processed, whether or not traffic flows. That's roughly $35 a month each in eu-west-1 before data.
- Next: the **ALB** (hourly plus LCUs), the **Elastic IPs** (public IPv4 is charged), and the Fargate task (0.25 vCPU, 512 MB, which is small).
- Options:
  - Non-production: **one NAT gateway**, or none (`destroy.yml` when you aren't using it).
  - **VPC endpoints**: an S3 gateway endpoint is free and carries ECR image layers. Interface endpoints for ECR API/DKR and CloudWatch Logs cost money per hour, so compare them with the NAT cost.
  - **Fargate Spot** for non-critical environments.
  - Set **AWS Budgets** alerts so you hear about it early.
- The trade-off: one NAT gateway saves money but makes it a **single point of failure** for outbound traffic from both AZs.

### Why it matters
Cost awareness is part of the Well-Architected Framework, and the NAT gateway is the classic hidden cost. Knowing it from your own bill sounds real.

## Two people run terraform apply at the same time
Topic: Terraform
Level: Junior
Files: infra/provider.tf, bootstrap/state.tf

You and a colleague both run `terraform apply` on Memos at the same moment. What happens?

### Answer
- The backend is S3 with **`use_lockfile = true`** (S3 native locking, with no DynamoDB table). The first apply writes a `.tflock` object next to `prod/terraform.tfstate`. The second fails with **“Error acquiring the state lock”** and changes nothing.
- When the first apply finishes, the lock is removed and the second person can **plan again** against the new state.
- Only use `terraform force-unlock LOCK_ID` if you're **sure** no apply is running (e.g. a CI job was killed mid-run).
- The state bucket also has **versioning** (to recover an old state), **AES256 encryption**, **public access blocked** and a policy that **denies non-HTTPS** access.

### Why it matters
Locking stops two applies from corrupting the state. Mentioning that native S3 locking replaced DynamoDB shows your knowledge is current.

## Someone changed a security group in the Console
Topic: Terraform
Level: Junior
Files: infra/modules/security/main.tf

During an incident, someone opened port 22 on the ECS security group in the Console. What happens on the next deploy, and how do you stop this happening?

### Answer
- That's **drift**: the real infrastructure no longer matches the code. The next `terraform plan` in `deploy.yml` shows the extra rule being **removed**, and `apply` removes it.
- My security group rules are separate `aws_vpc_security_group_ingress_rule`/`egress_rule` resources. A rule made in the Console isn't in state at all, so Terraform may not even notice it. Use `terraform plan -refresh-only` to see the drift, then either **import** it into code (if it should stay) or delete it.
- Prevention: no write access in the Console for normal users, changes **only through pull requests**, AWS Config or CloudTrail alerts on security group changes, and a **scheduled plan** in CI that fails if there's any drift.

### Why it matters
It shows you treat **Terraform as the source of truth**, and that you know *how* it detects drift and where it can't see it.

## Infra changes aren't being deployed
Topic: CI/CD
Level: Mid
Files: .github/workflows/build.yml, .github/workflows/deploy.yml

You change `infra/modules/alb/main.tf`, merge to `main`, and nothing deploys. Why?

### Answer
- `build.yml` only runs on pushes to `main` that touch **`app/**`, `Dockerfile` or `.dockerignore`**. `deploy.yml` runs on **`workflow_run`** after “Build and Push” succeeds, or by hand.
- A change only under `infra/**` doesn't trigger the build, so the deploy never runs.
- Today: run **Deploy** by hand (`workflow_dispatch`) with the SHA of the image that's currently live.
- Better:
  1. A **`terraform plan` on every pull request** that touches `infra/**`, with the plan posted as a comment for review.
  2. Deploy on `push` to `main` for `infra/**` as well, using the current image tag. That tag could come from an SSM parameter or the current task definition.

### Why it matters
It proves you actually know how your pipeline's triggers work, and it leads naturally to **plan-on-PR**, a common interview follow-up.

## The image scan found a critical vulnerability
Topic: Docker
Level: Junior
Files: Dockerfile, infra/modules/ecr/main.tf

ECR **scan on push** reports a critical CVE in the latest Memos image. What do you do?

### Answer
- Read the finding: is it in the **base image** (Alpine 3.21 packages) or in the **app** (a Go module)?
- Base image: rebuild on a patched `alpine:3.21` tag (or newer), or `apk upgrade` the affected package. Go module: bump it in `go.mod` and rebuild.
- Push. The new commit gets a **new SHA tag**, because tags are immutable. Deploy through the normal pipeline.
- What already limits the damage:
  - The **three-stage build**: the runtime image holds only the binary, CA certificates and tzdata, with no compilers, shell tools or source. That's 75.8 MB instead of 2.79 GB.
  - It runs as **non-root user 1001**.
  - The task runs in **private subnets**, reachable only through the ALB on 8081.
- Improve: scan in CI **before** pushing (e.g. Trivy) and fail the build on criticals.

### Why it matters
It links **image size to security**: fewer packages means fewer CVEs, and it shows you have a patching process, not just a scanner.

## Add a secret to Memos
Topic: Security
Level: Mid
Files: infra/modules/iam/main.tf, infra/modules/ecs/main.tf

You move Memos to RDS and now need to give it a database password. Where does the password go, and which role needs permission?

### Answer
- Store it in **Secrets Manager** (rotation) or **SSM Parameter Store SecureString**, never in `terraform.tfvars`, the Dockerfile or plain `environment` variables.
- In the task definition, use **`secrets = [{ name = "MEMOS_DSN", valueFrom = <secret ARN> }]`**. ECS fetches the secret when the task starts and injects it as an environment variable.
- The **execution role** needs `secretsmanager:GetSecretValue` on that one secret (plus `kms:Decrypt` if it uses a customer key). The **task role** doesn't, because ECS fetches it, not the app.
- Today in Memos: the execution role has `AmazonECSTaskExecutionRolePolicy` (pull from ECR, write logs), and the task role has **no permissions** because the app doesn't call AWS.

### Why it matters
**Execution role vs task role** is one of the most common ECS interview questions. Answering it with your own roles makes it concrete.

## The task is stuck: CannotPullContainerError
Topic: Troubleshooting
Level: Junior
Files: infra/modules/vpc/main.tf, infra/modules/security/main.tf, infra/modules/iam/main.tf

The service keeps launching tasks that stop with **CannotPullContainerError**. What could cause it in this design?

### Answer
- Tasks run in **private subnets with no public IP**, so they reach ECR through the **NAT gateway**. Check:
  1. **Route**: the private route table sends `0.0.0.0/0` to the NAT gateway in the same AZ.
  2. **Security group**: the ECS SG allows **outbound 443** (it does: `ecs_https`). Without it, nothing can be pulled.
  3. **Execution role**: it has `AmazonECSTaskExecutionRolePolicy` (`ecr:GetAuthorizationToken`, `BatchGetImage`, …).
  4. **Image**: the exact SHA tag exists in the `memos` repo. `deploy.yml` checks this with `describe-images` before applying.
- Alternative without NAT: **VPC endpoints** for `ecr.api`, `ecr.dkr`, `logs`, plus an **S3 gateway endpoint** (image layers are stored in S3).

### Why it matters
It tests whether you understand **how a private container reaches AWS services**: routing, security groups, IAM and the registry all have to line up.

## Re-running the pipeline fails: tag already exists
Topic: CI/CD
Level: Junior
Files: .github/workflows/build.yml, infra/modules/ecr/main.tf

You re-run a failed pipeline on the same commit and the push fails because **the tag already exists**. Why, and how did you fix it?

### Answer
- The ECR repository has `image_tag_mutability = "IMMUTABLE"`. Once `memos:<sha>` exists, it can never be overwritten, so a second `docker push` of the same tag is rejected.
- Fix in `build.yml`: call **`aws ecr describe-images`** for that SHA first.
  - If it exists, **reuse** it and skip the build.
  - If the error is `ImageNotFoundException`, build and push.
  - For any other error (e.g. permissions), **fail loudly** instead of guessing.
- The workflow outputs the image URI either way, so deploys stay consistent.

### Why it matters
Immutable tags are a deliberate safety feature. The fix shows you made the pipeline **idempotent** (safe to re-run) instead of turning the safety off.

## Your Terraform state bucket was deleted
Topic: Terraform
Level: Senior
Files: bootstrap/state.tf, infra/provider.tf

Someone tries to delete the `memos-terraform-state-enamul` bucket. What protects you, and how would you recover?

### Answer
- **`prevent_destroy = true`** on the bucket means Terraform refuses to destroy it, even with `terraform destroy` in the bootstrap stack.
- It lives in a separate **bootstrap** stack with **local state**, so `destroy.yml` (which destroys `infra/`) can't touch it.
- **Versioning** is on. If the state *file* is overwritten or deleted, restore the previous version of `prod/terraform.tfstate`.
- If the whole bucket really is gone (deleted outside Terraform): recreate it with bootstrap, then rebuild state with **`import` blocks** for the existing resources, or `terraform destroy` by hand in the Console and re-apply. Prevent it next time with an **SCP or bucket policy** denying `s3:DeleteBucket`.

### Why it matters
It shows you understand **resource lifecycles**: long-lived things (state, OIDC) are kept away from things you tear down often.

## ECR lives in the stack you destroy
Topic: Terraform
Level: Mid
Files: infra/modules/ecr/main.tf, .github/workflows/destroy.yml

`destroy.yml` tears down `infra/`, and the ECR repository is in `infra/` with `force_delete = true`. What's the problem, and what would you change?

### Answer
- Destroying the environment **deletes every image**, including the SHAs you'd need for a rollback. After a rebuild, the first deploy has nothing to deploy until a new build runs.
- Move ECR into the **bootstrap** layer next to the state bucket and OIDC role, because it holds long-lived **deployment artifacts**. Then:
  - remove `force_delete` or set it to false,
  - add an **ECR lifecycle policy** (e.g. keep the last 30 images) to control cost,
  - pass the repository URL into `infra/` as a variable or data source.

### Why it matters
This is the improvement from your prep doc: it shows **lifecycle and architecture thinking**, not just Terraform syntax.

## Logs from two weeks ago are gone
Topic: AWS
Level: Junior
Files: infra/modules/ecs/main.tf

A user reports a problem from 14 days ago. You open CloudWatch Logs and there's nothing. Why?

### Answer
- The log group `/ecs/memos` has **`retention_in_days = 7`**, so CloudWatch deletes events older than a week. That's a deliberate cost choice for a portfolio project.
- Options: raise retention (30 or 90 days), or **export/subscribe** logs to S3 with a lifecycle rule to Glacier for cheap long-term storage.
- For incidents you need more than logs: **Container Insights** is disabled (tfsec ignore, to save cost). Turning it on gives task-level CPU and memory metrics. Add **alarms** on ALB 5xx and unhealthy host count so you hear about problems before users do.

### Why it matters
It tests whether you know your **retention trade-offs**, and the difference between **monitoring** (alarms tell you *what*) and **observability** (logs, metrics and traces tell you *why*).

## Why did you add tfsec ignores?
Topic: Security
Level: Mid
Files: infra/modules/vpc/main.tf, infra/modules/ecs/main.tf, infra/modules/ecr/main.tf, infra/modules/security/main.tf

tfsec runs on every pipeline, but your code has several `tfsec:ignore` comments. Isn't that just hiding problems?

### Answer
- Each ignore is a **documented, deliberate trade-off** with a comment explaining it:
  - **VPC Flow Logs** off to save cost. The accepted limit: no network flow records for investigations.
  - **Container Insights** off to save cost. Basic ECS metrics are enough for one task.
  - **AWS-managed keys** instead of customer KMS keys for ECR and CloudWatch, to avoid KMS charges.
  - **Public ALB ingress on 80/443** is the point of a public website.
  - **ECS egress 443 to anywhere** is needed for ECR, S3 and CloudWatch through the NAT gateway. VPC endpoints would let me narrow it.
- For a real company I'd revisit the cost-based ones (Flow Logs and KMS especially) and track each ignore as a ticket.

### Why it matters
Interviewers want to see that you **make and document trade-offs**, not that you silence a scanner. Having the reason in a comment next to the code is exactly that.

## Stand up Memos in a second region
Topic: Terraform
Level: Senior
Files: infra/main.tf, infra/provider.tf, infra/terraform.tfvars

The business wants the same platform running in a **new AWS region** (for example the UAE, me-central-1) alongside eu-west-1. How would you reuse this Terraform?

### Answer
- The modules are already parameterised (`project_name`, `environment`, CIDRs, AZs, domain). Region-specific values go in a **separate tfvars per environment/region**.
- **Separate state per region**: a different backend key, e.g. `uae/terraform.tfstate`, or a separate root module or workspace. One bad apply should never touch both regions.
- Things that change: `aws_region` and the AZ list, a **non-overlapping VPC CIDR** (e.g. 10.1.0.0/16) in case you ever peer, an **ACM certificate in the new region** (certificates are regional for ALBs), an **ECR repository** there (or ECR replication), and **Route 53** records (latency-based or geolocation routing, or a separate subdomain).
- Watch out for **data residency rules**: user data may have to stay in-country, so the database is per region, not shared.
- Pipeline: a matrix or per-region job, with the OIDC role trust and permissions extended to the new region.

### Why it matters
This matches the job you interviewed for (a new UAE region next to the UK platform). It shows that your code is reusable and that you think about **state isolation and data residency**.

## terraform apply runs with -auto-approve on main
Topic: CI/CD
Level: Mid
Files: .github/workflows/deploy.yml

`deploy.yml` runs `terraform apply -auto-approve tfplan` with no human review. Is that safe? How would you add control?

### Answer
- It applies the **saved plan** (`-out=tfplan`), so what's applied is exactly what was planned in that run. That part is good.
- But nobody reviews the plan before it runs. A change that destroys and recreates the ALB, or replaces the VPC, would go straight through.
- Add:
  1. **Plan on pull request**, with the plan output posted to the PR so a reviewer sees the real changes before merging.
  2. A **GitHub environment `production`** with **required reviewers**. The apply job waits for approval, and the OIDC trust can require `environment:production`.
  3. A check that **fails if the plan includes destroys** of critical resources unless approved.
- Keep `fmt -check`, `validate` and tfsec before plan, as now.

### Why it matters
It shows you can balance **speed against safety**, and it's a natural follow-up to OIDC least privilege.

## The task keeps getting killed: exit code 137
Topic: Troubleshooting
Level: Junior
Files: infra/main.tf, infra/modules/ecs/main.tf

The Memos task stops every few hours with **exit code 137**. What does that mean, and what would you do?

### Answer
- **137 = 128 + 9**: the process was killed with **SIGKILL**. On ECS this is almost always **out of memory**: the container went over its **512 MB** limit.
- Confirm: the stopped reason says `OutOfMemoryError`, and the service's memory metrics climb (Container Insights would show it per task).
- Fix: raise the task size. Fargate has fixed CPU/memory pairs, e.g. 256 CPU with 1024 MB, or 512 CPU with 1024–4096 MB. Find out *why* memory grows (a leak or a large import). Add a **CloudWatch alarm on MemoryUtilization**.
- Exit codes: **0** success · **1** app error · **127** command not found · **137** SIGKILL/OOM · **143** SIGTERM (a normal stop).

### Why it matters
Exit codes are quick wins in interviews, and tying 137 to your **actual task size** (0.25 vCPU, 512 MB) shows you know your own system.
