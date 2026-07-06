/* ==========================================================================
   sebastianruss.com — home masonry (progressive enhancement)
   The home grid works without JavaScript as a CSS multi-column masonry.
   When JS is available this upgrades it to a shortest-column layout (like the
   original site): cards of differing heights tile organically AND a filtered
   category spreads across every column, filling the full width.
   No dependencies, no build step.
   ========================================================================== */
(function () {
  var root = document.documentElement;
  root.classList.add("js");

  var grid = document.querySelector(".grid");
  if (!grid) return;

  // Capture the cards once, in their authored order.
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));

  var tagChip = document.querySelector(".filter-tag");

  // The hash *is* the tag class, e.g. #tag-robot or #tag-2009. Any card class
  // works, so new tags need no JS changes.
  function activeTag() {
    var h = location.hash.replace(/^#/, "");
    return /^tag-/.test(h) ? h : null;
  }

  function prettyTag(tag) {
    var s = tag.replace(/^tag-/, "");
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function columnCount() {
    // Match the CSS fallback: ~300px columns, at least two.
    return Math.max(2, Math.floor(grid.clientWidth / 300));
  }

  function layout() {
    var tag = activeTag();

    // Drive the active-filter status bar (the CSS shows it on body.filtering).
    document.body.classList.toggle("filtering", !!tag);
    if (tagChip) tagChip.textContent = tag ? prettyTag(tag) : "";

    var visible = cards.filter(function (card) {
      return !tag || card.classList.contains(tag);
    });

    var n = columnCount();
    grid.textContent = "";

    var cols = [];
    for (var i = 0; i < n; i++) {
      var col = document.createElement("div");
      col.className = "masonry-col";
      grid.appendChild(col);
      cols.push(col);
    }

    // Append each card to the currently shortest column. Image dimensions are
    // set via width/height attributes, so column height is accurate even
    // before the images finish loading.
    visible.forEach(function (card) {
      var shortest = cols[0];
      for (var i = 1; i < cols.length; i++) {
        if (cols[i].offsetHeight < shortest.offsetHeight) shortest = cols[i];
      }
      shortest.appendChild(card);
    });
  }

  layout();

  window.addEventListener("hashchange", layout);

  var resizeTimer;
  var lastCols = columnCount();
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      // Only re-flow when the column count actually changes.
      var next = columnCount();
      if (next !== lastCols) {
        lastCols = next;
        layout();
      }
    }, 150);
  });
})();
