"""LMR for the Individual Metric Analysis table — AkamaiV2 only.

Run one fingerprinter at a time to avoid OOM when accumulating LMR hash dicts.
See also: paper_indvmetrics_lmr_fpjsV2.py, paper_indvmetrics_lmr_signifyd.py

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./analyze.py --start-day YYYYMMDD --end-day YYYYMMDD \\
    -o /work/sandbox-analyses/schema37/lmr_akamai --cache-dir /work/sandbox-cache \\
    --partition-width 2 \\
    -c configs/paper_indvmetrics_lmr_akamaiV2.py --skip-progress-bars
"""

import importlib.util as _ilu, os as _os
_spec = _ilu.spec_from_file_location("_base", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "paper_indvmetrics_lmr.py"))
_base = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_base)
globals().update({k: v for k, v in vars(_base).items() if not k.startswith('_')})

script_config = {**script_config, 'lmr_fingerprinters': {'AkamaiV2'}}  # noqa: F821
