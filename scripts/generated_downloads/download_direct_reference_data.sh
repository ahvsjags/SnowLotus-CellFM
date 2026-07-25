#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/public/direct_downloads
curl -L --retry 5 --connect-timeout 20 --max-time 7200 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/direct_downloads/scplantllm_srp169576_benchmark.download 'https://box.nju.edu.cn/seafhttp/f/66ed8930449d41e98b60/?op=download' || true
