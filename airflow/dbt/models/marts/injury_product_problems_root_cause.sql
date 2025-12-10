-- death_product_problems_root_cause (one root cause per event)

{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('injury_product_problems_category') }}
),

injury_product_problems_root_cause as (
    select
        event_key,
        problem_category,

    CASE 
        WHEN problem_category = 'Procedural / Anatomy' THEN 1
        WHEN problem_category = 'Critical Structural Failure' THEN 2
        WHEN problem_category = 'Biological / Infection' THEN 3
        WHEN problem_category = 'Hemodynamic / Functional' THEN 4
       ELSE 5
    END AS priority
    FROM source
    qualify row_number() OVER (PARTITION BY event_key order by priority) = 1
)

select event_key, problem_category from injury_product_problems_root_cause