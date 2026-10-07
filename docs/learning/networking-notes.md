
# Networking & AWS Request Path Cheat Sheet

## 🌐 Core Concepts Explained (The Restaurant Analogy)

* **IP (Internet Protocol):** The unique address of a machine or computer that allows others to communicate with it. 
  * *Analogy:* This is like the physical **street address** of a restaurant. Without it, you cannot locate the building.
* **Port:** The specific doorway or service endpoint inside the machine.
  * *Analogy:* This is like a **particular service counter** inside the restaurant (e.g., the front counter vs. the drive-thru window).
* **DNS (Domain Name System):** The system that maps human-readable names to IP addresses.
  * *Analogy:* This is like the **brand name of the restaurant** (e.g., *://my-app.com*). Humans remember the name, and the GPS looks up the street address.

---

## ⚡ Connection Refused vs. Timeout

* **Connection Refused:** The request successfully reached the target machine, but the machine actively rejected it.
  * **What to check:** Verify that the required application/service is actually running, healthy, and listening on the correct port.
* **Timeout:** The request was sent out, but the sender never received any response before timing out. The connection vanished into a black hole.
  * **What to check:** Verify your network paths, routing, and **Security Groups / Firewalls** to see where the traffic is being blocked.

---

## 🐋 Why Containers Must Bind to `0.0.0.0`
By default, binding an application to `127.0.0.1` (localhost) means it will *only* accept traffic coming from inside its own container. 

Binding to **`0.0.0.0`** forces the application to listen on all available network interfaces. This allows the container to receive external traffic routed to it from the host, load balancers, or other network environments.

---

## 🛠️ Request Path Architecture & Troubleshooting

### Traffic Flow
`browser` ➔ `DNS` ➔ `ALB:80` ➔ `task:8000` ➔ `FastAPI`

> **Summary:** The browser asks DNS for the ALB's name and receives the ALB's IPs. It connects to the ALB on port 80. The ALB then forwards the request to the Fargate task's private IP on port 8000. Uvicorn, bound to `0.0.0.0`, hands the request to FastAPI, which returns a `200 OK` on `/health`.

### Troubleshooting Matrix

| Step | What Happens | Breaks If... | Symptom |
| :---: | :--- | :--- | :--- |
| **1** | Browser asks DNS for the ALB's name and gets its IPs. | Wrong domain name configuration or missing record. | **DNS Error** |
| **2** | Browser connects to the ALB on port 80 (or 443 for HTTPS). | ALB **Security Group** does not allow public inbound traffic. | **Timeout** |
| **3** | ALB connects to the ECS task's IP on port 8000. | Task **Security Group** does not allow traffic from the ALB's Security Group. | **Timeout** |
| **4** | Uvicorn (bound to `0.0.0.0:8000`) hands the request to FastAPI. | App is bound to `127.0.0.1`, configured on the wrong port, or crashed entirely. | **Connection Refused** |
| **5** | FastAPI returns `200 OK` on the `/health` endpoint. | Application code throws an unhandled exception, marking the target unhealthy. | **503 Service Unavailable** (from ALB) |

