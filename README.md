# Data Quality Testing Framework

A BDD-driven data quality framework combining **Behave** (Gherkin/BDD),
**Great Expectations** (column/table-level validation), and **dbt**
(schema-level tests: uniqueness, referential integrity, accepted values)
against two Postgres tables: `customers` and `orders`.

The sample data is **intentionally seeded with real data quality issues**
(duplicate IDs, invalid emails, orphan foreign keys, negative amounts, null
statuses) so that running this framework produces genuine, explainable
pass/fail results — not just a wall of green checkmarks.

---

## 1. Architecture

```
dq-testing-framework/
├── data/
│   ├── generate_sample_data.py   # Generates customers.csv / orders.csv (stdlib only)
│   ├── customers.csv             # 201 rows, ~5% seeded issues
│   └── orders.csv                # 800 rows, ~4.5% seeded issues
├── db/
│   └── init.sql                  # raw.customers / raw.orders DDL
├── docker-compose.yml            # Postgres 16 for local dev
├── config/
│   └── config.yaml               # Central config (DB, paths, tool settings)
├── great_expectations/
│   ├── great_expectations.yml    # Data context / datasource config
│   ├── expectations/
│   │   ├── customers_suite.json
│   │   └── orders_suite.json
│   └── checkpoints/
│       ├── customers_checkpoint.yml
│       └── orders_checkpoint.yml
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/staging/
│   │   ├── stg_customers.sql
│   │   ├── stg_orders.sql
│   │   └── schema.yml            # unique / not_null / relationships / accepted_values
│   ├── macros/test_valid_email_format.sql   # custom generic test
│   └── tests/assert_no_negative_order_amounts.sql  # custom singular test
├── features/
│   ├── customer_data_quality.feature
│   ├── order_data_quality.feature
│   ├── environment.py
│   └── steps/
│       ├── common_steps.py
│       ├── ge_steps.py           # runs GE checkpoints, asserts expectation results
│       └── dbt_steps.py          # shells out to `dbt test`, parses run_results.json
├── scripts/
│   ├── setup.sh                  # one-shot environment bring-up
│   ├── run_all_tests.sh          # runs the full suite + generates reports
│   ├── load_data.py              # loads CSVs into Postgres
│   └── generate_report.py        # behave JSON -> standalone HTML report
├── .github/workflows/data-quality.yml   # CI: runs the whole suite on push/PR
├── reports/                       # evidence output (gitignored except .gitkeep)
├── requirements.txt
└── README.md
```

**Why this stack:** Behave gives you human-readable specs stakeholders can
review without reading code. Great Expectations gives you rich,
declarative column-level checks (regex, ranges, set membership, null
counts) with an auto-generated HTML "Data Docs" report. dbt gives you
schema-level relational tests (uniqueness, referential integrity across
tables) that live right next to your transformation logic. Behave sits on
top and orchestrates both, so a single `behave features/` run gives you
one unified pass/fail signal and one report.

---

## 2. Prerequisites

- Python 3.10+
- Docker + Docker Compose (for local Postgres)
- Git

---

## 3. Start-to-end setup and execution

### Step 1 — Clone and enter the repo
```bash
git clone <your-repo-url>
cd dq-testing-framework
```

### Step 2 — Run the one-shot setup script
```bash
chmod +x scripts/setup.sh scripts/run_all_tests.sh
./scripts/setup.sh
```
This will:
1. Start Postgres via `docker compose up -d`
2. Create a virtualenv and `pip install -r requirements.txt`
3. Regenerate `data/customers.csv` and `data/orders.csv`
4. Load them into `raw.customers` / `raw.orders`
5. Run `dbt debug` to confirm the dbt ↔ Postgres connection works

### Step 3 — Run the full BDD data quality suite
```bash
source .venv/bin/activate
./scripts/run_all_tests.sh
```
This runs `behave features/`, which in turn:
- Connects to Postgres and confirms both tables are loaded (`Given` steps)
- Runs the two Great Expectations checkpoints (`customers_checkpoint`,
  `orders_checkpoint`) and asserts individual expectation results
- Runs `dbt test --select stg_customers` / `stg_orders` and asserts
  individual dbt test results (unique, not_null, relationships,
  accepted_values, plus the custom email-format and negative-amount tests)
