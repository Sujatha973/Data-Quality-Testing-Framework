select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        country as value_field,
        count(*) as n_records

    from "dq_db"."analytics_staging"."stg_customers"
    group by country

)

select *
from all_values
where value_field not in (
    'USA','India','UK','Germany','Canada','Australia'
)



      
    ) dbt_internal_test