-- injury_product_problems_exploded (one row per problem)

{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('fct_adverse_events') }}
    where event_type_key = '47deba8478555be8eecd4256caa21c7b' -- Injury

),
injury_product_problems_exploded as (
SELECT 
    f.event_key,
    TRIM(s.value) AS product_problem
FROM source f,
    TABLE(SPLIT_TO_TABLE(f.product_problems, ',')) s
)

select * from injury_product_problems_exploded