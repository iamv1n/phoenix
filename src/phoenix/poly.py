"""Arithmetic in the truncated polynomial ring Z[x]/(x^N - 1).

A polynomial is a NumPy ``int64`` array of length ``N`` in *little-endian*
order: ``a[i]`` is the coefficient of ``x^i``.  Reduction modulo ``x^N - 1``
turns multiplication into a cyclic convolution, written ``*`` in the docs.

Nothing in this module is constant time.
"""

from __future__ import annotations

import numpy as np

from .errors import NotInvertibleError, ParameterError

# Products are accumulated in int64; with N < 2**12 and coefficients below
# 2**20 the largest intermediate value is under 2**52.
MAX_MODULUS = 1 << 20
MAX_DEGREE = 1 << 12


def as_poly(coeffs, N: int) -> np.ndarray:
    """Return ``coeffs`` as a length-``N`` int64 array (zero padded)."""
    a = np.asarray(coeffs, dtype=np.int64)
    if a.ndim != 1 or len(a) > N:
        raise ValueError(f"expected at most {N} coefficients, got shape {a.shape}")
    if len(a) < N:
        a = np.concatenate([a, np.zeros(N - len(a), dtype=np.int64)])
    return a


def convolve(a: np.ndarray, b: np.ndarray, modulus: int | None = None) -> np.ndarray:
    """Multiply ``a`` and ``b`` in Z[x]/(x^N - 1), optionally reducing mod ``modulus``."""
    N = len(a)
    if len(b) != N:
        raise ValueError("operands must have the same length")
    full = np.convolve(a, b)
    out = full[:N].copy()
    out[: N - 1] += full[N:]
    if modulus is not None:
        out %= modulus
    return out


def center(a: np.ndarray, modulus: int) -> np.ndarray:
    """Lift ``a`` mod ``modulus`` to representatives in ``(-modulus/2, modulus/2]``."""
    half = (modulus - 1) // 2
    return (a + half) % modulus - half


def is_prime(n: int) -> bool:
    """Trial-division primality test, adequate for the small moduli used here."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def prime_power(n: int) -> tuple[int, int] | None:
    """Return ``(p, k)`` with ``n == p**k`` and ``p`` prime, or ``None``."""
    if n < 2:
        return None
    p = 2
    while p * p <= n:
        if n % p == 0:
            k = 0
            while n % p == 0:
                n //= p
                k += 1
            return (p, k) if n == 1 else None
        p += 1
    return (n, 1)


def _trim(a: np.ndarray) -> np.ndarray:
    """Drop high-order zero coefficients (the zero polynomial becomes ``[]``)."""
    nz = np.flatnonzero(a)
    return a[: nz[-1] + 1] if len(nz) else a[:0]


def _divmod(a: np.ndarray, b: np.ndarray, p: int) -> tuple[np.ndarray, np.ndarray]:
    """Polynomial long division over GF(p); ``a`` and ``b`` trimmed, ``b != 0``."""
    db = len(b) - 1
    if len(a) <= db:
        return a[:0], a
    rem = a.copy()
    quo = np.zeros(len(a) - db, dtype=np.int64)
    lead_inv = pow(int(b[-1]), -1, p)
    for i in range(len(a) - db - 1, -1, -1):
        c = int(rem[i + db]) * lead_inv % p
        if c:
            quo[i] = c
            rem[i : i + db + 1] = (rem[i : i + db + 1] - c * b) % p
    return quo, _trim(rem[:db])


def _invert_mod_prime(a: np.ndarray, p: int) -> np.ndarray:
    """Inverse of ``a`` in GF(p)[x]/(x^N - 1) by the extended Euclidean algorithm.

    We run Euclid on ``(x^N - 1, a)`` and track only the Bezout coefficient of
    ``a``: when the gcd is a non-zero constant ``c`` we have
    ``t * a = c  (mod x^N - 1)``, so the inverse is ``t / c``.
    """
    N = len(a)
    modulus_poly = np.zeros(N + 1, dtype=np.int64)
    modulus_poly[0] = p - 1
    modulus_poly[N] = 1

    r0, r1 = modulus_poly, _trim(a % p)
    t0, t1 = r0[:0], np.ones(1, dtype=np.int64)
    while len(r1):
        quo, rem = _divmod(r0, r1, p)
        prod = np.convolve(quo, t1) if len(quo) and len(t1) else t1[:0]
        t2 = np.zeros(max(len(t0), len(prod)), dtype=np.int64)
        t2[: len(t0)] = t0
        t2[: len(prod)] -= prod
        r0, r1 = r1, rem
        t0, t1 = t1, _trim(t2 % p)
    if len(r0) != 1:
        raise NotInvertibleError(f"polynomial is not invertible modulo {p}")
    inv = as_poly(t0, N) * pow(int(r0[0]), -1, p) % p
    return inv


def invert(a: np.ndarray, modulus: int) -> np.ndarray:
    """Inverse of ``a`` in (Z/modulus)[x]/(x^N - 1).

    ``modulus`` must be a prime power.  The inverse is found modulo the prime
    and then lifted by Newton iteration ``b <- b * (2 - a * b)``, which doubles
    the exponent of the prime each round.

    Raises :class:`NotInvertibleError` if no inverse exists.
    """
    N = len(a)
    if N >= MAX_DEGREE or modulus > MAX_MODULUS:
        raise ParameterError("ring is too large for int64 arithmetic")
    pk = prime_power(modulus)
    if pk is None:
        raise ParameterError(f"modulus {modulus} is not a prime power")
    p, k = pk

    b = _invert_mod_prime(a, p)
    current = p
    while current < modulus:
        current = min(current * current, modulus)
        t = -convolve(a % current, b, current)
        t[0] += 2
        b = convolve(b, t % current, current)

    one = np.zeros(N, dtype=np.int64)
    one[0] = 1
    if not np.array_equal(convolve(a % modulus, b, modulus), one):  # pragma: no cover
        raise NotInvertibleError("inverse failed verification")
    return b


def format_poly(a, variable: str = "x") -> str:
    """Render a coefficient array as a human-readable polynomial."""
    terms = []
    for i in range(len(a) - 1, -1, -1):
        c = int(a[i])
        if c == 0:
            continue
        sign = "-" if c < 0 else "+"
        mag = abs(c)
        power = "" if i == 0 else variable if i == 1 else f"{variable}^{i}"
        body = str(mag) if not power else power if mag == 1 else f"{mag}{power}"
        terms.append((sign, body))
    if not terms:
        return "0"
    first_sign, first = terms[0]
    out = ("-" if first_sign == "-" else "") + first
    return out + "".join(f" {sign} {body}" for sign, body in terms[1:])
