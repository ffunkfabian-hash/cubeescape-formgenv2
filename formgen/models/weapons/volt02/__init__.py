"""Freigegebene Impulsgewehre der Serie Volt-02."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-02"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K02", "L02", "M02", "N02")}
