---
source: Kubernetes
---

## kubectl is locked out of the new cluster
@ topic: Kubernetes · level: Junior · files: terraform/modules/eks/main.tf
Terraform has just created your EKS cluster. `aws sts get-caller-identity` works, and `aws eks update-kubeconfig` succeeded, but `kubectl get nodes` says **"You must be logged in to the server (Unauthorized)"**.
? What's the fix?
- [ ] Regenerate your AWS access keys
  > Your AWS login works fine. This is Kubernetes authorisation.
- [x] Give your IAM identity an EKS **access entry** with an access policy (or set `enable_cluster_creator_admin_permissions = true` for whoever applies)
  > Correct. AWS authentication ≠ Kubernetes access.
- [ ] Open port 443 on the node security group
  > The API server is reachable: it answered with Unauthorized.
- [ ] Reinstall kubectl
  > The client works. The cluster is refusing your identity.
> **Takeaway:** the pipeline's role needs its own access entry too, or Pipeline 2 fails the same way.

## The ingress controller never gets an address
@ topic: Kubernetes · level: Mid · files: terraform/modules/vpc/main.tf
You installed the NGINX ingress controller with a `LoadBalancer` Service, but `kubectl get svc -n nginx-ingress` shows `EXTERNAL-IP <pending>` for 15 minutes.
? What do you check first?
- [ ] Restart the controller pods
  > The pods aren't the issue. AWS hasn't created the load balancer.
- [x] `kubectl describe svc` events, then the subnet tags: public subnets need `kubernetes.io/role/elb = 1` so AWS knows where to place the load balancer
  > Correct. Missing subnet tags are the classic cause (set `public_subnet_tags` in the VPC module).
- [ ] Add a NodePort
  > That doesn't create the cloud load balancer.
- [ ] Delete the Ingress resources
  > The Service is stuck before any Ingress matters.
> **Takeaway:** Kubernetes asks AWS for the load balancer, and the events and subnet tags tell you why it hasn't arrived.

## Prometheus stuck in Pending
@ topic: Kubernetes · level: Mid
After installing kube-prometheus-stack with persistent storage, the Prometheus pod is `Pending` and its PVC is `Pending` too.
? What's the likely cause on EKS?
- [ ] Prometheus needs a LoadBalancer Service
  > Networking doesn't affect scheduling here.
- [x] Nothing can create the volume: install the **EBS CSI driver** add-on (with its IAM role) and a StorageClass, or run without persistence for now
  > Correct. Dynamic provisioning needs a driver and a class.
- [ ] Grafana's password isn't set
  > Unrelated to storage.
- [ ] etcd is full
  > Very unlikely, and not what a Pending PVC means.
> **Takeaway:** `kubectl describe pvc` tells you what it's waiting for.

## The game deploys but the page is blank
@ topic: Kubernetes · level: Junior
The 2048 pods are `Running`, but `curl http://game.game` from a netshoot pod hangs and then fails. The image is `nginx-unprivileged`, and the Service says `port: 80, targetPort: 80`.
? What's wrong?
- [ ] The pods need more memory
  > They're running fine.
- [x] nginx-unprivileged listens on **8080**, so the Service's `targetPort` (and the probes) must be 8080
  > Correct. The Service forwards to a port nothing is listening on.
- [ ] CoreDNS is down
  > The name resolved: the connection to the pod port failed.
- [ ] A NetworkPolicy blocks it
  > Possible in general, but here the port mismatch is the clear cause.
> **Takeaway:** port, targetPort and containerPort must line up. Write down which process listens where.

## OOMKilled under load
@ topic: Kubernetes · level: Junior
Under load, pods restart repeatedly, and `kubectl describe pod` shows **Last State: Terminated, Reason: OOMKilled**.
? What's happening, and what do you change?
- [ ] CPU throttling: raise the CPU limit
  > CPU over its limit is throttled, not killed.
- [x] The container went over its **memory limit** and was killed. Check real usage (Grafana or `kubectl top`), then raise the request and limit or fix the memory growth
  > Correct. OOMKilled = exit 137.
- [ ] The liveness probe is too strict
  > That would show liveness failures, not OOMKilled.
- [ ] The image is corrupted
  > A bad image wouldn't run at all.
> **Takeaway:** size requests and limits from real metrics, not guesses.

