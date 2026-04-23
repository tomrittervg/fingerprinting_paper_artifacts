"""Min-set combo analysis: top 12 metrics, combo sizes 1–5, WINNT only."""

from configs.min_set_top12_smr import *

script_config = dict(script_config)
script_config['os_filter'] = 'WINNT'
script_config['per_os_analysis'] = False
