"""
Dry-run validator: applies the SAME rules defined in
great_expectations/expectations/*.json and dbt_project/models/staging/schema.yml
directly against the CSV files, with no database or network dependency.

This exists so the framework's logic can be demonstrated and sanity-checked
anywhere (including network-restricted environments) before you run the real
Postgres + Great Expectations + dbt + Behave stack per the README.

It is NOT a replacement for the real stack -- it re-implements the same
checks in plain Python/csv so there is something runnable everywhere.

Usage:
    python3 scripts/dry_run_validate.py
Outputs:
    reports/dry_run_results.json
    reports/dry_run_report.html
"""
import csv
import json
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
COUNTRIES = {"USA", "India", "UK", "Germany", "Canada", "Australia"}
STATUSES = {"placed", "shipped", "delivered", "cancelled", "returned"}


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def check(name, description, condition_fn, rows, tool):
    """condition_fn(row) -> True if row is VALID. Returns a result dict."""
    total = len(rows)
    failing = [r for r in rows if not condition_fn(r)]
    success = len(failing) == 0
    return {
        "tool": tool,
        "check": name,
        "description": description,
        "success": success,
        "element_count": total,
        "unexpected_count": len(failing),
        "unexpected_pct": round(100 * len(failing) / total, 2) if total else 0,
        "sample_failing_rows": failing[:5],
    }


def run_customer_checks(customers):
    seen_ids = set()
    seen_emails_first_seen = {}
    results = []

    results.append(check(
        "expect_column_values_to_not_be_null (customer_id)",
        "Great Expectations: customer_id must never be null",
        lambda r: bool(r["customer_id"]),
        customers, "great_expectations",
    ))

    def is_unique_id(r):
        cid = r["customer_id"]
        if cid in seen_ids:
            return False
        seen_ids.add(cid)
        return True
    results.append(check(
        "expect_column_values_to_be_unique / dbt unique (customer_id)",
        "customer_id must be unique across all rows",
        is_unique_id, customers, "great_expectations + dbt",
    ))

    results.append(check(
        "expect_column_values_to_not_be_null (full_name)",
        "Great Expectations: full_name must never be null/blank",
        lambda r: bool(r["full_name"].strip()),
        customers, "great_expectations",
    ))

    results.append(check(
        "expect_column_values_to_match_regex / dbt valid_email_format (email)",
        "email must match a valid email pattern (GE allows 3% tolerance)",
        lambda r: bool(EMAIL_RE.match(r["email"])),
        customers, "great_expectations + dbt",
    ))

    results.append(check(
        "expect_column_values_to_be_in_set (country)",
        "country must be one of the 6 supported markets",
        lambda r: r["country"] in COUNTRIES,
        customers, "great_expectations",
    ))

    results.append(check(
        "expect_column_values_to_not_be_null (signup_date)",
        "signup_date must always be recorded",
        lambda r: bool(r["signup_date"]),
        customers, "great_expectations",
    ))

    return results


def run_order_checks(orders, customer_ids):
    seen_ids = set()
    results = []

    results.append(check(
        "expect_column_values_to_not_be_null (order_id)",
        "Great Expectations: order_id must never be null",
        lambda r: bool(r["order_id"]),
        orders, "great_expectations",
    ))

    def is_unique_order_id(r):
        oid = r["order_id"]
        if oid in seen_ids:
            return False
        seen_ids.add(oid)
        return True
    results.append(check(
        "expect_column_values_to_be_unique / dbt unique (order_id)",
        "order_id must be unique across all rows",
        is_unique_order_id, orders, "great_expectations + dbt",
    ))

    results.append(check(
        "expect_column_values_to_be_between / assert_no_negative_order_amounts (amount)",
        "amount must never be negative",
        lambda r: float(r["amount"]) >= 0,
        orders, "great_expectations + dbt",
    ))

    results.append(check(
        "expect_column_values_to_be_in_set (status)",
        "status must be a known lifecycle value (and not null)",
        lambda r: r["status"] in STATUSES,
        orders, "great_expectations",
    ))

    results.append(check(
        "dbt relationships (orders.customer_id -> customers.customer_id)",
        "Every order must reference a customer that actually exists",
        lambda r: r["customer_id"] in customer_ids,
        orders, "dbt",
    ))

    return results


