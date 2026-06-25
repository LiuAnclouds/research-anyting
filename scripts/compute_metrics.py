#!/usr/bin/env python3
"""
Standard evaluation metrics for ML research.
Supports: AUC-ROC, AUC-PR, F1, Precision@K, Recall@K, and multi-seed aggregation.
Usage: python compute_metrics.py --pred predictions.npy --label labels.npy [--output results.json]
"""
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve, confusion_matrix
import argparse, json

def compute_all_metrics(y_true, y_pred, threshold=None):
    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()
    roc, pr = roc_auc_score(y_true, y_pred), average_precision_score(y_true, y_pred)
    if threshold is None:
        p, r, t = precision_recall_curve(y_true, y_pred)
        f1s = 2 * p * r / (p + r + 1e-10)
        threshold = t[np.argmax(f1s)]
    yb = (y_pred >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, yb).ravel()
    pre = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * pre * rec / (pre + rec) if (pre + rec) > 0 else 0
    k = max(1, int(0.05 * len(y_true)))
    topk = np.argsort(y_pred)[-k:]
    return {
        'auc_roc': round(roc, 4), 'auc_pr': round(pr, 4),
        'precision': round(pre, 4), 'recall': round(rec, 4), 'f1': round(f1, 4),
        'threshold': round(threshold, 4),
        f'precision@{k}': round(y_true[topk].mean(), 4),
        f'recall@{k}': round(y_true[topk].sum() / (y_true.sum() + 1e-10), 4),
        'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn)
    }

def compute_multi_seed(all_preds, all_labels):
    results = [compute_all_metrics(l, p) for p, l in zip(all_preds, all_labels)]
    agg = {}
    for key in results[0]:
        if key in ('tp', 'fp', 'tn', 'fn', 'threshold'):
            continue
        vals = [r[key] for r in results]
        agg[key] = f"{np.mean(vals):.4f} ± {np.std(vals):.4f}"
    return agg

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='ML Research Evaluation Metrics')
    p.add_argument('--pred', required=True, help='Path to predictions .npy')
    p.add_argument('--label', required=True, help='Path to labels .npy')
    p.add_argument('--threshold', type=float, help='Classification threshold')
    p.add_argument('--output', help='Output JSON file')
    a = p.parse_args()
    m = compute_all_metrics(np.load(a.label), np.load(a.pred), a.threshold)
    print("=" * 50)
    for k, v in m.items():
        print(f"  {k:20s}: {v}")
    print("=" * 50)
    if a.output:
        json.dump(m, open(a.output, 'w'), indent=2)
        print(f"Saved to {a.output}")