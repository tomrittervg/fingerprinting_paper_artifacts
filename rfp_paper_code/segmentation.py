import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

"""# Segmentation Analysis Tools"""

# Unified blocklist for both segmentation analyses.
# - exact:    metric name must match exactly
# - prefix:   metric name must start with the entry
# - contains: metric name must contain the entry
SEGMENTATION_BLOCKLIST = {
    'exact': [
        "webgl_vendor",         # use webgl_renderer_raw_vendor instead
        "webgl_renderer",       # use webgl_renderer_raw_* instead
        "webgl_version_raw",    # too specific; use webgl_renderer_raw_* classifiers instead
        "hw_machine_model",     # use hw_machine_model_* classifiers instead
        "math_ops",             # array form of target metrics
        "math_ops_fdlibm",      # array form of target metrics
        "math_ops_fdlibm_2",    # array form of target metrics
    ],
    'prefix': [
        "schema",
        "errors",
        "errors_js",
        "build_date",
        "channel",
        "version",
        "country",
        "ice_",
        "canvas_",
        "canvassoftware_",
        "screen_",
        "audio_",
        "fonts_",
        "font_",
        "missing_fonts",
        "voices_",
        "mathml_",
        "prefs_",
        "locale_",
        "intl_",
        "hw_gamepads",
        "hw_camera_count",
        "hw_microphone_count",
        "hw_speaker_count",
        "hw_max_touch_points",
        "hw_any_pointer_type",
        "hw_pointer_",
        "hw_touch_rotation_angle",
        "hw_motion_",
        "hw_orientation",
        "target_frame_rate",
        "hw_group_count",
        "webgl2_",
    ],
    'contains': [
        "_software",
        "_allowlisted",
        "_nonallowlisted",
        "_ssdeep",
    ],
}

def is_segmentation_blocklisted(metric):
    if metric in SEGMENTATION_BLOCKLIST['exact']:
        return True
    if any(metric.startswith(p) for p in SEGMENTATION_BLOCKLIST['prefix']):
        return True
    if any(s in metric for s in SEGMENTATION_BLOCKLIST['contains']):
        return True
    return False

"""
Data Segmentation relies on the assumption that if a metric A has a bunch of values, a1, a2, a3, a4
it is because of different values for metrics B, C, D, and so on.

If submissions have the same values for B, C, and D - then all of those submissions should have value a1.
And conversely, all submissions with value a1 should have the same values for B, C, and D.

If all the submissions with the same values for B, C, and D result in two values for A, say a1 and a2,
that implies that a there is some other metric E that should segment a1 and a2.

And if the submissions for a1 have different values for a metric B, it _might_ imply that B is not actually
relevant for segmenting.  However it is also possible that two values b1 and b2 both correspond to a1.

It is also possible, but much more complicated to calculate, that there is a more complex interaction occuring.
Something like
  B = b1 always implies A = a1
  B = b2 C = c1 implies A = a2
  B = b2, C = c2, D <> d1 implies A = a3
  B = b2, C = c2, D = d1 implies A = a4
"""

class ClassificationKey:
  def __init__(self, dv, segmentation_keys):
    self.segmentation_keys = segmentation_keys
    for k in self.segmentation_keys:
      if type(k) == str:
        setattr(self, k, getattr(dv, k, "None"))
      elif type(k) == tuple and type(k[0]) == str and type(k[1]) == type(lambda : ""):
        setattr(self, k[0], k[1](dv))
      else:
        raise Exception(f"Unexpected keytype passed to ClassificationKey: {type(k)}")

  def __hash__(self):
    return hash(str(self))

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return False
    for k in self.segmentation_keys:
      if type(k) == str:
        if getattr(self, k) != getattr(other, k):
          return False
      elif type(k) == tuple and type(k[0]) == str and type(k[1]) == type(lambda : ""):
        if getattr(self, k[0]) != getattr(other, k[0]):
          return False
      else:
        raise Exception(f"Error doing __eq__ in ClassificationKey: {type(k)}")
    return True

  def __str__(self):
    s = ""
    for k in self.segmentation_keys:
      if type(k) == str:
        s += f"{k}={getattr(self, k)} "
      elif type(k) == tuple and type(k[0]) == str and type(k[1]) == type(lambda : ""):
        s += f"{k[0]}={getattr(self, k[0])} "
      else:
        raise Exception(f"Error doing _str_ in ClassificationKey: {type(k)}")

    return s

def segment_data(all_data_values, metric_to_analyze, segmentation_keys):

  values_per_key = defaultdict(lambda: defaultdict(int))
  keys_per_value = defaultdict(lambda: defaultdict(int))

  for d in all_data_values:
    key = ClassificationKey(d, segmentation_keys)

    values_per_key[key][getattr(d, metric_to_analyze)] += 1
    keys_per_value[getattr(d, metric_to_analyze)][key] += 1

  return values_per_key, keys_per_value

