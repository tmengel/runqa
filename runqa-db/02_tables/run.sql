-- required info
\connect RunQAdb
CREATE TABLE IF NOT EXISTS run (
    runnumber INTEGER PRIMARY KEY,
    run_type TEXT DEFAULT NULL,
    run_time TIMESTAMPTZ DEFAULT NULL,
    dataset TEXT DEFAULT NULL,
    prod_status TEXT DEFAULT NULL,
);
