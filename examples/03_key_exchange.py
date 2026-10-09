"""Agree on a shared secret with the KEM, the way a handshake would."""

import phoenix

# Bob publishes a public key.
bob_public, bob_private = phoenix.generate_keypair(phoenix.PHOENIX509)

# Alice encapsulates: she gets a secret plus a ciphertext to send to Bob.
ciphertext, alice_secret = phoenix.encapsulate(bob_public)

# Bob decapsulates the ciphertext and arrives at the same secret.
bob_secret = phoenix.decapsulate(bob_private, ciphertext)

print(f"ciphertext on the wire : {len(ciphertext)} bytes")
print(f"alice's secret         : {alice_secret.hex()}")
print(f"bob's secret           : {bob_secret.hex()}")
assert alice_secret == bob_secret

# An attacker who flips a bit does not get an error to learn from; Bob just
# derives an unrelated key and the conversation fails to authenticate later.
tampered = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
print(f"after tampering        : {phoenix.decapsulate(bob_private, tampered).hex()}")
