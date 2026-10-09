# From a maths trick to something you can use

*Part 3 of 4 · [Index](README.md) · Previous: [NTRU by hand](02-ntru-by-hand.md) · Next: [Rebuilding Phoenix](04-rebuilding-phoenix.md)*

The [previous post](02-ntru-by-hand.md) ended with a working cryptosystem:

$$
e = r \star h + m \pmod q.
$$

It is correct. It is, as far as anyone knows, hard to invert without the
private key. And if you deployed it as is, it would be broken, without
anyone solving a single lattice problem.

This is the most important lesson in applied cryptography, and textbook NTRU
teaches it well: **a hard problem is not a secure system.** This post
breaks the textbook scheme three ways, then builds the layers that fix it.

All examples use a real-size key:

```python
>>> import numpy as np
>>> import phoenix
>>> from phoenix import ntru, poly
>>> public_key, private_key = phoenix.generate_keypair()
>>> N, q = public_key.params.N, public_key.params.q
>>> N, q
(677, 2048)
```

## Break 1: the attacker can edit your message

Encryption is *linear* in the message. Add something to the ciphertext and
the same thing is added to the plaintext:

$$
e + x^k = r \star h + (m + x^k).
$$

```python
>>> m = np.zeros(N, dtype=np.int64)
>>> m[:3] = [1, 0, -1]
>>> e = ntru.encrypt(public_key, m)
>>> e[1] = (e[1] + 1) % q              # attacker, in transit
>>> ntru.decrypt(private_key, e)[:5].tolist()
[1, 1, -1, 0, 0]
```

The second coefficient changed from 0 to 1. The attacker never learned the
message and did not need to. If that coefficient was a digit of an amount or
a bit of a permission flag, they have changed it anyway, and the receiver
has no way to notice.

This property is called **malleability**. Encryption that hides a message
without protecting it from modification is a trap that has caught many real
systems.

## Break 2: the ciphertext leaks a fact about the message

Evaluate any polynomial at $x = 1$ and you get the sum of its coefficients.
Evaluation at 1 is also compatible with our multiplication, since $x^N = 1$
holds when $x = 1$. So:

$$
e(1) = r(1) h(1) + m(1) \pmod q.
$$

Key generation draws $g$ with as many coefficients $+1$ as $-1$, so $g(1) = 0$,
and therefore $h(1) = 0$:

```python
>>> int(public_key.h.sum() % q)
0
```

Which leaves $e(1) = m(1)$. The sum of the message's coefficients is sitting
in the ciphertext for anyone to read:

```python
>>> rng = np.random.default_rng(1)
>>> m = np.where(rng.random(N) < 0.9, 1, 0)
>>> int(m.sum())
610
>>> e = ntru.encrypt(public_key, m)
>>> int(e.sum() % q)
610
```

No key was used in the last line. One number about the message is not the
whole message, but "encryption" is supposed to leak *nothing*, and real
attacks are assembled from leaks like this.

## Break 3: the receiver can be turned against themselves

This is the serious one.

Decryption only works because $p r \star g + f \star m$ stays small enough
not to wrap around modulo $q$. An attacker is not obliged to send honest
ciphertexts. Suppose they send one crafted so that the result sits right at
the edge, such that it wraps around *only if a particular coefficient of the
private key has a particular value*.

Then they watch. Did the receiver's software accept the message, or report
an error? Did the reply come back garbled? Each observation answers a yes/no
question about $f$, and enough well-chosen questions recover the key.

Attacks of exactly this kind against unpadded NTRU were published in 2000.
The receiver, by helpfully reacting to bad input, becomes a **decryption
oracle**. Note what this means: Break 1 was not just a nuisance. The ability
to submit modified ciphertexts and observe the outcome is what destroys the
scheme.

## Fix: stop encrypting messages

All three breaks share a root. The sender, or an attacker, gets to choose
what goes into the encryption, and the receiver cannot tell an honest
ciphertext from a manipulated one.

The modern answer is a **key encapsulation mechanism** (KEM). Do not encrypt
the message with NTRU at all. Use NTRU to transport a random value, and
derive a key from it.

```python
>>> ciphertext, secret = phoenix.encapsulate(public_key)
>>> phoenix.decapsulate(private_key, ciphertext) == secret
True
```

Inside, three changes do the work.

### 1. The message is random, and balanced

`encapsulate` picks a random polynomial $m$ with as many coefficients $+1$
as $-1$. Its coefficient sum is always zero, so **Break 2 has nothing to
leak**:

```python
>>> e = phoenix.encoding.unpack_coefficients(ciphertext, N, public_key.params.q_bits, q)
>>> int(e.sum() % q)
0
```

### 2. The randomness is derived from the message

In the textbook scheme $r$ is random. In the KEM it is *computed*:

