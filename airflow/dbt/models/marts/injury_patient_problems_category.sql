{{ config(
    materialized='table'
) }}

with source as (
    select * from {{ ref('injury_patient_problems_exploded') }}
),

injury_patient_problems_category as (
    select
        event_key,
        patient_problem,

    CASE 
    -- Insufficient Information (check first to catch these explicitly)
    WHEN patient_problem IN ('Insufficient Information', 
                              'Appropriate Term / Code Not Available',
                              'No Clinical Signs, Symptoms or Conditions',
                              'Unspecified Nervous System Problem') 
        THEN 'Insufficient Information'
    
    -- Valve Dysfunction
    WHEN patient_problem LIKE '%Valve Stenosis%'
         OR patient_problem LIKE '%Valve Insufficiency%'
         OR patient_problem LIKE '%Regurgitation%'
         OR patient_problem LIKE '%Transvalvular Pressure Gradient%'
        THEN 'Valve Dysfunction'
    
    -- Thromboembolic
    WHEN patient_problem LIKE '%Thrombosis%'
         OR patient_problem LIKE '%Thrombus%'
         OR patient_problem LIKE '%Thromboembolism%'
         OR patient_problem LIKE '%Stroke%'
         OR patient_problem LIKE '%CVA%'
         OR patient_problem LIKE '%Embolism%'
         OR patient_problem LIKE '%Embolus%'
         OR patient_problem LIKE '%Myocardial Infarction%'
         OR patient_problem LIKE '%Transient Ischemic Attack%'
         OR patient_problem LIKE '%Ischemic Heart Disease%'
        THEN 'Thromboembolic'
    
    -- Infectious
    WHEN patient_problem LIKE '%Endocarditis%'
         OR patient_problem LIKE '%Sepsis%'
         OR patient_problem LIKE '%Infection%'
         OR patient_problem LIKE '%Fever%'
         OR patient_problem LIKE '%Chills%'
        THEN 'Infectious'
    
    -- Cardiac Rhythm / Electrical
    WHEN patient_problem LIKE '%Arrhythmia%'
         OR patient_problem LIKE '%Fibrillation%'
         OR patient_problem LIKE '%Flutter%'
         OR patient_problem LIKE '%Heart Block%'
         OR patient_problem LIKE '%Bradycardia%'
         OR patient_problem LIKE '%Tachycardia%'
         OR patient_problem LIKE '%EKG%'
         OR patient_problem LIKE '%ECG%'
         OR patient_problem LIKE '%Irregular Pulse%'
        THEN 'Cardiac Rhythm / Electrical'
    
    -- Heart Failure / Hemodynamic
    WHEN patient_problem LIKE '%Heart Failure%'
         OR patient_problem LIKE '%Cardiogenic Shock%'
         OR patient_problem LIKE '%Cardiac Arrest%'
         OR patient_problem LIKE '%Low Cardiac Output%'
         OR patient_problem LIKE '%Hypotension%'
         OR patient_problem LIKE '%Cardiomyopathy%'
         OR patient_problem LIKE '%Hypovolemic Shock%'
        THEN 'Heart Failure / Hemodynamic'
    
    -- Structural / Mechanical
    WHEN patient_problem LIKE '%Aneurysm%'
         OR patient_problem LIKE '%Pseudoaneurysm%'
         OR patient_problem LIKE '%Cusp Tear%'
         OR patient_problem LIKE '%Perforation%'
         OR patient_problem LIKE '%Dissection%'
         OR patient_problem LIKE '%Calcification%'
         OR patient_problem LIKE '%Calcium Deposits%'
         OR patient_problem LIKE '%Fibrosis%'
         OR patient_problem LIKE '%Obstruction%'
         OR patient_problem LIKE '%Occlusion%'
         OR patient_problem LIKE '%Failure of Implant%'
         OR patient_problem LIKE '%Graft failure%'
         OR patient_problem LIKE '%Foreign Body Reaction%'
         OR patient_problem LIKE '%Pannus%'
         OR patient_problem = 'Stenosis'
        THEN 'Structural / Mechanical'
    
    -- Hemorrhagic / Bleeding
    WHEN patient_problem LIKE '%Hemorrhage%'
         OR patient_problem LIKE '%Bleeding%'
         OR patient_problem LIKE '%Blood Loss%'
         OR patient_problem LIKE '%Anemia%'
         OR patient_problem LIKE '%Cardiac Tamponade%'
         OR patient_problem LIKE '%Hemothorax%'
         OR patient_problem LIKE '%Pericardial Effusion%'
        THEN 'Hemorrhagic / Bleeding'
    
    -- Symptomatic Presentation (catch-all for symptoms)
    ELSE 'Symptomatic Presentation'
    
END AS problem_category

    FROM source
)

select * from injury_patient_problems_category
