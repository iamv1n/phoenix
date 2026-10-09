# Why your encryption has an expiry date

*Part 1 of 4 · [Index](README.md) · Next: [NTRU by hand](02-ntru-by-hand.md)*

Almost every secure connection you make starts the same way. Two machines
that have never met agree on a secret key while the whole network listens.
The mathematics that makes this possible, public-key cryptography, comes down
to a small number of problems that are easy to set up and believed to be hard
to undo:

- **RSA** rests on factoring: multiplying two large primes is easy, splitting
  the product back apart is not.
- **Diffie–Hellman and elliptic curves** rest on discrete logarithms:
  computing $g^x$ is easy, recovering $x$ is not.

"Believed to be hard" has held up for nearly fifty years against classical
computers. It does not hold up against a quantum one.

## What Shor found

In 1994 Peter Shor showed that a sufficiently large quantum computer could
factor integers and compute discrete logarithms in polynomial time.

The reason is worth a sentence, because it explains what survives. Both
problems can be rephrased as *finding the period of a function*. For
factoring $n$, the function is $x \mapsto a^x \bmod n$, which repeats with
some period $r$; knowing $r$ gives you the factors with a little extra
arithmetic. A quantum computer can evaluate a function on a superposition of
all inputs and then use the quantum Fourier transform to make the period
interfere constructively. Period-finding is, in a real sense, what quantum
computers are *for*.

So this is not a speed-up that bigger keys can outrun. RSA and elliptic
curves have exactly the hidden periodic structure that the algorithm
exploits. Doubling the key size makes the attacker's job a little longer, not
exponentially longer.

## What quantum computers do not break

It is easy to overcorrect into "quantum breaks all encryption". It does not.

**Symmetric ciphers and hashes** (AES, ChaCha20, SHA-2, SHA-3) have no
periodic structure to find. The best generic quantum attack, Grover's
algorithm, gives a quadratic speed-up to brute-force search: a 256-bit key
offers roughly the resistance a 128-bit key does today. Use 256-bit keys and
move on.

The damage is confined to public-key cryptography, which is to say, to the
step where two strangers agree on a key, and to digital signatures.

## "But nobody has that computer"

True, as of this writing. Machines large and reliable enough to break
real-world RSA do not exist, and estimates of when they will vary widely.
There are two reasons the timeline matters less than it seems.

**Harvest now, decrypt later.** Encrypted traffic can be recorded today and
stored. If the key exchange protecting it is broken in fifteen years, the
recording becomes readable in fifteen years. Anything that must stay secret
for longer than the time until a capable quantum computer exists is already
exposed. Medical records, state secrets and long-lived credentials are in
that category.

**Migration is slow.** Replacing a cryptographic primitive across the
world's software, hardware and standards takes a decade or more. It did for
every previous transition.

That is why the replacement is happening now. NIST ran a public competition
from 2016 and published its first post-quantum standards in August 2024:
ML-KEM for key exchange (FIPS 203) and ML-DSA and SLH-DSA for signatures
(FIPS 204 and 205). Major browsers, messaging apps and SSH implementations
already use post-quantum key exchange by default, usually combined with a
classical algorithm so that both would have to fail.

## Finding a problem without a period

A replacement needs a different kind of hard problem: one with no hidden
periodicity for Shor's algorithm to grab. Several families have been
studied seriously:

| Family | Hard problem | Notes |
| --- | --- | --- |
| **Lattices** | Finding short vectors in high-dimensional lattices | Fast, moderate sizes; basis of ML-KEM, ML-DSA and NTRU |
| **Codes** | Decoding random linear codes | Very old (1978), large public keys |
| **Hash-based** | Security of a hash function | Signatures only; very conservative |
| **Isogenies** | Finding maps between elliptic curves | Tiny keys; the leading candidate was broken classically in 2022 |

The last row is a useful reminder that "believed hard" is an empirical
statement. Confidence comes from years of failed attacks, and lattices have
accumulated more of those than any other family.

## Lattices in one picture

A lattice is a regular grid of points: every integer combination of some
basis vectors. In two dimensions:

```
      .     .     .     .     .
   .     .     .     .     .
      .     .     O     .     .          O = origin
   .     .     .     .     .
      .     .     .     .     .
```

The same lattice can be described by many different bases. Two short,
nearly perpendicular vectors describe this grid nicely. So do two enormously
long, nearly parallel ones; every point is still reachable, but you would
never guess the grid's shape from them.

**The shortest vector problem** asks: given a *bad* basis, find a shortest
non-zero lattice point. In two dimensions this is trivial. In several hundred
dimensions, the best known algorithms, classical and quantum alike, take time
exponential in the dimension.

That asymmetry is a trapdoor:

- The **private key** is a good, short basis.
- The **public key** is a bad basis for the same lattice.
- Encrypting hides a message near a lattice point; only someone with short
  vectors can reliably find their way back.

## Where NTRU fits

NTRU, published by Hoffstein, Pipher and Silverman in 1996, was the first
practical cryptosystem of this kind, and it reaches the lattice by an
unexpected route. Nothing in it looks like geometry. Keys and messages are
polynomials, and the private key is simply two polynomials with very small
coefficients. The lattice appears only when you ask how an attacker would
recover them.

It has aged well. NTRU was a finalist in the NIST competition; a close
relative, NTRU Prime, has been part of OpenSSH's default key exchange since
2022; and the Falcon signature scheme selected by NIST is built on NTRU
lattices.

It is also unusually easy to understand. The entire algorithm is a handful
of polynomial multiplications, and you can run it by hand on seven
coefficients. That is exactly what the [next post](02-ntru-by-hand.md) does.

## Try it

Phoenix implements NTRU end to end:

```python
import phoenix

public_key, private_key = phoenix.generate_keypair()
sealed = phoenix.seal(public_key, b"still secret in 2050?")
print(phoenix.unseal(private_key, sealed))
```

Or run `phoenix playground` and click around. One caveat, which later posts
return to: Phoenix is for learning. For production, use a reviewed
implementation of a standard.
