"""Freigegebene Scharfschützengewehre der Serie Volt-09."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-09"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K09", "L09", "M09", "N09")}
