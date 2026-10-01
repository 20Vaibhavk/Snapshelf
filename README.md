# SnapShelf

**One product photo in. A ready-to-sell listing out.**

SnapShelf helps small sellers turn a rough phone photo into a complete e-commerce listing and five channel-ready images in seconds.

- **Gemma 4** (open-weight, via the Gemini API) looks at the photo and writes the title, description, key features, search tags, accessible alt text and a social caption. It also suggests a background colour that suits the product.
- **Cloudinary** removes the background with AI, places the product on brand or marketplace backgrounds, extends scenes with generative fill, and delivers every image with automatic format and quality.

Built for the Cloudinary community media hackathon. Entered in **Best Use of Gemma 4** and **Best Open-Source AI Project**.

## What you get from one photo

| Output | Size | How |
|---|---|---|
| Listing copy | Title, description, 3 features, tags, alt text, caption | Gemma 4 multimodal |
| Instagram Post | 1080x1080 | `e_background_removal` + brand colour `c_pad` |
| Instagram Story | 1080x1920 | `e_background_removal` + brand colour `c_pad` |
| Marketplace | 2000x2000 | `e_background_removal` + pure white background |
| WhatsApp Catalog | 600x600 | `e_background_removal` + `q_auto:eco` |
| Website Banner | 1600x600 | `b_gen_fill` generative fill |

Every image uses `f_auto,q_auto`, and the app reports how much bandwidth this saves compared with the original upload.

## How it works

```
Photo ──► FastAPI ──┬──► Gemma 4 (Gemini API) ──► listing JSON ──► validated + normalised
                    │                                                    │
                    └──► Cloudinary upload ──► public_id ────────────────┤
                                                                         ▼
                              transformation URLs for 5 channels (+ download links)
```

Gemma analysis and the Cloudinary upload run **in parallel**. If Gemma fails, the images are still produced. If Cloudinary fails, the API returns a clear 502.

## Quick start (Windows)

1. Install Python 3.10 or later.
2. Double-click **`run.bat`**. It creates a virtual environment, installs dependencies and opens http://localhost:8000.
3. The app starts in **demo mode** (sample listing, local preview) until you add API keys.

### Add your API keys

1. Open `.env` in Notepad (copy `.env.example` to `.env` if it is missing).
2. Fill in:
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` from Cloudinary Console > Settings > API Keys
   - `GEMINI_API_KEY` from https://aistudio.google.com
   - `GEMMA_MODEL`: the exact Gemma 4 model ID shown in AI Studio
3. Save the file and restart `run.bat`. The badge in the top right changes to **Live**.

> `.env` is git-ignored. Never commit it and never paste keys into chats, issues or screenshots.

### macOS / Linux

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit it
uvicorn app.main:app --reload
```

## Agent Skill

`skills/snapshelf/` is an [Agent Skill](https://agentskills.io) that follows the Agent Skill Open Standard. Any compatible AI agent can use it to list a product:

```bash
python skills/snapshelf/scripts/snapshelf.py photo.jpg --brand-color "#E81A3B"
python skills/snapshelf/scripts/snapshelf.py --health
```

The script uses only the Python standard library.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Status, mode (`live` or `demo`) and Gemma model |
| GET | `/api/presets` | Available channel presets |
| POST | `/api/process` | Multipart: `file` (JPEG/PNG/WEBP, max 10 MB), `brand_color` (`auto` or `#RRGGBB`), `presets` (comma-separated IDs, optional) |

Interactive docs: http://localhost:8000/docs

## Tests

```bash
test.bat                 # Windows
python -m pytest -v      # any OS, inside the venv
```

The 78 tests cover every functional requirement in [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), with the external services mocked. That document includes a full traceability matrix linking each requirement to its code and tests.

## Project structure

```
app/            FastAPI backend (config, Gemma client, Cloudinary service, presets, demo mode)
static/         Frontend (HTML, CSS, JS, no build step)
skills/         Agent Skill (SKILL.md + standard-library CLI)
tests/          pytest suite
docs/           Requirements, traceability and demo script
samples/        Sample image generator
```

## License

[MIT](LICENSE)
