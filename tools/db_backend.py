# db_backend.py
# Centralizes all database access for run triage UI.

import os
import psycopg2

# ---------- CONFIG (overridable via env) ----------
DB_NAME = os.getenv("RUNQA_DB_NAME", "Production")
DB_USER = os.getenv("RUNQA_DB_USER", "phnxrc")
DB_HOST = os.getenv("RUNQA_DB_HOST", "sphnxproddbmaster")

DAQ_DB_PARAMS = {
    "dbname": os.getenv("RUNQA_DAQ_DB_NAME", "daq"),
    "user":   os.getenv("RUNQA_DAQ_DB_USER", "phnxro"),
    "host":   os.getenv("RUNQA_DAQ_DB_HOST", "sphnxdaqdbreplica"),
}

# ---------- CONNECTION HELPERS ----------
def _conn_main():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST)

def _conn_daq():
    return psycopg2.connect(**DAQ_DB_PARAMS)

# ---------- WHERE-BUILDER ----------
def build_where(filters, columns):
    """
    filters dict keys (strings already normalized upstream):
      run_number_exact (int or None)
      run_min (int or None)
      run_max (int or None)
      notes_contains (str)
      require_class (GOLDEN/QUESTIONABLE/BAD or '')
      subsys_filter (exact from columns or '')
      subsys_class (GOLDEN/QUESTIONABLE/BAD or '')
    returns: where_sql (str), params (list)
    """
    where = []
    params = []

    rne = filters.get("run_number_exact")
    rmin = filters.get("run_min")
    rmax = filters.get("run_max")
    notes_contains = (filters.get("notes_contains") or "").strip()
    require_class  = (filters.get("require_class") or "").strip().upper()
    subsys_filter  = (filters.get("subsys_filter") or "").strip()
    subsys_class   = (filters.get("subsys_class") or "").strip().upper()

    if rne is not None:
        where.append("runnumber = %s")
        params.append(rne)
    else:
        if rmin is not None:
            where.append("runnumber >= %s")
            params.append(rmin)
        if rmax is not None:
            where.append("runnumber <= %s")
            params.append(rmax)

    # Notes substring search: scan all subsystem composite text
    if notes_contains:
        like = f"%{notes_contains.lower()}%"
        ors = []
        for col in columns:
            ors.append(f"LOWER(CAST({col.lower()} AS TEXT)) LIKE %s")
            params.append(like)
        where.append("(" + " OR ".join(ors) + ")")

    # Require a runclass present in ANY subsystem
    if require_class in ("GOLDEN", "QUESTIONABLE", "BAD"):
        needle = f"({require_class},"
        ors = []
        for col in columns:
            ors.append(f"CAST({col.lower()} AS TEXT) LIKE %s")
            params.append(f"%{needle}%")
        where.append("(" + " OR ".join(ors) + ")")

    # Specific subsystem must have a given class
    if subsys_filter and subsys_filter in columns and subsys_class in ("GOLDEN", "QUESTIONABLE", "BAD"):
        where.append(f"CAST({subsys_filter.lower()} AS TEXT) LIKE %s")
        params.append(f"%({subsys_class},%")

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""
    return where_clause, params

# ---------- QUERIES ----------
def count_goodruns(filters, columns):
    where_clause, params = build_where(filters, columns)
    sql = f"SELECT COUNT(*) FROM goodruns {where_clause}"
    with _conn_main() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]

def fetch_goodruns_page(filters, columns, limit, offset):
    """
    returns: raw_rows (list of tuples)
      tuple = (runnumber, MVTX, INTT, ..., sEPD) in the same order as columns
    """
    where_clause, params = build_where(filters, columns)
    select_cols = ",".join([c.lower() for c in columns])
    sql = f"""
        SELECT runnumber, {select_cols}
        FROM goodruns
        {where_clause}
        ORDER BY runnumber DESC
        LIMIT %s OFFSET %s
    """
    with _conn_main() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params + [limit, offset])
            return cur.fetchall()

def get_run_metadata(run_numbers):
    """
    DAQ metadata: duration + runtype for given run_numbers
    returns: dict[rn] = {"duration": dur, "runtype": runtype_lower}
    """
    if not run_numbers:
        return {}
    placeholders = ",".join(["%s"] * len(run_numbers))
    sql = f"""
        SELECT runnumber,
               CAST(EXTRACT(EPOCH FROM ertimestamp) AS BIGINT)
               - CAST(EXTRACT(EPOCH FROM brtimestamp) AS BIGINT) AS duration,
               runtype
        FROM run
        WHERE runnumber IN ({placeholders})
    """
    info = {}
    with _conn_daq() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, run_numbers)
            for rn, dur, rt in cur.fetchall():
                info[rn] = {"duration": dur, "runtype": (rt or "").lower()}
    return info

def apply_updates(updates_by_run):
    """
    updates_by_run: dict[rn] -> list[(column_lc, runclass, notes)]
    Writes to goodruns: UPDATE goodruns SET {col} = (%s, %s) WHERE runnumber = %s
    """
    if not updates_by_run:
        return
    with _conn_main() as conn:
        with conn.cursor() as cur:
            for rn, items in updates_by_run.items():
                for col, rc, notes in items:
                    cur.execute(
                        f"UPDATE goodruns SET {col} = (%s, %s) WHERE runnumber = %s",
                        (rc, notes, rn),
                    )
        conn.commit()
