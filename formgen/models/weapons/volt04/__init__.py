"""Freigegebene Handfeuerwaffen der Serie Volt-04."""
from pathlib import Path

from ..volt01 import VoltSheet

SERIES = "Volt-04"
SHEETS = {sid: VoltSheet(sid, Path(__file__).parent) for sid in ("K04", "L04", "M04", "N04")}
