"""Änderungsdateien für Waffen und Roboter (`formgen/change-request` v1) samt Migration der Altdateien.

Schema: docs/schemas/change-request-1.schema.json; Altformat `formgen/robot-change-request` v1 (ein Punkt) und v2 (Markierungen):
docs/schemas/change-request-legacy.schema.json. Dieselbe Migration läuft im Editor (formgen/web/change-request.js); ein Test
vergleicht beide an den Fixtures. Altdateien werden nur gelesen. `downgrade` ist der Rückweg und beweist die Verlustfreiheit:
migrierte Dateien tragen `migrated_from`, Felder ohne eigenen Platz bleiben unverändert unter `sample.source`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FORMAT = 'formgen/change-request'
VERSION = 1
LEGACY_FORMAT = 'formgen/robot-change-request'
LEGACY_VERSIONS = (1, 2)
LEGACY_MODELS = {'RoboterBasic-01': ('RA01', 'robot')}   # Altdateien kennen nur diesen Modellnamen; Blatt-ID ist ewig
LEGACY_TARGET_ID = 'legacy-target'                       # v1 hatte genau einen Punkt ohne eigene ID
LOCATION_KEYS = ('gltf_node', 'gltf_mesh', 'gltf_primitive', 'gltf_triangle', 'triangle_vertex_indices', 'barycentric',
                 'local_gltf_xyz_m', 'local_normal_gltf_xyz', 'local_formgen_fux_mm')
_SCHEMAS = Path(__file__).resolve().parents[1]/'docs/schemas'


class ChangeRequestError(ValueError):
    pass


def _check(doc: dict, name: str) -> None:
    import jsonschema
    schema = json.loads((_SCHEMAS/name).read_text(encoding='utf-8'))
    try:
        jsonschema.Draft202012Validator(schema).validate(doc)
    except jsonschema.ValidationError as error:
        path = '/'.join(map(str, error.absolute_path))
        raise ChangeRequestError(f'{name}: {path}: {error.message}') from error


def validate(doc: dict) -> dict:
    _check(doc, 'change-request-1.schema.json')
    return doc


def _sample(target: dict) -> dict:
    rest = {k: v for k, v in target.items() if k not in LOCATION_KEYS and k not in ('formgen_part_id', 'assembly')}
    sample = {'part': target['formgen_part_id'], 'assembly': target['assembly'],
              'location': {k: target[k] for k in LOCATION_KEYS if k in target}}
    if rest:
        sample['source'] = rest
    return sample


def _target(sample: dict) -> dict:
    return {'assembly': sample['assembly'], 'formgen_part_id': sample['part'], **sample.get('source', {}), **sample['location']}


def migrate(doc: dict) -> dict:
    """Beliebige bekannte Datei auf den aktuellen Stand heben; unbekannte Formate und Versionen brechen ab."""
    if doc.get('format') == FORMAT:
        if doc.get('version') != VERSION:
            raise ChangeRequestError(f"Unbekannte Version {doc.get('version')!r} von {FORMAT}")
        return validate(doc)
    if doc.get('format') != LEGACY_FORMAT:
        raise ChangeRequestError(f"Unbekanntes Format {doc.get('format')!r}")
    _check(doc, 'change-request-legacy.schema.json')
    if doc['model'] not in LEGACY_MODELS:
        raise ChangeRequestError(f"Unbekanntes Altmodell {doc['model']!r}")
    sheet, kind = LEGACY_MODELS[doc['model']]
    if doc['version'] == 1:
        markings = [{'id': LEGACY_TARGET_ID, 'tool': 'point', 'comment': '', 'diameter_mm': None, 'samples': [_sample(doc['target'])]}]
    else:
        markings = [{'id': m['id'], 'tool': m['tool'], 'comment': m['comment'], 'diameter_mm': m['diameter_mm'],
                     'samples': [_sample(s) for s in m['samples']]} for m in doc['markings']]
    return validate({'format': FORMAT, 'version': VERSION, 'created_at': doc['created_at'],
                     'model': {'id': sheet, 'kind': kind, 'name': doc['model'], 'asset': doc['asset'], 'asset_sha256': doc['asset_sha256']},
                     'requested_change': doc['requested_change'], 'markings': markings,
                     'migrated_from': {'format': LEGACY_FORMAT, 'version': doc['version']}})


def downgrade(doc: dict) -> dict:
    """Rückweg einer migrierten Datei in ihr Altformat. Neue Dateien haben keinen Rückweg: Waffen gab es im Altformat nicht."""
    validate(doc)
    origin = doc.get('migrated_from')
    if not origin:
        raise ChangeRequestError('Nur migrierte Dateien lassen sich zurückführen')
    legacy = {'format': origin['format'], 'version': origin['version'], 'created_at': doc['created_at'], 'model': doc['model']['name'],
              'asset': doc['model']['asset'], 'asset_sha256': doc['model']['asset_sha256'], 'requested_change': doc['requested_change']}
    if origin['version'] == 1:
        legacy['target'] = _target(doc['markings'][0]['samples'][0])
    else:
        legacy['markings'] = [{'id': m['id'], 'comment': m['comment'], 'tool': m['tool'], 'diameter_mm': m['diameter_mm'],
                               'samples': [_target(s) for s in m['samples']]} for m in doc['markings']]
    _check(legacy, 'change-request-legacy.schema.json')
    return legacy


def load(path) -> dict:
    return migrate(json.loads(Path(path).read_text(encoding='utf-8')))


def dumps(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Änderungsdatei prüfen und auf den aktuellen Stand migrieren (Ausgabe auf stdout).')
    parser.add_argument('file', type=Path)
    sys.stdout.write(dumps(load(parser.parse_args().file)))
