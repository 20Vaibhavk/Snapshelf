"""FR-07 to FR-11: channel presets, Cloudinary transformations and URLs."""

import pytest

from app import cloudinary_service
from app.presets import PRESETS, PRESETS_BY_ID, build_transformation, resolve_background, selected_presets
from tests.conftest import LIVE_SETTINGS


def test_five_presets_with_expected_sizes():
    sizes = {p.id: (p.width, p.height) for p in PRESETS}
    assert sizes == {
        "instagram_post": (1080, 1080),
        "instagram_story": (1080, 1920),
        "marketplace": (2000, 2000),
        "whatsapp": (600, 600),
        "web_banner": (1600, 600),
    }


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p.id)
def test_every_preset_optimizes_delivery(preset):
    last = build_transformation(preset, "rgb:FFFFFF")[-1]
    assert last["fetch_format"] == "auto"
    assert last["quality"].startswith("auto")


@pytest.mark.parametrize("preset", [p for p in PRESETS if p.style == "cutout"], ids=lambda p: p.id)
def test_cutout_presets_remove_background(preset):
    steps = build_transformation(preset, "rgb:112233")
    assert steps[0] == {"effect": "background_removal"}
    assert steps[2] == {"width": preset.width, "height": preset.height, "crop": "pad", "background": "rgb:112233"}


def test_banner_uses_generative_fill():
    steps = build_transformation(PRESETS_BY_ID["web_banner"], "rgb:FFFFFF")
    assert steps[0]["background"] == "gen_fill"
    assert steps[0]["crop"] == "pad"


def test_whatsapp_uses_eco_quality():
    assert build_transformation(PRESETS_BY_ID["whatsapp"], "rgb:FFFFFF")[-1]["quality"] == "auto:eco"


def test_background_resolution():
    post, market = PRESETS_BY_ID["instagram_post"], PRESETS_BY_ID["marketplace"]
    assert resolve_background(post, "#112233", "#AABBCC") == "rgb:112233"   # brand colour wins
    assert resolve_background(post, "auto", "#aabbcc") == "rgb:AABBCC"      # AI suggestion
    assert resolve_background(post, "auto", None) == "rgb:F5F5F5"           # fallback
    assert resolve_background(post, "not-a-colour", "bad") == "rgb:F5F5F5"
    assert resolve_background(market, "#112233", "#AABBCC") == "rgb:FFFFFF"  # marketplace is always white


def test_selected_presets_filtering():
    assert [p.id for p in selected_presets(["whatsapp", "marketplace"])] == ["whatsapp", "marketplace"]
    assert len(selected_presets(None)) == 5
    assert len(selected_presets(["unknown"])) == 5


def test_variant_urls_and_download_links():
    cloudinary_service.configure(LIVE_SETTINGS)
    variants = {v["id"]: v for v in cloudinary_service.build_variants(
        "snapshelf/mug", list(PRESETS), "auto", "#F3E9DC")}

    post = variants["instagram_post"]
    assert post["url"].startswith("https://res.cloudinary.com/testcloud/image/upload/")
    assert "e_background_removal" in post["url"]
    assert "b_rgb:F3E9DC" in post["url"]
    assert "f_auto" in post["url"] and "q_auto" in post["url"]
    assert post["url"].endswith("/snapshelf/mug")
    assert "fl_attachment:snapshelf_instagram_post" in post["download_url"]
    assert "fl_attachment" not in post["url"]

    assert "b_rgb:FFFFFF" in variants["marketplace"]["url"]
    assert "b_gen_fill" in variants["web_banner"]["url"]
    assert "e_background_removal" not in variants["web_banner"]["url"]
    for secret in ("test-key-111", "test-secret-222"):
        assert all(secret not in v["url"] for v in variants.values())
