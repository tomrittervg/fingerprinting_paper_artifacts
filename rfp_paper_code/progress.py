"""Partition progress display for analyze.py (free-threaded / no-GIL Python).

Design:
- One PartitionProgress slot per partition, pre-allocated before the executor
  starts. The list never changes size, so the render thread can iterate it
  without any lock.
- Workers call slot._start() when they begin and slot.finish() (via
  release_slot) when done. Between those two calls they write slot fields
  freely. Stale or torn reads by the render thread produce at most one
  incorrect render frame (~100 ms) and never cause crashes.
- self.completed is written only by the main thread (single writer), so it
  needs no lock.
- No semaphore, no claim lock, no slot reuse. Simple.
"""

import shutil
import threading
import time


class _DummySlot:
    """No-op slot used when the display is disabled (non-TTY output)."""
    def _start(self, *a, **kw): pass
    def advance_phase(self, *a, **kw): pass
    def rename_phase(self, name): pass
    def update_progress(self, done): pass
    def finish(self): pass


_DUMMY = _DummySlot()


class PartitionProgress:
    """Per-partition progress state.

    Written by exactly one worker thread; read by the render thread.
    __slots__ keeps attribute access fast on the hot update_progress() path.
    """
    __slots__ = ('active', 'label', 'phase_num', 'total_phases',
                 'phase_name', 'phase_done', 'phase_total', 'rss_mb')

    def __init__(self):
        self.active       = False
        self.label        = ''
        self.phase_num    = 0
        self.total_phases = 1
        self.phase_name   = ''
        self.phase_done   = 0
        self.phase_total  = 0
        self.rss_mb       = 0

    def _start(self, label, total_phases):
        # Write descriptive fields before flipping active=True so the render
        # thread either sees the fully-initialised state or skips the slot.
        self.label        = label
        self.total_phases = total_phases
        self.phase_num    = 0
        self.phase_name   = 'Starting'
        self.phase_done   = 0
        self.phase_total  = 0
        self.active       = True   # last write

    def advance_phase(self, name, total_items=0):
        """Call at the start of each processing phase."""
        self.phase_name   = name
        self.phase_done   = 0
        self.phase_total  = total_items
        self.phase_num   += 1   # single writer; += is safe

    def rename_phase(self, name):
        """Update the display name of the current phase without advancing the counter."""
        self.phase_name = name

    def update_progress(self, done):
        """Hot-path: called from inner loops. Lock-free; stale reads are fine."""
        self.phase_done = done

    def finish(self):
        """Deactivate slot. Render thread may show it for one more tick."""
        self.active = False
        self.rss_mb = 0


