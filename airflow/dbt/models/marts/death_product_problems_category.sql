{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('death_product_problems_exploded') }}
),

death_product_problems_category as (
    select
        event_key,
        product_problem,

    CASE 
        WHEN product_problem IN ('Patient Device Interaction Problem', 'Patient-Device Incompatibility', 
                                'Inadequacy of Device Shape and/or Size', 'Entrapment of Device') 
            THEN 'Procedural / Anatomy'
        WHEN product_problem IN ('Degraded', 'Mechanical Jam') 
            THEN 'Critical Structural Failure'
        WHEN product_problem IN ('Device Stenosis', 'Calcified', 'Intravalvular regurgitation', 'Gradient Increase') 
            THEN 'Hemodynamic / Functional'
        ELSE 'Insufficient Information'
    END AS problem_category

    FROM source
)

select * from death_product_problems_category
