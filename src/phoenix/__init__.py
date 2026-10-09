"""Phoenix: an educational NTRU lattice-based encryption library.

Typical use::

    import phoenix

    public_key, private_key = phoenix.generate_keypair()
    sealed = phoenix.seal(public_key, b"attack at dawn")
    assert phoenix.unseal(private_key, sealed) == b"attack at dawn"

Phoenix has not been audited and is not constant time.  Do not use it to
protect real secrets.
"""

from . import encoding, kem, ntru, params, poly
from .encoding import (
    armor,
    dearmor,
    decode_private_key,
    decode_public_key,
    encode_private_key,
    encode_public_key,
)
from .errors import (
    DecryptionError,
    FormatError,
    NotInvertibleError,
    ParameterError,
    PhoenixError,
)
from .kem import decapsulate, encapsulate
from .ntru import PrivateKey, PublicKey, generate_keypair
from .params import DEFAULT, PHOENIX509, PHOENIX677, PHOENIX821, TOY, ParameterSet
from .sealing import seal, unseal

__version__ = "1.0.0"

__all__ = [
    "DEFAULT",
    "PHOENIX509",
    "PHOENIX677",
    "PHOENIX821",
    "TOY",
    "DecryptionError",
    "FormatError",
    "NotInvertibleError",
    "ParameterError",
    "ParameterSet",
    "PhoenixError",
    "PrivateKey",
    "PublicKey",
    "armor",
    "dearmor",
    "decapsulate",
    "decode_private_key",
    "decode_public_key",
    "encapsulate",
    "encode_private_key",
    "encode_public_key",
    "encoding",
    "generate_keypair",
    "kem",
    "ntru",
    "params",
    "poly",
    "seal",
    "unseal",
]
