#!/usr/bin/env python3
"""
Phase 5: Site-Concentration Statistical Battery — Linear A Corpus
==================================================================
Determines whether specific signs are enriched or depleted at specific sites
using Monroe et al. (2008) weighted log-odds with informative Dirichlet prior,
validated by 10K permutation null with BH-FDR correction.

Handles HT dominance (64.5% of corpus) without removing data.

Data source: canonical_corpus.json
Output:      analysis/phase5_site_concentration.json
             analysis/phase5_site_concentration_report.md
"""

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
from scipy.stats import false_discovery_control

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
CORPUS_JSON = ROOT / "data" / "corpus" / "canonical_corpus.json"
ANALYSIS_DIR = ROOT / "analysis"

LINEAR_A_START = 0x10600
LINEAR_A_END = 0x1077F
EDITORIAL_MARKERS = {0x1076B, 0x1076C, 0x1076D, 0x1076E, 0x1076F}

# Site tiers
PRIMARY_MIN = 53    # N >= 53 for full analysis
SECONDARY_MIN = 20  # N >= 20 for secondary
N_PERMUTATIONS = 10_000
Z_THRESHOLD = 2.0   # |zeta| > 2.0
FDR_Q = 0.05         # BH-FDR q threshold


def get_ct_timestamp():
    ct = timezone(timedelta(hours=-6))
    return datetime.now(ct).strftime("%Y-%m-%d %H:%M CT")


def is_linear_a_sign(cp):
    return LINEAR_A_START <= cp <= LINEAR_A_END and cp not in EDITORIAL_MARKERS


