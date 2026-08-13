with stg as (
    select * from {{ ref('stg_sales') }}
)

select
    client_id,
    count(*) as sales_count,
    sum(quantity) as total_quantity,
    sum(total_price) as total_revenue,
    sum(discount_per_item * quantity) as total_discount,
    count(distinct product_id) as unique_products,
    min(source_date) as first_purchase_date,
    max(source_date) as last_purchase_date
from stg
group by client_id
