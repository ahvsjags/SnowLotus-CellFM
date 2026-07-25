#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
DOCS_DIR="${DOCS_DIR:-${PROJECT_DIR}/github_release_docs}"
RELEASE_DIR="${RELEASE_DIR:-${PROJECT_DIR}/outputs/github_release/SnowLotus-CellFM}"
ARCHIVE_DIR="${ARCHIVE_DIR:-${PROJECT_DIR}/outputs/github_release_archives}"
GITHUB_REMOTE_URL="${GITHUB_REMOTE_URL:-git@github.com:ahvsjags/SnowLotus-CellFM.git}"
RELEASE_LABEL="${RELEASE_LABEL:-editor-v0.2}"
ANNOTATION_CHECKPOINT="${SNOWCELL_RELEASE_ANNOTATION_CHECKPOINT:-outputs/foundation_5090_pretrain/best.pt}"
EMBEDDING_CHECKPOINT="${SNOWCELL_RELEASE_EMBEDDING_CHECKPOINT:-outputs/foundation_5090_mlm_public_expansion_continuation/best.pt}"
if [ -z "${PYTHON:-}" ]; then
  if [ -x "${PROJECT_DIR}/.venv/bin/python" ]; then
    PYTHON="${PROJECT_DIR}/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  else
    PYTHON="python"
  fi
fi

cd "${PROJECT_DIR}"

mkdir -p "${RELEASE_DIR}/manuscript" "${RELEASE_DIR}/release_metadata" "${RELEASE_DIR}/models" "${RELEASE_DIR}/data"
mkdir -p "${ARCHIVE_DIR}"

copy_required() {
  local source="$1"
  local dest="$2"
  if [ ! -f "$source" ]; then
    echo "missing required file: $source" >&2
    return 1
  fi
  if [ -f "$dest" ] && [ "$source" -ef "$dest" ]; then
    echo "already linked ${dest}"
    return 0
  fi
  cp "$source" "$dest"
}

copy_release_doc() {
  local filename="$1"
  local dest="$2"
  local source="${DOCS_DIR}/${filename}"
  if [ -f "$source" ]; then
    cp "$source" "$dest"
    return 0
  fi
  if [ -f "$dest" ]; then
    echo "keeping existing ${dest}"
    return 0
  fi
  echo "missing release document: ${source}" >&2
  return 1
}

write_default_gitattributes() {
  cat > "${RELEASE_DIR}/.gitattributes" <<'EOF'
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.h5ad filter=lfs diff=lfs merge=lfs -text
*.npz filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
EOF
}

cleanup_release_caches() {
  find "${RELEASE_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} +
  find "${RELEASE_DIR}" -type d -name ".pytest_cache" -prune -exec rm -rf {} +
  find "${RELEASE_DIR}" -type f -name "*.pyc" -delete
  find "${RELEASE_DIR}" -type f -name "*.bak_*" -delete
}

rsync -a --delete --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='*.bak_*' src/ "${RELEASE_DIR}/src/"
rsync -a --delete --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='*.bak_*' configs/ "${RELEASE_DIR}/configs/"
rsync -a --delete --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='*.bak_*' scripts/ "${RELEASE_DIR}/scripts/"
rsync -a --delete --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='*.bak_*' tests/ "${RELEASE_DIR}/tests/"
if [ -d docs ]; then
  rsync -a --delete docs/ "${RELEASE_DIR}/docs/"
fi
cleanup_release_caches

copy_required pyproject.toml "${RELEASE_DIR}/pyproject.toml"
copy_required .gitignore "${RELEASE_DIR}/.gitignore"
copy_required data/public_dataset_manifest.tsv "${RELEASE_DIR}/data/public_dataset_manifest.tsv"
find "${RELEASE_DIR}/data" -maxdepth 1 -name "corpus_manifest*.tsv" -delete
for source in data/corpus_manifest*.tsv; do
  if [ -f "${source}" ]; then
    cp "${source}" "${RELEASE_DIR}/data/$(basename "${source}")"
  fi
done

