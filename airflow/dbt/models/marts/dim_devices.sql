{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('stg_adverse_events') }}
),

distinct_device as (
    select
        -- Group By these to define the "Grain"
        coalesce(manufacturer_name, 'Unknown') as manufacturer_name,
        coalesce(brand_name, 'Unknown') as brand_name,
        coalesce(product_code, 'Unknown') as product_code,

        -- Max these to handle duplicates
        MAX(coalesce(device_name, 'Unknown')) as device_name,
        MAX(coalesce(generic_name, 'Unknown')) as generic_name,
        MAX(coalesce(device_class, 'Unknown')) as device_class

    from source
    group by 1, 2, 3
),

final as (
    select
        -- 1. The Surrogate Key
        MD5(concat(
            manufacturer_name, 
            '-',
            brand_name,
            '-',
            product_code
        )) as device_key,
        
        -- 2. The Business Keys
        manufacturer_name,
        brand_name,
        product_code,

        -- 3. The Descriptive Context
        device_name,
        generic_name,
        device_class

    from distinct_device
)

select * from final