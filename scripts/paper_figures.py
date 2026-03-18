#!/usr/bin/env python3
"""
Generate figures for the Linear A structural analysis paper.

Figures:
  1. Sign count distribution by support type (box plot)
  2. Non-monotonic information density gradient (bar chart)
  3. Dependency graph hub analysis (bar chart of in-degree vs out-degree)
  4. Sign classification summary (stacked bar)
  5. Site vocabulary coverage (asymmetric coverage vs Jaccard)
"""

import json
import csv
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_JSON = ROOT / "data" / "corpus" / "canonical_corpus.json"
PHASE3_JSON = ROOT / "analysis" / "phase3_dependency_graph.json"
PHASE4_JSON = ROOT / "analysis" / "phase4_sign_classification.json"
PHASE5_JSON = ROOT / "analysis" / "phase5_site_concentration.json"
FIG_DIR = ROOT / "figures"

LA_START, LA_END = 0x10600, 0x1077F
EDITORIAL = {0x1076B, 0x1076C, 0x1076D, 0x1076E, 0x1076F}

FIG_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})


def load_corpus():
    with open(CORPUS_JSON) as f:
        return json.load(f)


def count_signs(text):
    return sum(1 for ch in text if LA_START <= ord(ch) <= LA_END and ord(ch) not in EDITORIAL)


# ── Figure 1: Sign count by support type ──────────────────────────────────

def fig1_support_type_boxplot(corpus):
    support_lengths = defaultdict(list)
    for insc in corpus:
        support = insc.get('support', 'Unknown')
        n = count_signs(insc.get('signs_unicode', ''))
        if n > 0:
            support_lengths[support].append(n)

    # Filter to supports with N >= 10
    supports = [(s, vals) for s, vals in support_lengths.items() if len(vals) >= 10]
    supports.sort(key=lambda x: np.median(x[1]))

    fig, ax = plt.subplots(figsize=(10, 5))
    labels = [f"{s}\n(N={len(v)})" for s, v in supports]
    data = [v for _, v in supports]

    bp = ax.boxplot(data, labels=labels, patch_artist=True, showfliers=True,
                    flierprops=dict(marker='.', markersize=3, alpha=0.4))

    colors = []
    portable = {'Stone vessel', 'Stone object', 'Metal object', 'Clay vessel'}
    for s, _ in supports:
        if s in portable:
            colors.append('#e74c3c')  # red for portable
        elif s in {'Nodule', 'Sealing'}:
            colors.append('#3498db')  # blue for room-bound
        elif s in {'Tablet', 'Roundel', 'Lames (short thin tablet)'}:
            colors.append('#2ecc71')  # green for building-bound
        else:
            colors.append('#95a5a6')  # gray for other

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('Signs per inscription')
    ax.set_title('Information Density by Support Type')
    ax.tick_params(axis='x', rotation=45)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#3498db', alpha=0.7, label='Room-bound (nodules, sealings)'),
        Patch(facecolor='#2ecc71', alpha=0.7, label='Building-bound (tablets, roundels)'),
        Patch(facecolor='#e74c3c', alpha=0.7, label='Portable (stone/metal/clay vessels)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left')

    fig.savefig(FIG_DIR / 'fig1_support_type_boxplot.png')
    fig.savefig(FIG_DIR / 'fig1_support_type_boxplot.pdf')
    plt.close(fig)
    print(f'Saved fig1')


# ── Figure 2: Non-monotonic gradient ──────────────────────────────────────

