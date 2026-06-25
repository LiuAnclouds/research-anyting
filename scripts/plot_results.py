#!/usr/bin/env python3
"""
Publication-quality plotting for ML research.
Generates: bar charts, ablation studies, training curves, heatmaps, embedding visualizations.
Uses colorblind-friendly palettes and vector output formats.
Usage: python plot_results.py --type bar --data plot_data.json --output figure.pdf
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse, json

NATURE_PALETTE = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#7E6148']

def set_style():
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'font.size': 10, 'axes.titlesize': 14, 'axes.labelsize': 12,
        'xtick.labelsize': 10, 'ytick.labelsize': 10, 'legend.fontsize': 10,
        'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
        'axes.spines.top': False, 'axes.spines.right': False,
        'lines.linewidth': 1.5, 'lines.markersize': 6
    })

def bar_chart(methods, scores, errors=None, xlabel='Method', ylabel='Score', title=None, save_path=None):
    set_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(methods))
    colors = NATURE_PALETTE[:len(methods)]
    if errors is None:
        errors = [0] * len(scores)
    bars = ax.bar(x, scores, yerr=errors, capsize=3, color=colors, edgecolor='white', linewidth=0.5)
    best_idx = np.argmax(scores)
    bars[best_idx].set_edgecolor('black')
    bars[best_idx].set_linewidth(1.5)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=30, ha='right')
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    if title:
        ax.set_title(title)
    for i, (s, e) in enumerate(zip(scores, errors)):
        ax.text(i, s + e + 0.005, f'{s:.3f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
        print(f"Saved: {save_path}")
    plt.close()

def ablation_hbar(components, full_score, ablated_scores, ylabel='Score', title='Ablation Study', save_path=None):
    set_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    drops = [full_score - s for s in ablated_scores]
    names = ['Full Model'] + components
    scores = [full_score] + ablated_scores
    colors = ['#3C5488'] + ['#E64B35'] * len(components)
    y_pos = np.arange(len(names))[::-1]
    ax.barh(y_pos, scores, color=colors, edgecolor='white')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel(ylabel)
    if title:
        ax.set_title(title)
    for i, (s, d) in enumerate(zip(ablated_scores, drops)):
        ax.text(s + 0.002, y_pos[i + 1], f'-{d:.3f}', va='center', fontsize=9, color='#E64B35')
    for i, s in enumerate(scores):
        ax.text(s + 0.002, y_pos[i], f'{s:.3f}', va='center', fontsize=9)
    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
    plt.close()

def training_curves(epochs, train_loss, val_metric, metric_name='Score', title=None, save_path=None):
    set_style()
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(epochs, train_loss, color='#E64B35', label='Training Loss', linewidth=1.5)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss', color='#E64B35')
    ax1.tick_params(axis='y', labelcolor='#E64B35')
    ax2 = ax1.twinx()
    ax2.plot(epochs, val_metric, color='#3C5488', label=f'Validation {metric_name}', linewidth=1.5)
    ax2.set_ylabel(f'Validation {metric_name}', color='#3C5488')
    ax2.tick_params(axis='y', labelcolor='#3C5488')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    if title:
        ax1.set_title(title)
    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
    plt.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Publication-Quality ML Plots')
    p.add_argument('--type', required=True, choices=['bar', 'ablation', 'curve'])
    p.add_argument('--data', required=True, help='JSON data file')
    p.add_argument('--output', required=True, help='Output figure path (.pdf)')
    a = p.parse_args()
    data = json.load(open(a.data))
    set_style()
    if a.type == 'bar':
        bar_chart(data['methods'], data['scores'], data.get('errors'), xlabel=data.get('xlabel', 'Method'),
                  ylabel=data.get('ylabel', 'Score'), title=data.get('title'), save_path=a.output)
    elif a.type == 'ablation':
        ablation_hbar(data['components'], data['full_score'], data['ablated_scores'],
                      ylabel=data.get('ylabel', 'Score'), title=data.get('title'), save_path=a.output)
    elif a.type == 'curve':
        training_curves(data['epochs'], data['train_loss'], data['val_metric'],
                        metric_name=data.get('metric_name', 'Score'), title=data.get('title'), save_path=a.output)