import os
import fnmatch
import pickle
import re
import json
import shutil
import time
import threading
from datetime import date, timedelta
from collections import defaultdict

import glob as _glob_mod
import config
import hashlib
import base64
import experiments as _experiments_module  # noqa: F401 — needed for pickle to resolve filter classes in range cache

def defaultdict_int():
    return defaultdict(int)

def defaultdict_defaultdict_int():
    return defaultdict(defaultdict_int)

def pickle_data(data, filename, hash, override_dir=None, quiet=False):
    pickled_data = pickle.dumps(data)

    if override_dir:
      file_path = os.path.join(override_dir, filename)
    else:
      file_path = os.path.join(config.get_analysis_hash_path(hash), filename)

    with open(file_path, "wb") as file:
        file.write(pickled_data)

    if not quiet:
        print(f"  Wrote {len(pickled_data)/ (1024 * 1024)} megabytes to {file_path}")
    return len(pickled_data)


def unpickle_data(filename, hash):
    file_path = os.path.join(config.get_analysis_hash_path(hash), filename)
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    return data

def unpickle_from_dir(filename, directory):
    """Load a pickled object from an explicit directory path."""
    file_path = os.path.join(directory, filename)
    with open(file_path, "rb") as f:
        return pickle.load(f)

def pickle_to_dir(data, filename, directory, quiet=False):
    """Save a pickled object to an explicit directory path. Returns bytes written.
    Always writes the file, even for empty data (unlike pickle_data)."""
    os.makedirs(directory, exist_ok=True)
    pickled_data = pickle.dumps(data)
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        f.write(pickled_data)
    if not quiet:
        print(f"  Wrote {len(pickled_data) / (1024 * 1024):.2f} MB to {file_path}")
    return len(pickled_data)


def dedup_by_client(raw_rows):
    """In-place dedup: keep only the latest submission per client_identifier.
    Modifies raw_rows in place and returns it (now shorter).

    Fast path: if all client IDs are unique (the common case), just verify
    with a set and return immediately — no dict of indices or compaction needed.
    """
    cids = {row['metrics']['uuid']['characteristics_client_identifier'] for row in raw_rows}
    if len(cids) == len(raw_rows):
        return raw_rows
    # Slow path: duplicates exist, keep latest per client
    best = {}  # cid -> index of winning row
    for i, row in enumerate(raw_rows):
        cid = row['metrics']['uuid']['characteristics_client_identifier']
        ts = row['submission_timestamp']
        if cid not in best or ts > raw_rows[best[cid]]['submission_timestamp']:
            best[cid] = i
    keep = sorted(best.values())
    for dst, src in enumerate(keep):
        raw_rows[dst] = raw_rows[src]
    del raw_rows[len(keep):]
    return raw_rows


def split_rows_by_day_and_prefix(raw_rows, prefix_width):
    """Bucket raw rows by (submission_date, uuid_prefix).
    For prefix_width=0, all rows share the 'all' prefix.
    Returns dict[(date, prefix_str), list[dict]]."""
    buckets = defaultdict(list)
    for row in raw_rows:
        day = row['submission_timestamp'].date() if hasattr(row['submission_timestamp'], 'date') else row['submission_timestamp']
        if prefix_width == 0:
            prefix = 'all'
        else:
            prefix = row['metrics']['uuid']['characteristics_client_identifier'][:prefix_width]
        buckets[(day, prefix)].append(row)
    return buckets


def compute_query_ranges(missing_days):
    """Split missing days into contiguous blocks and return a list of
    (start_date, end_date_exclusive) tuples, one per block.
    Returns an empty list if missing_days is empty."""
    if not missing_days:
        return []
    missing_sorted = sorted(missing_days)
    ranges = []
    block_start = missing_sorted[0]
    block_end = missing_sorted[0]
    for day in missing_sorted[1:]:
        if day - block_end == timedelta(days=1):
            block_end = day
        else:
            ranges.append((block_start, block_end + timedelta(days=1)))
            block_start = day
            block_end = day
    ranges.append((block_start, block_end + timedelta(days=1)))
    return ranges


def compute_query_range(missing_days):
    """Compute the (start_date, end_date_exclusive) for a single coalesced query.
    Asserts that missing days are contiguous (no gaps in the middle).
    Returns None if missing_days is empty."""
    if not missing_days:
        return None
    missing_sorted = sorted(missing_days)
    for i in range(1, len(missing_sorted)):
        assert missing_sorted[i] - missing_sorted[i - 1] == timedelta(days=1), \
            f"Missing days have a gap: {missing_sorted[i - 1]} -> {missing_sorted[i]}"
    return (missing_sorted[0], missing_sorted[-1] + timedelta(days=1))


