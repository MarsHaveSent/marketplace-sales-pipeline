with source as (
    select id, source_date, payload, fetched_at
    from {{ source('raw', 'sales') }}
)

select
    id as sale_id,
    source_date,
    (payload->>'client_id')::bigint as client_id,
    payload->>'gender' as gender,
    (payload->>'purchase_datetime')::date as purchase_date,
    (payload->>'purchase_time_as_seconds_from_midnight')::int as purchase_time_seconds,
    (payload->>'product_id')::bigint as product_id,
    (payload->>'quantity')::int as quantity,
    (payload->>'price_per_item')::numeric as price_per_item,
    (payload->>'discount_per_item')::numeric as discount_per_item,
    (payload->>'total_price')::numeric as total_price,
    fetched_at
from source
-- ~8% строк raw.sales — полностью пустой payload (все поля null разом), отбрасываю их здесь
where payload->>'client_id' is not null
