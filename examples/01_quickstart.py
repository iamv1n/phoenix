"""Encrypt a message to a public key and decrypt it again."""

import phoenix

public_key, private_key = phoenix.generate_keypair()

sealed = phoenix.seal(public_key, b"The phoenix rises at dawn.")
print(f"parameter set : {public_key.params.name}")
print(f"sealed size   : {len(sealed)} bytes")
print(f"decrypted     : {phoenix.unseal(private_key, sealed).decode()}")

# Associated data is authenticated but not encrypted: both sides must agree.
sealed = phoenix.seal(public_key, b"pay 100 to Bob", associated_data=b"invoice-17")
try:
    phoenix.unseal(private_key, sealed, associated_data=b"invoice-18")
except phoenix.DecryptionError as error:
    print(f"wrong context : {error}")
