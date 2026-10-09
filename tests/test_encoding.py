import numpy as np
import pytest

import phoenix
from phoenix import encoding, params
from phoenix.errors import FormatError
from phoenix.sampling import Xof, sample_ternary


@pytest.mark.parametrize("N, bits, modulus", [(7, 6, 41), (509, 11, 2048), (821, 12, 4096)])
def test_coefficient_packing_round_trip(N, bits, modulus):
    xof = Xof(b"pack")
    a = np.array([xof.randbelow(modulus) for _ in range(N)])
    packed = encoding.pack_coefficients(a, bits)
    assert len(packed) == encoding.packed_size(N, bits)
    assert np.array_equal(encoding.unpack_coefficients(packed, N, bits, modulus), a)


def test_unpack_coefficients_rejects_bad_input():
    packed = encoding.pack_coefficients(np.array([40] * 7), 6)
    with pytest.raises(FormatError, match="wrong length"):
        encoding.unpack_coefficients(packed + b"\0", 7, 6, 41)
    with pytest.raises(FormatError, match="out of range"):
        encoding.unpack_coefficients(encoding.pack_coefficients(np.array([41] * 7), 6), 7, 6, 41)
    tampered = bytearray(packed)
    tampered[-1] |= 0x80
    with pytest.raises(FormatError, match="padding"):
        encoding.unpack_coefficients(bytes(tampered), 7, 6, 41)


@pytest.mark.parametrize("N", [5, 7, 509, 677])
def test_trit_packing_round_trip(N):
    a = sample_ternary(N, N // 3, N // 3, Xof(b"trits"))
    packed = encoding.pack_trits(a)
    assert len(packed) == encoding.trits_size(N)
    assert np.array_equal(encoding.unpack_trits(packed, N), a)


def test_unpack_trits_rejects_bad_input():
    with pytest.raises(FormatError, match="wrong length"):
        encoding.unpack_trits(b"\0", 7)
    with pytest.raises(FormatError, match="invalid ternary byte"):
        encoding.unpack_trits(bytes([243, 0]), 7)
    with pytest.raises(FormatError, match="padding"):
        encoding.unpack_trits(bytes([0, 27]), 7)


def test_key_round_trip(keypair):
    public_key, private_key = keypair
    public_bytes = phoenix.encode_public_key(public_key)
    private_bytes = phoenix.encode_private_key(private_key)
    assert phoenix.decode_public_key(public_bytes) == public_key
    restored = phoenix.decode_private_key(private_bytes)
    assert restored == private_key
    assert np.array_equal(restored.fp, private_key.fp)
    # Built-in sets come back as the named singleton.
    assert restored.params is public_key.params


def test_custom_parameters_survive_serialization():
    custom = params.ParameterSet("mine", N=11, p=3, q=64, df=3, dg=3, dr=3)
    public_key, private_key = phoenix.generate_keypair(custom, seed=b"c")
    restored = phoenix.decode_private_key(phoenix.encode_private_key(private_key))
    assert (restored.params.N, restored.params.q, restored.params.name) == (11, 64, "custom")
    sealed = phoenix.seal(phoenix.decode_public_key(phoenix.encode_public_key(public_key)), b"hi")
    assert phoenix.unseal(restored, sealed) == b"hi"


def test_armor_round_trip(keypair):
    public_key, private_key = keypair
    for raw, label in (
        (phoenix.encode_public_key(public_key), "PHOENIX PUBLIC KEY"),
        (phoenix.encode_private_key(private_key), "PHOENIX PRIVATE KEY"),
        (phoenix.seal(public_key, b"x"), "PHOENIX MESSAGE"),
    ):
        text = phoenix.armor(raw)
        assert text.startswith(f"-----BEGIN {label}-----\n")
        assert text.endswith(f"-----END {label}-----\n")
        assert phoenix.dearmor(text) == raw
        assert phoenix.dearmor(text.encode()) == raw
        assert encoding.load(text) == encoding.load(raw) == raw


def test_decode_rejects_wrong_kind(default_keypair):
    public_key, private_key = default_keypair
    with pytest.raises(FormatError, match="expected a phoenix private key"):
        phoenix.decode_private_key(phoenix.encode_public_key(public_key))
    with pytest.raises(FormatError, match="expected a phoenix public key"):
        phoenix.decode_public_key(phoenix.encode_private_key(private_key))


def test_header_validation(default_keypair):
    raw = phoenix.encode_public_key(default_keypair[0])
    with pytest.raises(FormatError, match="too short"):
        phoenix.decode_public_key(raw[:10])
    with pytest.raises(FormatError, match="bad magic"):
        phoenix.decode_public_key(b"NOPE" + raw[4:])
    with pytest.raises(FormatError, match="unsupported format version"):
        phoenix.decode_public_key(raw[:4] + b"\x09" + raw[5:])
    with pytest.raises(FormatError, match="unknown object kind"):
        phoenix.decode_public_key(raw[:5] + b"\x09" + raw[6:])
    with pytest.raises(FormatError, match="invalid parameters"):
        phoenix.decode_public_key(raw[:6] + b"\x00\x09" + raw[8:])  # N = 9
    with pytest.raises(FormatError, match="wrong length"):
        phoenix.decode_public_key(raw + b"\0")


def test_private_key_length_and_invertibility_checks():
    _, private_key = phoenix.generate_keypair(params.TOY, seed=b"k")
    raw = phoenix.encode_private_key(private_key)
    with pytest.raises(FormatError, match="wrong length"):
        phoenix.decode_private_key(raw[:-1])
    zero_f = raw[: encoding.HEADER_SIZE] + bytes(2) + raw[encoding.HEADER_SIZE + 2 :]
    with pytest.raises(FormatError, match="not invertible"):
        phoenix.decode_private_key(zero_f)


@pytest.mark.parametrize(
    "text, message",
    [
        ("hello", "missing armor header"),
        ("-----BEGIN PHOENIX PUBLIC KEY-----\nAAAA\n-----END NOPE-----", "footer"),
        ("-----BEGIN PHOENIX PUBLIC KEY-----\n!!!!\n-----END PHOENIX PUBLIC KEY-----", "base64"),
        (b"\xff\xfe", "not ASCII"),
    ],
)
def test_dearmor_rejects_garbage(text, message):
    with pytest.raises(FormatError, match=message):
        phoenix.dearmor(text)


def test_dearmor_rejects_mismatched_label(default_keypair):
    text = phoenix.armor(phoenix.encode_public_key(default_keypair[0]))
    with pytest.raises(FormatError, match="label does not match"):
        phoenix.dearmor(text.replace("PUBLIC", "PRIVATE"))
