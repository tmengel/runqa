#!/usr/bin/python3
# Author Tanner Mengel
# tmengel@bnl.gov
# Last updated: 2025-08-19

import os
import math
import html
import urllib.parse
import urllib.request
import cgi
import cgitb
cgitb.enable() 

from tools.db_backend import (
    count_goodruns,
    fetch_goodruns_page,
    get_run_metadata,
    apply_updates,
)


from tools.templates import (
    urlencode_keep,
    render_pagination,
    parse_cell, class_to_css, label_for,
    active_filters_panel,
    render_header, render_filters_form, render_top_controls,
    render_table, render_form_footer, render_footer
)

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

COLUMNS = ["MVTX", "INTT", "TPC", "TPOT", "EMCAL", "IHCAL", "OHCAL", "MBD", "ZDC", "sEPD"]
PAGE_SIZE_DEFAULT = 15
PAGE_SIZE_MAX = 200


# ---------- CGI INPUT ----------
form = cgi.FieldStorage()

def _get_int(name, default=None):
    try:
        v = form.getfirst(name, "")
        if v in (None, ""):
            return default
        return int(v)
    except Exception:
        return default

def _get_str(name, default=""):
    v = form.getfirst(name, default)
    return v if v is not None else default

page = max(1, _get_int("page", 1))
page_size = min(max(1, _get_int("page_size", PAGE_SIZE_DEFAULT)), PAGE_SIZE_MAX)

# Filters
run_number_exact = _get_int("run_number", None)
run_min = _get_int("run_min", None)
run_max = _get_int("run_max", None)
run_type_filter = _get_str("run_type", "").strip().lower()   # physics/cosmics/calibration or ""
notes_contains  = _get_str("notes_contains", "").strip()
require_class   = _get_str("require_class", "").strip().upper()  # GOLDEN/QUESTIONABLE/BAD
subsys_filter   = _get_str("subsys", "").strip()                 # exact member of COLUMNS
subsys_class    = _get_str("subsys_class", "").strip().upper()   # GOLDEN/QUESTIONABLE/BAD
track_ready     = _get_str("track_ready", "")
calo_ready      = _get_str("calo_ready", "")

# Current params for links (strip empty when building QS)
current_params = {
    "run_number": "" if run_number_exact is None else str(run_number_exact),
    "run_min": "" if run_min is None else str(run_min),
    "run_max": "" if run_max is None else str(run_max),
    "run_type": run_type_filter or "",
    "page_size": str(page_size),
    "notes_contains": notes_contains or "",
    "require_class": require_class or "",
    "subsys": subsys_filter or "",
    "subsys_class": subsys_class or "",
    "track_ready": "1" if track_ready in ("1", "true", "True") else "",
    "calo_ready":  "1" if calo_ready  in ("1", "true", "True") else "",
    "page": str(page),
}

# ---------- HANDLE POST (updates) ----------
if os.environ.get("REQUEST_METHOD", "").upper() == "POST":
    updates_by_run = {}
    for key in form.keys():
        val = form.getfirst(key, "")
        if not val:
            continue
        if key.startswith("runclass_"):
            # runclass_COL_RUN
            _, col, rn = key.split("_", 2)
            rn = int(rn)
            notes = form.getfirst(f"notes_{col}_{rn}", "").strip()
            updates_by_run.setdefault(rn, []).append((col.lower(), val.strip(), notes))

    try:
        apply_updates(updates_by_run)
    except Exception as e:
        print("Content-type: text/html; charset=utf-8\r\n\r\n")
        print(f"<p>Error updating database: {_html.escape(str(e))}</p>")
        raise SystemExit

    print("Content-type: text/html; charset=utf-8\r\n\r\n")
    redir_qs = urlencode_keep(current_params, {"page": str(page)})
    print(f'<meta http-equiv="refresh" content="0; url=all.py?{redir_qs}">')
    print("<p>Update successful. Redirecting...</p>")
    raise SystemExit

# ---------- PAGE (GET) ----------
print("Content-type: text/html; charset=utf-8\r\n\r\n")
print(render_header())

# Filter form + “Active Filters”
filters_dict = {
    "run_number_exact": run_number_exact,
    "run_min": run_min,
    "run_max": run_max,
    "notes_contains": notes_contains,
    "require_class": require_class,
    "subsys_filter": subsys_filter,
    "subsys_class": subsys_class,
}
rn_val = "" if run_number_exact is None else str(run_number_exact)
rmin_val = "" if run_min is None else str(run_min)
rmax_val = "" if run_max is None else str(run_max)

print(render_filters_form(
    run_type_filter=run_type_filter,
    rn_val=rn_val, rmin_val=rmin_val, rmax_val=rmax_val,
    page_size=page_size,
    active_filters_html=active_filters_panel(
        {"run_number_exact": run_number_exact, "run_min": run_min, "run_max": run_max},
        run_type_filter
    )
))

# ---------- COUNT -> CLAMP -> FETCH ----------
try:
    filtered_total = count_goodruns(filters_dict, COLUMNS)
    total_pages = max(1, -(-filtered_total // page_size))  # ceil-div
    page = max(1, min(page, total_pages))
    offset = (page - 1) * page_size
    current_params["page"] = str(page)  # keep links in sync

    raw_rows = fetch_goodruns_page(filters_dict, COLUMNS, page_size, offset)
    run_numbers = [r[0] for r in raw_rows]

    # Metadata (safe if empty)
    meta = {}
    try:
        meta = get_run_metadata(run_numbers)
    except Exception as e:
        print(f"<p style='color:#a00;'>Warning: Could not fetch run metadata: {_html.escape(str(e))}</p>")

    # Post-join filters (type + optional QA-ready file presence)
    rows = []
    for row in raw_rows:
        rn = row[0]
        rt = (meta.get(rn, {}).get("runtype", "") or "")
        if run_type_filter and rt != run_type_filter:
            continue

        # 1000-run binning for QA artifacts
        floor = (rn // 1000) * 1000
        ceiling = floor + 1000
        tqa = f"/sphenix/WWW/subsystem/QAHtml/{rt}/run_{floor:010d}_{ceiling:010d}/{rn:05d}/TpcLasersQA_1_{rn:05d}.png"
        cqa = f"/sphenix/WWW/subsystem/QAHtml/{rt}/run_{floor:010d}_{ceiling:010d}/{rn:05d}/CaloQA_cemc1_{rn}.png"

        if current_params["track_ready"] and (not os.path.exists(tqa)):
            continue
        if current_params["calo_ready"] and (not os.path.exists(cqa)):
            continue

        rows.append(row)

    # ----- Render results area (AJAX-swappable) -----
    print('<div id="resultsRoot">')
    print(render_top_controls(current_params))
    print(render_table(rows, meta, COLUMNS))
    print(render_form_footer(current_params))
    print(f"<div class='pagination'>{render_pagination(current_params, page, total_pages, filtered_total, page_size)}</div>")
    print('</div>')  # end #resultsRoot

except Exception as e:
    print(f"<p style='color:#a00;'>Error: {_html.escape(str(e))}</p>")

print(render_footer())