class DayPartitionCache:
    """Manages per-day/per-prefix raw row cache and per-range DV cache for a single partition."""

    def __init__(self, partition, tiny_mode, minimize, no_cache, rebuild_cache,
                 prefix_width, schema="30"):
        self.partition = partition
        self.tiny_mode = tiny_mode
        self.minimize = minimize
        self.no_cache = no_cache
        self.rebuild_cache = rebuild_cache
        self.prefix_width = prefix_width

        self.schema = schema
        self.partition_hash = get_hash([partition])
        self.partition_dir = config.get_analysis_hash_path(self.partition_hash)

        # UUID prefix list: ['all'] for width=0, ['0'..'f'] for width=1, ['00'..'ff'] for width=2
        if prefix_width == 0:
            self.uuid_prefixes = ['all']
        else:
            n = 16 ** prefix_width
            self.uuid_prefixes = [f"{i:0{prefix_width}x}" for i in range(n)]

        # Filename suffixes for tiny mode
        self._raw_suffix = "_tiny" if tiny_mode else ""
        self._complete_marker = ".complete_tiny" if tiny_mode else ".complete"

        # DV cache filename
        if minimize and tiny_mode:
            self._dv_filename = "all_data_values_tiny_min.bin"
        elif tiny_mode:
            self._dv_filename = "all_data_values_tiny.bin"
        elif minimize:
            self._dv_filename = "all_data_values_min.bin"
        else:
            self._dv_filename = "all_data_values.bin"
        self._stats_filename = self._dv_filename.replace("all_data_values", "parse_stats")

    def day_dir(self, day):
        """Path to the day directory: .../partition_hash/days/schema{N}/YYYY-MM-DD/"""
        return os.path.join(self.partition_dir, "days", f"schema{self.schema}", str(day))

    def range_dir(self, start_day, end_day):
        """Path to the range directory: .../partition_hash/ranges/schema{N}/{range_hash}/"""
        range_hash = get_hash([str(start_day), str(end_day)])
        return os.path.join(self.partition_dir, "ranges", f"schema{self.schema}", range_hash)

    def _read_marker_count(self, day):
        """Read the row count stored in the .complete marker file.
        Returns the count as an int, or None if the marker is empty or missing."""
        marker = os.path.join(self.day_dir(day), self._complete_marker)
        try:
            with open(marker, "r") as f:
                content = f.read().strip()
            if content:
                return int(content)
        except (FileNotFoundError, ValueError):
            pass
        return None

    def _count_cached_rows(self, day):
        """Count total rows stored in the day cache.
        Falls back to reading prefix files if marker has no count,
        and backfills the marker so we don't have to do it again.
        Only reads the partition's own prefix file rather than all 16^width files."""
        marker_count = self._read_marker_count(day)
        if marker_count is not None:
            return marker_count
        # No count in marker — read prefix files to count
        _, dataset = self.partition
        if dataset is not None and dataset in self.uuid_prefixes:
            # Only this partition's prefix will have data
            total = len(self.load_day_prefix(day, dataset))
        else:
            # Width=0 or unexpected: sum all prefixes
            total = 0
            for prefix in self.uuid_prefixes:
                total += len(self.load_day_prefix(day, prefix))
        # Backfill the marker with the count
        marker = os.path.join(self.day_dir(day), self._complete_marker)
        try:
            with open(marker, "w") as f:
                f.write(str(total))
        except OSError:
            pass
        return total

    def _validate_day_cache_count(self, day, bq_counts):
        """Validate the cached row count against a pre-fetched BQ count.
        Returns True if the cache is stale (count mismatch), False if valid.
        If the marker has no stored count (old-format empty marker), unpickles
        all prefix files, counts rows, writes the count to the marker, then validates.
        bq_counts is a dict {(platform, prefix, day_str): count}."""
        cached_count = self._count_cached_rows(day)
        platform, dataset = self.partition
        bq_count = bq_counts.get((platform, dataset, str(day)), 0)
        if cached_count != bq_count:
            config.log(f"  cache count mismatch for {day}: cached={cached_count}, BQ={bq_count}")
            return True
        return False

    def classify_days(self, days, bq_counts=None):
        """Split days into (cached_days, missing_days).
        If bq_counts is provided, validates every cached day's row count against BQ.
        If bq_counts is None (e.g. tiny mode), trusts the cache based on marker presence only."""
        if self.no_cache or self.rebuild_cache:
            return [], list(days)
        cached = []
        missing = []
        count_check_days = []
        for day in days:
            marker = os.path.join(self.day_dir(day), self._complete_marker)
            if not os.path.exists(marker):
                missing.append(day)
            elif bq_counts is not None:
                count_check_days.append(day)
            else:
                cached.append(day)

        if count_check_days:
            config.log(f"  validating {len(count_check_days)} cached day(s) against BQ row counts...")
            for day in count_check_days:
                if self._validate_day_cache_count(day, bq_counts):
                    missing.append(day)
                else:
                    cached.append(day)

        return cached, missing

    def has_range_dv_cache(self, start_day, end_day):
        """Check if DV cache file exists in range_dir."""
        if self.no_cache or self.rebuild_cache:
            return False
        rd = self.range_dir(start_day, end_day)
        dv_path = os.path.join(rd, self._dv_filename)
        return os.path.exists(dv_path)

    def load_range_dv(self, start_day, end_day):
        """Unpickle DataValues and stats from range_dir. Returns (data_values, stats).

        Supports both the chunked format (DVCHUNK1 header + sequential chunks)
        and the legacy monolithic format (single pickled list).
        """
        rd = self.range_dir(start_day, end_day)
        path = os.path.join(rd, self._dv_filename)
        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        with open(path, "rb") as f:
            first_obj = pickle.load(f)
            if isinstance(first_obj, dict) and first_obj.get("magic") == self._RANGE_MAGIC:
                # Chunked format: materialize all chunks into a single list
                hdr = first_obj
                config.log(f"  range cache: chunked v{hdr['version']}, "
                           f"{hdr['chunk_count']} chunks, {hdr['total_count']} users, "
                           f"{file_size_mb:.0f} MB")
                data_values = []
                for i in range(hdr["chunk_count"]):
                    data_values.extend(pickle.load(f))
            else:
                # Legacy monolithic format: first_obj is the full list
                config.log(f"  range cache: legacy format, {len(first_obj)} users, "
                           f"{file_size_mb:.0f} MB")
                data_values = first_obj
        try:
            stats = unpickle_from_dir(self._stats_filename, rd)
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            num_users = len(data_values)
            stats = {
                'skipped': 0, 'included': num_users,
                'expected_errors': {}, 'unexpected_errors': '',
                'parse_time': 0, 'filter_time': 0,
            }

        # Restore combined hash lookup: check range cache dir first, then cache root
        if not config.COMBINED_HASH_LOOKUP:
            import json as _json
            for _lp in [os.path.join(rd, "combined_hash_lookup.json"),
                        os.path.join(config.ANALYSIS_FOLDER, "combined_hash_lookup.json")]:
                if os.path.exists(_lp):
                    with open(_lp, "r") as lf:
                        config.COMBINED_HASH_LOOKUP.update(_json.load(lf))
                    break

        return data_values, stats

    def iter_range_dv_chunks(self, start_day, end_day):
        """Yield DataValues in chunks without full materialization.

        Returns (total_count, stats, chunk_iterator) where chunk_iterator
        yields list[DataValues]. For the legacy format, yields the full list
        as a single chunk.
        """
        rd = self.range_dir(start_day, end_day)
        path = os.path.join(rd, self._dv_filename)

        try:
            stats = unpickle_from_dir(self._stats_filename, rd)
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            stats = {
                'skipped': 0, 'included': 0,
                'expected_errors': {}, 'unexpected_errors': '',
                'parse_time': 0, 'filter_time': 0,
            }

        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        f = open(path, "rb")
        first_obj = pickle.load(f)
        if isinstance(first_obj, dict) and first_obj.get("magic") == self._RANGE_MAGIC:
            hdr = first_obj
            config.log(f"  range cache (streaming): chunked v{hdr['version']}, "
                       f"{hdr['chunk_count']} chunks, {hdr['total_count']} users, "
                       f"{file_size_mb:.0f} MB")
            total_count = hdr["total_count"]
            chunk_count = hdr["chunk_count"]
            def _iter():
                try:
                    for _ in range(chunk_count):
                        yield pickle.load(f)
                finally:
                    f.close()
            return total_count, stats, _iter()
        else:
            config.log(f"  range cache (streaming): legacy format, {len(first_obj)} users, "
                       f"{file_size_mb:.0f} MB")
            f.close()
            return len(first_obj), stats, iter([first_obj])

    _RANGE_CHUNK_SIZE = 2000
    _RANGE_MAGIC = "DVCHUNK1"

    def save_range_dv(self, start_day, end_day, data_values, stats):
        """Pickle DataValues and stats to range_dir in chunked format.

        Returns total bytes written. Also writes a .count marker with
        len(data_values) for validation on load.
        """
        if self.no_cache:
            return 0
        rd = self.range_dir(start_day, end_day)
        os.makedirs(rd, exist_ok=True)

        cs = self._RANGE_CHUNK_SIZE
        n_chunks = (len(data_values) + cs - 1) // cs if data_values else 0
        header = {
            "magic": self._RANGE_MAGIC,
            "version": 1,
            "chunk_count": n_chunks,
            "total_count": len(data_values),
            "chunk_size": cs,
        }

        path = os.path.join(rd, self._dv_filename)
        tmp_path = path + ".tmp"
        with open(tmp_path, "wb") as f:
            pickle.dump(header, f, protocol=pickle.HIGHEST_PROTOCOL)
            for i in range(0, len(data_values), cs):
                pickle.dump(data_values[i:i + cs], f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp_path, path)
        bytes_written = os.path.getsize(path)

        pickle_to_dir(stats, self._stats_filename, rd, quiet=True)
        # Write count marker for range cache validation
        count_path = os.path.join(rd, self._dv_filename + ".count")
        with open(count_path, "w") as f:
            f.write(str(len(data_values)))

        # Save combined hash lookup alongside range cache
        if config.COMBINED_HASH_LOOKUP:
            import json as _json
            lookup_path = os.path.join(rd, "combined_hash_lookup.json")
            with open(lookup_path, "w") as f:
                _json.dump(config.COMBINED_HASH_LOOKUP, f)

        return bytes_written

    def load_day_prefix(self, day, uuid_prefix):
        """Unpickle raw rows for a specific day and uuid prefix.
        Returns [] if the file doesn't exist (empty day)."""
        dd = self.day_dir(day)
        filename = f"raw_rows_{uuid_prefix}{self._raw_suffix}.bin"
        try:
            return unpickle_from_dir(filename, dd)
        except FileNotFoundError:
            return []

    def _clean_day_dir(self, day):
        """Remove existing day directory to clear stale files from previous runs."""
        import shutil
        dd = self.day_dir(day)
        if os.path.exists(dd):
            shutil.rmtree(dd)

    def save_empty_day(self, day):
        """Mark a day as cached without writing any prefix files."""
        if self.no_cache:
            return
        if date.fromisoformat(str(day)) > date.today():
            return
        self._clean_day_dir(day)
        dd = self.day_dir(day)
        os.makedirs(dd, exist_ok=True)
        marker_path = os.path.join(dd, self._complete_marker)
        with open(marker_path, "w") as f:
            f.write("0")

    def save_day_rows(self, day, rows_by_prefix):
        """Save raw rows for a day, split by uuid prefix.
        Writes one file per prefix, then writes .complete marker.
        Returns total bytes written."""
        if self.no_cache:
            return 0
        if date.fromisoformat(str(day)) > date.today():
            return 0
        self._clean_day_dir(day)
        dd = self.day_dir(day)
        os.makedirs(dd, exist_ok=True)
        total_bytes = 0
        total_rows = 0
        for prefix in self.uuid_prefixes:
            rows = rows_by_prefix.get(prefix, [])
            total_rows += len(rows)
            if rows:  # skip writing empty files; reader returns [] on FileNotFoundError
                filename = f"raw_rows_{prefix}{self._raw_suffix}.bin"
                total_bytes += pickle_to_dir(rows, filename, dd, quiet=True)
        # Write completeness marker with row count
        marker_path = os.path.join(dd, self._complete_marker)
        with open(marker_path, "w") as f:
            f.write(str(total_rows))
        return total_bytes


