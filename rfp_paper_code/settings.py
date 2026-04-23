"""Runtime settings import shim.

Call sites throughout the toolkit do:

    from settings import BQ_PROJECT_ID, DEFAULT_CACHE_DIR

This module loads every key from `local_settings_example.py` first
(giving safe env-var-backed defaults), then lets `local_settings.py`
override any subset of those keys. If `local_settings.py` is absent
(e.g. after deletion for artifact sharing), the defaults stand.

Do not put values directly in this file — it is logic only.
"""

from local_settings_example import *  # noqa: F401,F403

try:
    from local_settings import *  # noqa: F401,F403
except ImportError:
    pass
