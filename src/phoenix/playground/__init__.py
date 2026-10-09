"""A local web playground for experimenting with Phoenix.

``phoenix playground`` starts an HTTP server on the loopback interface and
serves a single page that drives the real library through a small JSON API.
It is a learning tool: keys you paste into it travel over localhost in the
clear, so do not use it with keys that matter.
"""

from __future__ import annotations

import json
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

import numpy as np

from .. import encoding, kem, ntru, poly, sealing
from .. import params as params_mod
from ..errors import PhoenixError
from ..sampling import Xof, sample_ternary

_MAX_BODY = 1 << 20
_MAX_BENCH_ROUNDS = 200


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def _params_info(ps: params_mod.ParameterSet) -> dict:
    return {
        "name": ps.name,
        "N": ps.N,
        "p": ps.p,
        "q": ps.q,
        "df": ps.df,
        "dg": ps.dg,
        "dr": ps.dr,
        "dm": ps.dm,
        "max_coefficient": ps.max_coefficient,
        "limit": (ps.q - 1) // 2,
        "public_key_bytes": encoding.HEADER_SIZE + kem.ciphertext_size(ps),
        "ciphertext_bytes": kem.ciphertext_size(ps),
        "seal_overhead_bytes": sealing.overhead(ps),
        "default": ps is params_mod.DEFAULT,
    }


def api_params(_: dict) -> dict:
    return {"params": [_params_info(ps) for ps in params_mod.PARAMETER_SETS.values()]}


def api_keygen(body: dict) -> dict:
    ps = params_mod.get(body.get("params", params_mod.DEFAULT.name))
    start = time.perf_counter()
    public_key, private_key = ntru.generate_keypair(ps)
    elapsed = _ms(start)
    public = encoding.encode_public_key(public_key)
    private = encoding.encode_private_key(private_key)
    return {
        "public": encoding.armor(public),
        "private": encoding.armor(private),
        "public_bytes": len(public),
        "private_bytes": len(private),
        "ms": elapsed,
    }


def api_seal(body: dict) -> dict:
    public_key = encoding.decode_public_key(encoding.load(body["public"]))
    plaintext = body.get("plaintext", "").encode()
    start = time.perf_counter()
    sealed = sealing.seal(public_key, plaintext, body.get("aad", "").encode())
    return {
        "sealed": encoding.armor(sealed),
        "sealed_bytes": len(sealed),
        "plaintext_bytes": len(plaintext),
        "ms": _ms(start),
    }


def api_unseal(body: dict) -> dict:
    private_key = encoding.decode_private_key(encoding.load(body["private"]))
    sealed = encoding.load(body["sealed"])
    start = time.perf_counter()
    plaintext = sealing.unseal(private_key, sealed, body.get("aad", "").encode())
    return {"plaintext": plaintext.decode("utf-8", errors="replace"), "ms": _ms(start)}


def api_tamper(body: dict) -> dict:
    """Flip one random bit after the header of a sealed message."""
    sealed = bytearray(encoding.load(body["sealed"]))
    encoding.decode_header(bytes(sealed), encoding.KIND_SEALED)
    position = encoding.HEADER_SIZE + secrets.randbelow(len(sealed) - encoding.HEADER_SIZE)
    bit = secrets.randbelow(8)
    sealed[position] ^= 1 << bit
    return {"sealed": encoding.armor(bytes(sealed)), "byte": position, "bit": bit}


def _parse_poly(text: str, N: int) -> np.ndarray:
    """Parse coefficients listed from the constant term upwards."""
    values = [int(token) for token in text.replace(",", " ").split()]
    if len(values) > N:
        raise PhoenixError(f"at most {N} coefficients are allowed")
    return poly.as_poly(values, N)


