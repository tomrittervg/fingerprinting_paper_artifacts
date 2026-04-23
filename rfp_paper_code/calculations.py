import csv
import os
import pickle
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

import config
from cohort import cohort_fitness, cohort_fitness_from_histogram, cohort_fitness_excluding_singletons, cohort_fitness_from_histogram_excluding_singletons, cohort_p50, cohort_p50_from_histogram
from graphing import *
from graphing import _mpl_render_lock

def calculate_aggregated_metrics_impl(dv, metric_aggregation, metric_list):
    for metric in metric_list:
        try:
            val = getattr(dv, metric)
            if isinstance(val, list):
                val = str(val)
            metric_aggregation[metric][val] += 1
        except Exception as e:
            print("Error on", metric)
            raise e

def calculate_aggregated_metrics(metric_aggregation, all_data_values, metric_list,
                                progress_cb=None):
  for i, d in enumerate(all_data_values):
    if progress_cb and i % 100 == 0:
      progress_cb(i)
    calculate_aggregated_metrics_impl(d, metric_aggregation, metric_list)



def default_metric_aggregation_by_metric_inner():
  return defaultdict(int)

def default_metric_aggregation_by_metric():
  return [defaultdict(int), defaultdict(default_metric_aggregation_by_metric_inner)]

def calculate_aggregated_metrics_grouped_by_metric(metric_aggregation_by_os_accumulating, all_data_values, metric_list, grouping_metric,
                                                   progress_cb=None):
  for i, d in enumerate(all_data_values):
    if progress_cb and i % 100 == 0:
      progress_cb(i)
    for metric in metric_list:
      try:
        val = getattr(d, metric)
        if isinstance(val, list):
          val = str(val)

        grouped_value = getattr(d, grouping_metric)

        metric_aggregation_by_os_accumulating[metric][0][val] += 1
        metric_aggregation_by_os_accumulating[metric][1][grouped_value][val] += 1
      except Exception as e:
        print("Error on", metric)
        raise e

def calculate_fingerprint_set(fingerprints, fingerprints_by_category, all_data_values, subset, name, filters=None,
                              progress_cb=None):
  if filters is None:
    filters = []
  for f in filters:
    for d in all_data_values:
      d.add_filter(f)

  for i, d in enumerate(all_data_values):
    if progress_cb and i % 100 == 0:
      progress_cb(i)
    fp = d.fingerprint(subset)
    for category in fingerprints_by_category:
      (_, get_category, fingerprints_data, user_counts) = category
      if get_category(d):
        user_counts[get_category(d)] += 1
        fingerprints_data[get_category(d)][fp] += 1
    fingerprints[fp] += 1

  for f in reversed(filters):
    for d in all_data_values:
      d.pop_filter()




def _is_histogram(fp_dict):
    """Return True if fp_dict is a {cohort_size: num_cohorts} histogram (int keys),
    False if it is a {hash: count} counter (bytes keys)."""
    if not fp_dict:
        return False
    return isinstance(next(iter(fp_dict)), int)


def get_fingerprint_analysis(num_users, fingerprints):
  if _is_histogram(fingerprints):
      # {cohort_size: num_cohorts} — already aggregated
      num_unique_users = fingerprints.get(1, 0)
      cohort_size_frequency = dict(fingerprints)
      cohort_size_aggregate_users = {size: size * count for size, count in fingerprints.items()}
      return num_users, num_unique_users, cohort_size_aggregate_users, cohort_size_frequency

  num_unique_users = sum(1 for v in fingerprints.values() if v == 1)

  cohort_size_aggregate_users = defaultdict(int)
  cohort_size_frequency = defaultdict(int)
  for fp in fingerprints:
    cohort_size_aggregate_users[fingerprints[fp]] += fingerprints[fp]
    cohort_size_frequency[fingerprints[fp]] += 1

  return num_users, num_unique_users, cohort_size_aggregate_users, cohort_size_frequency



