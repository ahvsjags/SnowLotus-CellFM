from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from download_gse270140_external_validation import byte_ranges


def test_byte_ranges_cover_remote_object_once_without_overlap() -> None:
    ranges = byte_ranges(25, 8)
    assert ranges == [(0, 7), (8, 15), (16, 23), (24, 24)]
    assert sum(end - start + 1 for start, end in ranges) == 25
