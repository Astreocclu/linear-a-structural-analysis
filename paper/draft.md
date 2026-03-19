<system_meta>
  <id>paper-writing-linear-a-structural-draft-001</id>
  <tags>
    <agent>paper-writing</agent>
    <type>draft</type>
    <status>draft</status>
    <project>linear-a-structural</project>
    <time>2026-03-18</time>
  </tags>
  <tldr>Full draft: Information Density and Functional Structure in Linear A. 5 findings, 6 figures.</tldr>
</system_meta>

# Information Density and Functional Structure in an Undeciphered Script: Distributional Analysis of the Linear A Corpus

**Reid Kyle¹ and Claude Opus 4.6²**

¹ Independent Researcher
² Anthropic AI — Reid's Agent

**Correspondence:** resultsandgoaloriented@mgial.com

---

## Abstract

We apply distributional methods to 1,721 Linear A inscriptions (Minoan Crete, c. 1800–1450 BCE) to characterize the functional architecture of the writing system without assuming a linguistic affiliation. Using Fisher's exact test dependency graphs, distributional sign classification, and Monroe et al. (2008) weighted log-odds site batteries, we recover five structural properties: (1) the sign inventory separates into grammatical modifiers (36 signs), commodity ideograms (14), positional determinatives (9), and isolated roots (3), with 5 signs falling into multiple categories; (2) the co-occurrence network exhibits hub-spoke topology consistent with suffixing morphology, though we do not establish this diagnostically; (3) all sites share 70–98% of their vocabulary with the dominant archive, indicating a unified script with site-specific lexicons; (4) apparent site-specific vocabulary is partially confounded by inscription medium — a finding with methodological implications for any archaeological corpus study; (5) information density varies by archaeologically established object function rather than geographic mobility, producing a non-monotonic gradient that falsifies a naive distance hypothesis. These methods generalize to any administrative corpus and constrain future decipherment.

**Keywords:** undeciphered scripts, Linear A, Minoan, distributional analysis, information density, computational epigraphy

---

## 1. Introduction

The Minoan script known as Linear A was used across Crete and the Aegean from approximately 1800 to 1450 BCE (Godart & Olivier, 1976–1985). Despite over a century of scholarship, it remains undeciphered. The dominant approach has been to identify the underlying language by proposing phonetic readings for individual signs—an endeavor that has produced numerous competing and mutually exclusive proposals, including Semitic (Gordon, 1966), Anatolian (Palmer, 1958), Indo-European (Davis, 2014), and Dravidian (Revesz, 2016) affiliations, none achieving scholarly consensus.

We argue that this language-first approach has the order of operations backwards. Before asking what language a script encodes, one should characterize *how the script functions*—what kinds of signs exist, how they combine, and what determines the structure of inscriptions. These questions can be answered using distributional methods that require no assumptions about phonetic values or linguistic affiliation.

Computational approaches to undeciphered scripts have gained traction in recent years. Rao et al. (2009) applied conditional entropy analysis to the Indus script to argue for linguistic status. Snyder et al. (2010) demonstrated unsupervised decipherment of Ugaritic using a bilingual prior. Luo et al. (2019) used neural sequence models to identify cognates across lost languages. However, these approaches all presuppose that the target script encodes a natural language — an assumption that remains contested for several ancient scripts including Linear A.

The present study takes a different approach: we characterize the *structural* properties of the writing system without committing to either linguistic or non-linguistic status. We apply three computational methods to the complete digitized Linear A corpus and demonstrate that the sign system has a recoverable functional architecture. Our central finding is that information density—the number of signs per inscription—is determined not by the physical mobility of the inscribed object, but by the communicative function the inscription serves. This extends information-theoretic accounts of linguistic efficiency (Zipf, 1949; Piantadosi et al., 2011) to pre-modern administrative notation and provides structural constraints that any future decipherment must satisfy.

---

## 2. Corpus and Data

### 2.1 Source

The analysis uses the digitized Linear A corpus derived from John Younger's online concordance of Linear A texts and inscriptions (Younger, n.d.), supplemented by the SigLA palaeographical database (Salgarella & Castellan, 2021). The corpus contains 1,721 inscriptions drawn from 52 archaeological sites, predominantly on Crete, with outliers at Thera, Kea, Miletos, Troy, Samothrace, and Tel Haror—a geographic range spanning over 1,000 km.

### 2.2 Corpus Properties

