/* ==========================================================================
   sebastianruss.com — LQIP (low-quality image placeholder), progressive
   enhancement. Each image is wrapped in a .lqip-frame that shows the image's
   dominant colour (the data-lqip="#rrggbb" attribute stamped by
   `make previews`) while the real image loads. The <img> keeps its own src /
   srcset and loads natively — nothing is held, cancelled or fetched twice —
   and is kept at visibility:hidden until it has fully downloaded AND decoded,
   then revealed whole (never painted progressively row by row).

   Because the placeholder colour is inline (no network request), it paints
   instantly and never competes with the real images for connections — so the
   dominant colour is visible for the WHOLE load, even on the home grid where
   many large thumbnails download at once. All images load eagerly (no
   scroll-based lazy loading). Older images without a data-lqip fall back to the
   generated <name>_preview.gif as a background. Without JS there is no frame and
   images load normally. No dependencies, no build step. See
   tools/generate-previews.py.
   ========================================================================== */
(function () {
  document.documentElement.classList.add("lqip-js");

  // e.g. assets/img/Hello/foo.jpg -> assets/img/Hello/foo_preview.gif
  function previewURL(src) {
    return src.replace(/\.(jpe?g|png|gif)(\?.*)?$/i, "_preview.gif");
  }

  function frameFor(img) {
    var src = img.getAttribute("src");
    if (!src) return;
    var parent = img.parentNode;
    if (!parent) return;
    if (parent.classList && parent.classList.contains("lqip-frame")) return;

    // Prefer the inline dominant colour; fall back to the preview GIF background.
    var color = img.getAttribute("data-lqip");
    var preview = previewURL(src);
    if (!color && preview === src) return;             // unknown extension, no colour

    // Wrap the image in a frame carrying the dominant-colour placeholder.
    var frame = document.createElement("span");
    frame.className = "lqip-frame";
    if (color) {
      frame.style.backgroundColor = color;
    } else {
      frame.style.setProperty("--lqip", "url('" + preview + "')");
    }
    parent.insertBefore(frame, img);
    frame.appendChild(img);

    function reveal() {
      frame.classList.add("is-loaded");        // makes the <img> visible (CSS)
      // Drop the placeholder so transparent images show the page, not the tint.
      frame.style.removeProperty("--lqip");
      frame.style.backgroundColor = "";
      img.removeEventListener("load", onload);
      img.removeEventListener("error", reveal);
    }
    function onload() {
      // Prefer revealing once decoded (a single clean paint), but never block on
      // it — decode() can stall indefinitely in a background/throttled tab, and
      // the load event already means the full image is downloaded.
      if (!img.decode) { reveal(); return; }
      var settled = false;
      function finish() { if (!settled) { settled = true; reveal(); } }
      img.decode().then(finish, finish);
      setTimeout(finish, 100);
    }

    if (img.complete && img.naturalWidth > 0) { reveal(); return; }
    img.addEventListener("load", onload);
    img.addEventListener("error", reveal);
    // No holding: the <img> loads natively while the frame shows the colour, so
    // nothing is cancelled or fetched twice and srcset selection is untouched.
    // Moving a loading="lazy" <img> in the DOM pauses its native load, so resume
    // it by removing the attribute.
    img.removeAttribute("loading");
  }

  var imgs = document.querySelectorAll("img");
  for (var i = 0; i < imgs.length; i++) frameFor(imgs[i]);
})();
