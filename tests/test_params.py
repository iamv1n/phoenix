import pytest

from phoenix import params
from phoenix.errors import ParameterError
from phoenix.params import ParameterSet


@pytest.mark.parametrize("ps", params.PARAMETER_SETS.values(), ids=lambda ps: ps.name)
def test_builtin_sets_cannot_fail_decryption(ps):
    assert ps.max_coefficient <= (ps.q - 1) // 2


def test_default_is_registered():
    assert params.get(params.DEFAULT.name) is params.DEFAULT
    assert params.get("PHOENIX509") is params.PHOENIX509


def test_unknown_name():
    with pytest.raises(ParameterError, match="unknown parameter set"):
        params.get("nope")


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"N": 9}, "N must be an odd prime"),
        ({"N": 2}, "N must be an odd prime"),
        ({"p": 2}, "p must be an odd prime"),
        ({"p": 4}, "p must be an odd prime"),
        ({"q": 12}, "q must be a prime power"),
        ({"q": 81}, "coprime"),
        ({"df": 4}, "df must satisfy"),
        ({"df": 0}, "df must satisfy"),
        ({"dg": 4}, "dg must satisfy"),
        ({"dr": 0}, "dr must satisfy"),
        ({"q": 32}, "decryption could fail"),
    ],
)
def test_validation(overrides, message):
    base = {"name": "t", "N": 7, "p": 3, "q": 41, "df": 2, "dg": 2, "dr": 2}
    with pytest.raises(ParameterError, match=message):
        ParameterSet(**{**base, **overrides})


def test_original_phoenix_defaults_are_rejected():
    # The first version shipped these; 3*36 + 123 = 231 does not fit below 257/2.
    with pytest.raises(ParameterError, match="decryption could fail"):
        ParameterSet("legacy", N=503, p=3, q=257, df=61, dg=20, dr=18)