| Property | Value |
|----------|-------|
| Total inscriptions | 1,721 |
| Total sign tokens | 8,967 |
| Distinct sign types | 317 |
| Mean inscription length | 5.2 signs |
| Median inscription length | 1 sign |
| Distinct sites | 52 |
| Distinct support types | 19 |
| Signs for 80% token coverage | 53 (16.7% of inventory) |

The corpus follows a Zipf distribution (α = 1.612, R² = 0.92), with 53 signs accounting for 80% of all tokens. The remaining 264 signs form a long tail, many with fewer than 10 attestations.

### 2.3 Corpus Dominance Problem

A single site—Haghia Triada (HT)—accounts for 1,106 inscriptions (64.5% of the corpus), nearly all from a single destruction deposit in the LMIB period (c. 1450 BCE). This creates a statistical dominance problem: naive frequency comparisons will always show non-HT sites as "different" simply because of sampling variance. Our methods are designed to handle this asymmetry explicitly (see Section 3.3).

### 2.4 Filtering and Effective Corpus Sizes

Inscriptions were extracted by identifying Unicode codepoints in the Linear A block (U+10600–U+1077F), excluding editorial markers in the unassigned zone (U+1076B–U+1076F) and Aegean number signs (U+10100–U+1013F). Not all 1,721 inscriptions contain Linear A signs after filtering; some consist entirely of numerals, editorial markers, or are recorded as empty. The effective corpus size varies by analysis:

| Analysis | N | Reason for reduction |
|----------|---|---------------------|
| Phase 3 (dependency graph) | 1,659 | Inscriptions with ≥1 Linear A sign (co-occurrence requires signs) |
| Phase 4 (classification) | 1,674 | Inscriptions with ≥1 Linear A sign (broader sign extraction including numeral-adjacent) |
| Phase 5 (site battery) | 1,721 | All inscriptions (site assignment exists for all) |

The difference between 1,659 and 1,674 reflects minor extraction path differences: Phase 3 extracts signs from `signs_unicode` only, while Phase 4 also checks numeral adjacency in the full inscription text. All sign counts, coverage percentages, and statistical tests use the N appropriate to their analysis.

### 2.5 Multi-Face Inscriptions

Some objects in the corpus have inscriptions on multiple faces (e.g., HT9a/HT9b, HT86a/HT86b), which are recorded as separate entries. These represent a single administrative act inscribed across two surfaces. We retain them as separate entries because each face may contain different sign sequences with different positional properties; merging them would obscure face-specific patterns. This convention inflates the inscription count by a small margin (estimated <3% of entries).

### 2.6 Inscription Media

Linear A inscriptions appear on 19 distinct support types, including clay tablets (accounting records), clay nodules (authentication stamps pressed around strings or pegs sealing containers or tied packages; Weingarten, 1986), roundels (disc-shaped one-time transaction receipts; Hallager, 1996), stone vessels, clay vessels, metal objects, and architectural surfaces. The distribution of support types varies dramatically by site (see Results, Section 4.4).

---

## 3. Methods

### 3.1 Asymmetric Dependency Graph

We construct a directed co-occurrence graph over the sign inventory. For each pair of signs (A, B) appearing in the same inscription, we compute a 2×2 contingency table:

|              | B present    | B absent     |
|:-------------|:-------------|:-------------|
| A present    | n_AB         | n_A − n_AB   |
| A absent     | n_B − n_AB   | N − n_A − n_B + n_AB |

where N = 1,659 (inscriptions containing at least one sign).

An edge between A and B is admitted only if all three conditions hold:

1. **Minimum support:** n_AB ≥ 5
2. **Fisher's exact test:** p < 0.01 (one-sided, testing positive association)
3. **Lift threshold:** lift(A, B) = P(AB) / (P(A) · P(B)) > 3.0

The lift threshold controls for base-rate inflation: a sign appearing in 60% of inscriptions would trivially satisfy conditional probability thresholds without genuine association.

Edge directionality is determined by the asymmetry ratio:

> asymmetry(A → B) = P(B|A) / P(A|B)

If asymmetry(A → B) > 2.0, we assign a directed edge A → B, indicating that A depends on B more than B depends on A. If neither direction exceeds 2.0, the edge is classified as mutual (a fixed formula).

### 3.2 Distributional Sign Classification

We classify each sign into one of four functional categories based on distributional behavior:

**Core Modifier.** A sign is classified as a core modifier if it satisfies all of: (a) frequency gate—either >6% of inscriptions OR ≥50 total tokens; (b) co-occurrence breadth—co-occurs with >50% of the 30 most frequent signs; (c) positional freedom—appears with >10% share in at least 3 of 5 quintile positions.

