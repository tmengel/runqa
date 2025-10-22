# tools/templates.py
# Pure-Python helpers for HTML rendering and small utilities (no DB access).

import os
import html as _html
import urllib.parse as _urlparse
from typing import Optional, Dict, List, Tuple, Any

# -------------------- URL / PARAMS --------------------

def urlencode_keep(current_params: Dict[str, Any],
                   overrides: Optional[Dict[str, Any]] = None) -> str:
    """
    Merge current_params with optional overrides and build a short querystring.
    Any None/""/"None" value is stripped to keep URLs short.
    """
    base = dict(current_params or {})
    if overrides:
        base.update(overrides)
    clean = {k: v for k, v in base.items() if v not in (None, "", "None")}
    return _urlparse.urlencode(clean, doseq=False)

# -------------------- Pagination --------------------

def render_pagination(current_params: Dict[str, Any],
                      cur_page: int,
                      total_pages: int,
                      total_count: Optional[int],
                      page_size: int) -> str:
    """
    Adaptive pagination with first/prev/next/last, proportional window,
    and a “Showing X–Y of N” summary if total_count is provided.
    """
    def link(p: int, label: Optional[str] = None, aria: Optional[str] = None) -> str:
        lbl = label or str(p)
        href = "all.py?" + urlencode_keep(current_params, {"page": str(p)})
        aria_attr = ' aria-label="{}"'.format(_html.escape(aria)) if aria else ""
        return '<a href="{}"{}>{}</a>'.format(href, aria_attr, lbl)

    # Summary (always, if total_count is available)
    summary_html = ""
    if isinstance(total_count, int):
        if total_count == 0:
            summary_html = '<div class="pager-summary">Showing 0 of 0</div>'
        else:
            start_i = (cur_page - 1) * page_size + 1
            end_i = min(cur_page * page_size, total_count)
            summary_html = '<div class="pager-summary">Showing {}–{} of {}</div>'.format(start_i, end_i, total_count)

    if total_pages <= 1:
        return summary_html

    # Proportional window
    if total_pages <= 10:
        window = 10
    elif total_pages <= 50:
        window = 7
    elif total_pages <= 200:
        window = 9
    else:
        window = 11

    half = window // 2
    start = max(1, cur_page - half)
    end = min(total_pages, start + window - 1)
    start = max(1, end - window + 1)

    parts = []

    # First / Prev
    if cur_page > 1:
        parts.append(link(1, "&laquo;", "First page"))
        parts.append(link(cur_page - 1, "&lsaquo;", "Previous page"))

    # Left boundary
    if start > 1:
        parts.append(link(1))
        if start > 2:
            parts.append("<span>…</span>")

    # Middle window
    for p in range(start, end + 1):
        if p == cur_page:
            parts.append("<strong>{}</strong>".format(p))
        else:
            parts.append(link(p))

    # Right boundary
    if end < total_pages:
        if end < total_pages - 1:
            parts.append("<span>…</span>")
        parts.append(link(total_pages))

    # Next / Last
    if cur_page < total_pages:
        parts.append(link(cur_page + 1, "&rsaquo;", "Next page"))
        parts.append(link(total_pages, "&raquo;", "Last page"))

    return summary_html + '<div class="pager-links">' + " ".join(parts) + "</div>"

# -------------------- Small helpers used by table rendering --------------------

def parse_cell(val: Any) -> Tuple[Optional[str], str]:
    """
    goodruns column cell expected as string like: "(GOLDEN,\"notes...\")" or NULL.
    Returns (runclass, notes) normalized.
    """
    if val is None:
        return None, ""
    s = str(val).strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    if "," in s:
        first, rest = s.split(",", 1)
    else:
        first, rest = s, ""
    runclass = first.strip().strip('"').strip()
    notes = rest.strip().strip('"').strip()
    runclass = runclass if runclass else None
    notes = notes if notes else ""
    return runclass, notes