def print_fingerprint_analysis(title, num_users, fingerprints, print_cohort_size_tables,
                               display_title=None, experiment_metadata=None, baseline_info=None):
  """Analyze fingerprints and write results to .txt, .csv, and .bin files.

  Args:
    title: used for filenames ({title}.txt, {title}.csv, {title}.bin)
    display_title: used inside the file content (defaults to title)
    experiment_metadata: if provided, dict with per-experiment info
        (fingerprinter, short_name, long_name, filters) merged into
        the .bin pickle alongside global config.RUN_METADATA.
  """
  if display_title is None:
    display_title = title

  plog = lambda msg: config.log_and_file(f"{title}.txt", msg)
  plogq = lambda msg: config.write_file(f"{title}.txt", msg)

  num_users, num_unique_users, cohort_size_aggregate_users, cohort_size_frequency = get_fingerprint_analysis(num_users, fingerprints)

  plog(f"Analyzing the fingerprint distribution for {display_title}")
  plog("  There are " + str(num_users) + " total users")
  plog(f"  There are {num_unique_users} unique users, or {str(round(num_unique_users / num_users * 100, 4))}% out of {num_users} users")
  fitness = cohort_fitness_from_histogram(cohort_size_frequency) if _is_histogram(fingerprints) else cohort_fitness(fingerprints)
  fitness_hhi2 = cohort_fitness_from_histogram_excluding_singletons(cohort_size_frequency) if _is_histogram(fingerprints) else cohort_fitness_excluding_singletons(fingerprints)
  p50 = cohort_p50_from_histogram(cohort_size_frequency) if _is_histogram(fingerprints) else cohort_p50(fingerprints)
  plog("  Our cohort fitness score is " + str(fitness))
  plog("  Our cohort fitness score (HHI2, excl. singletons) is " + str(fitness_hhi2))
  plog("  Our P50 (median cohort size, non-unique users) is " + str(p50))
  if baseline_info is not None:
    b_unique, b_pct, b_fitness = baseline_info[:3]
    plog(f"  All-Data baseline:  {b_unique} unique users ({b_pct}%), cohort fitness {b_fitness}")
    if len(baseline_info) >= 4:
      plog(f"  All-Data baseline HHI2: {baseline_info[3]}")
    if len(baseline_info) >= 5:
      plog(f"  All-Data baseline P50: {baseline_info[4]}")
  plog("")

  # Write structured CSV alongside the text file
  csv_path = os.path.join(config.OUTPUT_FOLDER, f"{title}.csv")
  with open(csv_path, 'w', newline='') as csvf:
    writer = csv.writer(csvf)
    writer.writerow(["num_users", "num_unique_users", "pct_unique", "cohort_fitness", "cohort_fitness_hhi2", "p50"])
    writer.writerow([num_users, num_unique_users,
                     round(num_unique_users / num_users * 100, 4), fitness, fitness_hhi2, p50])

  # Write pickled fingerprint data with metadata
  metadata = dict(config.RUN_METADATA)
  metadata['num_users'] = num_users
  if experiment_metadata:
    metadata.update(experiment_metadata)
  bin_path = os.path.join(config.OUTPUT_FOLDER, f"{title}.bin")
  with open(bin_path, 'wb') as bf:
    payload = {'metadata': metadata, 'fingerprints': dict(fingerprints)}
    if _is_histogram(fingerprints):
        payload['format'] = 'histogram'
    pickle.dump(payload, bf, protocol=pickle.HIGHEST_PROTOCOL)

  if print_cohort_size_tables:
    max_lines = config.PRINT_MAX_LINES

    data_keys = sorted(cohort_size_frequency, key=cohort_size_aggregate_users.get, reverse=True)

    max_key_length = len(str(max(data_keys, key=lambda x: len(str(x)))))
    max_key_length = max(max_key_length, len("XXXXX Other Values"))

    plogq("  cohort_size".ljust(max_key_length) + "   | # of cohorts   | # of users   | % of users")
    plogq("  " + "-" * 60)

    num_shown = 0
    cohort_remainder_aggregate = 0
    cohort_user_aggregate = 0
    for k in data_keys:
      if num_shown >= max_lines:
        cohort_user_aggregate += cohort_size_aggregate_users[k]
        cohort_remainder_aggregate += cohort_size_frequency[k]
      else:
        plogq("  " + str(k).ljust(max_key_length) + " | " +
            "  " + str(cohort_size_frequency[k]).ljust(len("# of cohorts")) + " | " +
            "  " + str(cohort_size_aggregate_users[k]).ljust(len("# of users")) + " | " +
            "  " + str(round(cohort_size_aggregate_users[k] / num_users * 100, 2)) + " %")
      num_shown += 1
    if num_shown > max_lines:
        plogq("  " + (str(num_shown - max_lines) + " Other Values").ljust(max_key_length) + " | " +
            "  " + str(cohort_remainder_aggregate).ljust(len("# of cohorts")) + " | " +
            "  " + str(cohort_user_aggregate).ljust(len("# of users")) + " | " +
            "  " + str(round(cohort_user_aggregate / num_users * 100, 2)) + " %")

    plogq("")
    cdf_graph(
        'Cohort Size',
        'Percentage of Total Users',
        f'{title} Aggregation of Total Users Over Cohort Size',
        cohort_size_aggregate_users,
        num_users,
        rotate_xlabels=True,
        max_xticks=25
    )

    #save_cohort_zipf_plot(cohort_size_frequency, title)
    #save_cohort_ccdf_plot(cohort_size_frequency, title)


  plog("")
  plog(" " + "There are " + str(num_users) + " total users")
  plog(" " + f"There are {num_unique_users} unique users, or {str(round(num_unique_users / num_users * 100, 4))}% out of {num_users} users")
  plog("")



