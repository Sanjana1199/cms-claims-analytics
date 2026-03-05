SELECT
      hospital_state,
      drg_code,
      drg_description,
      COUNT(DISTINCT hospital_ccn)            AS total_hospitals,
      SUM(total_discharges)                   AS total_discharges,
      ROUND(AVG(avg_covered_charges), 2)      AS avg_covered_charges,
      ROUND(AVG(avg_medicare_payment), 2)     AS avg_medicare_payment,
      ROUND(
          (AVG(avg_covered_charges) - AVG(avg_medicare_payment))
          / NULLIF(AVG(avg_covered_charges), 0) * 100, 2
      )                                       AS payment_variance_pct

  FROM {{ ref('stg_inpatient_hospitals') }}

  GROUP BY hospital_state, drg_code, drg_description