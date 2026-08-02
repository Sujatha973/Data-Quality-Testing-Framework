-- Initializes the raw schema used by both Great Expectations and dbt.
-- Run automatically by docker-compose (mounted into /docker-entrypoint-initdb.d)
-- or manually via: psql -U dq_user -d dq_db -f db/init.sql

CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.customers;
CREATE TABLE raw.customers (
    customer_id   INTEGER,
    full_name     TEXT,
    email         TEXT,
    country       TEXT,
    signup_date   DATE
);

DROP TABLE IF EXISTS raw.orders;
CREATE TABLE raw.orders (
    order_id      INTEGER,
    customer_id   INTEGER,
    order_date    DATE,
    amount        NUMERIC(10, 2),
    status        TEXT
);

-- Data is loaded separately via scripts/load_data.py (uses COPY under the hood)
-- so this file works whether you're on Docker Postgres or a pre-existing server.