def fig2_mobility_gradient(corpus):
    levels = {
        'L1: Room-bound\n(nodules, sealings)': {'Nodule', 'Sealing'},
        'L2: Building-bound\n(tablets, roundels)': {'Tablet', 'Roundel', 'Lames (short thin tablet)'},
        'L3: Intra-site\n(clay vessels, graffiti)': {'Clay vessel', 'Architecture', 'Graffito', 'Inked inscription'},
        'L4: Inter-site\n(stone/metal vessels)': {'Stone vessel', 'Metal object', 'Stone object', 'ivory object'},
    }

    level_data = {}
    for label, supports in levels.items():
        vals = []
        for insc in corpus:
            if insc.get('support') in supports:
                n = count_signs(insc.get('signs_unicode', ''))
                if n > 0:
                    vals.append(n)
        level_data[label] = vals

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart of means
    labels = list(level_data.keys())
    means = [np.mean(v) for v in level_data.values()]
    medians = [np.median(v) for v in level_data.values()]
    ns = [len(v) for v in level_data.values()]
    sems = [np.std(v) / np.sqrt(len(v)) for v in level_data.values()]

    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']
    bars = ax1.bar(range(4), means, yerr=sems, color=colors, alpha=0.8, capsize=5)
    ax1.set_xticks(range(4))
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel('Mean signs per inscription')
    ax1.set_title('Information Density by Mobility Level')

    # Annotate with N
    for i, (bar, n, m) in enumerate(zip(bars, ns, means)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'μ={m:.1f}\nN={n}', ha='center', va='bottom', fontsize=8)

    # Arrow showing non-monotonicity
    ax1.annotate('', xy=(2, means[2]+0.5), xytext=(1, means[1]+0.5),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax1.text(1.5, max(means[1], means[2]) + 1.5, 'Non-monotonic\ndrop',
            ha='center', fontsize=9, color='red', style='italic')

    # Box plot
    bp = ax2.boxplot(list(level_data.values()), labels=[f'L{i+1}' for i in range(4)],
                     patch_artist=True, showfliers=True,
                     flierprops=dict(marker='.', markersize=3, alpha=0.4))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax2.set_ylabel('Signs per inscription')
    ax2.set_title('Distribution by Mobility Level')

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig2_mobility_gradient.png')
    fig.savefig(FIG_DIR / 'fig2_mobility_gradient.pdf')
    plt.close(fig)
    print('Saved fig2')


# ── Figure 3: Dependency graph hub structure ──────────────────────────────

def fig3_hub_structure():
    with open(PHASE3_JSON) as f:
        data = json.load(f)

    hubs = data['hub_stats'][:20]

    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(hubs))
    width = 0.25

    in_deg = [h['in_degree'] for h in hubs]
    out_deg = [h['out_degree'] for h in hubs]
    mut_deg = [h['mutual_degree'] for h in hubs]

    ax.bar(x - width, in_deg, width, label='In-degree', color='#e74c3c', alpha=0.8)
    ax.bar(x, mut_deg, width, label='Mutual', color='#f39c12', alpha=0.8)
    ax.bar(x + width, out_deg, width, label='Out-degree', color='#3498db', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([h['sign'] for h in hubs], rotation=45, fontsize=8)
    ax.set_ylabel('Edge count')
    ax.set_title('Top 20 Signs by Dependency Graph Degree\n(Hub-spoke topology: high in-degree, zero out-degree)')
    ax.legend()

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig3_hub_structure.png')
    fig.savefig(FIG_DIR / 'fig3_hub_structure.pdf')
    plt.close(fig)
    print('Saved fig3')


# ── Figure 4: Sign classification ─────────────────────────────────────────

def fig4_classification():
    with open(PHASE4_JSON) as f:
        data = json.load(f)

    summary = data['summary']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Pie chart of classifiable signs
    cats = ['Core Modifier', 'Slot-Restricted', 'Singleton Root', 'Commodity', 'Unclassified']
    vals = [summary['core_modifier'], summary['slot_restricted'],
            summary['singleton_root'], summary['commodity'], summary['unclassified']]
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#95a5a6']

    ax1.pie(vals, labels=cats, colors=colors, autopct='%1.0f%%', startangle=90)
    ax1.set_title(f'Classifiable Signs (N={summary["classifiable_signs"]})\nSigns with ≥10 tokens')

    # Full inventory breakdown
    cats2 = ['Core Modifier\n(36)', 'Slot-Restricted\n(9)', 'Singleton Root\n(3)',
             'Commodity\n(14)', 'Unclassified\n(45)', 'Insufficient Data\n(215)']
    vals2 = [36, 9, 3, 14, 45, 215]
    colors2 = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#95a5a6', '#bdc3c7']

    ax2.barh(range(len(cats2)), vals2, color=colors2, alpha=0.8)
    ax2.set_yticks(range(len(cats2)))
    ax2.set_yticklabels(cats2)
    ax2.set_xlabel('Number of signs')
    ax2.set_title(f'Full Sign Inventory (N={summary["total_signs"]})')
    ax2.invert_yaxis()

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig4_classification.png')
    fig.savefig(FIG_DIR / 'fig4_classification.pdf')
    plt.close(fig)
    print('Saved fig4')


# ── Figure 5: Site vocabulary coverage ─────────────────────────────────────

def fig5_site_coverage(corpus):
    site_vocab = defaultdict(set)
    for insc in corpus:
        site = insc.get('site', '')
        for ch in insc.get('signs_unicode', ''):
            cp = ord(ch)
            if LA_START <= cp <= LA_END and cp not in EDITORIAL:
                site_vocab[site].add(cp)

    main_sites = ['Khania', 'Phaistos', 'Knossos', 'Zakros', 'Palaikastro', 'Malia']
    ht_vocab = site_vocab['Haghia Triada']

    fig, ax = plt.subplots(figsize=(10, 5))

    sites_data = []
    for site in main_sites:
        v = site_vocab[site]
        shared = v & ht_vocab
        coverage = len(shared) / len(v) if v else 0
        union = v | ht_vocab
        jaccard = len(v & ht_vocab) / len(union) if union else 0
        sites_data.append({
            'site': site,
            'vocab_size': len(v),
            'coverage': coverage,
            'jaccard': jaccard,
            'unique': len(v - ht_vocab),
        })

    x = np.arange(len(main_sites))
    width = 0.35

    coverage_vals = [d['coverage'] for d in sites_data]
    jaccard_vals = [d['jaccard'] for d in sites_data]

    bars1 = ax.bar(x - width/2, coverage_vals, width, label='Asymmetric Coverage\n(% of site vocab shared with HT)',
                   color='#2ecc71', alpha=0.8)
    bars2 = ax.bar(x + width/2, jaccard_vals, width, label='Jaccard Similarity\n(misleading for asymmetric sets)',
                   color='#e74c3c', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{d['site']}\n({d['vocab_size']} signs)" for d in sites_data], fontsize=9)
    ax.set_ylabel('Similarity to Haghia Triada')
    ax.set_title('Site Vocabulary Overlap with Haghia Triada (211 signs)')
    ax.legend(loc='lower right')
    ax.set_ylim(0, 1.1)

    # Annotate coverage values
    for bar, val in zip(bars1, coverage_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
               f'{val:.0%}', ha='center', va='bottom', fontsize=8)

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig5_site_coverage.png')
    fig.savefig(FIG_DIR / 'fig5_site_coverage.pdf')
    plt.close(fig)
    print('Saved fig5')


# ── Figure 6: Support type distribution by site ───────────────────────────

def fig6_site_support_distribution(corpus):
    main_sites = ['Haghia Triada', 'Khania', 'Phaistos', 'Knossos', 'Zakros']
    main_supports = ['Nodule', 'Tablet', 'Roundel', 'Stone vessel', 'Clay vessel', 'Other']

    site_support = defaultdict(Counter)
    for insc in corpus:
        site = insc.get('site', '')
        if site not in main_sites:
            continue
        support = insc.get('support', 'Unknown')
        if support not in main_supports[:-1]:
            support = 'Other'
        if insc.get('signs_unicode'):
            site_support[site][support] += 1

    fig, ax = plt.subplots(figsize=(10, 5))

    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#95a5a6']
    x = np.arange(len(main_sites))
    width = 0.12

    for i, support in enumerate(main_supports):
        vals = []
        for site in main_sites:
            total = sum(site_support[site].values())
            vals.append(site_support[site].get(support, 0) / total if total else 0)
        ax.bar(x + i * width - 2.5 * width, vals, width, label=support,
               color=colors[i], alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(main_sites, fontsize=9)
    ax.set_ylabel('Proportion of inscriptions')
    ax.set_title('Administrative Technology by Site')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig6_site_support.png')
    fig.savefig(FIG_DIR / 'fig6_site_support.pdf')
    plt.close(fig)
    print('Saved fig6')


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    corpus = load_corpus()
    print(f'Loaded {len(corpus)} inscriptions')

    fig1_support_type_boxplot(corpus)
    fig2_mobility_gradient(corpus)
    fig3_hub_structure()
    fig4_classification()
    fig5_site_coverage(corpus)
    fig6_site_support_distribution(corpus)

    print(f'\nAll figures saved to {FIG_DIR}')


if __name__ == '__main__':
    main()
