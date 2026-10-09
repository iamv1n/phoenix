"""Command-line interface: ``phoenix keygen | encrypt | decrypt | info | params | playground``."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__, encoding, kem, sealing
from . import params as params_mod
from .errors import PhoenixError
from .ntru import generate_keypair


def _read(path: str) -> bytes:
    return sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()


def _write(path: str, data: bytes) -> None:
    if path == "-":
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    else:
        Path(path).write_bytes(data)


def _write_private(path: Path, data: bytes, force: bool) -> None:
    # Create with 0600 from the start so the key is never world-readable.
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL)
    with os.fdopen(os.open(path, flags, 0o600), "wb") as handle:
        handle.write(data)


def _cmd_keygen(args: argparse.Namespace) -> int:
    public_path = Path(f"{args.out}.pub")
    private_path = Path(f"{args.out}.key")
    if not args.force:
        for path in (public_path, private_path):
            if path.exists():
                raise PhoenixError(f"{path} already exists (use --force to overwrite)")
    public_key, private_key = generate_keypair(params_mod.get(args.params))
    _write_private(
        private_path, encoding.armor(encoding.encode_private_key(private_key)).encode(), args.force
    )
    public_path.write_text(encoding.armor(encoding.encode_public_key(public_key)))
    print(f"public key:  {public_path}", file=sys.stderr)
    print(f"private key: {private_path}  (keep this secret)", file=sys.stderr)
    return 0


def _cmd_encrypt(args: argparse.Namespace) -> int:
    public_key = encoding.decode_public_key(encoding.load(_read(args.key)))
    sealed = sealing.seal(public_key, _read(args.input), args.aad.encode())
    _write(args.output, encoding.armor(sealed).encode() if args.armor else sealed)
    return 0


def _cmd_decrypt(args: argparse.Namespace) -> int:
    private_key = encoding.decode_private_key(encoding.load(_read(args.key)))
    sealed = encoding.load(_read(args.input))
    _write(args.output, sealing.unseal(private_key, sealed, args.aad.encode()))
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    data = encoding.load(_read(args.file))
    kind, ps = encoding.decode_header(data)
    label = {
        encoding.KIND_PUBLIC_KEY: "public key",
        encoding.KIND_PRIVATE_KEY: "private key",
        encoding.KIND_SEALED: "sealed message",
    }[kind]
    print(f"type:       {label}")
    print(f"parameters: {ps}")
    print(f"size:       {len(data)} bytes")
    if kind == encoding.KIND_SEALED:
        print(f"plaintext:  {len(data) - sealing.overhead(ps)} bytes")
    return 0


def _cmd_params(_: argparse.Namespace) -> int:
    print(
        f"{'name':<12}{'N':>5}{'p':>3}{'q':>6}{'df':>5}{'dg':>5}{'dr':>5}"
        f"{'pk bytes':>10}{'ct bytes':>10}"
    )
    for ps in params_mod.PARAMETER_SETS.values():
        pk_size = encoding.HEADER_SIZE + kem.ciphertext_size(ps)
        default = "  (default)" if ps is params_mod.DEFAULT else ""
        print(
            f"{ps.name:<12}{ps.N:>5}{ps.p:>3}{ps.q:>6}{ps.df:>5}{ps.dg:>5}{ps.dr:>5}"
            f"{pk_size:>10}{kem.ciphertext_size(ps):>10}{default}"
        )
    return 0


def _cmd_playground(args: argparse.Namespace) -> int:
    from . import playground

    playground.serve(args.port, open_browser=not args.no_browser)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phoenix", description="Educational NTRU lattice-based encryption."
    )
    parser.add_argument("--version", action="version", version=f"phoenix {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    keygen = sub.add_parser("keygen", help="generate a key pair")
    keygen.add_argument("-o", "--out", default="phoenix", help="write OUT.pub and OUT.key")
    keygen.add_argument("-p", "--params", default=params_mod.DEFAULT.name, help="parameter set")
    keygen.add_argument("-f", "--force", action="store_true", help="overwrite existing files")
    keygen.set_defaults(func=_cmd_keygen)

    encrypt = sub.add_parser("encrypt", help="encrypt a file to a public key")
    encrypt.add_argument("-k", "--key", required=True, help="recipient public key file")
    encrypt.add_argument("-i", "--input", default="-", help="plaintext file (default: stdin)")
    encrypt.add_argument("-o", "--output", default="-", help="output file (default: stdout)")
    encrypt.add_argument("-a", "--armor", action="store_true", help="write base64 text")
    encrypt.add_argument("--aad", default="", help="associated data to authenticate")
    encrypt.set_defaults(func=_cmd_encrypt)

    decrypt = sub.add_parser("decrypt", help="decrypt a file with a private key")
    decrypt.add_argument("-k", "--key", required=True, help="private key file")
    decrypt.add_argument("-i", "--input", default="-", help="sealed file (default: stdin)")
    decrypt.add_argument("-o", "--output", default="-", help="output file (default: stdout)")
    decrypt.add_argument("--aad", default="", help="associated data used when encrypting")
    decrypt.set_defaults(func=_cmd_decrypt)

    info = sub.add_parser("info", help="describe a key or sealed message")
    info.add_argument("file")
    info.set_defaults(func=_cmd_info)

    listing = sub.add_parser("params", help="list built-in parameter sets")
    listing.set_defaults(func=_cmd_params)

    play = sub.add_parser("playground", help="open the local web playground")
    play.add_argument("--port", type=int, default=8765, help="port to listen on (default: 8765)")
    play.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    play.set_defaults(func=_cmd_playground)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (PhoenixError, OSError) as exc:
        print(f"phoenix: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
