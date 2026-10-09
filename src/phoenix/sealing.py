"""Hybrid public-key encryption of byte strings.

``seal`` encapsulates a fresh 256-bit key to the recipient and uses it once
with ChaCha20-Poly1305.  The lattice part only ever transports a random key;
the message itself is protected by a standard, well-studied AEAD.
"""

from __future__ import annotations

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from . import kem
from .encoding import HEADER_SIZE, KIND_SEALED, decode_header, encode_header
from .errors import DecryptionError, FormatError
from .ntru import PrivateKey, PublicKey
from .params import ParameterSet

# Each AEAD key comes from a fresh encapsulation and encrypts exactly one
# message, so a fixed nonce never repeats under the same key.
_NONCE = bytes(12)
_TAG_SIZE = 16


def overhead(params: ParameterSet) -> int:
    """Bytes a sealed message adds to its plaintext."""
    return HEADER_SIZE + kem.ciphertext_size(params) + _TAG_SIZE


def seal(public_key: PublicKey, plaintext: bytes, associated_data: bytes = b"") -> bytes:
    """Encrypt ``plaintext`` so only the holder of the private key can read it.

    ``associated_data`` is authenticated but not encrypted or stored; the
    same value must be supplied to :func:`unseal`.
    """
    header = encode_header(KIND_SEALED, public_key.params)
    kem_ciphertext, key = kem.encapsulate(public_key)
    bound = header + kem_ciphertext + associated_data
    return header + kem_ciphertext + ChaCha20Poly1305(key).encrypt(_NONCE, plaintext, bound)


def unseal(private_key: PrivateKey, sealed: bytes, associated_data: bytes = b"") -> bytes:
    """Decrypt a message produced by :func:`seal`.

    Raises :class:`~phoenix.errors.FormatError` if ``sealed`` is structurally
    invalid and :class:`~phoenix.errors.DecryptionError` if it does not
    authenticate under this key and ``associated_data``.
    """
    _, params = decode_header(sealed, KIND_SEALED)
    if params != private_key.params:
        raise DecryptionError("message was sealed for a different parameter set")
    split = HEADER_SIZE + kem.ciphertext_size(params)
    if len(sealed) < split + _TAG_SIZE:
        raise FormatError("sealed message is truncated")
    header, kem_ciphertext, body = sealed[:HEADER_SIZE], sealed[HEADER_SIZE:split], sealed[split:]

    key = kem.decapsulate(private_key, kem_ciphertext)
    bound = header + kem_ciphertext + associated_data
    try:
        return ChaCha20Poly1305(key).decrypt(_NONCE, body, bound)
    except InvalidTag:
        raise DecryptionError("message authentication failed") from None