copy_release_doc README.md "${RELEASE_DIR}/README.md"
copy_release_doc GITHUB_PUSH_INSTRUCTIONS.md "${RELEASE_DIR}/GITHUB_PUSH_INSTRUCTIONS.md"
copy_release_doc MODEL_RELEASE_NOTES_v0_2.md "${RELEASE_DIR}/MODEL_RELEASE_NOTES_v0_2.md"
copy_release_doc MODEL_RELEASE_NOTES_v0_3.md "${RELEASE_DIR}/MODEL_RELEASE_NOTES_v0_3.md"
copy_release_doc EDITOR_HANDOFF.md "${RELEASE_DIR}/EDITOR_HANDOFF.md"
copy_release_doc EDITOR_HANDOFF.docx "${RELEASE_DIR}/EDITOR_HANDOFF.docx"
copy_release_doc SnowLotus_CellFM_editor_submission_v0_2.md "${RELEASE_DIR}/manuscript/SnowLotus_CellFM_editor_submission_v0_2.md"
copy_release_doc SnowLotus_CellFM_editor_submission_v0_2.docx "${RELEASE_DIR}/manuscript/SnowLotus_CellFM_editor_submission_v0_2.docx"
copy_release_doc SnowLotus_CellFM_editor_submission_v0_3.md "${RELEASE_DIR}/manuscript/SnowLotus_CellFM_editor_submission_v0_3.md"
copy_release_doc SnowLotus_CellFM_editor_submission_v0_3.docx "${RELEASE_DIR}/manuscript/SnowLotus_CellFM_editor_submission_v0_3.docx"
copy_release_doc editor_cover_note_v0_2.md "${RELEASE_DIR}/manuscript/editor_cover_note_v0_2.md"
copy_release_doc editor_cover_note_v0_2.docx "${RELEASE_DIR}/manuscript/editor_cover_note_v0_2.docx"
copy_release_doc editor_cover_note_v0_3.md "${RELEASE_DIR}/manuscript/editor_cover_note_v0_3.md"
copy_release_doc editor_cover_note_v0_3.docx "${RELEASE_DIR}/manuscript/editor_cover_note_v0_3.docx"

for source in "${DOCS_DIR}"/MODEL_RELEASE_NOTES_*.md; do
  if [ -f "${source}" ]; then
    cp "${source}" "${RELEASE_DIR}/$(basename "${source}")"
  fi
done

for source in "${DOCS_DIR}"/SnowLotus_CellFM_editor_submission_*.md "${DOCS_DIR}"/SnowLotus_CellFM_editor_submission_*.docx "${DOCS_DIR}"/editor_cover_note_*.md "${DOCS_DIR}"/editor_cover_note_*.docx; do
  if [ -f "${source}" ]; then
    cp "${source}" "${RELEASE_DIR}/manuscript/$(basename "${source}")"
  fi
done

if [ -f "${DOCS_DIR}/.gitattributes" ]; then
  cp "${DOCS_DIR}/.gitattributes" "${RELEASE_DIR}/.gitattributes"
elif [ ! -f "${RELEASE_DIR}/.gitattributes" ]; then
  write_default_gitattributes
fi

if [ -f scripts/write_editor_live_status_panel.py ]; then
  "${PYTHON:-python}" scripts/write_editor_live_status_panel.py \
    --project-dir "${PROJECT_DIR}" \
    --output-md outputs/publication_package/editor_live_status_panel.md \
    --output-json outputs/publication_package/editor_live_status_panel.json || true
fi