def class_to_css(rc: Optional[str]) -> str:
    if not rc:
        return "unknown"
    u = rc.upper()
    if u == "GOLDEN": return "golden"
    if u == "QUESTIONABLE": return "questionable"
    if u == "BAD": return "bad"
    return "unknown"

def label_for(rc: Optional[str]) -> str:
    if not rc:
        return "&mdash;"
    u = rc.upper()
    return {"GOLDEN":"Good", "BAD":"Bad", "QUESTIONABLE":"Quest."}.get(u, "&mdash;")

def active_filters_panel(filters: Dict[str, Any], run_type_filter: str) -> str:
    """
    Pretty “Active Filters” line built from the filter dict and run_type.
    Expecting keys run_number_exact, run_min, run_max.
    """
    items = []
    if filters.get("run_number_exact") is not None:
        items.append("Run = {}".format(filters["run_number_exact"]))
    minmax = []
    if filters.get("run_min") is not None:
        minmax.append("&ge; {}".format(filters["run_min"]))
    if filters.get("run_max") is not None:
        minmax.append("&le; {}".format(filters["run_max"]))
    if minmax:
        items.append("Run " + " and ".join(minmax))
    if run_type_filter:
        items.append("Type = {}".format(_html.escape(run_type_filter)))
    if not items:
        return "<em>None</em>"
    return " &nbsp;•&nbsp; ".join(items)

# -------------------- Page sections --------------------

def render_header() -> str:
    # includes help_ui so the Help/Hotkeys pane is available
    return """
<html><head><title>Run Status Table for All Subsystems</title>
<link rel="stylesheet" href="tools/style.py?v=1">
<script src="tools/script.py?v=1" defer></script>
<script src="tools/filter_ui.py?v=1" defer></script>
<script src="tools/help_ui.py?v=1" defer></script>
</head><body>
<div style="display:flex;align-items:center;gap:20px;margin-bottom:10px;">
  <img src="https://sphenix-intra.sdcc.bnl.gov/WWW/static/sphenix-logo-white-bg.png" alt="sPHENIX Logo" style="height:80px;">
  <h1 style="margin:0;">sPHENIX Run Registry</h1>
</div>
"""

def render_filters_form(run_type_filter: str,
                        rn_val: str,
                        rmin_val: str,
                        rmax_val: str,
                        page_size: int,
                        active_filters_html: str) -> str:
    selected = {
        "":           " selected" if run_type_filter == "" else "",
        "physics":    " selected" if run_type_filter == "physics" else "",
        "cosmics":    " selected" if run_type_filter == "cosmics" else "",
        "calibration":" selected" if run_type_filter == "calibration" else "",
    }
    return """
<div class="filters">
  <form method="get" action="all.py" style="display:flex;flex-wrap:wrap;gap:10px;align-items:end;">
    <div>
      <label for="run_number">Run # (exact)</label><br>
      <input type="text" id="run_number" name="run_number" value="{rn}" style="width:120px;">
    </div>
    <div>
      <label for="run_min">Run &ge;</label><br>
      <input type="text" id="run_min" name="run_min" value="{rmin}" style="width:120px;">
    </div>
    <div>
      <label for="run_max">Run &le;</label><br>
      <input type="text" id="run_max" name="run_max" value="{rmax}" style="width:120px;">
    </div>
    <div>
      <label for="run_type">Type</label><br>
      <select id="run_type" name="run_type" style="width:140px;">
        <option value=""{sel_any}>-- Any --</option>
        <option value="physics"{sel_phy}>Physics</option>
        <option value="cosmics"{sel_cos}>Cosmics</option>
        <option value="calibration"{sel_cal}>Calibration</option>
      </select>
    </div>
    <div>
      <label for="page_size">Page size</label><br>
      <input type="text" id="page_size" name="page_size" value="{ps}" style="width:80px;">
    </div>
    <div>
      <button type="submit" style="padding:4px 10px;">Apply</button>
      <a href="all.py" style="margin-left:6px;">Reset</a>
    </div>
  </form>
  <div class="active-filters"><strong>Active Filters:</strong> {af}</div>
</div>
""".format(
        rn=_html.escape(rn_val),
        rmin=_html.escape(rmin_val),
        rmax=_html.escape(rmax_val),
        ps=page_size,
        af=active_filters_html,
        sel_any=selected[""],
        sel_phy=selected["physics"],
        sel_cos=selected["cosmics"],
        sel_cal=selected["calibration"],
    )

