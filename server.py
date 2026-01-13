# server.py
import random
import socket
import threading
from typing import List, Tuple

from common import (
    pack_offer, unpack_request,
    pack_server_payload,
    unpack_client_payload,
    RES_NOT_OVER, RES_WIN, RES_LOSS, RES_TIE,
    Card, rank_to_points, pretty_card
)

UDP_PORT = 13122
OFFER_INTERVAL_SEC = 1.0

TCP_BACKLOG = 50
TCP_TIMEOUT = 10.0

SERVER_NAME = "Blackijecky"


def make_deck() -> List[Card]:
    deck = [Card(rank=r, suit=s) for s in range(4) for r in range(1, 14)]
    random.shuffle(deck)
    return deck


def draw(deck: List[Card]) -> Card:
    return deck.pop()


def hand_total(hand: List[Card]) -> int:
    return sum(rank_to_points(c.rank) for c in hand)


def recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Client disconnected")
        buf += chunk
    return buf


def udp_broadcast_offers(stop_evt: threading.Event, tcp_port: int) -> None:
    msg = pack_offer(tcp_port, SERVER_NAME)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        while not stop_evt.is_set():
            try:
                s.sendto(msg, ("<broadcast>", UDP_PORT))
            except OSError:
                pass
            stop_evt.wait(OFFER_INTERVAL_SEC)
    finally:
        s.close()


def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    conn.settimeout(TCP_TIMEOUT)
    print(f"[+] TCP client connected from {addr[0]}:{addr[1]}")

    try:
        req = recv_exact(conn, 38)
        parsed = unpack_request(req)
        if not parsed:
            print("[!] Invalid request packet; closing")
            return

        rounds, client_name = parsed
        print(f"[i] Request from '{client_name}' for {rounds} rounds")

        wins = losses = ties = 0

        for r in range(1, rounds + 1):
            print(f"\n=== Round {r}/{rounds} with {client_name} ===")

            deck = make_deck()
            player = [draw(deck), draw(deck)]
            dealer = [draw(deck), draw(deck)]

            print(f"Player cards: {pretty_card(player[0].rank, player[0].suit)} "
                  f"{pretty_card(player[1].rank, player[1].suit)} (total={hand_total(player)})")
            print(f"Dealer shows: {pretty_card(dealer[0].rank, dealer[0].suit)} (hidden=??)")

            # initial 3 payloads
            conn.sendall(pack_server_payload(RES_NOT_OVER, player[0].rank, player[0].suit))
            conn.sendall(pack_server_payload(RES_NOT_OVER, player[1].rank, player[1].suit))
            conn.sendall(pack_server_payload(RES_NOT_OVER, dealer[0].rank, dealer[0].suit))

            round_finished = False

            while not round_finished:
                pt = hand_total(player)
                if pt > 21:
                    print(f"Player busts with {pt}. Dealer wins.")
                    losses += 1
                    # Send final result once (card field can be any valid card; keep dealer[0] like you had)
                    conn.sendall(pack_server_payload(RES_LOSS, dealer[0].rank, dealer[0].suit))
                    round_finished = True
                    break

                decision_pkt = recv_exact(conn, 10)
                decision = unpack_client_payload(decision_pkt)
                if decision not in ("Hittt", "Stand"):
                    print("[!] Invalid decision; treating as Stand")
                    decision = "Stand"

                print(f"Client decision: {decision}")

                if decision == "Hittt":
                    c = draw(deck)
                    player.append(c)
                    conn.sendall(pack_server_payload(RES_NOT_OVER, c.rank, c.suit))
                    print(f"Player hits: {pretty_card(c.rank, c.suit)} (total={hand_total(player)})")
                    continue

                # Stand: reveal hidden card
                conn.sendall(pack_server_payload(RES_NOT_OVER, dealer[1].rank, dealer[1].suit))
                print(f"Dealer reveals: {pretty_card(dealer[1].rank, dealer[1].suit)} "
                      f"(total={hand_total(dealer)})")

                while hand_total(dealer) < 17:
                    c = draw(deck)
                    dealer.append(c)
                    conn.sendall(pack_server_payload(RES_NOT_OVER, c.rank, c.suit))
                    print(f"Dealer hits: {pretty_card(c.rank, c.suit)} (total={hand_total(dealer)})")

                dt = hand_total(dealer)
                pt2 = hand_total(player)

                if dt > 21:
                    print(f"Dealer busts with {dt}. Player wins.")
                    wins += 1
                    conn.sendall(pack_server_payload(RES_WIN, dealer[-1].rank, dealer[-1].suit))
                else:
                    if pt2 > dt:
                        print(f"Player {pt2} > Dealer {dt}. Player wins.")
                        wins += 1
                        conn.sendall(pack_server_payload(RES_WIN, dealer[-1].rank, dealer[-1].suit))
                    elif dt > pt2:
                        print(f"Dealer {dt} > Player {pt2}. Dealer wins.")
                        losses += 1
                        conn.sendall(pack_server_payload(RES_LOSS, dealer[-1].rank, dealer[-1].suit))
                    else:
                        print(f"Tie: Player {pt2} == Dealer {dt}.")
                        ties += 1
                        conn.sendall(pack_server_payload(RES_TIE, dealer[-1].rank, dealer[-1].suit))

                round_finished = True

        total = wins + losses + ties
        win_rate = (wins / total) if total else 0.0
        print(f"\n[i] Finished session with {client_name}: "
              f"{total} rounds, W={wins}, L={losses}, T={ties}, win_rate={win_rate:.2%}")

    except (ConnectionError, socket.timeout) as e:
        print(f"[!] Connection issue with {addr}: {e}")
    except Exception as e:
        print(f"[!] Unexpected error with {addr}: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        print(f"[-] TCP client {addr[0]}:{addr[1]} disconnected")


def main():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.bind(("", 0))  # OS chooses port
    tcp.listen(TCP_BACKLOG)
    tcp_port = tcp.getsockname()[1]

    print(f"Server started, listening on TCP port {tcp_port}")

    stop_evt = threading.Event()
    t = threading.Thread(target=udp_broadcast_offers, args=(stop_evt, tcp_port), daemon=True)
    t.start()

    try:
        while True:
            conn, addr = tcp.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
    finally:
        stop_evt.set()
        try:
            tcp.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
