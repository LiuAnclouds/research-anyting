# GNN Dynamic Graph Anomaly Detection: Baseline Reproduction Guide

## Required Baselines (Must Compare)

### AddGraph (AAAI 2019)
- Repository: https://github.com/Ljiajie/Addgraph
- Framework: TensorFlow 1.x
- Key hyperparameters: GCN layers=2, hidden_dim=128, attention_heads=4, learning_rate=0.001
- Data format: Edge list with timestamps, converted to snapshots
- Reproduction notes: Requires TF 1.x environment. Use the provided preprocessing script. The paper reports results on Bitcoin-Alpha, Bitcoin-OTC, and UCI Messages.
- Known issues: Memory-intensive for graphs with >100K edges. The code does not support GPU acceleration for all operations.

### StrGNN (CIKM 2021)
- Repository: https://github.com/KnowledgeDiscovery/StrGNN
- Framework: PyTorch + PyG
- Key hyperparameters: GNN layers=3, hidden_dim=256, temporal_window=10, learning_rate=0.0005
- Data format: Edge list with timestamps. Supports both accumulated graph and time-evolving graph modes.
- Reproduction notes: Well-documented codebase. Use the time-evolving graph mode for fair comparison with snapshot-based methods.
- Known issues: Requires careful handling of edge direction for directed graphs.

### TADDY (TKDE 2023)
- Repository: https://github.com/yuetan031/TADDY_pytorch
- Framework: PyTorch
- Key hyperparameters: Transformer layers=3, attention_heads=8, hidden_dim=256, positional_encoding_dim=64, learning_rate=0.0001
- Data format: Edge list with timestamps, automatically converted to snapshots
- Reproduction notes: Best-documented baseline. Provides preprocessing scripts for all standard datasets. Use the default hyperparameters from the paper.
- Known issues: High memory usage for Transformer on long sequences (>50 snapshots). Consider gradient checkpointing for large graphs.

### GDN (AAAI 2021)
- Repository: No official code (re-implementations exist on GitHub)
- Framework: PyTorch (community implementations)
- Key hyperparameters: GCN layers=2, hidden_dim=128, top_k=10, learning_rate=0.001
- Reproduction notes: Use the most-starred community implementation. Verify against reported paper results on Bitcoin-Alpha before using in comparison.
- Known issues: No official implementation; results may vary across community re-implementations.

### EvolveGCN (AAAI 2020)
- Repository: https://github.com/IBM/EvolveGCN
- Framework: PyTorch
- Key hyperparameters: GCN layers=2, hidden_dim=128, learning_rate=0.001
- Data format: Edge list with timestamps, snapshots
- Reproduction notes: Well-maintained by IBM. Use the EvolveGCN-O variant (without node features) for fair comparison if your method does not use node features.
- Known issues: Limited to discrete snapshots; cannot handle continuous-time event streams.

### GeneralDyG (AAAI 2025)
- Repository: https://github.com/YXNTU/GeneralDyG
- Framework: PyTorch + PyG
- Key hyperparameters: Ego-graph radius=2, hidden_dim=128, pretraining_epochs=100, learning_rate=0.001
- Data format: Edge list with timestamps
- Reproduction notes: Most recent SOTA. Follow the provided training script exactly. The pretraining phase requires substantial unlabeled data.
- Known issues: Ego-graph sampling may be slow for dense graphs. Pretraining requires 2-4x the training time of non-pretrained methods.

## Additional Baselines (Recommended)

### Static Methods (for ablation: demonstrate temporal modeling is necessary)
- GCN (standard graph convolutional network without temporal modeling)
- GAT (graph attention network without temporal modeling)
- GraphSAGE (inductive representation learning without temporal modeling)

### Anomaly Detection Methods (broader context)
- Isolation Forest (classic non-graph baseline)
- LOF (Local Outlier Factor, classic non-graph baseline)
- DOMINANT (static graph anomaly detection, GCN-based autoencoder)

## Baseline Configuration Protocol

For fair comparison:
1. Use official implementations whenever available. Document any deviations.
2. Use hyperparameters from the original paper. If tuning is required, use the same tuning budget (number of trials) for all methods.
3. Use the same data split (chronological: 60% train, 20% val, 20% test) for all methods.
4. Use the same evaluation protocol (metrics, number of seeds) for all methods.
5. Report hardware and software versions for reproducibility.