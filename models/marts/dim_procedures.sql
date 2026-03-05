SELECT DISTINCT
      hcpcs_code,
      hcpcs_description,
      is_drug_service

  FROM {{ ref('stg_physician_utilization') }}

  WHERE hcpcs_code IS NOT NULL