-- stg_physician_utilization.sql
-- STAGING MODEL: Cleans raw Medicare physician utilization data
--
-- What this does:
--   1. Renames cryptic CMS column names to readable names
--   2. Casts data types (strings to numbers, etc.)
--   3. Filters out rows missing critical fields
--   4. Does NOT join or apply business logic — that's for later layers
--
-- Source: CMS Medicare Provider Utilization & Payment Data (2023)

SELECT
    -- Provider identifiers
    rndrng_npi                          AS provider_npi,
    rndrng_prvdr_last_org_name          AS provider_last_name,
    rndrng_prvdr_first_name             AS provider_first_name,
    rndrng_prvdr_crdntls                AS provider_credentials,
    rndrng_prvdr_ent_cd                 AS provider_entity_code,
    rndrng_prvdr_type                   AS provider_specialty,

    -- Location
    rndrng_prvdr_city                   AS provider_city,
    UPPER(rndrng_prvdr_state_abrvtn)    AS provider_state,
    rndrng_prvdr_zip5                   AS provider_zip,
    rndrng_prvdr_cntry                  AS provider_country,
    rndrng_prvdr_ruca                   AS provider_ruca_code,
    rndrng_prvdr_ruca_desc              AS provider_ruca_description,

    -- Service details
    hcpcs_cd                            AS hcpcs_code,
    hcpcs_desc                          AS hcpcs_description,
    hcpcs_drug_ind                      AS is_drug_service,
    place_of_srvc                       AS place_of_service,

    -- Utilization metrics
    CAST(tot_benes AS INTEGER)          AS total_beneficiaries,
    CAST(tot_srvcs AS INTEGER)          AS total_services,
    CAST(tot_bene_day_srvcs AS INTEGER) AS total_beneficiary_day_services,

    -- Payment metrics
    ROUND(avg_sbmtd_chrg, 2)           AS avg_submitted_charge,
    ROUND(avg_mdcr_alowd_amt, 2)       AS avg_medicare_allowed_amount,
    ROUND(avg_mdcr_pymt_amt, 2)        AS avg_medicare_payment,
    ROUND(avg_mdcr_stdzd_amt, 2)       AS avg_medicare_standardized_amount

FROM {{ source('raw', 'physician_utilization') }}

-- Filter out rows missing critical identifiers
WHERE rndrng_npi IS NOT NULL
  AND hcpcs_cd IS NOT NULL
  AND rndrng_prvdr_state_abrvtn IS NOT NULL
