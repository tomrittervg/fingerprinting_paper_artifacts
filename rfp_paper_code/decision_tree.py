import io
import os
import threading
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import config

# matplotlib is not thread-safe; all plot calls must hold this lock.
_matplotlib_lock = threading.Lock()


def run_decision_tree_analysis(all_data_values, default_subset, metrics_to_visualize, canvas_metrics, target_metrics, preferred_features, n_workers=8):
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.exceptions import UndefinedMetricWarning
    from sklearn import tree as sktree

    # 0. Prepare the data
    sklearn_metrics_to_analyze = target_metrics

    # Remove DataValues that have a bad value for any of the target metrics
    bad_keys = {"", "{}", None, "None"}
    filtered_data_values = []
    for dv in all_data_values:
        has_bad = False
        for metric in sklearn_metrics_to_analyze:
            val = getattr(dv, metric, None)
            if val in bad_keys:
                has_bad = True
                break
        if not has_bad:
            filtered_data_values.append(dv)
    print(f"Filtered out {len(all_data_values) - len(filtered_data_values)} DataValues with bad/missing target metric values.")
    print("  Left with ", len(filtered_data_values), "DataValues for sklearn analysis.")
    print("")
    all_data_values = filtered_data_values

    from segmentation import is_segmentation_blocklisted
    metrics_to_sklearn_from = [m for m in default_subset if not is_segmentation_blocklisted(m)]

    print(f"Using {len(metrics_to_sklearn_from)} out of {len(metrics_to_visualize)} metrics for sklearn analysis.")
    intersection = set(preferred_features) & set(metrics_to_sklearn_from)
    print(f"  Intersection of preferred features and metrics_to_sklearn_from: {intersection} (count: {len(intersection)})")
    print("")

    def _clean(mat):
        """Return a copy of a sparse matrix safe for sklearn (no inf/NaN, float32-safe)."""
        mat = mat.copy()
        mat.data = np.nan_to_num(mat.data, nan=0.0, posinf=0.0, neginf=0.0)
        np.clip(mat.data, -1e30, 1e30, out=mat.data)
        return mat

    def _analyze_one_metric(metric_to_analyze):
        """Run the full sklearn pipeline for one target metric.
        Returns buffered stdout text so the caller can flush in order."""
        buf = io.StringIO()

        def _print(*args, **kwargs):
            print(*args, file=buf, **kwargs)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

            _print("Performing sklearn analysis on", metric_to_analyze)

            # 1. Build feature dicts & labels
            _print("  Step 1: Building feature dicts and labels...")
            MINIMUM_LABEL_FREQUENCY = 50
            label_counts = {}
            for dv in all_data_values:
                label = getattr(dv, metric_to_analyze)
                label_counts[label] = label_counts.get(label, 0) + 1

            # Skip early if fewer than 2 labels have enough data — no need to vectorize
            frequent_labels = {l for l, c in label_counts.items() if c >= MINIMUM_LABEL_FREQUENCY}
            if len(frequent_labels) < 2:
                _print(f"  Skipping {metric_to_analyze} — only {len(frequent_labels)} distinct label value(s) with sufficient frequency, nothing to classify.")
                return buf.getvalue()

            feature_dicts = []
            labels = []
            for dv in all_data_values:
                label = getattr(dv, metric_to_analyze)
                if label_counts[label] < MINIMUM_LABEL_FREQUENCY:
                    continue
                labels.append(label)
                feat = {}
                for attr in metrics_to_sklearn_from:
                    if attr == metric_to_analyze:
                        continue
                    val = getattr(dv, attr, None)
                    if isinstance(val, (int, float, str, bool)):
                        feat[attr] = val
                    else:
                        feat[attr] = str(val)
                feature_dicts.append(feat)

            # 2. Vectorize into X matrix
            _print("  Step 2: Vectorizing features into X matrix...")
            vec = DictVectorizer(sparse=True)
            X = _clean(vec.fit_transform(feature_dicts))
            y = np.array([str(l) for l in labels])

            if len(np.unique(y)) < 2:
                _print(f"  Skipping {metric_to_analyze} — only 1 distinct label value, nothing to classify.")
                return buf.getvalue()

            # 3. Split into train & test
            _print("  Step 3: Splitting into train and test sets...")
            label_counts_y = Counter(y)
            mask = [label_counts_y[label] > 1 for label in y]
            X = X[mask]
            y = y[mask]
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )

            # 4a. Train a depth=1 stump using only the preferred features
            _print("  Step 4a: Training depth=1 stump on preferred features...")
            feature_names = vec.get_feature_names_out()
            preferred_indices = [
                i for i, name in enumerate(feature_names)
                if any(name.startswith(prefix) for prefix in preferred_features)
            ]
            if not preferred_indices:
                raise Exception("  Warning: None of the preferred features found in feature set.")

            X_train_pref = X_train[:, preferred_indices]
            X_test_pref = X_test[:, preferred_indices]
            stump = DecisionTreeClassifier(max_depth=1, random_state=42)
            stump.fit(_clean(X_train_pref), y_train)
            stump_pred = stump.predict(X_test_pref)
            config.log_and_file(f"{metric_to_analyze}_stump_analysis.txt", "  Stump Accuracy (preferred features):", accuracy_score(y_test, stump_pred))
            config.write_file(f"{metric_to_analyze}_stump_analysis.txt", classification_report(y_test, stump_pred))

            # 4b. Train a tree on the remaining features, after splitting by the stump
            _print("  Step 4b: Training tree on remaining features after stump split...")
            stump_leaf = stump.apply(X_test_pref)
            unique_leaves = np.unique(stump_leaf)
            stump_leaves = []
            for leaf in unique_leaves:
                idx = np.where(stump_leaf == leaf)[0]
                if len(idx) < 10:
                    _print(f"    Leaf {leaf}: too few samples ({len(idx)}), skipping.")
                    continue
                _print(f"    Leaf {leaf}: training tree on {len(idx)} samples.")
                remaining_indices = [i for i in range(X.shape[1]) if i not in preferred_indices]
                stump_leaf_train = stump.apply(X_train_pref)
                train_idx = np.where(stump_leaf_train == leaf)[0]
                if len(train_idx) < 10:
                    _print(f"    Leaf {leaf}: too few training samples ({len(train_idx)}), skipping.")
                    continue
                X_train_remain = X_train[train_idx][:, remaining_indices]
                y_train_remain = y_train[train_idx]
                X_test_remain = X_test[idx][:, remaining_indices]
                y_test_remain = y_test[idx]
                clf = DecisionTreeClassifier(max_depth=5, random_state=42)
                stump_leaves.append(clf)
                clf.fit(_clean(X_train_remain), y_train_remain)
                y_pred = clf.predict(X_test_remain)
                config.log_and_file(f"{metric_to_analyze}_leaf_{leaf}_analysis.txt", f"    Leaf {leaf} - Remaining Features Accuracy:", accuracy_score(y_test_remain, y_pred))
                config.write_file(f"{metric_to_analyze}_leaf_{leaf}_analysis.txt", classification_report(y_test_remain, y_pred))

            # 5. Evaluate full model for comparison
            _print("  Step 5: Training and evaluating full model for comparison...")
            clf_full = DecisionTreeClassifier(max_depth=5, random_state=42)
            clf_full.fit(_clean(X_train), y_train)
            y_pred_full = clf_full.predict(X_test)
            config.log_and_file(f"{metric_to_analyze}_full_analysis.txt", "  Full Model Accuracy:", accuracy_score(y_test, y_pred_full))
            config.write_file(f"{metric_to_analyze}_full_analysis.txt", classification_report(y_test, y_pred_full))

            # 6. Inspect learned rules
            _print("  Step 6: Inspecting learned rules...")

            def print_decision_tree(clf, feat_names, log_file):
                children_left = clf.tree_.children_left
                children_right = clf.tree_.children_right
                feature = clf.tree_.feature
                threshold = clf.tree_.threshold
                value = clf.tree_.value

                def recurse(node, depth=0):
                    indent = "  " * depth
                    if children_left[node] == children_right[node]:
                        config.write_file(log_file, f"{indent}Leaf: value={value[node]}")
                        config.write_file(log_file, "")
                    else:
                        fname = feat_names[feature[node]]
                        if threshold[node] == 0.5:
                            config.write_file(log_file, f"{indent}if {fname}:")
                            recurse(children_left[node], depth + 1)
                            config.write_file(log_file, f"{indent}else:  # if not {fname}")
                            recurse(children_right[node], depth + 1)
                        else:
                            config.write_file(log_file, f"{indent}if {fname} <= {threshold[node]:.4f}:")
                            recurse(children_left[node], depth + 1)
                            config.write_file(log_file, f"{indent}else:  # if {fname} > {threshold[node]:.4f}")
                            recurse(children_right[node], depth + 1)

                recurse(0)

            print_decision_tree(stump, [feature_names[i] for i in preferred_indices],
                                log_file=f"{metric_to_analyze}_prioritizedfeatures_root_decision_tree.txt")
            for idx, clf_leaf in enumerate(stump_leaves):
                print_decision_tree(clf_leaf,
                                    [feature_names[i] for i in range(len(feature_names)) if i not in preferred_indices],
                                    log_file=f"{metric_to_analyze}_prioritizedfeatures_leaf_{idx+1}_decision_tree.txt")

            # Plots — serialized via lock since matplotlib is not thread-safe
            with _matplotlib_lock:
                fig_width = 10 * (1 + len(stump_leaves))
                fig, axes = plt.subplots(1, 1 + len(stump_leaves), figsize=(fig_width, 12))
                sktree.plot_tree(stump, feature_names=[feature_names[i] for i in preferred_indices],
                                 class_names=[str(c) for c in np.unique(y)], filled=True, fontsize=14,
                                 ax=axes[0] if len(stump_leaves) > 0 else axes)
                axes[0].set_title("Stump (Root)", fontsize=18)
                for idx, clf_leaf in enumerate(stump_leaves):
                    sktree.plot_tree(clf_leaf,
                                     feature_names=[feature_names[i] for i in range(len(feature_names)) if i not in preferred_indices],
                                     class_names=[str(c) for c in np.unique(y)], filled=True, fontsize=14,
                                     ax=axes[idx + 1])
                    axes[idx + 1].set_title(f"Leaf {idx+1} Subtree", fontsize=18)
                plt.tight_layout()
                img_path = os.path.join(config.OUTPUT_FOLDER, f"{metric_to_analyze}_prioritizedfeatures_tree.png")
                try:
                    plt.savefig(img_path, dpi=200)
                    _print(f"Combined tree image saved to {img_path}")
                except Exception as e:
                    _print(f"  Warning: could not save combined tree image: {e}")
                plt.close(fig)

            # Compose combined full decision tree text file
            root_file = os.path.join(config.OUTPUT_FOLDER, f"{metric_to_analyze}_prioritizedfeatures_root_decision_tree.txt")
            leaf1_file = os.path.join(config.OUTPUT_FOLDER, f"{metric_to_analyze}_prioritizedfeatures_leaf_1_decision_tree.txt")
            leaf2_file = os.path.join(config.OUTPUT_FOLDER, f"{metric_to_analyze}_prioritizedfeatures_leaf_2_decision_tree.txt")
            full_file = os.path.join(config.OUTPUT_FOLDER, f"{metric_to_analyze}_prioritizedfeatures_full_decision_tree.txt")
            try:
                root_lines = open(root_file).readlines()
            except Exception:
                root_lines = []
            try:
                leaf1_lines = open(leaf1_file).readlines()
            except Exception:
                leaf1_lines = []
            try:
                leaf2_lines = open(leaf2_file).readlines()
            except Exception:
                leaf2_lines = []
            with open(full_file, "w") as wf:
                wf.writelines(root_lines[:3])
                for line in leaf1_lines:
                    wf.write("  " + line)
                wf.writelines(root_lines[3:])
                for line in leaf2_lines:
                    wf.write("  " + line)

            print_decision_tree(clf_full, feature_names,
                                log_file=f"{metric_to_analyze}_fullfeatureset_decision_tree.txt")

            with _matplotlib_lock:
                fig_full, ax_full = plt.subplots(figsize=(40, 24))
                sktree.plot_tree(clf_full, feature_names=feature_names,
                                 class_names=[str(c) for c in np.unique(y)], filled=True, fontsize=16,
                                 ax=ax_full)
                ax_full.set_title("Full Decision Tree", fontsize=24)
                img_full_path = os.path.join(config.OUTPUT_FOLDER, f"{metric_to_analyze}_fullfeatureset_tree.png")
                plt.tight_layout()
                try:
                    plt.savefig(img_full_path, dpi=200)
                    _print(f"Full decision tree image saved to {img_full_path}")
                except Exception as e:
                    _print(f"  Warning: could not save full tree image: {e}")
                plt.close(fig_full)

        return buf.getvalue()

    # Run all metrics in parallel; flush each metric's buffered output in submission order.
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        for output in executor.map(_analyze_one_metric, sklearn_metrics_to_analyze):
            print(output, end="")

    return all_data_values