## An Ingress that does nothing
@ topic: Kubernetes · level: Junior
You applied an Ingress for `game.lab.example.com`, but nothing answers, and no load balancer exists in AWS.
? What's the most likely reason?
- [x] No ingress controller is installed (or `ingressClassName` names one that doesn't exist)
  > Correct. An Ingress is only rules; a controller has to follow them.
- [ ] Ingresses take an hour to start
  > They take effect as soon as a controller sees them.
- [ ] Route 53 must be created by hand first
  > With ExternalDNS it isn't, and DNS doesn't create the load balancer anyway.
- [ ] The Service must be a LoadBalancer
  > Behind an Ingress, a ClusterIP Service is normal.
> **Takeaway:** check `kubectl get ingressclass` first.

## NetworkPolicy applied, nothing blocked
@ topic: Kubernetes · level: Mid
You applied a NetworkPolicy so only the API pods can reach the database pods. A test pod with no labels can still connect.
? Why?
- [ ] Policies only apply after a node reboot
  > They apply straight away when enforced.
- [x] The CNI isn't enforcing NetworkPolicies (on EKS, the VPC CNI's network policy support must be enabled, or use Calico or Cilium), so they're silently ignored
  > Correct. No error, no protection.
- [ ] You need one policy per pod
  > Policies select pods by label.
- [ ] Policies don't work on databases
  > They work on any pod.
> **Takeaway:** test your policies: assume nothing until a blocked connection proves it.

## terraform destroy hangs on the VPC
@ topic: Kubernetes · level: Mid
At the end of a session you ran `terraform destroy` on the EKS stack. It's been stuck deleting the VPC and subnets for 20 minutes.
? What's the cause, and the right order next time?
- [ ] The state lock: run force-unlock
  > A lock would stop the run immediately, not hang on the VPC.
- [x] Kubernetes created an NLB (and DNS records) that Terraform doesn't know about, and it's still using the subnets. Next time: delete the apps → `helm uninstall` the add-ons → `terraform destroy` → check for leftovers
  > Correct. Clean up inside out.
- [ ] NAT gateways can't be destroyed
  > They can; it just takes a minute.
- [ ] EKS clusters must be deleted in the console
  > Terraform can delete them.
> **Takeaway:** orphaned load balancers keep billing. Delete them in EC2 → Load Balancers, then re-run destroy.

## Pipeline 2 deploys a broken image
@ topic: Kubernetes · level: Mid
A bug makes the new 2048 pods fail their readiness probe. Pipeline 2 has already pushed the image and run `kubectl apply`.
? How should the pipeline handle this?
- [ ] Mark the job green: the apply succeeded
  > Apply succeeding doesn't mean the release works.
- [x] `kubectl rollout status --timeout=120s` fails → `kubectl rollout undo` → exit 1. The old pods keep serving because the new ones never became ready
  > Correct. Readiness gates the rollout, and the pipeline turns the failure into an automatic rollback.
- [ ] Delete the namespace and redeploy
  > That's an outage.
- [ ] Disable the readiness probe
  > That would send traffic to broken pods.
> **Takeaway:** probes + rollout status + undo = error handling worth marks.

## Argo CD can't read the repo
@ topic: Kubernetes · level: Junior
Your Argo CD Application shows **"authentication required"** and never syncs.
? What's the fix?
- [ ] Reinstall Argo CD
  > Argo CD works. It's being refused by Git.
- [x] Add the repository's credentials in Argo CD (Settings → Repositories, a deploy key or token), or make the repo public
  > Correct. Argo CD pulls from Git, so it needs read access.
- [ ] Put the Application in the default namespace
  > Applications belong in Argo CD's own namespace.
- [ ] Turn off selfHeal
  > Unrelated to authentication.
> **Takeaway:** in GitOps, the cluster needs read access to Git; the pipeline no longer needs cluster access.

## Certificate stuck, never Ready
@ topic: Kubernetes · level: Senior
Your Ingress has the cert-manager annotation, but `kubectl get certificate -n game` shows `READY False` for 30 minutes.
? Where do you look, in what order?
- [x] `kubectl describe certificate`, then the CertificateRequest/Order/Challenge, then the cert-manager logs: usually the IRSA role can't write the TXT record (wrong zone, namespace or service account), or Let's Encrypt rate limits were hit
  > Correct. Follow cert-manager's own chain of objects.
- [ ] Restart the ingress controller
  > It's waiting for the certificate, not causing the problem.
- [ ] Switch to HTTP
  > That avoids the problem rather than fixing it.
- [ ] Delete the hosted zone
  > Destructive, and it makes things worse.
> **Takeaway:** use Let's Encrypt **staging** until everything works, then switch to production.

## ECS or Kubernetes for a new app?
@ topic: Kubernetes · level: Senior
A small team is about to run one web app on AWS. A colleague insists on EKS "because it's the standard".
? What's the most balanced recommendation?
- [ ] Always EKS: ECS is legacy
  > ECS is actively developed and very common.
- [ ] Always ECS: Kubernetes is too complex
  > It depends on context.
- [x] For one small app on AWS, ECS is simpler and cheaper to run. Choose EKS when you need portability, many services, the Kubernetes ecosystem (Helm, Argo CD, operators) or the team already runs it
  > Correct. Trade-offs, not dogma.
- [ ] Use both for redundancy
  > Double the operational load for no benefit.
> **Takeaway:** EKS's control plane alone costs about $73 a month, and you still operate add-ons.
