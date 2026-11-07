"""Register der Roboter (data/robots.toml): Basic-Typen und Linien, Blatt = Linie × Typ, wie formgen.variants bei den Waffen.

Registerversion 2 (0.14 Kitbash): je Linie optional `[lines.parts]`, die Wahl je Einzelteil aus dem Varianten-Baukasten
(formgen/models/robot/catalog), z. B. `shoulders = "SH-C"`; fehlende Einzelteile bleiben bei der Grundform. Version 1 (ohne `version`)
wird beim Laden migriert: keine Wahl, also lauter Grundformen.
"""
from __future__ import annotations

import copy
import importlib
import re
import tomllib
from pathlib import Path

from formgen.models.robot import catalog

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / 'data/robots.toml'
SCHEMA = 'formgenv2/robot-register'
VERSION = 2
LETTERS = set('ABCDEFGHJKLMNPQRSTUVWXYZ')
RESERVED = {'R01', 'R02'}
GROUPS = dict(head=('head',), upper_body=('upper_body', 'pelvis'), arms=('shoulders', 'upper_arms', 'forearms', 'hands'), legs=('thighs', 'shins', 'feet'))
ASSEMBLIES = tuple(a for members in GROUPS.values() for a in members)      # Einzelteile; darüber die Baugruppen GROUPS
SOCKETS = ('Socket_Neck', 'Socket_Waist', 'Socket_Hip_R', 'Socket_Hip_L', 'Socket_Shoulder_R', 'Socket_Shoulder_L',
           'Socket_Wrist_R', 'Socket_Wrist_L', 'Socket_Hand')


def load(path=REGISTER):
    data = tomllib.loads(Path(path).read_text())
    if data.get('schema') != SCHEMA:
        raise ValueError(f'Register: Schema {data.get("schema")!r} unbekannt')
    data = migrate(data)
    return validate(data['types'], data['lines'])


def migrate(data):
    """Register auf VERSION heben: v1 kennt keine Teilewahl (alle Linien Grundform), v2 hat `parts` je Linie optional."""
    version = data.get('version', 1)
    if version == 1:
        if any('parts' in e for e in data['lines']):
            raise ValueError('Register v1: `parts` gibt es erst ab Version 2')
        return dict(data, version=VERSION)
    if version != VERSION:
        raise ValueError(f'Register: Version {version!r} unbekannt')
    return data


def validate(types, entries):
    nums = [t.get('num') for t in types]
    if len(set(nums)) != len(nums) or any(not isinstance(n, int) or not 1 <= n <= 99 for n in nums):
        raise ValueError('Typ-Nummern müssen eindeutig und 1–99 sein')
    for t in types:
        if not re.fullmatch(r'formgen\.models\.robot\.[a-z0-9_]+', t.get('module', '')):
            raise ValueError(f"Typ {t.get('num')}: Modul {t.get('module')!r} liegt nicht unter formgen.models.robot")
        for key in ('name_de', 'since'):
            if key not in t:
                raise ValueError(f"Typ {t['num']}: Feld {key} fehlt")
    seen, names = set(), set()
    kit = catalog.load()
    for e in entries:
        letter, name = e.get('letter'), e.get('name', '')
        if letter not in LETTERS:
            raise ValueError(f'Kennbuchstabe {letter!r} ungültig (A–Z ohne I/O)')
        if not re.fullmatch(r'[A-Za-z0-9]+( [A-Za-z0-9]+){0,2}', name) or len(name) > 16:
            raise ValueError(f'Name {name!r}: 1–3 englische Wörter, höchstens 16 Zeichen')
        if letter in seen or name in names:
            raise ValueError(f'Doppelter Eintrag {letter}/{name}')
        seen.add(letter)
        names.add(name)
        for key in ('since', 'idea', 'skin', 'types'):
            if key not in e:
                raise ValueError(f'Linie {letter}: Feld {key} fehlt')
        unknown = set(e['types']) - set(nums)
        if unknown or not e['types']:
            raise ValueError(f'Linie {letter}: unbekannte Typen {sorted(unknown)}')
        for num, over in e.get('params', {}).items():
            locked = set(over) & {'variants', 'replace', 'helmet'}
            if locked:
                raise ValueError(f'Linie {letter}: {sorted(locked)} nur über [lines.parts], nie unter params.{num}')
        for assembly, vid in e.get('parts', {}).items():
            try:
                catalog.parse(assembly, vid, kit)
            except ValueError as err:
                raise ValueError(f'Linie {letter}: {err}') from None
    return dict(types=types, lines=entries)