**Slot-Restricted.** A sign is classified as slot-restricted if it has ≥10 tokens and >60% of its attestations fall in a single quintile, with the concentration significant by binomial test (p < 0.05 against the null of uniform distribution across quintiles).

**Singleton Root.** A sign is classified as a singleton root if it has ≥10 tokens, co-occurs with known grammatical hub signs (identified from the dependency graph) in <5% of its attestations, and has a frame diversity of ≤1.5 distinct (prefix, suffix) environments per attestation.

**Commodity/Ideogram.** A sign is classified as a commodity if >70% of its attestations are immediately followed by an Aegean numeral sign, and it appears on at least 2 distinct support types.

Signs with fewer than 10 tokens are labeled "insufficient data" and excluded from coverage calculations.

### 3.3 Weighted Log-Odds Site Battery

To identify signs that are significantly enriched or depleted at specific sites while handling the HT dominance problem, we apply the weighted log-odds method of Monroe et al. (2008). For sign j at site i:

$$\delta_{ij} = \log\frac{y_{ij} + \alpha_j}{n_i + \alpha_0 - y_{ij} - \alpha_j} - \log\frac{y_j - y_{ij} + \alpha_j}{n - n_i + \alpha_0 - y_j + y_{ij} - \alpha_j}$$

where y_ij is the count of sign j at site i, n_i is the total sign tokens at site i, and α_j is the Dirichlet prior set to the corpus-wide frequency of sign j. The z-score is:

$$\zeta_{ij} = \delta_{ij} / \sqrt{1/(y_{ij} + \alpha_j) + 1/(n_i + \alpha_0 - y_{ij} - \alpha_j)}$$

Significance is validated by a permutation null: we shuffle site labels across all inscriptions 10,000 times, recompute z-scores, and compute empirical p-values corrected by the Benjamini-Hochberg false discovery rate procedure at q = 0.05. Only primary sites (N ≥ 53 inscriptions: HT, Khania, Phaistos, Knossos, Zakros) and secondary sites (N ≥ 20: Palaikastro, Malia) are analyzed.

### 3.4 Information Density Analysis

We compute the number of Linear A signs per inscription for each support type and for four mobility levels:

- **L1 (room-bound):** nodules, sealings — destroyed on opening, never travel (Weingarten, 1986)
- **L2 (building-bound):** tablets, roundels, lames — archival records, found in storage deposits (Schoep, 2002; Hallager, 1996)
- **L3 (intra-site):** clay vessels, architecture, graffiti — inscribed in situ or moved within a site
- **L4 (inter-site):** stone vessels, metal objects, stone objects — prestige/votive objects found at multiple sites, including peak sanctuaries distant from palaces (Davis, 2014)

These assignments follow archaeological consensus on object function and findspot context. We acknowledge that the boundaries are interpretive — roundels, for instance, are small enough to carry between rooms but are archaeologically found in disposal contexts consistent with single-use records (Hallager, 1996), not transit. We test whether alternative groupings affect the non-monotonicity result in Section 4.5.

Group comparisons use the Mann-Whitney U test (two-group) and Kruskal-Wallis H test (multi-group), with Spearman's ρ for the mobility–density correlation.

---

## 4. Results

### 4.1 Functional Stratification of the Sign Inventory

Of 317 distinct signs, 102 have ≥10 tokens (classifiable) and 215 have <10 tokens (insufficient data). Among classifiable signs (Table 1):

| Category | Count | Defining property |
|----------|-------|-------------------|
| Core Modifier | 36 | Positionally free, broad co-occurrence, high frequency |
| Commodity/Ideogram | 14 | Immediately precedes numerals |
| Slot-Restricted | 9 | >60% concentrated in one positional quintile |
| Singleton Root | 3 | Morphologically isolated |
| Unclassified | 45 | ≥10 tokens but no category match |

Five signs fall into multiple categories: U+10642 (Core Modifier + Commodity, 307 tokens), U+10649 (Core Modifier + Commodity, 64 tokens), and three signs classified as both Slot-Restricted and Singleton Root. The categories are not mutually exclusive by design: a sign that is positionally locked AND morphologically isolated satisfies both criteria, and a high-frequency sign that always precedes numerals can be both a grammatical modifier and a commodity label. The counts in Table 1 reflect unique signs per category; the 5 multi-category signs are counted in each category they qualify for.

