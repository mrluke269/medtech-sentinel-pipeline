{{ config(
    materialized='table'
) }}

-- Generate a date dimension table covering a wide range of dates
with date_sequence as (
SELECT 
    DATEADD('day', ROW_NUMBER() OVER (ORDER BY NULL) - 1, '2020-01-01'::DATE) as full_date
FROM TABLE(GENERATOR(ROWCOUNT => 2500))
),

dim_date as (
    select
        TO_NUMBER(TO_CHAR(full_date, 'YYYYMMDD')) as date_key,
        full_date,
        EXTRACT(year FROM full_date) as year,
        EXTRACT(month FROM full_date) as month,
        EXTRACT(day FROM full_date) as day,
        EXTRACT(quarter FROM full_date) as quarter,
        DAYOFWEEK(full_date) as day_of_week,
        WEEKOFYEAR(full_date) as week_of_year,
        TO_CHAR(full_date, 'Day') as day_name,
        TO_CHAR(full_date, 'Month') as month_name,
        CASE WHEN EXTRACT(month FROM full_date) IN (1,2,3) THEN 'Q1'
             WHEN EXTRACT(month FROM full_date) IN (4,5,6) THEN 'Q2'
             WHEN EXTRACT(month FROM full_date) IN (7,8,9) THEN 'Q3'
             WHEN EXTRACT(month FROM full_date) IN (10,11,12) THEN 'Q4'
        END as quarter_name
    from date_sequence
    where full_date <= CURRENT_DATE()
)

select * from dim_date