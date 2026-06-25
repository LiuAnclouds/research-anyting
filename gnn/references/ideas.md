# GNN DyG-AD Research Directions

## Direction 1: Heterophily-Aware Dynamic Graph AD

**Falsifiable hypothesis**: "A GNN architecture with explicit heterophily modeling through separate high-frequency and low-frequency signal processing channels achieves >=5% higher AUC-ROC than TADDY on dynamic graphs with heterophily ratio >0.3, while maintaining comparable performance on homophilic graphs."

**Assessment**: Novelty 5 (0 papers), Feasibility 4, Potential 5. Risk: heterophily ratio may not be the dominant factor. Target: ACM TKDD, Neural Networks (CCF-B); AAAI/KDD (CCF-A with theory).

## Direction 2: Multi-Scale Temporal Graph AD

**Falsifiable hypothesis**: "A multi-branch temporal encoder with differentiable window selection achieves >=3% higher AUC-ROC than single-scale methods when temporal scale mismatch between method and anomaly exceeds 10x."

**Assessment**: Novelty 4 (2 partial papers), Feasibility 5, Potential 4. Risk: multi-scale gain may be small relative to other components. Target: ACM TKDD, Pattern Recognition (CCF-B).

## Direction 3: Causal Dynamic Graph AD

**Falsifiable hypothesis**: "A causally-informed detector using invariant risk minimization achieves >=10% lower false positive rate than correlation-based methods under controlled distribution shift, while matching detection rate under stationary conditions."

**Assessment**: Novelty 5 (0 papers), Feasibility 3, Potential 5. Risk: defining meaningful environments for IRM on graphs may not succeed. Target: NeurIPS/ICLR (CCF-A) with strong theory.

## Direction 4: Continuous-Discrete Unified AD

Novelty 4, Feasibility 3, Potential 4.

## Direction 5: Prompt-Based Universal GAD

Novelty 4, Feasibility 3, Potential 4.

## Direction 6: Streaming-Efficient Expressive GNN

Novelty 3, Feasibility 4, Potential 3.

## Recommended: Directions 1 + 2 combined

"Multi-Scale Heterophily-Aware Dynamic Graph Anomaly Detection" — both individually feasible, naturally composable, cleanly separable in ablation.
