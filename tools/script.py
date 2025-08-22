#!/usr/bin/python3
# Emits shared JS helpers (hotkeys, row dbl-click, etc.) for all.py
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("Content-Type: application/javascript; charset=utf-8\r\n\r\n")

js = r'''
(function () {
  "use strict";

  function toggleColumn(colClass) {
    document.querySelectorAll("." + colClass).forEach((el) => {
      el.classList.toggle("hidden-col");
    });
  }

  function enterEditMode(on) {
    const root = document.documentElement;
    if (on === undefined) root.classList.toggle("edit-mode");
    else root.classList.toggle("edit-mode", !!on);

    const enabled = root.classList.contains("edit-mode");
    localStorage.setItem("runtriage_editmode", enabled ? "1" : "0");

    const btn = document.getElementById("btnEditMode");
    if (btn) {
      btn.textContent = enabled
        ? "Exit Edit Mode (Ctrl+E)"
        : "Enter Edit Mode (Ctrl+E)";
    }
  }

  function showToast(msg) {
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 1600);
  }

  function saveChanges() {
    const form = document.getElementById("bulkForm");
    if (!form) return;
    showToast("Saving…");
    form.submit();
  }

  function attachRowDblClick() {
    const rows = document.querySelectorAll("table tbody tr");
    rows.forEach((tr) => {
      tr.addEventListener(
        "dblclick",
        function () { tr.classList.toggle("row-edit"); },
        { passive: true }
      );
    });
  }

  function rewireAfterHydration() {
    attachRowDblClick();
    if (localStorage.getItem("runtriage_editmode") === "1") {
      enterEditMode(true);
    }
  }

  // Hotkeys: Ctrl/Cmd+E (toggle edit), Ctrl/Cmd+S (save)
  document.addEventListener("keydown", (e) => {
    const key = (e.key || "").toLowerCase();
    const mod = e.ctrlKey || e.metaKey;
    if (mod && key === "e") { e.preventDefault(); enterEditMode(); return; }
    if (mod && key === "s") { e.preventDefault(); saveChanges(); return; }
  });

  // Stop legacy plain 'e' handlers from firing while typing
  document.addEventListener("keydown", (e) => {
    const key = (e.key || "").toLowerCase();
    if (key !== "e") return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const t = e.target;
    const tag = t && t.tagName ? t.tagName.toLowerCase() : "";
    const inEditable = tag === "input" || tag === "textarea" || tag === "select" || t.isContentEditable;
    if (inEditable) e.stopPropagation();
  }, true);

  document.addEventListener("DOMContentLoaded", () => {
    if (localStorage.getItem("runtriage_editmode") === "1") {
      enterEditMode(true);
    }
    attachRowDblClick();
  });

  // expose for inline handlers / filter_ui
  window.toggleColumn = toggleColumn;
  window.enterEditMode = enterEditMode;
  window.saveChanges = saveChanges;
  window.showToast = showToast;
  window.rewireAfterHydration = rewireAfterHydration;


  
})();

(function(){
  function positionPanel(panel, anchorEl){
    // Default: fixed near bottom-right if no anchor provided
    if(!anchorEl){
      panel.style.right = "18px";
      panel.style.bottom = "60px";
      panel.style.left = "";
      panel.style.top = "";
      return;
    }
    const r = anchorEl.getBoundingClientRect();
    const margin = 8;
    // Prefer to open below the button; if not enough room, open above
    const openBelow = (window.innerHeight - r.bottom) >= 200;
    const top = openBelow ? (r.bottom + margin) : (r.top - panel.offsetHeight - margin);
    // Align left edge with button’s left, but keep within viewport
    let left = r.left;
    const maxLeft = window.innerWidth - panel.offsetWidth - margin;
    if (left > maxLeft) left = Math.max(margin, maxLeft);
    panel.style.left = left + "px";
    panel.style.top = Math.max(margin, top) + "px";
    panel.style.right = "";
    panel.style.bottom = "";
  }

  function openHelp(anchorId){
    const panel = document.getElementById("help-popup");
    if(!panel) return;
    panel.style.display = "block";
    // force layout so offsetHeight is valid for positioning above
    panel.getBoundingClientRect();
    const anchor = anchorId ? document.getElementById(anchorId) : null;
    positionPanel(panel, anchor);
  }
  function closeHelp(){
    const panel = document.getElementById("help-popup");
    if(panel) panel.style.display = "none";
  }
  function toggleHelp(anchorId){
    const panel = document.getElementById("help-popup");
    if(!panel) return;
    if(panel.style.display === "block") closeHelp();
    else openHelp(anchorId);
  }

  document.addEventListener("DOMContentLoaded", function(){
    const btn = document.getElementById("help-square");
    if(btn){
      btn.addEventListener("click", function(e){
        e.stopPropagation();
        toggleHelp(); // bottom-right floating
      });
    }
  });

  // Close on outside click / ESC
  document.addEventListener("click", function(e){
    const panel = document.getElementById("help-popup");
    if(!panel || panel.style.display !== "block") return;
    const helpBtn = document.getElementById("btnHelp");
    if(!panel.contains(e.target) && e.target !== helpBtn){
      closeHelp();
    }
  });
  document.addEventListener("keydown", function(e){
    if((e.key||"").toLowerCase() === "escape") closeHelp();
  });

  // Expose for inline handlers
  window.openHelp = openHelp;
  window.toggleHelp = toggleHelp;
})();


// --- Lightbox ---
function openLightbox(src, title) {
  var root = document.getElementById("lb-root");
  if (!root) return;
  var img = document.getElementById("lb-img");
  var ttl = document.getElementById("lb-title");
  img.src = src;
  img.alt = title || "";
  ttl.textContent = title || "";
  root.classList.add("open");
  root.setAttribute("aria-hidden", "false");
}
function closeLightbox() {
  var root = document.getElementById("lb-root");
  if (!root) return;
  var img = document.getElementById("lb-img");
  img.src = "";
  root.classList.remove("open");
  root.setAttribute("aria-hidden", "true");
}
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") closeLightbox();
});

// expose
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;


// ---- Image Gallery (full preview of all PNGs in dir) ----
// ---- Image Gallery (reads <template> of <a> elements; no JSON) ----
(function(){
  "use strict";
  let G = { list: [], idx: 0, title: "" };

  function buildFilmstrip() {
    const film = document.getElementById("gal-film");
    film.innerHTML = "";
    G.list.forEach((it, i) => {
      const im = document.createElement("img");
      im.src = it.url;
      im.alt = it.name || "";
      if (i === G.idx) im.classList.add("active");
      im.addEventListener("click", () => { showIndex(i); });
      film.appendChild(im);
    });
  }

  function showIndex(i) {
    if (!G.list.length) return;
    if (i < 0) i = G.list.length - 1;
    if (i >= G.list.length) i = 0;
    G.idx = i;
    const cur = G.list[G.idx];
    const img = document.getElementById("gal-img");
    img.src = cur.url;
    img.alt = cur.name || "";
    document.getElementById("gal-title").textContent = G.title || "";
    document.getElementById("gal-fname").textContent = cur.name || "";
    document.getElementById("gal-count").textContent = (G.idx+1) + " / " + G.list.length;
    const open = document.getElementById("gal-open");
    open.href = cur.url;

    const thumbs = document.querySelectorAll("#gal-film img");
    thumbs.forEach((t, k) => t.classList.toggle("active", k === G.idx));
  }

  function navGallery(delta) { showIndex(G.idx + delta); }

  function openGalleryFromTemplate(btn) {
    if (!btn) return;
    const tid = btn.getAttribute("data-tmpl");
    const title = btn.getAttribute("data-title") || "";
    if (!tid) return;

    const tpl = document.getElementById(tid);
    if (!tpl) return;

    const container = tpl.content ? tpl.content : tpl; // template or fallback
    const anchors = container.querySelectorAll("a[href]");
    const list = [];
    anchors.forEach(a => {
      list.push({ url: a.getAttribute("href"), name: a.getAttribute("data-name") || "" });
    });
    if (!list.length) return;

    G.list = list;
    G.idx = 0;
    G.title = title;

    buildFilmstrip();
    showIndex(0);

    const root = document.getElementById("gal-root");
    if (!root) return;
    root.classList.add("open");
    root.setAttribute("aria-hidden", "false");
  }

  function closeGallery() {
    const root = document.getElementById("gal-root");
    if (!root) return;
    root.classList.remove("open");
    root.setAttribute("aria-hidden", "true");
    const img = document.getElementById("gal-img");
    if (img) img.src = "";
  }

  document.addEventListener("keydown", (e) => {
    const root = document.getElementById("gal-root");
    if (!root || !root.classList.contains("open")) return;
    if (e.key === "Escape") { e.preventDefault(); closeGallery(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); navGallery(1); }
    else if (e.key === "ArrowLeft")  { e.preventDefault(); navGallery(-1); }
  });

  // expose
  window.openGalleryFromTemplate = openGalleryFromTemplate;
  window.closeGallery = closeGallery;
  window.navGallery = navGallery;
})();


'''
print(js)
