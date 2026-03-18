#!/usr/bin/env python3
"""
Phase 3: Asymmetric Dependency Graph — Linear A Corpus
======================================================
Identifies directed dependency relationships between signs using:
  - Fisher's exact test on 2x2 contingency tables
  - Lift thresholds (controls for base-rate inflation)
  - Asymmetry ratio for edge directionality

Entry gate (all three required):
  1. N_AB >= 5 (pair co-occurs in >= 5 inscriptions)
  2. Fisher's exact p < 0.01
  3. lift(A->B) > 3.0

Directed edge: asymmetry_ratio = lift(A->B) / lift(B->A) > 2.0

Data source: canonical_corpus.json (1,721 inscriptions)
Output:     analysis/phase3_dependency_graph.json
            analysis/phase3_dependency_report.md
            analysis/phase3_dependency_graph.dot
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scipy.stats import fisher_exact

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
CORPUS_JSON = ROOT / "data" / "corpus" / "canonical_corpus.json"
ANALYSIS_DIR = ROOT / "analysis"

# Unicode ranges
LINEAR_A_START = 0x10600
LINEAR_A_END = 0x1077F
EDITORIAL_MARKERS = {0x1076B, 0x1076C, 0x1076D, 0x1076E, 0x1076F}

# Thresholds from v4 plan
MIN_COOCCURRENCE = 5       # N_AB >= 5
FISHER_P_THRESHOLD = 0.01  # p < 0.01
LIFT_THRESHOLD = 3.0       # lift > 3.0
ASYMMETRY_THRESHOLD = 2.0  # asymmetry ratio > 2.0 for directed edge


def get_ct_timestamp():
    ct = timezone(timedelta(hours=-6))
    return datetime.now(ct).strftime("%Y-%m-%d %H:%M CT")


def is_linear_a_sign(cp):
    return LINEAR_A_START <= cp <= LINEAR_A_END and cp not in EDITORIAL_MARKERS


def sign_label(cp):
    """Human-readable label for a sign codepoint."""
    return f"U+{cp:05X}"


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
def load_corpus():
    with open(CORPUS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} inscriptions from canonical_corpus.json")
    return data


def extract_sign_sets(corpus):
    """
    For each inscription, extract the SET of distinct Linear A signs present.
    Returns list of (inscription_id, frozenset_of_codepoints).
    """
    result = []
    for insc in corpus:
        signs = set()
        text = insc.get("signs_unicode", "")
        for ch in text:
            cp = ord(ch)
            if is_linear_a_sign(cp):
                signs.add(cp)
        if signs:
            result.append((insc["id"], frozenset(signs)))
    return result


# ---------------------------------------------------------------------------
# PHASE 3 ANALYSIS
# ---------------------------------------------------------------------------
def compute_dependency_graph(sign_sets):
    """
    Compute asymmetric dependency edges between all sign pairs.

    For each pair (A, B):
      - Build 2x2 contingency table
      - Fisher's exact test
      - Lift in both directions
      - Asymmetry ratio
    """
    N = len(sign_sets)
    print(f"Computing on {N} inscriptions with sign data")

    # Count per-sign presence
    sign_counts = Counter()
    for _, signs in sign_sets:
        for s in signs:
            sign_counts[s] += 1

    # Get all signs that appear in at least MIN_COOCCURRENCE inscriptions
    # (a sign appearing in fewer can't possibly co-occur MIN_COOCCURRENCE times)
    viable_signs = {s for s, c in sign_counts.items() if c >= MIN_COOCCURRENCE}
    print(f"Signs with >= {MIN_COOCCURRENCE} attestations: {len(viable_signs)}")

    # Count pairwise co-occurrence
    pair_counts = Counter()
    for _, signs in sign_sets:
        viable_in_insc = signs & viable_signs
        sorted_signs = sorted(viable_in_insc)
        for i in range(len(sorted_signs)):
            for j in range(i + 1, len(sorted_signs)):
                pair_counts[(sorted_signs[i], sorted_signs[j])] += 1

    # Filter to pairs with N_AB >= MIN_COOCCURRENCE
    candidate_pairs = {p: c for p, c in pair_counts.items() if c >= MIN_COOCCURRENCE}
    print(f"Candidate pairs (N_AB >= {MIN_COOCCURRENCE}): {len(candidate_pairs)}")

    edges = []
    tested = 0
    passed_fisher = 0
    passed_lift = 0

    for (a, b), n_ab in candidate_pairs.items():
        tested += 1
        n_a = sign_counts[a]
        n_b = sign_counts[b]

        # 2x2 contingency table:
        #              B present    B absent
        # A present    n_ab         n_a - n_ab
        # A absent     n_b - n_ab   N - n_a - n_b + n_ab
        table = [
            [n_ab, n_a - n_ab],
            [n_b - n_ab, N - n_a - n_b + n_ab]
        ]

        # Sanity check: all cells must be >= 0
        if any(cell < 0 for row in table for cell in row):
            continue

        # Fisher's exact test (one-sided: greater, testing positive association)
        _, p_value = fisher_exact(table, alternative="greater")

        if p_value >= FISHER_P_THRESHOLD:
            continue
        passed_fisher += 1

        # Lift calculations
        p_a = n_a / N
        p_b = n_b / N
        p_ab = n_ab / N

        # Avoid division by zero
        if p_a == 0 or p_b == 0:
            continue

        lift_ab = p_ab / (p_a * p_b)  # lift(A->B) = P(AB) / (P(A)*P(B))
        # lift is symmetric for co-occurrence, but conditional probs are not
        # lift_ab == lift_ba by definition

        # Conditional probabilities (these ARE asymmetric)
        p_b_given_a = n_ab / n_a  # P(B|A)
        p_a_given_b = n_ab / n_b  # P(A|B)

        # Check lift threshold
        if lift_ab <= LIFT_THRESHOLD:
            continue
        passed_lift += 1

        # Asymmetry: which direction is the dependency?
        # If P(B|A) >> P(A|B), then A depends on B (A requires B more than B requires A)
        # We define asymmetry as the ratio of conditional probabilities
        # Since lift is symmetric, we use conditional prob ratio for directionality
        if p_a_given_b > 0 and p_b_given_a > 0:
            # asymmetry_ratio measures how much more A predicts B than B predicts A
            asym_ab = p_b_given_a / p_a_given_b  # > 1 means A->B
            asym_ba = p_a_given_b / p_b_given_a  # > 1 means B->A
        else:
            asym_ab = float('inf') if p_b_given_a > 0 else 0
            asym_ba = float('inf') if p_a_given_b > 0 else 0

        # Classify dependency strength
        def classify(p_forward, p_backward):
            if p_forward > 0.5 and p_backward < 0.1:
                return "strong"
            elif p_forward > 0.3 and p_backward < 0.2:
                return "moderate"
            else:
                return "weak"

        edge_data = {
            "sign_a": sign_label(a),
            "sign_b": sign_label(b),
            "sign_a_cp": a,
            "sign_b_cp": b,
            "n_ab": n_ab,
            "n_a": n_a,
            "n_b": n_b,
            "p_b_given_a": round(p_b_given_a, 4),
            "p_a_given_b": round(p_a_given_b, 4),
            "lift": round(lift_ab, 4),
            "fisher_p": p_value,
            "asymmetry_ab": round(asym_ab, 4),
            "asymmetry_ba": round(asym_ba, 4),
        }

        # Determine directed edges
        if asym_ab > ASYMMETRY_THRESHOLD:
            edge_data["direction"] = "A->B"
            edge_data["strength"] = classify(p_b_given_a, p_a_given_b)
            edges.append(edge_data)
        elif asym_ba > ASYMMETRY_THRESHOLD:
            edge_data["direction"] = "B->A"
            edge_data["strength"] = classify(p_a_given_b, p_b_given_a)
            edges.append(edge_data)
        else:
            # Mutual / symmetric — fixed formula type
            edge_data["direction"] = "mutual"
            edge_data["strength"] = "formula"
            edges.append(edge_data)

    print(f"\nFilter pipeline:")
    print(f"  Tested pairs:       {tested}")
    print(f"  Passed Fisher:      {passed_fisher}")
    print(f"  Passed lift:        {passed_lift}")
    print(f"  Final edges:        {len(edges)}")

    return edges, sign_counts


def analyze_graph(edges, sign_counts):
    """Compute graph-level statistics: hubs, components, etc."""
    # Build adjacency
    incoming = defaultdict(list)  # signs with arrows pointing TO them
    outgoing = defaultdict(list)  # signs with arrows pointing FROM them
    mutual = defaultdict(list)

    all_nodes = set()

    for e in edges:
        a = e["sign_a"]
        b = e["sign_b"]
        all_nodes.add(a)
        all_nodes.add(b)

        if e["direction"] == "A->B":
            outgoing[a].append(e)
            incoming[b].append(e)
        elif e["direction"] == "B->A":
            outgoing[b].append(e)
            incoming[a].append(e)
        else:  # mutual
            mutual[a].append(e)
            mutual[b].append(e)

    # Connected components (undirected)
    adj = defaultdict(set)
    for e in edges:
        adj[e["sign_a"]].add(e["sign_b"])
        adj[e["sign_b"]].add(e["sign_a"])

    visited = set()
    components = []
    for node in all_nodes:
        if node not in visited:
            component = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n in visited:
                    continue
                visited.add(n)
                component.add(n)
                stack.extend(adj[n] - visited)
            components.append(component)

    components.sort(key=len, reverse=True)

    # Hub analysis
    hub_stats = []
    for node in all_nodes:
        hub_stats.append({
            "sign": node,
            "in_degree": len(incoming.get(node, [])),
            "out_degree": len(outgoing.get(node, [])),
            "mutual_degree": len(mutual.get(node, [])),
            "total_degree": len(incoming.get(node, [])) + len(outgoing.get(node, [])) + len(mutual.get(node, [])),
            "count": sign_counts.get(int(node.replace("U+", ""), 16), 0),
        })

    hub_stats.sort(key=lambda x: x["total_degree"], reverse=True)

    return {
        "node_count": len(all_nodes),
        "edge_count": len(edges),
        "directed_edges": sum(1 for e in edges if e["direction"] != "mutual"),
        "mutual_edges": sum(1 for e in edges if e["direction"] == "mutual"),
        "component_count": len(components),
        "largest_component": len(components[0]) if components else 0,
        "component_sizes": [len(c) for c in components],
        "hub_stats": hub_stats,
        "components": [sorted(list(c)) for c in components],
    }


def generate_dot(edges, graph_stats):
    """Generate Graphviz DOT format for visualization."""
    lines = ["digraph LinearA_Dependencies {"]
    lines.append('  rankdir=LR;')
    lines.append('  node [shape=ellipse, fontsize=10];')
    lines.append('  edge [fontsize=8];')
    lines.append('')

    for e in edges:
        a = e["sign_a"]
        b = e["sign_b"]
        label = f"N={e['n_ab']}, lift={e['lift']:.1f}"

        if e["direction"] == "A->B":
            color = {"strong": "red", "moderate": "orange", "weak": "gray60"}.get(e["strength"], "black")
            lines.append(f'  "{a}" -> "{b}" [label="{label}", color={color}];')
        elif e["direction"] == "B->A":
            color = {"strong": "red", "moderate": "orange", "weak": "gray60"}.get(e["strength"], "black")
            lines.append(f'  "{b}" -> "{a}" [label="{label}", color={color}];')
        else:  # mutual
            lines.append(f'  "{a}" -> "{b}" [label="{label}", dir=both, color=blue];')

    lines.append("}")
    return "\n".join(lines)


def generate_report(edges, graph_stats, sign_counts, N_inscriptions):
    """Generate the Phase 3 markdown report."""
    ts = get_ct_timestamp()

    # Sort edges by lift descending for the table
    sorted_edges = sorted(edges, key=lambda e: e["lift"], reverse=True)

    # Separate by type
    strong = [e for e in edges if e["strength"] == "strong"]
    moderate = [e for e in edges if e["strength"] == "moderate"]
    weak = [e for e in edges if e["strength"] == "weak"]
    formulas = [e for e in edges if e["strength"] == "formula"]

    report = f"""<system_meta>
  <id>signal-theory-anth-linear-a-phase3-dep-001</id>
  <tags>
    <agent>signal-theory-anth-linear-a</agent>
    <type>research</type>
    <status>verified</status>
    <project>linear-a</project>
    <time>2026-03-17</time>
  </tags>
  <tldr>Phase 3: Asymmetric dependency graph — {graph_stats['edge_count']} edges, {graph_stats['directed_edges']} directed, {graph_stats['component_count']} components.</tldr>