def save_cohort_ccdf_plot(cohort_size_frequency, title, weight_by='cohorts'):
    """
    Save a CCDF plot for cohort sizes.

    Args:
        cohort_size_frequency (dict[int,int]): {cohort_size -> number_of_cohorts}
        title (str): plot title
        weight_by ('cohorts' | 'users'):
            - 'cohorts': CCDF over cohorts (each cohort counts once)
            - 'users'  : CCDF over users (cohorts weighted by their size)
    Returns:
        str: path to the saved image

    Requirements:
        - `config.OUTPUT_FOLDER` exists in scope
        - `safe_filename(title)` is available
    """
    # Extract and validate data
    items = [(int(s), int(c)) for s, c in cohort_size_frequency.items() if int(s) > 0 and int(c) > 0]
    if not items:
        raise ValueError("cohort_size_frequency is empty or has no positive sizes/counts.")

    # Sort by size (ascending)
    items.sort(key=lambda t: t[0])
    sizes = np.array([s for s, _ in items], dtype=int)
    counts = np.array([c for _, c in items], dtype=int)

    # Weights: per-cohort or per-user
    if weight_by == 'users':
        weights = counts * sizes
        ylabel_suffix = " (per user)"
    else:
        weights = counts
        ylabel_suffix = " (per cohort)"

    # Compute CCDF: P(S >= s) at each distinct size s
    survivors = np.cumsum(weights[::-1])[::-1].astype(float)  # sum from the tail
    ccdf = survivors / survivors[0]  # normalize to probability

    # Step-wise plot on log–log axes
    fig, ax = plt.subplots()
    ax.step(sizes, ccdf, where='post')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Cohort size (users per cohort)')
    ax.set_ylabel(f'CCDF: P(S ≥ s){ylabel_suffix}')
    ax.set_title(title)
    ax.set_ylim(top=1.0)  # CCDF starts at 1
    # Save using your path convention
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'
    fname = f"{safe_filename(title)}_cohort_ccdf.{fmt}"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, fname)

    with _mpl_render_lock:
        fig.tight_layout()
        fig.savefig(path, format=fmt, dpi=200)
    plt.close(fig)
    config.log(f"  Cohort plot saved to: {path}")


