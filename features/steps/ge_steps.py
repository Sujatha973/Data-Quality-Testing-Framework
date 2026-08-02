import json

import os
 
from behave import when, then

import great_expectations as gx
 
 
def _get_context(context):

    # NOTE: We intentionally check context.__dict__ directly instead of using

    # hasattr(context, "_ge_context"). Behave's Context.__getattr__ raises a

    # plain KeyError (not AttributeError) for missing attributes, which

    # hasattr() does not catch -- so hasattr() would crash here instead of

    # safely returning False on the first access.

    if context.__dict__.get("_ge_context") is None:

        context._ge_context = gx.get_context(context_root_dir=context.ge_project_dir)

    return context._ge_context
 
 
@when('I run the Great Expectations checkpoint "{checkpoint_name}"')

def step_run_checkpoint(context, checkpoint_name):

    ge_context = _get_context(context)

    result = ge_context.run_checkpoint(checkpoint_name=checkpoint_name)

    context.ge_result = result
 
    # Persist raw JSON evidence for the report / screenshots

    reports_dir = os.path.join(context.root_dir, "reports")

    os.makedirs(reports_dir, exist_ok=True)

    out_path = os.path.join(reports_dir, f"{checkpoint_name}_result.json")

    with open(out_path, "w") as f:

        json.dump(result.to_json_dict(), f, indent=2, default=str)
 
    print(f"[ge_steps] Checkpoint '{checkpoint_name}' success={result.success}. Evidence -> {out_path}")
 
 
def _find_expectation_result(context, expectation_type, column):

    """Locate a single expectation's result within the last checkpoint run."""

    assert context.ge_result is not None, "No checkpoint has been run yet in this scenario."
 
    run_results = context.ge_result.run_results

    for validation_result in run_results.values():

        validation_result_obj = validation_result["validation_result"]

        for res in validation_result_obj.results:

            cfg = res.expectation_config

            if cfg.expectation_type == expectation_type and cfg.kwargs.get("column") == column:

                return res

    return None
 
 
@then('the expectation "{expectation_type}" on column "{column}" should pass')

def step_expectation_should_pass(context, expectation_type, column):

    result = _find_expectation_result(context, expectation_type, column)

    assert result is not None, (

        f"Expectation '{expectation_type}' on column '{column}' was not found in the checkpoint run. "

        f"Check the suite JSON defines it."

    )

    unexpected = result.result.get("unexpected_count", 0)

    total = result.result.get("element_count", context.__dict__.get("row_count", "?"))

    assert result.success, (

        f"Expectation '{expectation_type}' on column '{column}' FAILED: "

        f"{unexpected} unexpected value(s) out of {total} rows. "

        f"See reports/ for the full validation result."

    )
 