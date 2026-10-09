import stat
import subprocess
import sys

import pytest

from phoenix import cli


@pytest.fixture
def keys(tmp_path):
    base = tmp_path / "alice"
    assert cli.main(["keygen", "-o", str(base), "-p", "phoenix509"]) == 0
    return base.with_name("alice.pub"), base.with_name("alice.key")


def test_keygen_writes_armored_keys_with_safe_permissions(keys):
    public, private = keys
    assert public.read_text().startswith("-----BEGIN PHOENIX PUBLIC KEY-----")
    assert private.read_text().startswith("-----BEGIN PHOENIX PRIVATE KEY-----")
    if sys.platform != "win32":
        assert stat.S_IMODE(private.stat().st_mode) == 0o600


def test_keygen_refuses_to_overwrite(keys, capsys):
    public, _ = keys
    base = str(public)[: -len(".pub")]
    before = public.read_text()
    assert cli.main(["keygen", "-o", base]) == 1
    assert "already exists" in capsys.readouterr().err
    assert public.read_text() == before
    assert cli.main(["keygen", "-o", base, "-p", "phoenix509", "--force"]) == 0
    assert public.read_text() != before


@pytest.mark.parametrize("armor", [False, True])
def test_encrypt_decrypt_files(keys, tmp_path, armor):
    public, private = keys
    plain, sealed, out = tmp_path / "plain.txt", tmp_path / "sealed", tmp_path / "out.txt"
    plain.write_bytes(b"hello from the cli\n" * 100)
    args = ["encrypt", "-k", str(public), "-i", str(plain), "-o", str(sealed)]
    assert cli.main(args + (["--armor"] if armor else [])) == 0
    assert sealed.read_bytes().startswith(b"-----BEGIN PHOENIX MESSAGE" if armor else b"PHNX")
    assert cli.main(["decrypt", "-k", str(private), "-i", str(sealed), "-o", str(out)]) == 0
    assert out.read_bytes() == plain.read_bytes()


def test_aad_mismatch_fails_cleanly(keys, tmp_path, capsys):
    public, private = keys
    plain, sealed, out = tmp_path / "p", tmp_path / "s", tmp_path / "o"
    plain.write_bytes(b"x")
    assert (
        cli.main(["encrypt", "-k", str(public), "-i", str(plain), "-o", str(sealed), "--aad", "a"])
        == 0
    )
    assert (
        cli.main(["decrypt", "-k", str(private), "-i", str(sealed), "-o", str(out), "--aad", "b"])
        == 1
    )
    assert "authentication failed" in capsys.readouterr().err
    assert not out.exists()


def test_using_the_public_key_to_decrypt_is_a_clear_error(keys, tmp_path, capsys):
    public, _ = keys
    sealed = tmp_path / "s"
    plain = tmp_path / "p"
    plain.write_bytes(b"x")
    cli.main(["encrypt", "-k", str(public), "-i", str(plain), "-o", str(sealed)])
    assert cli.main(["decrypt", "-k", str(public), "-i", str(sealed)]) == 1
    assert "expected a phoenix private key" in capsys.readouterr().err


def test_missing_file_is_a_clean_error(capsys):
    assert cli.main(["info", "/nonexistent/file"]) == 1
    assert "phoenix: error:" in capsys.readouterr().err


def test_info_and_params(keys, capsys):
    public, private = keys
    assert cli.main(["info", str(public)]) == 0
    out = capsys.readouterr().out
    assert "public key" in out and "phoenix509" in out
    assert cli.main(["info", str(private)]) == 0
    assert "private key" in capsys.readouterr().out
    assert cli.main(["params"]) == 0
    out = capsys.readouterr().out
    assert "phoenix677" in out and "(default)" in out


def test_pipes_through_stdin_and_stdout(keys):
    public, private = keys

    def run(*args, data):
        command = [sys.executable, "-m", "phoenix", *args]
        return subprocess.run(command, input=data, capture_output=True, check=True).stdout

    sealed = run("encrypt", "-k", str(public), data=b"piped \x00 bytes")
    assert run("decrypt", "-k", str(private), data=sealed) == b"piped \x00 bytes"
