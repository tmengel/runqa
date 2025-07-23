#!/bin/bash
SUBS=(
    run
)
for sub in "${SUBS[@]}"; do
    # echo "Creating table for $sub"
    # psql -d RunQAdb -f "runqa-db/${sub}_table.sql"
    touch "02_tables/${sub}.sql"
    # print required info
    echo "-- required info" > "02_tables/${sub}.sql"
    echo "\connect RunQAdb" >> "02_tables/${sub}.sql"
    echo "CREATE TABLE IF NOT EXISTS ${sub} (" >> "02_tables/${sub}.sql"
    echo "    runnumber INTEGER PRIMARY KEY," >> "02_tables/${sub}.sql"
    echo "    run_type TEXT DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    run_time TIMESTAMPTZ DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    dataset TEXT DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    prod_status TEXT DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo ");" >> "02_tables/${sub}.sql"
done



SUBS=(
    mbd sepd tpot tpc intt mvtx zdc emcal ohcal ihcal 
    event_alignment spin crossing_angle neutral_mesons jets single_photons photon_jet dijets
)
for sub in "${SUBS[@]}"; do
    # echo "Creating table for $sub"
    # psql -d RunQAdb -f "runqa-db/${sub}_table.sql"
    touch "02_tables/${sub}.sql"
    # print required info
    echo "-- required info" > "02_tables/${sub}.sql"
    echo "\connect RunQAdb" >> "02_tables/${sub}.sql"
    echo "CREATE TABLE IF NOT EXISTS ${sub}_triage (" >> "02_tables/${sub}.sql"
    echo "    runnumber INTEGER PRIMARY KEY REFERENCES run(runnumber)," >> "02_tables/${sub}.sql"
    echo "    qa_status varchar(255) DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    qa_status_auto TEXT DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    qa_time TIMESTAMPTZ DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    notes varchar(255) DEFAULT NULL" >> "02_tables/${sub}.sql"
    echo ");" >> "02_tables/${sub}.sql"
    echo "" >> "02_tables/${sub}.sql"
done



SUBS=(
    prod_info
    run_info
    daq_info
)
for sub in "${SUBS[@]}"; do
    # echo "Creating table for $sub"
    # psql -d RunQAdb -f "runqa-db/${sub}_table.sql"
    touch "02_tables/${sub}.sql"
    # print required info
    echo "-- required info" > "02_tables/${sub}.sql"
    echo "\connect RunQAdb" >> "02_tables/${sub}.sql"
    echo "CREATE TABLE IF NOT EXISTS ${sub} (" >> "02_tables/${sub}.sql"
    echo "    runnumber INTEGER PRIMARY KEY REFERENCES run(runnumber)," >> "02_tables/${sub}.sql"
    echo "    qa_status varchar(255) DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo "    qa_status_auto TEXT DEFAULT NULL," >> "02_tables/${sub}.sql"
    echo ");" >> "02_tables/${sub}.sql"
done