---
name: snapshelf
description: Turn a product photo into a ready-to-sell e-commerce listing and channel-ready images. Uses Gemma 4 (open-weight, via the Gemini API) to write the title, description, features, tags and alt text, and Cloudinary to remove the background and produce Instagram, Story, marketplace, WhatsApp and banner versions. Use when the user wants to list a product, create product images for social media or marketplaces, or write alt text for a product photo.
license: MIT
compatibility: Requires Python 3.10+ and a running SnapShelf server (default http://localhost:8000). No extra Python packages needed for the script.
metadata:
  author: SnapShelf contributors
  version: "1.0.0"
---

# SnapShelf Skill

Use this skill to convert one product photo into a complete listing plus five channel-ready images.

## When to use

- The user shares or names a product photo and asks for a listing, product description, tags or alt text.
- The user wants product images sized for Instagram, Instagram Stories, a marketplace (white background), WhatsApp or a website banner.

## Steps

1. Make sure the SnapShelf server is running. Check with:
   `python scripts/snapshelf.py --health`
   If it is not running, ask the user to start it from the project folder with `run.bat` (Windows) or `uvicorn app.main:app` (macOS/Linux).
2. Run the script on the image:
   `python scripts/snapshelf.py path/to/photo.jpg`
   Optional flags:
   - `--brand-color "#E81A3B"` uses a fixed brand background instead of the AI suggestion.
   - `--presets instagram_post,marketplace` limits the output channels.
   - `--json` prints the raw API response.
3. Present the result to the user:
   - The listing title, description, the three features and the tags.
   - The alt text, and suggest using it on every image.
   - One line per image variant with its label, size and URL.
   - The bandwidth saved, if reported.
4. If the response mode is `demo`, tell the user the listing is a sample and that real results need API keys in the server's `.env` file. Never ask the user to paste keys into the chat.

## Output channels

| Preset ID | Size | What Cloudinary does |
|---|---|---|
| `instagram_post` | 1080x1080 | AI background removal, brand colour background |
| `instagram_story` | 1080x1920 | AI background removal, brand colour background |
| `marketplace` | 2000x2000 | AI background removal, pure white background |
| `whatsapp` | 600x600 | AI background removal, eco quality for fast sharing |
| `web_banner` | 1600x600 | Generative fill extends the original scene |

All images are delivered with `f_auto` and `q_auto`.

## Errors

- Exit code 2: the server is unreachable. Ask the user to start it.
- Exit code 3: the server rejected the image (wrong type, too large or corrupt). Show the message.
- A warning starting with "AI listing unavailable" means images were produced but Gemma failed. Show the warning and the images.
