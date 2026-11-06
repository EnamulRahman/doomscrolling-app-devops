---
topic: Networking
source: tech-vault
level: Beginner
---

? What is the difference between HTTP and HTTPS?
- [ ] HTTPS is faster because it skips headers
- [x] HTTPS is HTTP inside TLS: encrypted, tamper-proof, and the server proves its identity with a certificate
- [ ] HTTP is for APIs, HTTPS for websites
- [ ] HTTPS uses UDP
> Default ports: HTTP **80**, HTTPS **443**.

? Which part of this HTTP request is the **method**?
```output
POST /api/v1/memos HTTP/1.1
Host: tm.myegh.com
Content-Type: application/json

{"content": "buy milk"}
```
- [x] `POST`
- [ ] `/api/v1/memos`
- [ ] `Host: tm.myegh.com`
- [ ] `{"content": "buy milk"}`
> Request line = **method + path + version**. Then come the headers, a blank line and the body.

? Which HTTP method is meant for **reading** data without changing anything?
- [x] GET
- [ ] POST
- [ ] PUT
- [ ] DELETE
> GET should be safe and idempotent. POST creates, PUT/PATCH update, DELETE removes.

? A `5xx` status code means…
- [ ] the client sent a bad request
- [x] the server failed to handle a valid request
- [ ] the request was redirected
- [ ] success
> 2xx success · 3xx redirect · 4xx client error · 5xx server error.

? When would you choose **UDP** over TCP?
- [ ] When every byte must arrive in order
- [x] When speed and low latency matter more than guaranteed delivery, e.g. DNS lookups, video calls, games
- [ ] For SSH sessions
- [ ] For database connections
> UDP has no handshake and no retransmits. A late video frame is useless anyway.

? Put the TCP three-way handshake in order.
- [ ] ACK → SYN → SYN-ACK
- [x] SYN → SYN-ACK → ACK
- [ ] SYN → ACK → FIN
- [ ] HELLO → CERT → DONE
> Client SYN, server SYN-ACK, client ACK, and the connection is open.

? What does DNS do?
- [ ] Encrypts traffic
- [x] Translates names such as tm.myegh.com into IP addresses
- [ ] Assigns IP addresses to devices
- [ ] Balances load between servers
> Handing out IP addresses is **DHCP**'s job, not DNS's.

? What is **DHCP** used for?
- [x] Automatically giving devices an IP address, gateway and DNS servers when they join a network
- [ ] Resolving domain names
- [ ] Encrypting Wi-Fi
- [ ] Routing between VPCs
> That's why your laptop "just works" on new Wi-Fi.

? How many addresses does `10.0.0.0/16` contain?
- [ ] 256
- [ ] 4,096
- [x] 65,536
- [ ] 16
> 2^(32−16) = 65,536.

@ level: Intermediate
? Which of these subnets does **not** fit inside the VPC `10.0.0.0/16`?
- [ ] `10.0.3.0/24`
- [ ] `10.0.255.0/24`
- [x] `10.1.0.0/24`
- [ ] `10.0.128.0/20`
> A /16 fixes the first two numbers (`10.0`). `10.1.x.x` is outside the range.

? What is **ingress** traffic?
- [x] Traffic coming **into** a network or resource
- [ ] Traffic going out
- [ ] Traffic between two AZs
- [ ] Encrypted traffic only
> Egress = outgoing. In Memos, users → ALB is ingress, and tasks → NAT → ECR is egress.

? A **switch** vs a **router**?
- [ ] They're the same device
- [x] A switch connects devices within one network using MAC addresses (L2); a router moves traffic between networks using IPs (L3)
- [ ] A router is wireless, a switch is wired
- [ ] A switch connects to the internet, a router doesn't
> A hub (old) blindly copies traffic to every port. A switch learns which MAC is on which port.

@ level: Intermediate
? What's the difference between a **stateful** and a **stateless** firewall?
- [ ] Stateful firewalls are hardware, stateless are software
- [x] Stateful tracks connections and automatically allows replies; stateless checks every packet on its own, so you must allow return traffic yourself
- [ ] Stateless firewalls are more secure
- [ ] There's no difference
> AWS **security groups** are stateful. **NACLs** are stateless.

@ level: Intermediate
? How does **mTLS** differ from normal TLS?
- [ ] It's faster
- [x] Both client and server present certificates and authenticate each other
- [ ] It skips encryption
- [ ] It only works over UDP
> Normal TLS only proves the server's identity. mTLS is common for service-to-service and API security.

@ level: Intermediate
? Why would you use **WebSockets** instead of plain HTTPS requests?
- [ ] They're more secure
- [x] To keep a two-way connection open so the server can push updates instantly (chat, live dashboards)
- [ ] To download large files
- [ ] They don't need a port
> HTTP is request/response. WebSockets upgrade one connection into a long-lived, two-way channel.

? You can't reach a website. In which order should you investigate?
- [ ] Restart the server, then check DNS
- [x] DNS resolves? → route reachable? → port open? → app responds correctly?
- [ ] Check the app logs only
- [ ] Clear browser cookies first
> Work outward from the basics, one layer at a time: `dig` → `traceroute` → `nc`/`curl -v` → logs.

? `curl` to a server immediately returns **"Connection refused"**. What does that tell you?
- [ ] A firewall dropped the packets
- [x] The host was reached but nothing is listening on that port
- [ ] DNS failed
- [ ] The certificate expired
> Refused = there's an answer, but no listener. A **timeout** points to something dropping traffic.

@ level: Intermediate
? Data transfer between two hosts is very slow. Which tool measures the actual throughput between them?
- [ ] `dig`
- [ ] `whoami`
- [x] `iperf3`
- [ ] `chmod`
> `iperf3` measures bandwidth. `mtr`/`traceroute` show latency and loss per hop. Also check the MTU, duplex settings and errors on the interfaces.

? Which OSI layer do IP addresses and routers belong to?
- [ ] Layer 2
- [x] Layer 3
- [ ] Layer 4
- [ ] Layer 7
> L2 is MAC/switches, **L3 is IP/routers**, L4 is TCP/UDP ports and L7 is HTTP/DNS.

@ source: My guide
? Which DNS record type points a name to **another name**?
- [ ] A
- [ ] MX
- [x] CNAME
- [ ] TXT
> A → IPv4, AAAA → IPv6, CNAME → another name, MX → mail servers, TXT → text (verification).
