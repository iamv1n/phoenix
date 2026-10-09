from collections import Counter

import pytest

from phoenix.sampling import Xof, sample_ternary


def test_xof_is_deterministic_and_streams():
    a, b = Xof(b"seed"), Xof(b"seed")
    assert a.read(10) + a.read(3000) == b.read(3010)
    assert Xof(b"seed").read(32) != Xof(b"other").read(32)


def test_unseeded_xof_is_random():
    assert Xof().read(32) != Xof().read(32)


def test_randbelow_range_and_coverage():
    xof = Xof(b"r")
    counts = Counter(xof.randbelow(5) for _ in range(5000))
    assert set(counts) == {0, 1, 2, 3, 4}
    assert all(800 < c < 1200 for c in counts.values())
    assert all(Xof(b"one").randbelow(1) == 0 for _ in range(10))


@pytest.mark.parametrize("N, ones, minus", [(7, 3, 2), (509, 128, 127), (11, 0, 0), (6, 3, 3)])
def test_sample_ternary_weights(N, ones, minus):
    a = sample_ternary(N, ones, minus)
    assert len(a) == N
    assert (a == 1).sum() == ones
    assert (a == -1).sum() == minus
    assert (a == 0).sum() == N - ones - minus


def test_sample_ternary_is_deterministic_under_a_seed():
    assert (sample_ternary(101, 20, 20, Xof(b"s")) == sample_ternary(101, 20, 20, Xof(b"s"))).all()
    assert (sample_ternary(101, 20, 20, Xof(b"s")) != sample_ternary(101, 20, 20, Xof(b"t"))).any()


def test_sample_ternary_positions_are_roughly_uniform():
    xof = Xof(b"uniform")
    hits = [0] * 7
    for _ in range(7000):
        for i, c in enumerate(sample_ternary(7, 1, 0, xof)):
            hits[i] += int(c)
    assert all(850 < h < 1150 for h in hits)


def test_sample_ternary_rejects_impossible_weights():
    with pytest.raises(ValueError):
        sample_ternary(5, 3, 3)
