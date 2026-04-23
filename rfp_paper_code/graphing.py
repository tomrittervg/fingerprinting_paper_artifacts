import os
import threading
import numpy as np
import matplotlib.pyplot as plt
import re
from collections import defaultdict

import config

import warnings

# matplotlib's font/text rendering and warnings.catch_warnings both use global
# state that is not thread-safe under PYTHON_GIL=0.  Serialise the render+save
# step so that data preparation (figure construction) can still be parallel.
_mpl_render_lock = threading.Lock()


# Invalid filename chars replaced with underscore
_filename_sanitize = re.compile(r'[^A-Za-z0-9._-]+')

def safe_filename(s: str) -> str:
    name = s.replace("\n", "_").replace(" ", "_")
    return _filename_sanitize.sub("_", name)

def print_aggregate_table(
    metric: str,
    data: dict,
    max_lines: int = config.PRINT_MAX_LINES
) -> None:
    """
    Print the top `max_lines` entries of `data` (key→count), then
    aggregate the rest under “X Other Values”.
    Adds columns for percentage and cumulative percentage.
    """
    if not data:
        return
    try:
        plog = lambda msg: config.write_file(f"{metric}.txt", msg)

        # Header
        plog("  " + metric)
        plog("  " + "-" * 60)

        # Sort keys by descending count
        data_keys = sorted(data, key=data.get, reverse=True)
        total = sum(data.values())

        # Compute column widths
        max_key_length = len(str(max(data_keys, key=lambda x: len(str(x)))))
        max_key_length = max(max_key_length, len(f"{max_lines} Other Values"))
        count_col_width = max(8, len("Count"))
        pct_col_width = 8
        cum_pct_col_width = 12

        # Print table header
        header = (
            "  " +
            "Key".ljust(max_key_length) + " " +
            "Count".rjust(count_col_width) + " " +
            "%".rjust(pct_col_width) + " " +
            "Cumulative %".rjust(cum_pct_col_width)
        )
        plog(header)
        plog("  " + "-" * (max_key_length + count_col_width + pct_col_width + cum_pct_col_width + 4))

        # Print first max_lines, aggregate the rest
        num_shown = 0
        remainder_aggregate = 0
        cumulative = 0
        for k in data_keys:
            count = data[k]
            if num_shown >= max_lines:
                remainder_aggregate += count
            else:
                pct = (count / total) * 100 if total > 0 else 0
                cumulative += count
                cum_pct = (cumulative / total) * 100 if total > 0 else 0
                plog(
                    "  " +
                    str(k).ljust(max_key_length) + " " +
                    str(count).rjust(count_col_width) + " " +
                    f"{pct:6.2f}".rjust(pct_col_width) + " " +
                    f"{cum_pct:10.2f}".rjust(cum_pct_col_width)
                )
            num_shown += 1

        # If there were extra keys, print the “Other Values” line
        if num_shown > max_lines:
            label = f"{num_shown - max_lines} Other Values"
            pct = (remainder_aggregate / total) * 100 if total > 0 else 0
            cumulative += remainder_aggregate
            cum_pct = (cumulative / total) * 100 if total > 0 else 0
            plog(
                "  " +
                label.ljust(max_key_length) + " " +
                str(remainder_aggregate).rjust(count_col_width) + " " +
                f"{pct:6.2f}".rjust(pct_col_width) + " " +
                f"{cum_pct:10.2f}".rjust(cum_pct_col_width)
            )

        plog("")  # blank line
    except:
        print(f"Error printing aggregate table for {metric}.")
        print(f"Data: {data}")
        raise


