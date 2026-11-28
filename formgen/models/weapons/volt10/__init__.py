"""Freigegebene Fusionsgewehre der Serie Volt-10."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-10"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K10", "L10", "M10", "N10")}
