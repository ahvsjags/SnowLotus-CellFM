#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/public/sra_runinfo
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/PRJNA1055099.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA1055099' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/PRJNA1113801.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA1113801' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/PRJNA1218246.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA1218246' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/PRJNA169171.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA169171' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/PRJNA454730.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA454730' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/PRJNA991078.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA991078' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/SRP169576.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=SRP169576' || true
curl -L --retry 5 --connect-timeout 20 --max-time 120 -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' -o data/public/sra_runinfo/SRR516284.runinfo.csv 'https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=SRR516284' || true