def render_html(all_results, generated_at):
    total = len(all_results)
    passed = sum(1 for r in all_results if r["success"])
    failed = total - passed

    rows_html = []
    for r in all_results:
        badge_class = "status-passed" if r["success"] else "status-failed"
        badge_text = "PASSED" if r["success"] else "FAILED"
        rows_html.append(f"""
        <tr>
          <td>{r['check']}</td>
          <td>{r['tool']}</td>
          <td>{r['description']}</td>
          <td>{r['unexpected_count']} / {r['element_count']} ({r['unexpected_pct']}%)</td>
          <td><span class="status-badge {badge_class}">{badge_text}</span></td>
        </tr>""")

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Dry-run Data Quality Results - {generated_at}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#0f1117; color:#e8e8ea; margin:0; padding:2rem; }}
  h1 {{ font-size:1.5rem; margin-bottom:0.25rem; }}
  .meta {{ color:#9aa0a6; margin-bottom:1.5rem; font-size:0.9rem; }}
  .summary {{ display:flex; gap:1rem; margin-bottom:1.5rem; }}
  .card {{ background:#1a1d27; border-radius:10px; padding:1rem 1.5rem; flex:1; text-align:center; }}
  .card .num {{ font-size:2rem; font-weight:700; }}
  .pass {{ color:#3ddc84; }}
  .fail {{ color:#ff5c5c; }}
  table {{ width:100%; border-collapse:collapse; background:#171a22; border-radius:10px; overflow:hidden; }}
  td, th {{ text-align:left; padding:0.55rem 0.8rem; border-bottom:1px solid #2a2d38; font-size:0.85rem; vertical-align:top; }}
  th {{ background:#1f2330; }}
  .status-badge {{ padding:0.15rem 0.6rem; border-radius:6px; font-size:0.78rem; font-weight:600; white-space:nowrap; }}
  .status-passed {{ background:#123d26; color:#3ddc84; }}
  .status-failed {{ background:#3d1212; color:#ff5c5c; }}
  .note {{ margin-top:1.5rem; padding:1rem; background:#1a1d27; border-radius:10px; font-size:0.85rem; color:#c8c8cc; }}
</style></head>
<body>
  <h1>Dry-run data quality results</h1>
  <div class="meta">Generated {generated_at} &middot; Direct CSV validation (no DB) &middot; mirrors great_expectations/*.json + dbt_project/models/staging/schema.yml</div>
  <div class="summary">
    <div class="card"><div class="num">{total}</div>Total checks</div>
    <div class="card"><div class="num pass">{passed}</div>Passed</div>
    <div class="card"><div class="num fail">{failed}</div>Failed</div>
  </div>
  <table>
    <tr><th>Check</th><th>Tool</th><th>Rule</th><th>Failing rows</th><th>Status</th></tr>
    {"".join(rows_html)}
  </table>
  <div class="note">
    This report was generated by <code>scripts/dry_run_validate.py</code>, which re-implements the same
    rules as the Great Expectations suites and dbt schema tests directly against the CSVs (no Postgres
    needed). It's a fast sanity check. For the full, real run — actual Great Expectations checkpoints,
    actual dbt test execution, and Behave-driven Gherkin scenarios against live Postgres — follow the
    README: <code>./scripts/setup.sh</code> then <code>./scripts/run_all_tests.sh</code>.
  </div>
</body></html>"""


def main():
    customers = load_csv(os.path.join(ROOT, "data", "customers.csv"))
    orders = load_csv(os.path.join(ROOT, "data", "orders.csv"))
    customer_ids = {r["customer_id"] for r in customers}

    all_results = run_customer_checks(customers) + run_order_checks(orders, customer_ids)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reports_dir = os.path.join(ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    with open(os.path.join(reports_dir, "dry_run_results.json"), "w") as f:
        json.dump({"generated_at": generated_at, "results": all_results}, f, indent=2)

    html = render_html(all_results, generated_at)
    with open(os.path.join(reports_dir, "dry_run_report.html"), "w") as f:
        f.write(html)

    total = len(all_results)
    passed = sum(1 for r in all_results if r["success"])
    print(f"Ran {total} checks: {passed} passed, {total - passed} failed.")
    print("Report -> reports/dry_run_report.html")
    for r in all_results:
        status = "PASS" if r["success"] else "FAIL"
        print(f"  [{status}] {r['check']} — {r['unexpected_count']}/{r['element_count']} failing")


if __name__ == "__main__":
    main()
