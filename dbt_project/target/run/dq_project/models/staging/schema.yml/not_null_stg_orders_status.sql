select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select status
from "dq_db"."analytics_staging"."stg_orders"
where status is null



      
    ) dbt_internal_test