def analyze_segmented_data(all_data_values, values_per_key, keys_per_value, verbose=False):
  # verbose can be a string which is then treated as a prefix.
  # If it's a bool, make it a zero width space which will still be treated as True
  # BECAUSE I AM THE WORST PROGRAMMER IN THE WORLD
  if type(verbose) == bool and verbose == True:
    verbose = "​"

  # First print out the data about how well we chose segment keys
  total_submissions = len(all_data_values)

  values_in_only_one_segment = 0
  values_in_more_than_one_segment = 0
  values_in_more_than_one_segment_but_all_the_segments_have_only_one_value = 0
  for v in keys_per_value:
    num_segments_containing_this_value = len(keys_per_value[v])
    if num_segments_containing_this_value == 1:
      values_in_only_one_segment += 1
    else:
      values_in_more_than_one_segment += 1
      values_in_more_than_one_segment_but_all_the_segments_have_only_one_value += 1
      for k in keys_per_value[v]:
        if len(values_per_key[k]) != 1:
          values_in_more_than_one_segment_but_all_the_segments_have_only_one_value -= 1
          break

  concerning_values_in_more_than_one_segment = values_in_more_than_one_segment - values_in_more_than_one_segment_but_all_the_segments_have_only_one_value
  percentage_good_1 = concerning_values_in_more_than_one_segment / len(keys_per_value) * 100

  if verbose:
    print(f"{verbose}There are {len(keys_per_value)} different values.")
    print(f"{verbose}{values_in_only_one_segment} of them are assigned into only one segment.")
    # print(f"{verbose}{round(values_in_more_than_one_segment / len(keys_per_value), 2) * 100}% ({values_in_more_than_one_segment} / {len(keys_per_value)}) of them are assigned into more than one segment.")
    print(f"{verbose}{percentage_good_1}% ({concerning_values_in_more_than_one_segment} / {len(keys_per_value)}) of them are assigned into more than one segment AND the segments contain more than one value.")
    print("")

  imperfect_segments = 0
  submissions_segmented_perfectly = 0
  for k in values_per_key:
    num_values_for_this_key = len(values_per_key[k])
    if num_values_for_this_key == 1:
      for v in values_per_key[k]:
        submissions_segmented_perfectly += values_per_key[k][v]
    else:
      imperfect_segments += 1

  percentage_good_2 = imperfect_segments / len(values_per_key) * 100
  percentage_good_3 = submissions_segmented_perfectly / total_submissions * 100

  if verbose:
    print(f"{verbose}There are {len(values_per_key)} different segments (aka key combinations).")
    print("")
    print(f"{verbose}{percentage_good_2}% of segments ({imperfect_segments} / {len(values_per_key)}) have more than one value.")
    print(f"{verbose}{percentage_good_3}% ({submissions_segmented_perfectly} / {total_submissions}) of submissions are in a segment with only one value.")

  return (percentage_good_1, percentage_good_2, percentage_good_3, len(values_per_key), total_submissions)

