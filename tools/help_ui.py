#!/usr/bin/python3
# Emits JS that builds a floating Help/Hotkeys window; opens via Ctrl+/ or button.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
print("Content-Type: application/javascript; charset=utf-8\r\n\r\n")

js = r'''
(function(){
  "use strict";

  // --- Small utils ---
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

  // LocalStorage keys
  const LS_OPEN = 'rt_help_open';
  const LS_POSX = 'rt_help_x';
  const LS_POSY = 'rt_help_y';

  // Build panel once
  function buildPanel() {
    if (document.getElementById('rtHelpPanel')) return;

    const panel = el('div', {
      id:'rtHelpPanel',
      style:{
        position:'fixed',
        top: (localStorage.getItem(LS_POSY)||'60')+'px',
        left:(localStorage.getItem(LS_POSX)||'60')+'px',
        width:'360px',
        background:'#fff',
        border:'1px solid #999',
        borderRadius:'8px',
        boxShadow:'0 6px 18px rgba(0,0,0,.2)',
        zIndex:99999,
        padding:'10px',
        font:'13px Arial,sans-serif',
        display:'none'
      }
    });

    panel.innerHTML = `
      <div id="rtHelpDragBar" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px; cursor:move;">
        <strong>Help / Hotkeys</strong>
        <div style="display:flex;gap:6px;align-items:center;">
          <button type="button" id="rtHelpClose" title="Close">×</button>
        </div>
      </div>
      <div>
        <ul style="margin:0; padding-left:18px;">
          <li><code>Ctrl</code> + <code>E</code> — Toggle edit mode</li>
          <li><code>Ctrl</code> + <code>S</code> — Save changes</li>
          <li>Double-click a row — Edit that row only</li>
          <li>Buttons — Show/Hide Offline/Online QA columns</li>
          <li><code>Ctrl</code> + <code>F</code> — Open filter window</li>
          <li><code>Ctrl</code> + <code>H</code> — Open this help window</li>
          <li><code>Esc</code> — Close this window</li>
        </ul>
      </div>
    `;

    document.body.appendChild(panel);

    // Dragging
    let drag=false, sx=0, sy=0, ox=0, oy=0;
    const dragBar = document.getElementById('rtHelpDragBar');
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

    document.getElementById('rtHelpClose').addEventListener('click', closeHelp);
  }

  // Position relative to an anchor (button) if given
  function positionToAnchor(panel, anchorEl){
    if (!anchorEl) return;
    const r = anchorEl.getBoundingClientRect();
    const m = 8;
    const below = (window.innerHeight - r.bottom) >= 200;
    const top = below ? (r.bottom + m) : (r.top - panel.offsetHeight - m);
    let left = r.left;
    const maxLeft = window.innerWidth - panel.offsetWidth - m;
    if (left > maxLeft) left = Math.max(m, maxLeft);
    panel.style.left = left + "px";
    panel.style.top  = Math.max(m, top) + "px";
  }

  function openHelp(anchorId){
    buildPanel();
    const panel = document.getElementById('rtHelpPanel');
    if (!panel) return;
    panel.style.display = 'block';
    panel.getBoundingClientRect(); // layout
    if (anchorId){
      const btn = document.getElementById(anchorId);
      if (btn) positionToAnchor(panel, btn);
    }
    localStorage.setItem(LS_OPEN, '1');
  }

  function closeHelp(){
    const panel = document.getElementById('rtHelpPanel');
    if (panel) panel.style.display = 'none';
    localStorage.removeItem(LS_OPEN);
  }

  function toggleHelp(anchorId){
    const panel = document.getElementById('rtHelpPanel');
    if (!panel || panel.style.display !== 'block') openHelp(anchorId);
    else closeHelp();
  }

  // Hotkey: Ctrl+/ toggles help (common “keyboard shortcuts” pattern)
  document.addEventListener('keydown', function(e){
    const key = (e.key||'').toLowerCase();
    if ((e.ctrlKey || e.metaKey) && key === 'h'){
      e.preventDefault();
      toggleHelp('btnHelp');
    }
    if (key === 'escape') closeHelp();
  });

  // Click outside closes
  document.addEventListener('click', function(e){
    const panel = document.getElementById('rtHelpPanel');
    if (!panel || panel.style.display !== 'block') return;
    const helpBtn = document.getElementById('btnHelp');
    if (!panel.contains(e.target) && e.target !== helpBtn) closeHelp();
  });

  // Reopen if it was open
  document.addEventListener('DOMContentLoaded', function(){
    buildPanel();
    if (localStorage.getItem(LS_OPEN) === '1'){
      const panel = document.getElementById('rtHelpPanel');
      if (panel) panel.style.display = 'block';
    }
  });

  // Expose for inline button
  window.openHelp = openHelp;
  window.toggleHelp = toggleHelp;
})();
'''
print(js)
