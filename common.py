# common.py
import struct
from dataclasses import dataclass
from typing import Optional, Tuple

MAGIC_COOKIE = 0xabcddcba

# Message types
MSG_OFFER = 0x2
MSG_REQUEST = 0x3
MSG_PAYLOAD = 0x4

# Fixed UDP port for offers (client must listen here)
UDP_PORT = 13122

# Offer / request sizes (fixed)
OFFER_STRUCT = struct.Struct("!I B H 32s")   # cookie, type, port, server_name  => 39 bytes
REQUEST_STRUCT = struct.Struct("!I B B 32s") # cookie, type, rounds, client_name => 38 bytes

# Payload header: cookie + type
PAYLOAD_HDR_STRUCT = struct.Struct("!I B")   # 5 bytes

# Server round result
RES_NOT_OVER = 0x0
RES_TIE      = 0x1
RES_LOSS     = 0x2
RES_WIN      = 0x3

# Suit encoding (HDCS) -> 0..3
SUITS = ["H", "D", "C", "S"]


def fix_name(name: str) -> bytes:
    """Encode name to exactly 32 bytes, null-padded."""
    b = name.encode("utf-8", errors="ignore")[:32]
    return b + b"\x00" * (32 - len(b))


def parse_name(b: bytes) -> str:
    """Decode null-terminated UTF-8 name from 32 bytes."""
    return b.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")


def pack_offer(tcp_port: int, server_name: str) -> bytes:
    return OFFER_STRUCT.pack(MAGIC_COOKIE, MSG_OFFER, tcp_port, fix_name(server_name))


def unpack_offer(data: bytes) -> Optional[Tuple[int, str]]:
    if len(data) != OFFER_STRUCT.size:
        return None
    cookie, mtype, port, name_b = OFFER_STRUCT.unpack(data)
    if cookie != MAGIC_COOKIE or mtype != MSG_OFFER:
        return None
    return port, parse_name(name_b)


def pack_request(num_rounds: int, client_name: str) -> bytes:
    if not (1 <= num_rounds <= 255):
        raise ValueError("num_rounds must be 1..255")
    return REQUEST_STRUCT.pack(MAGIC_COOKIE, MSG_REQUEST, num_rounds, fix_name(client_name))


def unpack_request(data: bytes) -> Optional[Tuple[int, str]]:
    if len(data) != REQUEST_STRUCT.size:
        return None
    cookie, mtype, rounds, name_b = REQUEST_STRUCT.unpack(data)
    if cookie != MAGIC_COOKIE or mtype != MSG_REQUEST:
        return None
    return rounds, parse_name(name_b)


def pack_card(rank: int, suit: int) -> bytes:
    """
    Card encoding is 3 bytes:
      - rank: uint16 (01-13)
      - suit: uint8  (0-3) mapped to SUITS = ["H","D","C","S"]
    """
    if not (1 <= rank <= 13) or not (0 <= suit <= 3):
        raise ValueError("Invalid card")
    return struct.pack("!H B", rank, suit)


def unpack_card(b: bytes) -> Optional[Tuple[int, int]]:
    if len(b) != 3:
        return None
    rank, suit = struct.unpack("!H B", b)
    if not (1 <= rank <= 13) or not (0 <= suit <= 3):
        return None
    return rank, suit


def pack_server_payload(result: int, card_rank: int, card_suit: int) -> bytes:
    # cookie(4) type(1) result(1) card(3) = 9 bytes
    return (
        PAYLOAD_HDR_STRUCT.pack(MAGIC_COOKIE, MSG_PAYLOAD)
        + bytes([result])
        + pack_card(card_rank, card_suit)
    )


def unpack_server_payload(data: bytes) -> Optional[Tuple[int, Tuple[int, int]]]:
    # Expect 9 bytes
    if len(data) != 9:
        return None
    cookie, mtype = PAYLOAD_HDR_STRUCT.unpack(data[:5])
    if cookie != MAGIC_COOKIE or mtype != MSG_PAYLOAD:
        return None
    result = data[5]
    card = unpack_card(data[6:9])
    if card is None:
        return None
    return result, card


def pack_client_payload(decision5: str) -> bytes:
    """
    Client decision is exactly 5 ASCII bytes: "Hittt" or "Stand"
    Packet: cookie(4) type(1) decision(5) = 10 bytes
    """
    if decision5 not in ("Hittt", "Stand"):
        raise ValueError("decision must be 'Hittt' or 'Stand'")
    d = decision5.encode("ascii")
    return PAYLOAD_HDR_STRUCT.pack(MAGIC_COOKIE, MSG_PAYLOAD) + d


def unpack_client_payload(data: bytes) -> Optional[str]:
    if len(data) != 10:
        return None
    cookie, mtype = PAYLOAD_HDR_STRUCT.unpack(data[:5])
    if cookie != MAGIC_COOKIE or mtype != MSG_PAYLOAD:
        return None
    decision = data[5:10].decode("ascii", errors="ignore")
    if decision not in ("Hittt", "Stand"):
        return None
    return decision


def rank_to_points(rank: int) -> int:
    # Ace=11, Face=10, Numbers=rank
    if rank == 1:
        return 11
    if rank >= 11:
        return 10
    return rank


def pretty_card(rank: int, suit: int) -> str:
    r = {1: "A", 11: "J", 12: "Q", 13: "K"}.get(rank, str(rank))
    s = SUITS[suit]
    return f"{r}{s}"


@dataclass
class Card:
    rank: int
    suit: int
