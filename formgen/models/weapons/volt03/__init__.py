"""Freigegebene Scout-Gewehre der Serie Volt-03."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-03"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K03", "L03", "M03", "N03")}
