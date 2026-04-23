"""Min-set combo analysis: top 9 metrics, combo sizes 1–5, Darwin only."""

from configs.min_set_top9_smr import *

script_config = dict(script_config)
script_config['os_filter'] = 'Darwin'
script_config['per_os_analysis'] = False
