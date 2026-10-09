"""Why the raw NTRU layer is not enough, and what sealing adds."""

import numpy as np

import phoenix
from phoenix import ntru, poly

public_key, private_key = phoenix.generate_keypair(phoenix.TOY, seed=b"demo")

# Textbook NTRU is malleable: adding 1 to a ciphertext coefficient adds 1 to
# the same coefficient of the plaintext, and nothing notices.
m = np.array([0, 1, 0, 0, -1, 0, 0])
e = ntru.encrypt(public_key, m)
forged = e.copy()
forged[0] = (forged[0] + 1) % public_key.params.q
print("textbook NTRU")
print("  sent      :", poly.format_poly(m))
print("  received  :", poly.format_poly(ntru.decrypt(private_key, forged)), " <- silently altered")

# The sealed format authenticates everything, so the same trick is caught.
public_key, private_key = phoenix.generate_keypair()
sealed = bytearray(phoenix.seal(public_key, b"transfer 10 coins"))
sealed[100] ^= 1
print("phoenix.seal")
try:
    phoenix.unseal(private_key, bytes(sealed))
except phoenix.DecryptionError as error:
    print("  received  :", f"DecryptionError: {error}")
