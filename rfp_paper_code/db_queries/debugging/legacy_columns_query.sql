-- Query for metrics that existed historically but have since been removed from metrics.yaml.
-- These columns appear in the type CSV snapshots but not in the current columnular_query.
--
-- Removal timeline:
--   2024-08-07: characteristics_audio_devices
--   2024-12-11: characteristics_canvasdata3avif/png/webp/cspsafe (+ software variants)
--   2025-01-15: characteristics_ice_foundations, media_capabilities, media_devices, voices, webglinfo
--   2025-01-30: characteristics_gl_version, gl_params_v1/v2 (+ software variants)
--   2025-03-11: characteristics_gl_version_software, gl2_version_software
--   2025-03-25: characteristics_color_depth/gamut, orientation_angle, pixel_depth,
--               posx/posy, screen_orientation, scalings, video_dynamic_range
--   2026-02-04: characteristics_canvasdata[1-13]software (old no-underscore naming)
--
-- Adjust the submission_timestamp filter to the period when the metrics you need were active.

SELECT
    characteristics_client_identifier,
    geo,
    header,
    isp,
    user_agent,
    -- ------------- QUANTITY
    characteristics_color_depth,
    characteristics_color_gamut,
    characteristics_gl_version,
    characteristics_gl_version_software,
    characteristics_gl2_version_software,
    characteristics_orientation_angle,
    characteristics_pixel_depth,
    characteristics_posx,
    characteristics_posy,
    characteristics_screen_orientation,
    -- ------------- BOOLEAN
    characteristics_video_dynamic_range,
    -- ------------- STRING
    characteristics_scalings,
    glean_client_annotation_experimentation_id,
    -- old canvas software naming (no underscore before "software")
    characteristics_canvasdata1software,
    characteristics_canvasdata2software,
    characteristics_canvasdata3software,
    characteristics_canvasdata4software,
    characteristics_canvasdata5software,
    characteristics_canvasdata6software,
    characteristics_canvasdata7software,
    characteristics_canvasdata8software,
    characteristics_canvasdata9software,
    characteristics_canvasdata10software,
    characteristics_canvasdata11_webglsoftware,
    characteristics_canvasdata12_fingerprintjs1software,
    characteristics_canvasdata13_fingerprintjs2software,
    -- experimental canvas format variants
    characteristics_canvasdata3avif,
    characteristics_canvasdata3avifsoftware,
    characteristics_canvasdata3cspsafe,
    characteristics_canvasdata3cspsafesoftware,
    characteristics_canvasdata3png,
    characteristics_canvasdata3pngsoftware,
    characteristics_canvasdata3webp,
    characteristics_canvasdata3webpsoftware,
    -- ------------- TEXT2
    characteristics_audio_devices,
    characteristics_gl_params_v1,
    characteristics_gl_params_v2,
    characteristics_gl_params_v1_software,
    characteristics_gl_params_v2_software,
    characteristics_ice_foundations,
    characteristics_media_capabilities,
    characteristics_media_devices,
    characteristics_voices,
    characteristics_webglinfo
from
(
    SELECT
        d.metrics.uuid.characteristics_client_identifier,
        array_agg(
          (
            SELECT AS STRUCT
              d.metadata.*,
              d.metrics.quantity.*,
              d.metrics.boolean.*,
              d.metrics.string.*,
              d.metrics.text2.*,
              d.metrics.string_list.*
          )
          ORDER BY d.submission_timestamp desc LIMIT 1
        )[OFFSET(0)].*
      FROM
        firefox_desktop.user_characteristics AS d
      WHERE
        submission_timestamp > '2024-08-01'
        and submission_timestamp < '2026-02-04'
        and d.metrics.quantity.characteristics_submission_schema >= 32
      GROUP BY
        d.metrics.uuid.characteristics_client_identifier,
        d.metrics.quantity.characteristics_submission_schema
)
