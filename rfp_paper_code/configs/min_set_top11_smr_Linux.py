"""Min-set combo analysis: top 11 metrics, combo sizes 1–5, Linux only."""

from configs.min_set_top11_smr import *

script_config = dict(script_config)
script_config['os_filter'] = 'Linux'
script_config['per_os_analysis'] = False
