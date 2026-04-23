"""ISMRP (metric replacement) — Android only.

Single-OS mode to reduce memory usage.
"""

from configs.ismrp import *

script_config = dict(script_config)
script_config['os_filter'] = 'Android'
script_config['per_os_analysis'] = False
