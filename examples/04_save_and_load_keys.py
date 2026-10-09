"""Serialize keys to bytes or to PEM-style text, and load them back."""

import tempfile
from pathlib import Path

import phoenix

public_key, private_key = phoenix.generate_keypair()

public_bytes = phoenix.encode_public_key(public_key)
private_bytes = phoenix.encode_private_key(private_key)
print(f"public key  : {len(public_bytes)} bytes")
print(f"private key : {len(private_bytes)} bytes")

armored = phoenix.armor(public_bytes)
print("\n".join(armored.splitlines()[:3]))
print("...")
print(armored.splitlines()[-1])

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "bob.pub"
    path.write_text(armored)
    loaded = phoenix.decode_public_key(phoenix.dearmor(path.read_text()))

assert loaded == public_key
sealed = phoenix.seal(loaded, b"sent to the reloaded key")
print(phoenix.unseal(private_key, sealed).decode())
