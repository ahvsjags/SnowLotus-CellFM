#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/public/geo
mkdir -p 'data/public/geo/GSE146034'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE146034' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE146nnn/GSE146034/suppl/' || true
mkdir -p 'data/public/geo/GSE149217'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE149217' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE149nnn/GSE149217/suppl/' || true
mkdir -p 'data/public/geo/GSE152766'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE152766' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE152nnn/GSE152766/suppl/' || true
mkdir -p 'data/public/geo/GSE172280'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE172280' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE172nnn/GSE172280/suppl/' || true
mkdir -p 'data/public/geo/GSE226097'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE226097' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE226nnn/GSE226097/suppl/' || true
mkdir -p 'data/public/geo/GSE243419'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE243419' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243419/suppl/' || true
mkdir -p 'data/public/geo/GSE251706'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE251706' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE251nnn/GSE251706/suppl/' || true
mkdir -p 'data/public/geo/GSE268881'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE268881' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE268nnn/GSE268881/suppl/' || true
mkdir -p 'data/public/geo/GSE270140'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE270140' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270140/suppl/' || true
mkdir -p 'data/public/geo/GSE270342'
wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' -P 'data/public/geo/GSE270342' 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270342/suppl/' || true
