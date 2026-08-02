from behave import given
import psycopg2


@given('the "{table_name}" table is loaded from "{qualified_name}"')
def step_table_is_loaded(context, table_name, qualified_name):
    schema, table = qualified_name.split(".")
    conn = psycopg2.connect(**context.db_settings)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table};")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    assert count > 0, (
        f"Expected {qualified_name} to contain rows before validating it, found 0. "
        f"Did you run scripts/load_data.py?"
    )
    context.row_count = count
    print(f"[common_steps] {qualified_name} has {count} rows.")
