#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

config="${SNOWCELL_SCPLANTLLM_CONFIG:-configs/foundation_5090_public_sprint.yaml}"
output_dir="${SNOWCELL_SCPLANTLLM_INPUT_DIR:-outputs/external_benchmarks/scplantllm_public_sprint_input}"
max_cells="${SNOWCELL_SCPLANTLLM_MAX_CELLS:-20000}"
reference_dir="external/scPlantLLM"
reference_preprocess_dir="${output_dir}/reference_preprocess"

python scripts/export_scplantllm_input.py \
  --config "$config" \
  --output-dir "$output_dir" \
  --max-cells "$max_cells" \
  --gene-vocab "${reference_dir}/gene_vocab.json"

if [ -f "${reference_dir}/prepare_meta.py" ]; then
  mkdir -p "$reference_preprocess_dir"
  python "${reference_dir}/prepare_meta.py" \
    --input_path "$output_dir" \
    --output_path "$reference_preprocess_dir" \
    --file_prefix batch_effect \
    --col_name orig.ident \
    --do_batch
  python "${reference_dir}/prepare_meta.py" \
    --input_path "$output_dir" \
    --output_path "$reference_preprocess_dir" \
    --file_prefix cell_type \
    --col_name celltype \
    --do_cell_type
fi

if [ "${SNOWCELL_RUN_SCPLANTLLM_PREPROCESS:-0}" = "1" ]; then
  if [ ! -f "${reference_dir}/preprocess_data.py" ]; then
    echo "Missing ${reference_dir}/preprocess_data.py" >&2
    exit 2
  fi
  mkdir -p "${reference_preprocess_dir}/chunks"
  project_dir="$(pwd)"
  (
    cd "$reference_dir"
    python preprocess_data.py \
      --input_path "${project_dir}/${output_dir}" \
      --output_path "${project_dir}/${reference_preprocess_dir}/chunks" \
      --has_celltype \
      --test_size "${SNOWCELL_SCPLANTLLM_TEST_SIZE:-0.0}" \
      --cell_type_file "${project_dir}/${reference_preprocess_dir}/cell_type.meta" \
      --cell_type_vocab_file "${project_dir}/${reference_preprocess_dir}/cell_type_vocab.meta.json" \
      --gene_vocab_file "${project_dir}/${reference_dir}/gene_vocab.json" \
      --batch_effect_file "${project_dir}/${reference_preprocess_dir}/batch_effect.meta" \
      --batch_effect_vocab_file "${project_dir}/${reference_preprocess_dir}/batch_effect_vocab.meta.json"
  )
fi

python scripts/write_scplantllm_input_readiness.py \
  --project-dir . \
  --input-dir "$output_dir" \
  --output-md outputs/publication_package/scplantllm_input_readiness.md \
  --output-json outputs/publication_package/scplantllm_input_readiness.json
