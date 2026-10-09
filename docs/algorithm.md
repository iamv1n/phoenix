# The NTRU algorithm

This page describes textbook NTRU exactly as [`phoenix.ntru`](api.md#phoenixntru--textbook-ntru)
implements it. It assumes the notation from
[Mathematical background](math.md): $\star$ is multiplication in
$\mathbb{Z}[x]/\langle x^N - 1\rangle$, and $T(a, b)$ is the set of ternary
polynomials with $a$ coefficients $+1$ and $b$ coefficients $-1$.

NTRU was introduced by Hoffstein, Pipher and Silverman in 1996.

> Textbook NTRU is a building block, not a finished cipher. It is malleable
> and breaks under chosen-ciphertext attack. [KEM and sealing](kem-and-sealing.md)
> covers what Phoenix layers on top.

## Parameters

| Symbol | Meaning | `phoenix677` |
| --- | --- | --- |
| $N$ | Polynomials have $N$ coefficients; prime | 677 |
| $p$ | Small modulus; the message lives modulo $p$ | 3 |
| $q$ | Large modulus; ciphertexts live modulo $q$; coprime to $p$ | 2048 |
| $d_f$ | $f \in T(d_f + 1,\ d_f)$ | 127 |
| $d_g$ | $g \in T(d_g,\ d_g)$ | 127 |
| $d_r$ | $r \in T(d_r,\ d_r)$ | 127 |

## Key generation

1. Pick a random $f \in T(d_f + 1, d_f)$.
2. Compute $f_p = f^{-1} \bmod p$ and $f_q = f^{-1} \bmod q$. If either does
   not exist, go back to step 1.
3. Pick a random $g \in T(d_g, d_g)$.
4. Compute

$$h = p \cdot f_q \star g \pmod q.$$

The **public key** is $h$. The **private key** is $f$ (with $f_p$, which can
be recomputed from it).

$h$ looks like $N$ uniformly random numbers modulo $q$, yet it secretly
factors as a ratio of two small polynomials.

## Encryption

To encrypt a message polynomial $m$ with coefficients in $\{-1, 0, 1\}$:

1. Pick a random **blinding polynomial** $r \in T(d_r, d_r)$.
2. Compute

$$e = r \star h + m \pmod q.$$

The term $r \star h$ looks random and hides $m$ completely from anyone who
cannot undo it.

## Decryption

Given $e$ and the private key:

1. Compute $a = f \star e \pmod q$.
2. **Center-lift** $a$: choose its coefficients in $(-q/2,\ q/2]$.
3. Compute $m = f_p \star a \pmod p$, centered.

## Why it works

Substitute the definition of $e$, then of $h$:

$$
\begin{aligned}
a &\equiv f \star e \\
  &\equiv f \star (r \star h + m) \\
  &\equiv f \star r \star (p\, f_q \star g) + f \star m \\
  &\equiv p\, r \star g + f \star m \pmod q,
\end{aligned}
$$

using $f \star f_q \equiv 1 \pmod q$.

Now the crucial observation: $r$, $g$, $f$ and $m$ are all small, so the
polynomial $p\, r \star g + f \star m$, computed over the plain integers, has
small coefficients. If all of them lie in $(-q/2, q/2]$, then reducing modulo
$q$ and center-lifting changes nothing, and step 2 hands back that integer
polynomial **exactly**, not merely modulo $q$.

Once it is an exact integer polynomial we are free to reduce it modulo a
*different* number, $p$. The first term vanishes because it is a multiple of
$p$:

$$a \equiv f \star m \pmod p,$$

and multiplying by $f_p$ removes $f$:

$$f_p \star a \equiv f_p \star f \star m \equiv m \pmod p.$$

The trick, in one sentence: **$q$ is large enough that the masked value never
wraps around, so the mask can be removed by reducing modulo $p$.** Without
$f$, an attacker cannot turn $e$ into anything small, and reducing $e$ modulo
$p$ directly is useless: $r \star h$ has already been reduced modulo $q$,
which scrambles its residues modulo $p$.

## Why decryption never fails

Everything hinges on $p\, r \star g + f \star m$ fitting in $(-q/2, q/2]$.
Bound each coefficient:

- A coefficient of $r \star g$ is a sum of products $r_i g_j$. At most
  $\min(2d_r, 2d_g)$ of them are non-zero and each is $\pm 1$.
- A coefficient of $f \star m$ is a sum of at most $2d_f + 1$ non-zero terms,
  each of absolute value at most 1.

Hence

$$\bigl|\,p\, r \star g + f \star m\,\bigr|_\infty \;\le\; 2p\,\min(d_r, d_g) + 2d_f + 1.$$

For `phoenix677` that is $6 \cdot 127 + 255 = 1017$, and the limit
$\lfloor (q-1)/2 \rfloor$ is $1023$. The bound holds for *every* possible
key, message and blinding polynomial, so decryption is correct with
certainty.

Many classical NTRU parameter sets only make failure *unlikely*. Phoenix
refuses them: constructing a `ParameterSet` that violates the bound raises
`ParameterError`.

```python
>>> from phoenix import ParameterSet
>>> ParameterSet("risky", N=503, p=3, q=257, df=61, dg=20, dr=18)
Traceback (most recent call last):
  ...
phoenix.errors.ParameterError: decryption could fail: p*r*g + f*m can reach 231,
which does not fit in (-q/2, q/2] for q = 257
```

Those were, incidentally, the defaults of the first version of this project.
Rare decryption failures are not just a reliability problem: an attacker who
can observe which ciphertexts fail learns about the private key.

## Worked example

Take the toy parameters $N = 7$, $p = 3$, $q = 41$, $d_f = d_g = d_r = 2$.
Run it yourself with
[`examples/02_textbook_ntru.py`](../examples/02_textbook_ntru.py), or in the
[playground](playground.md) via **Load the docs example**.

**Key generation.** Choose

$$f = x^6 - x^4 + x^3 + x^2 - 1, \qquad g = x^6 + x^4 - x^2 - x.$$

The inverses of $f$ are

$$f_p = x^6 + 2x^5 + x^3 + x^2 + x + 1,$$

$$f_q = 8x^6 + 26x^5 + 31x^4 + 21x^3 + 40x^2 + 2x + 37,$$

and the public key is

$$h = 3 f_q \star g = 19x^6 + 38x^5 + 6x^4 + 32x^3 + 24x^2 + 37x + 8 \pmod{41}.$$

**Encryption.** With message and blinding polynomial

$$m = -x^5 + x^3 + x^2 - x + 1, \qquad r = x^6 - x^5 + x - 1,$$

the ciphertext is

$$e = r \star h + m = 31x^6 + 19x^5 + 4x^4 + 2x^3 + 40x^2 + 3x + 25 \pmod{41}.$$

**Decryption.** Multiply by $f$ and center-lift:

$$a = f \star e = x^6 + 10x^5 - 8x^4 - x^3 - x^2 + x - 1.$$

Computing $3\, r \star g + f \star m$ over the integers gives the very same
polynomial. Its largest coefficient is 10, far below the limit of 20, so
nothing wrapped. Reduce modulo 3:

$$b = x^6 + x^5 + x^4 - x^3 - x^2 + x - 1,$$

and multiply by $f_p$:

$$f_p \star b = -x^5 + x^3 + x^2 - x + 1 = m. \quad\checkmark$$

The same thing in code:

```python
from phoenix import TOY, ntru

f = [-1, 0, 1, 1, -1, 0, 1]  # constant term first
g = [0, -1, -1, 0, 1, 0, 1]
m = [1, -1, 1, 1, 0, -1, 0]
r = [-1, 1, 0, 0, 0, -1, 1]

public_key, private_key = ntru.keypair_from(TOY, f, g)
e = ntru.encrypt(public_key, m, r)
assert ntru.decrypt(private_key, e).tolist() == m
```

## Three details worth knowing

**Why $f$ has an extra $+1$.** A polynomial whose coefficients sum to zero is
divisible by $x - 1$, which divides $x^N - 1$, so it can never be inverted.
$T(d_f + 1, d_f)$ guarantees $f(1) = 1$.

**What a ciphertext leaks.** $g(1) = 0$ forces $h(1) \equiv 0$, so evaluating
a ciphertext at $x = 1$ gives $e(1) \equiv m(1) \pmod q$: the sum of the
message's coefficients, in the clear. The KEM avoids this by only ever
encrypting messages from $T(d_m, d_m)$, whose coefficients sum to zero.

**Malleability.** Adding $x^k$ to a ciphertext adds $x^k$ to the plaintext,
and the receiver cannot tell:

```python
e[0] = (e[0] + 1) % 41  # m becomes m + 1, silently
```

That, and worse attacks built on the same idea, is why applications should
use `phoenix.seal` rather than this layer.

Next: [KEM and sealing](kem-and-sealing.md).
