#!/bin/bash
# Wrapper script for analyze.py — ensures the GIL is disabled for free-threaded Python.
# Usage: ./run.sh [analyze.py arguments...]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHON_GIL=0
export ANALYZE_VIA_WRAPPER=1
exec python3.14t "$SCRIPT_DIR/analyze.py" "$@"
