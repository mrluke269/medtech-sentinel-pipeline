
{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('fct_adverse_events') }}
    where event_type_key = '6097f89e3092d4ccd249c9d479785c1f' -- Death
),

death_product_problems_exploded as (
    SELECT 
        f.event_key,
        TRIM(s.value) AS product_problem
    FROM source f,
        TABLE(SPLIT_TO_TABLE(f.product_problems, ',')) s
)

select * from death_product_problems_exploded