class ProgressDisplay:
    """Multi-line in-place progress display written to a TTY.

    One PartitionProgress slot is allocated per partition up-front. The render
    thread iterates self.slots and skips inactive entries — fast even for
    width=2 (512 partitions).
    """

    def __init__(self, tty, total_partitions, enabled=None):
        self.tty              = tty
        self.enabled          = (hasattr(tty, 'isatty') and tty.isatty()) if enabled is None else enabled
        self.total_partitions = total_partitions
        self.completed        = 0   # written only by main thread
        self.start_time       = time.time()
        # One slot per partition; all start inactive.
        self.slots            = [PartitionProgress() for _ in range(total_partitions)]
        self._lines_written   = 0
        self._stop            = threading.Event()
        self._thread          = threading.Thread(
            target=self._render_loop, daemon=True, name='progress-render'
        )

    def start(self):
        if self.enabled:
            self._thread.start()

    def stop(self):
        """Stop the render thread and clear the display from the terminal. Safe to call multiple times."""
        if self.enabled and not self._stop.is_set():
            self._stop.set()
            self._thread.join()
            self._erase()

    def release_slot(self, slot):
        """Deactivate a slot and increment the overall completed count.

        Called only from the main thread (inside the as_completed loop) —
        single writer, so self.completed needs no lock.
        """
        if not self.enabled or slot is _DUMMY:
            return
        slot.finish()
        self.completed += 1   # single writer (main thread)

    # ── Render internals ──────────────────────────────────────────────────

    def _erase(self):
        n = self._lines_written
        if n == 0:
            return
        # Move cursor up n lines then erase from cursor to end of screen.
        # Using \033[J handles shrinking frames cleanly.
        self.tty.write(f'\033[{n}A\033[J')
        self.tty.flush()
        self._lines_written = 0

    @staticmethod
    def _solid_bar(pct, width):
        filled = int(width * pct)
        return '\u2588' * filled + '\u2591' * (width - filled)

    @staticmethod
    def _pulse_bar(width):
        """Pulsing indicator for phases whose total item count is unknown."""
        pos = int(time.time() * 6) % max(1, width)
        buf = ['\u2591'] * width
        for d in (-1, 0, 1):
            p = pos + d
            if 0 <= p < width:
                buf[p] = '\u2592'
        return ''.join(buf)

    def _render_loop(self):
        while not self._stop.is_set():
            self._render()
            time.sleep(0.1)

    def _render(self):
        cols = shutil.get_terminal_size(fallback=(120, 24)).columns
        lines = []

        # ── Overall partition bar ──────────────────────────────────────
        done    = self.completed
        total   = self.total_partitions
        elapsed = time.time() - self.start_time
        rate    = done / elapsed if elapsed > 0 and done > 0 else 0
        eta     = (total - done) / rate if rate > 0 else 0
        pct     = done / total if total else 0.0
        prefix  = f'Partitions: {done}/{total} '
        def _hms(s):
            h, r = divmod(int(s), 3600)
            m, s = divmod(r, 60)
            return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'
        suffix  = f' {_hms(elapsed)}<{_hms(eta)}'
        bw      = max(10, cols - len(prefix) - len(suffix) - 2)
        lines.append(f'{prefix}|{self._solid_bar(pct, bw)}|{suffix}')

        # ── Per-slot lines (only active slots) ────────────────────────
        # Pre-compute max label width for alignment
        active_slots = [(s, s.label) for s in self.slots if s.active]
        label_width = max((len(lbl) for _, lbl in active_slots), default=8)
        label_width = max(label_width, 8)

        for slot, label in active_slots:
            # Read all fields in one burst. Render thread may see slightly
            # stale values but will never crash (all simple Python objects).
            phase_num   = slot.phase_num
            total_ph    = slot.total_phases
            phase_name  = slot.phase_name
            phase_done  = slot.phase_done
            phase_total = slot.phase_total

            tag = f'Phase {phase_num}/{total_ph}: {phase_name:<12}'

            if phase_total > 0:
                p         = min(1.0, phase_done / phase_total)
                pct_str   = f'{p * 100:3.0f}%'
                use_solid = True
            else:
                p         = 0.0
                pct_str   = '   ?'
                use_solid = False

            left  = f'  {label:<{label_width}} {tag} '
            right = f' {pct_str}'
            bw    = max(4, cols - len(left) - len(right) - 2)
            bar_str = self._solid_bar(p, bw) if use_solid else self._pulse_bar(bw)
            lines.append(f'{left}|{bar_str}|{right}')

        # ── Memory summary line ────────────────────────────────────────
        try:
            import os as _os
            main_pid = _os.getpid()
            main_rss_mb = 0
            with open(f'/proc/{main_pid}/status') as f:
                for raw_line in f:
                    if raw_line.startswith('VmRSS:'):
                        main_rss_mb = int(raw_line.split()[1]) // 1024
                        break
            # Sum RSS of all descendant processes (forkserver workers are grandchildren)
            children_rss_mb = 0
            n_children = 0
            # Build pid → ppid map, then find all descendants of main_pid
            pid_ppid = {}
            pid_rss = {}
            for entry in _os.listdir('/proc'):
                if not entry.isdigit():
                    continue
                pid = int(entry)
                try:
                    with open(f'/proc/{entry}/stat') as f:
                        stat = f.read()
                    ppid = int(stat.split(') ', 1)[1].split()[1])
                    pid_ppid[pid] = ppid
                    with open(f'/proc/{entry}/status') as f:
                        for raw_line in f:
                            if raw_line.startswith('VmRSS:'):
                                pid_rss[pid] = int(raw_line.split()[1]) // 1024
                                break
                except (OSError, ValueError, IndexError):
                    continue
            # BFS to find all descendants
            descendants = set()
            frontier = {main_pid}
            while frontier:
                next_frontier = set()
                for pid, ppid in pid_ppid.items():
                    if ppid in frontier and pid not in descendants and pid != main_pid:
                        descendants.add(pid)
                        next_frontier.add(pid)
                frontier = next_frontier
            for pid in descendants:
                if pid in pid_rss:
                    children_rss_mb += pid_rss[pid]
                    n_children += 1
        except Exception:
            main_rss_mb = 0
            children_rss_mb = 0
            n_children = 0
        if main_rss_mb > 0 or children_rss_mb > 0:
            try:
                with open('/proc/meminfo') as f:
                    mi = {}
                    for raw_line in f:
                        parts = raw_line.split()
                        if len(parts) >= 2:
                            mi[parts[0].rstrip(':')] = int(parts[1])  # kB
                    total_gb = mi.get('MemTotal', 0) / 1048576
                    avail_gb = mi.get('MemAvailable', 0) / 1048576
                free_gb = mi.get('MemFree', 0) / 1048576
                bufcache_gb = (mi.get('Buffers', 0) + mi.get('Cached', 0)) / 1048576
                used_gb = total_gb - free_gb - bufcache_gb
                lines.append(
                    f'  Mem: main {main_rss_mb / 1024:.1f}  {n_children} workers {children_rss_mb / 1024:.1f}  |  '
                    f'used {used_gb:.1f}  cache {bufcache_gb:.1f}  avail {avail_gb:.1f}  / {total_gb:.0f} GB'
                )
            except OSError:
                lines.append(
                    f'  Mem: main {main_rss_mb / 1024:.1f}  {n_children} workers {children_rss_mb / 1024:.1f} GB'
                )

        self._erase()
        for line in lines:
            self.tty.write(line[:cols] + '\n')
        self._lines_written = len(lines)
        self.tty.flush()