def api_toy(body: dict) -> dict:
    """Run textbook NTRU on the toy parameters and return every intermediate."""
    ps = params_mod.TOY
    xof = Xof()

    def given(key: str, ones: int, minus: int) -> np.ndarray:
        text = body.get(key, "").strip()
        if not text:
            return sample_ternary(ps.N, ones, minus, xof)
        value = _parse_poly(text, ps.N)
        if np.abs(value).max() > 1:
            raise PhoenixError(f"{key} must have coefficients in -1, 0, 1")
        return value

    for _ in range(100):
        f = given("f", ps.df + 1, ps.df)
        g = given("g", ps.dg, ps.dg)
        try:
            public_key, private_key = ntru.keypair_from(ps, f, g)
            break
        except ArithmeticError:
            if body.get("f", "").strip():
                raise PhoenixError("f is not invertible modulo p and q; try another") from None
    else:
        raise PhoenixError("could not find an invertible f")
    r = given("r", ps.dr, ps.dr)
    m = given("m", ps.dm, ps.dm)

    fq = poly.invert(f, ps.q)
    e = ntru.encrypt(public_key, m, r)
    a = poly.center(poly.convolve(f % ps.q, e, ps.q), ps.q)
    exact = ps.p * poly.convolve(r, g) + poly.convolve(f, m)
    b = poly.center(a, ps.p)
    recovered = ntru.decrypt(private_key, e)

    fmt = poly.format_poly
    return {
        "params": _params_info(ps),
        "steps": [
            {"label": "f", "note": "private, small", "value": fmt(f)},
            {"label": "g", "note": "private, small", "value": fmt(g)},
            {"label": "f_p", "note": "f⁻¹ mod p", "value": fmt(private_key.fp)},
            {"label": "f_q", "note": "f⁻¹ mod q", "value": fmt(fq)},
            {"label": "h", "note": "public key = p·f_q·g mod q", "value": fmt(public_key.h)},
            {"label": "m", "note": "message", "value": fmt(m)},
            {"label": "r", "note": "random blinding", "value": fmt(r)},
            {"label": "e", "note": "ciphertext = r·h + m mod q", "value": fmt(e)},
            {"label": "a", "note": "f·e mod q, centered", "value": fmt(a)},
            {"label": "p·r·g + f·m", "note": "over the integers", "value": fmt(exact)},
            {"label": "b", "note": "a mod p, centered", "value": fmt(b)},
            {"label": "f_p·b", "note": "recovered message", "value": fmt(recovered)},
        ],
        "coefficients": {
            "f": f.tolist(),
            "g": g.tolist(),
            "r": r.tolist(),
            "m": m.tolist(),
        },
        "largest_coefficient": int(np.abs(exact).max()),
        "no_wraparound": bool(np.array_equal(a, exact)),
        "ok": bool(np.array_equal(recovered, m)),
    }


def api_benchmark(body: dict) -> dict:
    """Time the KEM and count successful round trips and tamper rejections."""
    ps = params_mod.get(body.get("params", params_mod.DEFAULT.name))
    rounds = max(1, min(int(body.get("rounds", 20)), _MAX_BENCH_ROUNDS))
    timings = {"keygen": [], "encapsulate": [], "decapsulate": []}
    round_trips = tamper_rejected = 0
    for _ in range(rounds):
        start = time.perf_counter()
        public_key, private_key = ntru.generate_keypair(ps)
        timings["keygen"].append(_ms(start))
        start = time.perf_counter()
        ciphertext, secret = kem.encapsulate(public_key)
        timings["encapsulate"].append(_ms(start))
        start = time.perf_counter()
        recovered = kem.decapsulate(private_key, ciphertext)
        timings["decapsulate"].append(_ms(start))
        round_trips += recovered == secret

        tampered = bytearray(ciphertext)
        tampered[secrets.randbelow(len(tampered) - 1)] ^= 1 << secrets.randbelow(8)
        tamper_rejected += kem.decapsulate(private_key, bytes(tampered)) != secret
    return {
        "params": ps.name,
        "rounds": rounds,
        "round_trips": round_trips,
        "tamper_rejected": tamper_rejected,
        "timings": {
            name: {
                "mean": round(sum(values) / len(values), 3),
                "min": min(values),
                "max": max(values),
            }
            for name, values in timings.items()
        },
    }


ROUTES = {
    "/api/params": api_params,
    "/api/keygen": api_keygen,
    "/api/seal": api_seal,
    "/api/unseal": api_unseal,
    "/api/tamper": api_tamper,
    "/api/toy": api_toy,
    "/api/benchmark": api_benchmark,
}


class Handler(BaseHTTPRequestHandler):
    server_version = "PhoenixPlayground"

    def log_message(self, format: str, *args) -> None:
        pass

    def _local_request(self) -> bool:
        # Refuse requests addressed to another name (DNS rebinding).
        host = self.headers.get("Host", "").rsplit(":", 1)[0]
        return host in ("127.0.0.1", "localhost")

    def _send(self, status: int, content_type: str, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data: dict) -> None:
        self._send(status, "application/json", json.dumps(data).encode())

    def do_GET(self) -> None:
        if not self._local_request():
            return self._json(403, {"error": "forbidden"})
        if self.path in ("/", "/index.html"):
            page = resources.files(__package__).joinpath("index.html").read_bytes()
            return self._send(200, "text/html; charset=utf-8", page)
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self._local_request():
            return self._json(403, {"error": "forbidden"})
        route = ROUTES.get(self.path)
        if route is None:
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= _MAX_BODY:
                return self._json(413, {"error": "request too large"})
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")
            self._json(200, route(body))
        except (PhoenixError, ValueError, KeyError, TypeError) as exc:
            message = f"missing field {exc}" if isinstance(exc, KeyError) else str(exc)
            self._json(400, {"error": message})


def make_server(port: int = 8765) -> ThreadingHTTPServer:
    """Create the playground server bound to the loopback interface."""
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port: int = 8765, open_browser: bool = True) -> None:
    server = make_server(port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Phoenix playground running at {url}  (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
