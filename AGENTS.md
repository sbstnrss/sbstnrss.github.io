# sebastianruss.com — static portfolio

Personal portfolio of Sebastian Russ, rebuilt as a **fully static site**: plain
hand-written HTML + one shared `style.css`. **No CMS, no build step.** There are
two dependency-free progressive-enhancement scripts — `masonry.js` (home grid,
loaded only by `index.html`) and `lqip.js` (image placeholders, loaded by every
page that has images) — every page works and reads fine without them. Run
`make start` to serve the folder locally (`http://localhost:8000`), or open any
`.html` directly in a browser. New projects are added by hand-editing HTML (see
the recipe below); `make previews` regenerates the image placeholders.

## Directory / file map

| Path                    | Purpose                                                          |
|-------------------------|-----------------------------------------------------------------|
| `index.html`            | Home — full-width grid of all project cards + CSS-only category filter |
| `<Project-Slug>.html`   | One detail page per project (e.g. `Prototype.html`, `Tudock.html`) |
| `info.html`             | Bio / about (linked as "Info" and from the "Hello!" card)       |
| `contact.html`          | Email + external profile links                                  |
| `impressum.html`        | Legal notice / privacy policy (German + English)                |
| `style.css`             | The single shared stylesheet for every page                     |
| `masonry.js`            | Home-grid masonry enhancement (loaded only by `index.html`)     |
| `lqip.js`               | Dominant-colour image placeholders + skeleton (loaded by every page with images) |
| `tools/generate-previews.py` | Stamps `data-lqip` colours on every `<img>` + writes the `<name>_preview.gif` fallbacks (`make previews`) |
| `assets/img/<Slug>/`    | Self-hosted images per project + a generated `<name>_preview.gif` per image |
| `Makefile`              | `make start` serves locally; `make previews` regenerates placeholders |
| `README.md`             | Project overview + quick start (points here for the full map)   |

Page slugs use the project's `Title-With-Hyphens` (matching the original URLs).

## Layout conventions

Every page shares the same hand-copied shell (keep them in sync):

- **Header** (`.site-header#top`): `SEBASTIAN RUSS` logo → `index.html`, then nav:
  Products / Illustrations / Graphics → `index.html#products|#illustrations|#graphics`,
  Info → `info.html`, Contact → `contact.html`. Add `class="active"` on the current
  page's nav link.
- **Footer** (`.site-footer`): back-to-top (`#top`), copyright line, Impressum link.

Design tokens live in `:root` in `style.css`: accent `--accent: #ff3366`, a generic
system `--font` stack, mono `--mono` for tags/footer, plus themeable `--bg`/`--ink`
(see theming below) with `--muted`/`--faint`/`--hairline` derived from them via
`color-mix`. No web fonts are loaded. Layout is **full-width on the home grid**
(it fills the viewport), while project pages are centered on a `--content` /
`--measure` column (both `1000px`, matching the original site) — text and media
share the same readable width.

### Theming (per-project background)

A project page can tint itself by setting `--bg`/`--ink` on its `<body>`, e.g.
`<body style="--bg:#000000;--ink:#e6e6e6">`. Everything reads `var(--ink)` on
`var(--bg)`, and the muted tones are `color-mix`ed from them, so a dark background
automatically gets light, legible text/nav/footer. Pick a light `--ink` when the
background is dark.

### Home grid: masonry + CSS category filter

The home grid is an organic masonry — cards of differing heights tile down columns
instead of snapping into aligned rows — that fills the viewport (~6 columns at 1920,
two on phones). It is built in two layers:

- **Without JS (fallback):** CSS multi-column (`.grid { column-width: 300px }`,
  `column-count: 2` under `max-width: 700px`). Fully functional and organic, but
  because multi-column *balances by height*, a filtered category with fewer cards
  than columns stacks them into the left columns instead of spreading out.
- **With JS (`masonry.js`):** adds `.js` to `<html>`, which flips `.grid` to a flex
  row of `.masonry-col` columns; the script packs each card into the currently
  **shortest** column. This reproduces the original site: a filtered category
  spreads across every column and fills the full width. The script re-runs on
  `hashchange` (filter changes) and on `resize` when the column count changes. Card
  images carry `width`/`height` attributes so column heights are correct before the
  images load. It reads `.card` order and the `tag-*` classes; **no per-project JS
  edits are needed** when adding a project.

**Every tag is a filter.** A card's tags (year + keywords) render as clickable
rounded **chips** (`.card-tags a`), and the top nav uses the exact same mechanism —
each is a link to `#tag-<slug>` (e.g. `#tag-product`, `#tag-robot`, `#tag-2009`),
where the slug is the lowercased tag. `masonry.js` reads the hash, keeps only cards
carrying that `tag-<slug>` class, and re-flows. Filtering is single-tag
(replace-on-click), matching the original site. Because the script matches on the
class named by the hash, **a brand-new tag or year needs no CSS/JS change** — just
add the `tag-<slug>` class + chip link to the card.

While a filter is active the script sets `body.filtering` and fills the
`.filter-status` bar (a `.filter-label` "Showing: <Tag>" + a `.filter-clear`
"× Show all" link, `href="#top"`). `#top` clears the filter without a reload,
letting the script re-flow on `hashchange`.

Fallback without JS: hidden `<span class="filter-target" id="tag-product">` …
anchors sit as **direct children of `<body>` before `.site-header` and `.grid`** so
the `:target ~` sibling rules in `style.css` can hide non-matching cards and
highlight the nav — but **only for the three main categories** (product /
illustration / graphic), to avoid one span+rule per tag. Other tag chips simply
show all without JS. Do not wrap the grid in another element — the `~` combinator
needs the grid to stay a body-level sibling.

