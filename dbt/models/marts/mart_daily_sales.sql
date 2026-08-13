with stg as (
    select * from {{ ref('stg_sales') }}
)

select
    source_date,
    count(*) as sales_count,
    sum(quantity) as total_quantity,
    sum(total_price) as total_revenue,
    sum(discount_per_item * quantity) as total_discount,
    count(distinct client_id) as unique_customers,
    count(distinct product_id) as unique_products
from stg
group by source_date
