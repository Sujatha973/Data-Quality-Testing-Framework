Feature: Order table data quality
  As a data quality engineer
  I want the "orders" table validated against defined rules
  So that revenue and fulfillment reporting is always trustworthy

  Background:
    Given the "orders" table is loaded from "raw.orders"

  @great_expectations @critical
  Scenario: Order primary key is unique and never null
    When I run the Great Expectations checkpoint "orders_checkpoint"
    Then the expectation "expect_column_values_to_be_unique" on column "order_id" should pass
    And the expectation "expect_column_values_to_not_be_null" on column "order_id" should pass

  @great_expectations @critical
  Scenario: Order amounts are never negative
    When I run the Great Expectations checkpoint "orders_checkpoint"
    Then the expectation "expect_column_values_to_be_between" on column "amount" should pass

  @great_expectations
  Scenario: Order status is always a known lifecycle value
    When I run the Great Expectations checkpoint "orders_checkpoint"
    Then the expectation "expect_column_values_to_be_in_set" on column "status" should pass

  @dbt @critical @TC-DQ-002
  Scenario: Every order references a real customer
    When I run dbt tests for model "stg_orders"
    Then the dbt test "relationships" on "stg_orders.customer_id" should pass

  @dbt
  Scenario: dbt enforces order table constraints
    When I run dbt tests for model "stg_orders"
    Then all dbt tests for "stg_orders" should pass
