"""
Runs both Great Expectations checkpoints directly via the GE Python API,
independent of Behave. Used as its own CI stage so Great Expectations has
a dedicated pipeline job with a clean pass/fail exit code, separate from
the BDD layer.

Usage:
    python3 scripts/run_ge_checkpoints.py
Exit code:
    0 if both checkpoints pass, 1 if either fails.
"""
import json
import os
import sys

import great_expectations as gx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GE_PROJECT_DIR = os.path.join(ROOT, "great_expectations")
REPORTS_DIR = os.path.join(ROOT, "reports")

CHECKPOINTS = ["customers_checkpoint", "orders_checkpoint"]


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ge_context = gx.get_context(context_root_dir=GE_PROJECT_DIR)

    overall_success = True
    summary = []

    for checkpoint_name in CHECKPOINTS:
        result = ge_context.run_checkpoint(checkpoint_name=checkpoint_name)
        success = result.success
        overall_success = overall_success and success

        out_path = os.path.join(REPORTS_DIR, f"{checkpoint_name}_result.json")
        with open(out_path, "w") as f:
            json.dump(result.to_json_dict(), f, indent=2, default=str)

        status = "PASSED" if success else "FAILED"
        print(f"[{status}] Checkpoint '{checkpoint_name}' -> {out_path}")
        summary.append({"checkpoint": checkpoint_name, "success": success})

    with open(os.path.join(REPORTS_DIR, "ge_checkpoints_summary.json"), "w") as f:
        json.dump({"overall_success": overall_success, "checkpoints": summary}, f, indent=2)

    if not overall_success:
        print("\nOne or more Great Expectations checkpoints failed.")
        sys.exit(1)

    print("\nAll Great Expectations checkpoints passed.")


if __name__ == "__main__":
    main()