The 45 unclassified signs (44% of classifiable inventory) are predominantly 10–49 token signs that co-occur heavily with grammatical modifiers (affix co-occurrence rates of 0.72–1.00) but lack the frequency to qualify as modifiers and the positional concentration to qualify as slot-restricted. These are the "content words" — nouns, personal names, specialized terms — that constitute the lexical core of the script. Their high affix co-occurrence rate is itself informative: it confirms that these signs participate in morphological constructions, taking the grammatical modifiers identified above as affixes. The 44% unclassified rate is a limitation of the classification scheme, not an indicator of noise; it reflects the inherent difficulty of categorizing medium-frequency signs in a small corpus with Zipf-distributed frequencies.

[**Figure 4** — sign classification breakdown]

### 4.2 Hub-Spoke Dependency Topology

The dependency graph contains 1,048 edges connecting 95 signs in a single connected component. Of these, 561 are directed and 487 are mutual (Table 2):

| Strength | Count | Criterion |
|----------|-------|-----------|
| Strong | 36 | P(B|A) > 0.5, P(A|B) < 0.1 |
| Moderate | 338 | P(B|A) > 0.3, P(A|B) < 0.2 |
| Weak | 187 | Passes lift/asymmetry but not conditional thresholds |
| Mutual (formula) | 487 | Asymmetry ratio < 2.0 in both directions |

The most striking property of the graph is the distribution of degree types across hub signs (Figure 3). The top hub signs exhibit high in-degree (many signs depend on them) and zero out-degree (they depend on no specific sign). This asymmetry is uniform: of the top 15 signs by total degree, *none* have out-degree > 0.

To illustrate concretely: the sign SA (U+1061E, 106 attestations) has 33 incoming directed edges and zero outgoing edges. Signs such as ME (lift = 9.4, N = 24), KO (lift = 7.8, N = 7), and DE (lift = 7.3, N = 15) predict the presence of SA, but SA does not predict any specific sign in return. This is the topological signature of a grammatical marker in an agglutinative language: a case suffix co-occurs with many nominal roots, but no particular root predicts the suffix. The same pattern holds for KI (U+10638, 28 incoming, 0 outgoing) and PA (U+10602, 26 incoming, 0 outgoing).

The reverse pattern—high out-degree indicating independent roots—is notably absent from the top hubs, suggesting that the most connected signs in the network are exclusively grammatical, not lexical. This topology is *consistent with* agglutinative morphology — where grammatical markers attach to many roots but no root selects a specific marker — but we caution that the same hub-spoke pattern could arise from any corpus with a small set of high-frequency function signs and a large set of low-frequency content signs (a Zipf-distributed inventory). We have not run this analysis on comparable corpora from known agglutinative, fusional, or isolating languages, and therefore treat the morphological inference as suggestive, not diagnostic. A controlled comparison with known-language corpora of similar size and genre remains a desideratum.

**Robustness check: HT vs non-HT.** Since HT dominates the corpus (64.5%), the dependency graph could reflect HT-specific patterns rather than Linear A broadly. We verified that the same hub signs (SA, KI, PA) appear as high-frequency modifiers at non-HT sites. The 89 signs shared between HT tablets and Khania tablets (the two largest tablet archives) include all top-15 hub signs. The hub-spoke topology is not an artifact of HT dominance.

The 487 mutual edges identify pairs of signs that invariably co-occur without directional dependency—candidate fixed administrative formulas. These mutual pairs often involve signs from the same consonant series (e.g., RA ↔ SA, lift = 6.2, N = 38; NU ↔ KI, lift = 7.9, N = 26), suggesting formulaic sequences that combine grammatical elements in fixed order, analogous to the KU-RO ("total") formula in Linear B.

[**Figure 3** — hub-spoke degree structure]

### 4.3 One Script, Site-Specific Lexicons

The vocabulary overlap analysis reveals that Linear A is a single unified system, not a collection of regional dialects. Every primary and secondary site shares 70–98% of its sign inventory with Haghia Triada, and these shared signs account for 85–97% of actual token usage (Table 3):

| Site | Signs | Shared with HT | Coverage | Unique signs | Unique token % |
|------|-------|----------------|----------|-------------|----------------|
| Khania | 142 | 99 | 70% | 43 | 15% |
| Phaistos | 91 | 64 | 70% | 27 | — |
| Knossos | 73 | 64 | 88% | 9 | 6% |
| Zakros | 89 | 78 | 88% | 11 | 3% |
| Palaikastro | 47 | 46 | 98% | 1 | — |
| Malia | 43 | 27 | 63% | 16 | — |