def sheet_id(line, num) -> str:
    sid = f"R{line['letter']}{num:02d}"
    if sid in RESERVED:
        raise ValueError(f'{sid} ist reserviert')
    return sid


def merge(base, overrides, path=''):
    """Vollständige Parameter einer Linie; ein unbekannter Schlüssel ist ein Fehler, nie eine stille Ergänzung."""
    return catalog.merge(base, overrides, path, what='Linie')


def params_of(entry):
    """Vollständige Parameter eines Blatts: PARAMS des Typs, Linienparameter, dann die Teilewahl als PARAMS['variants'] (Buchstaben)."""
    module = module_of(entry)
    out = merge(module.PARAMS, entry['params'])
    if entry.get('parts'):
        out['variants'] = dict(out['variants'], **{a: vid.split('-')[1] for a, vid in entry['parts'].items()})
    return out


def variants_of(entry, kit=None):
    """Gewählte Varianten aller Einzelteile (Grundform, wo die Linie nichts wählt), JSON-fähig für Spec und --list."""
    kit = catalog.load() if kit is None else kit
    chosen = entry.get('parts', {})
    return [(catalog.parse(a, chosen[a], kit) if a in chosen else kit[a][catalog.BASE]).info() for a in catalog.ASSEMBLIES]


def sheets(register=None):
    """Blatt-ID → Eintrag {line, type, skin, params}; JSON-fähig, geht unverändert in die Artefakte."""
    register = load() if register is None else register
    types = {t['num']: t for t in register['types']}
    out = {}
    for line in register['lines']:
        for num in line['types']:
            out[sheet_id(line, num)] = dict(line={k: line[k] for k in ('letter', 'name', 'since', 'idea')}, type=types[num], skin=line['skin'],
                                            params=line.get('params', {}).get(str(num), {}))
            if line.get('parts'):           # nur bei einer Wahl: Einträge ohne Wahl (Linie A) bleiben wie in Version 1
                out[sheet_id(line, num)]['parts'] = dict(sorted(line['parts'].items()))
    return out


def module_of(entry):
    return importlib.import_module(entry['type']['module'])


def check_document(document):
    """Schnittstelle eines Basic-Typs: gemeinsame Baugruppen, Anker und Rollen, damit Website, Markierung und Skins für alle Typen gelten."""
    roles = tomllib.loads((ROOT / 'skins.toml').read_text())['roles']
    if document['info'].get('kind') != 'figure':
        raise ValueError('Basic-Typ: INFO.kind muss figure sein')
    found = [a['id'] for a in document['assemblies']]
    if sorted(found) != sorted(ASSEMBLIES):
        raise ValueError(f'Basic-Typ: Einzelteile {found}, erwartet {list(ASSEMBLIES)}')
    for a in document['assemblies']:
        if a['id'] not in GROUPS.get(a.get('group'), ()) or not a.get('group_de'):
            raise ValueError(f"Basic-Typ: Einzelteil {a['id']} gehört nicht zur Baugruppe {a.get('group')!r} oder group_de fehlt")
    missing = [s for s in SOCKETS if s not in document['anchors']]
    if missing:
        raise ValueError(f'Basic-Typ: Anker fehlen: {missing}')
    unknown = sorted({p['role'] for p in document['parts']} - set(roles))
    if unknown:
        raise ValueError(f'Basic-Typ: Rollen nicht in skins.toml: {unknown}')
    return document
