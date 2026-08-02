"""
Loads data/customers.csv and data/orders.csv into the Postgres raw schema
defined in db/init.sql. Idempotent: truncates tables before loading.

Usage (run from repo root):
    python3 scripts/load_data.py
"""
import csv
import os
import sys

import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DQ_DB_HOST", "localhost"),
        port=os.environ.get("DQ_DB_PORT", "5432"),
        dbname=os.environ.get("DQ_DB_NAME", "dq_db"),
        user=os.environ.get("DQ_DB_USER", "dq_user"),
        password=os.environ.get("DQ_DB_PASSWORD", "dq_pass"),
    )


def load_csv(cur, table, csv_path, columns):
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            row = []
            for col in columns:
                val = r[col].strip()
                row.append(None if val == "" else val)
            rows.append(tuple(row))

    cur.execute(f"TRUNCATE TABLE raw.{table};")
    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    cur.executemany(
        f"INSERT INTO raw.{table} ({col_list}) VALUES ({placeholders})", rows
    )
    print(f"Loaded {len(rows)} rows into raw.{table}")


def main():
    conn = get_conn()
    conn.autocommit = True
    cur = conn.cursor()

    load_csv(
        cur,
        "customers",
        os.path.join(ROOT, "data", "customers.csv"),
        ["customer_id", "full_name", "email", "country", "signup_date"],
    )
    load_csv(
        cur,
        "orders",
        os.path.join(ROOT, "data", "orders.csv"),
        ["order_id", "customer_id", "order_date", "amount", "status"],
    )

    cur.close()
    conn.close()
    print("Data load complete.")


if __name__ == "__main__":
    main()