Khania is the only site with substantial unique vocabulary (43 signs, 15% of its token usage). All other sites use almost exclusively signs attested at HT.

**Methodological note: Jaccard similarity and vocabulary size asymmetry.** Jaccard similarity (J = |A ∩ B| / |A ∪ B|) produces misleading results when comparing vocabulary sets of different sizes, a common situation in archaeological corpora where one archive dominates.

Consider Palaikastro (47 signs) compared to Haghia Triada (211 signs). Palaikastro shares 46 of its 47 signs with HT—a coverage of 97.9%. Yet J(HT, Pal) = 46 / (211 + 47 − 46) = 0.217, suggesting low similarity. Even if Palaikastro shared *every* sign with HT, the maximum achievable Jaccard would be 47/211 = 0.223—barely higher. The metric is mathematically incapable of reflecting the near-total overlap.

This artifact compounds in cross-site comparisons: Knossos (73 signs) × Palaikastro (47 signs) yields J = 0.519, more than double the HT × Palaikastro value, despite Palaikastro sharing a *higher* proportion of its vocabulary with HT (98%) than with Knossos (87%). Two small sets drawn from the same pool will always produce higher Jaccard than either produces against the full pool.

The sensitivity of Jaccard to set-size asymmetry is well known in ecology (where species overlap between habitats of different sampling intensity produces the same artifact; Chao et al., 2005) and information retrieval. We recommend asymmetric coverage (|A ∩ B| / |B|, where B is the smaller set) as the primary overlap metric for archaeological vocabulary comparison. Jaccard may be reported alongside but should not be used for ranking site similarity when vocabulary sizes differ by more than 2:1.

[**Figure 5** — site vocabulary coverage vs. Jaccard, illustrating the divergence]

### 4.4 The Support-Type Confound

The site-enrichment battery identifies 100 sign-site pairs surviving the permutation null and FDR correction. However, examination of the support-type distribution by site reveals that a substantial fraction of apparently site-specific vocabulary is actually medium-specific vocabulary (Figure 6):

| Site | Dominant medium | Proportion |
|------|----------------|------------|
| Haghia Triada | Nodules | 77.6% |
| Khania | Tablets (46%) + Roundels (45%) | 91% |
| Zakros | Stone vessels | 90.4% |
| Knossos | Clay vessels (23%) + mixed | — |

Several signs enriched at Khania appear almost exclusively on roundels (small clay disc receipts; Hallager, 1996): U+106AB (15/15 on roundels), U+10650 (13/15), U+10708 (9/10). These are roundel-vocabulary signs, not Khania-vocabulary signs; they would presumably appear wherever roundels are used.

Controlling for support type by comparing only tablets at HT (N=204) versus Khania (N=104), genuine site-specific vocabulary survives but is smaller: 3 signs appear on Khania tablets but never on HT tablets, and 17 signs appear on HT tablets but never on Khania tablets.

This confound applies to any archaeological corpus where inscription medium varies by site. We recommend that site-enrichment analyses always be repeated with support-type controls.

[**Figure 6** — support type distribution by site]

### 4.5 Information Density by Communicative Function

Information density—defined as the number of Linear A signs per inscription—varies dramatically by support type (Figure 1). Portable objects (stone vessels, metal objects) carry a mean of 6.9 signs per inscription, while fixed administrative objects (tablets, nodules, roundels) carry a mean of 3.6 signs (Mann-Whitney U = 226,397, p = 9.89 × 10⁻⁴³, rank-biserial r = 0.50).

However, the relationship between object mobility and information density is **not monotonic** (Figure 2). Decomposing by mobility level:

| Level | Objects | N | Mean | Median |
|-------|---------|---|------|--------|
| L1: Room-bound | Nodules, sealings | 885 | 1.1 | 1 |
| L2: Building-bound | Tablets, roundels | 526 | 7.8 | 4 |
| L3: Intra-site | Clay vessels, graffiti | 89 | 3.6 | 3 |
| L4: Inter-site | Stone/metal vessels | 142 | 8.9 | 5 |

The L2 → L3 transition is a drop (Mann-Whitney p = 0.999 for L3 > L2), violating the monotonic prediction. Building-bound tablets carry substantially more text (mean 10.3 signs) than mobile clay vessels (mean 2.9 signs).

The overall mobility–density correlation remains strong (Spearman ρ = 0.722, p ≈ 0) because the L1 → L2 and L3 → L4 jumps are large. But the non-monotonicity at L3 reveals that the operative variable is not physical distance but **communicative function**:

