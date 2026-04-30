#!/bin/bash
# Wrapper script for analyze.py.
# Disables the GIL on free-threaded Python builds for better parallelism.
# On standard Python, PYTHON_GIL is not set (it would cause a fatal error).
# Usage: ./run.sh [analyze.py arguments...]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export ANALYZE_VIA_WRAPPER=1

# Detect free-threaded Python (sysconfig.get_config_var('Py_GIL_DISABLED'))
if python3 -c "import sysconfig; exit(0 if sysconfig.get_config_var('Py_GIL_DISABLED') else 1)" 2>/dev/null; then
    export PYTHON_GIL=0
fi

exec python3 "$SCRIPT_DIR/analyze.py" "$@"
