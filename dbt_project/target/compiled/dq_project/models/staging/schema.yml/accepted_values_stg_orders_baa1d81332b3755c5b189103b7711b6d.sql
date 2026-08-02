
    
    

with all_values as (

    select
        status as value_field,
        count(*) as n_records

    from "dq_db"."analytics_staging"."stg_orders"
    group by status

)

select *
from all_values
where value_field not in (
    'placed','shipped','delivered','cancelled','returned'
)


