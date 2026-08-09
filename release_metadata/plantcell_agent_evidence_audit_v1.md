# PlantCell-Agent evidence audit v1

This release separates accept-all direct inference from the Agent threshold policy.
The strict case is marked raw_h5ad_end_to_end only when the manifest H5AD is available; otherwise the report remains a locked 3,964-row prediction/embedding replay.

## Reference-backed audit

| Case | n | Accepted n | Coverage | Accepted accuracy | Review accuracy | Accepted error | Review error | Difference |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| strict_heldout_3964 | 3964 | 2239 | 0.5648 | 0.8571 | 0.4099 | 0.1429 | 0.5901 | 0.4472 |
| arabidopsis_secondary_root | 11760 | 9898 | 0.8417 | 0.9241 | 0.5596 | 0.0759 | 0.4404 | 0.3645 |
| wheat_nonoverlap | 7164 | 2963 | 0.4136 | 0.8289 | 0.5189 | 0.1711 | 0.4811 | 0.3100 |
| sorghum_sealed_library | 19316 | 14986 | 0.7758 | 0.9082 | 0.5233 | 0.0918 | 0.4767 | 0.3849 |

A positive Difference means the Agent review group has higher reference error than the automatically accepted group.
The public expert worksheet hides the acceptance group and reference label. Independent expert validation is claimed only when a completed blinded worksheet is passed to this script.
