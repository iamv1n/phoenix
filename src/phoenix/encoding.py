"""Binary serialization of keys and ciphertexts.

Every self-describing object starts with a 19-byte header::

    magic "PHNX" | version u8 | kind u8 | N u16 | p u8 | q u32 | df u16 | dg u16 | dr u16

(all integers big-endian) so that a key or message carries its own parameter
set.  docs/formats.md describes the payloads.
"""

from __future__ import annotations

import base64
import struct

import numpy as np

from .errors import FormatError, ParameterError
from .ntru import PrivateKey, PublicKey
from .params import PARAMETER_SETS, ParameterSet

MAGIC = b"PHNX"
VERSION = 1

KIND_PUBLIC_KEY = 1
KIND_PRIVATE_KEY = 2
KIND_SEALED = 3

_KIND_LABELS = {
    KIND_PUBLIC_KEY: "PHOENIX PUBLIC KEY",
    KIND_PRIVATE_KEY: "PHOENIX PRIVATE KEY",
    KIND_SEALED: "PHOENIX MESSAGE",
}

_HEADER = struct.Struct(">4sBBHBIHHH")
HEADER_SIZE = _HEADER.size

_TRITS_PER_BYTE = 5
_TRIT_WEIGHTS = np.array([1, 3, 9, 27, 81], dtype=np.int64)


# -- coefficient packing -----------------------------------------------------


def packed_size(N: int, bits: int) -> int:
    return (N * bits + 7) // 8


def pack_coefficients(a: np.ndarray, bits: int) -> bytes:
    """Pack non-negative coefficients, ``bits`` bits each, little-endian."""
    shifts = np.arange(bits, dtype=np.int64)
    bit_matrix = ((a[:, None] >> shifts) & 1).astype(np.uint8)
    return np.packbits(bit_matrix.ravel(), bitorder="little").tobytes()


def unpack_coefficients(data: bytes, N: int, bits: int, modulus: int) -> np.ndarray:
    """Inverse of :func:`pack_coefficients`; rejects non-canonical encodings."""
    if len(data) != packed_size(N, bits):
        raise FormatError("wrong length for packed polynomial")
    raw = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")
    if raw[N * bits :].any():
        raise FormatError("non-zero padding bits")
    weights = np.int64(1) << np.arange(bits, dtype=np.int64)
    a = raw[: N * bits].reshape(N, bits).astype(np.int64) @ weights
    if a.max() >= modulus:
        raise FormatError("coefficient out of range")
    return a


def trits_size(N: int) -> int:
    return (N + _TRITS_PER_BYTE - 1) // _TRITS_PER_BYTE


def pack_trits(a: np.ndarray) -> bytes:
    """Pack a ternary polynomial, five coefficients per byte (base 3)."""
    digits = np.zeros(trits_size(len(a)) * _TRITS_PER_BYTE, dtype=np.int64)
    digits[: len(a)] = a % 3
    return (digits.reshape(-1, _TRITS_PER_BYTE) @ _TRIT_WEIGHTS).astype(np.uint8).tobytes()


