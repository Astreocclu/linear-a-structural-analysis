<system_meta>
  <id>signal-theory-anth-linear-a-phase3-dep-001</id>
  <tags>
    <agent>signal-theory-anth-linear-a</agent>
    <type>research</type>
    <status>verified</status>
    <project>linear-a</project>
    <time>2026-03-17</time>
  </tags>
  <tldr>Phase 3: Asymmetric dependency graph — 1048 edges, 561 directed, 1 components.</tldr>
</system_meta>

# Phase 3: Asymmetric Dependency Graph

**Generated:** 2026-03-17 17:59 CT
**Corpus:** 1659 inscriptions, 317 distinct signs

---

## Method

For each pair of signs (A, B) co-occurring in the same inscription:

1. **Entry gate** (all three required):
   - N_AB >= 5 (co-occurrence count)
   - Fisher's exact test p < 0.01 (one-sided, greater)
   - lift(A,B) > 3.0

2. **Directionality:**
   - Asymmetry ratio = P(B|A) / P(A|B)
   - Directed edge if ratio > 2.0
   - Mutual edge if neither direction exceeds threshold

3. **Strength classification:**
   - Strong: P(forward) > 0.5 AND P(backward) < 0.1
   - Moderate: P(forward) > 0.3 AND P(backward) < 0.2
   - Weak: passes lift/asymmetry but not conditional thresholds

---

## Summary

| Metric | Value |
|--------|-------|
| Total edges | 1048 |
| Directed edges | 561 |
| Mutual edges (formulas) | 487 |
| Strong dependencies | 36 |
| Moderate dependencies | 338 |
| Weak dependencies | 187 |
| Fixed formulas | 487 |
| Nodes in graph | 95 |
| Connected components | 1 |
| Largest component | 95 nodes |

---

## Verification

| Criterion | Threshold | Observed | Status |
|-----------|-----------|----------|--------|
| Directed edges | >= 10 | 561 | PASS |
| Distinct signs in edges | > 6 | 95 | PASS |
| Not dominated by 2-3 signs | visual check | see hub table | — |

---

## Top Edges by Lift

| Rank | Sign A | Sign B | Direction | N_AB | P(B|A) | P(A|B) | Lift | Fisher p | Strength |
|------|--------|--------|-----------|------|--------|--------|------|----------|----------|
| 1 | U+1070B | U+10717 | mutual | 8 | 0.615 | 0.571 | 72.92 | 2.72e-15 | formula |
| 2 | U+10713 | U+10717 | mutual | 9 | 0.562 | 0.643 | 66.66 | 8.75e-17 | formula |
| 3 | U+10719 | U+1071D | mutual | 5 | 0.357 | 0.556 | 65.83 | 2.38e-09 | formula |
| 4 | U+1070B | U+10713 | mutual | 7 | 0.538 | 0.438 | 55.83 | 2.82e-12 | formula |
| 5 | U+10658 | U+10709 | B->A | 6 | 0.240 | 0.750 | 49.77 | 1.69e-10 | weak |
| 6 | U+1064B | U+10717 | mutual | 7 | 0.368 | 0.500 | 43.66 | 2.44e-11 | formula |
| 7 | U+1064B | U+1070B | mutual | 6 | 0.316 | 0.462 | 40.30 | 1.55e-09 | formula |
| 8 | U+106BB | U+10747 | A->B | 5 | 0.625 | 0.192 | 39.88 | 3.43e-08 | moderate |
| 9 | U+10657 | U+1074D | B->A | 5 | 0.116 | 1.000 | 38.58 | 9.25e-09 | moderate |
| 10 | U+10658 | U+10717 | mutual | 7 | 0.280 | 0.500 | 33.18 | 2.28e-10 | formula |
| 11 | U+1064B | U+10713 | mutual | 6 | 0.316 | 0.375 | 32.74 | 7.08e-09 | formula |
| 12 | U+1065C | U+10747 | A->B | 5 | 0.500 | 0.192 | 31.90 | 1.51e-07 | moderate |
| 13 | U+10656 | U+10717 | mutual | 6 | 0.261 | 0.429 | 30.91 | 9.84e-09 | formula |
| 14 | U+10658 | U+10713 | mutual | 7 | 0.280 | 0.438 | 29.03 | 7.44e-10 | formula |
| 15 | U+10626 | U+10628 | B->A | 5 | 0.156 | 0.556 | 28.80 | 2.31e-07 | moderate |
| 16 | U+10656 | U+10713 | mutual | 6 | 0.261 | 0.375 | 27.05 | 2.58e-08 | formula |
| 17 | U+10649 | U+10709 | B->A | 6 | 0.120 | 0.750 | 24.89 | 1.48e-08 | moderate |
| 18 | U+1064B | U+10658 | mutual | 7 | 0.368 | 0.280 | 24.45 | 3.19e-09 | formula |
| 19 | U+10657 | U+106DA | B->A | 5 | 0.116 | 0.625 | 24.11 | 4.89e-07 | moderate |
| 20 | U+10649 | U+10717 | B->A | 9 | 0.180 | 0.643 | 21.33 | 1.74e-11 | moderate |
| 21 | U+1060C | U+10660 | B->A | 5 | 0.128 | 0.500 | 21.27 | 1.28e-06 | moderate |
| 22 | U+10741 | U+10747 | mutual | 9 | 0.321 | 0.346 | 20.51 | 7.04e-11 | formula |
| 23 | U+10747 | U+10749 | mutual | 8 | 0.308 | 0.308 | 19.63 | 1.46e-09 | formula |
| 24 | U+10657 | U+10741 | mutual | 14 | 0.326 | 0.500 | 19.29 | 1.92e-16 | formula |
| 25 | U+10649 | U+10713 | B->A | 9 | 0.180 | 0.562 | 18.66 | 9.53e-11 | moderate |
| 26 | U+10649 | U+10658 | mutual | 14 | 0.280 | 0.560 | 18.58 | 2.56e-16 | formula |
| 27 | U+10610 | U+1062B | mutual | 5 | 0.227 | 0.238 | 17.95 | 4.48e-06 | formula |
| 28 | U+10649 | U+1070B | B->A | 7 | 0.140 | 0.538 | 17.87 | 2.20e-08 | moderate |
| 29 | U+1060C | U+10648 | mutual | 10 | 0.256 | 0.417 | 17.72 | 2.35e-11 | formula |
| 30 | U+10657 | U+1071A | B->A | 5 | 0.116 | 0.455 | 17.54 | 3.80e-06 | moderate |

