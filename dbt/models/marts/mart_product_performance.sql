with stg as (
    select * from {{ ref('stg_sales') }}
)

select
    product_id,
    count(*) as sales_count,
    sum(quantity) as total_quantity,
    sum(total_price) as total_revenue,
    sum(discount_per_item * quantity) as total_discount,
    count(distinct client_id) as unique_customers,
    avg(price_per_item) as avg_price_per_item,
    min(source_date) as first_sale_date,
    max(source_date) as last_sale_date
from stg
group by product_id
