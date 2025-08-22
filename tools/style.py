#!/usr/bin/python3
# Emits CSS for all.py (so we don't inline a giant <style> block)
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("Content-Type: text/css; charset=utf-8\r\n\r\n")

css = r'''
/* --- Layout / Typography --- */
body { font-family: Arial, sans-serif; }
table { border-collapse: collapse; font-size: 13px; width: 100%; }
th, td { padding: 6px 10px; text-align: center; vertical-align: middle; }
thead th { position: sticky; top: 0; background: #f4f7fb; z-index: 2; }
select { font-size: 12px; padding: 2px 4px; width: 70px; }
textarea { font-size: 12px; width: 220px; min-height: 26px; resize: vertical; }

/* --- Color states --- */
.golden { background-color: #c8f7c5; }
.questionable { background-color: #000000; color: white; }
.bad { background-color: #f7c5c5; }
.unknown { background-color: #ffffff; }

/* --- Pagination --- */
.pagination { text-align: center; margin: 16px 0; font-size: 14px; }
.pagination a, .pagination strong {
  display:inline-block; padding:6px 10px; margin:2px;
  border:1px solid #ccc; border-radius:5px; text-decoration:none;
  background:#f8f8f8; color:#005b96;
}
.pagination a:hover { background:#e6f2ff; border-color:#88c; }
.pagination strong { background:#005b96; color:#fff; border-color:#005b96; }

/* --- Filters panel (inline on page) --- */
.filters { margin-bottom: 10px; padding: 8px; background:#f9f9f9; border:1px solid #ccc; border-radius:6px; }
.active-filters { margin-top: 6px; color:#333; }

/* --- Column toggling --- */
.hidden-col { display: none; }

/* --- Edit controls / buttons --- */
.edit-controls { display:flex; gap:6px; align-items:center; }
.btn { padding:4px 8px; border:1px solid #bbb; background:#fff; border-radius:4px; cursor:pointer; }
.btn:hover { background:#eef4ff; }
.btn.primary { background:#005b96; color:#fff; border-color:#005b96; }

/* --- Pill labels in view mode --- */
.pill { display:inline-block; padding:2px 6px; border-radius:12px; font-weight:bold; }
.pill.g { background:#aee3a9; }
.pill.q { background:#555; color:#fff; }
.pill.b { background:#f3a7a7; }

/* --- Cell wrappers / edit-mode visibility --- */
.label-wrap { display:flex; flex-direction:column; gap:4px; align-items:center; }
.cell-edit { display:none; }
.edit-mode .cell-edit { display:block; }
.edit-mode .cell-view { display:none; }

/* --- Per-row editing (double-click) --- */
tbody tr { cursor: pointer; }       /* visual hint */
.row-edit .cell-edit { display: block; }
.row-edit .cell-view { display: none; }

/* --- Toast --- */
.toast {
  position: fixed; right: 12px; bottom: 12px;
  background: #333; color:#fff; padding:8px 12px; border-radius:6px;
  opacity:0; transition:opacity .2s;
}
.toast.show { opacity: 0.95; }

.pager-summary { margin:8px 0; color:#333; }
.pager-links { text-align:center; margin:6px 0; }
.pager-links a, .pager-links strong, .pager-links span { display:inline-block; padding:6px 10px; margin:2px; border:1px solid #ccc; border-radius:5px; text-decoration:none; background:#f8f8f8; color:#005b96; }
.pager-links a:hover { background:#e6f2ff; border-color:#88c; }
.pager-links strong { background:#005b96; color:#fff; border-color:#005b96; }
.pager-links span { background:#fff; border-color:transparent; }

#help-popup{
  position:fixed; right:18px; bottom:60px; width:260px; max-width:80vw;
  background:#f9f9f9; border:1px solid #ddd; border-radius:8px; padding:12px 14px;
  box-shadow:0 2px 10px rgba(0,0,0,.25); z-index:1000; display:none;
}
#help-popup h3{ margin:0 0 8px 0; font-size:15px; }
#help-popup ul{ margin:0; padding-left:18px; font-size:13px; }
#help-popup .kbd{ font-family:monospace; background:#eee; padding:1px 4px; border-radius:4px; }

/* --- Floating panel base (used by Help popup) --- */
.floating-panel{
  position:fixed;
  min-width:240px; max-width:80vw;
  background:#f9f9f9; border:1px solid #ddd; border-radius:8px; padding:12px 14px;
  box-shadow:0 2px 10px rgba(0,0,0,.25); z-index:1000; display:none;
}
.floating-panel h3{ margin:0 0 8px 0; font-size:15px; }
.floating-panel ul{ margin:0; padding-left:18px; font-size:13px; }
.floating-panel .kbd{ font-family:monospace; background:#eee; padding:1px 4px; border-radius:4px; }

/* Optional: small '?' help square trigger */
#help-square{
  position:fixed; right:18px; bottom:18px; width:32px; height:32px;
  background:#005b96; color:#fff; border-radius:6px; display:flex;
  align-items:center; justify-content:center; font-weight:bold; cursor:pointer;
  box-shadow:0 2px 8px rgba(0,0,0,.3); z-index:1000; user-select:none;
}

/* Specific id so old code continues to work */
#help-popup{ /* inherits floating-panel look */
}
#rtHelpPanel code { font-family: monospace; background:#eee; padding:1px 4px; border-radius:4px; }



/* --- QA chips --- */
.qa-links { display:flex; gap:6px; justify-content:center; flex-wrap:wrap; }
.qa-chip {
  display:inline-block; padding:2px 8px; border:1px solid #bbb;
  border-radius:999px; background:#fff; text-decoration:none; color:#005b96;
  font-size:12px;
}
.qa-chip:hover { background:#eef4ff; border-color:#88c; }
.qa-chip.ghost { opacity:0.8; }
.qa-chip.disabled { color:#888; border-color:#ddd; background:#f5f5f5; pointer-events:none; }

/* --- Thumbnails --- */
.thumbs { display:flex; gap:6px; justify-content:center; align-items:center; }
.thumb {
  max-width:80px; max-height:60px; border:1px solid #ccc; border-radius:4px;
  cursor:zoom-in; background:#fff; object-fit:contain;
}

/* --- Lightbox --- */
.lightbox { position:fixed; inset:0; display:none; z-index:99999; }
.lightbox.open { display:block; }
.lb-backdrop { position:absolute; inset:0; background:rgba(0,0,0,.6); }
.lb-content {
  position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
  background:#111; color:#fff; border-radius:8px; max-width:90vw; max-height:90vh;
  box-shadow:0 10px 30px rgba(0,0,0,.5); display:flex; flex-direction:column; overflow:hidden;
}
.lb-bar { display:flex; align-items:center; justify-content:space-between; padding:6px 10px; background:#222; }
.lb-title { font-size:14px; font-weight:bold; }
.lb-close { background:#444; color:#fff; border:0; padding:2px 8px; border-radius:4px; cursor:pointer; }
.lb-close:hover { background:#666; }
#lb-img { max-width:90vw; max-height:80vh; display:block; margin:auto; }

/* --- Notes ellipsis and editor stack --- */
.note-ellip { max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.editor-vert { display:flex; flex-direction:column; gap:4px; align-items:center; }

/* --- Preview cell --- */
.preview-cell { display:flex; gap:8px; align-items:center; justify-content:center; }
.thumb { max-width:80px; max-height:60px; border:1px solid #ccc; border-radius:4px; background:#fff; object-fit:contain; }
.qa-chip { display:inline-block; padding:2px 8px; border:1px solid #bbb; border-radius:999px; background:#fff; text-decoration:none; color:#005b96; font-size:12px; cursor:pointer; }
.qa-chip:hover { background:#eef4ff; border-color:#88c; }
.qa-chip.disabled { color:#888; border-color:#ddd; background:#f5f5f5; pointer-events:none; }

/* --- Gallery --- */
.galbox { position:fixed; inset:0; display:none; z-index:99999; }
.galbox.open { display:block; }
.gal-backdrop { position:absolute; inset:0; background:rgba(0,0,0,.65); }
.gal-wrap { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); background:#0f1115; color:#fff; width:90vw; max-width:1400px; height:90vh; border-radius:10px; box-shadow:0 10px 30px rgba(0,0,0,.5); display:flex; flex-direction:column; overflow:hidden; }
.gal-bar { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#171a21; }
.gal-title { font-weight:700; font-size:14px; }
.gal-actions { display:flex; gap:8px; align-items:center; }
.btn-mini { background:#2a3140; color:#fff; border:0; padding:4px 8px; border-radius:6px; cursor:pointer; text-decoration:none; font-size:12px; }
.btn-mini:hover { background:#3a4356; }
.gal-main { position:relative; flex:1 1 auto; display:flex; align-items:center; justify-content:center; }
.gal-main img { max-width:100%; max-height:100%; object-fit:contain; }
.gal-main .nav { position:absolute; top:50%; transform:translateY(-50%); background:rgba(0,0,0,.35); border:0; color:#fff; font-size:30px; width:44px; height:44px; border-radius:22px; cursor:pointer; }
.gal-main .nav:hover { background:rgba(0,0,0,.55); }
.gal-main .nav.prev { left:10px; }
.gal-main .nav.next { right:10px; }
.gal-film { display:flex; gap:8px; padding:8px; overflow-x:auto; background:#0f1115; border-top:1px solid #202532; }
.gal-film img { height:64px; border:2px solid transparent; border-radius:6px; cursor:pointer; object-fit:contain; background:#111; }
.gal-film img.active { border-color:#4da3ff; }
.gal-meta { display:flex; gap:12px; align-items:center; padding:6px 12px; font-size:12px; color:#cfd6e6; background:#0f1115; border-top:1px solid #202532; }

/* note/inputs you already had */
.note-ellip { max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.editor-vert { display:flex; flex-direction:column; gap:4px; align-items:center; }


'''
print(css)
