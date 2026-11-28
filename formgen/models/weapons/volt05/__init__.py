"""Freigegebene Pistolen der Serie Volt-05."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-05"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K05", "L05", "M05", "N05")}
