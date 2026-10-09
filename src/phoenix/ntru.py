"""Textbook NTRUEncrypt on polynomials.

This is the raw trapdoor: key generation, ``e = r*h + m (mod q)`` and its
inverse.  On its own it is malleable and unsafe against chosen-ciphertext
attacks; it is exposed for study and as the building block of
:mod:`phoenix.kem`.  Applications should use :func:`phoenix.seal` instead.
"""

from __future__ import annotations

import numpy as np

from . import poly
from .errors import NotInvertibleError, PhoenixError
from .params import DEFAULT, ParameterSet
from .sampling import Xof, sample_ternary

_MAX_KEYGEN_TRIES = 100


class PublicKey:
    """The public polynomial ``h = p * f_q * g (mod q)``."""

    __slots__ = ("params", "h")

    def __init__(self, params: ParameterSet, h) -> None:
        h = poly.as_poly(h, params.N)
        if h.min() < 0 or h.max() >= params.q:
            raise ValueError("coefficients of h must lie in [0, q)")
        h.flags.writeable = False
        self.params = params
        self.h = h

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PublicKey):
            return NotImplemented
        return self.params == other.params and np.array_equal(self.h, other.h)

    def __hash__(self) -> int:
        return hash((self.params, self.h.tobytes()))

    def __repr__(self) -> str:
        return f"PublicKey({self.params.name}, h=[{self.h[0]}, {self.h[1]}, ...])"


class PrivateKey:
    """The private polynomial ``f`` together with ``f_p = f^-1 (mod p)``.

    ``rejection_secret`` is used only by the KEM, to answer invalid
    ciphertexts with an unpredictable key instead of an error.
    """

    __slots__ = ("params", "f", "fp", "public_key", "rejection_secret")

    def __init__(
        self,
        params: ParameterSet,
        f,
        public_key: PublicKey,
        rejection_secret: bytes,
    ) -> None:
        f = poly.as_poly(f, params.N)
        if public_key.params != params:
            raise ValueError("public key uses a different parameter set")
        if np.abs(f).max() > 1:
            raise ValueError("f must be ternary")
        if len(rejection_secret) != 32:
            raise ValueError("rejection secret must be 32 bytes")
        fp = poly.invert(f, params.p)
        f.flags.writeable = False
        fp.flags.writeable = False
        self.params = params
        self.f = f
        self.fp = fp
        self.public_key = public_key
        self.rejection_secret = bytes(rejection_secret)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PrivateKey):
            return NotImplemented
        return (
            self.public_key == other.public_key
            and np.array_equal(self.f, other.f)
            and self.rejection_secret == other.rejection_secret
        )

    def __hash__(self) -> int:
        return hash(self.public_key)

    def __repr__(self) -> str:
        # Never print key material.
        return f"PrivateKey({self.params.name}, <secret>)"


def generate_keypair(
    params: ParameterSet = DEFAULT, *, seed: bytes | None = None
) -> tuple[PublicKey, PrivateKey]:
    """Generate an NTRU key pair.

    ``seed`` makes generation deterministic; it exists for tests and worked
    examples.  Leave it unset to use operating-system randomness.
    """
    xof = Xof(seed)
    for _ in range(_MAX_KEYGEN_TRIES):
        f = sample_ternary(params.N, params.df + 1, params.df, xof)
        g = sample_ternary(params.N, params.dg, params.dg, xof)
        try:
            return keypair_from(params, f, g, xof.read(32))
        except NotInvertibleError:
            continue
    raise PhoenixError("could not find an invertible f")  # pragma: no cover


def keypair_from(
    params: ParameterSet, f, g, rejection_secret: bytes = bytes(32)
) -> tuple[PublicKey, PrivateKey]:
    """Build a key pair from explicit ``f`` and ``g``.

    Computes ``h = p * f_q * g (mod q)``.  Meant for worked examples and
    tests; raises :class:`NotInvertibleError` if ``f`` has no inverse modulo
    ``p`` or ``q``.
    """
    f = poly.as_poly(f, params.N)
    g = poly.as_poly(g, params.N)
    fq = poly.invert(f, params.q)
    h = poly.convolve(fq, g % params.q, params.q) * params.p % params.q
    public_key = PublicKey(params, h)
    return public_key, PrivateKey(params, f, public_key, rejection_secret)


def sample_blinding(params: ParameterSet, xof: Xof | None = None) -> np.ndarray:
    """Draw a blinding polynomial ``r`` from ``T(dr, dr)``."""
    return sample_ternary(params.N, params.dr, params.dr, xof)


def encrypt(public_key: PublicKey, m, r=None) -> np.ndarray:
    """Return ``e = r*h + m (mod q)`` with coefficients in ``[0, q)``.

    ``m`` must have coefficients in ``[-(p-1)/2, (p-1)/2]`` (ternary for
    ``p = 3``).  ``r`` defaults to a fresh random blinding polynomial; pass
    one explicitly only to reproduce a worked example.
    """
    params = public_key.params
    m = poly.as_poly(m, params.N)
    if np.abs(m).max() > params.p // 2:
        raise ValueError(f"message coefficients must lie in [-{params.p // 2}, {params.p // 2}]")
    r = sample_blinding(params) if r is None else poly.as_poly(r, params.N)
    if np.abs(r).max() > 1:
        raise ValueError("r must be ternary")
    return (poly.convolve(r % params.q, public_key.h, params.q) + m) % params.q


def decrypt(private_key: PrivateKey, e) -> np.ndarray:
    """Recover ``m`` (centered modulo ``p``) from ``e``.

    ``a = f*e (mod q)`` equals ``p*r*g + f*m`` over the integers once lifted
    to ``(-q/2, q/2]``, because the parameter set bounds that polynomial.
    Reducing modulo ``p`` kills the first term and multiplying by ``f_p``
    strips ``f`` from the second.
    """
    params = private_key.params
    e = poly.as_poly(e, params.N)
    a = poly.center(poly.convolve(private_key.f % params.q, e % params.q, params.q), params.q)
    return poly.center(poly.convolve(private_key.fp, a % params.p, params.p), params.p)