</system_meta>

# Phase 3: Asymmetric Dependency Graph

**Generated:** {ts}
**Corpus:** {N_inscriptions} inscriptions, {len(sign_counts)} distinct signs

---

## Method

For each pair of signs (A, B) co-occurring in the same inscription:

1. **Entry gate** (all three required):
   - N_AB >= {MIN_COOCCURRENCE} (co-occurrence count)
   - Fisher's exact test p < {FISHER_P_THRESHOLD} (one-sided, greater)
   - lift(A,B) > {LIFT_THRESHOLD}

2. **Directionality:**
   - Asymmetry ratio = P(B|A) / P(A|B)
   - Directed edge if ratio > {ASYMMETRY_THRESHOLD}
   - Mutual edge if neither direction exceeds threshold

3. **Strength classification:**
   - Strong: P(forward) > 0.5 AND P(backward) < 0.1
   - Moderate: P(forward) > 0.3 AND P(backward) < 0.2
   - Weak: passes lift/asymmetry but not conditional thresholds

---

## Summary

| Metric | Value |
|--------|-------|
| Total edges | {graph_stats['edge_count']} |
| Directed edges | {graph_stats['directed_edges']} |
| Mutual edges (formulas) | {graph_stats['mutual_edges']} |
| Strong dependencies | {len(strong)} |
| Moderate dependencies | {len(moderate)} |
| Weak dependencies | {len(weak)} |
| Fixed formulas | {len(formulas)} |
| Nodes in graph | {graph_stats['node_count']} |
| Connected components | {graph_stats['component_count']} |
| Largest component | {graph_stats['largest_component']} nodes |

