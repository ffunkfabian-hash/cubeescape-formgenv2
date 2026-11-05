"""Blatt-Spec des Roboters `formgenv2/robot-sheet-spec`; reine Datenoperation auf dem ausgewerteten Dokument."""
from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMAT = 'formgenv2/robot-sheet-spec'
VERSION = 1


def _skin_name(skin):
    return tomllib.loads((ROOT / 'skins.toml').read_text())['skins'][skin]['de']


def build(document, entry) -> dict:
    (low, high) = document['bounds_m']
    counts = {}
    for p in document['parts']:
        counts[p['assembly']] = counts.get(p['assembly'], 0) + 1
    side = {'R': ' rechts', 'L': ' links'}
    forms = {}
    for p in document['parts']:
        forms[p.get('form', p['shape'])] = forms.get(p.get('form', p['shape']), 0) + 1
    return dict(format=FORMAT, version=VERSION, id=document['info']['id'], name_de=document['info']['name_de'], kind='robot',
                line=entry['line']['name'].lower(), line_info=entry['line'], type=dict(num=entry['type']['num'], name_de=entry['type']['name_de']), skin=entry['skin'], skin_de=_skin_name(entry['skin']),
                dimensions_mm=dict(height=round((high[2] - low[2]) * 1000, 1), width=round((high[0] - low[0]) * 1000, 1), depth=round((high[1] - low[1]) * 1000, 1)),
                parts=[dict(id=p['id'], name_de=p.get('label', p['id']) + side.get(p.get('side'), ''), assembly=p['assembly'], role=p['role']) for p in document['parts']],
                triangles=document['counts']['triangles'], forms=dict(sorted(forms.items())),
                assemblies=[dict(id=a['id'], de=a['de'], parts=counts[a['id']]) for a in document['assemblies']],
                sockets=sorted(document.get('anchors', {})), provenance=document['info']['provenance'],
                measured_parts=sorted(p['id'] for p in document['parts'] if p.get('provenance', {}).get('kind') == 'gemessen'), warnings=document.get('warnings', []))


def migrate(spec: dict) -> dict:
    if spec.get('format') != FORMAT:
        raise ValueError(f"Fremdes Format {spec.get('format')!r}")
    if spec.get('version') != VERSION:
        raise ValueError(f"Roboter-Spec Version {spec.get('version')!r} unbekannt")
    return spec
