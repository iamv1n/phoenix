"""Exception hierarchy for Phoenix."""


class PhoenixError(Exception):
    """Base class for every error raised by Phoenix."""


class ParameterError(PhoenixError, ValueError):
    """A parameter set is malformed or would allow decryption failures."""


class NotInvertibleError(PhoenixError, ArithmeticError):
    """A polynomial has no inverse in the requested quotient ring."""


class FormatError(PhoenixError, ValueError):
    """Serialized data (key, ciphertext, sealed message) is malformed."""


class DecryptionError(PhoenixError):
    """A sealed message failed authentication.

    Raised for a wrong key, a corrupted or tampered message, or mismatched
    associated data. The cause is deliberately not distinguished.
    """
