# Security

## The short version

**Do not use Phoenix to protect real secrets.** It is a learning project. It
has had no independent review, it is not constant time, and it is not an
implementation of any standard.

If you need post-quantum encryption in production, use a reviewed
implementation of a standardised scheme, such as ML-KEM (FIPS 203) through
[liboqs](https://openquantumsafe.org/) or your platform's cryptography
library.

What Phoenix *is* good for: reading, running, modifying and breaking a
complete, working lattice cryptosystem that is small enough to understand.

## What the design does provide

Assuming the underlying problem is hard and the implementation is correct:

| Property | How |
| --- | --- |
| Confidentiality against a passive attacker | NTRU one-wayness |
| Integrity of sealed messages | ChaCha20-Poly1305 tag over header, KEM ciphertext, body and associated data |
| Resistance to chosen-ciphertext probing | Re-encryption check with implicit rejection in the KEM |
| No decryption failures, ever | Parameter sets are rejected unless the worst case fits below $q/2$ |
| Fresh randomness per message | 256 bits from the OS, expanded with SHAKE-256 |

## What it does not provide

**Side-channel resistance.** Timing depends on secret data throughout:
NumPy's convolution, rejection sampling, the polynomial inversion and Python
integer arithmetic are all variable time. An attacker who can measure how
long your decapsulations take should be assumed able to recover the key.

**Memory hygiene.** Secrets live in ordinary Python objects. They are not
zeroed after use and may be copied by the garbage collector or written to
swap.

**Sender authentication, forward secrecy, length hiding.** See
[what sealing does not do](kem-and-sealing.md#what-sealing-does-not-do).

**A proof.** The KEM follows the Fujisaki–Okamoto recipe, but no one has
proved or reviewed this particular instantiation.

**Interoperability.** Phoenix is not NTRU-HPS, NTRU-HRSS, NTRU Prime or
IEEE 1363.1 NTRUEncrypt and cannot exchange keys or ciphertexts with them.

## Parameter sets

| Name | N | q | Weights (df, dg, dr) | Same ring as |
| --- | ---: | ---: | --- | --- |
| `phoenix509` | 509 | 2048 | 127 | NTRU-HPS 2048-509 |
| `phoenix677` | 677 | 2048 | 127 | NTRU-HPS 2048-677 |
| `phoenix821` | 821 | 4096 | 255 | NTRU-HPS 4096-821 |
| `toy` | 7 | 41 | 2 | nothing; insecure by design |

The ring dimension and modulus of the three real sets were chosen to match
the NTRU-HPS parameter sets from the NIST post-quantum competition, whose
submitters targeted security categories 1, 3 and 5.

**Those estimates do not transfer to Phoenix.** Phoenix differs from NTRU-HPS
in ways that affect security analysis:

- It works modulo $x^N - 1$ throughout, where NTRU-HPS works modulo the
  factor $x^{N-1} + \dots + 1$ for the secret-dependent parts.
- $f$ and $r$ have fixed weight here; in NTRU-HPS they are uniformly random
  ternary polynomials. For $N = 677$ and $821$ that makes Phoenix's secrets
  sparser.
- Sampling, encoding and hashing are entirely different.

Nobody has run lattice-reduction estimates against these sets. Treat the
names as sizes, not as security levels.

For scale, the number of possible private polynomials $f$ is about $2^{755}$,
$2^{893}$ and $2^{1286}$ for the three sets, so guessing is not the concern;
the relevant attacks are lattice reduction and meet-in-the-middle hybrids.

### The toy set

`TOY` exists so that examples fit on a page. There are 210 candidates for
$f$; [`examples/06_break_the_toy.py`](../examples/06_break_the_toy.py)
recovers a working private key from the public key by trying them all:

```console
$ python examples/06_break_the_toy.py
candidates tried : 210
keys that work   : 7
real f           : x^6 - x^5 + x^4 + x^3 - x^2
real f found     : True
decrypts with it : True
```

Seven keys work rather than one because $x^k \star f$ is just as good a
private key as $f$ for each of the $N = 7$ rotations.

### Custom parameters

`ParameterSet` validates structure (prime $N$, coprime moduli, weights that
fit) and correctness (no decryption failures). It cannot tell you whether a
set is *secure*. Small or unusual choices are almost certainly not.

## Why "quantum-resistant" is a belief, not a theorem

Shor's algorithm breaks RSA and elliptic-curve cryptography because both
reduce to finding a hidden period, which quantum computers do efficiently.
No comparable structure is known in lattice problems, and decades of effort
have produced only modest quantum speed-ups against them. That is strong
evidence, and it is the basis on which lattice schemes were standardised, but
it is not a proof. The same is true, classically, of every public-key system
in use.

## Operational notes

- **Private key files** are written with mode `0600` by `phoenix keygen`,
  and `*.key` is in the repository's `.gitignore`. Phoenix does not encrypt
  private keys at rest; protect them with your file system or a secrets
  manager.
- **The playground** sends keys over plain HTTP on the loopback interface.
  Use throwaway keys there.
- **`seed=` arguments** on `generate_keypair` and `encapsulate` make output
  deterministic. They exist for tests and worked examples. A key generated
  from a guessable seed is a guessable key.

## Reporting a problem

Open an issue at <https://github.com/iamv1n/phoenix/issues>. Since nobody
should be relying on Phoenix for real security, public issues are fine; bug
reports that break the scheme are especially welcome.
