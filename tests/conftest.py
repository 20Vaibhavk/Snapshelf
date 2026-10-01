import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import cloudinary_service, demo
from app.config import Settings, get_settings
from app.main import app

# Obviously fake credentials used only inside tests.
LIVE_SETTINGS = Settings(
    cloudinary_cloud_name="testcloud",
    cloudinary_api_key="test-key-111",
    cloudinary_api_secret="test-secret-222",
    gemini_api_key="test-gemini-333",
    gemma_model="gemma-4-test",
    max_upload_mb=10,
    force_demo=False,
)
DEMO_SETTINGS = Settings("", "", "", "", "gemma-4-test", 10, True)


def make_image(fmt: str = "PNG", size=(64, 48), color=(232, 26, 59)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def png_bytes() -> bytes:
    return make_image()


@pytest.fixture
def use_settings(monkeypatch, tmp_path):
    """Return a function that installs a Settings object and gives back a TestClient."""
    monkeypatch.setattr(demo, "UPLOAD_DIR", tmp_path)

    def _install(settings: Settings) -> TestClient:
        app.dependency_overrides[get_settings] = lambda: settings
        if settings.cloudinary_cloud_name:
            cloudinary_service.configure(settings)
        return TestClient(app)

    yield _install
    app.dependency_overrides.clear()


@pytest.fixture
def demo_client(use_settings) -> TestClient:
    return use_settings(DEMO_SETTINGS)


@pytest.fixture
def live_client(use_settings) -> TestClient:
    return use_settings(LIVE_SETTINGS)
