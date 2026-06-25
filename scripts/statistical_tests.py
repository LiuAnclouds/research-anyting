#!/usr/bin/env python3
"""
Statistical tests for ML research evaluation.
Supports: Wilcoxon signed-rank, Mann-Whitney U, Bonferroni correction, effect size.
Usage: python statistical_tests.py --data results.json --method-a "Ours" --method-b "Baseline"
"""
import numpy as np
from scipy import stats
import argparse, json

def wilcoxon_signed_rank(scores_a, scores_b, alpha=0.05):
    """Paired Wilcoxon signed-rank test across datasets."""
    statistic, p_value = stats.wilcoxon(scores_a, scores_b)
    significant = p_value < alpha
    return {'test': 'Wilcoxon signed-rank', 'statistic': float(statistic), 'p_value': float(p_value),
            'significant': bool(significant), 'alpha': alpha}

def mann_whitney_u(scores_a, scores_b, alpha=0.05):
    """Unpaired Mann-Whitney U test."""
    statistic, p_value = stats.mannwhitneyu(scores_a, scores_b, alternative='two-sided')
    significant = p_value < alpha
    return {'test': 'Mann-Whitney U', 'statistic': float(statistic), 'p_value': float(p_value),
            'significant': bool(significant), 'alpha': alpha}

def cohens_d(scores_a, scores_b):
    """Cohen's d effect size."""
    diff = np.mean(scores_a) - np.mean(scores_b)
    pooled_std = np.sqrt((np.std(scores_a, ddof=1)**2 + np.std(scores_b, ddof=1)**2) / 2)
    return diff / (pooled_std + 1e-10)

def bonferroni_correction(p_values, alpha=0.05):
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    corrected_alpha = alpha / n
    return [{'original_p': float(p), 'corrected_alpha': float(corrected_alpha),
             'significant_after_correction': bool(p < corrected_alpha)} for p in p_values]

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Statistical Tests for ML Research')
    p.add_argument('--data', required=True, help='JSON file with results')
    p.add_argument('--method-a', required=True, help='Method A name')
    p.add_argument('--method-b', required=True, help='Method B name')
    p.add_argument('--test', default='wilcoxon', choices=['wilcoxon', 'mannwhitney', 'both'])
    p.add_argument('--alpha', type=float, default=0.05)
    a = p.parse_args()

    data = json.load(open(a.data))
    scores_a = np.array(data[a.method_a])
    scores_b = np.array(data[a.method_b])

    print(f"Comparing {a.method_a} vs {a.method_b}")
    print(f"  {a.method_a}: {np.mean(scores_a):.4f} ± {np.std(scores_a):.4f}")
    print(f"  {a.method_b}: {np.mean(scores_b):.4f} ± {np.std(scores_b):.4f}")
    print(f"  Cohen's d: {cohens_d(scores_a, scores_b):.4f}")

    if a.test in ('wilcoxon', 'both'):
        r = wilcoxon_signed_rank(scores_a, scores_b, a.alpha)
        print(f"  Wilcoxon: statistic={r['statistic']:.4f}, p={r['p_value']:.4f}, significant={r['significant']}")

    if a.test in ('mannwhitney', 'both'):
        r = mann_whitney_u(scores_a, scores_b, a.alpha)
        print(f"  Mann-Whitney U: statistic={r['statistic']:.4f}, p={r['p_value']:.4f}, significant={r['significant']}")