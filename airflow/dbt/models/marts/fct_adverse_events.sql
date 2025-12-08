{{ config(
    materialized='incremental',
    unique_key='event_key'
) }}


with source as (
    select * from {{ ref('stg_adverse_events') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),
dim_devices as (
    select * from {{ ref('dim_devices') }}
),
dim_manufacturers as (
    select * from {{ ref('dim_manufacturers') }}
),
dim_event_types as (
    select * from {{ ref('dim_event_types') }}
),


final as (
    select  fde.mdr_report_key as event_key,
            ddt.date_key as date_key,
            dd.device_key as device_key,
            dm.manufacturer_key as manufacturer_key,
            det.event_type_key as event_type_key,
            fde.patient_problems as patient_problems,
            fde.product_problems as product_problems,
            fde.loaded_at as loaded_at

            

    from source as fde
        left join dim_devices as dd
            on coalesce(fde.manufacturer_name, 'Unknown') = dd.manufacturer_name 
            and coalesce(fde.brand_name, 'Unknown') = dd.brand_name 
            and coalesce(fde.product_code, 'Unknown') = dd.product_code
        left join dim_dates as ddt
            on to_number(to_char(fde.date_received, 'YYYYMMDD')) = ddt.date_key
        left join dim_manufacturers as dm
            on coalesce(fde.manufacturer_name, 'Unknown') = dm.manufacturer_name
        left join dim_event_types as det
            on coalesce(fde.event_type, 'Unknown') = det.event_type

    {% if is_incremental() %}
    where loaded_at >= (select max(loaded_at) from {{ this }})
    {% endif %}
)

select * from final