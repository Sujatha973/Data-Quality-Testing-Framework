select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
-- Custom generic test: flags any row where the column doesn't look like
-- a well-formed email address (basic regex: text@text.text).

select *
from "dq_db"."analytics_staging"."stg_customers"
where email is not null
  and email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'


      
    ) dbt_internal_test