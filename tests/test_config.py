"""NFR-01, NFR-02, NFR-07: configuration and secret handling."""

import pytest

from app.config import DEFAULT_GEMMA_MODEL, get_settings

KEYS = ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "GEMINI_API_KEY")


@pytest.fixture
def env(monkeypatch):
    for key in (*KEYS, "GEMMA_MODEL", "DEMO_MODE", "MAX_UPLOAD_MB"):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def _fill(env):
    env.setenv("CLOUDINARY_CLOUD_NAME", "mycloud")
    env.setenv("CLOUDINARY_API_KEY", "key-abc")
    env.setenv("CLOUDINARY_API_SECRET", "secret-def")
    env.setenv("GEMINI_API_KEY", "gemini-ghi")


def test_placeholders_are_treated_as_missing(env):
    env.setenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name")
    env.setenv("CLOUDINARY_API_KEY", "your_api_key")
    env.setenv("CLOUDINARY_API_SECRET", "<secret>")
    env.setenv("GEMINI_API_KEY", "your_gemini_api_key")
    settings = get_settings()
    assert settings.mode == "demo"
    assert settings.missing_keys() == list(KEYS)


def test_all_keys_present_means_live(env):
    _fill(env)
    assert get_settings().mode == "live"


def test_partial_keys_fall_back_to_demo(env):
    _fill(env)
    env.delenv("GEMINI_API_KEY")
    settings = get_settings()
    assert settings.mode == "demo"
    assert settings.missing_keys() == ["GEMINI_API_KEY"]


def test_demo_mode_can_be_forced(env):
    _fill(env)
    env.setenv("DEMO_MODE", "true")
    assert get_settings().mode == "demo"


def test_gemma_model_configurable(env):
    assert get_settings().gemma_model == DEFAULT_GEMMA_MODEL
    env.setenv("GEMMA_MODEL", "gemma-4-custom-it")
    assert get_settings().gemma_model == "gemma-4-custom-it"


def test_max_upload_parsing(env):
    env.setenv("MAX_UPLOAD_MB", "not-a-number")
    assert get_settings().max_upload_mb == 10
    env.setenv("MAX_UPLOAD_MB", "3")
    assert get_settings().max_upload_bytes == 3 * 1024 * 1024


def test_repr_never_contains_secrets(env):
    _fill(env)
    text = repr(get_settings())
    for secret in ("key-abc", "secret-def", "gemini-ghi"):
        assert secret not in text


def test_redact_removes_every_secret(env):
    _fill(env)
    message = "failed with key-abc and secret-def and gemini-ghi"
    assert get_settings().redact(message) == "failed with [REDACTED] and [REDACTED] and [REDACTED]"
