---
source: tech-vault
---

## A process can't write its logs any more
@ topic: Linux · level: Junior
An application on a Linux server has stopped writing to its log file. It's still running.
? What do you check first?
- [ ] Reinstall the application
  > Too drastic before you know the cause.
- [x] Disk space and inodes (`df -h`, `df -i`), then permissions and ownership on the log file and folder, then the logging config and service (rsyslog/journald)
  > Correct. Full disks and permissions are the usual suspects.
- [ ] Increase the server's RAM
  > Writing logs needs disk space, not RAM.
- [ ] Reboot immediately
  > You'd lose evidence, and it may not fix a full disk.
> **Takeaway:** for "can't write" problems, check space, inodes and permissions first.

## Is this Linux server healthy?
@ topic: Linux · level: Junior
You've just been given SSH access to a server and asked "is it healthy?"
? Which set of checks gives the best quick picture?
- [x] `uptime` (load), `free -h`, `df -h`/`df -i`, `systemctl --failed`, `journalctl -p err -b`, and `ss -tlnp` for expected listeners
  > Correct. CPU, memory, disk, services, errors and network in under a minute.
- [ ] `ls -la /`
  > That just lists files.
- [ ] `ping google.com`
  > It only tests outbound connectivity.
- [ ] `history`
  > It shows past commands, not health.
> **Takeaway:** have a checklist ready. The golden signals apply to servers too.

## I can't reach a website
@ topic: Networking · level: Mid
A user says "the website is down". You can SSH to a machine on the same network.
? What's the best troubleshooting order?
- [ ] Restart the web server, then check
  > Changes before diagnosis destroy evidence and may not help.
- [x] `dig` the name → `ping`/`traceroute` the IP → `nc -zv host 443` → `curl -v https://…` → server logs and listeners (`ss -tlnp`)
  > Correct. DNS, then routing, then the port, then the application. One layer at a time.
- [ ] Clear the browser cache and give up if that fails
  > Too shallow.
- [ ] Check the database first
  > Start at the edge and work in.
> **Takeaway:** a structured, layered approach. Say it out loud in interviews.

## Slow transfers between two hosts
@ topic: Networking · level: Mid
Copying data between two servers in the same data centre is extremely slow.
? Which approach is best?
- [x] Measure with `iperf3`, check per-hop latency and loss with `mtr`, check the interfaces for errors and duplex/MTU mismatches, and check whether the disk or CPU is the real bottleneck
  > Correct. Measure first: the network may not even be the problem.
- [ ] Switch from TCP to UDP
  > Not without understanding the cause, and UDP gives up reliability.
- [ ] Reboot both servers
  > It may hide the symptom without fixing anything.
- [ ] Buy faster disks
  > Maybe, but only once measurements say so.
> **Takeaway:** isolate network vs disk vs CPU before fixing anything.

## Resources in a private subnet need internet
@ topic: AWS · level: Junior
App servers in private subnets must download updates from the internet, but must **not** be reachable from it.
? What do you add?
- [ ] Public IPs on the app servers
  > That makes them reachable from the internet.
- [x] A NAT gateway in a public subnet, and a route `0.0.0.0/0 → NAT` in the private route table
  > Correct. Outbound only, and replies come back. One NAT per AZ for resilience.
- [ ] An internet gateway route in the private route table
  > That makes the subnet public.
- [ ] A VPC peering connection
  > Peering connects VPCs, not the internet.
> **Takeaway:** IGW = two-way for public resources; NAT = outbound only for private ones.

## Build a three-tier app on AWS
@ topic: AWS · level: Mid
"Design a classic three-tier web application on AWS."
? Which design is best?
- [ ] One big EC2 instance running the web server, app and database
  > A single point of failure, and the database is exposed.
- [x] A VPC across 2+ AZs: ALB (with ACM) in public subnets → app on an ASG or ECS in private subnets (from the ALB SG only) → RDS Multi-AZ in isolated subnets (from the app SG only), plus Route 53, Secrets Manager, CloudWatch and Terraform
  > Correct. Each tier is isolated and redundant, and only reachable from the tier in front of it.
- [ ] Everything in public subnets with strong passwords
  > Passwords don't replace network isolation.
- [ ] Three Regions, one tier each
  > That adds latency and cost without isolating anything properly.
> **Takeaway:** draw it. Memos is this design minus the data tier.

## The pipeline fails at the test stage
@ topic: CI/CD · level: Junior
After your change, the CI pipeline fails in the automated test stage.
? What's the best approach?
- [ ] Re-run until it passes
  > That might hide a real regression, or a flaky test you should fix.
- [ ] Disable the failing test to unblock the merge
  > That defeats the purpose of CI.
- [x] Read the logs to find which tests failed and why, decide if it's a real regression, a flaky test or the environment, reproduce it locally, then fix and re-run
  > Correct. The pipeline did its job by stopping bad code early.
