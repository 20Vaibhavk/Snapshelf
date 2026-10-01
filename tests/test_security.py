"""NFR-01, NFR-05: no secrets in the repository, .env is ignored, MIT license present."""

import re

from app.config import PROJECT_ROOT

SKIP_DIRS = {".venv", "venv", "__pycache__", ".pytest_cache", "uploads", ".git"}
SKIP_FILES = {".env"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".html", ".css", ".js", ".bat", ".ini", ".example", ".json", ".yml", ".yaml", ""}

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),               # Google API key
    re.compile(r"cloudinary://\d+:[A-Za-z0-9_\-]+@"),       # Cloudinary URL with credentials
    re.compile(r"(?i)api_secret\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
]


def _repo_files():
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or path.name in SKIP_FILES:
            continue
        if SKIP_DIRS & set(path.relative_to(PROJECT_ROOT).parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def test_no_secrets_committed():
    offenders = []
    for path in _repo_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(p.search(text) for p in SECRET_PATTERNS):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert offenders == [], f"Possible secrets found in: {offenders}"


def test_env_file_is_git_ignored():
    lines = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lines
    assert "!.env.example" in lines


def test_env_example_has_only_placeholders():
    for line in (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith(("CLOUDINARY_API", "GEMINI_API_KEY")):
            assert "your_" in line


def test_mit_license_present():
    assert "MIT License" in (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