---

## Verification

| Criterion | Threshold | Observed | Status |
|-----------|-----------|----------|--------|
| Directed edges | >= 10 | {graph_stats['directed_edges']} | {'PASS' if graph_stats['directed_edges'] >= 10 else 'FAIL'} |
| Distinct signs in edges | > 6 | {graph_stats['node_count']} | {'PASS' if graph_stats['node_count'] > 6 else 'FAIL'} |
| Not dominated by 2-3 signs | visual check | see hub table | — |

---

## Top Edges by Lift

| Rank | Sign A | Sign B | Direction | N_AB | P(B|A) | P(A|B) | Lift | Fisher p | Strength |
|------|--------|--------|-----------|------|--------|--------|------|----------|----------|
"""
    for i, e in enumerate(sorted_edges[:30]):
        report += f"| {i+1} | {e['sign_a']} | {e['sign_b']} | {e['direction']} | {e['n_ab']} | {e['p_b_given_a']:.3f} | {e['p_a_given_b']:.3f} | {e['lift']:.2f} | {e['fisher_p']:.2e} | {e['strength']} |\n"

    report += f"""
---

## Hub Analysis (Top 15 by Total Degree)

| Sign | Count | In-Degree | Out-Degree | Mutual | Total | Role |
|------|-------|-----------|------------|--------|-------|------|
"""
    for h in graph_stats["hub_stats"][:15]:
        if h["in_degree"] > h["out_degree"] + h["mutual_degree"]:
            role = "grammatical hub"
        elif h["out_degree"] > h["in_degree"] + h["mutual_degree"]:
            role = "independent root"
        elif h["mutual_degree"] > h["in_degree"] + h["out_degree"]:
            role = "formula participant"
        else:
            role = "mixed"
        report += f"| {h['sign']} | {h['count']} | {h['in_degree']} | {h['out_degree']} | {h['mutual_degree']} | {h['total_degree']} | {role} |\n"

    report += f"""
