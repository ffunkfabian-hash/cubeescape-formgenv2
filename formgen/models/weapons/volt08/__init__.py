"""Freigegebene Schrotflinten der Serie Volt-08."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-08"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K08", "L08", "M08", "N08")}
