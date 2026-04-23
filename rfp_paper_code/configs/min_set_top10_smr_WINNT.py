"""Min-set combo analysis: top 10 metrics, combo sizes 1–5, WINNT only.

Tests all C(10,k) combinations for k=1..5 using per-OS SMR orderings.
Single-OS mode to reduce memory usage.
"""

# Import base config and override os_filter
from configs.min_set_top10_smr import *

script_config = dict(script_config)
script_config['os_filter'] = 'WINNT'
script_config['per_os_analysis'] = False  # redundant with single OS
