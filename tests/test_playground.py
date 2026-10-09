import json
import threading
import urllib.error
import urllib.request

import pytest

from phoenix import playground


@pytest.fixture(scope="module")
def base_url():
    server = playground.make_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def post(base_url, path, body, headers=None):
    request = urllib.request.Request(
        base_url + path, data=json.dumps(body).encode(), headers=headers or {}, method="POST"
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_serves_the_page(base_url):
    with urllib.request.urlopen(base_url + "/") as response:
        assert response.status == 200
        assert b"Phoenix Playground" in response.read()


def test_full_flow_including_tamper(base_url):
    _, keys = post(base_url, "/api/keygen", {"params": "phoenix509"})
    _, sealed = post(
        base_url, "/api/seal", {"public": keys["public"], "plaintext": "héllo", "aad": "ctx"}
    )
    request = {"private": keys["private"], "sealed": sealed["sealed"], "aad": "ctx"}
    assert post(base_url, "/api/unseal", request) == (
        200,
        {"plaintext": "héllo", "ms": pytest.approx(0, abs=1000)},
    )

    _, tampered = post(base_url, "/api/tamper", {"sealed": sealed["sealed"]})
    status, result = post(base_url, "/api/unseal", {**request, "sealed": tampered["sealed"]})
    assert status == 400 and "authentication failed" in result["error"]


def test_toy_reproduces_the_docs_example(base_url):
    body = {
        "f": "-1 0 1 1 -1 0 1",
        "g": "0 -1 -1 0 1 0 1",
        "m": "1 -1 1 1 0 -1 0",
        "r": "-1 1 0 0 0 -1 1",
    }
    status, result = post(base_url, "/api/toy", body)
    assert status == 200 and result["ok"] and result["no_wraparound"]
    steps = {step["label"]: step["value"] for step in result["steps"]}
    assert steps["h"] == "19x^6 + 38x^5 + 6x^4 + 32x^3 + 24x^2 + 37x + 8"
    assert steps["e"] == "31x^6 + 19x^5 + 4x^4 + 2x^3 + 40x^2 + 3x + 25"
    assert steps["f_p·b"] == steps["m"] == "-x^5 + x^3 + x^2 - x + 1"


def test_toy_with_random_inputs_always_decrypts(base_url):
    for _ in range(20):
        status, result = post(base_url, "/api/toy", {})
        assert status == 200 and result["ok"]


def test_toy_rejects_bad_input(base_url):
    assert post(base_url, "/api/toy", {"f": "-1 1"})[0] == 400
    assert post(base_url, "/api/toy", {"m": "5"})[0] == 400
    assert post(base_url, "/api/toy", {"m": "abc"})[0] == 400


def test_benchmark(base_url):
    status, result = post(base_url, "/api/benchmark", {"params": "phoenix509", "rounds": 3})
    assert status == 200
    assert result["round_trips"] == result["tamper_rejected"] == result["rounds"] == 3
    assert set(result["timings"]) == {"keygen", "encapsulate", "decapsulate"}


def test_errors_are_reported_as_json(base_url):
    assert post(base_url, "/api/seal", {"plaintext": "x"}) == (
        400,
        {"error": "missing field 'public'"},
    )
    assert post(base_url, "/api/seal", {"public": "junk"})[0] == 400
    assert post(base_url, "/api/keygen", {"params": "nope"})[0] == 400
    assert post(base_url, "/api/nope", {})[0] == 404


def test_rejects_foreign_host_header(base_url):
    assert post(base_url, "/api/params", {}, {"Host": "evil.example"})[0] == 403
