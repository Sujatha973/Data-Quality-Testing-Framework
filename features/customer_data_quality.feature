Feature: Customer table data quality
  As a data quality engineer
  I want the "customers" table validated against defined rules
  So that downstream analytics never run on broken customer data

  Background:
    Given the "customers" table is loaded from "raw.customers"

  @great_expectations @critical
  Scenario: Customer primary key is unique and never null
    When I run the Great Expectations checkpoint "customers_checkpoint"
    Then the expectation "expect_column_values_to_be_unique" on column "customer_id" should pass
    And the expectation "expect_column_values_to_not_be_null" on column "customer_id" should pass

  @great_expectations @TC-DQ-001
  Scenario: Customer email addresses are well-formed
    When I run the Great Expectations checkpoint "customers_checkpoint"
    Then the expectation "expect_column_values_to_match_regex" on column "email" should pass

  @great_expectations
  Scenario: Customer country values are within the supported market list
    When I run the Great Expectations checkpoint "customers_checkpoint"
    Then the expectation "expect_column_values_to_be_in_set" on column "country" should pass

  @dbt @critical
  Scenario: dbt enforces customer table constraints
    When I run dbt tests for model "stg_customers"
    Then all dbt tests for "stg_customers" should pass
