#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/public/geo_filelists
mkdir -p data/public/geo_filelists/GSE146034
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE146034/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE146nnn/GSE146034/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE146034/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE146nnn/GSE146034/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE149217
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE149217/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE149nnn/GSE149217/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE149217/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE149nnn/GSE149217/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE152766
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE152766/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE152nnn/GSE152766/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE152766/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE152nnn/GSE152766/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE172280
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE172280/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE172nnn/GSE172280/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE172280/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE172nnn/GSE172280/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE226097
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE226097/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE226nnn/GSE226097/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE226097/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE226nnn/GSE226097/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE243419
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE243419/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243419/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE243419/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243419/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE251706
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE251706/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE251nnn/GSE251706/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE251706/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE251nnn/GSE251706/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE268881
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE268881/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE268nnn/GSE268881/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE268881/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE268nnn/GSE268881/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE270140
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE270140/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270140/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE270140/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270140/suppl/filelist.txt || true
mkdir -p data/public/geo_filelists/GSE270342
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE270342/index.html https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270342/suppl/ || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/geo_filelists/GSE270342/filelist.txt https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270342/suppl/filelist.txt || true
