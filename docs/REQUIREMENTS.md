# SnapShelf: Requirements Specification

SnapShelf turns one rough product photo into a ready-to-sell listing. Gemma 4 (via the Gemini API) understands the photo and writes the listing copy. Cloudinary removes the background, generates channel-ready variants and delivers them optimized.

## 1. Goals

| ID | Goal |
|---|---|
| G-1 | A small seller goes from phone photo to marketplace-ready assets in under one minute. |
| G-2 | Qualify for the "Best Use of Gemma 4" challenge: Gemma 4 is multimodal and central to the flow. |
| G-3 | Qualify for the "Best Open-Source AI Project" challenge: open-weight model, public repo, MIT license, Agent Skill compliant with the Agent Skill Open Standard. |
| G-4 | Show clear Cloudinary value: AI transformations, optimized delivery, automated workflow. |

## 2. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The user can upload one image by drag-and-drop or file picker. Accepted types: JPEG, PNG, WEBP. |
| FR-02 | Uploads larger than the configured limit (default 10 MB) are rejected with HTTP 413 and a clear message. |
| FR-03 | Files with an unsupported type are rejected with HTTP 415. Files that claim to be images but cannot be decoded are rejected with HTTP 400. |
| FR-04 | The image is sent to Gemma 4, which returns a structured listing: product name, category, title, description, three key features, tags, alt text, social caption and a suggested background colour. |
| FR-05 | Gemma output is validated and normalised: title at most 80 characters, 3 to 10 unique lowercase tags, exactly 3 features, a valid `#RRGGBB` background colour (fallback `#F5F5F5`). |
| FR-06 | The original image is uploaded to Cloudinary into the `snapshelf/` folder. |
| FR-07 | SnapShelf generates five channel variants: Instagram Post (1080x1080), Instagram Story (1080x1920), Marketplace (2000x2000, white background), WhatsApp Catalog (600x600, eco quality) and Website Banner (1600x600, generative fill). |
| FR-08 | Product-focused variants use Cloudinary AI background removal. The banner uses Cloudinary generative fill to extend the original scene. |
| FR-09 | Every variant is delivered with automatic format and quality (`f_auto`, `q_auto`). |
| FR-10 | The user can choose a brand background colour or let the AI suggestion be used ("auto"). |
| FR-11 | Every variant offers a direct download link. |
| FR-12 | The response reports original size, optimized size and percentage saved when measurable. |
| FR-13 | If Gemma fails, image variants are still returned together with a warning. If Cloudinary fails, the API returns HTTP 502 with a clear message. |
| FR-14 | A demo mode runs the full flow without any API keys, using a sample listing and local image serving. The UI shows a visible demo banner. |
| FR-15 | `GET /api/health` reports status, mode (live or demo) and the configured Gemma model. `GET /api/presets` lists the variants. |
| FR-16 | An Agent Skill (`skills/snapshelf/SKILL.md`) lets any compatible AI agent run SnapShelf from the command line. |

## 3. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Security: credentials are read only from environment variables or a local `.env` file. `.env` is git-ignored. No secret is ever hard-coded, logged or returned by the API. |
| NFR-02 | Placeholder values in `.env` are treated as missing, so the app falls back to demo mode instead of failing with confusing errors. |
| NFR-03 | Performance: Gemma analysis and Cloudinary upload run in parallel. |
| NFR-04 | Accessibility: AI alt text is applied to rendered images. The UI is keyboard operable and works at phone width. |
| NFR-05 | Licensing: MIT license. Public GitHub repository. |
| NFR-06 | Portability: runs on Windows, macOS and Linux with Python 3.10 or later. No Node.js needed. |
| NFR-07 | Configurability: the Gemma model ID is configurable through `GEMMA_MODEL`, so it can be updated on event day without code changes. |
| NFR-08 | Branding: UI uses Trebuchet MS and the BDO colour palette. |

## 4. Traceability Matrix

| Requirement | Implemented in | Verified by |
|---|---|---|
| FR-01 | `static/app.js`, `app/main.py` | `tests/test_api.py::test_process_demo_mode_end_to_end` |
| FR-02 | `app/main.py::_read_and_validate` | `tests/test_api.py::test_rejects_oversized_upload` |
| FR-03 | `app/main.py::_read_and_validate` | `tests/test_api.py::test_rejects_unsupported_type`, `test_rejects_corrupt_image` |
| FR-04 | `app/gemma_client.py` | `tests/test_listing.py`, `tests/test_api.py::test_live_flow_with_mocked_services` |
| FR-05 | `app/listing.py` | `tests/test_listing.py` |
| FR-06 | `app/cloudinary_service.py::upload_image` | `tests/test_api.py::test_live_flow_with_mocked_services` |
| FR-07 | `app/presets.py` | `tests/test_presets.py::test_five_presets_with_expected_sizes` |
| FR-08 | `app/presets.py::build_transformation` | `tests/test_presets.py::test_cutout_presets_remove_background`, `test_banner_uses_generative_fill` |
| FR-09 | `app/presets.py::build_transformation` | `tests/test_presets.py::test_every_preset_optimizes_delivery` |
| FR-10 | `app/presets.py::resolve_background` | `tests/test_presets.py::test_background_resolution` |
| FR-11 | `app/cloudinary_service.py::build_variants` | `tests/test_presets.py::test_variant_urls_and_download_links` |
| FR-12 | `app/cloudinary_service.py::measure_optimization` | `tests/test_api.py::test_live_flow_with_mocked_services` |
| FR-13 | `app/main.py::process` | `tests/test_api.py::test_gemma_failure_still_returns_variants`, `test_cloudinary_failure_returns_502` |
| FR-14 | `app/demo.py`, `static/app.js` | `tests/test_api.py::test_process_demo_mode_end_to_end` |
| FR-15 | `app/main.py` | `tests/test_api.py::test_health`, `test_presets_endpoint` |
| FR-16 | `skills/snapshelf/` | `tests/test_skill.py` |
| NFR-01 | `app/config.py`, `.gitignore` | `tests/test_config.py`, `tests/test_security.py` |
| NFR-02 | `app/config.py` | `tests/test_config.py` |
| NFR-03 | `app/main.py::process` | Code review (`asyncio.gather`) |
| NFR-04 | `static/` | Manual check |
| NFR-05 | `LICENSE` | `tests/test_security.py::test_mit_license_present` |
| NFR-06 | `requirements.txt` | Test run on Windows / Python 3.10 |
| NFR-07 | `app/config.py` | `tests/test_config.py::test_gemma_model_configurable` |
| NFR-08 | `static/styles.css` | Manual check |
