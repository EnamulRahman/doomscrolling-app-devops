---
topic: Kubernetes
source: Revision notes
level: Intermediate
---

? What three things run on every worker node?
- [ ] etcd, the scheduler and the API server
- [x] The kubelet, kube-proxy and a container runtime
- [ ] CoreDNS, Helm and kubectl
- [ ] The controller-manager, etcd and kubelet
> etcd, the scheduler and the API server are **control plane** components.

? Which file tells `kubectl` which clusters exist and how to log in?
- [ ] `/etc/kubernetes/admin.yaml`
- [x] `~/.kube/config` (the kubeconfig)
- [ ] `~/.aws/credentials`
- [ ] `kind-config.yaml`
> Each **context** in it is one cluster + user. `kubectl config use-context` switches.

? You type `kubectl create pod nginx --image=nginx` and get an error. What should you use?
- [x] `kubectl run nginx --image=nginx`
- [ ] `kubectl new pod nginx`
- [ ] `kubectl start nginx`
- [ ] `kubectl create container nginx`
> `kubectl create pod` doesn't exist. `create` is for Deployments and other objects.

? What does `image: nginx` (no tag) pull, and why is it risky?
- [ ] nginx:stable, which never changes
- [x] `nginx:latest`, which can change underneath you without warning
- [ ] The oldest nginx version
- [ ] Nothing: a tag is required
> Pin a version (better still, a digest) so every pod runs exactly what you tested.

? Which **apiVersion** does a Deployment use?
- [ ] `v1`
- [x] `apps/v1`
- [ ] `deployments/v1`
- [ ] `core/v1`
> Pods, Services, ConfigMaps and Secrets are `v1`. Deployments, ReplicaSets and StatefulSets are `apps/v1`.

? How do you generate a starting Deployment YAML file **without** creating anything?
- [ ] `kubectl get deploy -o yaml`
- [x] `kubectl create deploy game --image=nginx --dry-run=client -o yaml > deploy.yaml`
- [ ] `kubectl explain deployment > deploy.yaml`
- [ ] `kubectl apply --print`
> `--dry-run=client` prints the YAML and creates nothing. Then edit it and apply it.

? `kubectl apply` fails with "selector does not match template labels". What's wrong?
- [ ] The image tag is missing
- [x] The pod template's labels don't match `spec.selector.matchLabels`
- [ ] The namespace doesn't exist
- [ ] The Service is missing
> The Deployment must be able to recognise its own pods by label.

? Which statement about ReplicaSets and Deployments is true?
- [ ] ReplicaSets do rolling updates
- [x] A ReplicaSet keeps N pods running; a Deployment adds rolling updates and rollbacks by managing ReplicaSets
- [ ] You should always create ReplicaSets directly
- [ ] Deployments can't scale
> You almost always create Deployments.

? Compare the three Service types.
- [ ] They're all reachable from the internet
- [x] ClusterIP: inside the cluster only · NodePort: `<node-IP>:30000–32767` · LoadBalancer: a real cloud load balancer
- [ ] NodePort is the default
- [ ] LoadBalancer only works on kind
> ClusterIP is the default and the usual target of an Ingress.

? `curl http://game` from another pod returns nothing. What do you check first?
- [ ] The node's disk space
- [x] `kubectl describe svc game`: are there any **Endpoints**? Empty means the selector matches no pods
- [ ] The kubeconfig
- [ ] The Ingress annotations
> Nine times out of ten it's a label mismatch.

? What does the `--` mean in `kubectl exec -it pod -- sh`?
- [ ] It comments out the rest of the line
- [x] It ends kubectl's own flags; everything after it is the command to run inside the container
- [ ] It means "all containers"
- [ ] It's required by bash
> Without it, kubectl may try to read the container command's flags as its own.

? What does ReadWriteOnce (RWO) mean?
- [ ] Only one pod can ever use the volume
- [x] It can be mounted read-write by one **node** at a time
- [ ] It can only be written once
- [ ] Read-write for every node
> EBS is RWO. EFS supports ReadWriteMany.

? Name the three ways a pod can use a ConfigMap.
- [x] One key as an env var, all keys as env vars (`envFrom`), or as files in a mounted volume
- [ ] As a Service, an Ingress or a Secret
- [ ] Only as environment variables
- [ ] As a command-line flag to kubectl
> Mounted files update when the ConfigMap changes; env vars don't.

? What happens if the app tries to write to a Secret mounted as a volume?
- [ ] The Secret is updated
- [x] It fails with "Read-only file system"
- [ ] The pod restarts
- [ ] It writes to etcd
> Secret and ConfigMap volumes are mounted read-only.

? Describe the Kubernetes pod network model.
- [ ] Pods can only talk within their node
- [x] Every pod gets its own IP; pods reach each other directly with no NAT, across nodes; everything is open until NetworkPolicies are added
- [ ] Pods share the node's IP and use different ports
- [ ] All traffic goes through the API server
> A CNI plugin (Calico, Cilium, AWS VPC CNI…) builds it.

? A NetworkPolicy allows only pods labelled `role: backend` on TCP 80. A pod labelled `role: frontend` calls in. What happens?
- [ ] It's allowed, because policies are advisory
- [x] It's blocked: once a policy selects the pods, anything not explicitly allowed is denied
- [ ] It's allowed on port 443
- [ ] The frontend pod is deleted
> Assuming the CNI enforces policies.

