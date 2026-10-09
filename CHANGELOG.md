# Changelog

## 1.0.0

A complete rewrite. No code or file format is shared with earlier versions;
see [Rebuilding Phoenix](blog/04-rebuilding-phoenix.md) for the reasons.

### Added

- `phoenix` package (`src/phoenix`), installable with `pip`.
- NumPy implementation of arithmetic in Z[x]/(x^N - 1), including inversion
  modulo primes and prime powers.
- Parameter sets `PHOENIX509`, `PHOENIX677` (default), `PHOENIX821` and
  `TOY`, validated so that decryption cannot fail.
- Key encapsulation with re-encryption check and implicit rejection.
- `seal` / `unseal`: authenticated hybrid encryption of bytes.
- Binary and PEM-style serialization for keys and messages.
- `phoenix` command: `keygen`, `encrypt`, `decrypt`, `info`, `params`,
  `playground`.
- Local web playground.
- Test suite, examples, documentation and blog.

### Removed

- `ph_encrypt.py`, `ph_decrypt.py`, `ph_util.py` and the SymPy dependency.
- `requirements.txt` (dependencies are declared in `pyproject.toml`).
