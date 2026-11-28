"""Freigegebene Bögen der Serie Volt-07."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-07"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K07", "L07", "M07", "N07")}
