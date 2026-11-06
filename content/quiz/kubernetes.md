---
topic: Kubernetes
source: tech-vault
level: Intermediate
---

? What is Kubernetes?
- [ ] A container image format
- [x] An open-source container orchestration platform that deploys, scales, heals and networks containers across many machines
- [ ] A Linux distribution
- [ ] AWS's container service
> It started at Google and is now run by the CNCF. EKS is AWS's managed Kubernetes.

? What problems does Kubernetes solve?
- [ ] Writing application code
- [x] Scheduling containers onto machines, self-healing, scaling, service discovery and load balancing, and rolling updates
- [ ] Building images
- [ ] Version control
> All of it comes from the declarative desired state plus control loops.

? Docker vs Kubernetes?
- [ ] Kubernetes replaces images
- [x] Docker builds and runs containers on one host; Kubernetes orchestrates containers across a cluster of hosts
- [ ] They are competitors doing the same thing
- [ ] Docker is only for Windows
> Kubernetes runs container images using a runtime such as containerd.

? What is a **Pod**?
- [x] The smallest deployable unit: one or more containers sharing a network namespace (one IP) and volumes
- [ ] A physical server
- [ ] A cluster of nodes
- [ ] A Docker image
> Containers in the same pod talk over `localhost`.

? How do containers in the same Pod communicate?
- [ ] Through the Ingress
- [x] Over `localhost`, because they share a network namespace, and through shared volumes
- [ ] Only via a Service
- [ ] They can't
> A common pattern is a sidecar (e.g. a log shipper) next to the app container.

? What does a **Deployment** do?
- [ ] Builds images
- [x] Manages ReplicaSets to keep N pods running and performs rolling updates and rollbacks
- [ ] Exposes pods to the internet
- [ ] Stores secrets
> `kubectl rollout undo deployment/memos` rolls back.

? When do you use a **StatefulSet** instead of a Deployment?
- [ ] For stateless web apps
- [x] For stateful apps that need stable network identities and their own persistent volume each (databases, Kafka)
- [ ] For batch jobs
- [ ] For DaemonSets
> Pods get stable names (`db-0`, `db-1`) and keep their own storage across restarts.

? How do you restrict which pods can talk to each other?
- [ ] Security groups only
- [x] NetworkPolicies (enforced by a CNI plugin that supports them, such as Calico or Cilium)
- [ ] Namespaces alone block traffic
- [ ] ConfigMaps
> By default every pod can reach every pod. NetworkPolicies are how you lock that down.

? What is the role of **etcd**?
- [ ] Running containers
- [x] A consistent key-value store holding all cluster state and configuration
- [ ] Load balancing traffic
- [ ] Building images
> Back it up. Losing etcd means losing the cluster's state.

? What is the **kube-apiserver**?
- [x] The control plane's front door: every request (kubectl, controllers, kubelets) goes through it, and it validates and stores changes in etcd
- [ ] The node agent
- [ ] The DNS server
- [ ] The container runtime
> Nothing talks to etcd directly. Everything goes through the API server.

? What is an **Ingress controller**?
- [ ] A firewall for nodes
- [x] A component that implements Ingress rules: an HTTP(S) proxy routing outside traffic to Services by host or path (e.g. NGINX, or the AWS Load Balancer Controller → ALB)
- [ ] A type of Pod security policy
- [ ] The scheduler
> An Ingress object does nothing without a controller.

? What happens if a control-plane (master) node fails in a single-master cluster?
- [ ] All pods are deleted immediately
- [x] Running pods keep running, but you can't make changes, and failed pods aren't rescheduled until the control plane is back
- [ ] Nothing at all
- [ ] Worker nodes become masters
> That's why production uses **3+ control-plane nodes** (or a managed one, such as EKS).

? How do you build a highly available Kubernetes cluster?
- [ ] One big node
- [x] Several control-plane nodes with etcd quorum, worker nodes spread across AZs, multiple replicas per app, plus PodDisruptionBudgets
- [ ] Run everything in one namespace
- [ ] Disable the scheduler
> EKS runs the control plane across 3 AZs for you.

? What are **taints and tolerations**?
- [ ] Image vulnerabilities
- [x] A taint on a node repels pods; only pods with a matching toleration can be scheduled there
- [ ] Network rules
- [ ] Ways to tag images
> Used to dedicate nodes (GPU nodes, for example) or keep workloads off the control plane.

? Which object gives pods a stable name and IP?
- [ ] Deployment
- [x] Service
- [ ] ConfigMap
- [ ] Node
> Pod IPs change. A Service's ClusterIP and DNS name don't.
