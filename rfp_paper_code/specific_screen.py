

"""# Screen Available Analysis

## Negative Height Analysis
"""

perplatform_height = defaultdict(list)
perplatform_width = defaultdict(list)

neg_w = 0
neg_h = 0

for d in all_data_values:
  try:
    if int(d.screen_primary_avail_height_diff) < 0:
      neg_h += 1
      perplatform_height[d.os].append(int(d.screen_primary_avail_height_diff))
  except:
    pass

  try:
    if int(d.screen_primary_avail_width_diff) < 0:
      neg_w += 1
      perplatform_width[d.os].append(int(d.screen_primary_avail_width_diff))
  except:
    pass

print(f"{neg_w} people with a negative available width ({round(neg_w / len(all_data_values) * 100 , 2)}%)")
print(f"{neg_h} people with a negative available height ({round(neg_h / len(all_data_values) * 100 , 2)}%)")



neg_w = 0
neg_h = 0

for d in all_data_values:
  if d.screen_primary_avail_height_diff == "NA":
    continue
  if int(d.screen_primary_avail_height_diff) < 0:
    if len(d.screens) == 1:
      neg_h += 1
  if int(d.screen_primary_avail_width_diff) < 0:
    if len(d.screens) == 1:
      neg_w += 1
      print(d.screen_primary_resolution, d.screen_primary_avail, d.screens)
    else:
      pass


print(f"{neg_w} people with 1 monitor and a negative available width ({round(neg_w / len(all_data_values) * 100 , 2)}%)")
print(f"{neg_h} people with 1 monitor and a negative available height ({round(neg_h / len(all_data_values) * 100 , 2)}%)")

"""## Overall Analysis"""

perplatform_height = defaultdict(list)
perplatform_width = defaultdict(list)

for d in all_data_values:
  try:
    perplatform_height[d.os].append(int(d.screen_primary_avail_height_diff))
  except:
    pass

  try:
    perplatform_width[d.os].append(int(d.screen_primary_avail_width_diff))
  except:
    pass

import numpy as np
import matplotlib.pyplot as plt

def plot_cumulative_percentage(arr):
    # Sort the array
    sorted_arr = np.sort(arr)

    # Generate x values (unique sorted values) and cumulative percentage
    x_values = np.unique(sorted_arr)
    total_count = len(sorted_arr)
    y_values = [np.sum(sorted_arr <= x) / total_count * 100 for x in x_values]

    # Plot the cumulative percentage graph
    plt.figure(figsize=(8, 5))
    plt.plot(x_values, y_values, marker='o', linestyle='-')
    plt.xlabel("Value")
    plt.ylabel("Cumulative Percentage (%)")
    plt.title("Cumulative Percentage of Values Less Than or Equal to X")
    plt.ylim(0, 100)  # Y-axis from 0% to 100%
    plt.grid(True)
    plt.show()



def plot_most_common_values(arr):
    # Count occurrences of each value
    counter = collections.Counter(arr)

    # Sort by value
    sorted_items = sorted(counter.items())  # Sort by value
    values, counts = zip(*sorted_items)

    # Plot bar chart
    plt.figure(figsize=(8, 8))
    plt.bar(values, counts)
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.title("Most Common Values (Sorted by Value)")
    plt.yscale("log")  # Set Y-axis to log scale
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()

import collections

def print_bucketed_value_distribution(arr, min_percentage=5):
    total = len(arr)
    counter = collections.Counter(arr)
    sorted_items = sorted(counter.items())  # (value, count)

    result_rows = []

    current_bucket_start = None
    current_bucket_end = None
    running_count = 0

    for value, count in sorted_items:
        percentage = (count / total) * 100

        if current_bucket_start is None:
            current_bucket_start = value
            current_bucket_end = value

        running_count += count
        current_bucket_end = value

        running_percentage = (running_count / total) * 100

        if running_percentage >= min_percentage:
            if current_bucket_start == current_bucket_end:
                label = f"{current_bucket_start}"
            else:
                label = f"{current_bucket_start}-{current_bucket_end}"

            result_rows.append((label, running_percentage))
            current_bucket_start = None
            current_bucket_end = None
            running_count = 0

    # Handle any remaining values
    if running_count > 0:
        if current_bucket_start == current_bucket_end:
            label = f"{current_bucket_start}"
        else:
            label = f"{current_bucket_start}-{current_bucket_end}"
        result_rows.append((label, (running_count / total) * 100))

    # Print the result table
    print(f"{'Value Range':<15} | {'Percentage':>10}")
    print("-" * 30)
    for label, pct in result_rows:
        print(f"{label:<15} | {pct:>9.2f}%")


