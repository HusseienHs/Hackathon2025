# ♠️ Hackathon 2025 — Network Blackjack (UDP ➜ TCP)

<div align="center">

**A modern, binary-protocol client/server Blackjack game**  
Server discovery via **UDP broadcast**, gameplay over **TCP**.

Built for the **Intro to Computer Networks Hackathon (2025)**.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Sockets](https://img.shields.io/badge/Networking-Sockets-informational)
![UDP](https://img.shields.io/badge/UDP-Broadcast-orange)
![TCP](https://img.shields.io/badge/TCP-Binary%20Protocol-success)
![Status](https://img.shields.io/badge/Status-Ready%20to%20Play-brightgreen)

🎯 **One command to host. One command to play.**  
Fast setup, robust packet handling, protocol-faithful implementation.

</div>

---

## ✨ Highlights

- ⚡ **Zero‑config discovery** — clients auto‑discover servers using UDP broadcast (port `13122`)
- 🧠 **Binary protocol** — strict packet formats with magic cookies and fixed sizes
- ♣️ **Blackjack gameplay** — multi‑round sessions, dealer logic, and result handling
- 🧵 **Multi‑client server** — concurrent TCP clients via threading
- 🛡️ **Defensive networking** — exact‑length reads, timeouts, malformed packet protection

---

## 🗂️ Project Structure

```
.
├── client.py      # Discovers server via UDP, plays Blackjack over TCP
├── server.py      # Broadcasts offers (UDP), serves games (TCP)
├── common.py      # Protocol structs, packing/unpacking, card utilities
└── README.md
```

---

## 🚀 Quick Start

### 1️⃣ Clone the repository
```bash
git clone https://github.com/HusseienHs/Hackathon2025.git
cd Hackathon2025
```

### 2️⃣ Run the server (Terminal 1)
```bash
python server.py
```

Expected output:
```
Server started, listening on TCP port <PORT>
```

### 3️⃣ Run the client (Terminal 2)
```bash
python client.py
```

Client flow:
- Listens for UDP offers
- Connects to the server via TCP
- Sends a game request
- Plays Blackjack rounds automatically

---

## 🎮 Gameplay Flow (High Level)

### Server
- Broadcasts UDP offers every second
- Accepts TCP connections
- Deals cards and manages game logic
- Sends round updates and final results

### Client
- Listens on UDP port `13122`
- Connects to advertised TCP port
- Requests number of rounds
- Plays using a simple strategy

---

## 🧩 Protocol Summary (Binary)

All packets use a **magic cookie** and fixed sizes.

### UDP Offer (Server ➜ Client)
```
cookie(4) | msg_type(1) | tcp_port(2) | server_name(32)
```

### TCP Request (Client ➜ Server)
```
cookie(4) | msg_type(1) | num_rounds(1) | client_name(32)
```

### TCP Payloads

**Server ➜ Client**
```
cookie(4) | msg_type(1) | result(1) | card_rank(2) | card_suit(1)
```

**Client ➜ Server**
```
cookie(4) | msg_type(1) | decision(5)   # "Hittt" or "Stand"
```

---

## 🧠 Client Strategy

Default logic:
- **Hit** if total < 16
- **Stand** otherwise

```python
def decide_hit_or_stand(current_total: int) -> str:
    return "Hittt" if current_total < 16 else "Stand"
```

---

## 🛠️ Troubleshooting

### Client doesn’t receive offers
- Ensure server and client are on the same network
- Disable VPNs/firewalls temporarily
- Try running both on the same machine

### Connection hangs
Usually indicates a packet-size mismatch.

Packet sizes used:
- Offer: **39 bytes**
- Request: **38 bytes**
- Server payload: **9 bytes**
- Client payload: **10 bytes**

### Windows
Run PowerShell as **Administrator** if firewall blocks UDP/TCP traffic.

---

## 🔬 Engineering Notes

- Exact-length reads using `recv_exact()` prevent partial TCP reads
- Threaded server supports multiple clients
- Fixed-length UTF‑8 names (32 bytes, null‑padded)
- Simplified Blackjack rules per assignment specification

---

## 🧭 Roadmap

- [ ] Interactive client mode (manual Hit / Stand)
- [ ] Improved Blackjack strategy
- [ ] Server scoreboard & statistics
- [ ] Dockerized demo environment
- [ ] CI checks (lint + protocol tests)

---

## 👤 Author

**Husseien Hsnen**  
GitHub: https://github.com/HusseienHs

---

## ⭐ Support

If you liked this project, consider starring the repository ⭐
