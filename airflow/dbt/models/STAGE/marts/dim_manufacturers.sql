{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('stg_adverse_events') }}

),

distinct_manufacturer as (
    select
        distinct
        manufacturer_name
    from source
),

dim_manufacturer as (
    select
        MD5(coalesce(manufacturer_name, 'Unknown')) as manufacturer_key,
        coalesce(manufacturer_name, 'Unknown') as manufacturer_name
    from distinct_manufacturer
)

select * from dim_manufacturer