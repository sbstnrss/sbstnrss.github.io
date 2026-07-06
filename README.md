# sebastianruss.com

Personal portfolio of **Sebastian Russ** — a fully static website: hand-written
HTML, one shared `style.css`, and two dependency-free progressive-enhancement
scripts (`masonry.js`, `lqip.js`). **No CMS, no build step, no dependencies.**

## Quick start

```sh
make start      # serve at http://localhost:8000 (Ctrl+C to stop)
make open       # open the running site in your browser
make previews   # (re)generate 1x1 dominant-colour image placeholders
make help       # list all targets
```

Override the port with `make start PORT=9000`.

You can also just open `index.html` in a browser — every page works from the
filesystem. A local server (`make start`) is only recommended because it makes
relative asset paths behave exactly as they do in production.

## How it works

- `index.html` — home: a full-width masonry grid of project cards with a
  category/tag filter.
- `<Project-Slug>.html` — one detail page per project.
- `info.html`, `contact.html`, `impressum.html` — bio, contact, legal notice.
- `style.css` — the single shared stylesheet.
- `masonry.js` — home-grid masonry (loaded by `index.html`); the site is fully
  functional without it.
- `lqip.js` — low-quality image placeholders: shows each image's dominant colour
  until the full image has decoded, then swaps it in whole (no progressive
  row-by-row paint). Loaded by every page with images.
- `assets/img/<Slug>/` — self-hosted images per project, each with a generated
  `<name>_preview.gif` placeholder (`make previews`).

## Adding a project

New projects are added by hand-editing HTML — no generator involved. See
[`AGENTS.md`](AGENTS.md) for the full directory map, layout conventions, and the
step-by-step **"add a new project"** recipe.

## Deploy

Because it is fully static, deploy by copying the folder to any static host
(GitHub Pages, Netlify, S3, plain nginx/Apache) — no build required.
