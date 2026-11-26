"""Freigegebene Volt-01-Kits. Blattkennungen aus der Auswahlgalerie."""
from dataclasses import dataclass
import json
from pathlib import Path

SERIES = "Volt-01"


@dataclass(frozen=True)
class VoltSheet:
    id: str

    @property
    def source_path(self):
        return Path(__file__).with_name(self.id + ".json")

    def author(self, snap):
        return json.loads(self.source_path.read_text(encoding="utf-8"))

    def make(self, snap):
        doc = self.author(snap)
        info = doc["INFO"]
        return {"META": {"id": self.id, "name": info["nick"], "type_de": info["type_de"]},
                **{key: doc[key] for key in ("PARTS", "ASSEMBLIES", "ANCHORS")}}


SHEETS = {sid: VoltSheet(sid) for sid in ("K01", "L01", "M01", "N01")}
