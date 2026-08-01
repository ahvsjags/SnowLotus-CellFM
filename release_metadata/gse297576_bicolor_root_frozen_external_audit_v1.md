# GSE297576 Sorghum Root Frozen External Audit

- External author-labelled input: 19,316 cells; 14,909 (77.18%) map to predeclared coarse identities.
- Frozen zero-shot accuracy over all evaluable cells: 14.56%; macro-F1: 0.1083.
- The model returned `Unknow` for 63.39% of evaluable cells and 36.76% of non-comparable cells.
- Conditional accuracy among non-`Unknow` assignments is 39.78% across 5,458 cells; this selective quantity is not the primary accuracy.

## Evidence Boundary

- GSE297576 Sorghum bicolor is absent from the declared five-species frozen corpus; author labels are joined only after frozen inference.
- The reported primary denominator includes every cell whose author label has a predeclared direct broad counterpart in the 13-state root vocabulary.
- Non-comparable identities remain audited but are not recoded as correct, incorrect, or `Unknow` targets.
- This is a Plant-CellFM frozen external audit. It is neither target-species adaptation nor a comparison against third-party methods.
