#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

config="${SNOWCELL_SCPLANTLLM_CONFIG:-configs/foundation_5090_public_sprint.yaml}"
output_dir="${SNOWCELL_SCPLANTLLM_PROBE_INPUT_DIR:-outputs/external_benchmarks/scplantllm_preprocess_probe_input}"
max_cells="${SNOWCELL_SCPLANTLLM_PROBE_MAX_CELLS:-1000}"
test_size="${SNOWCELL_SCPLANTLLM_PROBE_TEST_SIZE:-0.3}"
reference_dir="external/scPlantLLM"
reference_preprocess_dir="${output_dir}/reference_preprocess"
chunks_dir="${reference_preprocess_dir}/chunks"

if [ ! -f "${reference_dir}/prepare_meta.py" ] || [ ! -f "${reference_dir}/preprocess_data.py" ]; then
  echo "Missing scPlantLLM prepare_meta.py or preprocess_data.py under ${reference_dir}" >&2
  exit 2
fi

python scripts/export_scplantllm_input.py \
  --config "$config" \
  --output-dir "$output_dir" \
  --max-cells "$max_cells" \
  --gene-vocab "${reference_dir}/gene_vocab.json"

mkdir -p "$reference_preprocess_dir" "$chunks_dir"
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

project_dir="$(pwd)"
(
  cd "$reference_dir"
  python preprocess_data.py \
    --input_path "${project_dir}/${output_dir}" \
    --output_path "${project_dir}/${chunks_dir}" \
    --has_celltype \
    --test_size "$test_size" \
    --cell_type_file "${project_dir}/${reference_preprocess_dir}/cell_type.meta" \
    --cell_type_vocab_file "${project_dir}/${reference_preprocess_dir}/cell_type_vocab.meta.json" \
    --gene_vocab_file "${project_dir}/${reference_dir}/gene_vocab.json" \
    --batch_effect_file "${project_dir}/${reference_preprocess_dir}/batch_effect.meta" \
    --batch_effect_vocab_file "${project_dir}/${reference_preprocess_dir}/batch_effect_vocab.meta.json"
)

python scripts/write_scplantllm_input_readiness.py \
  --project-dir . \
  --input-dir "$output_dir" \
  --output-md outputs/publication_package/scplantllm_preprocess_probe_readiness.md \
  --output-json outputs/publication_package/scplantllm_preprocess_probe_readiness.json