def bar_graph(xlabel, ylabel, title, data,
              max_lines=config.GRAPH_MAX_LINES,
              rotate_xlabels=False,
              truncate_chars=10,
              log_scale=False,
              x_order='value_desc',
              max_xticks=None,
              vline_at=None):   # NEW: numeric -> value threshold; str -> category label
    """
    Creates a bar graph from `data`, then saves it to:
        {out_dir}/{sanitized_title}_{sanitized_xlabel}_{sanitized_ylabel}.{fmt}

    Parameters
    ----------
    ...
    vline_at : float|int|str|None
        - If numeric: treated as a VALUE (y) threshold. The line is drawn between bars
          where values cross this threshold based on `x_order`.
          * value_desc (default): boundary at first index i with vals[i] < threshold (line at i - 0.5)
          * value_asc: boundary at first index i with vals[i] >= threshold (line at i - 0.5)
          * key_*: non-monotone in values; fallback to label match (see below).
        - If string: treated as a CATEGORY label; line drawn through that bar’s center.
    """

    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'

    def _safe_num(v):
        try:
            return float(v)
        except Exception:
            return None

    # --- ordering ---
    if x_order == 'key_asc':
        data_keys = sorted(data, key=lambda k: (_safe_num(k) is None,
                                                _safe_num(k) if _safe_num(k) is not None else str(k)))
    elif x_order == 'key_desc':
        data_keys = sorted(data, key=lambda k: (_safe_num(k) is None,
                                                _safe_num(k) if _safe_num(k) is not None else str(k)),
                           reverse=True)
    elif x_order == 'value_asc':
        data_keys = sorted(data, key=data.get, reverse=False)
    else:  # 'value_desc'
        data_keys = sorted(data, key=data.get, reverse=True)

    data_for_graphing = defaultdict(int)
    num_shown = 0
    remainder_aggregate = 0

    for k in data_keys:
        if max_lines != -1 and num_shown >= max_lines:
            remainder_aggregate += data[k]
        else:
            data_for_graphing[str(k)] = data[k]
        num_shown += 1

    if max_lines != -1 and num_shown > max_lines:
        label = f"{num_shown - max_lines} Other Values"
        data_for_graphing[label] = remainder_aggregate

    # Build positions and labels (plotted order)
    cats = list(data_for_graphing.keys())
    vals = list(data_for_graphing.values())
    pos = list(range(len(cats)))

    def _trunc(s):
        s = str(s)
        if not truncate_chars:
            return s
        return s if len(s) <= truncate_chars else (s[:truncate_chars] + "...")
    full_labels = [_trunc(c) for c in cats]

    # --- Plotting + Save (all matplotlib global state under lock) ---
    fname = f"{safe_filename(title)}{'log' if log_scale else ''}.{fmt}"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, fname)

    with _mpl_render_lock:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(pos, vals)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)

            # Sparse ticks
            if max_xticks is None or max_xticks >= len(pos):
                tick_idx = pos
            else:
                step = max(1, (len(pos) + max_xticks - 1) // max_xticks)  # ceil
                tick_idx = list(range(0, len(pos), step))
            ax.set_xticks(tick_idx)
            ax.set_xticklabels([full_labels[i] for i in tick_idx],
                               rotation=(90 if rotate_xlabels else 0))

            # --- Vertical line marking tail start ---
            if vline_at is not None and len(pos) > 0:
                try:
                    vline_x = cats.index(vline_at)
                    ax.axvline(vline_x, color='black', linestyle='-', linewidth=1.5)
                except ValueError:
                    pass

            # Y-scale
            if log_scale:
                ax.set_yscale('log')
            else:
                ax.ticklabel_format(style='plain', axis='y')

            fig.tight_layout()
            fig.savefig(path, format=fmt)
            plt.close(fig)

    config.log(f"  Bar graph saved to: {path}")
    for w in caught:
        config.log(f"  matplotlib warning ({path}): {w.category.__name__}: {w.message}")




def stacked_bar_graph(
    graph_title,
    x_axis_values,
    data,
    max_lines=config.GRAPH_MAX_LINES,
    truncate_chars=10,
    log_scale=False
):
    """
    Creates a stacked bar graph and saves it to:
      analysis-2025-06-26/{sanitized_graph_title}.png

    Parameters
    ----------
    graph_title : str
    x_axis_values : list
    data : dict
    max_lines : int
    truncate_chars : int
        Number of characters to truncate x axis labels to (default: 10)
    log_scale : bool
        If True, use log scale for y-axis
    """
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'

    # --- Prepare data_for_graphing ---
    num_shown = 0
    data_for_graphing = defaultdict(lambda: [0] * min(len(x_axis_values), max_lines + 1))
    remainder_aggregate = dict.fromkeys(data, 0)

    for idx in range(len(x_axis_values)):
        if max_lines != -1 and num_shown >= max_lines:
            for k in data:
                remainder_aggregate[k] += data[k][idx]
        else:
            for k in data:
                data_for_graphing[k][idx] = data[k][idx]
        num_shown += 1

    if max_lines != -1 and num_shown > max_lines:
        x_axis_values = x_axis_values[:max_lines] + [f"{num_shown - max_lines} Other Values"]
        for k in data:
            data_for_graphing[k][-1] = remainder_aggregate[k]

    # Optionally truncate x axis labels
    if truncate_chars:
        x_axis_labels = [str(x)[:truncate_chars] + "..." for x in x_axis_values]
    else:
        x_axis_labels = x_axis_values

    # --- Plotting + Save (all matplotlib global state under lock) ---
    fname = f"{safe_filename(graph_title)}{'_log' if log_scale else ''}.{fmt}"
    os.makedirs(out_dir, exist_ok=True)
    save_path = os.path.join(out_dir, fname)

    with _mpl_render_lock:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, ax = plt.subplots()
            ax.tick_params(axis='x', rotation=90)
            bottom = np.zeros(len(x_axis_labels))

            for stack_name, stack_count in data_for_graphing.items():
                ax.bar(x_axis_labels, stack_count, width=0.5, label=stack_name, bottom=bottom)
                bottom += stack_count

            ax.set_title(graph_title)
            ax.legend(loc="upper right")

            if not log_scale:
                ax.ticklabel_format(style='plain', axis='y')

            fig.tight_layout()
            fig.savefig(save_path, format=fmt)
            plt.close(fig)

    config.log(f"  Stacked bar graph saved to: {save_path}")
    for w in caught:
        config.log(f"  matplotlib warning ({save_path}): {w.category.__name__}: {w.message}")

def cdf_graph(xlabel, ylabel, title,
              data,                  # {cohort_size -> total users in cohorts of that size}
              num_users,
              x_order='key_asc',      # Sorting order: 'key_asc', 'key_desc', 'value_asc', 'value_desc'
              max_xticks=12,          # max number of MAJOR ticks across x-range
              truncate_chars=0,
              rotate_xlabels=False):
    """
    Plots cumulative percentage of users vs. cohort size (ascending/descending) and saves as:
      {config.OUTPUT_FOLDER}/{safe_filename(title)}.png
    Ticks are based on the X-AXIS RANGE (not on data point density).

    Parameters
    ----------
    x_order : str
        Sorting order for the data. Options:
        - 'key_asc': Sort by cohort size (ascending).
        - 'key_desc': Sort by cohort size (descending).
        - 'value_asc': Sort by total users in cohorts (ascending).
        - 'value_desc': Sort by total users in cohorts (descending).
    """

    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'

    # --- Prepare ordered data based on x_order ---
    def _safe_num(v):
        try:
            return float(v)
        except Exception:
            return None

    if x_order == 'key_asc':
        sorted_data = sorted(data.items(), key=lambda x: (_safe_num(x[0]) is None, _safe_num(x[0]) if _safe_num(x[0]) is not None else str(x[0])))
    elif x_order == 'key_desc':
        sorted_data = sorted(data.items(), key=lambda x: (_safe_num(x[0]) is None, _safe_num(x[0]) if _safe_num(x[0]) is not None else str(x[0])), reverse=True)
    elif x_order == 'value_asc':
        sorted_data = sorted(data.items(), key=lambda x: x[1])
    elif x_order == 'value_desc':
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    else:
        raise ValueError(f"Invalid x_order: {x_order}")

    sizes = [str(k) for k, _ in sorted_data]
    if not sizes:
        raise ValueError("No cohort sizes found in data.")

    users_per_size = np.array([float(v) for _, v in sorted_data], dtype=float)
    cum_users = np.cumsum(users_per_size)
    y_pct = cum_users / float(num_users) * 100.0

    cats = []
    for k, _ in sorted_data:
        if truncate_chars and len(str(k)) > truncate_chars:
            cats.append(str(k)[:truncate_chars] + "...")
        else:
            cats.append(str(k))

    # --- Plot + Save (all matplotlib global state under lock) ---
    fname = f"{safe_filename(title)}.{fmt}"
    os.makedirs(out_dir, exist_ok=True)
    save_path = os.path.join(out_dir, fname)
    with _mpl_render_lock:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, ax = plt.subplots(figsize=(10, 6))
            if len(cats) > 50:
                ax.plot(range(len(cats)), y_pct, linewidth=1)
            else:
                ax.plot(range(len(cats)), y_pct, marker='o', linewidth=1)

            n = len(cats)
            if max_xticks is None or max_xticks >= n:
                tick_idx = np.arange(n)
            else:
                step = max(1, (n + max_xticks - 1) // max_xticks)  # ceil
                tick_idx = np.arange(0, n, step, dtype=int)

            ax.set_xticks(tick_idx)
            ax.set_xticklabels([cats[i] for i in tick_idx], rotation=(90 if rotate_xlabels else 0))
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            fig.tight_layout()
            fig.savefig(save_path, format=fmt, dpi=200)
            plt.close(fig)

    config.log(f"  CDF graph saved to: {save_path}")
    for w in caught:
        config.log(f"  matplotlib warning ({save_path}): {w.category.__name__}: {w.message}")


def experiment_cumulative_line_graph(
    steps,        # list of (slug, short_label) in display order
    fp_data,      # {fp_name: {slug: pct_unique}}
    fp_order,     # list of fp_names in legend order
    title="Cumulative Experiment Steps — % Unique Users",
):
    """Line graph of pct_unique across cumulative experiment steps, one line per fingerprinter.

    steps:    ordered list of (slug, display_label) for the x-axis
    fp_data:  {fp_name: {slug: pct_unique float}}
    fp_order: fingerprinter names in the order they appear in the legend
    """
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'
    fname = f"{safe_filename(title)}.{fmt}"
    path = os.path.join(out_dir, fname)

    x_labels = [label for _, label in steps]
    x_pos = list(range(len(steps)))

    with _mpl_render_lock:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, ax = plt.subplots(figsize=(max(10, len(steps) * 0.7), 6))

            for fp_name in fp_order:
                data = fp_data.get(fp_name, {})
                y = [data.get(slug) for slug, _ in steps]
                # Only plot points where data exists
                xs = [x for x, v in zip(x_pos, y) if v is not None]
                ys = [v for v in y if v is not None]
                if xs:
                    ax.plot(xs, ys, marker='o', label=fp_name)

            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            ax.set_xlabel("Cumulative Experiment Step")
            ax.set_ylabel("% Unique Users")
            ax.set_title(title)
            ax.legend()
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
            fig.tight_layout()
            fig.savefig(path, format=fmt)
            plt.close(fig)

    config.log(f"  Experiment line graph saved to: {path}")
    for w in caught:
        config.log(f"  matplotlib warning ({path}): {w.category.__name__}: {w.message}")


def experiment_cumulative_line_graph_by_fp(
    steps,        # list of (slug, short_label) in display order
    os_fp_data,   # {os_label: {fp_name: {slug: pct_unique}}}  — "Overall" key for global
    fp_order,     # list of fp_names — one subplot row per fp
    os_order,     # list of os_labels — one line per OS (including "Overall")
    title="Cumulative Experiment Steps by Fingerprinter — % Unique Users",
):
    """One subplot row per fingerprinter, one line per OS (+ Overall) on each."""
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'
    fname = f"{safe_filename(title)}.{fmt}"
    path = os.path.join(out_dir, fname)

    x_labels = [label for _, label in steps]
    x_pos = list(range(len(steps)))
    n_fp = len(fp_order)

    with _mpl_render_lock:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, axes = plt.subplots(n_fp, 1,
                                     figsize=(max(12, len(steps) * 0.7), 5 * n_fp),
                                     sharex=True)
            if n_fp == 1:
                axes = [axes]

            for ax, fp_name in zip(axes, fp_order):
                for os_label in os_order:
                    data = os_fp_data.get(os_label, {}).get(fp_name, {})
                    y = [data.get(slug) for slug, _ in steps]
                    xs = [x for x, v in zip(x_pos, y) if v is not None]
                    ys = [v for v in y if v is not None]
                    if xs:
                        lw = 2.5 if os_label == "Overall" else 1.2
                        ax.plot(xs, ys, marker='o', label=os_label, linewidth=lw,
                                markersize=4)

                ax.set_ylabel("% Unique Users")
                ax.set_title(fp_name)
                ax.legend(fontsize='small')
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))

            axes[-1].set_xticks(x_pos)
            axes[-1].set_xticklabels(x_labels, rotation=45, ha='right')
            axes[-1].set_xlabel("Cumulative Experiment Step")
            fig.suptitle(title, fontsize=14, y=1.0)
            fig.tight_layout()
            fig.savefig(path, format=fmt)
            plt.close(fig)

    config.log(f"  Experiment by-FP line graph saved to: {path}")
    for w in caught:
        config.log(f"  matplotlib warning ({path}): {w.category.__name__}: {w.message}")


