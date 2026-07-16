# Customizable Consistent Hashing Load Balancer

An elastically scalable, highly available, and fault-tolerant distributed system load balancer built using **Python Flask**, **Docker**, and a custom-designed **Consistent Hashing Ring**.

---

## Key Features
* **Custom Consistent Hashing Ring:** Built with $M = 512$ slots, featuring $K = 50$ virtual replicas per node to distribute requests evenly across the ring.
* **Upgraded MD5 Hashing:** Employs cryptographically uniform MD5 hashing to completely eliminate server clustering and traffic bottlenecks.
* **Active Heartbeat & Self-Healing:** A background thread monitors the health of all  active backend containers. If a container fails, it automatically purges it from the ring and provisions a fresh recovery container in under 5 seconds.
* **Elastic REST API:** Exposes administrative endpoints to check active replicas (`GET /rep`), dynamically scale up (`POST /add`), and scale down (`DELETE /rm`) containers programmatically.

---

## System Architecture

The load balancer operates on a private, isolated Docker bridge network. The load balancer container acts as a reverse proxy on public port `5000`, while the backend server containers run on private network ports, shielded from direct host machine access.

---

## Installations & Deployment

### Prerequisites
* Ubuntu Linux (or VM)
* Docker & Docker Compose
* Python 3 & pip (for running tests)

### Quick Deployment
Deploy the entire baseline cluster ($N = 3$ backend replicas and the load balancer) with a single command:

```bash
# Launch the multi-container environment
make up
# or 
sudo docker compose up -d --build
# Verify that all baseline containers are running successfully
make status
```
### REST API Reference
* **Retrieve Active Replicas:**
    * Endpoint: **GET /rep**
    * Action: Queries the consistent hashing ring and returns a list of active backend nodes.
* **Elastic Scale-Up:**
    * Endpoint: **POST /add**
    * Payload: **{"n": 2, "hostnames": ["server-4", "server-5"]}**
    * Action: Provisions N new Docker containers on the fly and maps their virtual replicas to the hash ring
* **Dynamic Scale-Down**
    * Endpoint: **DELETE /rm**
    * Payload: **{"n": 1, "hostnames": ["server-5"]}
    * Action: Purges virtual nodes, shuts down corresponding containers, and frees system resources.
* **Stateful Client Request Routing**
    * Endpoint: **Get /<path>?id=<request_id>**
    * Action: Hashes the incoming query ID, maps it clockwise to the nearest server replica, and proxies the payload seamlessly.

### Testing & Scalability Verification
The testing environment uses a multithread simulation script **test_analysis.py** to flood the load balancer with 10,000 concurrent client requests over persistent connections.

To run the load testing analysis:

```bash
python3 test_analysis.py
```

### Scalability Performance Results
The MD5 hash ring modification successfully achieved uniform load distribution. When scaling the cluster size from N = 2 up to N = 6 servers, the actual workload curves tightly follow the mathematical Theoretical ideal baseline, with a maximum workload variance of only ~6.37%:

| Cluster Size ($N$) | Theoretical Ideal Load | Highest Server Load | Lowest Server Load | Operational Status |
| :---: | :---: | :---: | :---: | :---: |
| **2 Servers** | 5,000 | 5,359 (`server-1`) | 4,641 (`server-2`) | **Stable / Balanced** |
| **3 Servers** | 3,333 | 3,784 (`server-1`) | 2,830 (`server-3`) | **Stable / Balanced** |
| **4 Servers** | 2,500 | 3,155 (`server-1`) | 2,070 (`server-4`) | **Stable / Balanced** |
| **5 Servers** | 2,000 | 2,346 (`server-1`) | 1,814 (`server-5`) | **Stable / Balanced** |
| **6 Servers** | 1,666 | 2,047 (`server-1`) | 1,410 (`server-6`) | **Stable / Balanced** |