for file in \
  outputs/publication_package/top_journal_readiness_matrix.md \
  outputs/publication_package/model_data_card.md \
  outputs/publication_package/model_data_card.json \
  outputs/publication_package/model_release_manifest.md \
  outputs/publication_package/model_release_manifest.json \
  outputs/publication_package/public_mlm_plus_readiness.md \
  outputs/publication_package/public_mlm_plus_readiness.json \
  outputs/publication_package/saussurea_public_data_discovery.md \
  outputs/publication_package/saussurea_public_data_discovery.json \
  outputs/publication_package/saussurea_supporting_evidence.md \
  outputs/publication_package/saussurea_supporting_evidence.json \
  outputs/publication_package/saussurea_data_request_package.md \
  outputs/publication_package/saussurea_h5ad_contract.md \
  outputs/publication_package/data_integrity_audit.md \
  outputs/publication_package/data_integrity_audit.json \
  outputs/publication_package/download_progress_audit.md \
  outputs/publication_package/download_progress_audit.json \
  outputs/publication_package/geo_promotion_queue_health_audit.md \
  outputs/publication_package/geo_promotion_queue_health_audit.json \
  outputs/publication_package/corpus_provenance_audit.md \
  outputs/publication_package/environment_snapshot.md \
  outputs/publication_package/benchmark_gap_audit.md \
  outputs/publication_package/benchmark_gap_audit.json \
  outputs/publication_package/external_benchmark_blockers.md \
  outputs/publication_package/scplantannotate_access_audit.md \
  outputs/publication_package/scplantannotate_access_audit.json \
  outputs/publication_package/scplantannotate_benchmark_input_package.md \
  outputs/publication_package/scplantannotate_benchmark_input_package.json \
  outputs/publication_package/scplantllm_input_readiness.md \
  outputs/publication_package/scplantllm_input_readiness.json \
  outputs/publication_package/scplantllm_preprocess_probe_readiness.md \
  outputs/publication_package/scplantllm_preprocess_probe_readiness.json \
  outputs/publication_package/detailed_evaluation_index.txt \
  outputs/publication_package/strict_benchmark_index.txt \
  outputs/publication_package/editor_live_status_panel.md \
  outputs/publication_package/editor_live_status_panel.json \
  outputs/publication_package/artifact_checksums.tsv
do
  if [ -f "${file}" ]; then
    cp "${file}" "${RELEASE_DIR}/release_metadata/"
  fi
done

for directory in \
  outputs/publication_package/strict_benchmarks \
  outputs/publication_package/public_discovery
do
  if [ -d "${directory}" ]; then
    rsync -a --delete "${directory}/" "${RELEASE_DIR}/release_metadata/$(basename "${directory}")/"
  fi
done

copy_required "${ANNOTATION_CHECKPOINT}" "${RELEASE_DIR}/models/SnowLotus_CellFM_best_annotation.pt"
copy_required "${EMBEDDING_CHECKPOINT}" "${RELEASE_DIR}/models/SnowLotus_CellFM_best_embedding.pt"

cd "${RELEASE_DIR}"
sha256sum models/SnowLotus_CellFM_best_annotation.pt models/SnowLotus_CellFM_best_embedding.pt > models/SHA256SUMS.txt

if [ ! -d .git ]; then
  git init -b main
fi
git lfs install --local
git lfs track "*.pt" "*.pth" "*.h5ad" "*.npz" "*.tar.gz" "*.zip"
git config user.name "SnowLotus-CellFM Release Bot"
git config user.email "release@snowlotus-cellfm.local"
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "${GITHUB_REMOTE_URL}"
fi

git add .gitattributes README.md GITHUB_PUSH_INSTRUCTIONS.md MODEL_RELEASE_NOTES_*.md EDITOR_HANDOFF.md EDITOR_HANDOFF.docx
git add pyproject.toml .gitignore src configs scripts tests docs data manuscript release_metadata models
if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  git commit -m "Sync SnowLotus-CellFM ${RELEASE_LABEL} release"
fi

git tag -f "${RELEASE_LABEL}" HEAD
sha256sum -c models/SHA256SUMS.txt

tar --exclude='.git' --exclude='models/*.pt' --exclude='*/__pycache__' --exclude='*/.pytest_cache' --exclude='*.pyc' --exclude='*.bak_*' -czf "${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-source-metadata.tar.gz" -C "$(dirname "${RELEASE_DIR}")" "$(basename "${RELEASE_DIR}")"
manuscript_archive_items=(manuscript GITHUB_PUSH_INSTRUCTIONS.md README.md EDITOR_HANDOFF.md EDITOR_HANDOFF.docx)
for note in MODEL_RELEASE_NOTES_*.md; do
  if [ -f "${note}" ]; then
    manuscript_archive_items+=("${note}")
  fi
done
tar -czf "${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-manuscript.tar.gz" -C "${RELEASE_DIR}" "${manuscript_archive_items[@]}"

echo "RELEASE_DIR=${RELEASE_DIR}"
echo "SOURCE_ARCHIVE=${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-source-metadata.tar.gz"
echo "MANUSCRIPT_ARCHIVE=${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-manuscript.tar.gz"
git status -sb
git log --oneline -1
