-- required info
\connect RunQAdb
CREATE TABLE IF NOT EXISTS run_info (
    runnumber INTEGER PRIMARY KEY REFERENCES run(runnumber),
    qa_status varchar(255) DEFAULT NULL,
    qa_status_auto TEXT DEFAULT NULL,
);
