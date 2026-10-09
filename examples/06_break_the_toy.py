"""Recover a toy private key from the public key by brute force.

With N = 7 there are only 210 candidates for f, so the "hard problem" is a
loop.  Real parameter sets have more candidates than atoms in the universe;
the point is to see exactly what an attacker is searching for.
"""

from itertools import combinations

import numpy as np

import phoenix
from phoenix import TOY, ntru, poly

public_key, private_key = phoenix.generate_keypair(TOY)
N, p, q = TOY.N, TOY.p, TOY.q

tried = 0
recovered = []
for plus in combinations(range(N), TOY.df + 1):
    rest = [i for i in range(N) if i not in plus]
    for minus in combinations(rest, TOY.df):
        tried += 1
        f = np.zeros(N, dtype=np.int64)
        f[list(plus)] = 1
        f[list(minus)] = -1
        # The right f makes f*h = p*g (mod q) with g small and ternary.
        pg = poly.center(poly.convolve(f % q, public_key.h, q), q)
        if np.all(pg % p == 0) and np.abs(pg // p).max() <= 1:
            recovered.append(f)

print(f"candidates tried : {tried}")
print(f"keys that work   : {len(recovered)}")
print(f"real f           : {poly.format_poly(private_key.f)}")
print(f"real f found     : {any(np.array_equal(f, private_key.f) for f in recovered)}")

# Any recovered key decrypts, not just the original one.
m = np.array([1, 0, -1, 0, 1, -1, 0])
e = ntru.encrypt(public_key, m)
try:
    _, stolen = ntru.keypair_from(TOY, recovered[0], np.zeros(N, dtype=np.int64))
    print(f"decrypts with it : {np.array_equal(ntru.decrypt(stolen, e), m)}")
except phoenix.NotInvertibleError:
    print("first candidate is not invertible mod p; try another")
