"""
Reads a behave JSON-format results file and renders a single self-contained
HTML report -- good for screenshots and for attaching to a PR/ticket as
evidence of a test run.

Usage:
    python3 scripts/generate_report.py reports/behave_results_<timestamp>.json
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Test Report - {generated_at}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#0f1117; color:#e8e8ea; margin:0; padding:2rem; }}
  h1 {{ font-size:1.6rem; margin-bottom:0.25rem; }}
  .meta {{ color:#9aa0a6; margin-bottom:1.5rem; }}
  .summary {{ display:flex; gap:1rem; margin-bottom:2rem; }}
  .card {{ background:#1a1d27; border-radius:10px; padding:1rem 1.5rem; flex:1; text-align:center; }}
  .card .num {{ font-size:2rem; font-weight:700; }}
  .pass {{ color:#3ddc84; }}
  .fail {{ color:#ff5c5c; }}
  .skip {{ color:#f4c542; }}
  .feature {{ background:#171a22; border-radius:10px; margin-bottom:1rem; padding:1rem 1.5rem; }}
  .feature h2 {{ font-size:1.1rem; margin:0 0 0.5rem 0; }}
  table {{ width:100%; border-collapse:collapse; }}
  td, th {{ text-align:left; padding:0.4rem 0.5rem; border-bottom:1px solid #2a2d38; font-size:0.92rem; }}
  .status-badge {{ padding:0.15rem 0.6rem; border-radius:6px; font-size:0.8rem; font-weight:600; }}
  .status-passed {{ background:#123d26; color:#3ddc84; }}
  .status-failed {{ background:#3d1212; color:#ff5c5c; }}
  .status-skipped {{ background:#3d3512; color:#f4c542; }}
</style>
</head>
<body>
  <h1>Data Quality Test Report</h1>
  <div class="meta">Generated {generated_at} &middot; Source: {source_file}</div>
  <div class="summary">
    <div class="card"><div class="num">{total}</div>Total Scenarios</div>
    <div class="card"><div class="num pass">{passed}</div>Passed</div>
    <div class="card"><div class="num fail">{failed}</div>Failed</div>
    <div class="card"><div class="num skip">{skipped}</div>Skipped</div>
  </div>
  {features_html}
</body>
</html>
"""

FEATURE_TEMPLATE = """
<div class="feature">
  <h2>{feature_name}</h2>
  <table>
    <tr><th>Scenario</th><th>Status</th><th>Duration (s)</th></tr>
    {rows}
  </table>
</div>
"""


def status_badge(status):
    return f'<span class="status-badge status-{status}">{status.upper()}</span>'


def main(json_path):
    with open(json_path) as f:
        data = json.load(f)

    total = passed = failed = skipped = 0
    features_html = []

    for feature in data:
        rows = []
        for element in feature.get("elements", []):
            if element.get("type") != "scenario":
                continue
            total += 1
            steps = element.get("steps", [])
            duration = sum(s.get("result", {}).get("duration", 0) for s in steps)
            statuses = [s.get("result", {}).get("status", "skipped") for s in steps]
            if "failed" in statuses:
                status = "failed"
                failed += 1
            elif all(s == "passed" for s in statuses) and statuses:
                status = "passed"
                passed += 1
            else:
                status = "skipped"
                skipped += 1

            rows.append(
                f"<tr><td>{element.get('name')}</td>"
                f"<td>{status_badge(status)}</td>"
                f"<td>{duration:.2f}</td></tr>"
            )

        features_html.append(
            FEATURE_TEMPLATE.format(
                feature_name=feature.get("name", "Unnamed feature"),
                rows="\n".join(rows) if rows else "<tr><td colspan='3'>No scenarios</td></tr>",
            )
        )

    html = HTML_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        source_file=os.path.basename(json_path),
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        features_html="\n".join(features_html),
    )

    out_path = os.path.join(ROOT, "reports", "summary_report.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"Summary report -> {out_path}")
    print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 generate_report.py <behave_results.json>")
        sys.exit(1)
    main(sys.argv[1])
