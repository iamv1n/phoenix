import numpy as np
import pytest

from phoenix import poly
from phoenix.errors import NotInvertibleError, ParameterError
from phoenix.sampling import Xof, sample_ternary


def test_convolve_matches_docs_example():
    # (x^4 + 2x^3 + 3) * (x^4 + 3x^2 + x + 2) in Z_3[x]/(x^5 - 1)
    a = np.array([3, 0, 0, 2, 1])
    b = np.array([2, 1, 3, 0, 1])
    assert poly.convolve(a, b).tolist() == [13, 6, 11, 5, 7]
    assert poly.convolve(a, b, 3).tolist() == [1, 0, 2, 2, 1]


def test_convolve_wraps_x_to_the_n():
    x = np.array([0, 1, 0])
    x2 = np.array([0, 0, 1])
    assert poly.convolve(x, x2).tolist() == [1, 0, 0]


def test_convolve_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        poly.convolve(np.zeros(3, dtype=np.int64), np.zeros(4, dtype=np.int64))


@pytest.mark.parametrize(
    "modulus, expected",
    [(3, [0, 1, -1, 0, 1]), (4, [0, 1, 2, -1, 0]), (5, [0, 1, 2, -2, -1])],
)
def test_center(modulus, expected):
    assert poly.center(np.arange(5), modulus).tolist() == expected


@pytest.mark.parametrize("n", [2, 3, 5, 7, 41, 257, 509, 677, 821])
def test_is_prime_accepts_primes(n):
    assert poly.is_prime(n)


@pytest.mark.parametrize("n", [-7, 0, 1, 4, 9, 25, 49, 2048, 503 * 509])
def test_is_prime_rejects_composites_and_squares(n):
    assert not poly.is_prime(n)


@pytest.mark.parametrize(
    "n, expected",
    [(2, (2, 1)), (2048, (2, 11)), (41, (41, 1)), (243, (3, 5)), (12, None), (1, None)],
)
def test_prime_power(n, expected):
    assert poly.prime_power(n) == expected


@pytest.mark.parametrize("N", [7, 11, 61, 251])
@pytest.mark.parametrize("modulus", [2, 3, 41, 4, 27, 2048, 4096])
def test_invert_round_trip(N, modulus):
    xof = Xof(f"{N}-{modulus}".encode())
    one = np.zeros(N, dtype=np.int64)
    one[0] = 1
    found = 0
    for _ in range(20):
        f = sample_ternary(N, N // 4 + 1, N // 4, xof)
        try:
            inverse = poly.invert(f, modulus)
        except NotInvertibleError:
            continue
        found += 1
        assert inverse.min() >= 0 and inverse.max() < modulus
        assert np.array_equal(poly.convolve(f % modulus, inverse, modulus), one)
    assert found > 0


def test_invert_rejects_zero_divisor():
    # x - 1 divides x^N - 1, so it can never be inverted.
    f = poly.as_poly([-1, 1], 7)
    for modulus in (3, 41, 2048):
        with pytest.raises(NotInvertibleError):
            poly.invert(f, modulus)
    with pytest.raises(NotInvertibleError):
        poly.invert(np.zeros(7, dtype=np.int64), 3)


def test_invert_rejects_composite_modulus():
    with pytest.raises(ParameterError):
        poly.invert(poly.as_poly([1, 1], 7), 12)


@pytest.mark.parametrize(
    "coeffs, expected",
    [
        ([0, 0, 0], "0"),
        ([1], "1"),
        ([-1, 0, 1, 1, -1, 0, 1], "x^6 - x^4 + x^3 + x^2 - 1"),
        ([8, 37, 24], "24x^2 + 37x + 8"),
        ([0, -1], "-x"),
        ([0, 0, -3], "-3x^2"),
    ],
)
def test_format_poly(coeffs, expected):
    assert poly.format_poly(np.array(coeffs)) == expected


def test_as_poly_pads_and_validates():
    assert poly.as_poly([1, 2], 4).tolist() == [1, 2, 0, 0]
    with pytest.raises(ValueError):
        poly.as_poly([1, 2, 3], 2)
