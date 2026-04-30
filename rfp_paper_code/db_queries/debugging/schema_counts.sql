SELECT
    type,
    schema,
    COUNT(*) AS submissions
FROM (
    SELECT
        'desktop' AS type,
        d.metrics.quantity.characteristics_submission_schema AS schema
    FROM mozdata.firefox_desktop.user_characteristics AS d
    WHERE DATE(d.submission_timestamp) >= '2026-02-20'
      AND d.metrics.quantity.characteristics_submission_schema > 30

    UNION ALL

    SELECT
        'fenix' AS type,
        d.metrics.quantity.characteristics_submission_schema AS schema
    FROM mozdata.fenix.user_characteristics AS d
    WHERE DATE(d.submission_timestamp) >= '2026-02-20'
      AND d.metrics.quantity.characteristics_submission_schema > 30
)
GROUP BY type, schema
ORDER BY type, schema
