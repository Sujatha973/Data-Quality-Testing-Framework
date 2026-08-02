-- Singular test: fails (returns rows) if any order has a negative amount.
-- dbt tests "pass" when the query returns zero rows.

select order_id, amount
from {{ ref('stg_orders') }}
where amount < 0
