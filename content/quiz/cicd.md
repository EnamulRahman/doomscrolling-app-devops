---
topic: CI/CD
source: tech-vault
level: Beginner
---

? What problem does CI/CD solve?
- [ ] It removes the need for testing
- [x] Manual, infrequent, error-prone builds and releases: it automates building, testing and deploying small changes often
- [ ] It replaces version control
- [ ] It makes code run faster
> Small, frequent, automated releases are safer than big, rare, manual ones.

? What is continuous integration?
- [x] Developers merge small changes to the main branch often, and every change is automatically built and tested
- [ ] Deploying to production every hour
- [ ] Running tests once a week
- [ ] Integrating two companies' systems
> CI catches integration problems within minutes of a push.

? Continuous delivery vs continuous deployment?
- [ ] They're the same
- [x] Delivery: every change is releasable, but a human approves production; deployment: changes go to production automatically
- [ ] Deployment is only for infrastructure
- [ ] Delivery skips tests
> Memos does continuous **deployment**: build → deploy → health check, with no approval step.

? What is a build **artefact**?
- [ ] A broken build
- [x] The versioned output of a build (a binary, package or container image) that gets deployed
- [ ] The source code
- [ ] A test report only
> Memos' artefact is the `memos:<git-sha>` image in ECR.

? Why is automated testing important in CI/CD?
- [ ] It makes builds slower
- [x] It gives fast, consistent feedback and stops broken code reaching production without relying on someone remembering to test
- [ ] It replaces code review
- [ ] It's required by GitHub
> No tests means CI/CD just ships bugs faster.

? What should happen when a pipeline stage fails?
- [ ] Skip that stage and continue
- [x] Stop the pipeline, alert the team, and fix the cause before anything moves on
- [ ] Deploy anyway and fix in production
- [ ] Delete the pipeline
> A failed stage is the safety net working.

? What is a **blue/green** deployment?
- [ ] Deploying to two Regions at once
- [x] Running the new version (green) alongside the old (blue), then switching traffic over all at once, with instant switch-back
- [ ] Gradually replacing instances one by one
- [ ] Testing in a green-themed environment
> Costs double capacity during the switch, but rollback is a single traffic flip.

? What is a **canary** deployment?
- [x] Releasing to a small percentage of users first, watching the metrics, then widening
- [ ] Deploying only on Fridays
- [ ] Replacing everything at once
- [ ] A deployment that tests birds
> Weighted target groups or Route 53 weighted records can do canaries on AWS.

? What is a **rolling** deployment?
- [ ] Rebuilding the image each time
- [x] Replacing old instances or tasks with new ones gradually, so some capacity is always serving
- [ ] Deploying to all servers at the same instant
- [ ] Rolling back automatically
> ECS services do rolling deployments by default, which is how Memos updates.

? Why have separate dev, staging and prod environments?
- [ ] To triple the cost
- [x] To test changes safely in production-like conditions before real users see them
- [ ] Because Terraform requires three
- [ ] So each developer has a production
> Promote the **same artefact** through each environment.

@ level: Intermediate
? Many developers merge often and `main` keeps breaking. What helps most?
- [ ] Let one person merge everything
- [x] Required PR checks (build + tests), branch protection, small PRs and fast feedback, plus feature flags for unfinished work
- [ ] Merge once a month
- [ ] Turn off CI to go faster
> Make it **impossible** to merge red, and keep changes small.

@ level: Intermediate
? The pipeline passes, but the app fails in staging. What are the likely causes?
- [ ] The tests are too strict
- [x] Environment differences: config or variables, secrets, IAM permissions, networking, database schema or versions that the tests didn't cover
- [ ] The Git history is corrupted
- [ ] The CI runner is too slow
> Add integration and smoke tests against staging, and keep environments consistent with IaC.

@ source: Revision notes · level: Intermediate
? Which line lets a GitHub Actions job request an OIDC token for AWS?
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: ???
      contents: read
```
- [ ] `id-token: read`
- [x] `id-token: write`
- [ ] `id-token: none`
- [ ] `id-token: admin`
> `write` lets the job **request** an ID token. Without it, `configure-aws-credentials` can't do OIDC.

@ source: Revision notes · level: Intermediate
? Why pin third-party GitHub Actions to a full commit SHA rather than a tag like `@v4`?
- [ ] SHAs run faster
- [x] Tags can be moved to point at different (possibly malicious) code; a SHA can't change
- [ ] GitHub requires it
- [ ] Tags don't work for private repos
> Your workflow runs with your credentials, so supply-chain safety matters.

@ source: Revision notes
? Which trigger lets you run a workflow manually, with inputs, from the GitHub UI?
- [ ] `push`
- [ ] `schedule`
- [x] `workflow_dispatch`
- [ ] `pull_request_target`
> Memos' `deploy.yml` uses it with an `image_tag` input for rollbacks, and `destroy.yml` is dispatch-only.
