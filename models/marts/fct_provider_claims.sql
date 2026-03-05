SELECT
      provider_npi,
      provider_specialty,
      provider_state,
      provider_city,
      provider_zip,
      hcpcs_code,
      hcpcs_description,
      place_of_service,
      total_beneficiaries,
      total_services,
      avg_submitted_charge,
      avg_medicare_allowed_amount,
      avg_medicare_payment,
      avg_medicare_standardized_amount,
      ROUND(
          (avg_submitted_charge - avg_medicare_payment)
          / NULLIF(avg_submitted_charge, 0) * 100, 2
      )                                   AS payment_variance_pct,
      ROUND(
          avg_submitted_charge * total_services, 2
      )                                   AS total_submitted_charges,
      ROUND(
          avg_medicare_payment * total_services, 2
      )                                   AS total_medicare_payments

  FROM {{ ref('stg_physician_utilization') }}