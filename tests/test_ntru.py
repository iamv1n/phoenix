import numpy as np
import pytest

import phoenix
from phoenix import ntru, params, poly
from phoenix.errors import NotInvertibleError
from phoenix.sampling import Xof, sample_ternary

# The worked example from docs/algorithm.md (coefficients from x^0 upwards).
F = [-1, 0, 1, 1, -1, 0, 1]
G = [0, -1, -1, 0, 1, 0, 1]
M = [1, -1, 1, 1, 0, -1, 0]
R = [-1, 1, 0, 0, 0, -1, 1]


def test_worked_example():
    public_key, private_key = ntru.keypair_from(params.TOY, F, G)
    assert poly.format_poly(private_key.fp) == "x^6 + 2x^5 + x^3 + x^2 + x + 1"
    assert poly.format_poly(public_key.h) == "19x^6 + 38x^5 + 6x^4 + 32x^3 + 24x^2 + 37x + 8"
    e = ntru.encrypt(public_key, M, R)
    assert poly.format_poly(e) == "31x^6 + 19x^5 + 4x^4 + 2x^3 + 40x^2 + 3x + 25"
    assert ntru.decrypt(private_key, e).tolist() == M


def test_keygen_is_deterministic_under_a_seed():
    assert phoenix.generate_keypair(params.TOY, seed=b"a") == phoenix.generate_keypair(
        params.TOY, seed=b"a"
    )
    assert phoenix.generate_keypair(params.TOY, seed=b"a") != phoenix.generate_keypair(
        params.TOY, seed=b"b"
    )


def test_keygen_is_random_by_default():
    assert (
        phoenix.generate_keypair(params.PHOENIX509)[0]
        != phoenix.generate_keypair(params.PHOENIX509)[0]
    )


def test_key_structure(keypair):
    public_key, private_key = keypair
    ps = public_key.params
    assert private_key.public_key == public_key
    assert (private_key.f == 1).sum() == ps.df + 1
    assert (private_key.f == -1).sum() == ps.df
    # f * h = p * g (mod q), so centering it must reveal a small polynomial.
    pg = poly.center(poly.convolve(private_key.f % ps.q, public_key.h, ps.q), ps.q)
    assert np.all(pg % ps.p == 0)
    g = pg // ps.p
    assert (g == 1).sum() == ps.dg and (g == -1).sum() == ps.dg


def test_keys_are_read_only_and_do_not_leak_in_repr(keypair):
    public_key, private_key = keypair
    with pytest.raises(ValueError):
        private_key.f[0] = 0
    with pytest.raises(ValueError):
        public_key.h[0] = 0
    assert "secret" in repr(private_key)
    assert str(private_key.f[:8].tolist())[1:-1] not in repr(private_key)


def test_encrypt_decrypt_random_messages(keypair):
    public_key, private_key = keypair
    ps = public_key.params
    xof = Xof(b"messages")
    for _ in range(25):
        m = np.array([xof.randbelow(3) - 1 for _ in range(ps.N)])
        assert np.array_equal(ntru.decrypt(private_key, ntru.encrypt(public_key, m)), m)


@pytest.mark.parametrize("value", [1, -1])
def test_extreme_messages_decrypt(keypair, value):
    # All-(+1) and all-(-1) messages push f*m as far from zero as it can go.
    public_key, private_key = keypair
    m = np.full(public_key.params.N, value)
    for _ in range(5):
        assert np.array_equal(ntru.decrypt(private_key, ntru.encrypt(public_key, m)), m)


def test_adversarial_r_and_m_stay_within_the_bound(keypair):
    # Align r with g and m with f to maximise a single coefficient of
    # p*r*g + f*m; decryption must still succeed.
    public_key, private_key = keypair
    ps = public_key.params
    f = np.asarray(private_key.f)
    g = poly.center(poly.convolve(f % ps.q, public_key.h, ps.q), ps.q) // ps.p

    def reverse(a):  # a(x) -> a(1/x)
        return np.concatenate([a[:1], a[:0:-1]])

    m = reverse(f)
    r = reverse(g)
    exact = ps.p * poly.convolve(r, g) + poly.convolve(f, m)
    assert exact[0] == ps.p * 2 * ps.dg + 2 * ps.df + 1 == ps.max_coefficient
    assert np.array_equal(ntru.decrypt(private_key, ntru.encrypt(public_key, m, r)), m)


def test_encryption_is_randomised(keypair):
    public_key, _ = keypair
    m = np.zeros(public_key.params.N, dtype=np.int64)
    assert not np.array_equal(ntru.encrypt(public_key, m), ntru.encrypt(public_key, m))


def test_encrypt_validates_inputs():
    public_key, _ = ntru.keypair_from(params.TOY, F, G)
    with pytest.raises(ValueError, match="message coefficients"):
        ntru.encrypt(public_key, [2, 0, 0])
    with pytest.raises(ValueError, match="ternary"):
        ntru.encrypt(public_key, M, [2, 0, 0])
    with pytest.raises(ValueError):
        ntru.encrypt(public_key, [0] * 8)


def test_keypair_from_rejects_non_invertible_f():
    with pytest.raises(NotInvertibleError):
        ntru.keypair_from(params.TOY, [-1, 1], G)


def test_private_key_validation():
    public_key, private_key = ntru.keypair_from(params.TOY, F, G)
    with pytest.raises(ValueError, match="ternary"):
        ntru.PrivateKey(params.TOY, [2, 0, 1], public_key, bytes(32))
    with pytest.raises(ValueError, match="32 bytes"):
        ntru.PrivateKey(params.TOY, F, public_key, b"short")
    other = phoenix.generate_keypair(params.PHOENIX509, seed=b"x")[0]
    with pytest.raises(ValueError, match="different parameter set"):
        ntru.PrivateKey(params.TOY, F, other, bytes(32))
    with pytest.raises(ValueError, match=r"\[0, q\)"):
        ntru.PublicKey(params.TOY, [41, 0, 0])


def test_textbook_ntru_is_malleable():
    # Why applications must not use this layer directly: adding x^k to a
    # ciphertext adds x^k to the plaintext.
    public_key, private_key = ntru.keypair_from(params.TOY, F, G)
    m = np.array([0, 1, 0, 0, -1, 0, 0])
    e = ntru.encrypt(public_key, m)
    e[0] = (e[0] + 1) % params.TOY.q
    assert ntru.decrypt(private_key, e).tolist() == [1, 1, 0, 0, -1, 0, 0]


def test_sample_blinding_weights():
    r = ntru.sample_blinding(params.PHOENIX677)
    assert (r == 1).sum() == (r == -1).sum() == params.PHOENIX677.dr
    assert sample_ternary(7, 2, 2, Xof(b"q")).sum() == 0
