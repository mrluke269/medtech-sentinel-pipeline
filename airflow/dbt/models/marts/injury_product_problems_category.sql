-- death_product_problems_category (problem + category)

{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('injury_product_problems_exploded') }}
),

injury_product_problems_category as (
    select
        event_key,
        product_problem,

    CASE 
    -- Priority 1: Procedural / Anatomy
    WHEN product_problem IN ('Patient Device Interaction Problem', 'Patient-Device Incompatibility', 
                            'Inadequacy of Device Shape and/or Size', 'Entrapment of Device',
                            'Device Handling Problem', 'Improper or Incorrect Procedure or Method',
                            'Labelling, Instructions for Use or Training Problem') 
        THEN 'Procedural / Anatomy'
    
    -- Priority 2: Critical Structural Failure
    WHEN product_problem IN ('Degraded', 'Mechanical Jam', 'Break', 'Fracture',
                            'Material Split, Cut or Torn', 'Material Separation',
                            'Detachment of Device or Device Component', 'Device Dislodged or Dislocated',
                            'Difficult to Open or Close', 'Migration', 'Mechanical Problem') 
        THEN 'Critical Structural Failure'
    
    -- Priority 3: Biological / Infection
    WHEN product_problem IN ('Microbial Contamination of Device', 'Device Appears to Trigger Rejection') 
        THEN 'Biological / Infection'
    
    -- Priority 4: Hemodynamic / Functional
    WHEN product_problem IN ('Device Stenosis', 'Calcified', 'Intravalvular regurgitation', 
                            'Gradient Increase', 'Perivalvular Leak', 'Fluid/Blood Leak',
                            'Thickening of Material', 'Incomplete Coaptation', 'Mechanics Altered',
                            'Therapeutic or Diagnostic Output Failure') 
        THEN 'Hemodynamic / Functional'
    
    -- Priority 5: Insufficient Information
    ELSE 'Insufficient Information'
    END AS problem_category
    FROM source
)

select * from injury_product_problems_category