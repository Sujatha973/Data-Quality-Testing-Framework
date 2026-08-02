
  create view "dq_db"."analytics_staging"."stg_orders__dbt_tmp"
    
    
  as (
    -- Thin passthrough/staging model for the raw orders table.
-- Casts and light cleanup happen here; DQ tests are defined in schema.yml.

select
    order_id,
    customer_id,
    order_date,
    amount,
    nullif(trim(status), '') as status
from raw.orders
  );