def render_top_controls(current_params: Dict[str, Any]) -> str:
    return """
<div class="edit-controls" style="margin-bottom:8px;">
  <button type="button" id="btnEditMode" class="btn" onclick="enterEditMode()">
    Enter Edit Mode (Ctrl+E)
  </button>
  <button type="button" id="btnHelp" class="btn" onclick="openHelp('btnHelp')">
    Help / Hotkeys (Ctrl+H)
  </button>
</div>
<form id="bulkForm" method="post" action="all.py?{qs}">
""".format(qs=urlencode_keep(current_params))

# def render_table(rows: List[Tuple[Any, ...]],
#                  meta: Dict[int, Dict[str, Any]],
#                  columns: List[str]) -> str:
#     """
#     rows: list of tuples (runnumber, MVTX,...)
#     meta: { runnumber: {"runtype": "physics", ...}, ...}
#     """
#     out = []
#     out.append("<table border='1'>")
#     out.append("<thead><tr>")
#     out.append("<th>Run #</th>")
#     out.append("<th class='col-offline hidden-col'>Offline QA</th>")
#     out.append("<th class='col-online hidden-col'>Online QA</th>")
#     out.append("<th>Run Type</th>")
#     for col in columns:
#         out.append("<th class='col-{}'>{}</th>".format(col.lower(), _html.escape(col)))
#     out.append("<th>Tracking QA Ready</th>")
#     out.append("<th>Calo QA Ready</th>")
#     out.append("<th>Shifter Checked</th>")
#     out.append("</tr></thead><tbody>")

#     if not rows:
#         out.append("<tr><td colspan='{}' style='text-align:center;padding:10px;'>No runs match your filters on this page.</td></tr>".format(4 + len(columns) + 3))
#     else:
#         for row in rows:
#             rn = row[0]
#             subs = row[1:]
#             rt = (meta.get(rn, {}) or {}).get("runtype", "") or ""
#             floor = (rn // 1000) * 1000
#             ceiling = floor + 1000
#             offline_url = "https://sphenix-intra.sdcc.bnl.gov/WWW/subsystem/QAHtml/mon.cgi?runnumber={}&runtype={}".format(rn, rt)
#             online_url  = "https://sphenix-intra.sdcc.bnl.gov/WWW/run/2025/OnlMonHtml/mon.cgi?runnumber={}&runtype={}".format(rn, rt)
#             offline_path = "/sphenix/WWW/subsystem/QAHtml/{}/run_{:010d}_{:010d}/{:05d}/menu.html".format(rt, floor, ceiling, rn)
#             online_path  = "/sphenix/WWW/run/2025/OnlMonHtml/{}/run_{:010d}_{:010d}/{:05d}/menu.html".format(rt, floor, ceiling, rn)
#             offline_ok =  os.path.exists(offline_path)
#             online_ok =   os.path.exists(online_path)
           
#             out.append("<tr>")
#             out.append("<td>{}</td>".format(rn))
#             out.append("<td class='col-offline hidden-col'>{}</td>".format(
#                 "<a href='{}' target='_blank'>Offline</a>".format(offline_url) if offline_ok else "N/A"
#             ))
#             out.append("<td class='col-online hidden-col'>{}</td>".format(
#                 "<a href='{}' target='_blank'>Online</a>".format(online_url) if online_ok else "N/A"
#             ))
#             out.append("<td>{}</td>".format(_html.escape(rt)))

#             for i, raw in enumerate(subs):
#                 runclass, notes = parse_cell(raw)
#                 css = class_to_css(runclass)
#                 label = label_for(runclass)
#                 col_name = columns[i]
#                 field_base = "{}_{}".format(col_name, rn)
#                 col_class = "col-{}".format(col_name.lower())