? What's the difference between an Ingress resource and an ingress controller?
- [ ] They're the same thing
- [x] The Ingress is only routing rules; the controller is the running software (pods) that reads the rules and routes traffic
- [ ] The controller is a type of Service
- [ ] Ingress resources include their own load balancer
> No controller installed means nothing happens.

? What changed with the community **ingress-nginx** controller in 2026?
- [ ] It became part of core Kubernetes
- [x] It was retired (no further releases or security fixes), so use a maintained controller such as F5's NGINX Ingress Controller, or the Gateway API
- [ ] It was renamed to Traefik
- [ ] It now requires a paid licence
> F5's controller uses different annotations (`nginx.org/…`).

? Why delegate only a **subdomain** (e.g. `lab.example.com`) to Route 53?
- [ ] Route 53 can't host whole domains
- [x] The domain stays at its registrar, and AWS (and tools like ExternalDNS) can only change records in that one subzone
- [ ] It's required for Let's Encrypt
- [ ] It makes DNS faster
> Create the hosted zone, then add its 4 NS records at the registrar.

? Name two settings in a typical lab EKS setup that are **not** production-ready.
- [x] `single_nat_gateway = true` and a public API endpoint with admin for everyone
- [ ] Private subnets for nodes and IRSA
- [ ] Remote state with locking and OIDC
- [ ] Pinned module versions and tags
> One NAT is a single point of failure, and the public endpoint plus broad admin access widen the attack surface.

? cert-manager is installed in the wrong namespace and can't reach AWS. Why?
- [ ] Namespaces block internet access
- [x] Its IRSA role only trusts `system:serviceaccount:<namespace>:<sa>`, and a different namespace doesn't match
- [ ] cert-manager only works in default
- [ ] Route 53 is regional
> IRSA trust is tied to an exact namespace and service account.

? Why does the Argo CD server often run with `--insecure` behind an ingress?
- [ ] To disable authentication
- [x] The ingress already terminates TLS; without it, Argo CD redirects to HTTPS again, causing a redirect loop
- [ ] Argo CD doesn't support TLS
- [ ] For faster syncs
> TLS is handled once, at the edge.

? What does `terraform plan -detailed-exitcode` give you?
- [ ] More colourful output
- [x] Exit code 0 = no changes, 1 = error, 2 = changes, so a pipeline can tell errors apart from "there's work to do"
- [ ] A JSON plan
- [ ] Parallel planning
> Apply only when the code is 2, and fail on 1.

? Why add a `concurrency` group to a Terraform workflow?
- [ ] To run plans faster in parallel
- [x] So two runs can never apply at the same time or fight over the state lock
- [ ] To share runners
- [ ] It's required for OIDC
> Use `cancel-in-progress: false`: you don't want to kill an apply half-way through.

? An image works on an Apple Silicon Mac, but pods on t3 nodes fail with "exec format error". Why?
- [ ] The image is too big
- [x] It was built for ARM; t3 nodes are x86, so build with `--platform linux/amd64` (or build in CI)
- [ ] The node has no internet
- [ ] The Service port is wrong
> GitHub's standard runners are x86, so pipeline builds avoid this.

? Why use `nginxinc/nginx-unprivileged` to serve a static site such as 2048?
- [ ] It includes Node.js
- [x] It serves static files and runs as a non-root user out of the box, listening on 8080 (non-root can't bind below 1024)
- [ ] It's smaller than any other image
- [ ] It's required by EKS
> Remember the port: the probes and the Service's targetPort must be 8080.

? How does a deploy pipeline handle a release whose new pods never become ready?
- [x] `kubectl rollout status --timeout` fails → `kubectl rollout undo` → exit 1, so the run goes red and the old version keeps serving
- [ ] It retries forever
- [ ] It deletes the namespace
- [ ] It ignores readiness
> Readiness probes plus rollout status give automatic, safe rollback.

? Which Helm chart installs Prometheus, Grafana, Alertmanager and the exporters in one go?
- [ ] grafana/loki
- [x] prometheus-community/kube-prometheus-stack
- [ ] bitnami/metrics-server
- [ ] jetstack/cert-manager
> It also ships ready-made Kubernetes dashboards.

? What two views should an architecture diagram for an EKS project show?
- [ ] The Terraform state file and the README
- [x] The **request flow** (user → DNS → load balancer → ingress → Service → pods) and the **deployment flow** (Git → pipelines → ECR/Terraform → EKS)
- [ ] Only the VPC subnets
- [ ] The Grafana dashboard
> How traffic arrives, and how changes arrive.

? Look at the manifest. Why will traffic never reach the pods?
```yaml
kind: Service
spec:
  selector: { app: game-2048 }
  ports: [{ port: 80, targetPort: 8080 }]
---
kind: Deployment
spec:
  template:
    metadata:
      labels: { app: game }
```
- [ ] targetPort should be 80
- [x] The Service selects `app: game-2048`, but the pods are labelled `app: game`, so it has no Endpoints
- [ ] Services can't use port 80
- [ ] The Deployment needs a LoadBalancer
> Labels must match exactly.
