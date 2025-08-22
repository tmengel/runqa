#!/usr/bin/python3
# Emits JS that builds the floating filter window and wires Ctrl/Cmd+F to open it.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
print("Content-Type: application/javascript; charset=utf-8\r\n\r\n")

js = r'''
(function(){

  // --- Utilities ---
  function qs(k) {
    const u = new URL(window.location.href);
    return u.searchParams.get(k);
  }
  function buildURL(obj) {
    const u = new URL(window.location.href);
    // remove known keys first so we don't accumulate stale ones
    ['run_number','run_min','run_max','run_type','page_size',
     'notes_contains','require_class','subsys','subsys_class',
     'track_ready','calo_ready','page'].forEach(k => u.searchParams.delete(k));
    for (const [k,v] of Object.entries(obj)) {
      if (v === null || v === undefined || v === '') continue;
      u.searchParams.set(k, v);
    }
    return u;
  }
  function debounce(fn, ms) {
    let t = null;
    return function(...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), ms);
    };
  }
  function el(tag, attrs={}, children=[]) {
    const e = document.createElement(tag);
    for (const [k,v] of Object.entries(attrs||{})) {
      if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
      else if (k === 'class') e.className = v;
      else e.setAttribute(k, v);
    }
    for (const c of (children||[])) {
      if (typeof c === 'string') e.insertAdjacentHTML('beforeend', c);
      else if (c) e.appendChild(c);
    }
    return e;
  }

  // Compare intended query with current (avoid useless fetch)
  function qsEquals(obj) {
    const cur = new URL(window.location.href).searchParams;
    const next = new URL(window.location.href);
    Object.entries(obj).forEach(([k,v]) => {
      if (v === '' || v === null || v === undefined) next.searchParams.delete(k);
      else next.searchParams.set(k, v);
    });
    // normalize: remove empty we would have deleted
    for (const [k,v] of Array.from(next.searchParams.entries())) {
      if (v === '') next.searchParams.delete(k);
    }
    return next.search === new URL(window.location.href).search;
  }

  // --- AJAX page updater ---
  async function hydrateResults(obj, restore) {
    const u = buildURL(obj);
    if (qsEquals(obj)) return; // nothing changed
    // Stash focus/caret in panel
    const ae = document.activeElement;
    const focusInfo = (ae && ae.id && (ae === document.getElementById('f_notes') ||
                                       ae === document.getElementById('f_run_number') ||
                                       ae === document.getElementById('f_run_min') ||
                                       ae === document.getElementById('f_run_max') ||
                                       ae === document.getElementById('f_page_size'))) ? {
      id: ae.id,
      s: ('selectionStart' in ae ? ae.selectionStart : null),
      e: ('selectionEnd'   in ae ? ae.selectionEnd   : null)
    } : null;

    // Fetch new HTML for the page
    const res = await fetch(u.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' }});
    if (!res.ok) return;
    const html = await res.text();

    // Parse and grab #resultsRoot from the response
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const newRoot = doc.getElementById('resultsRoot');
    if (!newRoot) return;

    // Swap current #resultsRoot
    const curRoot = document.getElementById('resultsRoot');
    if (curRoot) curRoot.replaceWith(newRoot);

    // Update URL without reload
    history.replaceState(null, '', u.toString());

    // Rewire per-row events if the host page provides a hook
    if (typeof window.rewireAfterHydration === 'function') {
      try { window.rewireAfterHydration(); } catch(e) {}
    }

    // Restore focus/caret inside panel so user keeps typing
    if (restore !== false && focusInfo) {
      const el = document.getElementById(focusInfo.id);
      if (el) {
        el.focus();
        if (Number.isFinite(focusInfo.s) && Number.isFinite(focusInfo.e) && 'setSelectionRange' in el) {
          try { el.setSelectionRange(focusInfo.s, focusInfo.e); } catch(_){}
        }
      }
    }
  }

  // --- Floating Panel state ---
  const LS_OPEN = 'rt_filter_open';
  const LS_POSX = 'rt_filter_x';
  const LS_POSY = 'rt_filter_y';

  // --- Build Panel UI ---
  function buildPanel() {
    if (document.getElementById('rtFilterPanel')) return;

    const panel = el('div', { id:'rtFilterPanel', style:{
      position:'fixed', top: (localStorage.getItem(LS_POSY)||'20')+'px',
      left:(localStorage.getItem(LS_POSX)||'20')+'px',
      width:'360px', background:'#fff', border:'1px solid #999',
      borderRadius:'8px', boxShadow:'0 6px 18px rgba(0,0,0,.2)', zIndex:99999,
      padding:'10px', font:'13px Arial,sans-serif'
    }});

    panel.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px; cursor:move;" id="rtDragBar">
        <strong>Filters</strong>
        <div style="display:flex;gap:6px;align-items:center;">
          <button type="button" id="rtApplyNow" style="padding:2px 8px;">Apply</button>
          <button type="button" id="rtClose" title="Close">×</button>
        </div>
      </div>
      <div style="display:grid;grid-template-columns: 1fr 1fr; gap:6px;">
        <label>Run # (exact)<br><input id="f_run_number" type="text" style="width:100%"></label>
        <label>Page size<br><input id="f_page_size" type="text" style="width:100%"></label>

        <label>Run ≥<br><input id="f_run_min" type="text" style="width:100%"></label>
        <label>Run ≤<br><input id="f_run_max" type="text" style="width:100%"></label>

        <label>Type<br>
          <select id="f_run_type" style="width:100%">
            <option value="">-- Any --</option>
            <option value="physics">Physics</option>
            <option value="cosmics">Cosmics</option>
            <option value="calibration">Calibration</option>
          </select>
        </label>
        <span></span>

        <!-- New / useful -->
        <label>Notes contains<br><input id="f_notes" type="text" placeholder="substring" style="width:100%"></label>
        <label>Require class (any sub)<br>
          <select id="f_class_any" style="width:100%">
            <option value="">-- none --</option>
            <option value="GOLDEN">GOLDEN</option>
            <option value="QUESTIONABLE">QUESTIONABLE</option>
            <option value="BAD">BAD</option>
          </select>
        </label>

        <label>Subsystem<br>
          <select id="f_subsys" style="width:100%">
            <option value="">-- any --</option>
            <option>MVTX</option><option>INTT</option><option>TPC</option><option>TPOT</option>
            <option>EMCAL</option><option>IHCAL</option><option>OHCAL</option><option>MBD</option>
            <option>ZDC</option><option>sEPD</option>
          </select>
        </label>
        <label>Class for subsystem<br>
          <select id="f_subsys_class" style="width:100%">
            <option value="">-- none --</option>
            <option value="GOLDEN">GOLDEN</option>
            <option value="QUESTIONABLE">QUESTIONABLE</option>
            <option value="BAD">BAD</option>
          </select>
        </label>

        <label><input id="f_track_ready" type="checkbox"> Tracking QA ready</label>
        <label><input id="f_calo_ready"  type="checkbox"> Calo QA ready</label>
      </div>
    `;

    document.body.appendChild(panel);

    // Draggable by top bar
    let drag=false, sx=0, sy=0, ox=0, oy=0;
    const dragBar = document.getElementById('rtDragBar');
    dragBar.addEventListener('mousedown', function(e){
      drag = true; sx = e.clientX; sy = e.clientY; ox = panel.offsetLeft; oy = panel.offsetTop; e.preventDefault();
    });
    document.addEventListener('mousemove', function(e){
      if (!drag) return;
      panel.style.left = (ox + (e.clientX - sx)) + 'px';
      panel.style.top  = (oy + (e.clientY - sy)) + 'px';
    });
    document.addEventListener('mouseup', function(){
      if (!drag) return; drag=false;
      localStorage.setItem(LS_POSX, parseInt(panel.style.left,10));
      localStorage.setItem(LS_POSY, parseInt(panel.style.top,10));
    });

    // Controls -> query mapping
    const controls = {
      f_run_number: 'run_number',
      f_run_min: 'run_min',
      f_run_max: 'run_max',
      f_run_type: 'run_type',
      f_page_size: 'page_size',
      f_notes: 'notes_contains',
      f_class_any: 'require_class',
      f_subsys: 'subsys',
      f_subsys_class: 'subsys_class',
      f_track_ready: 'track_ready',
      f_calo_ready:  'calo_ready',
    };

    // Init from current QS
    Object.entries(controls).forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (!el) return;
      const v = qs(key);
      if (el.type === 'checkbox') el.checked = (v === '1' || v === 'true');
      else if (v !== null) el.value = v;
    });

    // IME friendly: don't trigger while composing in notes
    let composing = false;
    const notes = document.getElementById('f_notes');
    notes.addEventListener('compositionstart', ()=> composing=true);
    notes.addEventListener('compositionend',   ()=> composing=false);

    function collectObj() {
      const obj = {};
      Object.entries(controls).forEach(([id, key]) => {
        const el = document.getElementById(id);
        if (!el) return;
        obj[key] = (el.type === 'checkbox') ? (el.checked ? '1' : '') : (el.value || '').trim();
      });
      obj.page = '1';
      return obj;
    }

    const applyGeneral = debounce(() => {
      const obj = collectObj();
      hydrateResults(obj);
    }, 300);

    const applyNotes = debounce(() => {
      if (composing) return;
      const obj = collectObj();
      hydrateResults(obj);
    }, 600);

    for (const id of Object.keys(controls)) {
      const el = document.getElementById(id);
      if (!el) continue;
      const handler = (id === 'f_notes') ? applyNotes : applyGeneral;
      el.addEventListener('input', handler);
      el.addEventListener('change', handler);
    }

    document.getElementById('rtApplyNow').addEventListener('click', () => {
      hydrateResults(collectObj());
    });

    document.getElementById('rtClose').addEventListener('click', () => {
      panel.remove();
      localStorage.removeItem(LS_OPEN);
    });
  }

  function ensurePanelOpen() {
    buildPanel();
  }

  // Hotkey: Ctrl/Cmd+F opens filters (prevents browser find)
  document.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && (e.key || '').toLowerCase() === 'f') {
      e.preventDefault();
      ensurePanelOpen();
      localStorage.setItem(LS_OPEN, '1');
      setTimeout(()=>{ const n = document.getElementById('f_notes'); if (n) n.focus(); }, 0);
    }
  });

  // Reopen panel on load if it was open
  document.addEventListener('DOMContentLoaded', function(){
    if (localStorage.getItem(LS_OPEN) === '1') ensurePanelOpen();
  });

})();
'''
print(js)
