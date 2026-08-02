#!/usr/bin/env bash
# End-to-end environment setup. Run once before your first test run.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "==> [1/5] Starting Postgres via docker compose"
docker compose up -d
echo "    waiting for Postgres to be healthy..."
for i in {1..20}; do
  if docker compose exec -T postgres pg_isready -U dq_user -d dq_db > /dev/null 2>&1; then
    echo "    Postgres is ready."
    break
  fi
  sleep 2
done
echo "==> [2/5] Creating virtualenv + installing Python dependencies"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# Handle both Linux/macOS (.venv/bin) and Windows (.venv/Scripts) layouts
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
else
  source .venv/Scripts/activate
fi
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "==> [3/5] Generating sample data"
(cd data && python3 generate_sample_data.py)
echo "==> [4/5] Loading sample data into Postgres"
export DQ_DB_HOST=localhost DQ_DB_PORT=5432 DQ_DB_NAME=dq_db DQ_DB_USER=dq_user DQ_DB_PASSWORD=dq_pass
python3 scripts/load_data.py
echo "==> [5/5] Verifying dbt can connect"
(cd dbt_project && dbt debug --profiles-dir . )
echo ""
echo "Setup complete. Next: run 'scripts/run_all_tests.sh' to execute the full suite."