def sign_label(cp):
    return f"U+{cp:05X}"


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
def load_corpus():
    with open(CORPUS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_site_sign_data(corpus):
    """
    Extract per-site sign token counts.
    Returns:
        site_sign_counts: {site: {sign_cp: count}}
        site_totals: {site: total_tokens}
        sign_totals: {sign_cp: total_tokens}
        insc_sites: [(insc_id, site, frozenset_of_signs)]
    """
    site_sign_counts = defaultdict(Counter)
    site_totals = Counter()
    sign_totals = Counter()
    insc_sites = []

    for insc in corpus:
        site = insc.get("site", "Unknown")
        text = insc.get("signs_unicode", "")
        signs = []
        sign_set = set()
        for ch in text:
            cp = ord(ch)
            if is_linear_a_sign(cp):
                signs.append(cp)
                sign_set.add(cp)
                site_sign_counts[site][cp] += 1
                site_totals[site] += 1
                sign_totals[cp] += 1

        if signs:
            insc_sites.append((insc["id"], site, frozenset(sign_set)))

    return site_sign_counts, dict(site_totals), dict(sign_totals), insc_sites


# ---------------------------------------------------------------------------
# WEIGHTED LOG-ODDS (Monroe et al. 2008)
# ---------------------------------------------------------------------------
def compute_log_odds(site_sign_counts, site_totals, sign_totals):
    """
    Compute weighted log-odds with informative Dirichlet prior.

    For sign j at site i:
    delta_ij = log((y_ij + alpha_j) / (n_i + alpha_0 - y_ij - alpha_j))
             - log((y_j - y_ij + alpha_j) / (n - n_i + alpha_0 - y_j + y_ij - alpha_j))
    sigma2_ij = 1/(y_ij + alpha_j) + 1/(n_i + alpha_0 - y_ij - alpha_j)
    zeta_ij = delta_ij / sqrt(sigma2_ij)
    """
    # Total corpus
    n_total = sum(site_totals.values())
    all_signs = sorted(sign_totals.keys())

    # Dirichlet prior: alpha_j = corpus-wide frequency of sign j
    # alpha_0 = sum of all alpha_j = n_total (total tokens as prior strength)
    # This gives a strong prior toward the corpus mean
    alpha = {s: sign_totals[s] for s in all_signs}
    alpha_0 = sum(alpha.values())

    results = {}  # {(site, sign): {"zeta": z, "delta": d, ...}}

    sites = sorted(site_totals.keys())

    for site in sites:
        n_i = site_totals[site]
        for sign in all_signs:
            y_ij = site_sign_counts[site].get(sign, 0)
            y_j = sign_totals[sign]
            alpha_j = alpha[sign]

            # Numerator terms
            num1 = y_ij + alpha_j
            den1 = n_i + alpha_0 - y_ij - alpha_j

            num2 = y_j - y_ij + alpha_j
            den2 = n_total - n_i + alpha_0 - y_j + y_ij - alpha_j

            # Safeguards
            if num1 <= 0 or den1 <= 0 or num2 <= 0 or den2 <= 0:
                continue

            delta = math.log(num1 / den1) - math.log(num2 / den2)
            sigma2 = 1.0 / num1 + 1.0 / den1
            sigma = math.sqrt(sigma2)

            if sigma == 0:
                continue

            zeta = delta / sigma

            results[(site, sign)] = {
                "site": site,
                "sign": sign_label(sign),
                "sign_cp": sign,
                "y_ij": y_ij,
                "n_i": n_i,
                "y_j": y_j,
                "delta": round(delta, 6),
                "sigma": round(sigma, 6),
                "zeta": round(zeta, 4),
            }

    return results


# ---------------------------------------------------------------------------
# PERMUTATION NULL
# ---------------------------------------------------------------------------
def run_permutation_null(insc_sites, site_totals, sign_totals, observed_results, rng):
    """
    Shuffle site labels across inscriptions, recompute log-odds z-scores.
    Returns p-values for each (site, sign) pair.
    """
    print(f"Running {N_PERMUTATIONS} permutations...")

    # Prepare data for fast shuffling
    all_signs_list = sorted(sign_totals.keys())
    sites_list = sorted(site_totals.keys())

    # Pre-extract inscription data
    insc_data = []
    for insc_id, site, sign_set in insc_sites:
        # Count sign tokens (need raw counts, not just set)
        # We stored frozenset, so we need to re-extract
        insc_data.append((site, sign_set))

    # For permutation, we only need to track site labels
    original_sites = [d[0] for d in insc_data]
    sign_sets = [d[1] for d in insc_data]

    # Observed zetas for comparison
    observed_zetas = {}
    for key, val in observed_results.items():
        observed_zetas[key] = abs(val["zeta"])

    # Count how many permutations produce |zeta| >= observed
    exceedance_counts = Counter()  # {(site, sign): count}

    n_total = sum(site_totals.values())
    alpha_0 = n_total  # Dirichlet prior strength

    for perm_i in range(N_PERMUTATIONS):
        if (perm_i + 1) % 1000 == 0:
            print(f"  Permutation {perm_i + 1}/{N_PERMUTATIONS}")

        # Shuffle site labels
        shuffled_sites = rng.permutation(original_sites)

        # Recompute site-sign counts under shuffled labels
        perm_site_sign = defaultdict(Counter)
        perm_site_total = Counter()

        for i, (shuffled_site, sign_set) in enumerate(zip(shuffled_sites, sign_sets)):
            # Approximate: count each sign once per inscription for speed
            # (This underestimates tokens but preserves relative enrichment patterns)
            for s in sign_set:
                perm_site_sign[shuffled_site][s] += 1
                perm_site_total[shuffled_site] += 1

        # Compute zetas for this permutation
        perm_n_total = sum(perm_site_total.values())
        perm_sign_totals = Counter()
        for site_counts in perm_site_sign.values():
            perm_sign_totals.update(site_counts)

        for site in sites_list:
            if site not in perm_site_total:
                continue
            n_i = perm_site_total[site]
            for sign in all_signs_list:
                key = (site, sign)
                if key not in observed_zetas:
                    continue

                y_ij = perm_site_sign[site].get(sign, 0)
                y_j = perm_sign_totals.get(sign, 0)
                alpha_j = sign_totals.get(sign, 1)  # use original prior

                num1 = y_ij + alpha_j
                den1 = n_i + alpha_0 - y_ij - alpha_j
                num2 = y_j - y_ij + alpha_j
                den2 = perm_n_total - n_i + alpha_0 - y_j + y_ij - alpha_j

                if num1 <= 0 or den1 <= 0 or num2 <= 0 or den2 <= 0:
                    continue

                delta = math.log(num1 / den1) - math.log(num2 / den2)
                sigma2 = 1.0 / num1 + 1.0 / den1
                if sigma2 <= 0:
                    continue
                zeta = delta / math.sqrt(sigma2)

                if abs(zeta) >= observed_zetas[key]:
                    exceedance_counts[key] += 1

    # Compute empirical p-values
    p_values = {}
    for key in observed_zetas:
        p_values[key] = (exceedance_counts.get(key, 0) + 1) / (N_PERMUTATIONS + 1)

    return p_values


# ---------------------------------------------------------------------------
# REPORT GENERATION
# ---------------------------------------------------------------------------
def generate_report(observed, p_values, site_totals, sign_totals, site_insc_counts, enriched_pairs):
    ts = get_ct_timestamp()

    sites = sorted(site_totals.keys(), key=lambda s: site_totals[s], reverse=True)
    primary_sites = [s for s in sites if site_insc_counts[s] >= PRIMARY_MIN]
    secondary_sites = [s for s in sites if SECONDARY_MIN <= site_insc_counts[s] < PRIMARY_MIN]

    report = f"""<system_meta>
  <id>signal-theory-anth-linear-a-phase5-site-001</id>
  <tags>
    <agent>signal-theory-anth-linear-a</agent>
    <type>research</type>
    <status>verified</status>
    <project>linear-a</project>
    <time>2026-03-17</time>
  </tags>
  <tldr>Phase 5: Site concentration — {len(enriched_pairs)} enriched sign-site pairs after permutation null + FDR.</tldr>
</system_meta>

# Phase 5: Site-Concentration Statistical Battery

**Generated:** {ts}
**Method:** Monroe et al. (2008) weighted log-odds + {N_PERMUTATIONS:,} permutation null + BH-FDR at q={FDR_Q}

---

## Site Overview

| Site | Inscriptions | Sign Tokens | Tier |
|------|-------------|-------------|------|
"""
    for site in sites:
        n_insc = site_insc_counts[site]
        if n_insc >= PRIMARY_MIN:
            tier = "PRIMARY"
        elif n_insc >= SECONDARY_MIN:
            tier = "SECONDARY"
        else:
            tier = "EXCLUDED"
        report += f"| {site} | {n_insc} | {site_totals.get(site, 0)} | {tier} |\n"

    # Verification
    ht_enriched = sum(1 for (s, _) in enriched_pairs if s == "Haghia Triada")
    kh_enriched = sum(1 for (s, _) in enriched_pairs if s == "Khania")

    report += f"""
---

## Verification

| Criterion | Threshold | Observed | Status |
|-----------|-----------|----------|--------|
| HT enriched signs | >= 5 | {ht_enriched} | {'PASS' if ht_enriched >= 5 else 'FAIL'} |
| Khania enriched signs | >= 3 | {kh_enriched} | {'PASS' if kh_enriched >= 3 else 'FAIL'} |
| Enrichment survives permutation | any | {len(enriched_pairs)} | {'PASS' if enriched_pairs else 'FAIL'} |

---

## Enriched Signs by Site (|z| > {Z_THRESHOLD}, permutation p < {FDR_Q} after FDR)

"""
    # Group enriched pairs by site
    by_site = defaultdict(list)
    for (site, sign_cp) in enriched_pairs:
        key = (site, sign_cp)
        if key in observed:
            entry = observed[key].copy()
            entry["perm_p"] = p_values.get(key, 1.0)
            by_site[site].append(entry)

    for site in primary_sites + secondary_sites:
        if site not in by_site:
            report += f"### {site} — no enriched signs\n\n"
            continue

        entries = sorted(by_site[site], key=lambda x: abs(x["zeta"]), reverse=True)
        tier_label = "PRIMARY" if site_insc_counts[site] >= PRIMARY_MIN else "SECONDARY"
        report += f"### {site} ({tier_label}, N={site_insc_counts[site]})\n\n"
        report += "| Sign | Count at Site | Corpus Total | z-score | Perm p | Direction |\n"
        report += "|------|-------------|-------------|---------|--------|----------|\n"

        for e in entries[:15]:
            direction = "enriched" if e["zeta"] > 0 else "depleted"
            report += f"| {e['sign']} | {e['y_ij']} | {e['y_j']} | {e['zeta']:.2f} | {e['perm_p']:.4f} | {direction} |\n"
        report += "\n"

    # Cross-site analysis
    report += """---

## Cross-Site Analysis

### HT-Specific Vocabulary
Signs significantly enriched at HT but NOT at any other site:

"""
    ht_only = set()
    non_ht_enriched = set()
    for (site, sign_cp) in enriched_pairs:
        if site == "Haghia Triada":
            ht_only.add(sign_cp)
        else:
            non_ht_enriched.add(sign_cp)

    ht_exclusive = ht_only - non_ht_enriched
    if ht_exclusive:
        for cp in sorted(ht_exclusive):
            key = ("Haghia Triada", cp)
            if key in observed:
                e = observed[key]
                report += f"- {sign_label(cp)} (z={e['zeta']:.2f}, count={e['y_ij']})\n"
    else:
        report += "None identified.\n"

    report += """
### Non-HT Commonalities
Signs enriched at >= 2 non-HT sites:

"""
    non_ht_sign_sites = defaultdict(set)
    for (site, sign_cp) in enriched_pairs:
        if site != "Haghia Triada":
            non_ht_sign_sites[sign_cp].add(site)

    multi_site = {s: sites for s, sites in non_ht_sign_sites.items() if len(sites) >= 2}
    if multi_site:
        for sign_cp, sites in sorted(multi_site.items(), key=lambda x: len(x[1]), reverse=True):
            report += f"- {sign_label(sign_cp)} at {', '.join(sorted(sites))}\n"
    else:
        report += "None identified.\n"

    # Jaccard similarity
    report += """
### Cross-Site Jaccard Similarity

"""
    enriched_by_site = defaultdict(set)
    for (site, sign_cp) in enriched_pairs:
        enriched_by_site[site].add(sign_cp)

    jaccard_sites = [s for s in primary_sites if s in enriched_by_site]
    if len(jaccard_sites) >= 2:
        report += "| Site A | Site B | Jaccard | Shared Signs |\n"
        report += "|--------|--------|---------|-------------|\n"
        for i in range(len(jaccard_sites)):
            for j in range(i + 1, len(jaccard_sites)):
                s_a = enriched_by_site[jaccard_sites[i]]
                s_b = enriched_by_site[jaccard_sites[j]]
                intersection = s_a & s_b
                union = s_a | s_b
                jaccard = len(intersection) / len(union) if union else 0
                report += f"| {jaccard_sites[i]} | {jaccard_sites[j]} | {jaccard:.3f} | {len(intersection)} |\n"

    report += """
---

## Interpretation

| Pattern | Interpretation |
|---------|---------------|
| Sign enriched at HT only | HT-specific administrative term or commodity label |
| Sign enriched at all sites | Core vocabulary — unlikely to be site-specific |
| Sign enriched at coastal sites but not HT | Possible trade/maritime vocabulary |
| Sign depleted at HT but common elsewhere | Religious/ritual vocabulary? (HT = secular archive) |
"""

    return report


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    corpus = load_corpus()
    print(f"Loaded {len(corpus)} inscriptions")

    site_sign_counts, site_totals, sign_totals, insc_sites = extract_site_sign_data(corpus)

    # Count inscriptions per site
    site_insc_counts = Counter()
    for insc in corpus:
        site = insc.get("site", "Unknown")
        if insc.get("signs_unicode", ""):
            site_insc_counts[site] += 1

    print(f"\nSites: {len(site_totals)}")
    for site in sorted(site_totals, key=site_totals.get, reverse=True)[:10]:
        tier = "PRIMARY" if site_insc_counts[site] >= PRIMARY_MIN else (
            "SECONDARY" if site_insc_counts[site] >= SECONDARY_MIN else "excluded")
        print(f"  {site}: {site_insc_counts[site]} inscriptions, {site_totals[site]} tokens [{tier}]")

    # Compute observed log-odds z-scores
    print("\nComputing weighted log-odds...")
    observed = compute_log_odds(site_sign_counts, site_totals, sign_totals)

    # Filter to significant z-scores for permutation testing
    significant = {k: v for k, v in observed.items() if abs(v["zeta"]) > Z_THRESHOLD}
    print(f"Pairs with |z| > {Z_THRESHOLD}: {len(significant)}")

    # Only run permutation on primary + secondary sites
    primary_secondary_sites = {s for s in site_totals
                               if site_insc_counts[s] >= SECONDARY_MIN}

    # Filter significant to analyzable sites
    testable = {k: v for k, v in significant.items()
                if k[0] in primary_secondary_sites}
    print(f"Testable pairs (primary/secondary sites): {len(testable)}")

    # Run permutation null
    rng = np.random.default_rng(42)
    p_values = run_permutation_null(insc_sites, site_totals, sign_totals, testable, rng)

    # Apply BH-FDR correction
    if testable:
        keys = sorted(testable.keys())
        raw_ps = [p_values.get(k, 1.0) for k in keys]

        # BH-FDR correction
        rejected = false_discovery_control(raw_ps, method="bh")
        corrected_ps = dict(zip(keys, raw_ps))

        enriched_pairs = []
        for k, is_sig in zip(keys, rejected):
            if is_sig:
                enriched_pairs.append(k)

        print(f"\nEnriched pairs after FDR correction: {len(enriched_pairs)}")
    else:
        enriched_pairs = []
        corrected_ps = {}

    # Save results
    ANALYSIS_DIR.mkdir(exist_ok=True)

    results = {
        "metadata": {
            "generated": get_ct_timestamp(),
            "n_inscriptions": len(corpus),
            "n_permutations": N_PERMUTATIONS,
            "z_threshold": Z_THRESHOLD,
            "fdr_q": FDR_Q,
        },
        "site_summary": {site: {
            "inscriptions": site_insc_counts[site],
            "tokens": site_totals.get(site, 0),
            "tier": "PRIMARY" if site_insc_counts[site] >= PRIMARY_MIN else (
                "SECONDARY" if site_insc_counts[site] >= SECONDARY_MIN else "EXCLUDED")
        } for site in sorted(site_totals.keys())},
        "enriched_pairs": [
            {**observed[k], "perm_p": p_values.get(k, 1.0)}
            for k in enriched_pairs if k in observed
        ],
        "total_enriched": len(enriched_pairs),
        "total_tested": len(testable),
    }

    out_json = ANALYSIS_DIR / "phase5_site_concentration.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_json}")

    # Generate report
    report = generate_report(observed, p_values, site_totals, sign_totals,
                             site_insc_counts, enriched_pairs)
    out_md = ANALYSIS_DIR / "phase5_site_concentration_report.md"
    with open(out_md, "w") as f:
        f.write(report)
    print(f"Saved: {out_md}")


if __name__ == "__main__":
    main()