def save_cohort_zipf_plot(cohort_size_frequency, title):
    """
    Create a Rank–size (Zipf) plot from a mapping {cohort_size -> number_of_cohorts}
    and save it using the provided output-path snippet. Returns the saved file path.

    Expects:
      - `config.OUTPUT_FOLDER` to exist in scope
      - `safe_filename(title)` to be available
    """
    # --- Prepare data (sizes descending, counts aligned) ---
    items = [(int(s), int(c)) for s, c in cohort_size_frequency.items() if int(s) > 0 and int(c) > 0]
    if not items:
        raise ValueError("cohort_size_frequency is empty or has no positive sizes/counts.")
    items.sort(key=lambda t: t[0], reverse=True)

    # Build step-wise (rank, size) without expanding to all cohorts
    xs, ys = [], []
    rank = 1
    for size, count in items:
        start = rank
        end = rank + count - 1  # inclusive
        xs.extend([start, end])
        ys.extend([size,  size])
        rank = end + 1

    total_cohorts = xs[-1]

    # --- Plot (log–log rank vs. size) ---
    fig, ax = plt.subplots()
    ax.step(xs, ys, where='post')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Rank (cohorts sorted by size)')
    ax.set_ylabel('Cohort size (users per cohort)')
    ax.set_title(title)
    ax.set_xlim(1, total_cohorts)

    # --- Use your path snippet and save ---
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'
    fname = f"{safe_filename(title)}_cohort_zipf.{fmt}"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, fname)

    with _mpl_render_lock:
        fig.tight_layout()
        fig.savefig(path, format=fmt, dpi=200)
    plt.close(fig)
    config.log(f"  Cohort plot saved to: {path}")



def plot_cohort_size_hist(cohort_size_frequency, title, bins_per_decade=10, y='cohorts', y_log=True):
    """
    Plot a log-binned histogram from a mapping {cohort_size -> number_of_cohorts}.

    Args:
        cohort_size_frequency (dict[int,int]): keys are cohort sizes; values are counts of such cohorts.
        bins_per_decade (int): how many geometric bins per 10x increase in size.
        y ('cohorts'|'users'): y-axis meaning:
            - 'cohorts': number of cohorts per size bin (weights = #cohorts)
            - 'users'  : total users per size bin (weights = #cohorts * size)
        y_log (bool): use log-scale on y-axis (helpful for heavy tails).
    """
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'
    fname = f"{safe_filename(f"{title} Distribution of Cohort Sizes")}.{fmt}"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, fname)

    # Clean and sort input
    sizes = np.array(sorted(int(k) for k in cohort_size_frequency if int(k) > 0), dtype=int)
    counts = np.array([int(cohort_size_frequency[int(k)]) for k in sizes], dtype=int)

    if sizes.size == 0:
        raise ValueError("cohort_size_frequency is empty or has no positive sizes.")

    min_size, max_size = sizes.min(), sizes.max()
    if min_size == max_size:
        # Degenerate case: all cohorts the same size; make a simple bar.
        fig, ax = plt.subplots()
        height = counts.sum() if y == 'cohorts' else (counts * sizes).sum()
        ax.bar([min_size], [height])
        ax.set_xscale('log')
        if y_log:
            ax.set_yscale('log')
        ax.set_xlabel('Cohort size (users per cohort)')
        ax.set_ylabel('Total users' if y == 'users' else 'Number of cohorts')
        ax.set_title(f'{title} Distribution of Cohort Sizes')
        with _mpl_render_lock:
            fig.tight_layout()
            fig.savefig(path, format=fmt)
        plt.close(fig)
        config.log(f"  Cohort plot saved to: {path}")
        return

    # Build logarithmic bin edges
    decades = np.log10(max_size) - np.log10(min_size)
    n_bins = max(1, int(np.ceil(decades * bins_per_decade)))
    bin_edges = np.logspace(np.log10(min_size), np.log10(max_size), n_bins + 1)

    # Choose weights
    if y == 'users':
        weights = counts * sizes
        ylabel = 'Total users per size bin'
    else:
        weights = counts
        ylabel = 'Number of cohorts per size bin'

    # Plot
    fig, ax = plt.subplots()
    ax.hist(sizes, bins=bin_edges, weights=weights)
    ax.set_xscale('log')
    if y_log:
        ax.set_yscale('log')
    ax.set_xlabel('Cohort size (users per cohort)')
    ax.set_ylabel(ylabel)
    ax.set_title(f'{title} Distribution of Cohort Sizes')
    with _mpl_render_lock:
        fig.tight_layout()
        fig.savefig(path, format=fmt)
    plt.close(fig)
    config.log(f"  Cohort plot saved to: {path}")



import numpy as np

