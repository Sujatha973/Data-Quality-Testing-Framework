# Test Case Traceability Matrix

Maps formal Test Case IDs to their Gherkin scenario, so QA/audit reports can
reference a stable ID instead of a scenario name that might get edited.

Run a single tagged test case directly with:
```bash
behave features/ --tags=@TC-DQ-001
```

| Test Case ID | Scenario | Feature file | Tag | Tool(s) |
|---|---|---|---|---|
| TC-DQ-001 | Customer email addresses are well-formed | `customer_data_quality.feature` | `@TC-DQ-001` | Great Expectations |
| TC-DQ-002 | Every order references a real customer | `order_data_quality.feature` | `@TC-DQ-002` | dbt (`relationships`) |

## Adding a new Test Case ID

1. Pick the next sequential ID: `TC-DQ-003`, `TC-DQ-004`, ...
2. Add `@TC-DQ-00X` as a tag alongside the existing tags on the target scenario
   (e.g. `@great_expectations @TC-DQ-003`)
3. Add a row to the table above
4. Verify it runs in isolation: `behave features/ --tags=@TC-DQ-00X`
