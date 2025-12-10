{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('fct_adverse_events') }}
    where event_type_key = '47deba8478555be8eecd4256caa21c7b' -- Injury
),

injury_patient_problems_exploded as (
    SELECT 
        f.event_key,
        TRIM(s.value) AS patient_problem
    FROM source f,
        TABLE(SPLIT_TO_TABLE(f.patient_problems, ',')) s
)

select * from injury_patient_problems_exploded