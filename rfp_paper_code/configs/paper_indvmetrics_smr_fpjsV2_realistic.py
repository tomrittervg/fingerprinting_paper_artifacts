"""SMR for the Individual Metric Analysis table — FPJSv2_Realistic only.

Same as paper_indvmetrics_smr_fpjsV2.py but targets the realistic variant
(FPJSv2 without screen_web_inner / screen_web_outer).

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./analyze.py --start-day YYYYMMDD --end-day YYYYMMDD \\
    -o /work/sandbox-analyses/schema37/smr_fpjs_realistic --cache-dir /work/sandbox-cache \\
    --partition-width 2 \\
    -c configs/paper_indvmetrics_smr_fpjsV2_realistic.py --skip-progress-bars
"""

import importlib.util as _ilu, os as _os
_spec = _ilu.spec_from_file_location("_base", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "paper_indvmetrics_smr.py"))
_base = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_base)
globals().update({k: v for k, v in vars(_base).items() if not k.startswith('_')})

script_config = {**script_config, 'smr_fingerprinters': {'FPJSv2_Realistic'}}  # noqa: F821
