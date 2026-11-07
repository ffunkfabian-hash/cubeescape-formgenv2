"""Varianten-Baukasten der Roboter (0.14 Kitbash): je Einzelteil ein Katalog von Formvarianten, beide Basic-Typen.

Wie die Waffenlinien aus BA01 entstehen neue Roboter gezielt aus RA01/RA02, aber je Einzelteil: Eine Linie wählt im Register
(data/robots.toml, `[lines.parts]`) je Einzelteil eine Variante, fehlende Einzelteile bleiben bei der Grundform `A`.

Variante: ewige ID `<Kürzel>-<Buchstabe>` (Kürzel je Einzelteil in CODES, Buchstabe A–Z ohne I/O, A = Grundform), englischer Name
1–3 Wörter ≤ 16 Zeichen, je Einzelteil nichts doppelt, `since`, Idee (deutsch), Herkunft (`origin`, kind Vorgabe/Annahme/gemessen).
Wirkung nur über Parameter im gemeinsamen Vokabular beider Typen (`params`, strikt: nur vorhandene Schlüssel, nie Skelett, Haltung,
Maße oder Proportionen), optional je Typ (`types`). RA02 setzt eine Variante um wie seine Profile (`ra02 = 'field'`: Verschiebungsfeld
und kalibrierte Aufsätze, roboterbasic_02_parameters.templates) oder ersetzt die gemessenen Teile des Einzelteils durch konstruierte,
eingepasst in die gemessenen Maße und Gelenkpunkte (`ra02 = 'replace'`, Ersatzmodus; kostet dort den gemessenen Look).

Beide Typen rufen `apply` in parts() vor proportion.apply. Mit lauter Grundformen kommt params unverändert (gleiches Objekt) zurück:
Linie A und die Specs von RA01/RA02 bleiben bytegleich. Module je Einzelteil-Gruppe: head, torso (Oberkörper), pelvis, shoulders,
arms (Oberarm, Unterarm, Hände), legs (Oberschenkel, Unterschenkel, Füße); jedes liefert VARIANTS ohne die Grundform.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

ASSEMBLIES = ('head', 'upper_body', 'pelvis', 'shoulders', 'upper_arms', 'forearms', 'hands', 'thighs', 'shins', 'feet')
CODES = dict(head='HD', upper_body='UB', pelvis='PV', shoulders='SH', upper_arms='UA', forearms='FA', hands='HN', thighs='TH',
             shins='SN', feet='FT')
LETTERS = set('ABCDEFGHJKLMNPQRSTUVWXYZ')
BASE = 'A'
NAME = re.compile(r'^[A-Z][a-z0-9]+(?: [A-Z][a-z0-9]+){0,2}$')
KINDS = ('Vorgabe', 'Annahme', 'gemessen')
MODES = ('field', 'replace')
LOCKED = ('skeleton', 'pose', 'dimensions', 'proportion', 'variants', 'replace')   # Gelenke, Haltung, Maße bleiben die des Typs
BASIC = dict(variants=dict.fromkeys(ASSEMBLIES, BASE))        # PARAMS['variants'] beider Typen: Grundform je Einzelteil
# Schalter der Konstruktoren in body.py, die PARAMS bisher nicht nannte, mit genau dem Wert, den der Konstruktor ohne Schlüssel nimmt
# (`P.get(key, default)`): Damit dürfen Varianten sie strikt setzen, und die Grundform bleibt bytegleich. Herkunft: body.py (BALLON 14bd78d).
OPTIONS = dict(
    torso=dict(shoulder_pistons=False, rings=(-20, 6, 32), chest=dict(split=False, vent_x=112),
               pauldron=dict(panel=None, panel_center=62, stripe_span=34, n=2.6)),
    pelvis=dict(hip_len=92),
    legs=dict(thigh_piston=False, thigh_cable=False, knee_pistons=False, calf_piston=False, foot_ch=14, thigh_top=150, knee_len=136,
              ankle_len=122),
    upper_arm=dict(piston=False),
)


@dataclass(frozen=True)
class Variant:
    assembly: str
    letter: str
    name: str
    since: str
    idea: str
    origin: dict
    params: dict = field(default_factory=dict)       # beide Typen, gemeinsames Vokabular (Schlüssel wie PARAMS von RA01)
    types: dict = field(default_factory=dict)        # {1: {...}, 2: {...}}: zusätzlich je Typ
    ra02: str = 'field'

    @property
    def id(self) -> str:
        return f'{CODES[self.assembly]}-{self.letter}'

    def info(self) -> dict:
        """JSON-fähige Beschreibung für Spec, --list und Website."""
        return dict(id=self.id, assembly=self.assembly, letter=self.letter, name=self.name, since=self.since, idea=self.idea,
                    origin=dict(self.origin), ra02=self.ra02)


def options(params, table=None):
    """Kopie von params mit allen OPTIONS-Schlüsseln, die noch fehlen; vorhandene Werte bleiben (RA02 schaltet manches aus)."""
    out = copy.deepcopy(params)
    for key, value in (OPTIONS if table is None else table).items():
        if isinstance(value, dict):
            out[key] = options(out[key], value)
        else:
            out.setdefault(key, copy.deepcopy(value))
    return out


def basic(assembly) -> Variant:
    return Variant(assembly, BASE, 'Basic', '0.14', 'Grundform des Typs, unverändert',
                   dict(kind='Vorgabe', source='RoboterBasic-01/-02 wie im Register, ohne Abwandlung'))


def _modules():
    from . import arms, head, legs, pelvis, shoulders, torso
    return (head, torso, pelvis, shoulders, arms, legs)


def merge(base, overrides, path='', what='Variante'):
    """Überschreibung mit vollständigem Pfad; ein unbekannter Schlüssel ist ein Fehler, nie eine stille Ergänzung."""
    out = copy.deepcopy(base)
    for key, value in overrides.items():
        if key not in out:
            raise ValueError(f'{what}: unbekannter Parameter {path}{key}')
        out[key] = merge(out[key], value, f'{path}{key}.', what) if isinstance(value, dict) and isinstance(out[key], dict) else value
    return out


def validate(variants):
    """Variantenregel je Einzelteil; liefert {Einzelteil: {Buchstabe: Variant}} mit der Grundform A."""
    out = {a: {BASE: basic(a)} for a in ASSEMBLIES}
    names = {a: {'Basic'} for a in ASSEMBLIES}
    for v in variants:
        if v.assembly not in out:
            raise ValueError(f'Variante {v.name!r}: Einzelteil {v.assembly!r} unbekannt')
        if v.letter not in LETTERS or v.letter == BASE:
            raise ValueError(f'{v.assembly}: Kennbuchstabe {v.letter!r} ungültig (B–Z ohne I/O, A ist die Grundform)')
        if not NAME.fullmatch(v.name) or len(v.name) > 16:
            raise ValueError(f'{v.id}: Name {v.name!r}: 1–3 englische Wörter, höchstens 16 Zeichen')
        if v.letter in out[v.assembly] or v.name in names[v.assembly]:
            raise ValueError(f'{v.id}: doppelter Eintrag {v.letter}/{v.name}')
        if not re.fullmatch(r'\d+\.\d+', v.since) or not v.idea:
            raise ValueError(f'{v.id}: since oder idea fehlt')
        if v.origin.get('kind') not in KINDS or not v.origin.get('source'):
            raise ValueError(f'{v.id}: Herkunft braucht kind aus {KINDS} und source')
        if v.ra02 not in MODES:
            raise ValueError(f'{v.id}: ra02 {v.ra02!r}, erlaubt {MODES}')
        if not v.params and not v.types and v.ra02 == 'field':
            raise ValueError(f'{v.id}: Variante ohne Wirkung')
        for over in (v.params, *v.types.values()):
            locked = set(over) & set(LOCKED)
            if locked:
                raise ValueError(f'{v.id}: {sorted(locked)} gehören dem Typ, nicht der Variante')
        if set(v.types) - {1, 2}:
            raise ValueError(f'{v.id}: unbekannte Typen {sorted(set(v.types) - {1, 2})}')
        out[v.assembly][v.letter] = v
        names[v.assembly].add(v.name)
    return out


def load():
    """Alle Kataloge, validiert; Reihenfolge der Einzelteile wie ASSEMBLIES."""
    return validate([v for m in _modules() for v in m.VARIANTS])


def parse(assembly, vid, catalog=None) -> Variant:
    """Register-ID (`SH-C`) eines Einzelteils → Variante; falsches Kürzel oder unbekannter Buchstabe ist ein Fehler."""
    catalog = load() if catalog is None else catalog
    if assembly not in catalog:
        raise ValueError(f'Einzelteil {assembly!r} unbekannt, erlaubt {list(ASSEMBLIES)}')
    m = re.fullmatch(r'([A-Z]{2})-([A-Z])', str(vid))
    if not m or m.group(1) != CODES[assembly] or m.group(2) not in catalog[assembly]:
        raise ValueError(f'{assembly}: Variante {vid!r} unbekannt, erlaubt {[v.id for v in catalog[assembly].values()]}')
    return catalog[assembly][m.group(2)]


def choice(params) -> dict:
    """Wahl je Einzelteil aus params['variants'] (Buchstaben), vollständig und geprüft."""
    chosen = params['variants']
    if set(chosen) != set(ASSEMBLIES):
        raise ValueError(f'variants: Einzelteile {sorted(chosen)}, erwartet {sorted(ASSEMBLIES)}')
    return chosen


def apply(params, *, num, measured=False, catalog=None):
    """Kopie von params mit den Parametern der gewählten Varianten; nur Grundformen → params unverändert (gleiches Objekt).

    num: Typ-Nummer (für `types`); measured: gemessener Typ (RA02), dann sammeln Varianten mit `ra02 = 'replace'` ihr Einzelteil in
    params['replace'] (Ersatzmodus, roboterbasic_02_parameters)."""
    chosen = choice(params)
    if all(letter == BASE for letter in chosen.values()):
        return params
    catalog = load() if catalog is None else catalog
    out = params
    replace = []
    for a in ASSEMBLIES:
        if chosen[a] not in catalog[a]:
            raise ValueError(f'{a}: Variante {CODES[a]}-{chosen[a]} unbekannt')
        v = catalog[a][chosen[a]]
        out = merge(out, v.params, what=v.id)
        out = merge(out, v.types.get(num, {}), what=v.id)
        if measured and v.ra02 == 'replace':
            replace.append(a)
    if measured:
        out = dict(out, replace=replace)
    return out


def assembly_of(pid, kind):
    """Einzelteil eines Konstruktorteils (body.py, arm.py) nach Segment `kind` und ID; gilt für RA01 und den Ersatzmodus von RA02.
    Zur Schulter gehören die Teile `pauldron_*`/`shoulder_*` (Segment SHOULDER_* der Referenz, im Rumpf- bzw. Oberarmrahmen)."""
    if pid.startswith(('pauldron_', 'shoulder_')):
        return 'shoulders'
    if kind == 'hand' or re.fullmatch(r'(f\d|t)_\d', kind):
        return 'hands'
    found = dict(head='head', torso='upper_body', pelvis='pelvis', thigh='thighs', shin='shins', foot='feet', upper='upper_arms',
                 fore='forearms').get(kind)
    if not found:
        raise ValueError(f'{pid}: Segment {kind} gehört zu keinem Einzelteil')
    return found