def try_to_auto_fit_segments(all_data_values, metric_to_analyze, metrics_to_consider, verbosity=0, n_workers=8):
  def segmentation_fitness(percentages):
    # percentages = (pct_concerning_values, pct_imperfect_segments, pct_submissions_perfect, n_segments, total)
    # Primary: % of submissions in pure (single-value) segments
    # Secondary: small penalty for segment count to prefer simpler explanations
    import math
    if percentages[0] == 0:
      return float('inf')
    return percentages[2] - math.log2(max(percentages[3], 1)) * 0.01

  segmentation_set =[
       "os",
  ]
  necessary_step_increase = .001

  if verbosity >= 2:
    print(f"Our starting segment is {segmentation_set}.")
  starting_segment_data = segment_data(all_data_values, metric_to_analyze, segmentation_set)
  starting_segment_results = analyze_segmented_data(all_data_values, *starting_segment_data, verbose = verbosity >= 2)
  current_fitness = segmentation_fitness(starting_segment_results)
  if current_fitness == float('inf'):
    print(f"  Already perfectly segmented by {segmentation_set}.")
    return
  new_fitness = current_fitness
  current_fitness -= necessary_step_increase # Needed to bootstrap the while loop

  if verbosity >= 2:
    print("")
    print("-" * 40)
    print("")

  # Precompute target values once — they don't change between rounds
  n_total = len(all_data_values)
  target_vals = [getattr(d, metric_to_analyze) for d in all_data_values]

  while new_fitness - current_fitness >= necessary_step_increase:
      current_fitness = new_fitness
      if verbosity >= 1:
        print(f"Our current segment is {segmentation_set} with a fitness of {current_fitness}. Going to look for a metric to add.")
      best_additional_fitness = 0
      best_metric_to_add = ""

      candidates = [m for m in metrics_to_consider
                    if m not in segmentation_set
                    and m != metric_to_analyze
                    and not is_segmentation_blocklisted(m)]

      # Precompute base key tuples for current segmentation_set once per round —
      # avoids redundant getattr calls for the already-fixed keys inside each worker.
      # Non-hashable attribute values (e.g. lists) are stringified so tuples stay hashable.
      _current_set = list(segmentation_set)
      _hashable_types = (str, int, float, bool, type(None))
      def _kv(v):
        return v if isinstance(v, _hashable_types) else str(v)
      base_vals = [tuple(_kv(getattr(d, k)) for k in _current_set) for d in all_data_values]

      def _fast_eval_candidate(m):
        # Build segment membership with plain tuple keys (no ClassificationKey overhead).
        # Inline the fitness calculation to avoid segment_data / analyze_segmented_data overhead.
        import math
        values_per_key = {}   # key_tuple -> set of distinct target values
        count_per_key = {}    # key_tuple -> submission count
        keys_per_value = {}   # target_val -> set of key_tuples

        for base, target, d in zip(base_vals, target_vals, all_data_values):
          key = base + (_kv(getattr(d, m, "None")),)
          if key not in values_per_key:
            values_per_key[key] = set()
            count_per_key[key] = 0
          values_per_key[key].add(target)
          count_per_key[key] += 1
          if target not in keys_per_value:
            keys_per_value[target] = set()
          keys_per_value[target].add(key)

        n_values = len(keys_per_value)
        concerning = 0
        for v, keys in keys_per_value.items():
          if len(keys) > 1:
            if not all(len(values_per_key[k]) == 1 for k in keys):
              concerning += 1

        if concerning == 0:
          return float('inf'), m

        # Primary: % of submissions in pure (single-value) segments
        pure_submissions = sum(count_per_key[k] for k, vals in values_per_key.items() if len(vals) == 1)
        pct_perfect = pure_submissions / n_total * 100
        n_segments = len(values_per_key)
        return pct_perfect - math.log2(max(n_segments, 1)) * 0.01, m

      all_scores = []  # collected when verbosity >= 4
      with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_fast_eval_candidate, m) for m in candidates]
        for future in as_completed(futures):
          this_segment_fitness, m = future.result()
          if verbosity >= 4:
            all_scores.append((this_segment_fitness, m))
          if this_segment_fitness > best_additional_fitness:
            if verbosity >= 3:
              print("\t\t", m, "is better with", this_segment_fitness)
            best_additional_fitness = this_segment_fitness
            best_metric_to_add = m
          # Early exit: perfect fitness found, cancel remaining work (best-effort)
          if best_additional_fitness == float('inf'):
            for f in futures:
              f.cancel()
            break

      if verbosity >= 4 and all_scores:
        all_scores.sort(key=lambda x: (-x[0], x[1]))
        _log_path = os.path.join(os.environ.get('SEG_LOG_DIR', '/tmp'), 'run.log')
        with open(_log_path, 'a') as _lf:
          _lf.write(f"\n--- All candidate scores for segment {segmentation_set} on {metric_to_analyze} ---\n")
          _lf.write(f"{'Fitness':>12s}  Feature\n")
          for _sc, _mn in all_scores:
            _f_str = "inf" if _sc == float('inf') else f"{_sc:.6f}"
            _lf.write(f"{_f_str:>12s}  {_mn}\n")

      new_fitness = best_additional_fitness
      if new_fitness - current_fitness > necessary_step_increase:
        segmentation_set.append(best_metric_to_add)

        if verbosity >= 1:
          print(f"\tAdding {best_metric_to_add} to the segment brought out fitness to {new_fitness}")
        if verbosity >= 2:
          print("")

        new_segment_data = segment_data(all_data_values, metric_to_analyze, segmentation_set)
        analyze_segmented_data(all_data_values, *new_segment_data, verbose=("\t" if verbosity >= 2 else False))

        if verbosity >= 2:
          print("")
          print("\t", "-" * 40)
          print("")
      else:
        if verbosity >= 1:
          print(f"\tAdding {best_metric_to_add} to the segment brought out fitness to {new_fitness}")
          print(f"\tThat isn't enough to be worth it, so we're done.")

  if verbosity < 2:
    print("")
    print(f"Our final segmentation was {segmentation_set}")
    final_segment_data = segment_data(all_data_values, metric_to_analyze, segmentation_set)
    analyze_segmented_data(all_data_values, *final_segment_data, verbose=True)


