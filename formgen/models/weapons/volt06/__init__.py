"""Freigegebene Maschinenpistolen der Serie Volt-06."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-06"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K06", "L06", "M06", "N06")}
