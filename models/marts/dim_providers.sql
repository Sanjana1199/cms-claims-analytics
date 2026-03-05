SELECT DISTINCT
      provider_npi,
      provider_last_name,
      provider_first_name,
      provider_credentials,
      provider_entity_code,
      provider_specialty,
      provider_city,
      provider_state,
      provider_zip,
      provider_country,
      provider_ruca_code,
      provider_ruca_description

  FROM {{ ref('stg_physician_utilization') }}

  WHERE provider_npi IS NOT NULL