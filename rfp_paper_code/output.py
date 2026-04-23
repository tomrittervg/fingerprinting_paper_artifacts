"""Output and visualization functions extracted from analyze.py's Final Analysis sections."""

import os
import csv
import shutil
import time
import concurrent.futures
from math import log2
from collections import defaultdict

import tqdm

import config
from data import pickle_data
from graphing import bar_graph, stacked_bar_graph, print_aggregate_table, safe_filename
from calculations import print_fingerprint_analysis, get_fingerprint_analysis, tom_knee_of_curve
from cohort import cohort_fitness, cohort_fitness_excluding_singletons, cohort_p50, cohort_detailed_stats
from fingerprinters import ALL_FINGERPRINTERS
from modes import ALL_MODES
from segmentation import try_to_auto_fit_segments
from script_config import script_config, METRIC_EXPERIMENTS_BY_KEY, CALCULATIONS_FOR_ARCHIVING


# =============================================================================
# 1. Metrics aggregated
# =============================================================================
def _process_metric_chunk(metrics_chunk, metric_aggregation, progress_callback=None):
    """Process a chunk of metrics: bar graphs, tables, entropy, HHI, HHI2, P50.
    Returns (errors, entropy_dict, hhi_dict, hhi2_dict, p50_dict).
    progress_callback(), if provided, is called after each metric.
    """
    errors = []
    entropy_dict = {}
    hhi_dict = {}
    hhi2_dict = {}
    p50_dict = {}
    for metric in metrics_chunk:
        if script_config['print_x_aggregate_graphs']:
            try:
                bar_graph(
                    'Metric Value', 'Num Submissions',
                    metric, metric_aggregation[metric],
                    rotate_xlabels=True
                )
                if script_config['print_log_scale_also']:
                    bar_graph(
                        'Metric Value', 'Num Submissions',
                        metric, metric_aggregation[metric],
                        rotate_xlabels=True, log_scale=True
                    )
            except Exception as e:
                errors.append(f"  Error visualizing {metric}: {e}. Skipping.")

        if script_config['print_x_aggregate_tables']:
            print_aggregate_table(metric, metric_aggregation[metric])

        if script_config['print_x_aggregate_entropy']:
            counts = metric_aggregation[metric]
            total = sum(counts.values())
            if total > 0:
                if len(counts) == 1:
                    entropy = 0.0
                else:
                    entropy = -sum((count / total) * log2(count / total) for count in counts.values() if count > 0)
                entropy_dict[metric] = entropy

        if script_config['print_x_hhi_index']:
            _data = metric_aggregation[metric]
            hhi_dict[metric] = cohort_fitness(_data)
            hhi2_dict[metric] = cohort_fitness_excluding_singletons(_data)
            p50_dict[metric] = cohort_p50(_data)

        if progress_callback:
            progress_callback()

    return errors, entropy_dict, hhi_dict, hhi2_dict, p50_dict


