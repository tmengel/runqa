-- required info
\connect RunQAdb
CREATE TABLE IF NOT EXISTS spin_triage (
    runnumber INTEGER PRIMARY KEY REFERENCES run(runnumber),
    qa_status varchar(255) DEFAULT NULL,
    qa_status_auto TEXT DEFAULT NULL,
    qa_time TIMESTAMPTZ DEFAULT NULL,
    notes varchar(255) DEFAULT NULL
);

