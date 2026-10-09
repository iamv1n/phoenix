# NTRU by hand

*Part 2 of 4 · [Index](README.md) · Previous: [Why your encryption has an expiry date](01-why-post-quantum.md) · Next: [From a maths trick to something you can use](03-from-textbook-to-usable.md)*

Most cryptography is hard to *watch*. The numbers have hundreds of digits and
the interesting part happens inside a function call. NTRU is different: scale
it down far enough and the whole thing fits in a terminal, every intermediate
value visible.

This post runs NTRU on polynomials with seven coefficients. It is hopelessly
insecure at that size, and exactly the same algorithm as at full size.

You need Phoenix installed (`pip install -e .` from the repository) and a
Python prompt.

## The playing field

NTRU works with polynomials under two rules.

**Rule 1: exponents wrap around at N.** We set $x^N = 1$, so $x^{N+1} = x$,
and so on. A polynomial never has more than $N$ coefficients.

**Rule 2: coefficients wrap around at a modulus.** Sometimes a small one,
$p$; sometimes a large one, $q$.

We will use $N = 7$, $p = 3$, $q = 41$.

```python
>>> import numpy as np
>>> from phoenix import poly
>>> show = poly.format_poly
>>> N, p, q = 7, 3, 41
```

Phoenix stores a polynomial as an array with the constant term first:

```python
>>> f = np.array([-1, 0, 1, 1, -1, 0, 1])
>>> show(f)
'x^6 - x^4 + x^3 + x^2 - 1'
```

Multiplication under rule 1 is `poly.convolve`. Multiply $x^4$ by $x^5$ and
you get $x^9 = x^2$:

```python
>>> x4 = np.array([0, 0, 0, 0, 1, 0, 0])
>>> x5 = np.array([0, 0, 0, 0, 0, 1, 0])
>>> show(poly.convolve(x4, x5))
'x^2'
```

## Step 1: two small secrets

The private key starts as two polynomials whose coefficients are all $-1$,
$0$ or $1$:

```python
>>> f = np.array([-1, 0, 1, 1, -1, 0, 1])     # x^6 - x^4 + x^3 + x^2 - 1
>>> g = np.array([0, -1, -1, 0, 1, 0, 1])     # x^6 + x^4 - x^2 - x
```

*Small* is the important word. Everything that follows depends on these
coefficients being tiny compared with $q$.

## Step 2: undo f, twice

We need a polynomial that cancels $f$, an inverse, under each modulus:

```python
>>> fp = poly.invert(f, p)
>>> fq = poly.invert(f, q)
>>> show(fp)
'x^6 + 2x^5 + x^3 + x^2 + x + 1'
>>> show(fq)
'8x^6 + 26x^5 + 31x^4 + 21x^3 + 40x^2 + 2x + 37'
```

Check that they really are inverses:

```python
>>> show(poly.convolve(f % p, fp, p))
'1'
>>> show(poly.convolve(f % q, fq, q))
'1'
```

Look at `fq`. $f$ was tiny, and its inverse is a mess of numbers spread
across the whole range 0 to 40. **Inverting destroys smallness.** That is the
one-way street NTRU is built on.

