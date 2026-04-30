#!/usr/bin/env python3
"""
Define the Cohort Fitness function

The purpose of this function is to have an objective way to take different cohort distributions and say "This cohort distribution is better than this other cohort distribution".

I don't have a strong opinion that this is the best fitness function, if you think something would be better, go for it.
"""

"""
    Calculate the total number of users.
    For each cohort size, calculate the percentage of users in cohorts of that size.
    Assign weights to each cohort size based on the percentage of users it represents.
    Calculate the weighted average of the cohort sizes to get the score.

    This function assumes it will only be comparing values that were calculated from the same number of total users.

    Larger is better
"""

def cohort_fitness_1(fingerprints):
  total_users = sum(fingerprints.values())
  cohort_sizes = set(fingerprints.values())
  weighted_sum = 0

  for size in cohort_sizes:
      percentage = (size * list(fingerprints.values()).count(size)) #/ total_users
      weighted_sum += size * percentage

  score = weighted_sum / total_users
  return score

def cohort_fitness_2(fingerprints):
  " This treats each cohort as a competitor and calculates the HHI Index"
  total_users = sum(fingerprints.values())

  competitor_market_share_proportion = []
  for fp in fingerprints:
      competitor_market_share_proportion.append(fingerprints[fp] / total_users)

  score = 0
  for proportion in competitor_market_share_proportion:
     score += proportion ** 2

  return score

cohort_fitness = cohort_fitness_2


def cohort_fitness_from_histogram(histogram):
    """HHI index from a {cohort_size: num_cohorts} histogram (no per-hash keys needed)."""
    total_users = sum(size * count for size, count in histogram.items())
    if total_users == 0:
        return 0
    score = 0
    for size, count in histogram.items():
        proportion = size / total_users
        score += count * proportion ** 2
    return score


def cohort_fitness_excluding_singletons(fingerprints):
    """HHI2: HHI computed after removing singleton cohorts (count == 1)."""
    filtered = {fp: count for fp, count in fingerprints.items() if count > 1}
    if not filtered:
        return 0
    return cohort_fitness(filtered)


def cohort_fitness_from_histogram_excluding_singletons(histogram):
    """HHI2: HHI from histogram after removing the cohort_size=1 entry."""
    filtered = {size: count for size, count in histogram.items() if size > 1}
    if not filtered:
        return 0
    return cohort_fitness_from_histogram(filtered)


def cohort_p50(fingerprints):
    """Median cohort size among non-unique users (user-weighted).

    From a {hash: count} dict, considers only cohorts with count > 1,
    then finds the cohort size that the median non-unique user belongs to.
    """
    nonunique = sorted(c for c in fingerprints.values() if c > 1)
    if not nonunique:
        return 0
    total = sum(nonunique)
    target = total * 0.5
    cumulative = 0
    for c in nonunique:
        cumulative += c
        if cumulative >= target:
            return c
    return nonunique[-1]


def cohort_p50_from_histogram(histogram):
    """Median cohort size among non-unique users (user-weighted), from histogram.

    From a {cohort_size: num_cohorts} histogram, considers only sizes > 1,
    then finds the cohort size that the median non-unique user belongs to.
    """
    # Build sorted list of (size, total_users_at_size) for non-unique cohorts
    entries = sorted((size, size * count)
                     for size, count in histogram.items() if size > 1)
    if not entries:
        return 0
    total = sum(users for _, users in entries)
    target = total * 0.5
    cumulative = 0
    for size, users in entries:
        cumulative += users
        if cumulative >= target:
            return size
    return entries[-1][0]


def cohort_detailed_stats(fingerprints):
    """Compute cohort statistics from a {hash: count} dict.

    Returns a dict with:
      total_users, total_cohorts, unique_users, pct_unique,
      hhi, hhi2, p50
    """
    counts = list(fingerprints.values())
    total_users = sum(counts)
    total_cohorts = len(counts)
    unique_users = sum(1 for c in counts if c == 1)

    return {
        'total_users': total_users,
        'total_cohorts': total_cohorts,
        'unique_users': unique_users,
        'pct_unique': (100.0 * unique_users / total_users) if total_users else 0,
        'hhi': cohort_fitness(fingerprints),
        'hhi2': cohort_fitness_excluding_singletons(fingerprints),
        'p50': cohort_p50(fingerprints),
    }

    return result

meta_scenarios = []

meta_scenarios.append([])
meta_scenarios[0].append({'cohort1': 39, 'cohort2': 1})
meta_scenarios[0].append({'cohort1': 35, 'cohort2': 5})
meta_scenarios[0].append({'cohort1': 20, 'cohort2': 19, 'cohort3': 1})
meta_scenarios[0].append({'cohort1': 5, 'cohort2': 5, 'cohort3': 5, 'cohort4': 5, 'cohort5': 5, 'cohort6': 5, 'cohort7': 5, 'cohort8': 5})
meta_scenarios[0].append({'cohort1': 2, 'cohort2': 2, 'cohort3': 2, 'cohort4': 2, 'cohort5': 2, 'cohort6': 2, 'cohort7': 2, 'cohort8': 2, 'cohort9': 2, 'cohort10': 2,
             'cohort11': 2, 'cohort12': 2, 'cohort13': 2, 'cohort14': 2, 'cohort15': 2, 'cohort16': 1, 'cohort17': 1, 'cohort18': 1, 'cohort19': 1, 'cohort20': 1,
             'cohort21': 1, 'cohort22': 1, 'cohort23': 1, 'cohort24': 1, 'cohort25': 1, })


meta_scenarios.append([])
meta_scenarios[1].append({'cohort1': 149, 'cohort2': 1})
meta_scenarios[1].append({'cohort1': 140, 'cohort2': 10})
meta_scenarios[1].append({'cohort1': 120, 'cohort2': 20, 'cohort3': 10})
meta_scenarios[1].append({'cohort1': 100, 'cohort2': 25, 'cohort3': 25})
meta_scenarios[1].append({'cohort1': 75, 'cohort2': 20, 'cohort3': 15, 'cohort4': 10, 'cohort5': 10, 'cohort6': 10, 'cohort7': 10})
meta_scenarios[1].append({'cohort1': 50, 'cohort2': 25, 'cohort3': 20, 'cohort4': 15, 'cohort5': 10, 'cohort6': 10, 'cohort7': 10, 'cohort8': 10})
meta_scenarios[1].append({f'cohort{i+1}': 15 for i in range(10)})         # 10 × 15 = 150
meta_scenarios[1].append({f'cohort{i+1}': 5 for i in range(30)})          # 30 × 5 = 150


for scenario in meta_scenarios:
    assert len(set([sum(s.values()) for s in scenario])) == 1, "Some scenario does not have the same number of total users as the other scenarios. Distribution:" + str(set([sum(s.values()) for s in scenario]))
    for i in range(len(scenario)-1):
        assert cohort_fitness(scenario[i]) > cohort_fitness(scenario[i+1]), f"Scenario {i} is not better than Scenario {i+1}:\n  {cohort_fitness(scenario[i])} vs {cohort_fitness(scenario[i+1])}\n  {scenario[i]}\n  vs\n  {scenario[i+1]}"

if False:
  for index, scenario in enumerate(meta_scenarios):
      print(f"Scenario {index}")
      for i in range(len(scenario)):
          print(f"  {cohort_fitness(scenario[i])}: {scenario[i]}")
