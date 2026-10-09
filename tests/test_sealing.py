import pytest

import phoenix
from phoenix import encoding, params, sealing
from phoenix.errors import DecryptionError, FormatError


@pytest.mark.parametrize("size", [0, 1, 31, 1000, 100_000])
def test_round_trip(keypair, size):
    public_key, private_key = keypair
    message = bytes(i % 251 for i in range(size))
    sealed = phoenix.seal(public_key, message)
    assert len(sealed) == size + sealing.overhead(public_key.params)
    assert phoenix.unseal(private_key, sealed) == message


def test_unicode_text(default_keypair):
    public_key, private_key = default_keypair
    text = "Fénix 🔥 — 不死鳥"
    assert phoenix.unseal(private_key, phoenix.seal(public_key, text.encode())).decode() == text


def test_sealing_is_randomised(default_keypair):
    public_key, _ = default_keypair
    assert phoenix.seal(public_key, b"same") != phoenix.seal(public_key, b"same")


def test_associated_data_must_match(default_keypair):
    public_key, private_key = default_keypair
    sealed = phoenix.seal(public_key, b"payload", b"invoice-17")
    assert phoenix.unseal(private_key, sealed, b"invoice-17") == b"payload"
    with pytest.raises(DecryptionError):
        phoenix.unseal(private_key, sealed, b"invoice-18")
    with pytest.raises(DecryptionError):
        phoenix.unseal(private_key, sealed)


def test_any_tampering_is_detected(default_keypair):
    public_key, private_key = default_keypair
    sealed = phoenix.seal(public_key, b"do not touch")
    positions = [encoding.HEADER_SIZE, len(sealed) // 2, len(sealed) - 20, len(sealed) - 1]
    for position in positions:
        tampered = bytearray(sealed)
        tampered[position] ^= 0x01
        with pytest.raises(DecryptionError):
            phoenix.unseal(private_key, bytes(tampered))


def test_truncation_and_extension_are_detected(default_keypair):
    public_key, private_key = default_keypair
    sealed = phoenix.seal(public_key, b"do not touch")
    with pytest.raises(DecryptionError):
        phoenix.unseal(private_key, sealed[:-1])
    with pytest.raises(DecryptionError):
        phoenix.unseal(private_key, sealed + b"\0")
    with pytest.raises(FormatError, match="truncated"):
        phoenix.unseal(private_key, sealed[: encoding.HEADER_SIZE + 40])


def test_wrong_key_fails(default_keypair):
    public_key, _ = default_keypair
    _, other = phoenix.generate_keypair(seed=b"someone else")
    with pytest.raises(DecryptionError):
        phoenix.unseal(other, phoenix.seal(public_key, b"secret"))


def test_wrong_parameter_set_fails(default_keypair):
    public_key, _ = default_keypair
    _, other = phoenix.generate_keypair(params.PHOENIX509, seed=b"p")
    with pytest.raises(DecryptionError, match="different parameter set"):
        phoenix.unseal(other, phoenix.seal(public_key, b"secret"))


def test_unseal_rejects_non_messages(default_keypair):
    public_key, private_key = default_keypair
    with pytest.raises(FormatError):
        phoenix.unseal(private_key, b"garbage")
    with pytest.raises(FormatError, match="expected a phoenix message"):
        phoenix.unseal(private_key, phoenix.encode_public_key(public_key))
