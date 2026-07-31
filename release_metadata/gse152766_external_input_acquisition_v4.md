# GSE152766 External Root Input Acquisition

- Source: `https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4626nnn/GSM4626007/suppl/GSM4626007_sc_52_mtx.tar.gz`
- GEO sample: `GSM4626007`
- Archive SHA256: `7e55c00b6cd651e01a90989a487328694e6f65f3841227675b171b115517edaa`
- Spliced matrix: `6566` cells x `25171` TAIR10 gene identifiers
- Prepared input: `outputs/external_validation/gse152766_gsm4626007/GSM4626007_sc_52_spliced_external_root.h5ad`

## Evidence Boundary

- This is a blinded external input used for inference; its downloaded matrix does not contain expert cell-type labels.
- GSE152766 is absent from the frozen v4 corpus profile dataset IDs. This establishes only non-membership in that documented corpus, not a blanket claim about every historical resource used by all upstream models.
- Any resulting prediction is an external execution and marker-coherence case, not an accuracy benchmark unless expert labels are acquired under a frozen protocol.
