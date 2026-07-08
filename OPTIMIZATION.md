# Image Optimization Notes

A picked-up-later checklist for reducing image payload on sebastianruss.com.
Analysis done 2026-07-07; last updated 2026-07-08.

## Progress log

- **2026-07-08 — Siteless animations done.** All 4 Siteless `*_animiert.gif`
  converted to muted-autoplay `<video>` (H.264 MP4). 13.5 MB → 1.7 MB (~87%).
  `Siteless.html` + `style.css` (`.image-row > video`) + `AGENTS.md` updated.
  See **Recipe: animated GIF → video** below for the settled approach — apply it
  to the remaining GIFs next (Haystack is the big one left).
  Note: the original `*_animiert.gif` files and their `*_preview.gif` siblings
  are now unreferenced on disk — `git rm` them to reclaim the space.

## TL;DR verdict

The **74 MB** in `assets/img/` is misleading — nobody downloads that. What
matters is **per-page payload**. The home page is fine; some detail pages are
far too heavy.

| Page | Image payload | Verdict |
|---|---|---|
| Home grid (`index.html`, 35 thumbnails) | ~1.5 MB | ✅ Fine |
| `Haystack-Europe-2018.html` | 0.85 MB | ✅ Fine |
| `Prototype.html` | 4.9 MB | ⚠️ Heavy |
| `Rollercoaster.html` | 5.0 MB | ❌ Heavy |
| `Siteless.html` | ~~15.1 MB~~ → **3.3 MB** | ⚠️ Animations done; 2000px JPGs remain |

### Benchmarks for context (HTTP Archive Web Almanac 2025)

- Median mobile page: **2.56 MB total**, of which **~911 KB is images**.
- Common performance budget: **~650 KB total** for a 5 s load at the 75th
  percentile on a mid-tier device/connection.
- Global median mobile speed is ~60–90 Mbps, but real-world (latency,
  congestion, metered/roaming data) is much lower — 15 MB is a multi-second
  wait and a real chunk of someone's data plan.

The home page (thumbnails 52–88 KB each, proper `srcset` 1x/2x) sits in the
healthy zone. The detail pages blow past any budget — Siteless is ~6× the
*entire* median page.

## Root causes

Two problems — neither is "images are fundamentally too big":

### 1. Animated GIFs — 25 MB across just 12 files (worst offender)

GIF is a terrible modern format for animation.

- ~~Siteless: 4 animated GIFs (~13.5 MB)~~ — **done 2026-07-08**, now MP4 (1.7 MB).
- **Haystack still has ~5 animated GIFs (~2 MB each) — biggest remaining target.**
- `Tudock/…_weihnachtskarte_4.gif` (~1.1 MB) and `MICES-2017/…_08.gif` also remain.

**Fix:** replace animated GIFs with muted autoplay `<video>` (MP4). Confirmed
~85% saving on Siteless. Highest-impact single change. See the recipe below.

### 2. No modern still-image formats, no responsive sizing on detail pages

- Everything is JPG/PNG (46 MB JPG + 2.6 MB PNG). **Zero WebP, zero AVIF.**
  AVIF/WebP typically save **25–50%** over JPG at equal quality.
- Detail pages serve full 2000px JPGs (many 700 KB–1.8 MB each) even though the
  content column is `1000px` — a phone downloads ~4× the pixels it can show.
- `srcset` is only on the home grid; detail pages have none.

## Recommendation (priority order)

1. **Convert the remaining animated GIFs to MP4 video.** Siteless done; Haystack
   is the big one left, then Tudock + MICES. Use the recipe below.
2. **Add WebP/AVIF** (via `<picture>` or by re-encoding), starting with the
   heaviest JPGs. 25–50% off across the board.
3. **Add `srcset`/`sizes` to detail-page images** like the home grid already
   does. Cap the largest served variant near display width (~1000–1400px, plus
   a 2× for retina). The 2000px originals are oversized for a 1000px column.

