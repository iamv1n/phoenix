"""Key encapsulation built on textbook NTRU.

The raw trapdoor in :mod:`phoenix.ntru` is turned into a KEM with a
Fujisaki-Okamoto style transform:

* the message ``m`` is random, so there is no plaintext structure to exploit;
* the blinding polynomial ``r`` is *derived* from ``m`` and the public key,
  so the receiver can re-encrypt and check that a ciphertext is well formed;
* a ciphertext that fails the check yields a pseudorandom key derived from a
  private secret ("implicit rejection") rather than an error, so probing with
  malformed ciphertexts reveals nothing about ``f``.

The implementation is not constant time.
"""

from __future__ import annotations

import hashlib
import hmac

import numpy as np

from . import ntru
from .encoding import (
    encode_public_key,
    pack_coefficients,
    pack_trits,
    packed_size,
    unpack_coefficients,
)
from .ntru import PrivateKey, PublicKey
from .params import ParameterSet
from .sampling import Xof, sample_ternary

SHARED_SECRET_SIZE = 32

_DOMAIN_BLINDING = b"phoenix/v1/blinding"
_DOMAIN_KEY = b"phoenix/v1/key"
_DOMAIN_REJECT = b"phoenix/v1/reject"


def ciphertext_size(params: ParameterSet) -> int:
    """Length in bytes of a KEM ciphertext for ``params``."""
    return packed_size(params.N, params.q_bits)


def _hash(domain: bytes, *parts: bytes) -> bytes:
    h = hashlib.sha3_256(len(domain).to_bytes(1, "big") + domain)
    for part in parts:
        h.update(len(part).to_bytes(4, "big") + part)
    return h.digest()


def _derive_blinding(public_key: PublicKey, m_bytes: bytes) -> np.ndarray:
    seed = _hash(_DOMAIN_BLINDING, _hash(b"pk", encode_public_key(public_key)), m_bytes)
    return ntru.sample_blinding(public_key.params, Xof(seed))


def _encrypt(public_key: PublicKey, m: np.ndarray) -> tuple[bytes, bytes]:
    m_bytes = pack_trits(m)
    e = ntru.encrypt(public_key, m, _derive_blinding(public_key, m_bytes))
    return pack_coefficients(e, public_key.params.q_bits), m_bytes


def encapsulate(public_key: PublicKey, *, seed: bytes | None = None) -> tuple[bytes, bytes]:
    """Return ``(ciphertext, shared_secret)`` for ``public_key``.

    ``seed`` makes the result deterministic and exists only for tests and
    worked examples.
    """
    params = public_key.params
    m = sample_ternary(params.N, params.dm, params.dm, Xof(seed))
    ciphertext, m_bytes = _encrypt(public_key, m)
    return ciphertext, _hash(_DOMAIN_KEY, m_bytes, ciphertext)


def decapsulate(private_key: PrivateKey, ciphertext: bytes) -> bytes:
    """Recover the shared secret from ``ciphertext``.

    A ciphertext of the wrong length or with out-of-range coefficients raises
    :class:`~phoenix.errors.FormatError` (anyone can check that without the
    key).  Any other invalid ciphertext returns a pseudorandom secret.
    """
    params = private_key.params
    e = unpack_coefficients(ciphertext, params.N, params.q_bits, params.q)
    m = ntru.decrypt(private_key, e)

    well_formed = (
        np.abs(m).max() <= 1
        and int((m == 1).sum()) == params.dm
        and int((m == -1).sum()) == params.dm
    )
    # Re-encrypt unconditionally so both paths do the same amount of work.
    expected, m_bytes = _encrypt(private_key.public_key, np.clip(m, -1, 1))
    accept = _hash(_DOMAIN_KEY, m_bytes, ciphertext)
    reject = _hash(_DOMAIN_REJECT, private_key.rejection_secret, ciphertext)
    if well_formed and hmac.compare_digest(expected, ciphertext):
        return accept
    return reject
