#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/public/figshare_20255094
echo 'Figshare API file listing failed during script generation: <HTTPError 403: '"'"'Forbidden'"'"'>'
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/figshare_20255094/article_api.json https://api.figshare.com/v2/articles/20255094 || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/figshare_20255094/article_page.html https://figshare.com/articles/dataset/Single-cell_multi-omics_of_Catharanthus_roseus/20255094 || true