for os in perplatform_height:
  print("-" * 30)
  print(os)
  print("Mean Width:", np.mean(perplatform_width[os]))
  print("Median Width:", np.median(perplatform_width[os]))
  plot_most_common_values(perplatform_width[os])
  plot_cumulative_percentage(perplatform_width[os])
  print_bucketed_value_distribution(perplatform_width[os])
  print("")
  print("Mean Height:", np.mean(perplatform_height[os]))
  print("Median Height:", np.median(perplatform_height[os]))
  plot_most_common_values(perplatform_height[os])
  plot_cumulative_percentage(perplatform_height[os])
  print_bucketed_value_distribution(perplatform_height[os])

  print("\n\n\n")

screen_avail_metrics = [
    "screen_primary_avail_width_diff",
    "screen_primary_avail_height_diff",
  ]

# It's pointless to analyze them with mixed OSes
#screen_avail_metrics_metric_aggregation = calculate_aggregated_metrics(screen_avail_metrics, verbose=True)
screen_avail_metrics_metric_aggregation_by_os = calculate_aggregated_metrics_grouped_by_metric(screen_avail_metrics, "os")

for k in screen_avail_metrics:
  if len(screen_avail_metrics_metric_aggregation_by_os[k]) != 1:
    print(k)
    print("-"*30)
    print("Total number of submissions by value by OS")
    for i in range(len(screen_avail_metrics_metric_aggregation_by_os[k][0])):
      print(screen_avail_metrics_metric_aggregation_by_os[k][0][i], ":")
      for u in screen_avail_metrics_metric_aggregation_by_os[k][1]:
        print("\t", u, screen_avail_metrics_metric_aggregation_by_os[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by OS", screen_avail_metrics_metric_aggregation_by_os[k][0], screen_avail_metrics_metric_aggregation_by_os[k][1])

    print("")
    print("")

    #print("Total number of submissions by value by architecture")
    #for i in range(len(metric_aggregation_by_arch[k][0])):
    #  print(metric_aggregation_by_arch[k][0][i], ":")
    #  for u in metric_aggregation_by_arch[k][1]:
    #    print("\t", u, metric_aggregation_by_arch[k][1][u][i])
    #print("")
    #
    #stacked_bar_graph(k + " by Arch", metric_aggregation_by_arch[k][0], metric_aggregation_by_arch[k][1])

    print("")
    print("")

"""# Touch Analysis"""

touch_metrics = [
    "hw_max_touch_points",
]

touch_by_os = calculate_aggregated_metrics_grouped_by_metric(touch_metrics, "os")

for k in touch_metrics:
    x_values = touch_by_os[k][0]  # All touch point values (e.g., [0, 1, 2, 5])
    grouped_counts = touch_by_os[k][1]  # {os_name: [counts aligned with x_values]}

    os_list = sorted(grouped_counts.keys())

    # Print header
    header = f"{'Value':<10} | " + " | ".join(f"{os:<10}" for os in os_list)
    print(f"\nValue Frequencies by OS for {k}:\n")
    print(header)
    print("-" * len(header))

    # Print each row
    for i, val in enumerate(x_values):
        row = f"{str(val):<10} | "
        row += " | ".join(f"{grouped_counts[os][i]:<10}" for os in os_list)
        print(row)

"""# WebGL Parameter Analysis"""

webgl_metrics = [
    "webgl_params_MAX_TEXTURE_SIZE",
    "webgl_params_MAX_CUBE_MAP_TEXTURE_SIZE",
    "webgl_params_MAX_RENDERBUFFER_SIZE",
    "webgl_params_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
    "webgl_params_MAX_TEXTURE_IMAGE_UNITS",
    "webgl_params_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
    "webgl_params_MAX_VERTEX_ATTRIBS",
    "webgl_params_MAX_VERTEX_UNIFORM_VECTORS",
    "webgl_params_MAX_FRAGMENT_UNIFORM_VECTORS",
    "webgl_params_MAX_VARYING_VECTORS",
    "webgl_params_MAX_VIEWPORT_DIMS",
    "webgl_params_ALIASED_POINT_SIZE_RANGE_MIN",
    "webgl_params_ALIASED_POINT_SIZE_RANGE_MAX",
    "webgl_params_ALIASED_LINE_WIDTH_RANGE_MIN",
    "webgl_params_ALIASED_LINE_WIDTH_RANGE_MAX"
]

webgl_by_os = calculate_aggregated_metrics_grouped_by_metric(webgl_metrics, "os")

for k in webgl_metrics:
    x_values = webgl_by_os[k][0]  # All touch point values (e.g., [0, 1, 2, 5])
    grouped_counts = webgl_by_os[k][1]  # {os_name: [counts aligned with x_values]}

    os_list = sorted(grouped_counts.keys())

    # Print header
    header = f"{'Value':<10} | " + " | ".join(f"{os:<10}" for os in os_list)
    print(f"\nValue Frequencies by OS for {k}:\n")
    print(header)
    print("-" * len(header))

    # Print each row
    for i, val in enumerate(x_values):
        row = f"{str(val):<10} | "
        row += " | ".join(f"{grouped_counts[os][i]:<10}" for os in os_list)
        print(row)

    print(f"\nSmallest value such that 99% of submissions are greater than it (for {k}):")
    for os in os_list:
        counts = grouped_counts[os]

        # Filter and sort numerically (excluding "")
        val_count_pairs = [
            (x_values[i], counts[i])
            for i in range(len(x_values))
            if x_values[i] != ""
        ]

        try:
            val_count_pairs.sort(key=lambda x: float(x[0]))  # ASCENDING
        except ValueError:
            pass

        total = sum(count for _, count in val_count_pairs)
        cumulative = 0
        value = None

        for val, count in val_count_pairs:
            cumulative += count
            if cumulative / total >= 0.01:
                value = val
                break

        print(f"  {os:<10}: {value}")



    print("-" * len(header))

"""# Canvas Analysis

# DNT / GPC Analysis
"""

privpref_metrics = [
    "prefs_general_donottrack_enabled",
    "prefs_general_globalprivacycontrol_enabled"
]

privpref_by_os = calculate_aggregated_metrics_grouped_by_metric(privpref_metrics, "os")

for k in privpref_metrics:
    x_values = privpref_by_os[k][0]  # All touch point values (e.g., [0, 1, 2, 5])
    grouped_counts = privpref_by_os[k][1]  # {os_name: [counts aligned with x_values]}

    os_list = sorted(grouped_counts.keys())

    # Print header
    header = f"{'Value':<10} | " + " | ".join(f"{os:<10}" for os in os_list)
    print(f"\nValue Frequencies by OS for {k}:\n")
    print(header)
    print("-" * len(header))

    # Print each row
    for i, val in enumerate(x_values):
        row = f"{str(val):<10} | "
        row += " | ".join(f"{grouped_counts[os][i]:<10}" for os in os_list)
        print(row)

gpc_by_dnt = calculate_aggregated_metrics_grouped_by_metric(["prefs_general_globalprivacycontrol_enabled"], "prefs_general_donottrack_enabled")

for k in ["prefs_general_globalprivacycontrol_enabled"]:
    x_values = gpc_by_dnt[k][0]  # All touch point values (e.g., [0, 1, 2, 5])
    grouped_counts = gpc_by_dnt[k][1]  # {os_name: [counts aligned with x_values]}

    os_list = sorted(grouped_counts.keys())

    # Print header
    header = f"{'Value':<10} | " + " | ".join(f"{os:<10}" for os in os_list)
    print(f"\nValue Frequencies by GPC for {k}:\n")
    print(header)
    print("-" * len(header))

    # Print each row
    for i, val in enumerate(x_values):
        row = f"{str(val):<10} | "
        row += " | ".join(f"{grouped_counts[os][i]:<10}" for os in os_list)
        print(row)

dnt_by_gpc = calculate_aggregated_metrics_grouped_by_metric(["prefs_general_donottrack_enabled"], "prefs_general_globalprivacycontrol_enabled")

for k in ["prefs_general_donottrack_enabled"]:
    x_values = dnt_by_gpc[k][0]  # All touch point values (e.g., [0, 1, 2, 5])
    grouped_counts = dnt_by_gpc[k][1]  # {os_name: [counts aligned with x_values]}

    os_list = sorted(grouped_counts.keys())

    # Print header
    header = f"{'Value':<10} | " + " | ".join(f"{os:<10}" for os in os_list)
    print(f"\nValue Frequencies by DNT for {k}:\n")
    print(header)
    print("-" * len(header))

    # Print each row
    for i, val in enumerate(x_values):
        row = f"{str(val):<10} | "
        row += " | ".join(f"{grouped_counts[os][i]:<10}" for os in os_list)
        print(row)

"""# Math Value Analysis"""

# Apply the Experiment Filter

count_values_affected = 0
for d in all_data_values:
  if d.add_filter(fdlibmFilter):
      count_values_affected += 1
  #d.pop_filter()
  pass

print(f"fdlibm filter took effect {count_values_affected} times")
print("")

print("Active Filters:")
print(all_data_values[0].list_filters())

if str(fdlibmFilter) in all_data_values[0].list_filters():
  for i in range(30):
    print("This analysis won't work because you're applying the fdlibm filter!!!")


math_metrics = []
for i in range(24):
  math_metrics.append(f"math_op_{i}")

math_metric_aggregation = calculate_aggregated_metrics(math_metrics)
math_metric_aggregation_by_os = calculate_aggregated_metrics_grouped_by_metric(math_metrics, "os")

for k in math_metrics:
  if len(math_metric_aggregation[k].keys()) == 1:
    print("Op", k, "has all identical submissions")
  else:
    print("Not Op", k, "!")

print("")
for k in math_metrics:
  if len(math_metric_aggregation[k].keys()) != 1:
    print(k)
    print("-"*30)
    print("Total number of submissions by value")
    for v in math_metric_aggregation[k].keys():
      print(v, "-", math_metric_aggregation[k][v])

    print("")

    print("Total number of submissions by value by OS")
    for i in range(len(math_metric_aggregation_by_os[k][0])):
      print(math_metric_aggregation_by_os[k][0][i], ":")
      for u in math_metric_aggregation_by_os[k][1]:
        print("\t", u, math_metric_aggregation_by_os[k][1][u][i])
    print("")

    differences = defaultdict(lambda: defaultdict(int))
    for d in all_data_values:
      k_fdlibm = k.replace("op_", "op_fdlibm_")
      val = getattr(d, k)
      fdlibm_val = getattr(d, k_fdlibm)
      if fdlibm_val != "None" and val != fdlibm_val:
        if d.os != "WINNT":
          raise Exception("We got a fdlibm different on " + d.os)
        differences[val][fdlibm_val] += 1
        #print(k, "orig=", val, "fdlibm=", fdlibm_val)
    print(" original          ->   fdlibm              -  num occurrances")
    for r in differences:
      for s in differences[r]:
        print(r, "-> ", s, " - ", differences[r][s], "times")


    print("")
    bar_graph('Metric Value', 'Num Submissions', k, math_metric_aggregation[k], rotate_xlabels=True)
    stacked_bar_graph(k + " by OS", math_metric_aggregation_by_os[k][0], math_metric_aggregation_by_os[k][1])
    print("")
    print("")

if str(fdlibmFilter) in all_data_values[0].list_filters():
  for i in range(30):
    print("This analysis won't work because you're applying the fdlibm filter!!!")

for d in all_data_values:

  d.pop_filter()
  pass

print("Active Filters:")
print(all_data_values[0].list_filters())

"""# WebAudio Analysis"""

audio_metrics = ["audio_fingerprint"]

audio_metric_aggregation = calculate_aggregated_metrics(audio_metrics, verbose=True)
audio_metric_aggregation_by_os = calculate_aggregated_metrics_grouped_by_metric(audio_metrics, "os")
audio_metric_aggregation_by_arch = calculate_aggregated_metrics_grouped_by_metric(audio_metrics, "hw_cpu_arch")
#audio_metric_aggregation_by_cpu = calculate_aggregated_metrics_grouped_by_metric(audio_metrics, "hw_cpu_model_friendly_2")
audio_metric_aggregation_by_tmp = calculate_aggregated_metrics_grouped_by_metric(audio_metrics, "canvassoftware_canvasdata13_fingerprintjs2")


for k in audio_metrics:
  if len(audio_metric_aggregation[k].keys()) != 1:
    print(k)
    print("-"*30)
    print("Total number of submissions by value")
    for v in audio_metric_aggregation[k].keys():
      print(v, "-", audio_metric_aggregation[k][v])

    bar_graph('Metric Value', 'Num Submissions', k, audio_metric_aggregation[k], rotate_xlabels=True)
    print("")

    print("Total number of submissions by value by OS")
    for i in range(len(audio_metric_aggregation_by_os[k][0])):
      print(audio_metric_aggregation_by_os[k][0][i], ":")
      for u in audio_metric_aggregation_by_os[k][1]:
        print("\t", u, audio_metric_aggregation_by_os[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by OS", audio_metric_aggregation_by_os[k][0], audio_metric_aggregation_by_os[k][1])

    print("")
    print("")

    print("Total number of submissions by value by architecture")
    for i in range(len(audio_metric_aggregation_by_arch[k][0])):
      print(audio_metric_aggregation_by_arch[k][0][i], ":")
      for u in audio_metric_aggregation_by_arch[k][1]:
        print("\t", u, audio_metric_aggregation_by_arch[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by Arch", audio_metric_aggregation_by_arch[k][0], audio_metric_aggregation_by_arch[k][1])

    print("")
    print("")

    print("Total number of submissions by value by FOO")
    for i in range(len(audio_metric_aggregation_by_tmp[k][0])):
      print(audio_metric_aggregation_by_tmp[k][0][i], ":")
      for u in audio_metric_aggregation_by_tmp[k][1]:
        print("\t", u, audio_metric_aggregation_by_tmp[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by FOO", audio_metric_aggregation_by_tmp[k][0], audio_metric_aggregation_by_tmp[k][1])

    print("")
    print("")

"""# MathML Analysis"""

MATHML_METRICS = [
    #"mathml_1",
    "mathml_2",
    #"mathml_3",
    #"mathml_4",
    #"mathml_5",
    #"mathml_6",
    #"mathml_7",
    #"mathml_8",
    #"mathml_9",
    #"mathml_10",
  ]

blocklisted_metrics = ["schema", "errors", "errors_js", "channel", "build_date", "ice_sd", "version", "country", "intl_keyboard_layout",
                      "screen_inner", "screen_outer", "screen_avail", "hw_group_count", "canvas", "prefs_zoom_count", "missing_fonts",
                      "screen_inverted_colors", "font_prefcolor_", "hw_gamepads", "voices_local_ssdeep", "voices_default", "mathml"]

if colab_config['mathml_autosegmentation']:
  for m in MATHML_METRICS:
    print("=" * 50)
    print("=" * 50)
    print(m)
    print("")
    try_to_auto_fit_segments(m, blocklisted_metrics, verbosity=1)

mathml_metric_aggregation_by_arch = calculate_aggregated_metrics_grouped_by_metric(MATHML_METRICS, "hw_cpu_arch")

for k in MATHML_METRICS:
  if len(metric_aggregation[k].keys()) != 1:
    print(k)
    print("-"*30)
    print("Total number of submissions by value")
    for v in metric_aggregation[k].keys():
      print(v, "-", metric_aggregation[k][v])

    bar_graph('Metric Value', 'Num Submissions', k, metric_aggregation[k], rotate_xlabels=True)
    print("")

    print("Total number of submissions by value by OS")
    for i in range(len(metric_aggregation_by_os[k][0])):
      print(metric_aggregation_by_os[k][0][i], ":")
      for u in metric_aggregation_by_os[k][1]:
        print("\t", u, metric_aggregation_by_os[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by OS", metric_aggregation_by_os[k][0], metric_aggregation_by_os[k][1])

    print("")
    print("")

    print("Total number of submissions by value by architecture")
    for i in range(len(mathml_metric_aggregation_by_arch[k][0])):
      print(mathml_metric_aggregation_by_arch[k][0][i], ":")
      for u in mathml_metric_aggregation_by_arch[k][1]:
        print("\t", u, mathml_metric_aggregation_by_arch[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by Arch", mathml_metric_aggregation_by_arch[k][0], mathml_metric_aggregation_by_arch[k][1])

    print("")
    print("")

"""# Media Capability Analysis"""

class mediaCapabilitiesFilter(Filter):
  def __init__(self, dataValues):
    media_capabilities_metrics = [
      "media_capabilities_not_efficient",
      "media_capabilities_not_smooth",
      "media_capabilities_unsupported",
    ]

    dataValues.media_capabilities_combined = f"{dataValues.media_capabilities_not_efficient} - {dataValues.media_capabilities_not_smooth} - {dataValues.media_capabilities_unsupported}"
    self.applied_effect = True

  def revert(self, dataValues):
    pass

# Apply the Filter

count_values_affected = 0
for d in all_data_values:
  if d.add_filter(mediaCapabilitiesFilter):
      count_values_affected += 1
  #d.pop_filter()
  pass

print(f"media capabilities filter took effect {count_values_affected} times")
print("")

print("Active Filters:")
print(all_data_values[0].list_filters())

MEDIA_METRICS = [
    #"media_capabilities_combined",
    #"media_capabilities_not_efficient",
    #"media_capabilities_not_smooth",
    "media_capabilities_unsupported",
  ]

blocklisted_metrics = [
    "schema", "errors", "errors_js", "channel", "build_date", "screen_inner", "locale_accept_language", "hw_gamepads",
    "intl_system_locale", "screen_outer", "screen_posy", "screen_posy", "font_", "intl_intl_locale", "screen_posx",
    "ice_sd", "country", "media_capabilities_", "prefs_general_overlay_scrollbars", "screen_orientation_angle", "prefs_pdf_viewer",
    "prefs_eme_enabled", "screen_avail", "audio_frames", "canvas_dpr", "prefs_zoom_count", "missing_fonts", "voices_default",
    "webgl_renderer_raw"
  ]

if colab_config['media_capabilities_autosegmentation']:
  for m in MEDIA_METRICS:
    print("=" * 50)
    print("=" * 50)
    print(m)
    print("")
    try_to_auto_fit_segments(m, blocklisted_metrics, verbosity=3)

MEDIA_METRICS = [
    #"media_capabilities_combined",
    #"media_capabilities_not_efficient",
    #"media_capabilities_not_smooth",
    "media_capabilities_unsupported",
  ]

def os_versioning(dv):
  if dv.os == "WINNT":
    return dv.os_version
  return dv.os

segmentation_metrics = [
    "os",
    ("os_versioning", os_versioning)
]

for m in MEDIA_METRICS:
  data = segment_data(m, segmentation_metrics)
  results = analyze_segmented_data(*data, verbose=True)

media_capabilities_metrics = [
    "media_capabilities_unsupported",
  ]

media_capabilities_metric_aggregation = calculate_aggregated_metrics(media_capabilities_metrics, verbose=True)
media_capabilities_metric_aggregation_by_os = calculate_aggregated_metrics_grouped_by_metric(media_capabilities_metrics, "os")
media_capabilities_metric_aggregation_by_arch = calculate_aggregated_metrics_grouped_by_metric(media_capabilities_metrics, "hw_cpu_arch")

for k in media_capabilities_metrics:
  if len(media_capabilities_metric_aggregation[k].keys()) != 1:
    print(k)
    print("-"*30)
    print("Total number of submissions by value")
    for v in media_capabilities_metric_aggregation[k].keys():
      print(v, "-", media_capabilities_metric_aggregation[k][v])

    bar_graph('Metric Value', 'Num Submissions', k, media_capabilities_metric_aggregation[k], rotate_xlabels=True)
    print("")

    print("Total number of submissions by value by OS")
    for i in range(len(media_capabilities_metric_aggregation_by_os[k][0])):
      print(media_capabilities_metric_aggregation_by_os[k][0][i], ":")
      for u in media_capabilities_metric_aggregation_by_os[k][1]:
        print("\t", u, media_capabilities_metric_aggregation_by_os[k][1][u][i])
    print("")

    stacked_bar_graph(k + " by OS", media_capabilities_metric_aggregation_by_os[k][0], media_capabilities_metric_aggregation_by_os[k][1])

    print("")
    print("")

    #print("Total number of submissions by value by architecture")
    #for i in range(len(metric_aggregation_by_arch[k][0])):
    #  print(metric_aggregation_by_arch[k][0][i], ":")
    #  for u in metric_aggregation_by_arch[k][1]:
    #    print("\t", u, metric_aggregation_by_arch[k][1][u][i])
    #print("")
    #
    #stacked_bar_graph(k + " by Arch", metric_aggregation_by_arch[k][0], metric_aggregation_by_arch[k][1])

    print("")
    print("")

for d in all_data_values:
  continue

  d.pop_filter()
  pass

print("Active Filters:")
print(all_data_values[0].list_filters())