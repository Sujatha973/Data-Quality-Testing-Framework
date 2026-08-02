"""
Behave environment hooks.

Loads shared config, verifies DB connectivity before the suite runs, and
makes sure a fresh reports/ directory exists so each run's evidence
(screenshots, JSON, HTML) doesn't get mixed up with a previous run.
"""
import os
import sys
import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def db_settings():
    return {
        "host": os.environ.get("DQ_DB_HOST", "localhost"),
        "port": os.environ.get("DQ_DB_PORT", "5432"),
        "dbname": os.environ.get("DQ_DB_NAME", "dq_db"),
        "user": os.environ.get("DQ_DB_USER", "dq_user"),
        "password": os.environ.get("DQ_DB_PASSWORD", "dq_pass"),
    }


def before_all(context):
    context.root_dir = ROOT
    context.db_settings = db_settings()
    context.ge_project_dir = os.path.join(ROOT, "great_expectations")
    context.dbt_project_dir = os.path.join(ROOT, "dbt_project")

    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)

    try:
        conn = psycopg2.connect(**context.db_settings)
        conn.close()
        print(f"[environment] Connected to Postgres at {context.db_settings['host']}:{context.db_settings['port']}")
    except Exception as exc:
        print(
            "[environment] WARNING: could not connect to Postgres. "
            f"Did you run `docker compose up -d` and `scripts/load_data.py`? Error: {exc}"
        )


def before_scenario(context, scenario):
    context.ge_result = None
    context.dbt_result = None
    context.dbt_run_results = None


def after_scenario(context, scenario):
    status = "PASSED" if scenario.status.name == "passed" else "FAILED"
    print(f"[environment] Scenario '{scenario.name}' -> {status}")