def visualize_metrics_aggregated(metric_aggregation, metric_aggregation_experiments,
                                  metrics_to_visualize, metrics_to_visualize_special, canvas_metrics,
                                  metric_experiments_by_key=None):
    if metric_experiments_by_key is None:
        metric_experiments_by_key = METRIC_EXPERIMENTS_BY_KEY
    aggregate_metrics_to_process = set()
    if script_config['show_special_metrics_aggregated']:
        aggregate_metrics_to_process.update(metrics_to_visualize_special)
    if script_config['show_all_metrics_aggregated']:
        aggregate_metrics_to_process.update(metrics_to_visualize)
    aggregate_metrics_to_process = sorted(aggregate_metrics_to_process)

    # Remove empty string, "{}", or None keys from canvas metric aggregations
    for metric in canvas_metrics:
        if metric in metric_aggregation:
            for bad_key in ["", "{}", None, "None"]:
                if bad_key in metric_aggregation[metric]:
                    del metric_aggregation[metric][bad_key]
        for name, metrics in metric_experiments_by_key.items():
            if metric in metrics:
                for bad_key in ["", "{}", None, "None"]:
                    if bad_key in metric_aggregation_experiments[name][metric]:
                        del metric_aggregation_experiments[name][metric][bad_key]

    entropy_dict = {}
    hhi_dict = {}
    hhi2_dict = {}
    p50_dict = {}

    if script_config['calculate_metrics_aggregated']:
        graph_threads = script_config['max_threads_graph_export']
        n_groups = graph_threads + 1
        print(f"Visualizing metric values aggregated... (progress bar is partition 1/{n_groups})")
        # Interleaved split for even load distribution
        chunks = [aggregate_metrics_to_process[i::n_groups] for i in range(n_groups)]
        main_chunk, worker_chunks = chunks[0], chunks[1:]

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=graph_threads)
        futures = [executor.submit(_process_metric_chunk, chunk, metric_aggregation)
                   for chunk in worker_chunks if chunk]

        errors = []
        with tqdm.tqdm(total=len(main_chunk), desc="  Bar graphs", file=config.terminal) as pbar:
            main_errors, main_entropy, main_hhi, main_hhi2, main_p50 = _process_metric_chunk(
                main_chunk, metric_aggregation,
                progress_callback=lambda: pbar.update(1)
            )
        errors.extend(main_errors)
        entropy_dict.update(main_entropy)
        hhi_dict.update(main_hhi)
        hhi2_dict.update(main_hhi2)
        p50_dict.update(main_p50)

        if futures:
            print("  Waiting for other groups to complete...")
            for future in concurrent.futures.as_completed(futures):
                chunk_errors, chunk_entropy, chunk_hhi, chunk_hhi2, chunk_p50 = future.result()
                errors.extend(chunk_errors)
                entropy_dict.update(chunk_entropy)
                hhi_dict.update(chunk_hhi)
                hhi2_dict.update(chunk_hhi2)
                p50_dict.update(chunk_p50)
        executor.shutdown(wait=False)

        for err in errors:
            print(err)

    if script_config['calculate_metric_experiment_aggregated']:
        experiment_metrics_flat = [(name, metric) for name, metrics in metric_experiments_by_key.items() for metric in metrics]
        errors = []
        with tqdm.tqdm(experiment_metrics_flat, desc="  Experiment bar graphs", file=config.terminal) as pbar:
            for name, metric in pbar:
                if script_config['print_x_aggregate_graphs']:
                    try:
                        bar_graph(
                            'Metric Value', 'Num Submissions',
                            f"{name} - {metric}", metric_aggregation_experiments[name][metric],
                            rotate_xlabels=True
                        )
                        if script_config['print_log_scale_also']:
                            bar_graph(
                                'Metric Value', 'Num Submissions',
                                f"{name} - {metric}", metric_aggregation_experiments[name][metric],
                                rotate_xlabels=True, log_scale=True
                            )
                    except Exception as e:
                        errors.append(f"  Error visualizing {name} - {metric}: {e}. Skipping.")

                if script_config['print_x_aggregate_tables']:
                    print_aggregate_table(f"{name} - {metric}", metric_aggregation_experiments[name][metric])

                if script_config['print_x_aggregate_entropy']:
                    # on the way through we just calculate
                    counts = metric_aggregation_experiments[name][metric]
                    total = sum(counts.values())
                    if total > 0:
                        if len(counts) == 1:
                            entropy = 0.0
                        else:
                            entropy = -sum((count / total) * log2(count / total) for count in counts.values() if count > 0)
                        entropy_dict[f"{name} - {metric}"] = entropy
                if script_config['print_x_hhi_index']:
                    _exp_data = metric_aggregation_experiments[name][metric]
                    hhi_dict[f"{name} - {metric}"] = cohort_fitness(_exp_data)
                    hhi2_dict[f"{name} - {metric}"] = cohort_fitness_excluding_singletons(_exp_data)
                    p50_dict[f"{name} - {metric}"] = cohort_p50(_exp_data)

        for err in errors:
            print(err)

    # At the end we print out the shannon entropy
    if script_config['print_x_aggregate_entropy'] and entropy_dict:
        sorted_entropy = sorted(entropy_dict.items(), key=lambda x: x[1], reverse=True)

        max_metric_length = max(len(metric) for metric, _ in sorted_entropy)
        config.log_and_file("metric_shannon_entropy_table.txt", f"{'Metric':<{max_metric_length}} | {'Entropy':>10}")
        config.log_and_file("metric_shannon_entropy_table.txt", "-" * (max_metric_length + 13))
        for metric, entropy in sorted_entropy:
            line = f"{metric:<{max_metric_length}} | {entropy:>10.4f}"
            config.log_and_file("metric_shannon_entropy_table.txt", line)
        # Write the entropy data to a CSV file
        csv_file_path = os.path.join(config.OUTPUT_FOLDER, "metric_shannon_entropy.csv")
        with open(csv_file_path, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Metric", "Entropy"])
            for metric, entropy in sorted_entropy:
                csv_writer.writerow([metric, entropy])
        print(f"  Shannon entropy data written to {csv_file_path}")

    # At the end we print out the HHI
    if script_config['print_x_hhi_index'] and hhi_dict:
        sorted_hhi = sorted(hhi_dict.items(), key=lambda x: x[1], reverse=False)

        max_metric_length = max(len(metric) for metric, _ in sorted_hhi)
        config.log_and_file("metric_hhi_table.txt", f"{'Metric':<{max_metric_length}} | {'HHI':>10}")
        config.log_and_file("metric_hhi_table.txt", "-" * (max_metric_length + 13))
        for metric, hhi in sorted_hhi:
            line = f"{metric:<{max_metric_length}} | {hhi:>10.4f}"
            config.log_and_file("metric_hhi_table.txt", line)

        # Write the HHI to a CSV file
        csv_file_path = os.path.join(config.OUTPUT_FOLDER, "metric_hhi.csv")
        with open(csv_file_path, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Metric", "HHI"])
            for metric, hhi in sorted_hhi:
                csv_writer.writerow([metric, hhi])
        print(f"  HHI data written to {csv_file_path}")

    # At the end we print out the HHI2 (excluding singletons)
    if script_config['print_x_hhi_index'] and hhi2_dict:
        sorted_hhi2 = sorted(hhi2_dict.items(), key=lambda x: x[1], reverse=False)

        max_metric_length = max(len(metric) for metric, _ in sorted_hhi2)
        config.log_and_file("metric_hhi2_table.txt", f"{'Metric':<{max_metric_length}} | {'HHI2':>10}")
        config.log_and_file("metric_hhi2_table.txt", "-" * (max_metric_length + 13))
        for metric, hhi2 in sorted_hhi2:
            line = f"{metric:<{max_metric_length}} | {hhi2:>10.4f}"
            config.log_and_file("metric_hhi2_table.txt", line)

        csv_file_path = os.path.join(config.OUTPUT_FOLDER, "metric_hhi2.csv")
        with open(csv_file_path, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Metric", "HHI2"])
            for metric, hhi2 in sorted_hhi2:
                csv_writer.writerow([metric, hhi2])
        print(f"  HHI2 data written to {csv_file_path}")

    # At the end we print out the P50 (median cohort size, non-unique users)
    if script_config['print_x_hhi_index'] and p50_dict:
        sorted_p50 = sorted(p50_dict.items(), key=lambda x: x[1], reverse=True)

        max_metric_length = max(len(metric) for metric, _ in sorted_p50)
        config.log_and_file("metric_p50_table.txt", f"{'Metric':<{max_metric_length}} | {'P50':>10}")
        config.log_and_file("metric_p50_table.txt", "-" * (max_metric_length + 13))
        for metric, p50 in sorted_p50:
            line = f"{metric:<{max_metric_length}} | {p50:>10}"
            config.log_and_file("metric_p50_table.txt", line)

        csv_file_path = os.path.join(config.OUTPUT_FOLDER, "metric_p50.csv")
        with open(csv_file_path, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Metric", "P50"])
            for metric, p50 in sorted_p50:
                csv_writer.writerow([metric, p50])
        print(f"  P50 data written to {csv_file_path}")

    # Report NULL/None percentages per metric
    if metric_aggregation and aggregate_metrics_to_process:
        null_sentinels = {"None", "", None}
        null_stats = []
        for metric in aggregate_metrics_to_process:
            counts = metric_aggregation.get(metric, {})
            total = sum(counts.values())
            if total == 0:
                continue
            null_count = sum(counts.get(s, 0) for s in null_sentinels)
            pct = 100.0 * null_count / total
            null_stats.append((metric, null_count, total, pct))

        null_stats.sort(key=lambda x: x[3], reverse=True)
        max_len = max((len(m) for m, *_ in null_stats), default=20)

        config.log_and_file("metric_null_rates.txt",
                            f"{'Metric':<{max_len}} | {'NULL Count':>10} | {'Total':>10} | {'% NULL':>8}")
        config.log_and_file("metric_null_rates.txt", "-" * (max_len + 37))
        for metric, null_count, total, pct in null_stats:
            config.log_and_file("metric_null_rates.txt",
                                f"{metric:<{max_len}} | {null_count:>10} | {total:>10} | {pct:>7.2f}%")

        csv_path = os.path.join(config.OUTPUT_FOLDER, "metric_null_rates.csv")
        with open(csv_path, mode="w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Metric", "NullCount", "Total", "PctNull"])
            for metric, null_count, total, pct in null_stats:
                w.writerow([metric, null_count, total, f"{pct:.4f}"])
        print(f"  NULL/None rates written to {csv_path}")


# =============================================================================
# 2. Metrics aggregated by OS
# =============================================================================
def visualize_metrics_by_os(metric_aggregation_by_os_accumulating, metric_aggregation_by_os,
                             metrics_to_visualize, metrics_to_visualize_special, canvas_metrics):
    aggregate_metrics_to_process = set()
    if script_config['show_special_metrics_aggregated']:
        aggregate_metrics_to_process.update(metrics_to_visualize_special)
    if script_config['show_all_metrics_aggregated']:
        aggregate_metrics_to_process.update(metrics_to_visualize)
    aggregate_metrics_to_process = sorted(aggregate_metrics_to_process)

    # Remove empty string, "{}", or None keys from canvas metric aggregations by OS
    for metric in canvas_metrics:
        if metric in metric_aggregation_by_os_accumulating:
            all_values_count = metric_aggregation_by_os_accumulating[metric][0]
            count_of_values_by_group = metric_aggregation_by_os_accumulating[metric][1]
            for bad_key in ["", "{}", None, "None"]:
                if bad_key in all_values_count:
                    del all_values_count[bad_key]

                    for group in count_of_values_by_group:
                        if bad_key in count_of_values_by_group[group]:
                            del count_of_values_by_group[group][bad_key]

    # First transform the accumulating data structure into the final data structure
    for metric in metrics_to_visualize:
        all_values_count = metric_aggregation_by_os_accumulating[metric][0]
        count_of_values_by_group = metric_aggregation_by_os_accumulating[metric][1]

        # Sort values by descending frequency
        all_values_sorted = sorted(all_values_count, key=all_values_count.get, reverse=True)
        val_to_index = {val: i for i, val in enumerate(all_values_sorted)}

        # Convert group counts to lists aligned with sorted values
        count_of_values_by_group_aligned = {}
        for grouped_value, val_counts in count_of_values_by_group.items():
            aligned = [0] * len(all_values_sorted)
            for val, count in val_counts.items():
                aligned[val_to_index[val]] = count
            count_of_values_by_group_aligned[grouped_value] = aligned

        # Store results
        metric_aggregation_by_os[metric] = [all_values_sorted, count_of_values_by_group_aligned]

    def _process_stacked_chunk(metrics_chunk, metric_aggregation_by_os, progress_callback=None):
        errors = []
        for metric in metrics_chunk:
            if script_config['print_x_by_os_aggregate_graphs']:
                try:
                    c, a = metric_aggregation_by_os[metric]
                    stacked_bar_graph(f"{metric} by OS", c, a)
                    if script_config['print_log_scale_also']:
                        stacked_bar_graph(f"{metric} by OS (log scale)", c, a, log_scale=True)
                except Exception as e:
                    errors.append(f"  Error visualizing {metric} by OS: {e}. Skipping.")
            if progress_callback:
                progress_callback()
        return errors

    graph_threads = script_config['max_threads_graph_export']
    n_groups = graph_threads + 1
    chunks = [aggregate_metrics_to_process[i::n_groups] for i in range(n_groups)]
    main_chunk, worker_chunks = chunks[0], chunks[1:]

    print(f"Visualizing metrics values aggregated by OS... (progress bar is partition 1/{n_groups})")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=graph_threads)
    futures = [executor.submit(_process_stacked_chunk, chunk, metric_aggregation_by_os)
               for chunk in worker_chunks if chunk]

    errors = []
    with tqdm.tqdm(total=len(main_chunk), desc="  Stacked bar graphs", file=config.terminal) as pbar:
        errors.extend(_process_stacked_chunk(main_chunk, metric_aggregation_by_os,
                                             progress_callback=lambda: pbar.update(1)))

    if futures:
        print("  Waiting for other groups to complete...")
        for future in concurrent.futures.as_completed(futures):
            errors.extend(future.result())
    executor.shutdown(wait=False)

    for err in errors:
        print(err)
    print("")


# =============================================================================
# 3. Fingerprint archiving with anonymization
# =============================================================================
def process_fingerprint_archiving(fingerprint_archive_anonymizing_tracking):
    print("Processing fingerprint archiving with anonymization...")
    start = time.time()

    for title, expose_metrics, filter_set, fingerprinters_set in CALCULATIONS_FOR_ARCHIVING:
        input_file = os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_{safe_filename(title)}.csv")
        output_file = os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_anonymized_{safe_filename(title)}.csv")

        if not expose_metrics:
            shutil.copy(input_file, output_file)

            # Store the header row
            with open(input_file, mode="r") as infile:
                csv_reader = csv.reader(infile)
                header = next(csv_reader)
        else:
            with open(input_file, mode="r") as infile, open(output_file, mode="w", newline="") as outfile:
                csv_reader = csv.reader(infile)
                csv_writer = csv.writer(outfile)

                # Store the header row, do not write it
                header = next(csv_reader)
                # csv_writer.writerow(header)

                # Process each row
                for row in tqdm.tqdm(csv_reader, desc="  Anonymizing fingerprint archive", file=config.terminal):
                    anonymized_row = []
                    for i, value in enumerate(row):
                        if i < len(expose_metrics):
                            metric = expose_metrics[i]
                            if fingerprint_archive_anonymizing_tracking[metric][value] < 100:
                                anonymized_row.append("ANONYMIZED")
                            else:
                                anonymized_row.append(value)
                        else:
                            anonymized_row.append(value)
                    csv_writer.writerow(anonymized_row)

        # Shuffle the anonymized file
        shuffled_file = os.path.join(config.OUTPUT_FOLDER, f"temp_values.csv")
        os.system(f"shuf --random-source=/dev/urandom {output_file} > {shuffled_file}")

        # Write the header row to a temporary file
        temp_header_file = os.path.join(config.OUTPUT_FOLDER, "temp_header.csv")
        with open(temp_header_file, "w", newline="") as thf:
            csv_writer = csv.writer(thf)
            csv_writer.writerow(header)

        # Use Unix commands to concatenate the header and shuffled file
        final_shuffled_file = os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_anonymized_shuffled_{safe_filename(title)}.csv")
        os.system(f"cat {temp_header_file} {shuffled_file} > {final_shuffled_file}")

        # Remove the temporary header file
        os.remove(temp_header_file)
        os.remove(shuffled_file)

        # Compress all three remaining files with zstd
        files_to_compress = [
            os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_{safe_filename(title)}.csv"),
            os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_anonymized_{safe_filename(title)}.csv"),
            os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_anonymized_shuffled_{safe_filename(title)}.csv"),
        ]

        for file_path in files_to_compress:
            os.system(f"zstd -q --rm {file_path}")
            print(f"  Compressed {file_path}")

        print(f"  Shuffled, anonymized fingerprint archive written to {final_shuffled_file}")

    elapsed = time.time() - start
    print(f"  All anonymized fingerprint archives written in {elapsed:.2f}s\n")


# =============================================================================
# 4. Print fingerprint results (shared for fingerprints / experiments / modes)
# =============================================================================
def print_fingerprint_results(label, total_num_users, fp_counters, fp_categories, fingerprinters,
                              display_label=None, filters=None, filename_label=None, baseline_by_fp=None):
    """Print fingerprint analysis for each fingerprinter.

    Args:
        label: short experiment name (used for display and as fallback for filenames)
        display_label: long experiment name (used inside files)
        filters: list of filter classes applied for this experiment (for metadata)
        filename_label: if set, used instead of label for output filenames/paths
    """
    if display_label is None:
        display_label = label
    file_label = filename_label if filename_label is not None else label
    for name, subset in fingerprinters.items():
        if name not in fp_counters:
            continue
        exp_meta = {
            'fingerprinter': name,
            'short_name': label,
            'long_name': display_label,
            'filters': [f.__name__ for f in filters] if filters else [],
        }
        print_fingerprint_analysis(
            f"{file_label}-{name}", total_num_users, fp_counters[name],
            script_config['print_cohort_size_tables'],
            display_title=f"{display_label}-{name}",
            experiment_metadata=exp_meta,
            baseline_info=baseline_by_fp.get(name) if baseline_by_fp else None,
        )
        for category in fp_categories[name]:
            (category_label, _, fingerprints_data, user_counts) = category
            for category_key in fingerprints_data.keys():
                if user_counts[category_key] > 1:
                    print_fingerprint_analysis(
                        f"{file_label} {name} {category_label}{category_key}", user_counts[category_key], fingerprints_data[category_key],
                        script_config['print_cohort_size_tables'],
                        display_title=f"{display_label} {name} {category_label}{category_key}"
                    )
                else:
                    config.log(f"  Skipping {name} for {category_label}{category_key} due to {"only 1" if user_counts[category_key] == 1 else "no"} users there.")
        config.log("")


# =============================================================================
# 5. Print fingerprint bucket results
# =============================================================================
def print_fingerprint_bucket_results(fingerprints_buckets, label=None):
    import time as _time
    _t0 = _time.time()
    filename = f"{label}.txt" if label else "fingerprint_buckets.txt"
    config.log_and_file(filename, "Fingerprinter, Liklihood, Total Users, Unique Users, Percentage of Unique Users, Cohort Fitness, Cohort Fitness HHI2, P50")
    # Get fingerprinter names from the data (handles config-selected subsets)
    _first_lk = next(iter(fingerprints_buckets.values()), {})
    _fp_names = sorted(_first_lk.keys()) if _first_lk else sorted(ALL_FINGERPRINTERS.keys())

    _csv_name = f"{label}.csv" if label else "fingerprint_buckets.csv"
    _csv_path = os.path.join(config.OUTPUT_FOLDER, _csv_name)

    # Build all (name, likelihood, fp_data) tasks for parallel stat computation
    _tasks = []
    for name in _fp_names:
        for likelihood, fp_sets in fingerprints_buckets.items():
            _tasks.append((name, likelihood, fp_sets[name][0], fp_sets[name][1]))

    def _compute_one(task):
        name, likelihood, fp_data, declared_total = task
        num_users, num_unique_users, _, _ = get_fingerprint_analysis(declared_total, fp_data)
        stats = cohort_detailed_stats(fp_data)
        return {
            'name': name, 'likelihood': likelihood,
            'declared_total': declared_total,
            'num_unique_users': num_unique_users,
            'stats': stats,
        }

    # Parallel computation
    _results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        with tqdm.tqdm(total=len(_tasks), desc=f"  Bucket stats{' (' + label + ')' if label else ''}",
                       unit="pair", file=config.terminal) as pbar:
            for result in pool.map(_compute_one, _tasks):
                _results.append(result)
                pbar.update(1)

    _t_stats = _time.time() - _t0

    # Write text output (grouped by fingerprinter)
    _csv_rows = []
    for r in _results:
        name = r['name']
        likelihood = r['likelihood']
        s = r['stats']
        try:
            config.log_and_file(filename,
                f"  {name}, {likelihood:.4f}, {r['declared_total']}, "
                f"{r['num_unique_users']}, "
                f"{round(r['num_unique_users'] / r['declared_total'] * 100, 4)}, "
                f"{s['hhi']}, {s['hhi2']}, {s['p50']}")
        except:
            print(f"  {name}, {likelihood:.4f}, error")

        _csv_rows.append({
            'Fingerprinter': name,
            'Likelihood': f'{likelihood:.4f}',
            'TotalUsers': r['declared_total'],
            'UniqueUsers': r['num_unique_users'],
            'PctUnique': round(r['num_unique_users'] / r['declared_total'] * 100, 4) if r['declared_total'] else 0,
            'HHI': s['hhi'],
            'HHI2': s['hhi2'],
            'P50': s['p50'],
        })

    # Add blank lines between fingerprinters in text output
    for name in _fp_names:
        config.log_and_file(filename, "")

    # Write detailed CSV
    if _csv_rows:
        with open(_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=_csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(_csv_rows)

    _t_total = _time.time() - _t0
    config.log(f"  Bucket stats + output: {_t_total:.1f}s (stats={_t_stats:.1f}s, write={_t_total - _t_stats:.1f}s)")
    print("")


# =============================================================================
# 6. Print metric bucket results
# =============================================================================
def print_metric_bucket_results(metrics_to_run_bucketing_for, metric_buckets):
    for metric in metrics_to_run_bucketing_for:
        filename = f"metric_buckets_{metric}.csv"
        print(f"Writing metric buckets for {metric}... to {filename}")
        config.write_file(filename, "Metric, Likelihood, Total Users, Unique Values, Percentage of Unique Values")
        for likelihood, metric_sets in metric_buckets.items():
            total_users = metric_sets[metric][1]
            value_counts = metric_sets[metric][0]
            num_unique_values = sum(1 for v in value_counts.values() if v == 1)
            try:
                pct_unique = (num_unique_values / total_users * 100) if total_users else 0
                config.write_file(filename, f"  {metric}, {likelihood:.4f}, {total_users}, {num_unique_values}, {pct_unique:.4f}")
            except Exception:
                config.write_file(filename, f"  {metric}, {likelihood:.4f}, error")
    print("")


# =============================================================================
# 7. Font analysis
# =============================================================================
def analyze_missing_fonts(font_counters, user_counts):
    missing_fonts_strings_counter = font_counters['strings']
    missing_fonts_individual_counter = font_counters['individual']
    missing_fonts_individual_counter_by_version = font_counters['by_version']
    missing_fonts_individual_counter_by_locale = font_counters['by_locale']
    missing_fonts_individual_android_counter_by_machine = font_counters['android_by_machine']
    missing_fonts_individual_android_counter_by_machine_version = font_counters['android_by_machine_version']

    total_num_users_by_os = user_counts['by_os']
    total_num_users_by_os_version = user_counts['by_os_version']
    total_num_users_by_os_locale = user_counts['by_os_locale']
    total_num_users_by_os_machine_model = user_counts['by_os_machine_model']
    total_num_users_by_os_machine_model_version = user_counts['by_os_machine_model_version']

    if script_config['missing_font_sets']:
        pickle_data(
            missing_fonts_strings_counter,
            "missing_font_sets_counter.bin",
            hash=None,
            override_dir=config.OUTPUT_FOLDER
        )
        for os_key in missing_fonts_strings_counter:
            logfile = f"missing_font_sets_{os_key}.txt"
            config.log_and_file(logfile, f"Most common missing font sets for OS {os_key} (as sorted, comma-separated strings):")
            config.write_file(logfile, "-" * 50)
            config.write_file(logfile, f"{'Count':>8} | {'% Users':>8} | Value")
            config.write_file(logfile, "-" * 50)
            for fonts_str, count in sorted(missing_fonts_strings_counter[os_key].items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_num_users_by_os[os_key] * 100) if total_num_users_by_os[os_key] else 0
                config.write_file(logfile, f"{count:8d} | {pct:8.2f} | {fonts_str}")
            config.write_file(logfile, "-" * 50)

    for os_key in missing_fonts_individual_counter:
        pickle_data(
            missing_fonts_individual_counter,
            "missing_fonts_individual_counter.bin",
            hash=None,
            override_dir=config.OUTPUT_FOLDER
        )
        config.log_and_file(f"missing_fonts_{os_key}.txt", f"Most common individual missing fonts for OS {os_key}:")
        config.write_file(f"missing_fonts_{os_key}.txt", f"{'Font':<40} | {'Count':>8} | {'% Users':>8}")
        config.write_file(f"missing_fonts_{os_key}.txt", "-" * 65)
        total_os_users = total_num_users_by_os[os_key]
        for font, count in sorted(missing_fonts_individual_counter[os_key].items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_os_users * 100) if total_os_users else 0
            config.write_file(f"missing_fonts_{os_key}.txt", f"{font:<40} | {count:8d} | {pct:8.2f}")

    if script_config['missing_fonts_by_version']:
        pickle_data(
            missing_fonts_individual_counter_by_version,
            "missing_fonts_individual_counter_by_version.bin",
            hash=None,
            override_dir=config.OUTPUT_FOLDER
        )
        pickle_data(
            missing_fonts_individual_android_counter_by_machine,
            "missing_fonts_individual_android_counter_by_machine.bin",
            hash=None,
            override_dir=config.OUTPUT_FOLDER
        )
        pickle_data(
            missing_fonts_individual_android_counter_by_machine_version,
            "missing_fonts_individual_android_counter_by_machine_version.bin",
            hash=None,
            override_dir=config.OUTPUT_FOLDER
        )
        for os_key in missing_fonts_individual_counter_by_version:
            for version_key in missing_fonts_individual_counter_by_version[os_key]:
                logfilename = f"missing_fonts_{os_key}_{version_key}.txt"
                config.log_and_file(logfilename, f"Most common individual missing fonts for OS {os_key}, version {version_key}:")
                config.write_file(logfilename, f"{'Font':<40} | {'Count':>8} | {'% Users':>8}")
                config.write_file(logfilename, "-" * 65)
                total_os_users = total_num_users_by_os_version[os_key][version_key]
                for font, count in sorted(missing_fonts_individual_counter_by_version[os_key][version_key].items(), key=lambda x: x[1], reverse=True):
                    pct = (count / total_os_users * 100) if total_os_users else 0
                    config.write_file(logfilename, f"{font:<40} | {count:8d} | {pct:8.2f}")

        for machine_key in missing_fonts_individual_android_counter_by_machine:
            logfilename = f"missing_fonts_Android_{machine_key}.txt".replace(" ", "_")
            config.log_and_file(logfilename, f"Most common individual missing fonts for Android, machine {machine_key}:")
            config.write_file(logfilename, f"{'Font':<40} | {'Count':>8} | {'% Users':>8}")
            config.write_file(logfilename, "-" * 65)
            total_machine_users = total_num_users_by_os_machine_model["Android"][machine_key]
            for font, count in sorted(missing_fonts_individual_android_counter_by_machine[machine_key].items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_machine_users * 100) if total_machine_users else 0
                config.write_file(logfilename, f"{font:<40} | {count:8d} | {pct:8.2f}")

        for machine_version_key in missing_fonts_individual_android_counter_by_machine_version:
            logfilename = f"missing_fonts_Android_{machine_version_key}.txt".replace(" ", "_")
            config.log_and_file(logfilename, f"Most common individual missing fonts for Android, machine version {machine_version_key}:")
            config.write_file(logfilename, f"{'Font':<40} | {'Count':>8} | {'% Users':>8}")
            config.write_file(logfilename, "-" * 65)
            total_machine_users = total_num_users_by_os_machine_model_version["Android"][machine_version_key]
            for font, count in sorted(missing_fonts_individual_android_counter_by_machine_version[machine_version_key].items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_machine_users * 100) if total_machine_users else 0
                config.write_file(logfilename, f"{font:<40} | {count:8d} | {pct:8.2f}")

    if script_config['missing_fonts_by_locale']:
        pickle_data(
            missing_fonts_individual_counter_by_locale,
            "missing_fonts_individual_counter_by_locale.bin",
            hash=None,
            override_dir=config.OUTPUT_FOLDER
        )
        for os_key in missing_fonts_individual_counter_by_locale:
            for locale_key in missing_fonts_individual_counter_by_locale[os_key]:
                config.log_and_file(f"missing_fonts_{os_key}_{locale_key}.txt", f"Most common individual missing fonts for OS {os_key}, locale {locale_key}:")
                config.write_file(f"missing_fonts_{os_key}_{locale_key}.txt", f"{'Font':<40} | {'Count':>8} | {'% Users':>8}")
                config.write_file(f"missing_fonts_{os_key}_{locale_key}.txt", "-" * 65)
                total_os_users = total_num_users_by_os_locale[os_key][locale_key]
                for font, count in sorted(missing_fonts_individual_counter_by_locale[os_key][locale_key].items(), key=lambda x: x[1], reverse=True):
                    pct = (count / total_os_users * 100) if total_os_users else 0
                    config.write_file(f"missing_fonts_{os_key}_{locale_key}.txt", f"{font:<40} | {count:8d} | {pct:8.2f}")


# =============================================================================
# 8. Segmentation
# =============================================================================
def run_segmentation(all_data_values, target_metrics, metrics_to_visualize, canvas_metrics):
    n_workers = script_config.get('parallel_segmentation', 8)
    for m in target_metrics:
        data_for_metric = [dv for dv in all_data_values if hasattr(dv, m)]
        n_total = len(all_data_values)
        n_present = len(data_for_metric)
        if n_present < n_total * 0.9:
            print(f"Skipping {m} — only present on {n_present}/{n_total} DataValues ({100*n_present/n_total:.1f}%)")
            continue
        print("=" * 50)
        print(m)
        if n_present < n_total:
            print(f"  (metric absent on {n_total - n_present} records; analyzing {n_present})")
        print("")
        try_to_auto_fit_segments(data_for_metric, m, metrics_to_visualize, verbosity=3, n_workers=n_workers)


# =============================================================================
# 9. Single-metric removal analysis
# =============================================================================
# lives in smr.py
