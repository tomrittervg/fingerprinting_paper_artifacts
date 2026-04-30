"""SMR for the Individual Metric Analysis table — AkamaiV2_Realistic only.

Like paper_indvmetrics_smr_akamaiV2.py but uses the Realistic variant
(screen_web_inner and screen_web_outer removed).
"""

import importlib.util as _ilu, os as _os
_spec = _ilu.spec_from_file_location("_base", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "paper_indvmetrics_smr.py"))
_base = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_base)
globals().update({k: v for k, v in vars(_base).items() if not k.startswith('_')})

script_config = {**script_config, 'smr_fingerprinters': {'AkamaiV2_Realistic'}}  # noqa: F821
