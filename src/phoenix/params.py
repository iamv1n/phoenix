"""NTRU parameter sets.

Notation: ``T(a, b)`` is the set of polynomials of degree below ``N`` with
exactly ``a`` coefficients equal to ``+1``, ``b`` equal to ``-1`` and the rest
zero.  Phoenix draws

* the private key ``f`` from ``T(df + 1, df)``,
* the private ``g`` from ``T(dg, dg)``,
* the blinding polynomial ``r`` from ``T(dr, dr)``,
* KEM messages ``m`` from ``T(dm, dm)`` with ``dm = N // 3``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import ParameterError
from .poly import MAX_DEGREE, MAX_MODULUS, is_prime, prime_power


@dataclass(frozen=True)
class ParameterSet:
    """An NTRU parameter set.  Instances are validated on construction."""

    name: str
    N: int
    p: int
    q: int
    df: int
    dg: int
    dr: int

    def __post_init__(self) -> None:
        if not is_prime(self.N) or self.N < 3:
            raise ParameterError("N must be an odd prime")
        if self.N >= MAX_DEGREE:
            raise ParameterError(f"N must be below {MAX_DEGREE}")
        if not is_prime(self.p) or self.p == 2 or self.p > 255:
            raise ParameterError("p must be an odd prime below 256")
        if prime_power(self.q) is None or self.q > MAX_MODULUS:
            raise ParameterError(f"q must be a prime power no larger than {MAX_MODULUS}")
        if math.gcd(self.p, self.q) != 1:
            raise ParameterError("p and q must be coprime")
        if self.df < 1 or 2 * self.df + 1 > self.N:
            raise ParameterError("df must satisfy 1 <= df and 2*df + 1 <= N")
        for label, d in (("dg", self.dg), ("dr", self.dr)):
            if d < 1 or 2 * d > self.N:
                raise ParameterError(f"{label} must satisfy 1 <= {label} and 2*{label} <= N")
        if self.max_coefficient > (self.q - 1) // 2:
            raise ParameterError(
                f"decryption could fail: p*r*g + f*m can reach {self.max_coefficient}, "
                f"which does not fit in (-q/2, q/2] for q = {self.q}"
            )

    @property
    def dm(self) -> int:
        """Number of ``+1`` (and of ``-1``) coefficients in a KEM message."""
        return self.N // 3

    @property
    def max_coefficient(self) -> int:
        """Worst-case absolute coefficient of ``p*r*g + f*m`` over the integers.

        A coefficient of ``r*g`` is a sum of at most ``min(2*dr, 2*dg)`` terms
        of size 1; a coefficient of ``f*m`` is a sum of at most ``2*df + 1``
        terms of size at most ``p // 2``.  Requiring this bound to fit below
        ``q/2`` makes decryption failures impossible rather than merely rare.
        """
        return self.p * 2 * min(self.dr, self.dg) + (2 * self.df + 1) * (self.p // 2)

    @property
    def q_bits(self) -> int:
        """Bits needed to store one coefficient modulo ``q``."""
        return (self.q - 1).bit_length()

    def __str__(self) -> str:
        return (
            f"{self.name} (N={self.N}, p={self.p}, q={self.q}, "
            f"df={self.df}, dg={self.dg}, dr={self.dr})"
        )


# The ring dimensions and moduli match NTRU-HPS 2048-509, 2048-677 and
# 4096-821.  Phoenix is not that scheme and is not interoperable with it; see
# docs/security.md before relying on any security estimate.
PHOENIX509 = ParameterSet("phoenix509", N=509, p=3, q=2048, df=127, dg=127, dr=127)
PHOENIX677 = ParameterSet("phoenix677", N=677, p=3, q=2048, df=127, dg=127, dr=127)
PHOENIX821 = ParameterSet("phoenix821", N=821, p=3, q=4096, df=255, dg=255, dr=255)

# Small enough to follow by hand.  Offers no security whatsoever.
TOY = ParameterSet("toy", N=7, p=3, q=41, df=2, dg=2, dr=2)

DEFAULT = PHOENIX677

PARAMETER_SETS: dict[str, ParameterSet] = {
    ps.name: ps for ps in (PHOENIX509, PHOENIX677, PHOENIX821, TOY)
}


def get(name: str) -> ParameterSet:
    """Look up a built-in parameter set by name (case-insensitive)."""
    try:
        return PARAMETER_SETS[name.lower()]
    except KeyError:
        known = ", ".join(PARAMETER_SETS)
        raise ParameterError(f"unknown parameter set {name!r} (known: {known})") from None
