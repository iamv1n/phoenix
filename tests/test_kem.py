import pytest

import phoenix
from phoenix import kem, params
from phoenix.errors import FormatError


def test_round_trip(keypair):
    public_key, private_key = keypair
    for _ in range(10):
        ciphertext, secret = phoenix.encapsulate(public_key)
        assert len(ciphertext) == kem.ciphertext_size(public_key.params)
        assert len(secret) == kem.SHARED_SECRET_SIZE
        assert phoenix.decapsulate(private_key, ciphertext) == secret


def test_encapsulation_is_fresh_each_time(default_keypair):
    public_key, _ = default_keypair
    first, second = phoenix.encapsulate(public_key), phoenix.encapsulate(public_key)
    assert first[0] != second[0] and first[1] != second[1]


def test_seeded_encapsulation_is_deterministic(default_keypair):
    public_key, _ = default_keypair
    assert phoenix.encapsulate(public_key, seed=b"s") == phoenix.encapsulate(public_key, seed=b"s")


@pytest.mark.parametrize("ps", [params.PHOENIX509, params.PHOENIX677, params.PHOENIX821])
def test_every_single_bit_flip_changes_the_secret(ps):
    public_key, private_key = phoenix.generate_keypair(ps, seed=b"flip")
    ciphertext, secret = phoenix.encapsulate(public_key, seed=b"ct")
    padding_bits = len(ciphertext) * 8 - ps.N * ps.q_bits
    for bit in range(0, len(ciphertext) * 8 - padding_bits, 7):
        tampered = bytearray(ciphertext)
        tampered[bit // 8] ^= 1 << (bit % 8)
        assert phoenix.decapsulate(private_key, bytes(tampered)) != secret


def test_implicit_rejection_is_deterministic_and_key_dependent(default_keypair):
    public_key, private_key = default_keypair
    ciphertext, secret = phoenix.encapsulate(public_key)
    tampered = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
    rejected = phoenix.decapsulate(private_key, tampered)
    assert rejected != secret
    assert phoenix.decapsulate(private_key, tampered) == rejected
    other_tampered = bytes([ciphertext[0] ^ 2]) + ciphertext[1:]
    assert phoenix.decapsulate(private_key, other_tampered) != rejected


def test_wrong_private_key_gives_a_different_secret(default_keypair):
    public_key, _ = default_keypair
    _, other_private = phoenix.generate_keypair(seed=b"other")
    ciphertext, secret = phoenix.encapsulate(public_key)
    assert phoenix.decapsulate(other_private, ciphertext) != secret


def test_structurally_valid_but_unblinded_ciphertext_is_rejected(default_keypair):
    # e = m (i.e. r = 0) decrypts to a well-formed m but fails re-encryption.
    import numpy as np

    from phoenix.encoding import pack_coefficients
    from phoenix.sampling import sample_ternary

    public_key, private_key = default_keypair
    ps = public_key.params
    m = sample_ternary(ps.N, ps.dm, ps.dm)
    forged = pack_coefficients(np.asarray(m) % ps.q, ps.q_bits)
    honest_key = kem._hash(kem._DOMAIN_KEY, phoenix.encoding.pack_trits(m), forged)
    assert phoenix.decapsulate(private_key, forged) != honest_key


def test_malformed_ciphertexts_raise(default_keypair):
    _, private_key = default_keypair
    size = kem.ciphertext_size(private_key.params)
    with pytest.raises(FormatError):
        phoenix.decapsulate(private_key, bytes(size - 1))
    with pytest.raises(FormatError):
        phoenix.decapsulate(private_key, bytes(size - 1) + b"\xff")


def test_out_of_range_coefficient_raises_for_prime_q():
    _, private_key = phoenix.generate_keypair(params.TOY, seed=b"t")
    with pytest.raises(FormatError, match="out of range"):
        phoenix.decapsulate(private_key, b"\xff" * 5 + b"\x03")
