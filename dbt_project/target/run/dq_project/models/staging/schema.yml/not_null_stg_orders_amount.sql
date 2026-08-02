select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select amount
from "dq_db"."analytics_staging"."stg_orders"
where amount is null



      
    ) dbt_internal_test