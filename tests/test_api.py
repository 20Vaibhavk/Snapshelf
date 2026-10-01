"""FR-01 to FR-03, FR-06, FR-12 to FR-15, NFR-03: API behaviour in demo and live mode."""

import threading

from app import cloudinary_service, gemma_client
from app.cloudinary_service import CloudinaryError
from app.config import Settings
from app.demo import DEMO_LISTING
from app.gemma_client import GemmaError
from tests.conftest import DEMO_SETTINGS, make_image


def _post(client, data: bytes, content_type="image/png", name="mug.png", **form):
    return client.post("/api/process", files={"file": (name, data, content_type)}, data=form)


# ---------- basics ----------

def test_index_is_served(demo_client):
    res = demo_client.get("/")
    assert res.status_code == 200
    assert "SnapShelf" in res.text


def test_health(demo_client):
    body = demo_client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["mode"] == "demo"
    assert body["gemma_model"] == "gemma-4-test"


def test_health_never_exposes_secrets(live_client):
    text = live_client.get("/api/health").text
    for secret in ("test-key-111", "test-secret-222", "test-gemini-333"):
        assert secret not in text


def test_presets_endpoint(demo_client):
    body = demo_client.get("/api/presets").json()
    assert len(body) == 5
    assert {"id", "label", "width", "height", "style"} <= set(body[0])


# ---------- upload validation ----------

def test_rejects_unsupported_type(demo_client):
    res = _post(demo_client, b"hello", content_type="text/plain", name="notes.txt")
    assert res.status_code == 415


def test_rejects_disguised_gif(demo_client):
    res = _post(demo_client, make_image("GIF"), content_type="image/png")
    assert res.status_code == 415


def test_rejects_corrupt_image(demo_client):
    res = _post(demo_client, b"definitely not an image", content_type="image/png")
    assert res.status_code == 400


def test_rejects_empty_file(demo_client):
    assert _post(demo_client, b"").status_code == 400


def test_rejects_oversized_upload(use_settings):
    small_limit = Settings("", "", "", "", "gemma-4-test", 1, True)
    client = use_settings(small_limit)
    res = _post(client, b"\x89PNG" + b"0" * (1024 * 1024 + 10))
    assert res.status_code == 413


def test_accepts_jpeg_and_webp(demo_client):
    assert _post(demo_client, make_image("JPEG"), "image/jpeg", "a.jpg").status_code == 200
    assert _post(demo_client, make_image("WEBP"), "image/webp", "a.webp").status_code == 200


# ---------- demo mode ----------

def test_process_demo_mode_end_to_end(demo_client, png_bytes, tmp_path):
    res = _post(demo_client, png_bytes)
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "demo"
    assert body["listing"]["title"] == DEMO_LISTING.title
    assert len(body["variants"]) == 5
    assert body["warnings"] and "Demo mode" in body["warnings"][0]
    assert body["original"]["url"].startswith("/uploads/")
    assert len(list(tmp_path.iterdir())) == 1
    for variant in body["variants"]:
        assert variant["transformation"][-1]["fetch_format"] == "auto"


def test_demo_respects_presets_and_brand_colour(demo_client, png_bytes):
    body = _post(demo_client, png_bytes, presets="instagram_post,marketplace", brand_color="#112233").json()
    variants = {v["id"]: v for v in body["variants"]}
    assert set(variants) == {"instagram_post", "marketplace"}
    assert variants["instagram_post"]["background_used"] == "rgb:112233"
    assert variants["marketplace"]["background_used"] == "rgb:FFFFFF"


# ---------- live mode with mocked services ----------

def _mock_live(monkeypatch, gemma=None, upload=None):
    calls = {"gemma": 0, "upload": 0}

    def fake_gemma(data, mime, settings):
        calls["gemma"] += 1
        return gemma(data, mime, settings) if gemma else DEMO_LISTING

    def fake_upload(data, filename, settings):
        calls["upload"] += 1
        if upload:
            return upload(data, filename, settings)
        return {"public_id": "snapshelf/mug_abc", "url": "https://res.cloudinary.com/testcloud/image/upload/snapshelf/mug_abc.png",
                "bytes": 200_000, "width": 64, "height": 48, "format": "png"}

    monkeypatch.setattr(gemma_client, "analyze_product", fake_gemma)
    monkeypatch.setattr(cloudinary_service, "upload_image", fake_upload)
    monkeypatch.setattr(cloudinary_service, "measure_optimization",
                        lambda original, url, timeout=20.0: {"original_bytes": original, "optimized_bytes": 50_000,
                                                             "saved_percent": 75.0, "optimized_url": url})
    return calls


def test_live_flow_with_mocked_services(live_client, monkeypatch, png_bytes):
    calls = _mock_live(monkeypatch)
    res = _post(live_client, png_bytes)
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "live"
    assert calls == {"gemma": 1, "upload": 1}
    assert body["listing"]["product_name"] == DEMO_LISTING.product_name
    assert body["optimization"]["saved_percent"] == 75.0
    assert body["warnings"] == []
    post = next(v for v in body["variants"] if v["id"] == "instagram_post")
    assert "res.cloudinary.com/testcloud" in post["url"]
    assert "b_rgb:F3E9DC" in post["url"]  # AI-suggested background applied


def test_gemma_and_upload_run_in_parallel(live_client, monkeypatch, png_bytes):
    upload_started = threading.Event()

    def slow_gemma(data, mime, settings):
        assert upload_started.wait(timeout=3), "upload did not start while Gemma was running"
        return DEMO_LISTING

    def upload(data, filename, settings):
        upload_started.set()
        return {"public_id": "snapshelf/p", "url": "https://x/p.png", "bytes": 1000}

    _mock_live(monkeypatch, gemma=slow_gemma, upload=upload)
    assert _post(live_client, png_bytes).status_code == 200


def test_gemma_failure_still_returns_variants(live_client, monkeypatch, png_bytes):
    def broken(*_):
        raise GemmaError("Gemma request failed (gemma-4-test): quota exceeded")

    _mock_live(monkeypatch, gemma=broken)
    res = _post(live_client, png_bytes)
    assert res.status_code == 200
    body = res.json()
    assert body["listing"] is None
    assert len(body["variants"]) == 5
    assert "AI listing unavailable" in body["warnings"][0]


def test_cloudinary_failure_returns_502(live_client, monkeypatch, png_bytes):
    def broken(*_):
        raise CloudinaryError("Cloudinary upload failed: Invalid cloud_name")

    _mock_live(monkeypatch, upload=broken)
    res = _post(live_client, png_bytes)
    assert res.status_code == 502
    assert "Invalid cloud_name" in res.json()["detail"]


def test_unexpected_upload_error_is_generic(live_client, monkeypatch, png_bytes):
    def broken(*_):
        raise RuntimeError("internal detail with test-secret-222")

    _mock_live(monkeypatch, upload=broken)
    res = _post(live_client, png_bytes)
    assert res.status_code == 502
    assert "test-secret-222" not in res.text


def test_demo_settings_never_call_services(use_settings, monkeypatch, png_bytes):
    client = use_settings(DEMO_SETTINGS)
    calls = _mock_live(monkeypatch)
    assert _post(client, png_bytes).status_code == 200
    assert calls == {"gemma": 0, "upload": 0}
