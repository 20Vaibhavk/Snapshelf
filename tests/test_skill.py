"""FR-16: Agent Skill structure follows the Agent Skill Open Standard."""

import importlib.util
import re

import pytest
import yaml

from app.config import PROJECT_ROOT

SKILL_DIR = PROJECT_ROOT / "skills" / "snapshelf"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _frontmatter() -> tuple[dict, str]:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    _, front, body = text.split("---\n", 2)
    return yaml.safe_load(front), body


def _load_script():
    spec = importlib.util.spec_from_file_location("snapshelf_skill", SKILL_DIR / "scripts" / "snapshelf.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frontmatter_required_fields():
    meta, body = _frontmatter()
    assert 1 <= len(meta["name"]) <= 64
    assert NAME_RE.match(meta["name"])
    assert meta["name"] == SKILL_DIR.name, "name must match the skill directory"
    assert 1 <= len(meta["description"]) <= 1024
    assert body.strip()


def test_frontmatter_optional_fields_are_valid():
    meta, _ = _frontmatter()
    allowed = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
    assert set(meta) <= allowed
    assert len(meta.get("compatibility", "")) <= 500
    assert all(isinstance(v, str) for v in meta.get("metadata", {}).values())


def test_skill_script_summarizes_result():
    script = _load_script()
    result = {
        "mode": "live",
        "listing": {"title": "Mug", "category": "Kitchen", "description": "Nice.", "features": ["a", "b", "c"],
                    "tags": ["mug"], "alt_text": "A mug.", "social_caption": "#mug"},
        "variants": [{"label": "Marketplace", "width": 2000, "height": 2000, "url": "https://res.cloudinary.com/x"},
                     {"label": "Local", "width": 10, "height": 10, "url": "/uploads/a.png"}],
        "optimization": {"saved_percent": 61.5},
        "warnings": [],
    }
    text = script.summarize(result, "http://localhost:8000")
    assert "Title: Mug" in text
    assert "Marketplace (2000x2000): https://res.cloudinary.com/x" in text
    assert "http://localhost:8000/uploads/a.png" in text
    assert "Bandwidth saved: 61.5%" in text


def test_skill_script_multipart_body(tmp_path):
    script = _load_script()
    image = tmp_path / "photo.png"
    image.write_bytes(b"PNGDATA")
    body, content_type = script._multipart({"brand_color": "auto"}, image)
    assert content_type.startswith("multipart/form-data; boundary=")
    assert b'name="brand_color"' in body and b"PNGDATA" in body
    assert b"Content-Type: image/png" in body


def test_skill_script_missing_file_exit_code(tmp_path):
    script = _load_script()
    assert script.main([str(tmp_path / "missing.png")]) == 3


def test_skill_script_unreachable_server_exit_code(tmp_path):
    script = _load_script()
    with pytest.raises(SystemExit) as info:
        script.main(["--health", "--api", "http://127.0.0.1:9"])
    assert info.value.code == 2
