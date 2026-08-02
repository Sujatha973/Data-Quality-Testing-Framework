#!/usr/bin/env bash
# Runs the complete data quality suite end-to-end and generates evidence
# (JSON + HTML reports, GE data docs) under reports/.
set -euo pipefail
cd "$(dirname "$0")/.."

source .venv/bin/activate 2>/dev/null || true
export DQ_DB_HOST=localhost DQ_DB_PORT=5432 DQ_DB_NAME=dq_db DQ_DB_USER=dq_user DQ_DB_PASSWORD=dq_pass

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p reports

echo "==> Running Behave BDD suite"
# behave-html-formatter must be installed (see requirements-optional below) for HTML output;
# JSON output works out of the box with behave itself.
python3 -m behave features/ \
  --junit --junit-directory reports/junit \
  -f json -o "reports/behave_results_${TIMESTAMP}.json" \
  -f pretty \
  || BEHAVE_EXIT=$?

echo "==> Great Expectations Data Docs are built automatically as part of running checkpoints"

echo "==> Generating consolidated summary report"
python3 scripts/generate_report.py "reports/behave_results_${TIMESTAMP}.json"

echo ""
echo "Done. Evidence saved under reports/. Open the HTML summary and GE Data Docs for screenshots."
exit "${BEHAVE_EXIT:-0}"
