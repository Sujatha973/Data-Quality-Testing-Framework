select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select email
from "dq_db"."analytics_staging"."stg_customers"
where email is null



      
    ) dbt_internal_test