#!/usr/bin/env python3
"""Generate dominant-colour placeholders for every image in assets/img.

For each raster original (jpg/png/gif) this writes a sibling ``<stem>_preview.gif``
holding a single pixel of the image's average colour, and stamps the same colour
onto every ``<img>`` in the site's HTML as a ``data-lqip="#rrggbb"`` attribute.
``lqip.js`` uses that inline colour as a low-quality image placeholder while the
full image loads (the manu.ninja "Dominant Colors for Lazy Loading Images"
technique) — no per-image network request, so nothing competes with the real
images. The GIF is kept as a no-``data-lqip`` fallback.

Pure standard library + macOS ``sips`` (which downscales to 1x1 to average the
colour) — no ImageMagick / Pillow required. Run via ``make previews``.
"""

import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

# Repo root and the directory holding the per-project image folders.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets", "img")

SOURCE_EXTS = (".jpg", ".jpeg", ".png", ".gif")
PREVIEW_SUFFIX = "_preview.gif"

# Fallback tint for (near-)transparent images, so transparent logos get a neutral
# skeleton backdrop instead of an arbitrary colour bleeding through them.
NEUTRAL = (221, 221, 221)


def sips_pixel_png(src, dst):
    """Downscale ``src`` to a 1x1 PNG at ``dst`` (that pixel is the average colour)."""
    subprocess.run(
        ["sips", "-z", "1", "1", src, "-s", "format", "png", "--out", dst],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def read_png_pixel(path):
    """Return (r, g, b) for a 1x1 PNG, honouring the IHDR colour type.

    Handles the colour types sips emits for a 1x1 image at 8-bit depth:
    grayscale (0), RGB (2), palette (3), grayscale+alpha (4), RGBA (6).
    Mostly-transparent pixels fall back to the neutral tint.
    """
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: %s" % path)

    color_type = bit_depth = None
    palette = b""
    idat = b""
    i = 8
    while i < len(data):
        (length,) = struct.unpack(">I", data[i:i + 4])
        ctype = data[i + 4:i + 8]
        chunk = data[i + 8:i + 8 + length]
        if ctype == b"IHDR":
            bit_depth = chunk[8]
            color_type = chunk[9]
        elif ctype == b"PLTE":
            palette = chunk
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
        i += 12 + length

    if bit_depth != 8:
        raise ValueError("unsupported bit depth %r in %s" % (bit_depth, path))

    raw = zlib.decompress(idat)
    px = raw[1:]  # drop the per-row filter byte (row 0 of a 1x1 image)

    if color_type == 2:            # RGB
        return px[0], px[1], px[2]
    if color_type == 6:            # RGBA
        if px[3] < 128:
            return NEUTRAL
        return px[0], px[1], px[2]
    if color_type == 0:            # grayscale
        g = px[0]
        return g, g, g
    if color_type == 4:            # grayscale + alpha
        if px[1] < 128:
            return NEUTRAL
        g = px[0]
        return g, g, g
    if color_type == 3:            # palette
        idx = px[0]
        return palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]

    raise ValueError("unsupported PNG colour type %r in %s" % (color_type, path))


def gif_1x1(r, g, b):
    """Build a minimal 1x1 GIF89a filled with the given colour (35 bytes)."""
    header = b"GIF89a"
    # Logical screen: 1x1, 2-entry global colour table (packed byte 0xF0).
    lsd = struct.pack("<HH", 1, 1) + bytes([0xF0, 0, 0])
    gct = bytes([r, g, b, 0, 0, 0])
    # Image descriptor at (0,0), 1x1, no local colour table.
    img = b"\x2C" + struct.pack("<HHHH", 0, 0, 1, 1) + b"\x00"
    # LZW min code size 2; one data sub-block: clear, index 0, end-of-info.
    img += bytes([0x02, 0x02, 0x44, 0x01, 0x00])
    return header + lsd + gct + img + b"\x3B"