- Writes JSON evidence to `reports/`
- Builds Great Expectations Data Docs (HTML) under
  `great_expectations/uncommitted/data_docs/local_site/index.html`
- Builds a consolidated `reports/summary_report.html`

 terminal output of `behave features/`
showing scenario names with `PASSED`/`FAILED` in color, e.g.:
```
Scenario: Customer primary key is unique and never null   # FAILED
Scenario: Customer email addresses are well-formed        # FAILED
Scenario: Order amounts are never negative                # FAILED
Scenario: Every order references a real customer          # FAILED
```
(These failures are **expected** — they're the seeded issues, and they
prove the framework actually catches problems instead of always passing.)

### Step 4 — Review the reports

| Report | Path | What to screenshot |
|---|---|---|
| Behave summary | `reports/summary_report.html` | Open in browser — shows pass/fail counts per feature/scenario with colored badges |
| Great Expectations Data Docs | `great_expectations/uncommitted/data_docs/local_site/index.html` | Open in browser — shows each expectation, expected vs. observed values, and which specific rows failed |
| dbt test results | `reports/dbt_run_results_stg_customers.json`, `..._stg_orders.json` | Raw JSON — useful for CI logs, or `dbt test` terminal output directly |
| JUnit XML | `reports/junit/*.xml` | For CI dashboards (Jenkins, GitLab, GitHub Actions test summary tab) |

```bash
# macOS
open reports/summary_report.html
open great_expectations/uncommitted/data_docs/local_site/index.html

# Linux
xdg-open reports/summary_report.html
```

### Step 5 — (Optional) Fix the seeded issues and re-run to show green
To demonstrate the full before/after story for a portfolio or demo:
1. Open `data/generate_sample_data.py`, set all the "seed ~X% issues" random
   thresholds to `0`, regenerate: `cd data && python3 generate_sample_data.py`
2. Reload: `python3 scripts/load_data.py`
3. Re-run: `./scripts/run_all_tests.sh`

### Step 6 — Push to GitHub and show CI passing
```bash
git init
git add .
git commit -m "Data quality testing framework: Behave + Great Expectations + dbt"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```
The included `.github/workflows/data-quality.yml` spins up Postgres as a
GitHub Actions service container and runs the identical suite on every
push/PR, uploading `reports/` and GE Data Docs as build artifacts.

---

## 4. What's actually being tested

**Great Expectations (`great_expectations/expectations/*.json`)**
- Row counts aren't zero
- `customer_id` / `order_id` are unique and non-null
- `email` matches a valid email regex (97% tolerance to show partial-failure handling)
- `country` / `status` are within accepted value sets
- `amount` is never negative

**dbt (`dbt_project/models/staging/schema.yml` + custom tests)**
- `unique` / `not_null` on both primary keys
- `relationships`: every `orders.customer_id` must exist in `customers.customer_id`
- `accepted_values` on `country` and `status`
- Custom generic test `valid_email_format` (regex-based, reusable across any column/model)
- Custom singular test `assert_no_negative_order_amounts.sql`

---

## 5. Extending the framework

- **Add a new table:** add a row to `config/config.yaml` under `tables`,
  add DDL to `db/init.sql`, add a GE suite + checkpoint, add a dbt staging
  model + schema.yml tests, add a `.feature` file, and reuse the existing
  step definitions (they're written generically, keyed off checkpoint/model
  names passed in from Gherkin).
- **Add a new expectation type:** just add another JSON block to the
  relevant suite file — no code changes needed.
- **Add a new dbt test:** either use a built-in generic test (`unique`,
  `not_null`, `accepted_values`, `relationships`) in `schema.yml`, or drop
  a new `.sql` file in `dbt_project/tests/` for a singular test.
- **Swap Postgres for another warehouse:** update `dbt_project/profiles.yml`
  and the `connection_string` in `great_expectations/great_expectations.yml`;
  everything else (feature files, step definitions) is warehouse-agnostic.

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `psycopg2.OperationalError: could not connect` | Run `docker compose ps` — is the `postgres` container healthy? |
| `dbt debug` fails auth | Check `DQ_DB_*` env vars match `docker-compose.yml` credentials |
| Behave can't find steps | Run `behave` from the repo root, not from inside `features/` |
| GE checkpoint errors "datasource not found" | Confirm `great_expectations/uncommitted/config_variables.yml` isn't required — this project uses env-var substitution directly in `great_expectations.yml` |
