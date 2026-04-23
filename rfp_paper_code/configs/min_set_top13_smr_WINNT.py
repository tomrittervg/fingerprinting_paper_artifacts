"""Min-set combo analysis: top 13 metrics, combo sizes 1–4, WINNT only."""

from configs.min_set_top13_smr import *

script_config = dict(script_config)
script_config['os_filter'] = 'WINNT'
script_config['per_os_analysis'] = False
