---
topic: Terraform
source: tech-vault
level: Beginner
---

? What is Infrastructure as Code?
- [ ] Writing apps that run on servers
- [x] Defining infrastructure in version-controlled files so it can be reviewed, repeated and automated
- [ ] A cloud provider
- [ ] Documentation of servers
> Terraform, CloudFormation, CDK and Pulumi are all IaC tools.

? Terraform vs CloudFormation?
- [ ] Terraform only works on Azure
- [x] Terraform works with many providers (AWS, Azure, GitHub…) and keeps its own state; CloudFormation is AWS-only and AWS manages the state
- [ ] CloudFormation is declarative, Terraform isn't
- [ ] They're identical
> Azure's equivalent of CloudFormation is ARM/Bicep.

? Terraform vs Ansible?
- [x] Terraform **provisions** infrastructure (declarative, with state); Ansible mostly **configures** servers (procedural tasks, agentless over SSH)
- [ ] Ansible can't talk to clouds
- [ ] Terraform configures packages inside servers
- [ ] Ansible needs a state file
> They're often used together: Terraform builds the servers, Ansible sets them up.

? What is Terraform **state**?
- [ ] The current Git branch
- [x] A file mapping resources in your code to real resource IDs, used to work out what to change
- [ ] A log of every apply
- [ ] The provider's cache
> It can hold secrets, so keep it remote, encrypted and private, and **never** commit it.

? Local vs remote state?
- [ ] Local is better for teams
- [x] Local state is a file on your machine (fine for solo experiments); remote state (e.g. S3) is shared, locked and backed up, so it's needed for teams and CI
- [ ] Remote state can't be encrypted
- [ ] There's no difference
> Memos stores its state in S3 with `use_lockfile = true`.

? What is a **provider**?
- [x] A plugin that lets Terraform talk to a platform's API (aws, azurerm, github, kubernetes…)
- [ ] The person who runs apply
- [ ] A type of module
- [ ] The state backend
> Pin provider versions (`~> 5.0`) and commit `.terraform.lock.hcl`.

? Which command checks your configuration for syntax and reference errors?
- [ ] `terraform fmt`
- [x] `terraform validate`
- [ ] `terraform plan -check`
- [ ] `terraform lint`
> `fmt` formats HCL (`-check` fails if anything needs formatting). `validate` checks correctness.

? How do you format all Terraform files, including in subfolders?
- [x] `terraform fmt -recursive`
- [ ] `terraform validate -all`
- [ ] `terraform format .`
- [ ] `terraform fix`
> Memos' pipeline runs `terraform fmt -check -recursive` and fails on bad formatting.

@ level: Intermediate
? How does state **locking** work with an S3 backend today?
- [ ] It doesn't: two applies can run safely
- [x] With `use_lockfile = true`, Terraform writes a `.tflock` object; other runs wait or fail until it's released (DynamoDB is no longer required)
- [ ] Git branches act as locks
- [ ] The provider locks AWS resources
> S3 native locking arrived in Terraform 1.10. Memos uses it.

@ level: Intermediate
? Three engineers will work on the same AWS infrastructure. What should you set up first?
- [ ] Each keeps their own local state
- [x] A remote backend with locking, plus a PR workflow that runs `plan` in CI
- [ ] A shared laptop
- [ ] Email each other before applying
> Shared, locked state plus reviewed plans stops people overwriting each other's work.

@ level: Intermediate
? How do you bring a resource created by hand under Terraform management?
- [ ] Delete it and recreate it
- [x] Write the resource block, then use an `import` block (or `terraform import`) so state records the existing ID
- [ ] `terraform refresh`
- [ ] Copy its ID into a variable
> Memos used import blocks for ACM validation records that already existed.

@ level: Intermediate
? How do you pass a value from one module to another?
- [ ] Global variables
- [x] Declare an `output` in the first module and pass `module.first.output_name` into the second module's variable
- [ ] Read the other module's state file
- [ ] You can't
> e.g. `certificate_arn = module.acm.certificate_arn` in Memos' root module.

@ level: Intermediate
? Which command reconciles state with real infrastructure without proposing resource changes?
- [ ] `terraform refresh` (recommended)
- [x] `terraform plan -refresh-only` / `apply -refresh-only` (`terraform refresh` is deprecated)
- [ ] `terraform validate`
- [ ] `terraform state rm`
> The guide corrects the repo here: use the `-refresh-only` mode.

? How should you handle secrets in Terraform?
- [ ] Hard-code them in `terraform.tfvars` and commit it
- [x] Keep them out of Git; read them from Secrets Manager/SSM or environment variables, mark variables `sensitive`, and protect the state (which can still contain them)
- [ ] Put them in outputs so they're easy to find
- [ ] Base64-encode them in the code
> Sensitive values can still end up in **state**, so encrypt it and restrict access.

? What is **Terragrunt**?
- [ ] A Terraform competitor from AWS
- [x] A thin wrapper that keeps Terraform configurations DRY across many environments and modules (shared backend config, dependencies)
- [ ] A security scanner
- [ ] A Terraform cloud service
> Useful at scale; not needed for a single stack like Memos.

? What do **Checkov** and **tfsec** do?
- [ ] Format Terraform
- [x] Static-analyse IaC for security and compliance problems (public buckets, open SGs, missing encryption)
- [ ] Run Terraform faster
- [ ] Store state
> Memos runs tfsec on every pipeline and documents accepted findings with `tfsec:ignore` and a reason.

@ level: Intermediate
? In a pipeline, where should Terraform state live?
- [ ] On the CI runner's disk
- [ ] In the Git repo
- [x] In a remote backend (e.g. an encrypted, versioned S3 bucket with locking) the pipeline reads through least-privilege credentials
- [ ] In the Docker image
> Runners are throwaway VMs. State saved there would be lost after every job.

@ source: My guide · level: Intermediate
? What does `-/+` mean in a plan?
```output
-/+ resource "aws_lb" "this" {
      ~ name = "memos-alb" -> "memos-prod-alb" # forces replacement
    }
```
- [ ] Update in place
- [x] The resource will be destroyed and recreated (replaced)
- [ ] Nothing changes
- [ ] It's imported
> Some attributes can't be changed in place. Renaming an ALB replaces it, which means a new DNS name and a brief outage.

@ source: My guide · level: Intermediate
? Why prefer `for_each` over `count` for things you may remove later?
- [ ] count is deprecated
- [x] count tracks items by position, so removing one shifts the rest and can recreate them; for_each uses stable keys
- [ ] for_each is faster
- [ ] count can't create subnets
> Memos uses `for_each` over ACM's validation options.

@ source: My guide
? Why does Memos keep the state bucket and OIDC role in a separate `bootstrap/` stack?
- [ ] Terraform requires it
- [x] They must exist before the main stack (the state has to live somewhere), and they're long-lived, so destroying `infra/` won't touch them
- [ ] To save money
- [ ] Because bootstrap uses CloudFormation
> Separate lifecycles: long-lived foundations versus the app stack you rebuild.
