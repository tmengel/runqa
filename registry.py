#!/usr/bin/python3
# Author Tanner Mengel
# tmengel@bnl.gov
# Last updated: 2025-07-10

import psycopg2
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import os
import cgi
import cgitb
cgitb.enable()

# DB config
DB_NAME = "Production"
DB_USER = "phnxrc"
DB_HOST = "sphnxproddbmaster"
COLUMNS = ["EMCal", "OHCal", "IHCal", "MBD", "SEPD", "TPOT", "TPC", "INTT", "MVTX", "ZDC", "SPIN"]
PAGE_SIZE = 25

DAQ_DB_PARAMS = {
    'dbname': 'daq',
    'user': 'phnxro',
    'host': 'sphnxdaqdbreplica'
}

form = cgi.FieldStorage()
page = int(form.getvalue('page', 1))
offset = (page - 1) * PAGE_SIZE

if os.environ.get("REQUEST_METHOD", "").upper() == "POST":
    runnumber = form.getvalue("runnumber")
    page = form.getfirst("page", "1")  # Default to page 1 if missing

    updates = []
    for col in COLUMNS:
        base = f"{col}_{runnumber}"
        runclass = form.getfirst(f"runclass_{base}")
        notes = form.getfirst(f"notes_{base}")

        if runclass:
            updates.append((col.lower(), runclass, notes))

    try:
        with psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST) as conn:
            with conn.cursor() as cur:
                for column, runclass, notes in updates:
                    cur.execute(f"UPDATE goodruns SET {column} = (%s, %s) WHERE runnumber = %s",
                                (runclass, notes, runnumber))
            conn.commit()
    except Exception as e:
        print("Content-type: text/html; charset=utf-8\r\n\r\n")
        print(f"<p>Error updating database: {e}</p>")
        exit()

    # Redirect to same page
    print("Content-type: text/html; charset=utf-8\r\n\r\n")
    print(f'<meta http-equiv="refresh" content="0; url=all.py?page={page}">')
    print("<p>Update successful. Redirecting...</p>")
    exit()


print("Content-type: text/html; charset=utf-8\r\n\r\n")
print("""
<html><head><title>Run Status Table for All Subsystems</title>
<style>
    body { font-family: Arial, sans-serif; }
    table { border-collapse: collapse; font-size: small; }
    th, td { padding: 3px 20px; text-align: center; vertical-align: top; }
    select { font-size: small; padding: 0; margin: 0; width: 45px; }
    input[type=text] { font-size: small; width: 95%; }
    .golden { background-color: #c8f7c5; }
    .questionable { background-color: #000000; color: white; }
    .bad { background-color: #f7c5c5; }
    .unknown { background-color: #ffffff; }
    .notes-panel { display: none; margin-top: 3px; }
    .clickable { cursor: pointer; }
    .pagination { text-align: center; margin: 20px 0; font-size: 16px; }
    .pagination a, .pagination strong { display: inline-block;
        padding: 6px 12px;
        margin: 2px;
        border: 1px solid #ccc;
        border-radius: 5px;
        text-decoration: none;
        font-weight: normal;
        background-color: #f8f8f8;
        color: #005b96;
        transition: background-color 0.2s, border-color 0.2s;
    }
    .pagination a:hover { background-color: #e6f2ff; border-color: #88c; }
    .pagination strong { background-color: #005b96; color: white; border-color: #005b96; font-weight: bold; }
    .logo-container {
        padding: 10px;
        margin-bottom: 10px;
    }
    .logo-container img {
        height: 60px;
    }
    .hidden-col {
        display: none;
    }

</style>
<script>
function toggleNotes(id) {
    var panel = document.getElementById(id);
    if (panel.style.display === "none" || panel.style.display === "") {
        panel.style.display = "block";
    } else {
        panel.style.display = "none";
    }
}
function toggleDropdown(id) {
    var sel = document.getElementById(id);
    sel.style.display = sel.style.display === "inline-block" ? "none" : "inline-block";
}
function toggleEditable(checkbox) {
    const run = checkbox.getAttribute("data-row");
    const blocks = document.querySelectorAll(`.editable-${run}`);
    blocks.forEach(el => {
        el.style.display = checkbox.checked ? "block" : "none";
    });
}
function toggleColumn(colClass) {
    const elements = document.querySelectorAll('.' + colClass);
    elements.forEach(el => {
        el.classList.toggle('hidden-col');
    });
}
</script>
</head><body>
<div style="display: flex; align-items: center; gap: 20px; margin-bottom: 10px;">
    <img src="https://sphenix-intra.sdcc.bnl.gov/WWW/static/sphenix-logo-white-bg.png" alt="sPHENIX Logo" style="height: 80px;">
    <h1 style="margin: 0;">sPHENIX Run Registry</h1>
</div>
""")