def _bq_query_removed(*args, **kwargs):
    raise NotImplementedError("BigQuery query functions removed — run from cache only")

query_bq_day_counts = _bq_query_removed
query_bq_filtered_counts = _bq_query_removed
query_single_partition = _bq_query_removed


def get_database_partitions(platforms, patterns, width=2):
  """
  Yields (platform, hex_partition) tuples for each platform and partition
  matching the given glob patterns. width=0 means no partitioning (yields (platform, None)).
  """
  if width == 0:
    for platform in platforms:
      yield (platform, None)
    return
  n = 16 ** width
  for pattern in patterns:
    for platform in platforms:
      for i in range(n):
        part = f"{i:0{width}x}"
        if fnmatch.fnmatch(part, pattern):
          yield (platform, part)

def get_hash(items):
    """64-bit base64-encoded hash of a sorted list of items."""
    key = "\n".join(sorted(str(s) for s in items)).encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(key).digest()[:8]).decode("ascii")



def load_partition_data(partition, all_days, start_day, end_day,
                        tiny_mode, no_cache, rebuild_cache,
                        minimize,
                        partition_width, raw_rows_only=False,
                        quiet=False, source_cb=None, schema="30",
                        bq_counts=None,
                        bq_filtered_counts=None,
                        n_filter_threads=1):
  """Load data for a single partition using per-day/per-prefix caching.
  Returns (data_values, num_users, num_users_by_os, stats).

  If bq_counts is provided (from query_bq_day_counts), non-recent cached days
  are validated against BQ row counts. Pass None to skip validation.

  If bq_filtered_counts is provided (from query_bq_filtered_counts), the range
  cache is validated against the expected post-validation row count."""
  from datavalues import parse_datavalues, Struct
  from filters import webGLParamMetricFilter, minimizeMemoryFilter

  cache = DayPartitionCache(
      partition, tiny_mode, minimize, no_cache, rebuild_cache,
      partition_width, schema)
  os.makedirs(cache.partition_dir, exist_ok=True)

  part_label = f"{partition[0]}/{partition[1]}" if partition[1] else partition[0]
  config.log(f"\n[{part_label}] loading {all_days[0]}..{all_days[-1]} ({len(all_days)} day{'s' if len(all_days) != 1 else ''})")

  cache_bytes_written = 0

  # ---- Try DV range cache (skip if raw_rows_only) ----
  _range_cache_ok = False
  if not raw_rows_only and cache.has_range_dv_cache(start_day, end_day):
    if source_cb: source_cb('cache')
    dv_path = os.path.join(cache.range_dir(start_day, end_day), cache._dv_filename)
    config.log(f"[{part_label}]   range cache hit: {dv_path}")
    _t0_range_load = time.time()
    try:
      data_values, stats = cache.load_range_dv(start_day, end_day)
      num_users = len(data_values)
      _range_cache_ok = True
    except Exception as e:
      config.log(f"[{part_label}]   RANGE CACHE CORRUPT: {type(e).__name__}: {e}")
      config.log(f"[{part_label}]   path: {dv_path}")
      config.log(f"[{part_label}]   deleting corrupt cache and rebuilding from day caches")
      import shutil
      shutil.rmtree(cache.range_dir(start_day, end_day), ignore_errors=True)
    _range_load_time = time.time() - _t0_range_load

  if _range_cache_ok:
    # Validate range cache against filtered BQ count
    range_valid = True
    if bq_filtered_counts is not None:
      platform, dataset = partition
      expected = bq_filtered_counts.get((platform, dataset), 0)
      if num_users != expected:
        config.log(f"[{part_label}]   range cache count mismatch: loaded={num_users}, expected={expected}")
        range_valid = False
      else:
        config.log(f"[{part_label}]   range cache validated: {num_users} rows match BQ")

    if range_valid:
      num_users_by_os = defaultdict(int)
      for dv in data_values:
        num_users_by_os[dv.os] += 1
      config.log(f"[{part_label}]   loaded {num_users} users from range cache  [unpickle {_range_load_time:.2f}s]")
      stats['source'] = 'range_cache'
      stats['cached_days'] = len(all_days)
      stats['queried_days'] = 0
      stats['cache_bytes_written'] = 0
      stats['unpickle_time'] = _range_load_time
      # Zero out build-time stats so the load breakdown reflects actual work this run
      for _k in ('prefilter_time', 'dedup_time', 'parse_time', 'filter_time', 'range_save_time'):
          stats[_k] = 0
      return data_values, num_users, num_users_by_os, stats
    else:
      # ---- Incremental range cache update ----
      # Range cache exists but is stale. Try to update incrementally by
      # loading only the changed days instead of rebuilding from scratch.
      cached_days, stale_days = cache.classify_days(all_days, bq_counts=bq_counts)

      if stale_days:
        if source_cb: source_cb('cache')
        config.log(f"[{part_label}]   incremental update: {len(stale_days)} stale day(s), "
                    f"{len(cached_days)} unchanged")

        # Fetch/cache stale days from BQ — includes days with no cache AND
        # days whose day cache row count doesn't match BQ (stale day cache)
        _days_needing_fetch = []
        for d in stale_days:
          marker = os.path.join(cache.day_dir(d), cache._complete_marker)
          if not os.path.exists(marker):
            config.log(f"[{part_label}]     stale day {d}: no day cache, will fetch from BQ")
            _days_needing_fetch.append(d)
          elif bq_counts is not None:
            # Day cache exists but was classified as stale — re-fetch it
            config.log(f"[{part_label}]     stale day {d}: day cache count mismatch, re-fetching from BQ")
            cache._clean_day_dir(d)
            _days_needing_fetch.append(d)
        _missing_no_cache = _days_needing_fetch
        if _missing_no_cache:
          query_ranges = compute_query_ranges(_missing_no_cache)
          # Collect all rows across all query ranges before saving day caches,
          # so that multi-range queries don't clobber each other's results.
          _all_fetched_rows = []
          for q_start, q_end in query_ranges:
            config.log(f"[{part_label}]   BigQuery: table={partition[0]!r} dataset={partition[1]!r} dates=[{q_start}, {q_end})")
            chunk = query_single_partition(tiny_mode, partition, q_start, q_end, schema)
            config.log(f"[{part_label}]   BigQuery returned {len(chunk)} row(s)")
            _all_fetched_rows.extend(chunk)
            del chunk

          if _all_fetched_rows:
            buckets = split_rows_by_day_and_prefix(_all_fetched_rows, partition_width)
            days_with_data = {day for (day, _) in buckets}
            for day in _missing_no_cache:
              if day in days_with_data:
                day_prefix_rows = {p: buckets.get((day, p), []) for p in cache.uuid_prefixes}
                day_bytes = cache.save_day_rows(day, day_prefix_rows)
                cache_bytes_written += day_bytes
              else:
                cache.save_empty_day(day)
            del buckets
          else:
            for day in _missing_no_cache:
              cache.save_empty_day(day)
          del _all_fetched_rows

        # Load and parse only the stale days' raw rows
        _incr_stats = {
            'skipped': 0, 'included': 0,
            'expected_errors': defaultdict(int), 'unexpected_errors': '',
            'unpickle_time': 0, 'prefilter_time': 0, 'dedup_time': 0,
            'parse_time': 0, 'filter_time': 0,
        }
        new_dvs = []
        _stale_days_with_files = [d for d in stale_days
            if _glob_mod.glob(os.path.join(cache.day_dir(d),
                f"raw_rows_*{cache._raw_suffix}.bin"))]

        if _stale_days_with_files:
          config.log(f"[{part_label}]   loading {len(_stale_days_with_files)} stale day(s) from day cache for incremental parse")
          for uuid_prefix in cache.uuid_prefixes:
            _t0 = time.time()
            prefix_rows = []
            for day in _stale_days_with_files:
              prefix_rows.extend(cache.load_day_prefix(day, uuid_prefix))
            _incr_stats['unpickle_time'] += time.time() - _t0
            if not prefix_rows:
              continue

            _t0 = time.time()
            _pre_errors = defaultdict(int)
            _pre_kept = []
            for _r in prefix_rows:
              _s = Struct(**_r)
              if not record_has_errors(_pre_errors, _s):
                _pre_kept.append(_r)
            pre_filter_skipped = len(prefix_rows) - len(_pre_kept)
            prefix_rows[:] = _pre_kept
            del _pre_kept
            _incr_stats['prefilter_time'] += time.time() - _t0

            if not prefix_rows:
              _incr_stats['skipped'] += pre_filter_skipped
              for k, v in _pre_errors.items():
                _incr_stats['expected_errors'][k] += v
              continue

            _t0 = time.time()
            dedup_by_client(prefix_rows)
            _incr_stats['dedup_time'] += time.time() - _t0

            dvs, n_users, n_by_os, _parse_stats = parse_datavalues(
                prefix_rows, quiet=True, n_filter_threads=n_filter_threads)
            _incr_stats['skipped'] += _parse_stats.get('skipped', 0) + pre_filter_skipped
            _incr_stats['included'] += _parse_stats.get('included', 0)
            _incr_stats['parse_time'] += _parse_stats.get('parse_time', 0)
            _incr_stats['filter_time'] += _parse_stats.get('filter_time', 0)
            del prefix_rows

            if minimize:
              for d in dvs:
                d.add_filter(webGLParamMetricFilter)
                d.add_filter(minimizeMemoryFilter)

            new_dvs.extend(dvs)

        # Merge: build client_id -> DV map from old cache, overlay new DVs.
        # Note: if a client existed only in a stale day and that day's data shrank,
        # the old DV persists. This is acceptable — BQ data is append-only in practice.
        _t0_merge = time.time()
        dv_by_client = {dv.client_id: dv for dv in data_values}
        for dv in new_dvs:
          existing = dv_by_client.get(dv.client_id)
          if existing is None or dv.submission_date >= existing.submission_date:
            dv_by_client[dv.client_id] = dv
        del data_values, new_dvs

        all_data_values = list(dv_by_client.values())
        del dv_by_client
        _merge_time = time.time() - _t0_merge

        total_num_users = len(all_data_values)
        total_num_users_by_os = defaultdict(int)
        for dv in all_data_values:
          total_num_users_by_os[dv.os] += 1

        config.log(
            f"[{part_label}]   incremental timing: unpickle={_incr_stats['unpickle_time']:.2f}s"
            f"  prefilter={_incr_stats['prefilter_time']:.2f}s"
            f"  dedup={_incr_stats['dedup_time']:.2f}s"
            f"  parse={_incr_stats['parse_time']:.2f}s"
            f"  filter={_incr_stats['filter_time']:.2f}s"
            f"  merge={_merge_time:.2f}s"
            f"  ({_incr_stats['included']} new rows, {total_num_users} total)")

        agg_stats = {
            'skipped': _incr_stats['skipped'], 'included': total_num_users,
            'expected_errors': dict(_incr_stats['expected_errors']),
            'unexpected_errors': _incr_stats['unexpected_errors'],
            'unpickle_time': _range_load_time + _incr_stats['unpickle_time'],
            'prefilter_time': _incr_stats['prefilter_time'],
            'dedup_time': _incr_stats['dedup_time'],
            'parse_time': _incr_stats['parse_time'],
            'filter_time': _incr_stats['filter_time'],
            'range_save_time': 0,
        }

        # Save updated range cache
        if not no_cache:
          dv_path = os.path.join(cache.range_dir(start_day, end_day), cache._dv_filename)
          _t0 = time.time()
          range_bytes = cache.save_range_dv(start_day, end_day, all_data_values, agg_stats)
          agg_stats['range_save_time'] = time.time() - _t0
          cache_bytes_written += range_bytes
          config.log(f"[{part_label}]   wrote range cache: {dv_path} "
                      f"({range_bytes / (1024*1024):.2f} MB, {total_num_users} users)")

        agg_stats['source'] = 'incremental'
        agg_stats['cached_days'] = len(cached_days)
        agg_stats['queried_days'] = len(stale_days)
        agg_stats['cache_bytes_written'] = cache_bytes_written
        return all_data_values, total_num_users, total_num_users_by_os, agg_stats

      else:
        # No stale days found but count didn't match — shouldn't happen,
        # fall through to full rebuild
        config.log(f"[{part_label}]   no stale days identified but range cache invalid, full rebuild")
        del data_values, stats

  # ---- Full rebuild: no range cache or incremental update not possible ----
  config.log(f"[{part_label}]   full rebuild from day caches")
  cached_days, missing_days = cache.classify_days(all_days, bq_counts=bq_counts)
  if source_cb:
    if not missing_days:
      source_cb('cache')
    elif not cached_days:
      source_cb('db')
    else:
      source_cb('db+cache')

  if cached_days:
    config.log(f"[{part_label}]   {len(cached_days)} day(s) from day cache:")
    for day in sorted(cached_days):
      config.log(f"[{part_label}]     {cache.day_dir(day)}/")
  if missing_days:
    config.log(f"[{part_label}]   {len(missing_days)} day(s) not cached: {', '.join(str(d) for d in sorted(missing_days))}")

  # ---- Query missing days ----
  total_raw_rows = 0
  if missing_days:
    query_ranges = compute_query_ranges(missing_days)
    all_raw_rows = []
    for q_start, q_end in query_ranges:
      config.log(f"[{part_label}]   BigQuery: table={partition[0]!r} dataset={partition[1]!r} dates=[{q_start}, {q_end})")
      chunk = query_single_partition(tiny_mode, partition, q_start, q_end, schema)
      config.log(f"[{part_label}]   BigQuery returned {len(chunk)} row(s)")
      all_raw_rows.extend(chunk)
    raw_rows = all_raw_rows
    total_raw_rows = len(raw_rows)
    if len(query_ranges) > 1:
      config.log(f"[{part_label}]   BigQuery total across {len(query_ranges)} ranges: {total_raw_rows} row(s)")

    if total_raw_rows > 0:
      # Split by (day, uuid_prefix) and cache per day — only days with data
      buckets = split_rows_by_day_and_prefix(raw_rows, partition_width)
      days_with_data = set()
      for (day, prefix) in buckets:
        days_with_data.add(day)
      for day in missing_days:
        if day in days_with_data:
          day_prefix_rows = {}
          for prefix in cache.uuid_prefixes:
            day_prefix_rows[prefix] = buckets.get((day, prefix), [])
          day_bytes = cache.save_day_rows(day, day_prefix_rows)
          cache_bytes_written += day_bytes
          config.log(f"[{part_label}]     wrote day cache: {cache.day_dir(day)}/ ({day_bytes / (1024*1024):.2f} MB)")
        else:
          # Empty day — just write the marker, no prefix files needed
          cache.save_empty_day(day)
          config.log(f"[{part_label}]     empty day {day}: wrote marker only")
      del raw_rows, buckets
    else:
      # No rows at all — mark all missing days as empty
      for day in missing_days:
        cache.save_empty_day(day)
        config.log(f"[{part_label}]     empty day {day}: wrote marker only")
      del raw_rows

  # ---- If raw_rows_only, we're done ----
  if raw_rows_only:
    stats = {
        'skipped': 0, 'included': 0,
        'expected_errors': {}, 'unexpected_errors': '',
        'parse_time': 0, 'filter_time': 0,
        'cache_hit': False, 'cache_bytes_written': cache_bytes_written,
    }
    return [], 0, defaultdict(int), stats

  # ---- Dedup + parse per uuid prefix (full rebuild) ----
  all_data_values = []
  total_num_users = 0
  total_num_users_by_os = defaultdict(int)
  agg_stats = {
      'skipped': 0, 'included': 0,
      'expected_errors': defaultdict(int), 'unexpected_errors': '',
      'unpickle_time': 0, 'prefilter_time': 0, 'dedup_time': 0,
      'parse_time': 0, 'filter_time': 0, 'range_save_time': 0,
  }

  # Figure out which days actually have prefix files on disk (non-empty days)
  days_with_files = []
  for day in all_days:
    # Check if any raw_rows_*.bin file exists (not all prefixes are written)
    dd = cache.day_dir(day)
    if _glob_mod.glob(os.path.join(dd, f"raw_rows_*{cache._raw_suffix}.bin")):
      days_with_files.append(day)

  if days_with_files:
    for uuid_prefix in cache.uuid_prefixes:
      # Load this prefix's raw rows from days that have files
      _t0 = time.time()
      prefix_rows = []
      for day in days_with_files:
        prefix_rows.extend(cache.load_day_prefix(day, uuid_prefix))
      agg_stats['unpickle_time'] += time.time() - _t0

      if not prefix_rows:
        continue

      # Filter out bad rows BEFORE dedup, so the latest *valid* submission
      # per client is kept (matching BQ's WHERE-then-dedup ordering).
      _t0 = time.time()
      _pre_errors = defaultdict(int)
      _pre_kept = []
      for _r in prefix_rows:
        _s = Struct(**_r)
        if not record_has_errors(_pre_errors, _s):
          _pre_kept.append(_r)
      pre_filter_skipped = len(prefix_rows) - len(_pre_kept)
      prefix_rows[:] = _pre_kept
      del _pre_kept
      agg_stats['prefilter_time'] += time.time() - _t0

      if not prefix_rows:
        # All rows in this prefix were bad
        agg_stats['skipped'] += pre_filter_skipped
        for k, v in _pre_errors.items():
          agg_stats['expected_errors'][k] += v
        continue

      # In-place dedup (now among valid rows only)
      _t0 = time.time()
      dedup_by_client(prefix_rows)
      agg_stats['dedup_time'] += time.time() - _t0

      # Parse (record_has_errors already applied, so no rows will be skipped)
      dvs, n_users, n_by_os, stats = parse_datavalues(prefix_rows, quiet=True, n_filter_threads=n_filter_threads)
      stats['skipped'] += pre_filter_skipped
      for k, v in _pre_errors.items():
        stats['expected_errors'][k] = stats.get('expected_errors', {}).get(k, 0) + v
      del prefix_rows

      if minimize:
        for d in dvs:
          d.add_filter(webGLParamMetricFilter)
          d.add_filter(minimizeMemoryFilter)

      all_data_values.extend(dvs)
      total_num_users += n_users
      for k, v in n_by_os.items():
        total_num_users_by_os[k] += v

      # Merge stats
      agg_stats['skipped'] += stats['skipped']
      agg_stats['included'] += stats['included']
      agg_stats['parse_time'] += stats.get('parse_time', 0)
      agg_stats['filter_time'] += stats.get('filter_time', 0)
      agg_stats['unexpected_errors'] += stats.get('unexpected_errors', '')
      for k, v in stats.get('expected_errors', {}).items():
        agg_stats['expected_errors'][k] += v

  if days_with_files:
    t = agg_stats
    config.log(
        f"[{part_label}]   timing: unpickle={t['unpickle_time']:.2f}s  prefilter={t['prefilter_time']:.2f}s"
        f"  dedup={t['dedup_time']:.2f}s  parse={t['parse_time']:.2f}s"
        f"  filter={t['filter_time']:.2f}s  range_save={t['range_save_time']:.2f}s"
    )

  # ---- Save DV range cache ----
  if not no_cache:
    dv_path = os.path.join(cache.range_dir(start_day, end_day), cache._dv_filename)
    _t0 = time.time()
    range_bytes = cache.save_range_dv(start_day, end_day, all_data_values, agg_stats)
    agg_stats['range_save_time'] = time.time() - _t0
    cache_bytes_written += range_bytes
    config.log(f"[{part_label}]   wrote range cache: {dv_path} ({range_bytes / (1024*1024):.2f} MB, {len(all_data_values)} users)")

  if missing_days:
    agg_stats['source'] = 'database' if not cached_days else 'mixed'
  else:
    agg_stats['source'] = 'day_cache'
  agg_stats['cached_days'] = len(cached_days)
  agg_stats['queried_days'] = len(missing_days)
  agg_stats['cache_bytes_written'] = cache_bytes_written
  return all_data_values, total_num_users, total_num_users_by_os, agg_stats