#                 pill_class = (
#                     'g' if (runclass or '').upper() == 'GOLDEN' else
#                     'q' if (runclass or '').upper() == 'QUESTIONABLE' else
#                     'b' if (runclass or '').upper() == 'BAD' else ''
#                 )

#                 view_html = (
#                     "<span class='pill {}'>{}</span>".format(pill_class, label) +
#                     ("<div style='max-width:240px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{}</div>".format(_html.escape(notes or "")) if notes else "")
#                 )

#                 edit_html = (
#                     "<div style=\"display:flex;flex-direction:column;gap:4px;align-items:center;\">"
#                     + "<select name=\"runclass_{}\" class=\"{}\">".format(field_base, css)
#                     + "<option value=\"\">--</option>"
#                     + "<option value=\"GOLDEN\" {}>GOLDEN</option>".format('selected' if (runclass or '').upper()=='GOLDEN' else '')
#                     + "<option value=\"QUESTIONABLE\" {}>QUESTIONABLE</option>".format('selected' if (runclass or '').upper()=='QUESTIONABLE' else '')
#                     + "<option value=\"BAD\" {}>BAD</option>".format('selected' if (runclass or '').upper()=='BAD' else '')
#                     + "</select>"
#                     + "<textarea name=\"notes_{}\" placeholder=\"Notes…\">{}</textarea>".format(field_base, _html.escape(notes or ""))
#                     + "</div>"
#                 )

#                 out.append(
#                     "<td class='{} {}'>"
#                     "<div class='label-wrap'>"
#                     "<div class='cell-view'>{}</div>"
#                     "<div class='cell-edit'>{}</div>"
#                     "</div></td>".format(css, col_class, view_html, edit_html)
#                 )

#             # Tracking / Calo QA readiness
   
#             tqa = "/sphenix/WWW/subsystem/QAHtml/{}/run_{:010d}_{:010d}/{:05d}/TpcLasersQA_1_{:05d}.png".format(rt, floor, ceiling, rn, rn)
#             cqa = "/sphenix/WWW/subsystem/QAHtml/{}/run_{:010d}_{:010d}/{:05d}/CaloQA_cemc1_{}.png".format(rt, floor, ceiling, rn, rn)
#             tqa_ready = os.path.exists(tqa)
#             cqa_ready = os.path.exists(cqa)

#             out.append("<td style='background-color:{};'>{}</td>".format("#c8f7c5" if tqa_ready else "#f7c5c5", "QA ready" if tqa_ready else "QA Not ready"))
#             out.append("<td style='background-color:{};'>{}</td>".format("#c8f7c5" if cqa_ready else "#f7c5c5", "QA ready" if cqa_ready else "QA Not ready"))

#             out.append("""
# <td style="background-color:#white; color:white; text-align:center;">
#   <select>
#     <option value="OPEN">Open</option>
#     <option value="COMPLETED">Shifter completed</option>
#     <option value="SIGNOFF">Expert signed off</option>
#   </select>
# </td>
# """)
#             out.append("</tr>")

#     out.append("</tbody></table>")
#     return "".join(out)

def render_form_footer(current_params: Dict[str, Any]) -> str:
    return """
<div style="display:flex; gap:8px; justify-content:flex-end; margin:10px 0;">
  <button type="submit" class="btn primary">Save changes</button>
  <a class="btn" href="all.py?{}">Discard</a>
</div>
<div id="toast" class="toast" aria-live="polite"></div>
</form>
""".format(urlencode_keep(current_params))

def render_footer() -> str:
    return "</body></html>"


_SPHENIX_HTTP = "https://sphenix-intra.sdcc.bnl.gov"
_OFF_HTTP_BASE = _SPHENIX_HTTP + "/WWW/subsystem/QAHtml"
_ONL_HTTP_BASE = _SPHENIX_HTTP + "/WWW/run/2025/OnlMonHtml"
_OFF_FS_BASE   = "/sphenix/WWW/subsystem/QAHtml"

