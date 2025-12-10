{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('death_product_problems_category') }}
),

death_product_problems_root_cause as (
    select
        event_key,
        problem_category,

    CASE 
        WHEN problem_category = 'Procedural / Anatomy' THEN 1
        WHEN problem_category = 'Critical Structural Failure' THEN 2
        WHEN problem_category = 'Hemodynamic / Functional' THEN 3
        ELSE 4
    END AS priority
    FROM source
    QUALIFY ROW_NUMBER() OVER (PARTITION BY event_key ORDER BY priority) = 1
)

select event_key, problem_category from death_product_problems_root_cause