def check_gil_status():
  """Warn if the GIL is enabled, which prevents true CPU parallelism in threads."""
  import sys
  if hasattr(sys, '_is_gil_enabled') and sys._is_gil_enabled():
    print("WARNING: GIL is enabled. A C extension may have re-enabled it.")
    print("  ThreadPoolExecutor will not achieve true CPU parallelism.")
    print("  Run with free-threaded Python and check extension compatibility.")


def write_progress(tty, label, completed, total, start_time):
  """Write a single-line progress bar to tty using \\r overwrite."""
  elapsed = time.time() - start_time
  rate = completed / elapsed if elapsed > 0 and completed > 0 else 0
  eta = (total - completed) / rate if rate > 0 else 0
  pct = completed / total if total else 0
  cols = shutil.get_terminal_size(fallback=(80, 24)).columns
  prefix = f"  {label} {completed}/{total} "
  suffix = f" {elapsed:.0f}s<{eta:.0f}s {rate:.1f}/s"
  bar_width = max(10, cols - len(prefix) - len(suffix) - 2)
  filled = int(bar_width * pct)
  bar = '\u2588' * filled + '\u2591' * (bar_width - filled)
  tty.write(f"\r\033[2K{prefix}|{bar}|{suffix}")
  tty.flush()


def clear_progress(tty):
  """Clear the progress bar line."""
  tty.write("\r\033[2K")
  tty.flush()