def read_gif_pixel(path):
    """Return (r, g, b) from a preview GIF we generated (fixed GIF89a layout).

    The global colour table's first entry sits right after the 6-byte header and
    7-byte logical screen descriptor, i.e. at byte offset 13.
    """
    data = open(path, "rb").read()
    if data[:6] not in (b"GIF89a", b"GIF87a") or len(data) < 16:
        raise ValueError("not a preview GIF: %s" % path)
    return data[13], data[14], data[15]


# One <img ...> tag (attribute values are quoted and contain no ">", so this is
# safe for the site's single-line image tags).
IMG_TAG_RE = re.compile(r"<img\b[^>]*>")
SRC_ATTR_RE = re.compile(r'\bsrc="([^"]+)"')
DATA_LQIP_RE = re.compile(r'\s*data-lqip="[^"]*"')


def sync_html(colors):
    """Stamp ``data-lqip="#rrggbb"`` onto every <img> whose src has a known colour.

    ``colors`` maps an absolute source-image path to its (r, g, b). Idempotent:
    an existing data-lqip is replaced, so re-running produces no further changes.
    Returns the number of attributes written.
    """
    by_src = {}
    for src, rgb in colors.items():
        rel = os.path.relpath(src, REPO).replace(os.sep, "/")
        by_src[rel] = "#%02x%02x%02x" % rgb

    def patch_tag(match):
        tag = match.group(0)
        src_match = SRC_ATTR_RE.search(tag)
        if not src_match:
            return tag
        hexcolor = by_src.get(src_match.group(1))
        if not hexcolor:
            return tag
        tag = DATA_LQIP_RE.sub("", tag)          # drop any stale data-lqip
        src_match = SRC_ATTR_RE.search(tag)      # re-locate (tag may have shifted)
        end = src_match.end()
        return tag[:end] + ' data-lqip="%s"' % hexcolor + tag[end:]

    written = 0
    for name in sorted(os.listdir(REPO)):
        if not name.endswith(".html"):
            continue
        path = os.path.join(REPO, name)
        original = open(path, encoding="utf-8").read()
        patched, _ = IMG_TAG_RE.subn(patch_tag, original)
        if patched != original:
            open(path, "w", encoding="utf-8").write(patched)
        written += sum(1 for _ in DATA_LQIP_RE.finditer(patched))
    return written


def iter_sources():
    for root, _dirs, files in os.walk(ASSETS):
        for name in files:
            lower = name.lower()
            if lower.endswith(PREVIEW_SUFFIX):
                continue
            if os.path.splitext(lower)[1] in SOURCE_EXTS:
                yield os.path.join(root, name)


def preview_path(src):
    stem, _ext = os.path.splitext(src)
    return stem + PREVIEW_SUFFIX


def main():
    if not os.path.isdir(ASSETS):
        sys.exit("assets/img not found at %s" % ASSETS)

    made = skipped = failed = 0
    colors = {}  # source image path -> (r, g, b), for the HTML data-lqip sync
    for src in sorted(iter_sources()):
        dst = preview_path(src)
        # Idempotent: skip when the preview is newer than its source.
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            skipped += 1
        else:
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_png = tmp.name
                try:
                    sips_pixel_png(src, tmp_png)
                    r, g, b = read_png_pixel(tmp_png)
                finally:
                    os.unlink(tmp_png)
                with open(dst, "wb") as fh:
                    fh.write(gif_1x1(r, g, b))
                made += 1
                print("  %s  #%02x%02x%02x" % (os.path.relpath(dst, ASSETS), r, g, b))
            except Exception as exc:  # noqa: BLE001 - report and continue
                failed += 1
                print("  FAILED %s: %s" % (os.path.relpath(src, ASSETS), exc), file=sys.stderr)
                continue
        # Record the colour (read back from the preview) so the HTML stays in sync.
        try:
            colors[src] = read_gif_pixel(dst)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print("  FAILED reading %s: %s" % (os.path.relpath(dst, ASSETS), exc), file=sys.stderr)

    stamped = sync_html(colors)

    print("previews: %d written, %d up-to-date, %d failed; %d data-lqip in sync"
          % (made, skipped, failed, stamped))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
