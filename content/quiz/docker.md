---
topic: Docker
source: tech-vault
level: Beginner
---

? What is a container?
- [ ] A small virtual machine with its own kernel
- [x] An isolated Linux process (namespaces + cgroups) packaged with its app and dependencies
- [ ] A zip file
- [ ] A type of server
> It shares the host kernel. That's why it starts in seconds.

? What is a Dockerfile used for?
- [x] Defining, step by step, how to build an image
- [ ] Running several containers together
- [ ] Storing container logs
- [ ] Configuring Kubernetes
> Running several containers together is Docker **Compose**'s job.

? Which command opens a shell inside a running container called `memos`?
- [ ] `docker run memos sh`
- [x] `docker exec -it memos sh`
- [ ] `docker attach -shell memos`
- [ ] `docker ssh memos`
> `run` starts a **new** container. `exec` runs a command in an **existing** one.

? What is a **dangling** image?
- [ ] An image with a security issue
- [x] An image layer with no tag (shown as `<none>`), usually left over after rebuilding a tag
- [ ] An image being pushed
- [ ] An image over 1 GB
> Clean up with `docker image prune`.

? `COPY` vs `ADD` in a Dockerfile?
- [x] COPY just copies files; ADD can also extract local tar files and download URLs, so prefer COPY unless you need that
- [ ] ADD is faster
- [ ] COPY only works with folders
- [ ] They're identical
> Being explicit (COPY) avoids surprises.

? `EXPOSE 8081` in a Dockerfile vs `-p 8081:8081` at run time?
- [ ] Both publish the port
- [x] EXPOSE only documents the port; `-p` actually publishes it to the host
- [ ] EXPOSE opens a firewall rule
- [ ] `-p` is only for Kubernetes
> Without `-p` (or a service or orchestrator mapping it), nothing outside can reach the port.

? `RUN`, `CMD` and `ENTRYPOINT`?
- [ ] All three run at build time
- [x] RUN runs at build time; ENTRYPOINT is the main executable at start-up; CMD gives default arguments that can be overridden
- [ ] CMD runs at build time
- [ ] ENTRYPOINT only works with shell scripts
> Memos uses `ENTRYPOINT ["memos"]`.

@ level: Intermediate
? If you set a 512 MB memory **limit** on a container, is that memory reserved for it?
- [ ] Yes, the host sets aside 512 MB immediately
- [x] No, it's a maximum; the container is killed (OOM, exit 137) if it tries to go over
- [ ] It's a minimum guarantee
- [ ] Limits are ignored by Docker
> A **reservation** (or a request in Kubernetes) is the guarantee. A **limit** is the cap.

@ level: Intermediate
? Is it a good idea to run a **stateful** app (like a database) in a container?
- [ ] Never
- [x] It can be done, but only with persistent volumes, backups and care; managed databases are often simpler
- [ ] Always: containers are ideal for state
- [ ] Only if it runs as root
> Containers are disposable. Memos' SQLite-in-the-container problem is exactly this lesson.

? What is Docker Compose for?
- [x] Defining and running multiple related containers (app + database) from one YAML file
- [ ] Building images faster
- [ ] Production orchestration across many hosts
- [ ] Scanning images
> For production across many hosts you'd use ECS or Kubernetes. Compose is great for local development.

@ level: Intermediate
? What is an **orphaned** (dangling) volume, and how do you remove it?
- [ ] A volume shared by two containers; `docker rm -v`
- [x] A volume no container uses any more; `docker volume prune`
- [ ] A volume that's full; `docker volume grow`
- [ ] A volume with root files; `chmod`
> Removing containers doesn't remove their named volumes. They pile up until pruned.

@ level: Intermediate
? Name a real limitation of containers compared with VMs.
- [ ] They're slower to start
- [x] Weaker isolation, because they share the host kernel, and they can't run a different OS kernel
- [ ] They use more RAM
- [ ] They can't run Linux
> For strong multi-tenant isolation people use VMs, or micro-VMs such as Firecracker (which Fargate uses underneath).

? Which is a production best practice for containers?
- [ ] Run as root for simplicity
- [ ] Use the `latest` tag everywhere
- [x] Use small trusted base images, run as non-root, inject secrets at runtime and pin image versions
- [ ] Store data inside the container
> Memos follows these: Alpine, user 1001, SHA tags. Secrets would come from Secrets Manager.

? Look at the Dockerfile. What will be in the **final** image?
```dockerfile
FROM golang:1.25-alpine AS backend
COPY . .
RUN go build -o /memos ./cmd/memos

FROM alpine:3.21
COPY --from=backend /memos /usr/local/bin/memos
ENTRYPOINT ["memos"]
```
- [ ] Go, the source code and the binary
- [x] Only Alpine plus the `memos` binary
- [ ] Just the source code
- [ ] Both stages stacked
> The final image is **only the last stage**. The Go toolchain and source stay behind in the builder.