def tom_knee_of_curve(metric_counts):
    DECREASE_FACTOR = 1.5
    keys_in_order = [k for k, v in sorted(metric_counts.items(), key=lambda item: item[1], reverse=True)]
    values_in_order = [v for k, v in sorted(metric_counts.items(), key=lambda item: item[1], reverse=True)]
    percent_decrease_in_order = []
    for indx, count in enumerate(values_in_order):
        if indx + 1 < len(metric_counts):
           percent_decrease_in_order.append((count - values_in_order[indx + 1]) / values_in_order[indx + 1] * 100)

    print("\t", percent_decrease_in_order[0:20])
    for indx, count in enumerate(values_in_order):
        print("\t", indx, keys_in_order[indx], count, end="")
        if indx + 1 < len(metric_counts):
           print(f"  {count} > {values_in_order[indx+1] * DECREASE_FACTOR} - {count > values_in_order[indx+1] * DECREASE_FACTOR}", end="")
           if count > values_in_order[indx+1] * DECREASE_FACTOR:
              print("  .", end="\n")
              return {"vline_at": keys_in_order[indx]}
        print("", end="\n")
    return {
        "vline_at": None
    }

def long_tail_piecewise_ccdf(metric_counts, min_points_per_side=5):
    """
    Determine the 'long tail' cutoff using a two-segment linear fit on the
    log–log CCDF of category counts.

    Args:
        metric_counts (dict[str, int]): {category -> user_count}, counts > 0
        min_points_per_side (int): minimum CCDF points per segment for the split

    Returns:
        dict with:
          - 'pct_users_in_tail' (float): 100 * users with count < vline_at / total_users
          - 'tail_users' (int): users in categories with count < vline_at
          - 'total_users' (int): total users across all categories
          - 'vline_at' (int): value threshold (count) where the tail begins
                              (use this with bar_graph(..., x_order='value_desc', vline_at=...))
    """
    # --- 1) Build counts array (one count per category) ---
    counts = np.array([int(v) for v in metric_counts.values() if int(v) > 0], dtype=int)
    if counts.size == 0:
        return {"pct_users_in_tail": 0.0, "tail_users": 0, "total_users": 0, "vline_at": 0}

    total_users = int(counts.sum())

    # --- 2) CCDF over distinct count values (category perspective) ---
    # x: distinct counts (ascending), ccdf: P(C >= x)
    uniq, freq = np.unique(counts, return_counts=True)
    # survivors from the tail
    surv = np.cumsum(freq[::-1])[::-1].astype(float)
    ccdf = surv / surv[0]  # normalize to probability in (0,1]

    # Need enough points to split
    n = uniq.size
    if n < (2 * min_points_per_side + 1):
        # Fallback: take the value at the middle as a simple split
        vline_at = int(np.ceil(uniq[max(min_points_per_side, n // 2)]))
        tail_users = int(counts[counts < vline_at].sum())
        pct = 100.0 * tail_users / total_users if total_users else 0.0
        return {"pct_users_in_tail": float(pct),
                "tail_users": tail_users,
                "total_users": total_users,
                "vline_at": vline_at}

    # --- 3) Piecewise linear fit on log–log space ---
    X = np.log10(uniq.astype(float))
    Y = np.log10(ccdf)

    best_idx = None
    best_sse = np.inf

    # candidate split: left segment = [0:i), right segment = [i:n)
    # ensure at least min_points_per_side points on each side
    for i in range(min_points_per_side, n - min_points_per_side + 1):
        # Fit line to left segment
        p1 = np.polyfit(X[:i], Y[:i], 1)
        y1_hat = np.polyval(p1, X[:i])
        sse1 = np.sum((Y[:i] - y1_hat) ** 2)

        # Fit line to right segment
        p2 = np.polyfit(X[i:], Y[i:], 1)
        y2_hat = np.polyval(p2, X[i:])
        sse2 = np.sum((Y[i:] - y2_hat) ** 2)

        sse = sse1 + sse2
        if sse < best_sse:
            best_sse = sse
            best_idx = i

    # Breakpoint x-value (count threshold) is the first point of the right segment
    # We interpret the 'long tail' as the many rare categories -> counts < threshold
    threshold = float(uniq[best_idx])
    vline_at = int(np.ceil(threshold))

    # --- 4) Users in the long tail (low-frequency side) ---
    tail_users = int(counts[counts < vline_at].sum())
    pct_users_in_tail = 100.0 * tail_users / total_users if total_users else 0.0

    return {
        "pct_users_in_tail": float(pct_users_in_tail),
        "tail_users": tail_users,
        "total_users": total_users,
        "vline_at": vline_at,
    }



def users_long_tail_percentage(metric_counts, min_tail_count=50, candidates=None):
    """
    Determine a value threshold via powerlaw_xmin_ks (fitted on the distribution
    of category counts) and treat the 'long tail' as counts < ceil(xmin).
    Returns dict with: pct_users_in_tail, tail_users, total_users, vline_at
    """
    # build array of positive counts (one per category)
    counts = np.array([int(v) for v in metric_counts.values() if int(v) > 0], dtype=int)
    if counts.size == 0:
        return {"pct_users_in_tail": 0.0, "tail_users": 0, "total_users": 0, "vline_at": 0}

    # frequency-of-frequencies for fitting (right-tail model -> we use threshold to split low tail)
    freq_of_freq = Counter(counts)

    xmin, _alpha = powerlaw_xmin_ks(freq_of_freq, candidates=candidates, min_tail_count=min_tail_count)
    vline_at = int(np.ceil(float(xmin))) if np.isfinite(xmin) else int(np.max(counts))

    total = int(counts.sum())
    # define long tail as low-frequency side:
    tail_users = int(counts[counts < vline_at].sum())
    pct_users_in_tail = (100.0 * tail_users / total) if total > 0 else 0.0

    return {
        "pct_users_in_tail": float(pct_users_in_tail),
        "tail_users": tail_users,
        "total_users": total,
        "vline_at": vline_at,
    }

def powerlaw_xmin_ks(metric_counts_or_counts_iterable, candidates=None, min_tail_count=50):
    """
    Estimate x_min for the RIGHT-HAND tail of a count distribution by minimizing
    the KS distance between the empirical CDF (for counts >= x_min) and a
    continuous power-law model. Intended for inputs where you have a mapping:
        {metric_value -> user_count_for_that_value}
    but it also accepts a plain iterable of positive counts.

    Args:
        metric_counts_or_counts_iterable:
            - dict-like: {value -> count}  (counts are numbers/strings convertible to int)
            - or iterable of positive counts (one per category)
        candidates (Iterable[float] | None):
            Optional candidate thresholds (in counts). If None, uses the unique
            observed counts in the data.
        min_tail_count (int):
            Minimum number of observations required in the tail for a candidate.

    Returns:
        (xmin, alpha)
            xmin (float): estimated threshold for the power-law tail.
            alpha (float | None): MLE exponent; None if a fallback was used.

    Notes:
        - This uses the standard *continuous* Pareto approximation:
              alpha = 1 + n / sum(log(x_i / xmin))
          which is typically fine for large discrete counts.
        - This models the distribution of **category frequencies** (not users).
          Each category contributes a single observation equal to its user count.
    """
    # --- Build the sample of counts (one per category) ---
    if isinstance(metric_counts_or_counts_iterable, (str, bytes)):
        raise TypeError("Input looks like a single string; pass a mapping {value->count} or an iterable of counts.")

    counts_list = []
    if hasattr(metric_counts_or_counts_iterable, "items"):
        # mapping: {value -> count}
        for v in metric_counts_or_counts_iterable.values():
            try:
                c = int(v)
            except Exception:
                continue
            if c > 0:
                counts_list.append(float(c))
    else:
        # iterable of counts
        for v in metric_counts_or_counts_iterable:
            try:
                c = float(v)
            except Exception:
                continue
            if c > 0:
                counts_list.append(c)

    sample = np.array(counts_list, dtype=float)
    if sample.size == 0:
        raise ValueError("No positive counts found.")

    # Default candidate thresholds: unique observed counts (ascending)
    if candidates is None:
        candidates = np.unique(sample)

    best = (None, np.inf, None)  # (xmin, ks, alpha)

    for xmin in candidates:
        tail = sample[sample >= xmin]
        n = tail.size
        if n < min_tail_count:
            continue

        denom = np.log(tail / xmin).sum()
        if denom <= 0:
            continue

        alpha = 1.0 + n / denom

        # Empirical CDF vs model CDF on the tail
        tail_sorted = np.sort(tail)
        ecdf = np.arange(1, n + 1) / n
        model_cdf = 1.0 - (tail_sorted / xmin) ** (1.0 - alpha)
        ks = np.max(np.abs(ecdf - model_cdf))

        if ks < best[1]:
            best = (float(xmin), float(ks), float(alpha))

    xmin, ks, alpha = best
    if xmin is None:
        # Fallback: 95th percentile of counts as a simple long-tail threshold
        xmin = float(np.quantile(sample, 0.95))
        alpha = None

    return xmin, alpha


def long_tail_percentile(metric_counts, percentile=95):
    """
    Long-tail cutoff by percentile of category counts.

    Tail = categories with count < threshold, where
    threshold = percentile (e.g., 95th) of the per-category counts.

    Args:
        metric_counts (dict[str, int]): {category -> user_count}, counts > 0
        percentile (float): percentile in [0, 100]; default 95

    Returns:
        dict with:
          - 'pct_users_in_tail' (float): 100 * users in tail / total users
          - 'tail_users' (int)         : users in categories with count < threshold
          - 'total_users' (int)        : total users across all categories
          - 'vline_at' (int)           : count threshold for plotting (bar_graph vline)
    """
    counts = np.array([int(v) for v in metric_counts.values() if int(v) > 0], dtype=int)
    if counts.size == 0:
        return {"pct_users_in_tail": 0.0, "tail_users": 0, "total_users": 0, "vline_at": 0}

    total_users = int(counts.sum())

    # Discrete threshold at the requested percentile of counts
    # 'higher' ensures the threshold is an observed count >= the percentile.
    thr = int(np.percentile(counts, percentile, method='higher' if hasattr(np, 'percentile') else 'linear'))
    thr = max(thr, 1)

    # Tail = low-frequency side
    tail_users = int(counts[counts < thr].sum())
    pct_users_in_tail = 100.0 * tail_users / total_users if total_users else 0.0

    return {
        "pct_users_in_tail": float(pct_users_in_tail),
        "tail_users": tail_users,
        "total_users": total_users,
        "vline_at": thr,
    }


import numpy as np

def long_tail_head_tail_breaks(metric_counts, head_ratio=0.20, min_group=5):
    """
    Long-tail cutoff via Head/Tail Breaks:
      - Repeatedly split counts at the mean; 'head' = values > mean.
      - Stop at the first split where head_count / group_count <= head_ratio.
      - Tail = categories with count < cutoff (value threshold).
    
    Args:
        metric_counts (dict[str, int]): {category -> user_count}, counts > 0
        head_ratio (float): stop when head proportion <= this (default 0.40)
        min_group (int): stop if the current group has fewer than this many items

    Returns:
        dict with:
          - 'pct_users_in_tail' (float): 100 * users in tail / total users
          - 'tail_users' (int)         : users in categories with count < vline_at
          - 'total_users' (int)        : total users across all categories
          - 'vline_at' (float)         : value threshold (mean at stopping level)
    """
    # --- collect positive per-category counts ---
    counts = np.array([int(v) for v in metric_counts.values() if int(v) > 0], dtype=int)
    if counts.size == 0:
        return {"pct_users_in_tail": 0.0, "tail_users": 0, "total_users": 0, "vline_at": 0.0}

    total_users = int(counts.sum())

    # Work on indices so we don't copy arrays repeatedly
    idx = np.arange(counts.size)
    vline_at = float(np.mean(counts))  # default to the first mean in case we exit early

    while True:
        group = counts[idx].astype(float)
        n = group.size
        if n < min_group:
            # Too few items left to justify another split
            break

        mu = float(group.mean())
        head_mask = group > mu
        head_idx = idx[head_mask]
        head_n = head_idx.size
        head_frac = head_n / n

        # Record current mean as candidate cutoff
        vline_at = mu

        # Stop at first split where head is sufficiently small
        if head_frac <= head_ratio or head_n < min_group:
            break

        # Otherwise, recurse on the head
        idx = head_idx

    # Tail = low-frequency side (strictly below threshold)
    tail_users = int(counts[counts < vline_at].sum())
    pct_users_in_tail = 100.0 * tail_users / total_users if total_users else 0.0

    return {
        "pct_users_in_tail": float(pct_users_in_tail),
        "tail_users": tail_users,
        "total_users": total_users,
        "vline_at": float(vline_at),
    }
