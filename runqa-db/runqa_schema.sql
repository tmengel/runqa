\connect RunQA

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'qa_status') THEN
        CREATE TYPE qa_status AS ENUM ('NA', 'NOPROD', 'BAD', 'QUESTIONABLE', 'GOOD');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'run_year') THEN
        CREATE TYPE run_year AS ENUM ('2023', '2024', '2025', 'NA');
    END IF;
END$$;

-- run_year INTEGER CHECK (run_year IN (2023, 2024, 2025)) DEFAULT NULL
-- qa_status varchar(20) CHECK (qa_status IN ('NA', 'BAD', 'QUESTIONABLE', 'GOOD')) DEFAULT NULL
-- qa_note varchar(255) DEFAULT NULL
-- run_status varchar(20) CHECK (run_status IN ('BAD', 'GOOD')) DEFAULT NULL
-- verified BOOLEAN DEFAULT FALSE


DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prod_status') THEN
        CREATE TYPE prod_status AS ENUM ('none', 'bad', 'questionable', 'good');
    END IF;
END$$;

-- === Tables ===

CREATE TABLE IF NOT EXISTS runtriage_auto (
    runnumber INTEGER PRIMARY KEY,

    mbd triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    sepd triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    tpot triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    tpc triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    intt triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    mvtx triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    zdc triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    emcal triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    ohcal triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    ihcal triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    event_align triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    spin triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    crossing_angle triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    neutral_mesons triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    jets triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    single_photons triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    photon_jet triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    dijets triage DEFAULT ROW('NONE', 'Pending QA')::triage
);

CREATE TABLE IF NOT EXISTS runtriage (
    runnumber INTEGER PRIMARY KEY,

    mbd triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    sepd triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    tpot triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    tpc triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    intt triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    mvtx triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    zdc triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    emcal triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    ohcal triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    ihcal triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    event_align triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    spin triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    crossing_angle triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    neutral_mesons triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    jets triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    single_photons triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    photon_jet triage DEFAULT ROW('NONE', 'Pending QA')::triage,
    dijets triage DEFAULT ROW('NONE', 'Pending QA')::triage,

    nevents BIGINT,
    dataset TEXT,
    tag TEXT,
    prod_status prod_status,
    species species_type DEFAULT 'nocoll',
    run_year run_year DEFAULT 'NA'
);
