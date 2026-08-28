# Local asset sources

All runtime assets in this directory are stored locally so the mini-program does not depend on third-party image hosts.

## Recipe photography

- `recipes/chicken-quinoa.jpg` — generated with OpenAI built-in ImageGen on 2026-08-19; natural-light top-down chicken quinoa salad.
- `recipes/avocado-shrimp.jpg` — generated with OpenAI built-in ImageGen on 2026-08-19; natural-light top-down avocado shrimp salad.
- `recipes/tomato-oat-soup.jpg` — generated with OpenAI built-in ImageGen on 2026-08-19; natural-light top-down tomato mushroom oat soup.

The generated originals are retained in the local Codex generated-image store. Project copies are resized and JPEG-compressed for the mini-program package.

The first reviewed platform recipe dataset intentionally reuses these three project-owned images as category covers: `chicken-quinoa.jpg` for poultry, meat, rice, noodle, and egg dishes; `avocado-shrimp.jpg` for shrimp and cold vegetable dishes; and `tomato-oat-soup.jpg` for soups, tomato, tofu, and braised vegetable dishes. They are illustrative category photography rather than exact photographs of every recipe.