"""
To keep our records and code cleaner, we do not check for invalid data in the DataValues class.
(We rely mostly on the schema field to ensure all the data we expect to be there to be present.)
Instead, here, we will put checks
"""

diagnostic_pattern = re.compile(  # (as above)
    r"^\{'message': '\{\}',\s*'diagnostics':\s*\{"
    r"'winCount':\s*\d+,\s*"
    r"'tabCount':\s*\d+,\s*"
    r"'closed':\s*\d+,\s*"
    r"'noActor':\s*\d+,\s*"
    r"'noDebugInfo':\s*\d+,\s*"
    r"'notHW':\s*\d+,\s*"
    r"'remoteTypes':\s*\[(?:'[^']*'(?:,\s*'[^']*')*)\]"
    r"\}\}$"
)

def record_has_errors(expected_errors, obj):
  tz = obj.metrics['string']['characteristics_timezone']
  #try:
  #  zoneinfo.ZoneInfo(tz)
  #except:
  #  expected_errors['bad timezone: ' + tz] += 1
  #  return True

  if obj.metrics['text2']['characteristics_math_ops'] == None:
    expected_errors['None math ops'] += 1
    return True

  try:
    json.loads(obj.metrics['text2']['characteristics_math_ops'])
  except:
    return "Could not parse '%s' as json" % obj.metrics['text2']['characteristics_math_ops']

  if obj.metrics['boolean'] == None:
    return "Missing boolean section"
  if obj.metrics['text2']['characteristics_errors']:
    return f"Found non-js errors on a record:\n{obj.metrics['text2']['characteristics_errors']}"
  if not obj.metrics['text2']['characteristics_screens'] and obj.metrics['quantity']['characteristics_submission_schema'] >= 25:
    # The data is in additional_properties, but it's so few records its not worth writing the code to dig it out of there.
    return "Missing screen data metric"
  if obj.metrics['text2']['characteristics_screens'] == '[]' and obj.metrics['quantity']['characteristics_submission_schema'] >= 25:
    # The data is in additional_properties, but it's so few records its not worth writing the code to dig it out of there.
    return "Missing screen data entirely"
  if obj.metrics['text2']['characteristics_js_errors'] != "[]":
    allowThrough = True
    try:
      js_errors = json.loads(obj.metrics['text2']['characteristics_js_errors'])
    except:
      match = re.search(r'"tabCount":\s*(\d+),', obj.metrics['text2']['characteristics_js_errors'])
      if match:
        tab_count = int(match.group(1))
        if tab_count > 100:
          truncated = obj.metrics['text2']['characteristics_js_errors'][:350] + "..."
          return f"Could not parse the js errors on a record as JSON (truncated):\n{truncated}..."

      return f"Could not parse the js errors on a record as JSON:\n{obj.metrics['text2']['characteristics_js_errors']}"
    for e in js_errors:
      understood = False
      if diagnostic_pattern.match(str(e)):
        understood = True
        expected_errors['diagnostic info'] += 1
      if "Canvas is [object Element] and doesn't have getContext. TagName: canvas" in e:
        understood = True
        expected_errors['canvas doesnt have getContext'] += 1
      if "message" in e and "can't access property \"devicePixelRatio\", this.contentWindow is null" in e["message"]:
        understood = True
        expected_errors['canvas_dpr_null'] += 1
      if "message" in e and "TypeError: this.contentWindow is null render@resource://gre/actors/UserCharacteristicsCanvasRenderingChild.sys.mjs" in e["message"]:
        understood = True
        expected_errors['canvas contentWindow is null'] += 1
      if "populateWindowInfo: Error: TIMEOUT" in e:
        understood = True
        expected_errors['populateWindowTimeout'] += 1
      if "message" in e and "NO_HW_ACTOR" in e['message']:
        understood = True
        expected_errors['NO_HW_ACTOR'] += 1
      if "message" in e and "NO_ACTOR" in e['message']:
        understood = True
        expected_errors['NO_ACTOR'] += 1
      if "Actor 'UserCharacteristicsCanvasRendering' destroyed" in str(e):
        understood = True
        expected_errors['UserCharacteristicsCanvasRendering destroyed'] += 1
      if "tab.linkedBrowser is null" in e:
        understood = True
        expected_errors['tab.linkedBrowser is null'] += 1
      if "tab.linkedBrowser is undefined" in e:
        understood = True
        expected_errors['tab.linkedBrowser is undefined'] += 1
      if "window.navigator.gpu is undefined" in e:
        understood = True
        expected_errors["window.navigator.gpu is undefined"] += 1
      if "tab.linkedBrowser.browsingContext.currentWindowGlobal is null" in e:
        understood = True
        expected_errors['currentWindowGlobal is null'] += 1
      if e == "populateDisabledMediaPrefs: {}":
        understood = True
        expected_errors["empty populateDisabledMediaPrefs error"] += 1
      if e == "populateWebGPUProperties: {}":
        understood = True
        expected_errors["empty populateWebGPUProperties error"] += 1
      if "canvasdata3', 'error': 'RENDERING_ERROR" in str(e):
        understood = True
        expected_errors["canvas3 rendering"] += 1
      if "canvasdata3software', 'error': 'RENDERING_ERROR" in str(e):
        understood = True
        expected_errors["canvas3 software rendering"] += 1
      if "error" in e and "WRONG_RENDERING_MODE" == e['error']:
        understood = True
        expected_errors['WRONG_RENDERING_MODE'] += 1

      timeouts = ["Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1057:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1064:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:956:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1062:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1074:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1075:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1068:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1072:14\nnotify@resource://gre/modules/Timer.sys.mjs:66:16\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1072:14\nnotify@resource://gre/modules/Timer.sys.mjs:49:17\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1651:14\nnotify@resource://gre/modules/Timer.sys.mjs:66:16\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1658:14\nnotify@resource://gre/modules/Timer.sys.mjs:66:16\n",
                  "Error: TIMEOUT timeoutPromise/</timeoutId<@resource://gre/modules/UserCharacteristicsPageService.sys.mjs:1659:14\nnotify@resource://gre/modules/Timer.sys.mjs:66:16\n"]
      for i in range(len(timeouts)):
        if "populateScreenInfo" in str(e) and (timeouts[i] in e or timeouts[i].replace("\n", "\\n") in str(e)):
          understood = True
          expected_errors[f"populateScreenInfo timeout {i}"] += 1
        if "populatePointerInfo" in str(e) and (timeouts[i] in e or timeouts[i].replace("\n", "\\n") in str(e)):
          understood = True
          expected_errors[f"populatePointerInfo timeout {i}"] += 1
        if (timeouts[i] in e or timeouts[i].replace("\n", "\\n") in str(e)):
          understood = True
          expected_errors[f"generic timeout {i}"] += 1


      if not understood:
        expected_errors[f"unrecognized js error: {str(e)[:80]}"] += 1

  return False