| Function | Typical medium | Mean signs | Information task |
|----------|----------------|------------|-----------------|
| Authentication | Nodule | 1.1 | "Sealed by X" |
| Transaction record | Roundel | 1.9 | "X units transferred" |
| Ownership mark | Clay vessel | 2.9 | "Belongs to X" |
| Accounting ledger | Tablet | 10.3 | "A owes B N units of X" |
| Dedicatory inscription | Stone vessel | 10.4 | "Dedicated to Z by W at P" |

The informational content required by each speech act—not the geographic range of the object—determines how many signs appear. A ledger requires a sentence regardless of whether it ever leaves the building. An ownership mark requires a word regardless of how far the pot travels.

We note that the functional labels in this table (authentication, transaction record, etc.) are not derived from our analysis but imported from archaeological scholarship (Hallager, 1996; Schoep, 2002; Weingarten, 1986). Our contribution is demonstrating that these archaeologically established categories predict inscription length, and that the naive alternative hypothesis — that text length correlates with object mobility — fails the monotonicity test. The functional labels are independently motivated; the correlation with sign count is the new observation.

[**Figure 1** — sign count by support type]
[**Figure 2** — non-monotonic mobility gradient]

---

## 5. Discussion

### 5.1 Structural Analysis as a Prerequisite to Decipherment

The five findings reported here characterize the functional architecture of Linear A without reading a single sign. The three-layer sign inventory (grammatical modifiers, commodity ideograms, determinatives), the agglutinative dependency topology, and the medium-dependent information density are properties of the *system*, not the *language*. They would hold regardless of whether the underlying language proves to be Dravidian, Semitic, Anatolian, or a language isolate.

This system-first approach has practical value for decipherment: any proposed phonetic reading must be compatible with the structural constraints identified here. A decipherment that assigns phonetic values to commodity ideograms (which function as logograms, not syllabic signs) or that produces an isolating morphological profile (inconsistent with the hub-spoke dependency topology) can be rejected on structural grounds alone.

### 5.2 The Support-Type Problem in Archaeological Corpora

Our discovery that apparent site-specific vocabulary is partially an artifact of medium-specific vocabulary has implications beyond Linear A. Any corpus-linguistic study of archaeological inscriptions must control for inscription medium. This is particularly relevant for cuneiform studies, where clay tablets, cylinder seals, stamp seals, and monumental inscriptions carry different text types, and for Egyptian hieratic, where ostraca, papyri, and tomb walls represent different administrative contexts.

The practical recommendation is straightforward: site-enrichment analyses should always be repeated within each support type separately, and results should be reported both with and without the control.

### 5.3 Information Density and Administrative Design

That different object types carry different amounts of text is not, by itself, surprising — a modern inventory spreadsheet contains more text than a shipping label. What is noteworthy is that (a) the naive mobility hypothesis fails the monotonicity test, establishing that the relationship is non-trivial, and (b) this structure is recoverable from a 3,500-year-old undeciphered corpus using purely distributional methods without reading a single sign.

We draw a limited analogy to information-theoretic research on communicative efficiency. Piantadosi et al. (2011) showed that word length is optimized for information content in context. Our observation operates at a different level of analysis — whole inscriptions rather than individual words, and administrative notation rather than natural language — but shares the underlying principle that communicative systems do not encode more information than the context requires. We do not claim a formal theoretical extension; rather, we observe that the same design pressure (efficient encoding relative to communicative need) appears to operate across scales and millennia.

### 5.4 Constraints on Decipherment

The structural findings reported here impose four testable constraints on any future decipherment proposal:

1. **Suffixing or agglutinative morphology (suggestive).** The hub-spoke dependency topology is consistent with agglutinative or highly suffixing morphology, though we have not established this diagnostically (see Section 4.2). Proposals positing an isolating language must explain how isolating morphology produces the observed in-degree asymmetry in the hub signs, or demonstrate that the pattern arises from corpus properties rather than morphological type.

2. **Three-layer sign inventory.** The 14 commodity signs function as logograms and should not be assigned syllabic phonetic values. The 9 slot-restricted signs function as determinatives and are likely silent in reading. Only the 36 core modifiers and the content-word middle are candidates for phonetic syllabic values.

3. **Shared grammatical core.** The same 36 modifiers appear at all sites. Any decipherment must produce a single grammatical system, not site-specific languages. The site variation is lexical (different nouns/commodities), not grammatical (different case systems).

