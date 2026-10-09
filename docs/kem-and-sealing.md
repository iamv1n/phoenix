# KEM and sealing

[Textbook NTRU](algorithm.md) encrypts one small polynomial and offers no
protection against an attacker who modifies ciphertexts. Phoenix turns it
into something usable in two steps:

```
phoenix.ntru   textbook trapdoor            e = r*h + m
      │
phoenix.kem    key encapsulation            (ciphertext, 32-byte secret)
      │
phoenix.seal   hybrid encryption of bytes   header | KEM ciphertext | AEAD ciphertext
```

## What is wrong with the textbook scheme

1. **It is malleable.** Add $x^k$ to a ciphertext and the plaintext gains
   $x^k$. An attacker can alter messages they cannot read.
2. **Decryption can be turned into an oracle.** Feed the receiver carefully
   malformed ciphertexts, watch how they react, and the private key leaks
   piece by piece. Practical attacks of this kind against unpadded NTRU have
   been known since 2000.
3. **It leaks $m(1)$.** See
   [the algorithm page](algorithm.md#three-details-worth-knowing).
4. **Messages are polynomials.** Real data is bytes of arbitrary length.

The standard cure is to never encrypt a chosen message at all.

## The KEM

A **key encapsulation mechanism** has two operations:

- `encapsulate(public_key) -> (ciphertext, shared_secret)`
- `decapsulate(private_key, ciphertext) -> shared_secret`

The sender does not choose what gets encrypted; the mechanism generates a
random secret and transports it. Phoenix builds its KEM with a
Fujisaki–Okamoto-style transform.

### Encapsulation

1. Sample a random message $m \in T(d_m, d_m)$ with $d_m = \lfloor N/3 \rfloor$.
2. **Derive** the blinding polynomial from the message and the public key:
   $r = \text{Sample}\bigl(H(\texttt{blinding},\ H(\text{pk}),\ m)\bigr)$.
3. Compute $e = r \star h + m \pmod q$ and pack it into bytes: the
   ciphertext $c$.
4. Output the shared secret $K = H(\texttt{key},\ m,\ c)$.

Step 2 is the heart of it. Because $r$ is a deterministic function of $m$,
anyone who knows $m$ can recompute the entire ciphertext.

### Decapsulation

1. Unpack $c$ and decrypt it to get a candidate $m'$.
2. Check that $m'$ really is in $T(d_m, d_m)$.
3. Re-derive $r'$ from $m'$, **re-encrypt**, and compare with $c$ byte for
   byte.
4. If everything matches, output $K = H(\texttt{key},\ m',\ c)$.
5. Otherwise output $K' = H(\texttt{reject},\ s,\ c)$, where $s$ is a random
   32-byte value stored in the private key.

### Why this fixes the problems

- **Malleability is gone.** A modified ciphertext is not the encryption of
  any message under its derived $r$, so it fails step 3.
- **There is no oracle.** Step 5 is called *implicit rejection*. A bad
  ciphertext does not produce an error; it produces a key that is
  unpredictable to anyone without $s$ and is useless to the attacker. From
  the outside, every ciphertext appears to decapsulate "successfully".
- **$m(1)$ is always zero**, so nothing is leaked by evaluating at 1.
- **The secret has no structure.** $m$ is random and only its hash is ever
  used.

```python
>>> ciphertext, secret = phoenix.encapsulate(public_key)
>>> phoenix.decapsulate(private_key, ciphertext) == secret
True
>>> tampered = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
>>> phoenix.decapsulate(private_key, tampered) == secret
False                      # no exception, just an unrelated key
```

A ciphertext that is not even well-formed (wrong length, coefficient
$\ge q$) raises `FormatError`. That is safe: anyone can perform those checks
without the key, so the error reveals nothing.

## Sealing

`phoenix.seal` is **hybrid encryption**: the KEM transports a key, and a
standard symmetric cipher encrypts the data.

```
seal(public_key, plaintext, associated_data):
    kem_ciphertext, key = encapsulate(public_key)
    body = ChaCha20-Poly1305(key, nonce = 0).encrypt(
               plaintext,
               aad = header | kem_ciphertext | associated_data)
    return header | kem_ciphertext | body
```

Notes on the design:

- **ChaCha20-Poly1305** is an authenticated cipher (AEAD): it encrypts and
  appends a 16-byte tag that fails to verify if a single bit changes.
  Phoenix uses the implementation from the `cryptography` package rather
  than writing its own.
- **The nonce is fixed at zero.** Nonce reuse is only dangerous under the
  same key, and each key here comes from a fresh encapsulation and encrypts
  exactly one message.
- **The header and KEM ciphertext are authenticated** as associated data, so
  the two halves of a message cannot be mixed and matched, and the parameter
  set cannot be swapped.
- **Implicit rejection composes cleanly.** If the KEM ciphertext was
  tampered with, decapsulation silently yields a wrong key, the AEAD tag
  fails, and `unseal` raises `DecryptionError`. Tampering with either half
  produces the same error.

The overhead is constant: 966 bytes for `phoenix677`, whatever the message
size.

### What sealing does not do

- **It does not say who sent the message.** Anyone with the public key can
  seal. If you need sender authentication, sign the message with a signature
  scheme; Phoenix does not include one.
- **It does not hide the length** of the plaintext.
- **It has no forward secrecy.** If a private key leaks, every message ever
  sealed to it can be read. Protocols get forward secrecy by generating a
  fresh key pair per session and using the [KEM](#the-kem) directly.
- **It does not stream.** A message is sealed in one piece, in memory.

## Caveats on the construction

The transform follows the standard recipe, but this exact combination (this
ring, these distributions, this encoding) has no published security proof
and has not been reviewed. Details that a production design would also get
right, such as constant-time decapsulation, are out of scope here. See
[Security](security.md).

The byte-level details of every hash input are in
[File formats](formats.md#kem-derivations).
