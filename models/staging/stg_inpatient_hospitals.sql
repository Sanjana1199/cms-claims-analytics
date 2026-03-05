-- stg_inpatient_hospitals.sql
-- STAGING MODEL: Cleans raw Medicare inpatient hospital data
--
-- What this does:
--   1. Renames CMS column names to readable names
--   2. Casts data types properly
--   3. Filters out rows missing critical fields
--
-- Source: CMS Medicare Inpatient Hospitals by Provider and Service (2023)

SELECT
    -- Hospital identifiers
    rndrng_prvdr_ccn                    AS hospital_ccn,
    rndrng_prvdr_org_name               AS hospital_name,

    -- Location
    rndrng_prvdr_city                   AS hospital_city,
    rndrng_prvdr_st                     AS hospital_address,
    UPPER(rndrng_prvdr_state_abrvtn)    AS hospital_state,
    rndrng_prvdr_zip5                   AS hospital_zip,
    rndrng_prvdr_state_fips             AS state_fips_code,
    rndrng_prvdr_ruca                   AS hospital_ruca_code,
    rndrng_prvdr_ruca_desc              AS hospital_ruca_description,

    -- Diagnosis Related Group (how hospitals get paid)
    drg_cd                              AS drg_code,
    drg_desc                            AS drg_description,

    -- Utilization
    CAST(tot_dschrgs AS INTEGER)        AS total_discharges,

    -- Payment metrics
    ROUND(avg_submtd_cvrd_chrg, 2)     AS avg_covered_charges,
    ROUND(avg_tot_pymt_amt, 2)         AS avg_total_payment,
    ROUND(avg_mdcr_pymt_amt, 2)        AS avg_medicare_payment

FROM {{ source('raw', 'inpatient_hospitals') }}

-- Filter out rows missing critical identifiers
WHERE rndrng_prvdr_ccn IS NOT NULL
  AND drg_cd IS NOT NULL