$$
r = \text{Sample}\bigl(H(\text{public key}, m)\bigr).
$$

This looks like a strange thing to do; it is the key idea. It means that a
ciphertext is a deterministic function of $m$. So after the receiver decrypts
and obtains $m$, they can **encrypt it again themselves and check that they
get exactly the ciphertext they were sent.**

An honest ciphertext passes. A ciphertext that has been altered in any way,
or crafted to sit at a wrap-around boundary, is not the encryption of
anything under its derived $r$, and fails. **That ends Break 1 and Break 3.**

This re-encryption check is the Fujisaki–Okamoto transform, and it is how
essentially every modern KEM, including the standardised ML-KEM, defends
itself.

### 3. Failure is silent

One hole remains. If the receiver *reports* that the check failed, that
report is itself an oracle.

So the KEM does not report it. On failure, `decapsulate` returns a key
anyway: a hash of the ciphertext and a secret value stored in the private
key.

```python
>>> forged = bytearray(ciphertext)
>>> forged[0] ^= 1
>>> phoenix.decapsulate(private_key, bytes(forged)).hex()[:16]
'427f3c0b4a609651'
>>> secret.hex()[:16]
'7e976cb5328e1daf'
```

(Your values will differ.) No exception. The attacker receives 32 bytes
that are indistinguishable from a real key and tell them nothing. The honest
parties simply end up with different keys and their conversation fails
later, for a reason the attacker cannot attribute to anything. This is
**implicit rejection**.

## From a key to a message

A KEM gives two parties 32 shared bytes. To encrypt actual data, hand those
bytes to a symmetric cipher. This two-part construction is **hybrid
encryption**, and it is how public-key encryption is always done in
practice: the expensive, fragile public-key operation handles 32 bytes, and
a fast, robust symmetric cipher handles the gigabytes.

Phoenix uses ChaCha20-Poly1305, an *authenticated* cipher: along with the
ciphertext it produces a tag that will not verify if a single bit of the
message has changed.

```python
>>> sealed = phoenix.seal(public_key, b"transfer 10 coins")
>>> phoenix.unseal(private_key, sealed)
b'transfer 10 coins'
```

Now replay Break 1 against it:

```python
>>> tampered = bytearray(sealed)
>>> tampered[100] ^= 1
>>> phoenix.unseal(private_key, bytes(tampered))
Traceback (most recent call last):
  ...
phoenix.errors.DecryptionError: message authentication failed
```

The two layers cooperate. Byte 100 is inside the KEM ciphertext, so the
re-encryption check failed, implicit rejection produced a wrong key, the tag
did not verify under that key, and `unseal` refused. Flip a bit in the body
instead and the tag fails directly. Either way the caller sees the same
error and no plaintext.

One design choice deserves a comment, because it would be a bug anywhere
else: `seal` uses a constant nonce. ChaCha20-Poly1305 is catastrophically
broken if a nonce repeats *under the same key*. Here every message gets a
fresh key from a fresh encapsulation, used exactly once, so there is nothing
to repeat. Phoenix did not write its own ChaCha20 either; it uses the
`cryptography` package.

## What it costs

| | Textbook NTRU | `phoenix.seal` |
| --- | --- | --- |
| Encrypts | one ternary polynomial | any number of bytes |
| Tampering | silently changes the plaintext | detected |
| Malformed ciphertexts | leak the private key | harmless |
| Leaks $m(1)$ | yes | no |
| Size overhead (`phoenix677`) | 931 bytes | 966 bytes |

Thirty-five more bytes (a 19-byte header and a 16-byte tag) and one extra
NTRU encryption during decapsulation. Encapsulation and decapsulation each
take about half a millisecond on a laptop.

## What is still missing

This is where honesty matters more than polish.

- **Timing.** The attacks above were stopped at the level of *what* the
  receiver outputs. But *how long* decapsulation takes also depends on secret
  data in Phoenix, and timing is observable. Production implementations are
  written so that every operation takes the same time regardless of secrets.
  Phoenix, built on NumPy and Python integers, is not.
- **Proof and review.** The transform follows a standard recipe. Nobody has
  proved that this exact variant is secure, and nobody independent has
  looked for mistakes.
- **Sender identity.** Anyone can seal to a public key. Knowing who sent a
  message needs signatures, a different primitive.
- **Forward secrecy.** If a private key leaks, old messages sealed to it are
  readable. Real protocols use short-lived keys.

So: Phoenix shows how the pieces fit, completely and runnably. It does not
replace a vetted library, and its [security page](../docs/security.md) says
so at length.

The gap between the first equation in this post and the last code block is
the whole craft. The lattice problem was never the weak point.

Next: [Rebuilding Phoenix](04-rebuilding-phoenix.md), on how the first
version of this project went wrong in more ordinary ways.
