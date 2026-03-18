# Information Density and Functional Structure in Linear A

**Reid Kyle and Claude Opus 4.6**

Distributional analysis of the Linear A corpus (1,721 inscriptions, Minoan Crete, c. 1800-1450 BCE) revealing the functional architecture of the writing system without assuming a linguistic affiliation.

## Key Findings

1. **Functional stratification**: 36 grammatical modifiers, 14 commodity ideograms, 9 positional determinatives, 3 isolated roots
2. **Agglutinative dependency topology**: Hub-spoke co-occurrence network with high in-degree / zero out-degree hubs
3. **Unified script with site-specific lexicons**: All sites share 70-98% of vocabulary with the dominant archive
4. **Support-type confound**: Apparent site-specific vocabulary is partially driven by inscription medium (nodules vs roundels vs tablets)
5. **Information density by function**: Signs per inscription scales with communicative function, not object mobility (non-monotonic gradient)

## Repository Structure

```
paper/          Draft manuscript
scripts/        Analysis pipeline (Python)
  phase3_dependency_graph.py     Fisher/lift dependency analysis
  phase4_sign_classification.py  Distributional sign classification
  phase5_site_concentration.py   Monroe et al. weighted log-odds site battery
  paper_figures.py               Figure generation
  parse_corpus.py                Corpus parser
data/
  corpus/       Canonical corpus (1,721 inscriptions as JSON)
  dictionaries/ Reference data (PD morpheme dictionary)
analysis/       Results (JSON + markdown reports)
figures/        Publication figures (PNG + PDF)
```

## Reproducing the Analysis

```bash
# Requirements: Python 3.10+, scipy, numpy, matplotlib
pip install scipy numpy matplotlib

# Run the pipeline (from repo root)
python scripts/phase3_dependency_graph.py
python scripts/phase4_sign_classification.py
python scripts/phase5_site_concentration.py
python scripts/paper_figures.py
```

Note: Scripts expect the corpus at `data/corpus/canonical_corpus.json` relative to the script's parent directory. Adjust paths if running from a different location.

## Data Source

Corpus derived from John Younger's Linear A concordance and the SigLA palaeographical database (Salgarella & Castellan, 2021).

## License

Data and analysis scripts are provided for research purposes. The Linear A corpus is derived from publicly available scholarly resources.

## Citation

```
Kyle, R., & Claude Opus 4.6. (2026). Information Density and Functional Structure
in an Undeciphered Script: Distributional Analysis of the Linear A Corpus. Preprint.
```
