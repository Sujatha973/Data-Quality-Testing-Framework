import json
import os
import shutil
import subprocess

from behave import when, then


def _run_dbt_test(context, select):
    cmd = [
        "dbt", "test",
        "--select", select,
        "--project-dir", context.dbt_project_dir,
        "--profiles-dir", context.dbt_project_dir,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    context.dbt_stdout = proc.stdout
    context.dbt_stderr = proc.stderr
    context.dbt_returncode = proc.returncode

    run_results_path = os.path.join(context.dbt_project_dir, "target", "run_results.json")
    run_results = None
    if os.path.exists(run_results_path):
        with open(run_results_path) as f:
            run_results = json.load(f)
    context.dbt_run_results = run_results

    # Copy evidence into reports/ for the run
    reports_dir = os.path.join(context.root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    if run_results_path and os.path.exists(run_results_path):
        dest = os.path.join(reports_dir, f"dbt_run_results_{select.replace(':', '_').replace('.', '_')}.json")
        shutil.copy(run_results_path, dest)

    print(f"[dbt_steps] `dbt test --select {select}` exited {proc.returncode}")
    if proc.returncode != 0:
        print(proc.stdout[-2000:])


@when('I run dbt tests for model "{model_name}"')
def step_run_dbt_tests(context, model_name):
    _run_dbt_test(context, model_name)


@then('all dbt tests for "{model_name}" should pass')
def step_all_dbt_tests_pass(context, model_name):
    assert context.dbt_run_results is not None, "No dbt run_results.json found; did dbt test run?"

    failures = [
        r for r in context.dbt_run_results.get("results", [])
        if r.get("status") not in ("pass", "success")
    ]
    if failures:
        details = "\n".join(f"  - {f['unique_id']}: {f['status']}" for f in failures)
        raise AssertionError(
            f"{len(failures)} dbt test(s) failed for model '{model_name}':\n{details}\n"
            f"Full logs in dbt_project/logs/dbt.log and reports/dbt_run_results_{model_name}.json"
        )


@then('the dbt test "{test_type}" on "{target}" should pass')
def step_specific_dbt_test_passes(context, test_type, target):
    assert context.dbt_run_results is not None, "No dbt run_results.json found; did dbt test run?"

    matches = [
        r for r in context.dbt_run_results.get("results", [])
        if test_type in r.get("unique_id", "") and target.split(".")[-1] in r.get("unique_id", "")
    ]
    assert matches, f"No dbt test matching type '{test_type}' on '{target}' was executed."

    for r in matches:
        assert r.get("status") in ("pass", "success"), (
            f"dbt test {r['unique_id']} FAILED with status '{r.get('status')}'. "
            f"Failing rows: {r.get('failures')}"
        )
