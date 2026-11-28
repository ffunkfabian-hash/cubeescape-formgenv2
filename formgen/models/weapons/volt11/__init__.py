"""Freigegebene lineare Fusionsgewehre der Serie Volt-11."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-11"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K11", "L11", "M11", "N11")}
