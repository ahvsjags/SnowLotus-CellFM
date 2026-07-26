from __future__ import annotations

import glob
import json

import numpy as np


for path in sorted(glob.glob("data/public/GSE155304_npz/*.npz")):
    data = np.load(path, allow_pickle=True)
    summary = {"path": path, "keys": sorted(data.files)}
    for key in data.files:
        value = data[key]
        if hasattr(value, "shape"):
            summary[key] = {
                "shape": tuple(int(x) for x in value.shape),
                "dtype": str(value.dtype),
            }
        else:
            summary[key] = str(type(value))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
