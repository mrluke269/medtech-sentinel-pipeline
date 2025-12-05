{{ config(
    materialized='view'
) }}

with source as (
    select * from {{ source('medtech_raw', 'RAW_ADVERSE_EVENTS') }}

),

parsed as (
    select
        -- 1. IDs and Dates (Cast to explicit types)
        raw_data:mdr_report_key::STRING as mdr_report_key,
        raw_data:date_received::DATE as date_received,
        
        -- 2. Device Information
        -- Renaming 'code' to 'product_code' for clarity downstream
        raw_data:device[0]:brand_name::STRING as brand_name,
        raw_data:device[0]:device_operator::STRING as device_operator,
        raw_data:device[0]:device_report_product_code::STRING as product_code,
        raw_data:device[0]:generic_name::STRING as generic_name,
        raw_data:device[0]:openfda:device_class::STRING as device_class,
        raw_data:device[0]:openfda:device_name::STRING as device_name,

        -- 3. Standardizing Manufacturer Names
        case 
            -- Map Junk/Generic terms to NULL
            WHEN raw_data:device[0]:manufacturer_d_name::STRING = '' THEN NULL
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'UNKNOWN' THEN NULL
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'REPLACEMENT HEART-VALVE' THEN NULL
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'EMAIL ADDRESS%' THEN NULL
            -- Standardize Edwards Lifesciences (Catch typos like LIVESCIENCES, LFIESCIENCES)
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'EDWARDS%' THEN 'Edwards Lifesciences'
            -- Standardize Covidien (Includes "COVIDIEN/MEDTRONIC")
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'COVIDIEN%' THEN 'Covidien'
            -- Standardize Medtronic (Includes "MEDTRONIC.../ COVIDIEN")
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'MEDTRONIC%' THEN 'Medtronic'
            -- Standardize Jiangyin Sinbon
            WHEN raw_data:device[0]:manufacturer_d_name::STRING ILIKE 'JIANGYIN SINBON%' THEN 'Jiangyin Sinbon Electronics Co'
            -- Keep legitimate others as-is (Advantech, Avnet, St. Jude, etc.)
            ELSE TRIM(raw_data:device[0]:manufacturer_d_name::STRING)
        END as manufacturer_name,

        -- 4. Event Details
        raw_data:event_type::STRING as event_type,
        raw_data:health_professional::STRING as health_professional,

        -- 5. Array Handling
        -- These fields are lists [ "problem1", "problem2" ]. We flatten them to strings "problem1, problem2"
        ARRAY_TO_STRING(raw_data:patient[0]:patient_problems, ', ') as patient_problems,
        ARRAY_TO_STRING(raw_data:product_problems, ', ') as product_problems,

        -- 6. Metadata
        loaded_at

    from source
)

select * from parsed