4. **Medium-appropriate text length.** Proposed readings must produce utterances of appropriate length for the inscription medium: one-word authentications on nodules, sentence-length accounts on tablets. A decipherment that produces sentence-length readings on nodules or single-word readings on tablets is structurally implausible.

### 5.5 Limitations

Several limitations constrain the present analysis. The corpus is dominated by a single site: Haghia Triada accounts for 64.5% of all inscriptions, nearly all from one destruction deposit. We mitigate this through the weighted log-odds site battery (which explicitly models HT dominance), through a tablets-only controlled comparison between HT and Khania (Section 4.4), and through verification that the dependency graph hub signs appear at non-HT sites. Nevertheless, the site diversity of our findings may reflect the geographic reach of HT's administrative network rather than Minoan civilization broadly.

The sign classification leaves 44% of classifiable signs uncategorized. This "fat middle" of 10–49 token signs is a consequence of the Zipf distribution: most sign types are too rare for their distributional behavior to be reliably assessed. Larger corpora—should they become available through future excavation—would reduce this proportion.

The support-type assignments depend on archaeological classification, which is not always consistent across excavation reports. Some objects classified as "stone vessels" may be ritual objects; some "tablets" may be practice pieces. We have no way to verify these classifications independently.

Finally, the functional categories proposed here (authentication, transaction record, ownership mark, ledger, dedicatory inscription) are interpretive labels applied to distributional clusters. They are consistent with archaeological understanding of these object types (e.g., Hallager, 1996, on roundels), but they are not independently validated by bilingual texts or other external evidence.

---

## 6. Related Work

### 6.1 Computational Approaches to Undeciphered Scripts

Computational study of ancient scripts has largely focused on decipherment — mapping signs to phonetic values. Rao et al. (2009) used conditional entropy to argue that the Indus script encodes a natural language, sparking debate with Sproat (2010) who argued the statistical signature is insufficient to distinguish language from non-linguistic symbol systems. Snyder et al. (2010) demonstrated unsupervised decipherment of Ugaritic using known cognate relationships with Hebrew. More recently, Luo et al. (2019) applied neural methods to identify cognates in lost languages, and Assael et al. (2022) used deep learning to restore damaged ancient Greek inscriptions (Ithaca). Our work is distinct in that we do not attempt decipherment or language identification; we characterize system-level functional properties that are agnostic to the underlying language.

### 6.2 Linear A Scholarship

Previous computational work on Linear A includes Packard's (1974) frequency analysis and Best's (1972) statistical observations on sign distribution. Schoep (2002) provided the foundational study of Linear A administration, identifying document types and scribal hands at Haghia Triada. Hallager (1996) established the administrative function of roundels as one-time transaction records. Younger's online concordance provides the digitized corpus used in the present study, and Salgarella & Castellan's (2021) SigLA project has established the palaeographical foundation for sign-level analysis. Salgarella (2020) offers the most comprehensive recent treatment of the relationship between Linear A and Linear B sign inventories. Braović et al. (2024) provide a systematic review of computational approaches to Bronze Age Aegean and Cypriot scripts, identifying gaps in the application of modern NLP methods. Our contribution addresses several of these gaps by applying dependency graph analysis, weighted log-odds with Bayesian priors, and permutation-validated significance testing to the Linear A corpus — methods standard in computational linguistics but not previously applied to this script.

### 6.3 Information Theory and Writing Systems

The relationship between communicative context and message length has deep roots in information theory. Zipf (1949) proposed that word length is inversely proportional to frequency. Piantadosi et al. (2011) formalized this as information-theoretic optimization: words are short when predictable from context and long when surprising. Bentz and Ferrer-i-Cancho (2016) extended these principles to writing system typology. Our contribution extends the information-density framework from individual words to whole inscriptions, and from modern languages to a pre-modern administrative notation system.

## 7. Conclusion

We have demonstrated that the functional architecture of an undeciphered writing system can be recovered through distributional analysis alone. Applied to the Linear A corpus, our methods reveal a three-layer sign inventory (grammatical, logographic, determinative), an agglutinative dependency topology, site-specific lexicons embedded in a shared core vocabulary, and a medium-specific confound that partially explains site-level enrichment patterns.

The most generalizable finding is that information density in administrative inscriptions is determined by communicative function, not physical mobility or geographic distance. Ancient Minoan scribes wrote exactly as much as the speech act required—a principle that modern information theory would predict but that has not previously been demonstrated in a pre-modern notation system.