## Recipe: animated GIF → video (settled approach)

Decisions locked in from the Siteless conversion — follow these for every
remaining GIF so the site stays consistent.

**Format: H.264 MP4 only. No WebM, no `<source>` fallback.** At these small
dimensions (~500px) VP9/WebM came out *larger* than H.264, and H.264 MP4 plays
in every browser and on iOS/Android — so a second encode would be pure dead
weight. Revisit only if a future clip is large enough that AV1/VP9 actually wins.

**Encode** (requires `ffmpeg`; installed via `brew install ffmpeg`):

```
ffmpeg -i in.gif -movflags +faststart -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -crf 23 -an out.mp4
```

- `-pix_fmt yuv420p` — required; also drops the GIF's alpha channel, which VP9
  chokes on and which yuv420p needs gone anyway.
- `scale=trunc(iw/2)*2:…` — forces even dimensions (yuv420p requirement); a 1px
  trim, negligible.
- `-crf 23` — good quality/size balance for these clips. Lower = higher quality.
- `-an` — strip audio (there is none). `+faststart` — moov atom up front so
  playback can start before full download.

**Markup** — replace the `<img …gif>` with, keeping the same `width`/`height`:

```html
<video src="…​.mp4" width="500" height="281"
       autoplay loop muted playsinline preload="auto"
       style="background:#rrggbb" aria-label="…"></video>
```

- `autoplay loop muted playsinline` — muted + `playsinline` are what make
  autoplay allowed on mobile (esp. iOS). Reproduces GIF behaviour.
- `style="background:#rrggbb"` — the clip's dominant colour, as an instant
  LQIP-style placeholder. **`lqip.js` only wraps `<img>`, so videos get no
  frame** — reuse the colour the old GIF's `data-lqip` carried.
- Keep `width`/`height` to reserve the box (same reason as images).

**CSS** — already handled: `.image-row > video` and `.image-row video` are in
`style.css` alongside the `<img>` rules, so a video is a proper flex item in a
two-up row. No change needed unless you place a video in `.image-single`.

**After converting:** the source `*.gif` and its `*_preview.gif` sibling become
unreferenced — `git rm` them to actually reclaim the bytes. No `make previews`
run is needed (videos aren't `<img>`, so `data-lqip`/preview state is unaffected).

## Notes on fit with this project

The architecture already supports all of this — no build step needed:

- The home grid proves the pattern (`srcset` 1x/2x, `width`/`height`, LQIP
  placeholders). Detail pages just never got the same treatment; the GIFs
  predate the video era.
- `tools/generate-previews.py` (`make previews`) stamps `data-lqip` colours and
  writes `_preview.gif` fallbacks — re-run after adding/replacing any images.
- Keep `width`/`height` attributes on every `<img>` (required for masonry +
  LQIP box reservation).

## Heaviest individual files (reference)

Siteless `*_animiert.gif` (5.6/4.8/2.8M) converted to MP4 2026-07-08 — no longer
in the top offenders (and pending `git rm`). Remaining:

```
2.1M  Haystack-Europe-2018/…_thumbnail.gif           ← GIF, convert next
2.1M  Haystack-Europe-2018/…_animated_01..04_500.gif  (×4)  ← GIF, convert next
1.8M  Victorinox/…_concept_04_2000.jpg
1.4M  Rollercoaster/…_02_2000.jpg
1.1M  Tudock/…_weihnachtskarte_4.gif                 ← GIF, convert
1.1M  Rollercoaster/…_01_2000.jpg
```

## Sources

- [Page Weight — Web Almanac 2025 (HTTP Archive)](https://almanac.httparchive.org/en/2025/page-weight)
- [SpeedCurve — Page bloat update 2025](https://www.speedcurve.com/blog/page-bloat-2025/)
- [DataReportal — Digital 2025: accelerated access (mobile speeds)](https://datareportal.com/reports/digital-2025-sub-section-accelerated-access)
