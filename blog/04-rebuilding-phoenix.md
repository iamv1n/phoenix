# Rebuilding Phoenix

*Part 4 of 4 · [Index](README.md) · Previous: [From a maths trick to something you can use](03-from-textbook-to-usable.md)*

Phoenix began as a university project: three Python files implementing NTRU
with SymPy. Version 1.0 keeps the name and none of the code. This post goes
through what was wrong with the original, because nearly every problem is a
mistake that is easy to make and worth recognising.

To be fair to the original: its core mathematics was right. Once the first
problem below was patched, it generated keys and round-tripped
`"Hello world"`. The trouble was everything around the mathematics.

The old code is still in the repository's history
(`git show 930e0fa:ph_decrypt.py`), and every behaviour described here was
reproduced by running it.

## 1. It could not be imported

```python
from phpy.ph_util import *
```

There was no `phpy` package; the files sat in the repository root. And the
demo at the bottom of each file called classes that did not exist:

```python
class ph_encrypt: ...


if __name__ == "__main__":
    e = NTRUencrypt()  # NameError
```

The code had been renamed and never run again.

**Lesson:** a test that does nothing but import the package and round-trip
one message would have caught this. Phoenix now has 216 tests, and they take
under four seconds.

## 2. The primality test thought 4 was prime

```python
def isPrime(num):
    if num > 1:
        for i in range(2, int(math.sqrt(num))):
            if (num % i) == 0:
                return False
        else:
            return True
```

`range` excludes its upper bound, so the loop never tries the square root
itself, nor anything when the root rounds down to 2. Running it:

```
composites called prime below 60: [4, 6, 8, 9, 15, 25, 35, 49]
```

This guarded the parameters $N$, $p$ and $q$.

**Lesson:** off-by-one errors hide at boundaries, so test the boundaries.
The new test suite checks squares of primes specifically.

## 3. Changing N erased the other parameters

```python
if df is None:
    if self.df * 2 >= N:
        raise ValueError("Input df if too small than the default N")
    else:
        self.df = df  # df is None here
```

Calling `setNpq(N=509)` left `df`, `dg` and `dr` all set to `None`, to fail
somewhere far away later.

**Lesson:** mutable configuration with half-applied updates is a bug
factory. `ParameterSet` is now an immutable dataclass validated once, in one
place, on construction. There is no way to hold an invalid one.

## 4. A result thrown away

```python
pub.replace("\n", "")
```

Strings are immutable; `replace` returns a new one, which was discarded.
This one happened to be harmless, because the parser that followed tolerated
newlines. Bugs that are harmless by luck are the ones that survive.

## 5. Text was silently corrupted

Messages were turned into bits through a big integer:

```python
bin(int.from_bytes(str(s).encode(), "big"))
```

and decoded one byte at a time:

```python
charb.to_bytes(...).decode("utf-8", errors="ignore")
```

Any character that takes more than one byte in UTF-8 was split into pieces
that are not valid on their own, and `errors="ignore"` deleted them without
complaint:

```
'héllo 🔥'  ->  'hllo '
```

The integer conversion also drops leading zero bits, which the code papered
over with padding.

**Lesson:** `errors="ignore"` converts a loud failure into silent data loss.
More fundamentally, a cryptographic API should deal in **bytes**. Phoenix's
`seal` takes bytes and returns bytes; text encoding is the caller's decision,
made explicitly.

## 6. Correct decryption was a matter of luck

The defaults were $N = 503$, $q = 257$, $d_f = 61$, $d_g = 20$, $d_r = 18$.
Decryption requires every coefficient of $p\,r \star g + f \star m$ to stay
within $\pm q/2 \approx 128$. Its worst case with those weights is 231.

Typical values are much smaller, so failures would have been rare. But
"rare" is not "never", nothing checked, and decryption failures in NTRU are
not merely an inconvenience: an attacker who can observe them learns about
the private key.

**Lesson:** make invalid states unrepresentable. Those exact numbers now
raise an error:

```python
>>> phoenix.ParameterSet("legacy", N=503, p=3, q=257, df=61, dg=20, dr=18)
phoenix.errors.ParameterError: decryption could fail: p*r*g + f*m can reach 231, ...
```

and the built-in sets are chosen so the worst case provably fits (1017
against a limit of 1023, for the default).

## 7. The random numbers were not secret

```python
np.random.shuffle(f)
```