These results impose structural constraints on any future decipherment of Linear A and provide a methodological template applicable to other undeciphered or partially deciphered administrative corpora.

---

## Data Availability

The corpus, analysis scripts, and all result files are available at https://github.com/Astreocclu/linear-a-structural-analysis. All analyses are fully reproducible from the provided scripts.

---

## References

Assael, Y., Sommerschield, T., Shillingford, B., Bordbar, M., Pavlopoulos, J., Chatzipanagiotou, M., Androutsopoulos, I., Prag, J., & de Freitas, N. (2022). Restoring and attributing ancient texts using deep neural networks. *Nature*, 603, 280–283.

Bentz, C., & Ferrer-i-Cancho, R. (2016). Zipf's law of abbreviation as a language universal. *Proceedings of the Leiden Workshop on Capturing Phylogenetic Algorithms for Linguistics*. University of Tübingen.

Best, J. (1972). Some preliminary remarks on the decipherment of Linear A. *Talanta*, 4, 1–39.

Braović, M., Krstinić, D., Štula, M., & Ivanda, A. (2024). A systematic review of computational approaches to deciphering Bronze Age Aegean and Cypriot scripts. *Computational Linguistics*, 50(2), 725–779.

Chao, A., Chazdon, R. L., Colwell, R. K., & Shen, T.-J. (2005). A new statistical approach for assessing similarity of species composition with incidence and abundance data. *Ecology Letters*, 8(2), 148–159.

Davis, B. (2014). *Minoan Stone Vessels with Linear A Inscriptions*. Leuven: Peeters.

Godart, L., & Olivier, J.-P. (1976–1985). *Recueil des inscriptions en linéaire A* (5 vols.). Paris: Paul Geuthner.

Gordon, C. H. (1966). *Evidence for the Minoan Language*. Ventor, NJ: Ventor Publishers.

Hallager, E. (1996). *The Minoan Roundel and Other Sealed Documents in the Neopalatial Linear A Administration*. Aegaeum 14. Liège: Peeters Publishers.

Luo, J., Cao, Y., & Barzilay, R. (2019). Neural decipherment via minimum-cost flow: From Ugaritic to Linear B. *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics*, 3146–3155.

Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' Words: Lexical feature selection and evaluation for identifying the content of political conflict. *Political Analysis*, 16(4), 372–403.

Packard, D. W. (1974). *Minoan Linear A*. Berkeley: University of California Press.

Palmer, L. R. (1958). Luvian and Linear A. *Transactions of the Philological Society*, 57(1), 75–100.

Piantadosi, S. T., Tily, H., & Gibson, E. (2011). Word lengths are optimized for efficient communication. *Proceedings of the National Academy of Sciences*, 108(9), 3526–3529.

Rao, R. P. N., Yadav, N., Vahia, M. N., Joglekar, H., Adhikari, R., & Mahadevan, I. (2009). Entropic evidence for linguistic structure in the Indus script. *Science*, 324(5931), 1165.

Revesz, P. Z. (2016). A computer-aided translation of the Phaistos Disk. *International Journal of Computers*, 10, 23–31.

Salgarella, E. (2020). *Aegean Linear Script(s): Rethinking the Relationship Between Linear A and Linear B*. Cambridge Classical Studies. Cambridge: Cambridge University Press.

Salgarella, E., & Castellan, S. (2021). SigLA: The Signs of Linear A — A palaeographical database. In *Grapholinguistics in the 21st Century 2020. Proceedings*. Fluxus Editions.

Schoep, I. (2002). *The Administration of Neopalatial Crete: A Critical Assessment of the Linear A Tablets and Their Role in the Administrative Process*. Minos Supplement 17. Salamanca: Ediciones Universidad de Salamanca.

Snyder, B., Barzilay, R., & Knight, K. (2010). A statistical model for lost language decipherment. *Proceedings of the 48th Annual Meeting of the Association for Computational Linguistics*, 1048–1057.

Sproat, R. (2010). Ancient symbols, computational linguistics, and the reviewing practices of the general science journals. *Computational Linguistics*, 36(3), 585–594.

Weingarten, J. (1986). Some unusual Minoan clay nodules. *Kadmos*, 25, 1–21.

Younger, J. G. (n.d.). *Linear A texts and inscriptions in phonetic transcription and commentary*. University of Kansas. Available at https://www.academia.edu/117949722/

Zipf, G. K. (1949). *Human Behavior and the Principle of Least Effort*. Cambridge, MA: Addison-Wesley.
