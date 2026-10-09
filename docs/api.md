# API reference

```python
import phoenix
```

Everything most programs need is available at the top level. The lower-level
modules are documented further down.

- [Keys](#keys)
- [Sealing](#sealing)
- [Key encapsulation](#key-encapsulation)
- [Serialization](#serialization)
- [Parameter sets](#parameter-sets)
- [Errors](#errors)
- [`phoenix.ntru` — textbook NTRU](#phoenixntru--textbook-ntru)
- [`phoenix.poly` — ring arithmetic](#phoenixpoly--ring-arithmetic)
- [`phoenix.sampling` — randomness](#phoenixsampling--randomness)
- [`phoenix.playground`](#phoenixplayground)

## Keys

### `generate_keypair(params=DEFAULT, *, seed=None) -> (PublicKey, PrivateKey)`

Generate a key pair. Takes roughly 10 ms for the default set.

`seed` (bytes) makes generation deterministic. It is for tests and worked
examples; leave it unset for real keys.

```python
public_key, private_key = phoenix.generate_keypair()
public_key, private_key = phoenix.generate_keypair(phoenix.PHOENIX821)
```

### `PublicKey`

| Attribute | Type | Meaning |
| --- | --- | --- |
| `params` | `ParameterSet` | The parameter set |
| `h` | read-only `ndarray` | Coefficients of $h$, in $[0, q)$, constant term first |

Supports `==` and hashing.

### `PrivateKey`

| Attribute | Type | Meaning |
| --- | --- | --- |
| `params` | `ParameterSet` | The parameter set |
| `f` | read-only `ndarray` | The secret ternary polynomial |
| `fp` | read-only `ndarray` | $f^{-1} \bmod p$ |
| `public_key` | `PublicKey` | The matching public key |
| `rejection_secret` | `bytes` | 32 bytes used for implicit rejection |

`repr()` of a private key never includes key material, so it is safe to end
up in a log line.

## Sealing

### `seal(public_key, plaintext, associated_data=b"") -> bytes`

Encrypt `plaintext` (bytes) to `public_key`. The result is `len(plaintext)`
plus a fixed overhead (966 bytes for the default set) and is different every
time.

`associated_data` is authenticated but neither encrypted nor included in the
output.

### `unseal(private_key, sealed, associated_data=b"") -> bytes`

Decrypt a sealed message.

Raises:

- `DecryptionError` if the message does not authenticate: wrong key,
  modified message, wrong associated data, or a different parameter set.
- `FormatError` if `sealed` is not a Phoenix sealed message at all.

```python
sealed = phoenix.seal(public_key, b"hello", b"context")
phoenix.unseal(private_key, sealed, b"context")  # b'hello'
```

### `phoenix.sealing.overhead(params) -> int`

Bytes added by `seal` for a parameter set.

## Key encapsulation

### `encapsulate(public_key, *, seed=None) -> (ciphertext, shared_secret)`

Generate a random 32-byte shared secret and a ciphertext that transports it.
Both are `bytes`.

### `decapsulate(private_key, ciphertext) -> bytes`

Recover the shared secret.

If `ciphertext` was not produced by `encapsulate` for this key, the function
does **not** raise: it returns a different, unpredictable 32-byte value
(implicit rejection). Your protocol finds out when the two sides' keys
disagree. Compare secrets only through authenticated use, never by sending
them.

Raises `FormatError` only for input that is structurally invalid: wrong
length or out-of-range coefficients.

### `phoenix.kem.ciphertext_size(params) -> int`

Length of a KEM ciphertext in bytes.

### `phoenix.kem.SHARED_SECRET_SIZE`

`32`.

## Serialization

| Function | Converts |
| --- | --- |
| `encode_public_key(public_key) -> bytes` | key to binary |
| `decode_public_key(data) -> PublicKey` | binary to key |
| `encode_private_key(private_key) -> bytes` | key to binary |
| `decode_private_key(data) -> PrivateKey` | binary to key |
| `armor(data) -> str` | any encoded object to PEM-style text |
| `dearmor(text) -> bytes` | PEM-style text back to binary |
| `phoenix.encoding.load(data) -> bytes` | binary *or* armored input to binary |

Decoders raise `FormatError` on anything malformed, including an object of
the wrong kind:

```python
>>> phoenix.decode_private_key(phoenix.encode_public_key(public_key))
Traceback (most recent call last):
  ...
phoenix.errors.FormatError: expected a phoenix private key, got a phoenix public key
```

The byte layout is specified in [File formats](formats.md).

## Parameter sets

### Constants

`PHOENIX509`, `PHOENIX677`, `PHOENIX821`, `TOY`, and `DEFAULT`
(= `PHOENIX677`).

### `ParameterSet(name, N, p, q, df, dg, dr)`

An immutable parameter set, validated on construction. Raises
`ParameterError` if:

- `N` is not an odd prime (or is 4096 or more),
- `p` is not an odd prime below 256,
- `q` is not a prime power, exceeds $2^{20}$, or shares a factor with `p`,
- a weight does not fit in `N` coefficients,
- decryption could fail (see
  [the bound](algorithm.md#why-decryption-never-fails)).

| Property | Meaning |
| --- | --- |
| `dm` | `N // 3`; KEM messages are drawn from $T(d_m, d_m)$ |
| `max_coefficient` | Worst-case coefficient of $p r \star g + f \star m$ |
| `q_bits` | Bits per packed coefficient |

```python
mine = phoenix.ParameterSet("mine", N=11, p=3, q=64, df=3, dg=3, dr=3)
public_key, private_key = phoenix.generate_keypair(mine)
```

Custom sets work everywhere and survive serialization (they come back named
`custom`). Passing validation says nothing about security.

### `phoenix.params.get(name) -> ParameterSet`

Look up a built-in set by case-insensitive name.

### `phoenix.params.PARAMETER_SETS`

Dictionary of the built-in sets by name.

## Errors

```
PhoenixError
├── ParameterError       (also a ValueError)
├── NotInvertibleError   (also an ArithmeticError)
├── FormatError          (also a ValueError)
└── DecryptionError
```

Catch `PhoenixError` to handle anything Phoenix raises deliberately. Invalid
argument *values* in the low-level API (a message with coefficients out of
range, mismatched lengths) raise plain `ValueError`.

## `phoenix.ntru` — textbook NTRU

The raw trapdoor, for study. **Not safe for application use**: see
[KEM and sealing](kem-and-sealing.md#what-is-wrong-with-the-textbook-scheme).

Polynomials are array-likes of integers, constant term first, and may be
shorter than `N`.

### `keypair_from(params, f, g, rejection_secret=bytes(32)) -> (PublicKey, PrivateKey)`

Build a key pair from explicit polynomials, computing
$h = p f_q \star g \bmod q$. Raises `NotInvertibleError` if `f` has no
inverse modulo `p` or `q`.

### `encrypt(public_key, m, r=None) -> ndarray`

Return $e = r \star h + m \bmod q$. `m` must have coefficients in
$[-(p-1)/2, (p-1)/2]$. `r` defaults to a fresh random blinding polynomial.

### `decrypt(private_key, e) -> ndarray`

Return the message with centered coefficients.

### `sample_blinding(params, xof=None) -> ndarray`

Draw $r \in T(d_r, d_r)$.

```python
from phoenix import TOY, ntru

public_key, private_key = phoenix.generate_keypair(TOY)
e = ntru.encrypt(public_key, [1, 0, -1, 0, 1, -1, 0])
ntru.decrypt(private_key, e).tolist()  # [1, 0, -1, 0, 1, -1, 0]
```

## `phoenix.poly` — ring arithmetic

Operations in $\mathbb{Z}[x]/\langle x^N - 1 \rangle$ on `int64` arrays of
length `N`, constant term first.

| Function | Meaning |
| --- | --- |
| `as_poly(coeffs, N)` | Convert to a zero-padded array of length `N` |
| `convolve(a, b, modulus=None)` | $a \star b$, optionally reduced |
| `center(a, modulus)` | Representatives in $(-\text{modulus}/2, \text{modulus}/2]$ |
| `invert(a, modulus)` | $a^{-1}$ for a prime-power modulus; raises `NotInvertibleError` |
| `format_poly(a, variable="x")` | Human-readable string |
| `is_prime(n)`, `prime_power(n)` | Small number-theory helpers |

```python
>>> import numpy as np
>>> from phoenix import poly
>>> f = np.array([-1, 0, 1, 1, -1, 0, 1])
>>> poly.format_poly(f)
'x^6 - x^4 + x^3 + x^2 - 1'
>>> poly.format_poly(poly.invert(f, 3))
'x^6 + 2x^5 + x^3 + x^2 + x + 1'
>>> poly.convolve(f % 3, poly.invert(f, 3), 3).tolist()
[1, 0, 0, 0, 0, 0, 0]
```

## `phoenix.sampling` — randomness

### `Xof(seed=None)`

A deterministic byte stream built on SHAKE-256. Without a seed it draws 32
bytes from the operating system.

- `read(n) -> bytes`
- `randbelow(n) -> int`, uniform in `[0, n)` with no modulo bias

### `sample_ternary(N, ones, minus_ones, xof=None) -> ndarray`

A uniformly random ternary polynomial with exactly `ones` coefficients equal
to $+1$ and `minus_ones` equal to $-1$.

## `phoenix.playground`

### `serve(port=8765, open_browser=True)`

Run the [playground](playground.md) until interrupted.

### `make_server(port=8765) -> ThreadingHTTPServer`

Create the server without starting it; pass port `0` for a free port.
