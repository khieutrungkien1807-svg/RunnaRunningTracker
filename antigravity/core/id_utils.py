"""
ID Utilities — Foundation for all Antigravity components.

Provides time-sortable ID generation (ULID and UUIDv7) and validation.
All system-generated IDs (session_id, operation_id, patch_id, trace_id)
must use one of these formats to ensure lexicographic == chronological ordering.

Requirements: 8.1, 8.3
"""

from __future__ import annotations

import os
import re
import struct
import time

# ── Validation patterns ───────────────────────────────────────────────────────

# Crockford Base32 alphabet (uppercase, no I/L/O/U)
_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CROCKFORD_SET = set(_CROCKFORD_ALPHABET)

ULID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
UUIDV7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# ── ULID implementation ───────────────────────────────────────────────────────

def _encode_crockford(value: int, length: int) -> str:
    """Encode an integer into Crockford Base32 string of given length."""
    chars = []
    for _ in range(length):
        chars.append(_CROCKFORD_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def generate_ulid() -> str:
    """
    Generate a ULID (Universally Unique Lexicographically Sortable Identifier).

    Format: 26 characters, Crockford Base32 alphabet.
    - First 10 chars: 48-bit millisecond timestamp
    - Last 16 chars: 80-bit cryptographically random component

    Time-sortable: lexicographic order == chronological order.
    """
    # 48-bit timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    timestamp_part = _encode_crockford(timestamp_ms, 10)

    # 80-bit random component (10 bytes)
    random_bytes = os.urandom(10)
    random_int = int.from_bytes(random_bytes, "big")
    random_part = _encode_crockford(random_int, 16)

    return timestamp_part + random_part


# ── UUIDv7 implementation ─────────────────────────────────────────────────────

def generate_uuidv7() -> str:
    """
    Generate a UUIDv7 (time-ordered UUID per RFC 9562 draft).

    Format: xxxxxxxx-xxxx-7xxx-xxxx-xxxxxxxxxxxx
    - Bits 0-47:  48-bit Unix timestamp in milliseconds
    - Bits 48-51: version field (0b0111 = 7)
    - Bits 52-63: 12-bit sub-millisecond / random
    - Bits 64-65: variant field (0b10)
    - Bits 66-127: 62-bit random

    Time-sortable: lexicographic order == chronological order.
    """
    timestamp_ms = int(time.time() * 1000)

    # 12 random bits for sub-ms precision
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF

    # 62 random bits (8 bytes, top 2 bits overwritten by variant)
    rand_b_bytes = os.urandom(8)
    rand_b = int.from_bytes(rand_b_bytes, "big")

    # Pack into 128-bit UUID
    # time_high (32 bits): top 32 bits of timestamp
    time_high = (timestamp_ms >> 16) & 0xFFFFFFFF
    # time_mid (16 bits): next 16 bits of timestamp
    time_mid = timestamp_ms & 0xFFFF
    # ver_rand_a (16 bits): version=7 (4 bits) + rand_a (12 bits)
    ver_rand_a = 0x7000 | rand_a
    # variant_rand_b (64 bits): variant=10 (2 bits) + rand_b (62 bits)
    variant_rand_b = (rand_b & 0x3FFFFFFFFFFFFFFF) | 0x8000000000000000

    # Format as UUID string
    b = struct.pack(
        ">IHH8s",
        time_high,
        time_mid,
        ver_rand_a,
        variant_rand_b.to_bytes(8, "big"),
    )
    hex_str = b.hex()
    return (
        f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}"
        f"-{hex_str[16:20]}-{hex_str[20:32]}"
    )


# ── Validation ────────────────────────────────────────────────────────────────

def is_valid_time_sortable_id(id_str: str) -> bool:
    """
    Validate that a string is a valid UUIDv7 or ULID.

    Accepts:
    - ULID: 26 chars, Crockford Base32 (0-9, A-H, J-N, P-T, V-Z)
    - UUIDv7: standard UUID format with version=7

    Returns True if valid, False otherwise.
    """
    if not isinstance(id_str, str):
        return False
    return bool(ULID_PATTERN.match(id_str) or UUIDV7_PATTERN.match(id_str))


# ── Convenience function ──────────────────────────────────────────────────────

def new_id() -> str:
    """
    Generate a new time-sortable ID.

    Returns a ULID by default (26-char, Crockford Base32).
    Use generate_uuidv7() directly if UUID format is required.
    """
    return generate_ulid()
