CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Alembic defaults to VARCHAR(32), but this repository uses descriptive revision IDs.
-- Keep this in bootstrap as defense in depth; migrations/env.py also upgrades existing installs.
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(255) NOT NULL PRIMARY KEY
);
ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);
