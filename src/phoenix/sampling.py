"""Random sampling of ternary polynomials.

All randomness flows through :class:`Xof`, a SHAKE-256 based byte stream.
Seeding it from the operating system gives fresh randomness; seeding it from
a hash gives the deterministic sampling the KEM needs for re-encryption.
"""

from __future__ import annotations

import hashlib
import secrets

import numpy as np

_BLOCK = 1024


class Xof:
    """Deterministic byte stream: SHAKE-256 over ``seed`` in counter mode."""

    def __init__(self, seed: bytes | None = None) -> None:
        self._seed = secrets.token_bytes(32) if seed is None else bytes(seed)
        self._counter = 0
        self._buffer = b""

    def read(self, n: int) -> bytes:
        while len(self._buffer) < n:
            block = hashlib.shake_256(self._counter.to_bytes(8, "big") + self._seed)
            self._buffer += block.digest(_BLOCK)
            self._counter += 1
        out, self._buffer = self._buffer[:n], self._buffer[n:]
        return out

    def randbelow(self, n: int) -> int:
        """Uniform integer in ``[0, n)`` for ``0 < n <= 2**32``, by rejection."""
        limit = (1 << 32) - ((1 << 32) % n)
        while True:
            value = int.from_bytes(self.read(4), "big")
            if value < limit:
                return value % n


def sample_ternary(N: int, ones: int, minus_ones: int, xof: Xof | None = None) -> np.ndarray:
    """Uniform element of ``T(ones, minus_ones)``: a Fisher-Yates shuffle."""
    if ones < 0 or minus_ones < 0 or ones + minus_ones > N:
        raise ValueError("weights do not fit in a polynomial of this length")
    xof = Xof() if xof is None else xof
    coeffs = [1] * ones + [-1] * minus_ones + [0] * (N - ones - minus_ones)
    for i in range(N - 1, 0, -1):
        j = xof.randbelow(i + 1)
        coeffs[i], coeffs[j] = coeffs[j], coeffs[i]
    return np.array(coeffs, dtype=np.int64)
