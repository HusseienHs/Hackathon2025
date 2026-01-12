# Hackathon2025
<!-- =======================
      Hackathon 2025 README
     ======================= -->

<div align="center">

# ♠️ Hackathon 2025 — Network Blackjack (UDP Offer ➜ TCP Game)

**A clean, binary-protocol client/server game** that discovers servers via **UDP broadcast** and plays **Blackjack over TCP** — built for the *Intro to Computer Networks Hackathon (2025)*.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white" />
  <img alt="Sockets" src="https://img.shields.io/badge/Networking-Sockets-informational" />
  <img alt="UDP" src="https://img.shields.io/badge/UDP-Broadcast-orange" />
  <img alt="TCP" src="https://img.shields.io/badge/TCP-Binary%20Protocol-success" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Ready%20to%20Play-brightgreen" />
</p>

<br/>

**🎯 One command to host. One command to play.**  
Fast setup, robust packet handling, and a protocol-faithful implementation.

</div>

---

## ✨ Highlights

- ⚡ **Zero-config discovery** — client listens for **UDP offers** (port `13122`) and connects automatically.
- 🧠 **Binary protocol** — strict packet sizes & parsing (cookie, message types, fixed-length names).
- ♣️ **Blackjack gameplay** — multi-round sessions, dealer logic, and result reporting.
- 🧵 **Multi-client server** — handles multiple TCP clients concurrently (threads).
- 🛡️ **Defensive networking** — exact-length reads, timeouts, malformed packet handling.

---

## 🗂️ Project Structure

```text
.
├── client.py      # Discovers server via UDP offer, plays rounds over TCP
├── server.py      # Broadcasts offers over UDP, serves games over TCP
├── common.py      # Protocol structs, packing/unpacking helpers, card utils
└── README.md
🚀 Quick Start
1) Clone
bash
Copy code
git clone https://github.com/HusseienHs/Hackathon2025.git
cd Hackathon2025
2) Run the server (Terminal 1)
bash
Copy code
python server.py
You should see something like:

nginx
Copy code
Server started, listening on TCP port <PORT>
3) Run the client (Terminal 2)
bash
Copy code
python client.py
Client flow:

Waits for UDP offer

Connects to server TCP port

Sends request (round count + client name)

Plays blackjack rounds

🎮 Gameplay Flow (High Level)
Server

Broadcasts UDP offers every second

Accepts TCP clients

Deals cards and drives the game logic

Sends round updates + final outcome

Client

Listens for offers on UDP 13122

Connects to server TCP port from the offer

Sends a game request

Plays with a simple strategy (“Hit under 16, else Stand”)

🧩 Protocol Summary (Binary)
This implementation uses a magic cookie and fixed-size packets.

UDP Offer (Server ➜ Client)
cookie(4) | msg_type(1) | tcp_port(2) | server_name(32)

TCP Request (Client ➜ Server)
cookie(4) | msg_type(1) | num_rounds(1) | client_name(32)

TCP Payload (Both Directions)
Server ➜ Client (round updates)

cookie(4) | msg_type(1) | result(1) | card_rank(2) | card_suit(1)

Client ➜ Server (decision)

cookie(4) | msg_type(1) | decision(5) → "Hittt" or "Stand"

🧠 Strategy (Client)
Default strategy:

Hit if total < 16

Stand otherwise

You can change it here:

py
Copy code
def decide_hit_or_stand(current_total: int) -> str:
    return "Hittt" if current_total < 16 else "Stand"
🛠️ Troubleshooting
“Client doesn’t receive offers”
Make sure server and client are on the same network

UDP broadcast can be blocked by:

firewall rules

VPNs

different subnets

Try running both on the same machine first.

“Connection hangs”
Usually means a packet-size mismatch

This repo uses:

Offer = 39 bytes

Request = 38 bytes

Server payload = 9 bytes

Client payload = 10 bytes

Windows tips
Run PowerShell as Admin if ports are restricted by firewall policies.

🔬 Engineering Notes
Exact-length reads are done via recv_exact() to avoid partial TCP reads.

The server is multi-threaded for concurrent clients.

Names are fixed 32 bytes and null-padded (UTF-8 safe).

Game rules follow simplified blackjack scoring (e.g., Ace handling per spec).

🧭 Roadmap (Nice-to-have)
 Interactive client mode (manual Hit/Stand)

 Better strategy (basic blackjack heuristic)

 Server scoreboard + session summary packet

 Dockerfile for quick demo environment

 CI sanity checks (lint + minimal protocol tests)

👤 Author
YOUR_NAME / TEAM_NAME
GitHub: https://github.com/HusseienHs

📜 License
Add a license if required by your course/team (MIT is common).
If not needed, you can remove this section.

