from __future__ import annotations

import sys
from pathlib import Path


for raw_path in sys.argv[1:]:
    path = Path(raw_path)
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"")
    path.write_bytes(data)
    print(path)