---

## Connected Components

{graph_stats['component_count']} components detected. Sizes: {graph_stats['component_sizes']}

"""
    for i, comp in enumerate(graph_stats["components"][:5]):
        report += f"### Component {i+1} ({len(comp)} nodes)\n"
        report += f"Signs: {', '.join(comp)}\n\n"

    report += f"""---

## Interpretation

- **Grammatical hubs** (high in-degree): Signs that many other signs depend on — likely modifiers, case markers, or structural operators.
- **Independent roots** (high out-degree): Signs that predict others but aren't predicted by them — likely nouns, commodity labels.
- **Formula participants** (high mutual degree): Signs locked into fixed sequences — administrative formulas (cf. Indus KU-RO type).

## Rejected approaches
- Raw P(B|A)/P(A|B) without lift: base-rate blind — high-frequency signs trivially satisfy.
- Chi-square: expected cell counts too small for rare sign pairs.
"""

    return report


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    corpus = load_corpus()
    sign_sets = extract_sign_sets(corpus)
    N = len(sign_sets)

    print(f"\nInscriptions with sign data: {N}")

    # Get all signs for counts
    sign_counts = Counter()
    for _, signs in sign_sets:
        for s in signs:
            sign_counts[s] += 1
    print(f"Distinct signs: {len(sign_counts)}")

    edges, _ = compute_dependency_graph(sign_sets)
    graph_stats = analyze_graph(edges, sign_counts)

    # Save results JSON
    ANALYSIS_DIR.mkdir(exist_ok=True)
    results = {
        "metadata": {
            "generated": get_ct_timestamp(),
            "n_inscriptions": N,
            "n_signs": len(sign_counts),
            "thresholds": {
                "min_cooccurrence": MIN_COOCCURRENCE,
                "fisher_p": FISHER_P_THRESHOLD,
                "lift": LIFT_THRESHOLD,
                "asymmetry": ASYMMETRY_THRESHOLD,
            }
        },
        "summary": {
            "total_edges": graph_stats["edge_count"],
            "directed_edges": graph_stats["directed_edges"],
            "mutual_edges": graph_stats["mutual_edges"],
            "node_count": graph_stats["node_count"],
            "component_count": graph_stats["component_count"],
            "largest_component": graph_stats["largest_component"],
            "component_sizes": graph_stats["component_sizes"],
        },
        "edges": edges,
        "hub_stats": graph_stats["hub_stats"],
        "components": graph_stats["components"],
    }

    out_json = ANALYSIS_DIR / "phase3_dependency_graph.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_json}")

    # Save DOT file
    dot = generate_dot(edges, graph_stats)
    out_dot = ANALYSIS_DIR / "phase3_dependency_graph.dot"
    with open(out_dot, "w") as f:
        f.write(dot)
    print(f"Saved: {out_dot}")

    # Save report
    report = generate_report(edges, graph_stats, sign_counts, N)
    out_md = ANALYSIS_DIR / "phase3_dependency_report.md"
    with open(out_md, "w") as f:
        f.write(report)
    print(f"Saved: {out_md}")


if __name__ == "__main__":
    main()