NumPy's global generator is a Mersenne Twister, designed for simulations.
Its internal state can be reconstructed from its outputs, at which point
every "random" private key it produces is predictable.

**Lesson:** key material comes from the operating system's
cryptographic generator. Phoenix draws 256 bits from `secrets` and expands
them with SHAKE-256.

## 8. It printed the plaintext

Debugging output was never removed. Key generation logged progress, the
public key was echoed, and `decrypt` contained:

```python
print(c)  # c is the decrypted message polynomial
```

Round-tripping an eleven-character message wrote about 3,700 characters to
standard output, including the secret it had just recovered.

**Lesson:** a library should be silent. Related: `repr()` of a Phoenix
private key is `PrivateKey(phoenix677, <secret>)`, so a key that ends up in
a log line or a traceback does not expose itself.

## 9. Errors were swallowed

```python
try:
    return np.array(poly(invert(...)).all_coeffs(), dtype=int)
except:
    return np.array([])
```

A bare `except` catches everything, including typos and Ctrl+C, and here
turned all of it into "this polynomial is not invertible, try another".
A genuine bug would have looked like bad luck, for a hundred attempts, and
then key generation would have silently finished with an all-zero key.

**Lesson:** catch the one exception you expect. `poly.invert` raises
`NotInvertibleError`, key generation catches exactly that, and running out
of attempts is an error rather than a zero key.

## 10. It was only the textbook scheme

The code implemented $e = r \star h + m$ directly on message bits. That is
malleable and falls to chosen-ciphertext attacks, as the
[previous post](03-from-textbook-to-usable.md) shows in detail. Nothing
warned a user about it; the README described the project as "robust
protection".

**Lesson:** the hard problem is the easy part. Version 1.0 keeps the
textbook layer for study, clearly labelled, and puts a KEM and an
authenticated cipher on top for anything resembling use. It also stopped
describing itself as protection: it is a learning project and says so in
the first paragraph of every entry point.

## 11. The packaging described a different project

`requirements.txt` pinned eleven packages, among them `requests`, `PyYAML`,
`Naked` and `shellescape`, none of which were imported. The usage section of
the README read, in full, "TBC".

**Lesson:** `pip freeze > requirements.txt` records your environment, not
your dependencies. Phoenix now declares two, in `pyproject.toml`: NumPy and
`cryptography`.

## 12. The documentation disagreed with the code

The notes defined the public key as $h = g \star f_q$ and encryption as
$e = p\, r \star h + m$, while the code computed $h = p\, f_q \star g$ and
$e = r \star h + m$. Both conventions are valid and give the same
ciphertexts, but a reader comparing the two would be lost. The definition of
an ideal had a typo that changed its meaning, the set of secret polynomials
was defined as binary while the example used ternary ones, and the
explanation of decryption was a screenshot.

**Lesson:** documentation rots unless something executes it. The worked
example in the new docs is also a test
(`tests/test_ntru.py::test_worked_example`), the same example is one click
away in the playground, and every snippet in these posts was produced by
running it.

## What changed besides the bugs

**Speed.** SymPy manipulates polynomials symbolically, which is general and
slow. Storing coefficients in NumPy arrays and writing the two algorithms
that matter (cyclic convolution and inversion) directly made a large
difference. Measured on the same machine at comparable sizes:

| | Original (N = 503) | 1.0 (N = 677) |
| --- | ---: | ---: |
| Key generation | 0.7 s | about 10 ms |
| Encrypt + decrypt, short message | 0.4 s | about 1 ms |

**Shape.** Three scripts became a package with one job per module:

```
poly        ring arithmetic
params      validated parameter sets
sampling    randomness
ntru        the textbook trapdoor
kem         key encapsulation
sealing     hybrid encryption of bytes
encoding    serialization
cli         the phoenix command
playground  the local web UI
```

**A way to play with it.** `phoenix playground` opens a local page where
you can generate keys, seal and unseal, flip bits, and step through the toy
example row by row.

## If you take one thing away

Most of these twelve problems have nothing to do with lattices. They are
an off-by-one, an unchecked return value, a swallowed exception, a stray
`print`, a wrong random number generator. Cryptographic code fails in the
same ways as any other code. The difference is that it fails silently, and
someone may be looking for the failure.

That is also the honest reason Phoenix still calls itself a learning
project. Fixing every bug you know about is not the same as review by people
whose job is to find the ones you do not.
