select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      -- Singular test: fails (returns rows) if any order has a negative amount.
-- dbt tests "pass" when the query returns zero rows.

select order_id, amount
from "dq_db"."analytics_staging"."stg_orders"
where amount < 0
      
    ) dbt_internal_test