---

## Hub Analysis (Top 15 by Total Degree)

| Sign | Count | In-Degree | Out-Degree | Mutual | Total | Role |
|------|-------|-----------|------------|--------|-------|------|
| U+1061E | 106 | 33 | 0 | 25 | 58 | grammatical hub |
| U+10638 | 101 | 28 | 0 | 27 | 55 | grammatical hub |
| U+10602 | 93 | 26 | 0 | 29 | 55 | formula participant |
| U+10746 | 89 | 30 | 0 | 25 | 55 | grammatical hub |
| U+10634 | 96 | 25 | 0 | 28 | 53 | formula participant |
| U+10633 | 141 | 33 | 0 | 18 | 51 | grammatical hub |
| U+10606 | 86 | 19 | 0 | 32 | 51 | formula participant |
| U+1061D | 113 | 32 | 0 | 17 | 49 | grammatical hub |
| U+1061A | 155 | 33 | 0 | 15 | 48 | grammatical hub |
| U+10619 | 105 | 24 | 0 | 24 | 48 | mixed |
| U+10605 | 114 | 25 | 0 | 22 | 47 | grammatical hub |
| U+10607 | 150 | 32 | 0 | 14 | 46 | grammatical hub |
| U+10641 | 96 | 16 | 0 | 30 | 46 | formula participant |
| U+10600 | 104 | 20 | 0 | 25 | 45 | formula participant |
| U+1062D | 61 | 7 | 5 | 31 | 43 | formula participant |

---

## Connected Components

1 components detected. Sizes: [95]

### Component 1 (95 nodes)
Signs: U+10600, U+10601, U+10602, U+10603, U+10604, U+10605, U+10606, U+10607, U+10608, U+10609, U+1060A, U+1060B, U+1060C, U+1060D, U+10610, U+10613, U+10615, U+10617, U+10618, U+10619, U+1061A, U+1061C, U+1061D, U+1061E, U+1061F, U+10620, U+10621, U+10622, U+10623, U+10624, U+10625, U+10626, U+10627, U+10628, U+1062B, U+1062C, U+1062D, U+1062E, U+1062F, U+10630, U+10631, U+10632, U+10633, U+10634, U+10635, U+10636, U+10637, U+10638, U+10639, U+1063A, U+1063B, U+1063D, U+1063E, U+1063F, U+10640, U+10641, U+10642, U+10644, U+10645, U+10647, U+10648, U+10649, U+1064B, U+1064C, U+1064D, U+10653, U+10656, U+10657, U+10658, U+10659, U+1065A, U+1065C, U+10660, U+10662, U+106BB, U+106DA, U+106ED, U+10709, U+1070B, U+10713, U+10717, U+10719, U+1071A, U+1071D, U+10740, U+10741, U+10742, U+10743, U+10744, U+10745, U+10746, U+10747, U+10749, U+1074D, U+10755

---

## Interpretation

- **Grammatical hubs** (high in-degree): Signs that many other signs depend on — likely modifiers, case markers, or structural operators.
- **Independent roots** (high out-degree): Signs that predict others but aren't predicted by them — likely nouns, commodity labels.
- **Formula participants** (high mutual degree): Signs locked into fixed sequences — administrative formulas (cf. Indus KU-RO type).

## Rejected approaches
- Raw P(B|A)/P(A|B) without lift: base-rate blind — high-frequency signs trivially satisfy.
- Chi-square: expected cell counts too small for rare sign pairs.