def ceil(x):
    return -int(-x // 1)

def render_pagination(current, total):
    output = []

    def page_link(p, label=None):
        label = label or str(p)
        return f'<a href="all.py?page={p}">{label}</a>'

    # First and Prev
    if current > 1:
        output.append(page_link(1, "&laquo;"))  # <<
        output.append(page_link(current - 1, "&lsaquo;"))  # <

    # Left ellipsis if needed
    if current > 3:
        output.append("<span>...</span>")

    # Middle (current -1, current, current +1)
    for p in range(current - 1, current + 2):
        if 1 <= p <= total:
            if p == current:
                output.append(f"<strong>{p}</strong>")
            else:
                output.append(page_link(p))

    # Right ellipsis if needed
    if current < total - 2:
        output.append("<span>...</span>")

    # Next and Last
    if current < total:
        output.append(page_link(current + 1, "&rsaquo;"))  # >
        output.append(page_link(total, "&raquo;"))  # >>

    return " ".join(output)

def get_run_metadata(run_numbers):
    if not run_numbers:
        return {}

    placeholders = ','.join(['%s'] * len(run_numbers))
    query = f"""
        SELECT runnumber,
               CAST(EXTRACT(EPOCH FROM ertimestamp) AS BIGINT)
               - CAST(EXTRACT(EPOCH FROM brtimestamp) AS BIGINT) AS duration,
               runtype
        FROM run
        WHERE runnumber IN ({placeholders})
    """

    run_info = {}
    try:
        with psycopg2.connect(**DAQ_DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(query, run_numbers)
                for run, duration, runtype in cur.fetchall():
                    run_info[run] = {
                        "duration": duration,
                        "runtype": runtype
                    }
    except Exception as e:
        print(f"<p>Warning: Could not fetch run metadata: {e}</p>")
    return run_info

def run_link_exists(url):
    return True  # For testing purposes, assume all links exist
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=1) as r:
            return r.status == 200
    except:
        return False

def batch_check_links(run_runtype_map):
    base_offline = "https://sphenix-intra.sdcc.bnl.gov/WWW/subsystem/QAHtml/mon.cgi"
    base_online = "https://sphenix-intra.sdcc.bnl.gov/WWW/run/2025/OnlMonHtml/mon.cgi"
    results = {}

    def check_pair(runnumber, runtype):
        params = f"?runnumber={runnumber}&runtype={runtype}"
        offline = run_link_exists(f"{base_offline}{params}")
        online = run_link_exists(f"{base_online}{params}")
        return runnumber, offline, online

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(check_pair, run, runtype): run
            for run, runtype in run_runtype_map.items()
        }
        for future in futures:
            runnumber, offline_ok, online_ok = future.result()
            results[runnumber] = (offline_ok, online_ok)

    return results


