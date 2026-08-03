"""Minimal authenticated encryption built entirely on Python's stdlib.

Implements the ChaCha20-Poly1305 AEAD construction from RFC 8439 so the
vault has real confidentiality and integrity without third-party
dependencies. Passwords are stretched with PBKDF2-HMAC-SHA256 before use.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct

MAGIC = b"PASSGEN1"
NONCE_LEN = 12
SALT_LEN = 16
TAG_LEN = 16
PBKDF2_ITERATIONS = 200_000


def _rotl32(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF


def quarter_round(state: list[int], a: int, b: int, c: int, d: int) -> None:
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 16)
    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 12)
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 8)
    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 7)


def _chacha_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    """Return one 64-byte ChaCha20 keystream block (RFC 8439 section 2.3)."""
    constants = b"expand 32-byte k"
    state = list(struct.unpack("<4I", constants))
    state += list(struct.unpack("<8I", key))
    state.append(counter & 0xFFFFFFFF)
    state += list(struct.unpack("<3I", nonce))
    working = list(state)
    for _ in range(10):
        quarter_round(working, 0, 4, 8, 12)
        quarter_round(working, 1, 5, 9, 13)
        quarter_round(working, 2, 6, 10, 14)
        quarter_round(working, 3, 7, 11, 15)
        quarter_round(working, 0, 5, 10, 15)
        quarter_round(working, 1, 6, 11, 12)
        quarter_round(working, 2, 7, 8, 13)
        quarter_round(working, 3, 4, 9, 14)
    output = []
    for left, right in zip(state, working):
        output.append(((left + right) & 0xFFFFFFFF).to_bytes(4, "little"))
    return b"".join(output)


def _chacha_stream(key: bytes, nonce: bytes, length: int, start_counter: int) -> bytes:
    out = bytearray()
    counter = start_counter
    while len(out) < length:
        out += _chacha_block(key, counter, nonce)
        counter += 1
    return bytes(out[:length])


def _poly1305(key: bytes, message: bytes) -> bytes:
    """Poly1305 one-time authenticator (RFC 8439 section 2.5)."""
    r = int.from_bytes(key[:16], "little") & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    s = int.from_bytes(key[16:32], "little")
    accumulator = 0
    p = (1 << 130) - 5

    for i in range(0, len(message), 16):
        block = message[i : i + 16]
        padded = block + b"\x01" + b"\x00" * (16 - len(block))
        n = int.from_bytes(padded, "little")
        accumulator = (accumulator + n) * r % p

    accumulator = (accumulator + s) & ((1 << 128) - 1)
    return accumulator.to_bytes(16, "little")


def _pad16(data: bytes) -> bytes:
    rem = len(data) % 16
    return b"" if rem == 0 else b"\x00" * (16 - rem)


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32)


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt ``data`` under ``password``.

    Returns ``MAGIC | salt | nonce | ciphertext | tag``.
    """
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = _derive_key(password, salt)

    poly_key = _chacha_stream(key, nonce, 32, start_counter=0)
    ciphertext = bytes(c ^ s for c, s in zip(data, _chacha_stream(key, nonce, len(data), 1)))

    mac_data = (
        MAGIC
        + _pad16(MAGIC)
        + ciphertext
        + _pad16(ciphertext)
        + struct.pack("<Q", len(MAGIC))
        + struct.pack("<Q", len(ciphertext))
    )
    tag = _poly1305(poly_key, mac_data)
    return MAGIC + salt + nonce + ciphertext + tag


def decrypt(blob: bytes, password: str) -> bytes:
    """Decrypt a blob produced by :func:`encrypt`, raising on tampering."""
    if not blob.startswith(MAGIC):
        raise ValueError("unknown or corrupted blob")
    salt = blob[len(MAGIC) : len(MAGIC) + SALT_LEN]
    nonce = blob[
        len(MAGIC) + SALT_LEN : len(MAGIC) + SALT_LEN + NONCE_LEN
    ]
    head = len(MAGIC) + SALT_LEN + NONCE_LEN
    ciphertext = blob[head:-TAG_LEN]
    tag = blob[-TAG_LEN:]

    key = _derive_key(password, salt)
    poly_key = _chacha_stream(key, nonce, 32, start_counter=0)
    mac_data = (
        MAGIC
        + _pad16(MAGIC)
        + ciphertext
        + _pad16(ciphertext)
        + struct.pack("<Q", len(MAGIC))
        + struct.pack("<Q", len(ciphertext))
    )
    expected = _poly1305(poly_key, mac_data)
    if not hmac.compare_digest(tag, expected):
        raise ValueError("authentication failed")
    return bytes(
        c ^ b
        for c, b in zip(ciphertext, _chacha_stream(key, nonce, len(ciphertext), 1))
    )
