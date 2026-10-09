# File formats

All multi-byte integers are big-endian. Format version 1 is described here.

## Header

Keys and sealed messages begin with the same 19-byte header, so every object
carries its own parameter set.

| Offset | Size | Field | Value |
| ---: | ---: | --- | --- |
| 0 | 4 | magic | `PHNX` |
| 4 | 1 | version | `1` |
| 5 | 1 | kind | `1` public key, `2` private key, `3` sealed message |
| 6 | 2 | N | |
| 8 | 1 | p | |
| 9 | 4 | q | |
| 13 | 2 | df | |
| 15 | 2 | dg | |
| 17 | 2 | dr | |

A decoder rejects headers whose parameters do not form a valid
`ParameterSet`. If the six numbers match a built-in set, that set is used;
otherwise the object gets a parameter set named `custom`.

## Polynomial encodings

**Packed coefficients** (for polynomials modulo $q$). Each coefficient, in
$[0, q)$, takes $b = \lceil \log_2 q \rceil$ bits. Coefficients are
concatenated starting with $x^0$, least significant bit first, and the bit
stream fills bytes from the least significant bit. Unused bits in the last
byte must be zero. Length: $\lceil N b / 8 \rceil$ bytes.

**Packed trits** (for ternary polynomials). Map $-1 \to 2$. Group
coefficients five at a time, starting with $x^0$, and store each group as the
byte $t_0 + 3t_1 + 9t_2 + 27t_3 + 81t_4$. Pad the final group with zeros.
Length: $\lceil N / 5 \rceil$ bytes.

Decoders reject non-canonical input: wrong lengths, coefficients $\ge q$,
bytes above 242, and non-zero padding.

## Public key

```
header (kind 1) | h, packed coefficients
```

## Private key

```
header (kind 2) | f, packed trits | h, packed coefficients | rejection secret, 32 bytes
```

$f_p$ is not stored; it is recomputed on load. A private key whose $f$ is
not invertible modulo $p$ is rejected.

## Sealed message

```
header (kind 3) | KEM ciphertext | ChaCha20-Poly1305 ciphertext and 16-byte tag
```

- The KEM ciphertext is $e$ as packed coefficients.
- The AEAD nonce is twelve zero bytes.
- The AEAD associated data is `header | KEM ciphertext | user associated data`.

## Sizes

| | `phoenix509` | `phoenix677` | `phoenix821` | `toy` |
| --- | ---: | ---: | ---: | ---: |
| Public key | 719 | 950 | 1251 | 25 |
| Private key | 853 | 1118 | 1448 | 59 |
| KEM ciphertext | 700 | 931 | 1232 | 6 |
| Sealed overhead | 735 | 966 | 1267 | 41 |

## Armor

Any object can be wrapped as text:

```
-----BEGIN PHOENIX PUBLIC KEY-----
<base64 of the binary object, 76 characters per line>
-----END PHOENIX PUBLIC KEY-----
```

The label is `PHOENIX PUBLIC KEY`, `PHOENIX PRIVATE KEY` or
`PHOENIX MESSAGE` and must agree with the `kind` byte inside.

## KEM derivations

The hash $H(\text{domain}, x_1, \dots, x_n)$ is SHA3-256 over

```
len(domain) as 1 byte | domain | len(x1) as 4 bytes | x1 | ... | len(xn) as 4 bytes | xn
```

| Value | Definition |
| --- | --- |
| blinding seed | `H("phoenix/v1/blinding", H("pk", encoded public key), trits(m))` |
| shared secret | `H("phoenix/v1/key", trits(m), ciphertext)` |
| rejection key | `H("phoenix/v1/reject", rejection secret, ciphertext)` |

**Sampling from a seed.** The byte stream is the concatenation, for
$i = 0, 1, 2, \dots$, of 1024 bytes of SHAKE-256 over
`i as 8 bytes | seed`. A uniform integer below $n$ is drawn by reading four
bytes as an integer $v$ and retrying while $v \ge 2^{32} - (2^{32} \bmod n)$,
then taking $v \bmod n$. A polynomial in $T(a, b)$ starts as $a$ ones, then
$b$ minus-ones, then zeros, and is shuffled by Fisher–Yates: for
$i = N-1$ down to $1$, swap positions $i$ and a uniform $j \le i$.
