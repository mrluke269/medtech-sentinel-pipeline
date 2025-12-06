{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('stg_adverse_events') }}

),

distinct_events as (
    select
        distinct
        event_type
    from source
),

final as (
    select
        MD5(coalesce(event_type, 'Unknown')) as event_type_key,
        coalesce(event_type, 'Unknown') as event_type,
        CASE 
            WHEN event_type ILIKE '%Death%' THEN 1
            WHEN event_type ILIKE '%Injury%' THEN 2
            WHEN event_type ILIKE '%Malfunction%' THEN 3
            ELSE 4 
        END as severity_rank
    from distinct_events
)

select * from final