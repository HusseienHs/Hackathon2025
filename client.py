# client.py
import socket
import time

from common import (
    unpack_offer, pack_request,
    pack_client_payload,
    unpack_server_payload,
    RES_NOT_OVER, RES_WIN, RES_LOSS, RES_TIE,
    pretty_card, rank_to_points
)

UDP_PORT = 13122
OFFER_TIMEOUT_SEC = 2.0
TCP_TIMEOUT_SEC = 10.0

CLIENT_TEAM_NAME = "JokerClient"


def ask_rounds() -> int:
    while True:
        s = input("Enter number of rounds (1-255): ").strip()
        try:
            x = int(s)
            if 1 <= x <= 255:
                return x
        except ValueError:
            pass
        print("Invalid number. Try again.")


def listen_for_offer() -> tuple[str, int, str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", UDP_PORT))
        s.settimeout(OFFER_TIMEOUT_SEC)
        print("Client started, listening for offer requests...")

        while True:
            try:
                data, (ip, _) = s.recvfrom(2048)
            except socket.timeout:
                continue

            offer = unpack_offer(data)
            if not offer:
                continue

            port, server_name = offer
            print(f"Received offer from {ip} (server='{server_name}', tcp_port={port})")
            return ip, port, server_name
    finally:
        s.close()


def recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Server disconnected")
        buf += chunk
    return buf


def decide_hit_or_stand(current_total: int) -> str:
    # Simple strategy: hit under 16, else stand.
    return "Hittt" if current_total < 16 else "Stand"


def main():
    while True:
        rounds = ask_rounds()
        server_ip, server_port, server_name = listen_for_offer()

        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.settimeout(TCP_TIMEOUT_SEC)

        print(f"Connecting to {server_ip}:{server_port} ...")
        tcp.connect((server_ip, server_port))
        print("Connected!")

        # Send request (exactly 38 bytes)
        tcp.sendall(pack_request(rounds, CLIENT_TEAM_NAME))

        wins = losses = ties = 0

        try:
            for r in range(1, rounds + 1):
                print(f"\n=== Round {r}/{rounds} ===")

                player_total = 0
                dealer_total = 0

                # Receive initial 3 server payloads: 2 player cards + dealer upcard
                for i in range(3):
                    pkt = recv_exact(tcp, 9)
                    parsed = unpack_server_payload(pkt)
                    if not parsed:
                        raise ValueError("Invalid server payload")

                    res, (rank, suit) = parsed
                    card_str = pretty_card(rank, suit)

                    if i < 2:
                        player_total += rank_to_points(rank)
                        print(f"Player got: {card_str} (player_total={player_total})")
                    else:
                        dealer_total += rank_to_points(rank)
                        print(f"Dealer shows: {card_str} (dealer_partial={dealer_total})")

                # Player turn
                round_over = False
                while not round_over:
                    # If player busts, server should send final LOSS next
                    if player_total > 21:
                        pkt = recv_exact(tcp, 9)
                        parsed = unpack_server_payload(pkt)
                        if parsed:
                            res, _ = parsed
                            if res == RES_LOSS:
                                losses += 1
                        print("Player busts. Round lost.")
                        round_over = True
                        break

                    decision = decide_hit_or_stand(player_total)
                    tcp.sendall(pack_client_payload(decision))
                    print(f"Decision sent: {decision}")

                    if decision == "Hittt":
                        pkt = recv_exact(tcp, 9)
                        parsed = unpack_server_payload(pkt)
                        if not parsed:
                            raise ValueError("Invalid server payload")

                        res, (rank, suit) = parsed
                        card_str = pretty_card(rank, suit)

                        player_total += rank_to_points(rank)
                        print(f"Player hit -> {card_str} (player_total={player_total})")

                        if res != RES_NOT_OVER:
                            if res == RES_WIN:
                                wins += 1
                                print("Result: WIN")
                            elif res == RES_LOSS:
                                losses += 1
                                print("Result: LOSS")
                            elif res == RES_TIE:
                                ties += 1
                                print("Result: TIE")
                            round_over = True

                    else:
                        # Stand -> dealer reveals cards until final result.
                        while True:
                            pkt = recv_exact(tcp, 9)
                            parsed = unpack_server_payload(pkt)
                            if not parsed:
                                raise ValueError("Invalid server payload")

                            res, (rank, suit) = parsed
                            card_str = pretty_card(rank, suit)

                            if res == RES_NOT_OVER:
                                dealer_total += rank_to_points(rank)
                                print(f"Dealer card: {card_str} (dealer_total={dealer_total})")

                            if res != RES_NOT_OVER:
                                if res == RES_WIN:
                                    wins += 1
                                    print("Result: WIN")
                                elif res == RES_LOSS:
                                    losses += 1
                                    print("Result: LOSS")
                                elif res == RES_TIE:
                                    ties += 1
                                    print("Result: TIE")
                                round_over = True
                                break

            total = wins + losses + ties
            win_rate = (wins / total) if total else 0.0
            print(f"\nFinished playing {total} rounds, win rate: {win_rate:.2%}")

        except (ConnectionError, socket.timeout) as e:
            print(f"[!] Connection issue: {e}")
        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            try:
                tcp.close()
            except Exception:
                pass

        print("\nReturning to offer-listening mode...\n")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