(How the inverse is computed is a story of its own, told in
[the maths docs](../docs/math.md#inverses-and-the-euclidean-algorithm).)

## Step 3: the public key

```python
>>> h = 3 * poly.convolve(fq, g % q, q) % q
>>> show(h)
'19x^6 + 38x^5 + 6x^4 + 32x^3 + 24x^2 + 37x + 8'
```

That is $h = p \cdot f_q \star g \bmod q$. Publish it. It looks like seven
random numbers, and the claim underpinning NTRU's security is that, at real
sizes, nobody can tell it apart from seven random numbers, let alone recover
the small $f$ and $g$ hidden inside.

## Step 4: encrypt

The message is also a small polynomial. Here is one, along with a random
small polynomial $r$ that will be used once and thrown away:

```python
>>> m = np.array([1, -1, 1, 1, 0, -1, 0])     # -x^5 + x^3 + x^2 - x + 1
>>> r = np.array([-1, 1, 0, 0, 0, -1, 1])     # x^6 - x^5 + x - 1
```

Encryption is one multiplication and one addition:

```python
>>> mask = poly.convolve(r % q, h, q)
>>> show(mask)
'31x^6 + 20x^5 + 4x^4 + x^3 + 39x^2 + 4x + 24'
>>> e = (mask + m) % q
>>> e.tolist()
[25, 3, 40, 2, 4, 19, 31]
```

The mask $r \star h$ looks random, so adding the message to it gives
something that looks random too. An eavesdropper sees `e` and learns nothing
they can use.

## Step 5: decrypt

The receiver multiplies by the secret $f$:

```python
>>> a = poly.convolve(f % q, e, q)
>>> a.tolist()
[40, 1, 40, 40, 33, 10, 1]
```

Now the step that makes everything work. Read each number as the nearest
representative to zero: 40 is really $-1$, and 33 is really $-8$.

```python
>>> a = poly.center(a, q)
>>> a.tolist()
[-1, 1, -1, -1, -8, 10, 1]
```

The numbers have suddenly become small. Something collapsed. Hold that
thought, reduce modulo 3, and multiply by `fp`:

```python
>>> poly.center(poly.convolve(fp, a % p, p), p).tolist()
[1, -1, 1, 1, 0, -1, 0]
>>> m.tolist()
[1, -1, 1, 1, 0, -1, 0]
```

The message is back.

## Why did the numbers get small?

Unpack what $f \star e$ actually is:

$$
f \star e = f \star (r \star h + m) = f \star r \star (3 f_q \star g) + f \star m = 3 r \star g + f \star m.
$$

The $f$ met the $f_q$ buried inside $h$ and they cancelled. What remains is
built entirely from the four small polynomials. Compute it with **no modular
reduction at all**:

```python
>>> show(poly.convolve(r, g))
'2x^5 - 2x^4 - x^2 + 1'
>>> show(poly.convolve(f, m))
'x^6 + 4x^5 - 2x^4 - x^3 + 2x^2 + x - 4'
>>> (3 * poly.convolve(r, g) + poly.convolve(f, m)).tolist()
[-1, 1, -1, -1, -8, 10, 1]
```

Identical to the centered `a`. The values modulo 41 and the true integer
values agree, because no coefficient was big enough to wrap around.

And once you hold true integers rather than residues modulo 41, you may
reduce them modulo anything you like. Modulo 3, the term $3 r \star g$ is
zero. That leaves $f \star m$, and `fp` strips off the $f$.

The secret is not an exotic operation. It is knowing a multiplier that makes
the ciphertext *small*.

## Break it on purpose

Two experiments show how little slack there is.

**Skip the centering.** Use the raw residues `[40, 1, 40, 40, 33, 10, 1]`:

```python
>>> raw = poly.convolve(f % q, e, q)
>>> poly.center(poly.convolve(fp, raw % p, p), p).tolist()
[0, 1, -1, 0, 0, 0, 0]
```

Wrong. 40 and $-1$ are the same number modulo 41 but different numbers modulo
3, and it is the true value $-1$ we need.

**Make q too small.** The largest coefficient above was 10. With $q = 16$ the
centered range is $-7$ to $8$, and 10 no longer fits:

```python
>>> q = 16
>>> fq = poly.invert(f, q)
>>> h = 3 * poly.convolve(fq, g % q, q) % q
>>> e = (poly.convolve(r % q, h, q) + m) % q
>>> a = poly.center(poly.convolve(f % q, e, q), q)
>>> a.tolist()
[-1, 1, -1, -1, 8, -6, 1]
>>> poly.center(poly.convolve(fp, a % p, p), p).tolist()
[1, 1, 0, 0, 0, -1, 0]
```

The 10 wrapped to $-6$ and the $-8$ to $8$, and the "decrypted" message is
garbage. This is a **decryption failure**, and it is why $q$ must be large
relative to the secrets.

Phoenix computes the worst case for a parameter set up front and refuses any
set where this could happen:

```python
>>> import phoenix
>>> phoenix.ParameterSet("too-small", N=7, p=3, q=16, df=2, dg=2, dr=2)
Traceback (most recent call last):
  ...
phoenix.errors.ParameterError: decryption could fail: p*r*g + f*m can reach 17,
which does not fit in (-q/2, q/2] for q = 16
```

## The same thing, without the scaffolding

Everything above is what `phoenix.ntru` does:

```python
from phoenix import TOY, ntru

public_key, private_key = ntru.keypair_from(TOY, f, g)
e = ntru.encrypt(public_key, m, r)
assert ntru.decrypt(private_key, e).tolist() == m.tolist()
```

And the playground will run it on random inputs as often as you like, with
every row shown: `phoenix playground`, then **Step through the maths**.

## How hard is it to break?

At this size, not at all. An attacker wants a small $f$ such that
$f \star h$ is three times something small. There are only 210 ways to place
three coefficients $+1$ and two coefficients $-1$ in seven slots, so try them all:

```console
$ python examples/06_break_the_toy.py
candidates tried : 210
keys that work   : 7
real f           : x^6 - x^5 + x^4 + x^3 - x^2
real f found     : True
decrypts with it : True
```

(Seven keys work, not one: rotating $f$ by multiplying it by $x^k$ gives an
equally good key.)

Now scale up. With Phoenix's default $N = 677$ and 255 non-zero coefficients
in $f$, the number of candidates is about $2^{893}$. Brute force is not an
option, and cleverer attacks rephrase the search as finding a short vector in
a lattice of dimension 1354, which is the problem nobody knows how to solve.

Same algorithm; seven coefficients became 677.

## What we have not solved

We encrypted one small polynomial. And if you were paying attention to the
shape of $e = r \star h + m$, you may have noticed something uncomfortable:
anyone can add to it.

```python
e[0] = (e[0] + 1) % 41  # the receiver will decrypt m + 1 and never know
```

That turns out to be the thread that unravels the whole textbook scheme. The
[next post](03-from-textbook-to-usable.md) pulls on it.