def _rt_dir(rt: str) -> str:
    return (rt or "").strip().lower()

def _bin_dir(rn: int) -> str:
    floor = (rn // 1000) * 1000
    end   = floor + 1000  # directory name uses the NEXT thousand (inclusive range in name)
    return f"run_{floor:010d}_{end:010d}"

def _offline_paths_urls(rn: int, rt: str) -> dict:
    rtd = _rt_dir(rt)
    bin_dir = _bin_dir(rn)
    leaf = f"{rn:05d}"
    # FS locations (existence checks)
    dir_fs   = os.path.join(_OFF_FS_BASE, rtd, bin_dir, leaf)
    menu_fs  = os.path.join(dir_fs, "menu.html")
    tqa_fs   = os.path.join(dir_fs, f"TpcLasersQA_1_{rn:05d}.png")
    cqa_fs   = os.path.join(dir_fs, f"CaloQA_cemc1_{rn}.png")
    # HTTP for viewing
    menu_url = f"{_OFF_HTTP_BASE}/{rtd}/{bin_dir}/{leaf}/menu.html"
    tqa_url  = f"{_OFF_HTTP_BASE}/{rtd}/{bin_dir}/{leaf}/TpcLasersQA_1_{rn:05d}.png"
    cqa_url  = f"{_OFF_HTTP_BASE}/{rtd}/{bin_dir}/{leaf}/CaloQA_cemc1_{rn}.png"
    # Legacy mon.cgi (you said these work fine—keep them)
    mon_url  = f"{_OFF_HTTP_BASE}/mon.cgi?runnumber={rn}&runtype={rtd}"
    return {
        "dir_exists": os.path.isdir(dir_fs) or os.path.exists(menu_fs),
        "menu_url": menu_url,
        "mon_url":  mon_url,
        "tqa_fs": tqa_fs, "tqa_url": tqa_url,
        "cqa_fs": cqa_fs, "cqa_url": cqa_url,
    }

def _online_urls(rn: int, rt: str) -> dict:
    rtd = _rt_dir(rt)
    bin_dir = _bin_dir(rn)
    leaf = f"{rn:05d}"
    # We only link online by URL; pngs live offline tree per your example.
    menu_url = f"{_ONL_HTTP_BASE}/{rtd}/{bin_dir}/{leaf}/menu.html"
    mon_url  = f"{_ONL_HTTP_BASE}/mon.cgi?runnumber={rn}&runtype={rtd}"
    # Try a cheap existence check: if the menu URL mirrors local export, you can
    # check the matching FS path; otherwise leave as always-enabled link.
    onl_dir_fs = f"/sphenix/WWW/run/2025/OnlMonHtml/{rtd}/{bin_dir}/{leaf}"
    exists = os.path.isdir(onl_dir_fs) or os.path.exists(os.path.join(onl_dir_fs, "menu.html"))
    return {"exists": exists, "menu_url": menu_url, "mon_url": mon_url}

def render_table(rows: List[Tuple[Any, ...]],
                 meta: Dict[int, Dict[str, Any]],
                 columns: List[str]) -> str:
    out = []
    out.append("<table border='1'>")
    out.append("<thead><tr>")
    out.append("<th>Run #</th>")
    out.append("<th>Begin Run Time</th>")
    out.append("<th>QA Links</th>")
    out.append("<th>Previews</th>")
    out.append("<th>Run Type</th>")
    for col in columns:
        out.append(f"<th class='col-{col.lower()}'>{_html.escape(col)}</th>")
    out.append("<th>Tracking QA Ready</th>")
    out.append("<th>Calo QA Ready</th>")
    out.append("<th>Shifter Checked</th>")
    out.append("</tr></thead><tbody>")

    if not rows:
        out.append(f"<tr><td colspan='{3 + 1 + len(columns) + 3}' style='text-align:center;padding:10px;'>No runs match your filters on this page.</td></tr>")
        out.append("</tbody></table>")
        return "".join(out)

    for row in rows:
        rn = row[0]
        runtime = row[1]
        subs = row[2:]
        rt  = (meta.get(rn, {}) or {}).get("runtype", "") or ""

        offline = _offline_paths_urls(rn, rt)
        online  = _online_urls(rn, rt)

        # QA Links cell: two chips, disabled when not found (offline) / (online)
        off_html = (
            f"<a class='qa-chip' href='{_html.escape(offline['menu_url'])}' target='_blank' title='Offline menu'>Offline</a>"
            f"<a class='qa-chip ghost' href='{_html.escape(offline['mon_url'])}' target='_blank' title='Offline mon.cgi'>Mon</a>"
            if offline["dir_exists"]
            else "<span class='qa-chip disabled' title='No offline artifacts'>Offline</span>"
        )
        onl_html = (
            f"<a class='qa-chip' href='{_html.escape(online['menu_url'])}' target='_blank' title='Online menu'>Online</a>"
            f"<a class='qa-chip ghost' href='{_html.escape(online['mon_url'])}' target='_blank' title='Online mon.cgi'>Mon</a>"
            if online["exists"]
            else "<span class='qa-chip disabled' title='No online artifacts'>Online</span>"
        )
        qa_links_cell = f"<div class='qa-links'>{off_html}{onl_html}</div>"

        # Thumbnails / previews (lazy load). Click -> lightbox
        thumbs = []
        if os.path.exists(offline["tqa_fs"]):
            thumbs.append(
                "<img class='thumb' loading='lazy' "
                f"src='{_html.escape(offline['tqa_url'])}' alt='TPC Lasers' "
                f"onclick=\"openLightbox('{_html.escape(offline['tqa_url'])}','Run {rn} • TPC Lasers')\">"
            )
        if os.path.exists(offline["cqa_fs"]):
            thumbs.append(
                "<img class='thumb' loading='lazy' "
                f"src='{_html.escape(offline['cqa_url'])}' alt='Calo QA' "
                f"onclick=\"openLightbox('{_html.escape(offline['cqa_url'])}','Run {rn} • Calo QA')\">"
            )
        previews_cell = "<div class='thumbs'>" + ("".join(thumbs) if thumbs else "&mdash;") + "</div>"

        out.append("<tr>")
        out.append(f"<td>{rn}</td>")
        out.append(f"<td>{runtime}</td>")
        out.append(f"<td>{qa_links_cell}</td>")
        out.append(f"<td>{previews_cell}</td>")
        out.append(f"<td>{_html.escape(rt)}</td>")

        # Subsystem cells (unchanged)
        for i, raw in enumerate(subs):
            runclass, notes = parse_cell(raw)
            css = class_to_css(runclass)
            label = label_for(runclass)
            col_name = columns[i]
            field_base = f"{col_name}_{rn}"
            col_class = f"col-{col_name.lower()}"

            pill_class = (
                'g' if (runclass or '').upper() == 'GOLDEN' else
                'q' if (runclass or '').upper() == 'QUESTIONABLE' else
                'b' if (runclass or '').upper() == 'BAD' else ''
            )

            view_html = (
                f"<span class='pill {pill_class}'>{label}</span>"
                + (f"<div class='note-ellip'>{_html.escape(notes or '')}</div>" if notes else "")
            )

            edit_html = (
                "<div class=\"editor-vert\">"
                f"<select name=\"runclass_{field_base}\" class=\"{css}\">"
                "<option value=\"\">--</option>"
                f"<option value=\"GOLDEN\" {'selected' if (runclass or '').upper()=='GOLDEN' else ''}>GOLDEN</option>"
                f"<option value=\"QUESTIONABLE\" {'selected' if (runclass or '').upper()=='QUESTIONABLE' else ''}>QUESTIONABLE</option>"
                f"<option value=\"BAD\" {'selected' if (runclass or '').upper()=='BAD' else ''}>BAD</option>"
                "</select>"
                f"<textarea name=\"notes_{field_base}\" placeholder=\"Notes…\">{_html.escape(notes or '')}</textarea>"
                "</div>"
            )

            out.append(
                f"<td class='{css} {col_class}'>"
                f"<div class='label-wrap'>"
                f"<div class='cell-view'>{view_html}</div>"
                f"<div class='cell-edit'>{edit_html}</div>"
                f"</div></td>"
            )

        # QA ready (re-using offline FS checks)
        tqa_ready = os.path.exists(offline["tqa_fs"])
        cqa_ready = os.path.exists(offline["cqa_fs"])
        out.append("<td style='background-color:{};'>{}</td>".format("#c8f7c5" if tqa_ready else "#f7c5c5", "QA ready" if tqa_ready else "QA Not ready"))
        out.append("<td style='background-color:{};'>{}</td>".format("#c8f7c5" if cqa_ready else "#f7c5c5", "QA ready" if cqa_ready else "QA Not ready"))

        out.append("""
<td style="background-color:#fff; color:#111; text-align:center;">
  <select>
    <option value="OPEN">Open</option>
    <option value="COMPLETED">Shifter completed</option>
    <option value="SIGNOFF">Expert signed off</option>
  </select>
</td>
""")
        out.append("</tr>")

    out.append("</tbody></table>")
    # Lightbox root (once per page). Script will fill it.
    out.append("""
<div id="lb-root" class="lightbox" aria-hidden="true">
  <div class="lb-backdrop" onclick="closeLightbox()"></div>
  <div class="lb-content" role="dialog" aria-modal="true">
    <div class="lb-bar">
      <div class="lb-title" id="lb-title"></div>
      <button class="lb-close" type="button" onclick="closeLightbox()" aria-label="Close">×</button>
    </div>
    <img id="lb-img" alt="">
  </div>
</div>
""")
    return "".join(out)

# _SPHENIX_HTTP = "https://sphenix-intra.sdcc.bnl.gov"
# _OFF_HTTP_BASE = _SPHENIX_HTTP + "/WWW/subsystem/QAHtml"
# _OFF_FS_BASE   = "/sphenix/WWW/subsystem/QAHtml"

# def _rt_dir(rt: str) -> str:
#     return (rt or "").strip().lower()

# def _bin_dir(rn: int) -> str:
#     floor = (rn // 1000) * 1000
#     end   = floor + 1000
#     return f"run_{floor:010d}_{end:010d}"

def _offline_paths(rn: int, rt: str) -> dict:
    rtd     = _rt_dir(rt)
    bin_dir = _bin_dir(rn)
    leaf    = f"{rn:05d}"
    dir_fs  = os.path.join(_OFF_FS_BASE, rtd, bin_dir, leaf)
    http_base = f"{_OFF_HTTP_BASE}/{rtd}/{bin_dir}/{leaf}"
    return {"dir_fs": dir_fs, "http_base": http_base}

# def _list_offline_pngs(rn: int, rt: str) -> list[tuple[str,str]]:
#     """Return list of (url, filename) for all .png under offline dir."""
#     p = _offline_paths(rn, rt)
#     dir_fs   = p["dir_fs"]
#     http_base= p["http_base"]
#     out: list[tuple[str,str]] = []
#     try:
#         if os.path.isdir(dir_fs):
#             for fn in sorted(os.listdir(dir_fs)):
#                 if fn.lower().endswith(".png"):
#                     out.append((f"{http_base}/{fn}", fn))
#     except Exception:
#         pass
#     return out

# def _gallery_row_template(run_id: int, title: str, items: list[tuple[str,str]]) -> str:
#     """
#     Build a hidden <template> with <a> children for the gallery.
#     Each <a> has href=url and data-name=filename.
#     """
#     tid = f"gal-tmpl-{run_id}"
#     parts = [f"<template id='{tid}' data-title='{_html.escape(title)}'>"]
#     for url, name in items:
#         parts.append(f"<a href='{_html.escape(url)}' data-name='{_html.escape(name)}'></a>")
#     parts.append("</template>")
#     return "".join(parts)



