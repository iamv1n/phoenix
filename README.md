# Phoenix

An educational implementation of **NTRU**, a lattice-based public-key
cryptosystem designed to resist attacks by quantum computers.

Phoenix is small enough to read in an afternoon and complete enough to use
end to end: key generation, a key encapsulation mechanism, authenticated
hybrid encryption, a command-line tool, and a local web playground.

> [!WARNING]
> **Phoenix is a learning project.** It has not been audited, it is not
> constant time, and it does not implement any standard. Do not use it to
> protect real secrets. See [Security](docs/security.md).

```python
import phoenix

public_key, private_key = phoenix.generate_keypair()

sealed = phoenix.seal(public_key, b"The phoenix rises at dawn.")
phoenix.unseal(private_key, sealed)
# b'The phoenix rises at dawn.'
```

## Contents

- [Install](#install)
- [Usage](#usage)
- [Playground](#playground)
- [How it works](#how-it-works)
- [Documentation](#documentation)
- [Blog](#blog)
- [Development](#development)
- [License](#license)

## Install

Requires Python 3.10 or newer.

```console
$ git clone https://github.com/iamv1n/phoenix.git
$ cd phoenix
$ python -m venv .venv && source .venv/bin/activate
$ pip install -e .
```

## Usage

### Python

```python
import phoenix

# Encrypt bytes to a public key
public_key, private_key = phoenix.generate_keypair()
sealed = phoenix.seal(public_key, b"hello", associated_data=b"msg-1")
plaintext = phoenix.unseal(private_key, sealed, associated_data=b"msg-1")

# Or agree on a 32-byte shared secret
ciphertext, alice_secret = phoenix.encapsulate(public_key)
bob_secret = phoenix.decapsulate(private_key, ciphertext)
assert alice_secret == bob_secret

# Save and load keys
data = phoenix.encode_public_key(public_key)
public_key = phoenix.decode_public_key(data)
```

A modified message, the wrong key, or mismatched associated data raises
`phoenix.DecryptionError`; nothing is ever returned unauthenticated.

### Command line

```console
$ phoenix keygen -o alice
public key:  alice.pub
private key: alice.key  (keep this secret)

$ echo "meet me at the old bridge" > note.txt
$ phoenix encrypt -k alice.pub -i note.txt -o note.phx
$ phoenix decrypt -k alice.key -i note.phx
meet me at the old bridge
```

### Examples

Six short scripts in [`examples/`](examples) cover the API from first use to
breaking a toy key:

| Script | Shows |
| --- | --- |
| [`01_quickstart.py`](examples/01_quickstart.py) | Sealing and unsealing |
| [`02_textbook_ntru.py`](examples/02_textbook_ntru.py) | Every intermediate value of the algorithm, N = 7 |
| [`03_key_exchange.py`](examples/03_key_exchange.py) | The KEM, and what tampering does |
| [`04_save_and_load_keys.py`](examples/04_save_and_load_keys.py) | Binary and PEM-style serialization |
| [`05_tampering.py`](examples/05_tampering.py) | Why raw NTRU is not enough |
| [`06_break_the_toy.py`](examples/06_break_the_toy.py) | Recovering a toy private key by brute force |

## Playground

```console
$ phoenix playground
Phoenix playground running at http://127.0.0.1:8765/  (Ctrl+C to stop)
```

A local web page, driven by the real library, where you can:

- generate keys, seal and unseal messages, and flip bits to watch
  authentication fail;
- step through textbook NTRU on seven coefficients with every intermediate
  polynomial shown;
- run round-trip tests and timing benchmarks for each parameter set.

It runs entirely on your machine and loads nothing from the network.
See [docs/playground.md](docs/playground.md).

## How it works

NTRU works with polynomials whose exponents wrap around at $N$ and whose
coefficients wrap around at a modulus.

- The **private key** is a polynomial $f$ with tiny coefficients ($-1$, $0$
  or $1$).
- The **public key** is $h = p \cdot f^{-1} \star g \bmod q$ for another tiny
  polynomial $g$. It looks random.
- **Encryption** hides a message behind a random multiple of the public key:
  $e = r \star h + m \bmod q$.
- **Decryption** multiplies by $f$, which collapses the ciphertext into
  something small enough that reducing it modulo $p$ reveals $m$.

Recovering $f$ from $h$ means finding an unusually short vector in a lattice
of dimension $2N$, a problem no known classical or quantum algorithm solves
efficiently.

On top of that trapdoor, Phoenix builds:

| Layer | Module | Adds |
| --- | --- | --- |
| Textbook NTRU | `phoenix.ntru` | The raw trapdoor, for study |
| KEM | `phoenix.kem` | Chosen-ciphertext protection via re-encryption and implicit rejection |
| Sealing | `phoenix.seal` | Arbitrary bytes, authenticated with ChaCha20-Poly1305 |

Parameter sets are validated so that decryption failures are impossible,
not just unlikely.

| Parameter set | N | q | Public key | Ciphertext | Keygen | Encapsulate | Decapsulate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `PHOENIX509` | 509 | 2048 | 719 B | 700 B | 6 ms | 0.4 ms | 0.4 ms |
| `PHOENIX677` (default) | 677 | 2048 | 950 B | 931 B | 10 ms | 0.5 ms | 0.6 ms |
| `PHOENIX821` | 821 | 4096 | 1251 B | 1232 B | 13 ms | 0.7 ms | 0.8 ms |

Timings are from an Apple Silicon laptop with Python 3.14 and are only
indicative; run the playground's benchmark tab for your own.

## Documentation

| | |
| --- | --- |
| [Quickstart](docs/quickstart.md) | Install and encrypt in five minutes |
| [Playground](docs/playground.md) | The local web UI |
| [Command line](docs/cli.md) | Every `phoenix` subcommand |
| [API reference](docs/api.md) | Every public function |
| [Mathematical background](docs/math.md) | Rings, quotients, inverses, lattices |
| [The NTRU algorithm](docs/algorithm.md) | Key generation, encryption, decryption, with a worked example |
| [KEM and sealing](docs/kem-and-sealing.md) | From trapdoor to usable encryption |
| [Security](docs/security.md) | What is and is not protected |
| [File formats](docs/formats.md) | Byte-level layout of keys and messages |

## Blog

1. [Why your encryption has an expiry date](blog/01-why-post-quantum.md)
2. [NTRU by hand](blog/02-ntru-by-hand.md)
3. [From a maths trick to something you can use](blog/03-from-textbook-to-usable.md)
4. [Rebuilding Phoenix](blog/04-rebuilding-phoenix.md)

## Development

```console
$ pip install -e ".[dev]"
$ pytest            # 216 tests, a few seconds
$ ruff check .
$ ruff format .
$ python tools/check_math.py    # maths in docs/blog renders everywhere
```

```
src/phoenix/
    poly.py         arithmetic in Z[x]/(x^N - 1)
    params.py       validated parameter sets
    sampling.py     randomness and ternary sampling
    ntru.py         textbook NTRU
    kem.py          key encapsulation
    sealing.py      hybrid encryption
    encoding.py     serialization and armor
    cli.py          the phoenix command
    playground/     local web UI
tests/              pytest suite
examples/           runnable scripts
docs/               reference documentation
blog/               long-form articles
tools/              documentation checks
```

Contributions are welcome: fork, branch, make your change with a test, and
open a pull request. Attacks, however small, are the most valuable
contribution of all.

## Support

Questions and bug reports: [open an issue](https://github.com/iamv1n/phoenix/issues/new)
or [email the author](mailto:mail@vineet.site).

## License

[GNU General Public License v3.0](LICENSE).
