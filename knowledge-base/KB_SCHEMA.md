# Moon-Research Knowledge Base Schema

> **Note**: Wikilinks in this schema document (e.g., `[[module-slug-1]]`) are illustrative placeholders
> showing the format of the `connections` and `composable_with` fields. They do not reference actual
> KB entries. The `kb_check.py` script is configured to skip this file during wikilink validation.

## Architecture

The KB is organized around four entity types connected by a pipeline: **Papers** contain **Modules** which combine into **Ideas** which target **Venues**. Sessions, experiments, and insights provide supporting context.

```
Papers ──> Modules ──> Ideas ──> Venues
  │          │           │
  │   (paper contains    │   (modules from      │   (idea targets
  │    multiple modules) │    multiple papers   │    specific venues)
  │                      │    combine into idea)
  │                      │
  └── Each paper is decomposed into its constituent methodological modules.
      Each module is independently validated against paper evidence.
      Validated modules from different papers are recombined into novel ideas.
```

## Entity Specifications

### Paper Entry

```yaml
type: paper
domain: gnn | vla-vlm
title: "Full paper title"
authors: "First Author et al."
year: YYYY
venue: "Conference or Journal Name"
venue_tier: CCF-A | CCF-B | CCF-C | Workshop | Preprint
code_available: true | false
code_url: "URL or null"
code_verified: true | false | null  # Have we confirmed the code runs?
novelty_level: paradigm-shift | high | medium | incremental
  # paradigm-shift: opens a new sub-field
  # high: solves a previously unsolved problem
  # medium: significant improvement over existing methods
  # incremental: minor modification of existing method
validation_quality: strong | moderate | weak
  # strong: >=5 datasets, multiple baselines, ablation, statistical tests, code available
  # moderate: 3-4 datasets, reasonable baselines, some ablation
  # weak: <3 datasets, limited baselines, no ablation
modules: [[module-slug-1]], [[module-slug-2]], ...  # Decomposed from this paper
key_contribution: "One sentence describing the primary contribution"
limitations: ["limitation 1", "limitation 2"]
connections: [[other-paper-slug]], [[idea-slug]]
tags: [keyword1, keyword2, keyword3]
created: YYYY-MM-DD
source: agent-name
```

### Module Entry

A module is a reusable methodological component extracted from a paper. Modules are the atomic units of idea construction.

```yaml
type: module
domain: gnn | vla-vlm
category: encoder | temporal | anomaly-scorer | loss-function | training-strategy |
         visual-encoder | projector | action-head | training-recipe
name: "Descriptive module name"
description: "One paragraph describing what this module does and how it works"
source_papers: [[paper-slug-1]], [[paper-slug-2]]  # Papers that use this module
validation_status: validated | partially-validated | unvalidated
  # validated: independently verified across >=2 papers with consistent evidence
  # partially-validated: evidence from a single paper, or inconsistent across papers
  # unvalidated: proposed but not yet empirically tested
validation_evidence: "Specific evidence supporting this module's effectiveness"
composable_with: [[module-slug-1]], [[module-slug-2]]
  # Modules that have been successfully combined with this module
incompatible_with: [[module-slug-3]]
  # Modules known to conflict (e.g., requires homophily vs. requires heterophily)
assumptions: ["assumption 1", "assumption 2"]  # Conditions required for this module to work
limitations: ["limitation 1"]  # Known failure modes
connections: [[paper-slug]], [[idea-slug]]
created: YYYY-MM-DD
source: agent-name
```

### Idea Entry

```yaml
type: idea
domain: gnn | vla-vlm | cross-domain
status: active | incubating | discarded
hypothesis: "Falsifiable hypothesis statement"
derived_from_modules: [[module-slug-1]], [[module-slug-2]], [[module-slug-3]]
derived_from_papers: [[paper-slug-1]], [[paper-slug-2]]
synergy_type: multiplicative | bootstrap | constraint-resolution
synergy_description: "Why these modules together produce something none can alone"
novelty_assessment: 1-5 with justification
feasibility_assessment: 1-5 with resource estimate
target_venue_tier: CCF-A | CCF-B | CCF-C
target_venues: ["venue-slug-1", "venue-slug-2"]  # Specific recommended venues
min_required_validation: "What experiments are the minimum bar for the target tier"
connections: [[module-slug]], [[paper-slug]], [[hyperedge-slug]]
tags: [keyword1, keyword2]
created: YYYY-MM-DD
source: agent-name
```

