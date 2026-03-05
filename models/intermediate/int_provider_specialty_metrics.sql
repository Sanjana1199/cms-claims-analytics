SELECT
      provider_specialty,
      provider_state,
      COUNT(DISTINCT provider_npi)        AS total_providers,
      SUM(total_services)                 AS total_services,
      SUM(total_beneficiaries)            AS total_beneficiaries,
      ROUND(AVG(avg_submitted_charge), 2) AS avg_submitted_charge,
      ROUND(AVG(avg_medicare_payment), 2) AS avg_medicare_payment,
      ROUND(
          (AVG(avg_submitted_charge) - AVG(avg_medicare_payment))
          / NULLIF(AVG(avg_submitted_charge), 0) * 100, 2
      )                                   AS payment_variance_pct

  FROM {{ ref('stg_physician_utilization') }}

  GROUP BY provider_specialty, provider_state