- [ ] Merge anyway and fix later
  > Now everyone's builds are red.
> **Takeaway:** a red pipeline is a safety net, not an obstacle.

## main keeps breaking
@ topic: CI/CD · level: Mid
Many developers merge frequently and `main` is broken several times a week.
? What helps most?
- [x] Branch protection with required checks and reviews, small PRs, fast CI feedback, merge queues, and feature flags for unfinished work
  > Correct. Make it impossible to merge red, and keep each change small.
- [ ] Only allow merges on Mondays
  > Bigger batches mean more breakage.
- [ ] One person reviews and merges everything
  > A bottleneck that doesn't scale.
- [ ] Turn off tests to go faster
  > Faster breakage.
> **Takeaway:** guardrails beat gatekeepers.

## Green pipeline, broken staging
@ topic: CI/CD · level: Mid
CI passes, but the app fails once deployed to staging.
? What are the most likely causes?
- [ ] The tests were too thorough
  > Thorough tests aren't the problem.
- [x] Environment differences the tests didn't cover: config or env vars, missing secrets, IAM permissions, network rules, database schema or migrations, dependency versions
  > Correct. Then add smoke and integration tests against staging, and define environments with IaC.
- [ ] Git history is corrupted
  > Very unlikely.
- [ ] The runner was too slow
  > Speed doesn't change behaviour like this.
> **Takeaway:** "works in CI" ≠ "works in the environment". Close the gap with IaC and smoke tests.

## Walk me through commit to production
@ topic: CI/CD · level: Mid
"Walk me through a CI/CD pipeline from code commit to production."
? Which answer is strongest?
- [x] PR opens → CI builds, lints, unit-tests and scans → one versioned artefact (image:sha) → deploy to staging → integration/smoke tests → approval (if continuous delivery) → same artefact to prod with a rolling or blue/green deployment → monitor and roll back automatically on failure
  > Correct. Build once, promote everywhere, and close the loop with monitoring.
- [ ] Developer builds locally and copies files to the server
  > Manual, unrepeatable and risky.
- [ ] Deploy straight to production on every commit with no tests
  > Speed without safety.
- [ ] Build a different artefact for each environment
  > You'd ship something you never tested.
> **Takeaway:** then tell them how Memos does it: build.yml → deploy.yml → /healthz.

## Kubernetes pod in CrashLoopBackOff
@ topic: Kubernetes · level: Mid
A deployment's pods are in `CrashLoopBackOff`.
? What do you do first?
- [ ] Delete the node
  > The node is probably fine.
- [x] `kubectl logs <pod> --previous` and `kubectl describe pod <pod>` to see why the container exits (config, missing secret, OOM, failing probe)
  > Correct. The container keeps starting and dying, so read the last crash's logs and the events.
- [ ] Scale to 0 and forget it
  > That hides the problem.
- [ ] Restart the API server
  > The control plane isn't the issue.
> **Takeaway:** describe + logs --previous solves most pod problems.

## A master node fails
@ topic: Kubernetes · level: Senior
In a cluster with a single control-plane node, that node dies.
? What's the impact, and how do you prevent it?
- [ ] Every pod stops immediately
  > Running pods keep running on the workers.
- [x] Running workloads continue, but nothing can be changed or rescheduled until it's back. Prevent it with 3+ control-plane nodes (etcd quorum) or a managed control plane such as EKS
  > Correct. That's control-plane HA.
- [ ] Workers elect a new master automatically
  > Not without an HA control plane.
- [ ] Nothing happens
  > You lose all management and self-healing.
> **Takeaway:** etcd quorum needs an odd number of members: 3 or 5.

## Bring a stale branch up to date
@ topic: Git · level: Junior
Your feature branch is weeks behind `main`, and you need the latest changes before opening a PR.
? What's the cleanest approach?
- [ ] Delete your branch and start again
  > You'd lose your work.
- [x] `git fetch origin`, then `git rebase origin/main` (or merge it), resolve conflicts, then `git push --force-with-lease`
  > Correct. `--force-with-lease` refuses to overwrite commits you haven't seen.
- [ ] `git push --force` without fetching
  > That could overwrite other people's work.
- [ ] Copy files from main by hand
  > Error-prone, and you lose history.
> **Takeaway:** rebase your own branches; never force-push shared ones without `--with-lease`.

## Undo a pushed commit safely
@ topic: Git · level: Junior
A bad commit was pushed to `main` an hour ago, and others have already pulled it.
? What's the safe fix?
- [x] `git revert <sha>` and push. It adds a new commit that undoes the change
  > Correct. History stays intact for everyone.
- [ ] `git reset --hard HEAD~1` and force-push
  > That rewrites shared history and breaks teammates' clones.
- [ ] Delete the repository
  > Extreme and destructive.
- [ ] `git stash`
  > Stash only affects uncommitted local changes.
> **Takeaway:** shared branch → revert. Private branch → reset is fine.
