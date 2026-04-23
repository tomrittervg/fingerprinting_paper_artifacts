import io
import os
import queue
import subprocess
import threading

ANALYSIS_FOLDER = None #"../analysis-2025-06-26"
OUTPUT_FOLDER = "../output-2025-06-26"

# The pattern hash is the hash for _all_ of the files we will eventually read.  It is needed for metric aggrevation caching.
PATTERN_HASH = "default"
# The fileset hash is the hash of this set of files, which is used for DataValues caching
FILESET_HASH = "default"

COMBINED_HASH_LOOKUP = {}   # hash -> original JSON string, for combined_*_hash attrs

# Populated by analyze.py at startup; used by calculations.py for pickle metadata
RUN_METADATA = {}

def get_git_hash():
    """Return the short git commit hash, or 'unknown' if not in a git repo."""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return 'unknown'

GRAPH_MAX_LINES = 30
PRINT_MAX_LINES = 100000

def get_analysis_hash_path(hash):
    return os.path.join(ANALYSIS_FOLDER, hash)

# Output channel handles — set by analyze.py at startup, after the Tee is wired up.
run_log  = None   # CleanStream → run.log only (not terminal)
terminal = None   # sys.__stderr__ — raw TTY only (not run.log)

# Single background thread drains this queue and writes to run_log.
# Workers call log() which only does a queue.put() — they never touch run_log
# directly and never wait on file I/O.  Because exactly one thread writes to
# run_log, CleanStream._buf needs no locking.
_log_queue  = queue.SimpleQueue()
_log_thread = None


def _log_worker():
    while True:
        msg = _log_queue.get()
        if msg is None:          # sentinel — time to exit
            break
        run_log.write(msg)


def start_log_thread():
    """Start the background log-writer thread.  Call once, after run_log is set."""
    global _log_thread
    _log_thread = threading.Thread(target=_log_worker, daemon=True, name='log-writer')
    _log_thread.start()
    atexit.register(stop_log_thread)


def stop_log_thread():
    """Drain remaining messages and shut down the writer thread."""
    global _log_thread
    if _log_thread is None or not _log_thread.is_alive():
        return
    _log_queue.put(None)   # sentinel
    _log_thread.join()
    _log_thread = None


def log(*args, **kwargs):
    """Write to run.log only — not the terminal.

    Formats the message in the calling thread then hands a pre-built string to
    the background writer thread via a queue.  Returns immediately; callers
    (including worker threads) never wait on file I/O.
    """
    if run_log is None:
        return
    buf = io.StringIO()
    print(*args, file=buf, **kwargs)
    _log_queue.put(buf.getvalue())


def log_and_print(*args, **kwargs):
    """Write to run.log AND the real terminal atomically.

    Formats once, prints to the real terminal (bypassing Tee to avoid
    double-writing to run.log), then queues for run.log via the log thread.
    """
    buf = io.StringIO()
    print(*args, file=buf, **kwargs)
    msg = buf.getvalue()
    # Write to real terminal, not Tee'd sys.stdout (which would also write to run.log)
    _out = terminal if terminal is not None else sys.__stdout__
    try:
        _out.write(msg)
        _out.flush()
    except (ValueError, OSError):
        pass
    if run_log is not None:
        _log_queue.put(msg)


def write_file(filename, *args, **kwargs):
    """Append to OUTPUT_FOLDER/filename only — not terminal, not run.log."""
    log_path = os.path.join(OUTPUT_FOLDER, filename)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a', buffering=1) as f:
        print(*args, file=f, **kwargs)


def log_and_file(filename, *args, **kwargs):
    """Write to run.log AND OUTPUT_FOLDER/filename — not terminal."""
    log(*args, **kwargs)
    write_file(filename, *args, **kwargs)

import re, atexit

class CleanStream:
    """
    Clean tqdm-style output for logs:
      - Strip ANSI escapes
      - Treat '\r' as 'overwrite this line'
      - Only emit lines when a '\n' arrives (or at close()).
    """
    _ansi_re = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

    def __init__(self, stream, keep_last_line=True):
        self.stream = stream
        self.keep_last_line = keep_last_line
        self._buf = []  # chars of current line
        atexit.register(self.close)

    def write(self, data):
        # coerce to text and strip ANSI
        s = data.decode(errors="replace") if isinstance(data, (bytes, bytearray)) else str(data)
        s = self._ansi_re.sub("", s)

        for ch in s:
            if ch == '\r':
                # overwrite current line: discard buffered chars
                self._buf.clear()
            elif ch == '\n':
                # complete line -> write it once
                self.stream.write(''.join(self._buf) + '\n')
                self._buf.clear()
            else:
                self._buf.append(ch)
        return len(data)

    def flush(self):
        # IMPORTANT: do NOT write the partial buffer here
        self.stream.flush()

    def close(self):
        try:
            if self.keep_last_line and self._buf:
                # emit the final in-progress bar once at shutdown
                self.stream.write(''.join(self._buf) + '\n')
                self._buf.clear()
            self.stream.flush()
        except ValueError:
            pass  # underlying stream already closed



class Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
        for s in self.streams:
            s.flush()
    def flush(self):
        for s in self.streams:
            s.flush()
    def isatty(self):
        return any(hasattr(s, 'isatty') and s.isatty() for s in self.streams)