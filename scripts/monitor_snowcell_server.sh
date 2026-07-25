#!/usr/bin/env bash
set -euo pipefail

cd /root/snowlotus-cellfm

echo "== date =="
date

echo "== tmux =="
tmux ls 2>/dev/null || true

echo "== gpu =="
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || true

echo "== foundation tail =="
tail -n 20 logs/foundation_long_20260723_150323.log 2>/dev/null || true

echo "== gse268881 pane =="
tmux capture-pane -t snowcell_gse268881_subset -p -S - 2>/dev/null | tail -40 || true

echo "== gse270342 pane =="
tmux capture-pane -t snowcell_gse270342_wheat_subset -p -S - 2>/dev/null | tail -40 || true

echo "== gse152766 pane =="
tmux capture-pane -t snowcell_gse152766_arabidopsis_subset -p -S - 2>/dev/null | tail -40 || true

echo "== gse146034 pane =="
tmux capture-pane -t snowcell_gse146034_rice_root_tip_subset -p -S - 2>/dev/null | tail -40 || true

echo "== gse270140 pane =="
tmux capture-pane -t snowcell_gse270140_arabidopsis_secondary_root_subset -p -S - 2>/dev/null | tail -40 || true

echo "== gse243419 pane =="
tmux capture-pane -t snowcell_gse243419_cotton_glandular_subset -p -S - 2>/dev/null | tail -40 || true

echo "== gse rds pane =="
tmux capture-pane -t snowcell_gse251706_rice_rds_subset -p -S - 2>/dev/null | tail -25 || true
tmux capture-pane -t snowcell_gse226097_arabidopsis_lifecycle_subset -p -S - 2>/dev/null | tail -25 || true

echo "== queue pane =="
tmux capture-pane -t snowcell_public_mlm_queue -p -S - 2>/dev/null | tail -40 || true

echo "== late refresh queue pane =="
tmux capture-pane -t snowcell_late_public_refresh_queue -p -S - 2>/dev/null | tail -40 || true

echo "== reviewed geo download queue pane =="
tmux capture-pane -t snowcell_reviewed_geo_download_queue -p -S - 2>/dev/null | tail -40 || true

echo "== saussurea metadata pane =="
tmux capture-pane -t snowcell_saussurea_metadata -p -S - 2>/dev/null | tail -40 || true

echo "== seurat public sprint pane =="
tmux capture-pane -t snowcell_seurat_public_sprint -p -S - 2>/dev/null | tail -60 || true

echo "== late refresh training pane =="
tmux capture-pane -t snowcell_mlm_public_late_refresh -p -S - 2>/dev/null | tail -40 || true

echo "== manifests =="
ls -lh data/corpus_manifest*.tsv 2>/dev/null || true

echo "== corpus h5ad =="
ls -lh data/plant_foundation_corpus*.h5ad 2>/dev/null || true

echo "== available gse268881 manifest =="
if [ -s data/corpus_manifest.gse268881.available.tsv ]; then
  cat data/corpus_manifest.gse268881.available.tsv
fi

echo "== public npz =="
find data/public/GSE268881_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE270342_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE152766_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE146034_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE243419_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE270140_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE251706_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE226097_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE338572_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE313726_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE311951_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE302041_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE314252_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE300264_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true
find data/public/GSE336751_npz -maxdepth 1 -type f -name "*.npz" -printf "%f %s\n" 2>/dev/null | sort || true

echo "== publication package =="
ls -lh \
  outputs/publication_package/status_summary.json \
  outputs/publication_package/top_journal_readiness_matrix.md \
  outputs/publication_package/data_availability_and_fair.md \
  outputs/publication_package/README.md \
  outputs/publication_package/artifact_checksums.tsv \
  outputs/publication_package/environment_snapshot.md \
  outputs/publication_package/environment_snapshot.json \
  outputs/publication_package/pending_corpus_additions.md \
  outputs/publication_package/pending_corpus_additions.json \
  outputs/publication_package/data_integrity_audit.md \
  outputs/publication_package/download_progress_audit.md \
  outputs/publication_package/download_progress_audit.json \
  outputs/publication_package/training_health_audit.md \
  outputs/publication_package/training_health_audit.json \
  outputs/publication_package/modality_compatibility_audit.md \
  outputs/publication_package/modality_compatibility_audit.json \
  outputs/publication_package/saussurea_supporting_evidence.md \
  outputs/publication_package/saussurea_supporting_evidence.json \
  2>/dev/null || true

echo "== outputs =="
find outputs -maxdepth 2 -type f \( -name "test_metrics.json" -o -name "history.json" -o -name "best.pt" \) -printf "%p %s\n" 2>/dev/null | sort || true
