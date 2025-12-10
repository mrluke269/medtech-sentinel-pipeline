{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('injury_patient_problems_category') }}
),

injury_patient_problems_root_cause as (
    select
        event_key,
        problem_category,

    CASE problem_category
    WHEN 'Valve Dysfunction' THEN 1
    WHEN 'Structural / Mechanical' THEN 2
    WHEN 'Thromboembolic' THEN 3
    WHEN 'Infectious' THEN 4
    WHEN 'Hemorrhagic / Bleeding' THEN 5
    WHEN 'Cardiac Rhythm / Electrical' THEN 6
    WHEN 'Heart Failure / Hemodynamic' THEN 7
    WHEN 'Symptomatic Presentation' THEN 8
    WHEN 'Insufficient Information' THEN 9
    ELSE 10
    END AS priority
    FROM source
    QUALIFY ROW_NUMBER() OVER (PARTITION BY event_key ORDER BY priority) = 1
)

select event_key, problem_category from injury_patient_problems_root_cause