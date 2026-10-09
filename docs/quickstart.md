# Quickstart

## Install

Phoenix needs Python 3.10 or newer.

```console
$ git clone https://github.com/iamv1n/phoenix.git
$ cd phoenix
$ python -m venv .venv && source .venv/bin/activate
$ pip install -e .
```

This installs the `phoenix` Python package and the `phoenix` command. Its two
dependencies are NumPy (polynomial arithmetic) and `cryptography`
(ChaCha20-Poly1305).

## Encrypt and decrypt

```python
import phoenix

public_key, private_key = phoenix.generate_keypair()

sealed = phoenix.seal(public_key, b"The phoenix rises at dawn.")
print(phoenix.unseal(private_key, sealed))
# b'The phoenix rises at dawn.'
```

`seal` takes and returns `bytes`. Encode text yourself (`"…".encode()`), so
there is never any doubt about which encoding was used.

Anyone with the public key can seal; only the private key can unseal. If the
message was modified in transit, or you use the wrong key, `unseal` raises
`phoenix.DecryptionError` instead of returning garbage.

## Bind a message to its context

Associated data is authenticated but not encrypted and not stored in the
message. Both sides must supply the same value:

```python
sealed = phoenix.seal(public_key, b"pay 100 to Bob", associated_data=b"invoice-17")

phoenix.unseal(private_key, sealed, associated_data=b"invoice-17")  # ok
phoenix.unseal(private_key, sealed, associated_data=b"invoice-18")  # DecryptionError
```

Use it to stop a valid message from being replayed somewhere it does not
belong.

## Save and load keys

```python
public_bytes = phoenix.encode_public_key(public_key)  # 950 bytes
private_bytes = phoenix.encode_private_key(private_key)  # 1118 bytes

public_key = phoenix.decode_public_key(public_bytes)
private_key = phoenix.decode_private_key(private_bytes)
```

For text-friendly storage, wrap any encoded object in PEM-style armor:

```python
text = phoenix.armor(public_bytes)
# -----BEGIN PHOENIX PUBLIC KEY-----
# UEhOWAEBAqUDAAAIAAB/AH8Af01I7WVM0ZSM1kKfsdSolh4ljmMkdD+tXMZ/5CLzri8Dq+sWMGTt
# ...
# -----END PHOENIX PUBLIC KEY-----
public_key = phoenix.decode_public_key(phoenix.dearmor(text))
```

## Agree on a shared secret

If you want a key for your own protocol rather than an encrypted message, use
the KEM directly:

```python
ciphertext, alice_secret = phoenix.encapsulate(bob_public_key)  # Alice
bob_secret = phoenix.decapsulate(bob_private_key, ciphertext)  # Bob
assert alice_secret == bob_secret  # 32 bytes
```

## Choose a parameter set

```python
public_key, private_key = phoenix.generate_keypair(phoenix.PHOENIX821)
```

| Name | N | q | Public key | Sealed overhead |
| --- | ---: | ---: | ---: | ---: |
| `PHOENIX509` | 509 | 2048 | 719 B | 735 B |
| `PHOENIX677` (default) | 677 | 2048 | 950 B | 966 B |
| `PHOENIX821` | 821 | 4096 | 1251 B | 1267 B |
| `TOY` | 7 | 41 | 25 B | 41 B |

`TOY` is for studying the algorithm by hand and provides no security. A
sealed message records its parameter set, so the receiver never has to be
told. See [Security](security.md) for what the sizes mean.

## From the shell

```console
$ phoenix keygen -o alice
public key:  alice.pub
private key: alice.key  (keep this secret)
$ echo "meet me at the old bridge" > note.txt
$ phoenix encrypt -k alice.pub -i note.txt -o note.phx
$ phoenix decrypt -k alice.key -i note.phx
meet me at the old bridge
```

More in [Command line](cli.md). To experiment without writing anything, run
`phoenix playground` ([details](playground.md)).

## Where next

- [The NTRU algorithm](algorithm.md) explains what just happened.
- [API reference](api.md) lists everything public.
- [`examples/`](../examples) has six short runnable scripts.