def experiment_individual_bar_graph(
    experiments,  # list of (slug, short_label) in display order
    fp_data,      # {fp_name: {slug: pct_reduction float}}
    fp_order,     # list of fp_names in legend order
    title="Individual Experiment Steps — % Uniqueness Reduction vs All-Data",
):
    """Grouped bar graph of uniqueness reduction per individual experiment, one bar group per experiment.

    experiments: ordered list of (slug, display_label) for the x-axis
    fp_data:     {fp_name: {slug: pct_reduction}} where pct_reduction = baseline_pct - experiment_pct
    fp_order:    fingerprinter names in legend/bar order within each group
    """
    out_dir = config.OUTPUT_FOLDER
    fmt = 'png'
    fname = f"{safe_filename(title)}.{fmt}"
    path = os.path.join(out_dir, fname)

    n_exp = len(experiments)
    n_fp  = len(fp_order)
    width = 0.8 / max(n_fp, 1)
    x_pos = np.arange(n_exp)

    x_labels = [label for _, label in experiments]

    with _mpl_render_lock:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, ax = plt.subplots(figsize=(max(10, n_exp * 0.8), 6))

            for i, fp_name in enumerate(fp_order):
                data = fp_data.get(fp_name, {})
                offsets = x_pos + (i - n_fp / 2 + 0.5) * width
                vals = [data.get(slug, 0.0) for slug, _ in experiments]
                ax.bar(offsets, vals, width=width, label=fp_name)

            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            ax.set_xlabel("Individual Experiment")
            ax.set_ylabel("% Uniqueness Reduction vs All-Data")
            ax.set_title(title)
            ax.legend()
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}%"))
            ax.axhline(0, color='black', linewidth=0.8)
            fig.tight_layout()
            fig.savefig(path, format=fmt)
            plt.close(fig)

    config.log(f"  Experiment bar graph saved to: {path}")
    for w in caught:
        config.log(f"  matplotlib warning ({path}): {w.category.__name__}: {w.message}")
