"""Textbook NTRU on the toy parameters, printing every intermediate value.

This is the worked example from docs/algorithm.md.  Coefficient lists run
from the constant term upwards.
"""

import numpy as np

from phoenix import TOY, ntru, poly

show = poly.format_poly
N, p, q = TOY.N, TOY.p, TOY.q

f = np.array([-1, 0, 1, 1, -1, 0, 1])
g = np.array([0, -1, -1, 0, 1, 0, 1])
m = np.array([1, -1, 1, 1, 0, -1, 0])
r = np.array([-1, 1, 0, 0, 0, -1, 1])

print(f"N = {N}, p = {p}, q = {q}\n")
print("Key generation")
print("  f   =", show(f))
print("  g   =", show(g))
fp, fq = poly.invert(f, p), poly.invert(f, q)
print("  f_p =", show(fp))
print("  f_q =", show(fq))
print("  check f*f_p mod p =", show(poly.convolve(f % p, fp, p)))
print("  check f*f_q mod q =", show(poly.convolve(f % q, fq, q)))
public_key, private_key = ntru.keypair_from(TOY, f, g)
print("  h   =", show(public_key.h))

print("\nEncryption")
print("  m   =", show(m))
print("  r   =", show(r))
e = ntru.encrypt(public_key, m, r)
print("  e   =", show(e))

print("\nDecryption")
a = poly.center(poly.convolve(f % q, e, q), q)
print("  a   =", show(a), "  (f*e mod q, centered)")
print("      =", show(p * poly.convolve(r, g) + poly.convolve(f, m)), "  (p*r*g + f*m over Z)")
b = poly.center(a, p)
print("  b   =", show(b), "  (a mod p)")
recovered = poly.center(poly.convolve(fp, b % p, p), p)
print("  m'  =", show(recovered), "  (f_p*b mod p)")
assert np.array_equal(recovered, m)
assert np.array_equal(ntru.decrypt(private_key, e), m)
