-- Sanity check for metrics added in schema 33-37:
--   math_ops, math_ops_fdlibm, math_ops_fdlibm_2 (diag),
--   mathml_diag_values, gl_params (webgl1/2 + software), gl_params_extensions, gamepads
--
-- For each metric reports: total submissions, how many have a non-null/non-empty value,
-- and a sample value so we can eyeball whether it looks reasonable.
--
-- Run against schema >= 37 to verify new data is populated correctly.

WITH raw AS (
  SELECT
    d.metrics.quantity.characteristics_submission_schema                  AS schema,
    d.metrics.text2.characteristics_math_ops                              AS math_ops,
    d.metrics.text2.characteristics_math_ops_fdlibm                       AS math_ops_fdlibm,
    d.metrics.text2.characteristics_math_ops_fdlibm_2                     AS math_ops_diag,
    d.metrics.text2.characteristics_mathml_diag_values                    AS mathml_diag,
    d.metrics.text2.characteristics_gl_params                             AS webgl1_params,
    d.metrics.text2.characteristics_gl_params_software                    AS webgl1_params_sw,
    d.metrics.text2.characteristics_gl2_params                            AS webgl2_params,
    d.metrics.text2.characteristics_gl2_params_software                   AS webgl2_params_sw,
    d.metrics.text2.characteristics_gl_params_extensions                  AS webgl_extensions,
    d.metrics.text2.characteristics_gl_params_extensions_software         AS webgl_extensions_sw,
    d.metrics.text2.characteristics_gl2_params_extensions                 AS webgl2_extensions,
    d.metrics.text2.characteristics_gl2_params_extensions_software        AS webgl2_extensions_sw,
    ARRAY_TO_STRING(d.metrics.string_list.characteristics_gamepads, ',')  AS gamepads
  FROM mozdata.firefox_desktop.user_characteristics d
  WHERE d.metrics.quantity.characteristics_submission_schema >= 37
    AND d.submission_timestamp >= TIMESTAMP('2026-02-15')
    AND d.submission_timestamp < TIMESTAMP('2026-03-17')
),
totals AS (SELECT COUNT(*) AS n FROM raw),
stats AS (
  SELECT 'math_ops'           AS metric, COUNT(*) AS present, ANY_VALUE(math_ops)           AS sample FROM raw WHERE math_ops IS NOT NULL           UNION ALL
  SELECT 'math_ops_fdlibm',             COUNT(*),             ANY_VALUE(math_ops_fdlibm)    FROM raw WHERE math_ops_fdlibm IS NOT NULL    UNION ALL
  SELECT 'math_ops_diag',               COUNT(*),             ANY_VALUE(math_ops_diag)      FROM raw WHERE math_ops_diag IS NOT NULL      UNION ALL
  SELECT 'mathml_diag',                 COUNT(*),             ANY_VALUE(mathml_diag)        FROM raw WHERE mathml_diag IS NOT NULL        UNION ALL
  SELECT 'webgl1_params',               COUNT(*),             ANY_VALUE(webgl1_params)      FROM raw WHERE webgl1_params IS NOT NULL      UNION ALL
  SELECT 'webgl1_params_sw',            COUNT(*),             ANY_VALUE(webgl1_params_sw)   FROM raw WHERE webgl1_params_sw IS NOT NULL   UNION ALL
  SELECT 'webgl2_params',               COUNT(*),             ANY_VALUE(webgl2_params)      FROM raw WHERE webgl2_params IS NOT NULL      UNION ALL
  SELECT 'webgl2_params_sw',            COUNT(*),             ANY_VALUE(webgl2_params_sw)   FROM raw WHERE webgl2_params_sw IS NOT NULL   UNION ALL
  SELECT 'webgl_extensions',            COUNT(*),             ANY_VALUE(webgl_extensions)   FROM raw WHERE webgl_extensions IS NOT NULL   UNION ALL
  SELECT 'webgl_extensions_sw',         COUNT(*),             ANY_VALUE(webgl_extensions_sw)FROM raw WHERE webgl_extensions_sw IS NOT NULL UNION ALL
  SELECT 'webgl2_extensions',           COUNT(*),             ANY_VALUE(webgl2_extensions)  FROM raw WHERE webgl2_extensions IS NOT NULL  UNION ALL
  SELECT 'webgl2_extensions_sw',        COUNT(*),             ANY_VALUE(webgl2_extensions_sw)FROM raw WHERE webgl2_extensions_sw IS NOT NULL UNION ALL
  SELECT 'gamepads',                    COUNT(*),             ANY_VALUE(gamepads)           FROM raw WHERE gamepads IS NOT NULL AND gamepads != ''
)
SELECT
  s.metric,
  t.n                                                         AS total_submissions,
  s.present                                                   AS non_null,
  ROUND(100.0 * s.present / t.n, 1)                          AS pct_present,
  LEFT(s.sample, 120)                                         AS sample_value
FROM stats s
CROSS JOIN totals t
ORDER BY s.metric
