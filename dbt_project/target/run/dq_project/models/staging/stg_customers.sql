
  create view "dq_db"."analytics_staging"."stg_customers__dbt_tmp"
    
    
  as (
    -- Thin passthrough/staging model for the raw customers table.
-- Casts and light cleanup happen here; DQ tests are defined in schema.yml.

select
    customer_id,
    nullif(trim(full_name), '') as full_name,
    lower(trim(email))          as email,
    country,
    signup_date
from raw.customers
  );