### Venue Entry

```yaml
type: venue
name: "Full venue name"
abbreviation: "ABBREV"
tier: CCF-A | CCF-B | CCF-C
category: journal | conference
publisher: "Publisher name"
impact_factor: X.X  # Journal only
acceptance_rate: "~XX%"  # Conference only
review_time: "X-X months" | "X months"
submission_deadline: "Month"  # Typical deadline month(s), conference only
topics: [topic1, topic2, topic3]
typical_paper_length: "X-X pages"
requires_theory: true | false | preferred
requires_code: true | false | preferred
requires_real_world_validation: true | false | preferred
difficulty_level: very-high | high | medium | moderate
best_fit_for: "Description of what kind of work fits best"
recent_similar_papers: [[paper-slug-1]]  # Examples of similar work published here
connections: [[idea-slug]]
created: YYYY-MM-DD
```

## Pipeline: Paper → Module → Idea

### Step 1: Paper Decomposition

When a paper is added to the KB (via Paper Reader agent), the KB Manager decomposes it into modules:

1. Identify distinct methodological contributions in the paper.
2. For each contribution, create or update a module entry. If the same module already exists from another paper, merge the evidence rather than duplicating.
3. Link the paper to its modules via `modules` field.
4. Link each module back to the paper via `source_papers` field.
5. Update module `validation_status` based on accumulated evidence across all source papers.

### Step 2: Module Validation

A module transitions through validation levels as evidence accumulates:

- `unvalidated` → `partially-validated`: At least one paper demonstrates the module's contribution via ablation.
- `partially-validated` → `validated`: At least two independent papers confirm the module's effectiveness, with no contradictory evidence.

### Step 3: Module Combination → Idea

When the KB Manager's hypergraph computation identifies a valid set of modules (complementary, compatible, synergistic, minimal), and that set is NOT yet covered by an existing idea:

1. Create a new idea entry in `ideas/incubating/`.
2. Link it to its constituent modules and source papers.
3. Assess novelty by checking whether any existing paper already combines these modules.
4. Recommend target venues based on contribution strength and domain fit.
5. The idea transitions to `active` when the researcher begins experimentation.

## Index Maintenance

Every directory has an `INDEX.md` maintained by the KB Manager. The `papers/INDEX.md` provides multi-dimensional navigation (by domain, method type, venue tier, novelty level, code availability, module composition). The `modules/INDEX.md` provides navigation by category, validation status, composability. The `venues/INDEX.md` provides navigation by tier, domain fit, difficulty.

## Cross-Domain Idea Routing

The KB supports cross-domain idea generation: modules from different domains (GNN, VLA-VLM, and any user-created domains) can be combined into a single idea. This is enabled by the `domain: cross-domain` value in the Idea entry frontmatter.

### Cross-Domain Combinability Criteria

A cross-domain hyperedge is valid when ALL of:

1. **Shared abstraction** (replaces the standard complementarity check): The modules from different domains address the same abstract challenge. Example: "heterophily-aware encoder" (GNN) and "contrastive visual grounding" (VLM) both address the challenge of "learning representations when surface similarity is misleading." Evidence: the challenge descriptions in the modules' `description` and `tags` fields overlap.

2. **Data modality bridge**: There exists a concrete method to map data between the two domains. Example: VLM visual features can be node attributes in a GNN, or GNN graph structures can represent VLM attention patterns. The bridge must be specified in the hyperedge entry.

3. **Joint contribution**: The combination produces a contribution that neither domain could produce alone. It is not "GNN method + VLM method" but "a new method that uses VLM capabilities to solve a GNN problem, or vice versa."

4. **Compatibility** (unchanged): Module assumptions must be jointly satisfiable across domains.

5. **Minimality** (unchanged): No proper subset is itself a valid cross-domain hyperedge.

### Cross-Domain Idea Entry Differences

Cross-domain ideas have these additional frontmatter fields:

```yaml
domain: cross-domain
source_domains: [gnn, vla-vlm]  # Which domains' modules are combined
data_bridge: "Description of how data maps between domains"
primary_audience: gnn | vla-vlm  # Which community is the primary target
```

### Cross-Domain Venue Recommendation

Cross-domain ideas require special venue consideration. The KB Manager:
1. Checks whether the primary audience's domain venues accept cross-domain work.
2. Searches for venues that explicitly welcome interdisciplinary contributions.
3. If no venue in the target tier matches, recommends the best fit in the primary audience's domain at the next tier down.