try:
    run_number_filter = form.getfirst("run_number", "").strip()
    run_type_filter = form.getfirst("run_type", "").strip()

    # Render the filter form
    print(f"""
    <div style="margin-bottom: 1em; padding: 0.5em; background-color: #f9f9f9; border: 1px solid #ccc; border-radius: 4px; display: inline-block;">
        <form method="get" action="all.py" style="display: flex; flex-wrap: wrap; gap: 0.5em; align-items: center;">

            <label for="run_number" style="margin: 0;">Run #</label>
            <input type="text" id="run_number" name="run_number" value="{run_number_filter}" style="width: 100px; padding: 2px 2px;">

            <label for="run_type" style="margin: 0;">Type</label>
            <select id="run_type" name="run_type" style="width: 100px; padding: 2px 2px;">
                <option value="">-- Any --</option>
                <option value="physics" {'selected' if run_type_filter == 'physics' else ''}>Physics</option>
                <option value="cosmics" {'selected' if run_type_filter == 'cosmics' else ''}>Cosmics</option>
                <option value="calibration" {'selected' if run_type_filter == 'calibration' else ''}>Calibration</option>
            </select>

            <input type="submit" value="Search" style="padding: 2px 10px;">
        </form>
    </div>
    """)

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST)
    cur = conn.cursor()

    # Count all goodruns
    cur.execute("SELECT COUNT(*) FROM goodruns")
    total = cur.fetchone()[0]
    page_count = ceil(total / PAGE_SIZE)

    # Apply filtering logic
    conditions = []
    params = []

    if run_number_filter:
        conditions.append("runnumber = %s")
        params.append(run_number_filter)
    if run_type_filter:
        conditions.append("runtype = %s")
        params.append(run_type_filter)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT runnumber, {','.join([c.lower() for c in COLUMNS])}
        FROM goodruns
        {where_clause}
        ORDER BY runnumber DESC
        LIMIT %s OFFSET %s
    """
    params.extend([PAGE_SIZE, offset])
    cur.execute(query, params)

    raw_rows = cur.fetchall()
    raw_run_numbers = [row[0] for row in raw_rows]

    # Get metadata and filter by relevant run types
    metadata = get_run_metadata(raw_run_numbers)

    rows = []
    for row in raw_rows:
        runnumber = row[0]
        runtype = metadata.get(runnumber, {}).get("runtype", "")
        if runtype in ["physics", "cosmics", "calibration"]:
            rows.append(row)

    if not rows:
        print("<p>No valid runs found for this page.</p></body></html>")
        exit()

    filtered_run_runtype_map = {row[0]: metadata[row[0]]["runtype"] for row in rows}
    link_status = batch_check_links(filtered_run_runtype_map)
    print("""
    <div style="margin-bottom: 1em;">
        <button onclick="toggleColumn('col-offline')">Show Offline QA</button>
        <button onclick="toggleColumn('col-online')">Show Online QA</button>
    </div>
    """)
    # Table header
    print("<table border='1'>")
    print("<tr>")
    print("<th class='sticky-col'>Run #</th>")
    print("<th class='col-offline hidden-col'>Offline QA</th>")
    print("<th class='col-online hidden-col'>Online QA</th>")

    print("<th>Run Type</th>")
    for col in COLUMNS:
        print(f"<th>{col}</th>")
    print("<th>Edit</th>")
    print("</tr>")

    for row in rows:


        runnumber = row[0]
        subsystems = row[1:]
        runtype = metadata[runnumber]["runtype"]
        offline_url = f"https://sphenix-intra.sdcc.bnl.gov/WWW/subsystem/QAHtml/mon.cgi?runnumber={runnumber}&runtype={runtype}"
        online_url  = f"https://sphenix-intra.sdcc.bnl.gov/WWW/run/2025/OnlMonHtml/mon.cgi?runnumber={runnumber}&runtype={runtype}"
        offline_ok, online_ok = link_status.get(runnumber, (False, False))


        print(f"<tr><form method='post' action='all.py'>")
        # print(f"<td>{runnumber}</td>")
        print(f"<input type='hidden' name='runnumber' value='{runnumber}'>")

        # Links and metadata
        print(f"<td class='sticky-col'>{runnumber}</td>")
        print(f"<td class='col-offline hidden-col'>" + (f"<a href='{offline_url}' target='_blank'>Offline</a>" if offline_ok else "N/A") + "</td>")
        print(f"<td class='col-online hidden-col'>" + (f"<a href='{online_url}' target='_blank'>Online</a>" if online_ok else "N/A") + "</td>")

        print(f"<td>{runtype}</td>")


        for i, value in enumerate(subsystems):
            if value is None:
                print("<td class='unknown'>(None)</td>")
                continue

            runclass, notes = value.strip("()").split(",", 1)
            runclass = runclass.strip('"')
            notes = notes.strip('"')
            color_class = {
                "GOLDEN": "golden",
                "QUESTIONABLE": "questionable",
                "BAD": "bad"
            }.get(runclass.upper(), "unknown")

            col_name = COLUMNS[i]
            field_base = f"{col_name}_{runnumber}"  # For unique input names

            # Human-readable label
            if runclass == "GOLDEN":
                label = "Good"
            elif runclass == "BAD":
                label = "Bad"
            elif runclass == "QUESTIONABLE":
                label = "Quest."
            else:
                label = "&mdash;"

            display_text = f"{label}{': ' + notes if notes else ''}"
            cell_id = f"notes_{runnumber}_{i}"

            print(f"""
            <td class="{color_class}">
                <div class="clickable" onclick="toggleNotes('{cell_id}')">
                    <div class="summary-text editable-{runnumber}" style="display: block;">
                        {display_text}
                    </div>
                    <div class="edit-block editable-{runnumber}" style="display:none;">
                        <select name="runclass_{field_base}" class="{color_class}" style="background-color: inherit;">
                            <option value="GOLDEN" style="background-color:#c8f7c5;" {'selected' if runclass == 'GOLDEN' else ''}>G</option>
                            <option value="QUESTIONABLE" style="background-color:#000; color:white;" {'selected' if runclass == 'QUESTIONABLE' else ''}>Q</option>
                            <option value="BAD" style="background-color:#f7c5c5;" {'selected' if runclass == 'BAD' else ''}>B</option>
                        </select>
                        <input type="text" name="notes_{field_base}" value="{notes}" style="margin-top: 3px;">
                    </div>
                </div>
            </td>
            """)

        print(f"<td class='editable-{runnumber}' style='display:none;'><input type='submit' value='Save'></td>")
        print(f"<td><input type='checkbox' onclick='toggleEditable(this)' data-row='{runnumber}'></td>")

        print("</form></tr>")
    print("</table>")
    print(f"<div class='pagination'>Pages: {render_pagination(page, page_count)}</div>")
    cur.close()

except Exception as e:
    print(f"<p>Error: {e}</p>")
finally:
    if conn:
        conn.close()

print("</body></html>")