def unpack_trits(data: bytes, N: int) -> np.ndarray:
    """Inverse of :func:`pack_trits`, returning coefficients in ``{-1, 0, 1}``."""
    if len(data) != trits_size(N):
        raise FormatError("wrong length for packed ternary polynomial")
    values = np.frombuffer(data, dtype=np.uint8).astype(np.int64)
    if values.max() >= 3**_TRITS_PER_BYTE:
        raise FormatError("invalid ternary byte")
    digits = (values[:, None] // _TRIT_WEIGHTS) % 3
    digits = digits.ravel()
    if digits[N:].any():
        raise FormatError("non-zero padding trits")
    a = digits[:N]
    return np.where(a == 2, -1, a)


# -- header ------------------------------------------------------------------


def encode_header(kind: int, params: ParameterSet) -> bytes:
    return _HEADER.pack(
        MAGIC, VERSION, kind, params.N, params.p, params.q, params.df, params.dg, params.dr
    )


def decode_header(data: bytes, expected_kind: int | None = None) -> tuple[int, ParameterSet]:
    """Parse and validate a header, returning ``(kind, params)``."""
    if len(data) < HEADER_SIZE:
        raise FormatError("data is too short to be a Phoenix object")
    magic, version, kind, N, p, q, df, dg, dr = _HEADER.unpack_from(data)
    if magic != MAGIC:
        raise FormatError("not a Phoenix object (bad magic)")
    if version != VERSION:
        raise FormatError(f"unsupported format version {version}")
    if kind not in _KIND_LABELS:
        raise FormatError(f"unknown object kind {kind}")
    if expected_kind is not None and kind != expected_kind:
        raise FormatError(
            f"expected a {_KIND_LABELS[expected_kind].lower()}, got a {_KIND_LABELS[kind].lower()}"
        )
    try:
        params = ParameterSet("custom", N, p, q, df, dg, dr)
    except ParameterError as exc:
        raise FormatError(f"invalid parameters in header: {exc}") from None
    for known in PARAMETER_SETS.values():
        if (known.N, known.p, known.q, known.df, known.dg, known.dr) == (N, p, q, df, dg, dr):
            params = known
    return kind, params


# -- keys --------------------------------------------------------------------


def _pack_h(public_key: PublicKey) -> bytes:
    return pack_coefficients(public_key.h, public_key.params.q_bits)


def encode_public_key(public_key: PublicKey) -> bytes:
    return encode_header(KIND_PUBLIC_KEY, public_key.params) + _pack_h(public_key)


def decode_public_key(data: bytes) -> PublicKey:
    _, params = decode_header(data, KIND_PUBLIC_KEY)
    h = unpack_coefficients(data[HEADER_SIZE:], params.N, params.q_bits, params.q)
    return PublicKey(params, h)


def encode_private_key(private_key: PrivateKey) -> bytes:
    return (
        encode_header(KIND_PRIVATE_KEY, private_key.params)
        + pack_trits(private_key.f)
        + _pack_h(private_key.public_key)
        + private_key.rejection_secret
    )


def decode_private_key(data: bytes) -> PrivateKey:
    _, params = decode_header(data, KIND_PRIVATE_KEY)
    f_end = HEADER_SIZE + trits_size(params.N)
    h_end = f_end + packed_size(params.N, params.q_bits)
    if len(data) != h_end + 32:
        raise FormatError("wrong length for private key")
    f = unpack_trits(data[HEADER_SIZE:f_end], params.N)
    h = unpack_coefficients(data[f_end:h_end], params.N, params.q_bits, params.q)
    try:
        return PrivateKey(params, f, PublicKey(params, h), data[h_end:])
    except ArithmeticError:
        raise FormatError("private key is not invertible") from None


# -- ASCII armor -------------------------------------------------------------


def armor(data: bytes) -> str:
    """Wrap a serialized object in a PEM-style text envelope."""
    kind, _ = decode_header(data)
    label = _KIND_LABELS[kind]
    body = base64.encodebytes(data).decode("ascii")
    return f"-----BEGIN {label}-----\n{body}-----END {label}-----\n"


def dearmor(text: str | bytes) -> bytes:
    """Inverse of :func:`armor`."""
    if isinstance(text, bytes):
        try:
            text = text.decode("ascii")
        except UnicodeDecodeError:
            raise FormatError("armored data is not ASCII") from None
    lines = [line.strip() for line in text.strip().splitlines()]
    if len(lines) < 3 or not lines[0].startswith("-----BEGIN PHOENIX "):
        raise FormatError("missing armor header")
    if lines[-1] != lines[0].replace("BEGIN", "END", 1):
        raise FormatError("armor footer does not match header")
    try:
        data = base64.b64decode("".join(lines[1:-1]), validate=True)
    except ValueError:
        raise FormatError("invalid base64 in armored data") from None
    kind, _ = decode_header(data)
    if f"-----BEGIN {_KIND_LABELS[kind]}-----" != lines[0]:
        raise FormatError("armor label does not match contents")
    return data


def load(data: str | bytes) -> bytes:
    """Return raw bytes from either binary or armored input."""
    if isinstance(data, bytes) and data.startswith(MAGIC):
        return data
    return dearmor(data)
