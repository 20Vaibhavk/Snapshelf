#!/usr/bin/env python3
"""SnapShelf Agent Skill client. Standard library only.

Usage:
    python snapshelf.py photo.jpg [--brand-color "#E81A3B"] [--presets a,b] [--json] [--api URL]
    python snapshelf.py --health
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_API = "http://localhost:8000"


def _multipart(fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n".encode() + file_path.read_bytes() + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _request(req: urllib.request.Request, timeout: int = 120) -> dict:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        try:
            detail = json.loads(err.read().decode()).get("detail", err.reason)
        except Exception:
            detail = err.reason
        print(f"SnapShelf rejected the request ({err.code}): {detail}", file=sys.stderr)
        sys.exit(3)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
        print(f"SnapShelf server is unreachable: {err}", file=sys.stderr)
        sys.exit(2)


def health(api: str) -> dict:
    return _request(urllib.request.Request(f"{api}/api/health"), timeout=10)


def process(api: str, image: Path, brand_color: str, presets: str) -> dict:
    body, content_type = _multipart({"brand_color": brand_color, "presets": presets}, image)
    req = urllib.request.Request(f"{api}/api/process", data=body, method="POST",
                                 headers={"Content-Type": content_type})
    return _request(req)


def summarize(result: dict, api: str) -> str:
    lines = [f"Mode: {result['mode']}"]
    listing = result.get("listing")
    if listing:
        lines += [
            f"Title: {listing['title']}",
            f"Category: {listing['category']}",
            f"Description: {listing['description']}",
            "Features:", *[f"  - {f}" for f in listing["features"]],
            "Tags: " + ", ".join(listing["tags"]),
            f"Alt text: {listing['alt_text']}",
            f"Social caption: {listing['social_caption']}",
        ]
    lines.append("Images:")
    for v in result["variants"]:
        url = v["url"] if v["url"].startswith("http") else api + v["url"]
        lines.append(f"  - {v['label']} ({v['width']}x{v['height']}): {url}")
    saved = (result.get("optimization") or {}).get("saved_percent")
    if saved is not None:
        lines.append(f"Bandwidth saved: {saved}%")
    lines += [f"Warning: {w}" for w in result.get("warnings", [])]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SnapShelf: product photo to listing")
    parser.add_argument("image", nargs="?", type=Path)
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--brand-color", default="auto")
    parser.add_argument("--presets", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args(argv)
    api = args.api.rstrip("/")

    if args.health:
        print(json.dumps(health(api), indent=2))
        return 0
    if not args.image:
        parser.error("an image path is required")
    if not args.image.is_file():
        print(f"File not found: {args.image}", file=sys.stderr)
        return 3

    result = process(api, args.image, args.brand_color, args.presets)
    print(json.dumps(result, indent=2) if args.json else summarize(result, api))
    return 0


if __name__ == "__main__":
    sys.exit(main())
