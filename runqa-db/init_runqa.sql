-- This creates the database ONLY if it does not already exist

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'RunQA'
    ) THEN
        EXECUTE 'CREATE DATABASE "RunQA"';
    END IF;
END$$;
