
    
    

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