### Activation

Cross-domain combinations are evaluated when `/mr combinations` is run and modules from >=2 domains exist in the KB. Cross-domain hyperedges are tagged with `confidence: speculative` by default and require the `data_bridge` field to be populated before the idea is promoted to `active`.

## Retrieval Protocol

Same as previously specified: filter by frontmatter → rank by relevance (recency + connection density) → top-K → condensed summary for agent context injection.

## P1 Extension — Audit entity + external-verification fields

The panel-audit system (P0/P1 upgrade — see `schemas/audit-v1.json`,
`workflows/audit-loop.js`) introduces one new entity and three new
frontmatter fields on Paper/Module/Idea.

### Audit Entry

Every audit-loop round emits an Audit record at
`knowledge-base/audit-rounds/YYYY-MM-DD-<phase>-round<N>.json` and an
indexed wikilink in `knowledge-base/audit-rounds/INDEX.md`. The
human-readable Markdown shape (when an expert chooses to materialize
its verdict into the graph for cross-link queries):

```yaml
type: audit
audit_id: "2026-06-30-WRITE-round2-figure-expert"
phase: EXPLORE | DESIGN | VALIDATE | ANALYZE | WRITE | REVIEW
target: "manuscript/main.tex" | "[[idea-slug]]" | "[[module-slug]]"
round: 1 | 2 | ...
expert: figure-expert | claim-trace-expert | hallucination-expert | ...
verdict: PASS | REVISE | VETO
score: 0-100                              # weighted_mean of axes
weight: 25                                 # this expert's panel weight
axes: {axis_name: score, ...}              # raw axis scores
critical_axes: [axis_name, ...]            # axes on which this expert can veto
vetoes: [axis_name, ...]                   # axes that triggered a critical veto this round
blocking_findings:                          # findings that block PASS
  - {axis: ..., severity: blocking, msg: ..., fix_hint: ..., loci: [file:line, ...]}
advisory_findings: [...]                    # findings reported but non-blocking
evidence:                                   # grounding for every axis>=80
  - {type: file | kb | url | recompute, uri: ..., retrieved_at: ISO8601}
diff_vs_previous_round:
  axes_improved: [...]
  axes_regressed: [...]
  new_blocking: [...]
  resolved_blocking: [...]
links_to: [[paper-slug]], [[module-slug]], [[idea-slug]]
created: YYYY-MM-DD
source: workflows/audit-loop.js
```

### Frontmatter additions on Paper / Module / Idea

After the panel-audit migration date, **new** Paper entries are rejected
by `kb-manager` unless the external-verification fields are populated.

```yaml
# Add to existing Paper entries:
external_verified: true | false | null
  # true:  paper_fetcher.py returned >=1 source hit with Jaccard >=0.6
  # false: looked up but no source matched
  # null:  not yet checked (only valid for pre-migration entries)
verifier_used: "scripts/paper_fetcher.py" | "scripts/verify_citations.py"
verified_at: YYYY-MM-DDTHH:MM:SSZ
verification_evidence:
  - {source: dblp | semantic_scholar | arxiv | crossref,
     uri: "DOI or arXiv id or URL",
     similarity: 0.0-1.0,
     retrieved_at: ISO8601}
```

The same three fields propagate to Module entries (when the source paper
gets verified the module inherits the verification) and to Idea entries
(when each derived-from paper is verified).

### Retrieval extensions

The `kb-manager` retrieval protocol gains an additional filter:

```
audit_status:
  PASSED   -> entity has >=1 Audit record with verdict=PASS and score>=90
             on the most recent round
  REVISING -> latest Audit is verdict=REVISE
  ESCALATED -> latest Audit verdict=REVISE on round 10 (10-round cap)
  UNAUDITED -> no Audit record (pre-migration or never run)
```

Default queries from any expert filter out `UNAUDITED` entities except
when the query is itself an audit (in which case it operates on the
unaudited entity to produce the first Audit record).

### Backward compatibility

Pre-migration entries are tagged `external_verified: null` at migration
time. A periodic batch job (`/mr verify` — runs `verify_citations.py` and
populates `verification_evidence`) walks `knowledge-base/papers/**` and
upgrades `null` to true/false. `kb-manager` continues to surface
`UNAUDITED` entries in retrieval but flags them with a yellow caveat in
the rendered context block.
