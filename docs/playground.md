# Playground

The playground is a small web page for experimenting with Phoenix without
writing code. It runs entirely on your machine and calls the real library, so
what you see is what the Python API does.

```console
$ phoenix playground
Phoenix playground running at http://127.0.0.1:8765/  (Ctrl+C to stop)
```

Your browser opens automatically. Use `--port` to pick another port and
`--no-browser` to only print the address.

## Tabs

### Encrypt & decrypt

1. **Keys** — pick a parameter set and generate a pair, or paste keys you
   made with `phoenix keygen`.
2. **Seal** — type a message (and optional associated data) and seal it to
   the public key. The status line reports the sizes and time taken.
3. **Unseal** — decrypt with the private key.

Things worth trying:

- Press **Flip a random bit**, then **Unseal**. Authentication fails, no
  matter which bit was hit.
- Seal the same message twice. The outputs differ completely, because every
  seal uses fresh randomness.
- Seal with associated data `a`, change the field to `b`, then unseal.
- Generate a second key pair, keep the old sealed message, and unseal.

### Step through the maths

Runs textbook NTRU on the toy parameters (N = 7, p = 3, q = 41) and prints
every intermediate polynomial: `f`, `g`, both inverses, the public key `h`,
the ciphertext `e`, and each stage of decryption.

Leave the inputs empty for random values, or enter up to seven coefficients
from the constant term upwards. **Load the docs example** fills in the values
used in [The NTRU algorithm](algorithm.md#worked-example) so you can follow
along. Compare the rows `a` and `p·r·g + f·m`: they are identical, which is
the whole reason decryption works.

### Test & benchmark

Runs the number of rounds you ask for. Each round generates a new key pair,
encapsulates, decapsulates and checks that both sides derived the same
secret, then flips one bit of the ciphertext and checks that the secret
changes. You get pass counts and mean/min/max timings for each operation.

### Parameter sets

Lists the built-in sets with their sizes, and the worst-case coefficient next
to the limit it must stay under (see
[why decryption never fails](algorithm.md#why-decryption-never-fails)).

## Safety notes

- The server binds to `127.0.0.1` only and rejects requests whose `Host`
  header is not `localhost` or `127.0.0.1`.
- Keys and messages are posted to that local server in plain HTTP. That is
  fine for experiments; do not paste keys you rely on.
- Nothing is saved to disk and nothing leaves your machine. The page loads no
  external scripts, fonts or styles.

## HTTP API

The page talks to a JSON API you can also call yourself. All endpoints are
`POST` with a JSON object body; errors come back as status 400 with
`{"error": "…"}`.

| Endpoint | Body | Returns |
| --- | --- | --- |
| `/api/params` | `{}` | every built-in parameter set with sizes |
| `/api/keygen` | `{"params": "phoenix677"}` | armored `public` and `private`, sizes, `ms` |
| `/api/seal` | `{"public", "plaintext", "aad"}` | armored `sealed`, sizes, `ms` |
| `/api/unseal` | `{"private", "sealed", "aad"}` | `plaintext`, `ms` |
| `/api/tamper` | `{"sealed"}` | `sealed` with one bit flipped, and which `byte`/`bit` |
| `/api/toy` | optional `f`, `g`, `m`, `r` | `steps`, `ok`, `largest_coefficient` |
| `/api/benchmark` | `{"params", "rounds"}` | pass counts and `timings` |

```console
$ curl -s -X POST http://127.0.0.1:8765/api/benchmark \
       -d '{"params": "phoenix509", "rounds": 10}'
```
