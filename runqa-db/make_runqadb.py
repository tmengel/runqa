import psycopg2

conn = psycopg2.connect(
    dbname="Production",
    user="phnxrc",
    host="sphnxproddbmaster",
)

cur = conn.cursor()

cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'triage') THEN
        CREATE TYPE triage AS (
            status varchar(255),
            note varchar(255)
        );
    END IF;
END$$;
""")


columns = [
    ("mbd", "triage"),
    ("sepd", "triage"),
    ("tpot", "triage"),
    ("tpc", "triage"),
    ("intt", "triage"),
    ("mvtx", "triage"),
    ("zdc", "triage"),
    ("emcal", "triage"),
    ("ohcal", "triage"),
    ("ihcal", "triage"),
    ("event_align", "triage"),
    ("spin", "triage"),
    ("crossing_angle", "triage"),
    ("neutral_mesons", "triage"),
    ("jets", "triage"),
    ("single_photons", "triage"),
    ("photon_jet", "triage"),
    ("dijets", "triage"),
]

def ensure_table(table_name, suffix=""):
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        runnumber integer PRIMARY KEY
    );
    """)
    cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = %s;
    """, (table_name,))
    existing_columns = set(row[0].lower() for row in cur.fetchall())

    for col, coltype in columns:
        full_col = col + suffix
        if full_col.lower() not in existing_columns:
            cur.execute(f"""
            ALTER TABLE {table_name}
            ADD COLUMN {full_col} {coltype}
            DEFAULT ROW('NONE', 'Pending QA')::{coltype};
            """)
            print(f"Added column {full_col} to {table_name}")

# Create or update tables
ensure_table("runtriage_auto", suffix="_auto")

columns.append(
    ("nevents", "bigint"),
    ("dataset", "text"),
    ("tag", "text"),
    ("prod_status", "prod_status")
    )
ensure_table("runtriage")
# Add species and run_year columns if missing
for table in ["runtriage"]:
    # Add species
    cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = %s AND lower(column_name) = 'species';
    """, (table,))
    if cur.fetchone() is None:
        cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN species species_type DEFAULT 'nocoll';
        """)
        print(f"Added species column to {table}")

    # Add run_year
    cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = %s AND lower(column_name) = 'run_year';
    """, (table,))
    if cur.fetchone() is None:
        cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN run_year run_year DEFAULT 'NA';
        """)
        print(f"Added run_year column to {table}")

# Finalize
conn.commit()
cur.close()
conn.close()

print("runtriage and runtriage_auto tables created or updated successfully.")