### Project detail pages

Each project page has, in order: the shared header, a `.project-nav`
(← previous / grid-icon → index / next → in the `index.html` grid order, wrapping
around), a visible `.project-title`, then `.project-content`, a `.project-footer`
(`Filed under` + the same tag chips, linking to `index.html#tag-<slug>`), and a
`.view-all` link.

Inside `.project-content`, content is a sequence of:
- `.image-single` — one or more full-width stacked images
- `.image-row` — a 2-up responsive image grid
- `.video` — a responsive Vimeo embed (aspect-ratio wrapper + `<iframe>`); the only
  third-party dependency. It loads `player.vimeo.com` but is not our own script.
- `.text-cols` › `.text-col` — side-by-side text columns (original is EN + DE)
- `.centered` — centered link/text block

### Image loading (LQIP + skeleton)

Every `<img>` gets a low-quality placeholder while it loads (the manu.ninja
"dominant colors for lazy loading" technique). Each image's **dominant/average
colour** is stamped **inline** on the tag as `data-lqip="#rrggbb"`. These are
**generated, not hand-authored** — run `make previews` (→
`tools/generate-previews.py`), which uses macOS `sips` + stdlib only (no
ImageMagick/Pillow), is idempotent, and gives transparent PNGs a neutral fallback
tint. The same run also writes a sibling 1×1 `<name>_preview.gif` (~35 bytes) per
image, kept only as a background fallback for any `<img>` that lacks a `data-lqip`.

`lqip.js` is the progressive enhancement that uses them. For every `<img>` it wraps
the image in a `<span class="lqip-frame">` whose background is the inline
`data-lqip` colour (or, if absent, the `_preview.gif` via the `--lqip` custom
property; the `.lqip-frame` rules live in `style.css`). Because the placeholder is
**inline, it needs no network request** — it paints instantly and never competes
with the real images for connections, so the dominant colour stays visible for the
*whole* load even on the home grid where many thumbnails download at once. The
`<img>` **keeps its own `src`/`srcset` and loads natively** — **nothing is held,
cancelled or fetched twice, and `srcset` selection is untouched** — but is kept at
`visibility:hidden` until it has fully downloaded **and** decoded, then revealed
whole (`.is-loaded`), so the image appears **complete in one paint, never
progressively row by row**. On reveal the placeholder is cleared so transparent
images show the page, not the tint. All images load **eagerly** — there is no
scroll-based lazy loading. (Moving a `loading="lazy"` `<img>` in the DOM pauses its
native load, so `lqip.js` resumes it by removing the attribute.) The wrapper (not
the `<img>`) carries the between-image spacing in `.image-single`, and is the flex
item in `.image-row`. This is pure enhancement: **without JS there is no frame and
images just load normally.** Because `make previews` stamps `data-lqip` from each
image's `src`, **no per-`<img>` edits are needed** — only run it after adding
images. The `width`/`height` attributes (already required for masonry) reserve the
box so the placeholder shows at the right size.

## Recipe: add a new project

1. Create `assets/img/<New-Slug>/` and drop the images in (keep them ~1000px wide),
   then run `make previews` to generate their placeholders (the `data-lqip`
   colours are stamped onto the HTML once the tags exist — re-run after step 4).
2. Copy an existing project page (e.g. `Prototype.html`) to `<New-Slug>.html`; set
   the `<title>`/`<meta description>`, the `.project-title` + `.visually-hidden`
   `<h1>`, the image/text blocks, and the `.project-footer` tag chips (year +
   keywords, each `<a href="index.html#tag-<slug>">`). Optionally tint it with
   `--bg`/`--ink` on `<body>`.
3. Fix the `.project-nav` prev/next links on the new page **and on its two
   neighbours** so the ← / → chain stays in `index.html` grid order.
4. Add a card to `index.html`'s `.grid`: `<div class="card tag-…">` with the
   thumbnail (`assets/img/<New-Slug>/…`), `.card-title`, `.card-excerpt`, and
   `.card-tags`. Give the thumbnail `<img>` correct `width`/`height` attributes so
   `masonry.js` can measure column heights before the image loads. The card's
   `class` must carry a `tag-<slug>` for **every** tag it shows (year included, e.g.
   `tag-2020`), and each `.card-tags` chip is an `<a href="#tag-<slug>">`. Filtering
   (and the footer chips) then work automatically — new tags/years need no CSS/JS.
5. Only if you add a tag to the **top nav** (a fourth main category) do you touch
   `style.css`: add a `<span class="filter-target" id="tag-<slug>">` + the two
   `#tag-<slug>:target ~ …` rules (grid-hide + nav-highlight) for the no-JS
   fallback, plus the nav link. Any other new tag needs no CSS change.

## Verify a change

Open `index.html` in a browser; click a nav category **and** a tag chip (e.g. a
year) and confirm the grid re-flows to only matching cards spread across the full
width, the "Showing: <tag>" bar appears, "× Show all" clears it, and the
logo/`index.html` restores all. Check a project page renders, its footer chips link
to `index.html#tag-<slug>`, and all images load. Throttle the network (DevTools) to
watch each image show its dominant-colour placeholder for the whole load, then
appear complete in one paint (no broken-image icon/alt text, no progressive
row-by-row paint, and no cancelled/duplicate image requests in the Network tab).
Quick guards from the project root:

- `grep -rl "masonry.js" *.html` → only `index.html` (the home grid is the only
  page-specific script)
- `grep -Ll "lqip.js" $(grep -rl "<img " *.html)` → empty (every page with images
  loads the placeholder script)
- `make previews` → reports `0 written` and `N data-lqip in sync` when everything is
  up to date (every image has its `<name>_preview.gif` and its inline `data-lqip`)
