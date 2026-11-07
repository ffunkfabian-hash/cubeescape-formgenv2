"""Ersatzmodus von RoboterBasic-02 (0.14 Kitbash): Einzelteile aus dem 01-Baukasten statt gemessener Teile.

Eine Variante mit `ra02 = 'replace'` (catalog.apply schreibt ihr Einzelteil in params['replace']) entfernt alle gemessenen Teile
dieses Einzelteils und setzt die Konstruktorteile aus body.py/arm.py (dieselben Parameter wie RA01) ein, eingepasst in die gemessenen
Maße. Ablauf je Einzelteil X:

1. Zuordnung. Ein gemessenes Teil gehört X nach `roboterbasic_02._assembly` (Quellbone). Ein Konstruktorteil gehört dem Einzelteil
   seines gemessenen Gegenstücks (`roboterbasic_02_parameters.binding`, Mehrheit), sonst dem Gegenstück seines Gruppenkopfs
   (`knee_ring` → `knee_axle`, `collar_trim` → `collar`), sonst `catalog.assembly_of`. An den Gelenken gelten so die Grenzen von
   RA02, nicht die von RA01: Ellbogen zum Oberarm, Knöchelachse zum Unterschenkel, Hüftgelenk zum Oberschenkel, Taille und
   Bauchplatten zum Becken, Kragen zum Kopf. Jedes Gelenk ist genau einmal da, gemessen oder ersetzt (keine doppelten, keine fehlenden).
2. Einpassung. Je Einzelteil und Einpassgruppe (Segment des Konstruktors; Schulterteile aus dem Rumpf um das Schultergelenk, Hüftteile
   aus dem Becken um das Hüftgelenk, die am Fuß gemessene Knöchelkolbenstange um den Knöchel, Finger um den gemessenen
   Fingerknochen, der 19–44 mm neben dem 01-Fingerrahmen des Quellrigs liegt) kommt der Gelenkpunkt des Konstruktors auf den gemessenen
   Gelenkpunkt, dann wird je Achse um ihn skaliert: Faktor = Ausgleich der Hüllenenden (Konstruktor-Grundform gegen gemessene Hülle,
   kleinste Quadrate), links und rechts gemeinsam, der Ursprung bleibt fest. Die Faktoren kommen aus der Grundform des Typs (defaults);
   Variantenmaße und Proportionen wirken darum relativ dazu weiter (erst Ersatz, dann wie gehabt Proportionen).
3. Lage. Jedes Ersatzteil übernimmt Knochen, Rahmen und Schultermontage eines gemessenen Teils (Wirt: Gegenstück, sonst Gegenstück
   des Gruppenkopfs, sonst größtes Teil der Gruppe) und geht dann den normalen Rig-Weg (`roboterbasic_02._transform`) in die Haltung.

Herkunft: Konstruktorzahlen Vorgabe (BALLON 14bd78d über body.py/arm.py), Zuordnung und Einpassung Annahme (dieses Modul).
"""
from __future__ import annotations

from copy import deepcopy
import re

import numpy as np

from . import catalog, kit
from . import roboterbasic_02_parameters as profiles

SCALE_LIMITS = (0.25, 4.0)      # Annahme: außerhalb ist die Einpassung kein Anpassen mehr, sondern ein Fehler der Zuordnung
MIN_END = 5.0                   # mm, Annahme: kürzere Hüllenenden am Gelenk tragen keine Skala (Rauschen der Mittelachse)
FIT = True                      # Gegenprobe der Tests: False baut die rohen 01-Maße ohne Gelenkabgleich und Skalierung
ALLOWED = tuple(a for a in catalog.ASSEMBLIES if a != 'head')   # Kopf (Helm H 80) noch nicht eingepasst
PROVENANCE = ('Ersatzmodus, eingepasst in gemessene Maße: Konstruktor {key} (body.py/arm.py, Vorgabe BALLON 14bd78d); '
              'Gelenkpunkt auf das gemessene Gelenk, Skala −/+ je Segmentachse x y z {scale} um das Gelenk, Gruppe {group} (Annahme)')
_HEADS = ('', '_axle', '_disc', '_cyl', '_core')
_LIMB = ('upper', 'fore', 'hand')
_FINGER = re.compile(r'(f\d|t)_\d')
# Einpassgruppen, die nicht dem Konstruktorsegment folgen (Segmentart, Besitzer) → Gruppe: Schulterteile des Rumpfs um das Schultergelenk,
# Hüftteile des Beckens um das Hüftgelenk, die Knöchelkolbenstange (in RA02 am Fuß gemessen) mit dem Fuß um den Knöchel. Annahme.
_SPECIAL = {('torso', 'shoulders'): 'shoulder', ('pelvis', 'thighs'): 'hip', ('shin', 'feet'): 'foot'}


def _two():
    from . import roboterbasic_02 as two     # zur Laufzeit: roboterbasic_02 importiert dieses Modul über die Profile
    return two


def _sided(kind):
    return kind in ('thigh', 'shin', 'foot') or kind in _LIMB or bool(_FINGER.fullmatch(kind))


def _native(kind, side):
    if kind in ('thigh', 'shin', 'foot'):
        return f'{kind}_{side}'
    if kind in _LIMB or _FINGER.fullmatch(kind):
        return f'arm_{side}_{kind}'
    return kind


def _finger_bone(kind, side):
    finger, link = kind.split('_')
    if finger == 't':
        return ('thumb', 'thumbmid', 'thumbtip')[int(link)] + '_' + side
    return ('finger', 'fingermid', 'fingertip')[int(link)] + str(int(finger[1:]) + 1) + '_' + side


def _row_side(row):
    bone = row['bone']
    return bone[-1] if bone.endswith(('_R', '_L')) else 'C'


def _pid_side(pid):
    m = re.search(r'_([rl])(?:_|$)', pid)
    if not m:
        raise ValueError(f'Ersatzmodus: Seite von {pid} unbekannt')
    return m.group(1).upper()


def _direct(row):
    return profiles.binding(dict(row, profile_binding=None))


def _size(row):
    cloud = profiles._cloud(row)
    return -float(np.prod(np.ptp(cloud, axis=0) + 1)) if len(cloud) else 0.0


class Plan:
    """Zuordnung ohne Geometrie: Besitzer, Einpassgruppe und Wirt je Konstruktorteil, Gruppen der gemessenen Teile."""

    def __init__(self, params, rows, associated=None):
        two = _two()
        bad = sorted(set(params.get('replace', ())) - set(ALLOWED))
        if bad:
            raise ValueError(f'replace: {bad} ohne Ersatzmodus, erlaubt {list(ALLOWED)}')
        self.replace = [a for a in ALLOWED if a in params.get('replace', ())]
        self.raw = rows
        self.rows = profiles.associate(rows) if associated is None else associated
        self.assembly = {r['id']: two._assembly(r) for r in self.rows}
        self.canonical = profiles._canonical(params)
        votes = {}
        for r in self.rows:
            key = _direct(r)
            if key is not None:
                votes.setdefault(key, []).append(self.assembly[r['id']])
        order = {a: i for i, a in enumerate(catalog.ASSEMBLIES)}
        self.bound = {key: min(set(v), key=lambda a: (-v.count(a), order[a])) for key, v in votes.items()}
        self._hosts = {}

    def owner(self, key):
        """Einzelteil eines Konstruktorteils nach den Grenzen von RA02 (Modulkopf, Punkt 1)."""
        if key in self.bound:
            return self.bound[key]
        family, pid = key
        tokens = pid.split('_')
        for n in range(len(tokens) - 1, 0, -1):
            for suffix in _HEADS:
                head = (family, '_'.join(tokens[:n]) + suffix)
                if head in self.bound:
                    return self.bound[head]
        kind = self.canonical[key][2] if key in self.canonical else None
        return catalog.assembly_of(pid, kind)

    def group(self, key, kind, side):
        """Einpassgruppe (Art, Seite): Schulter- und Hüftteile aus Rumpf und Becken um ihr Gelenk, sonst das Segment."""
        special = _SPECIAL.get((kind, self.owner(key)))
        if special:
            return special, side if _sided(kind) else _pid_side(key[1])
        return kind, side if _sided(kind) else 'C'

    def constructor(self, X):
        """[(key, kind, side, group)] der Konstruktorteile von X in Konstruktorreihenfolge."""
        out = []
        for key, row in self.canonical.items():
            if self.owner(key) != X:
                continue
            kind = row[2]
            for side in (('R', 'L') if _sided(kind) else ('C',)):
                group = self.group(key, kind, side)
                out.append((key, kind, group[1] if group[1] != 'C' else side, group))
        return out

    def measured_group(self, row):
        """Einpassgruppe eines gemessenen Teils: über seine Bindung an ein Konstruktorteil, Finger über ihr Segment."""
        key = profiles.binding(row)
        if key is None:
            seg = _two()._segment(row['bone'])
            return (seg.split('_', 2)[2], _row_side(row)) if seg.startswith('arm_') else None
        if key not in self.canonical:
            return None
        return self.group(key, self.canonical[key][2], _row_side(row))

    def measured(self, X):
        return [r for r in self.rows if self.assembly[r['id']] == X]

    def hosts(self, X):
        """Wirt je Konstruktorteil von X und gemessene Teile je Gruppe (Modulkopf, Punkt 3)."""
        if X in self._hosts:
            return self._hosts[X]
        by_group, by_key = {}, {}
        for r in self.measured(X):
            by_group.setdefault(self.measured_group(r), []).append(r)
            key = _direct(r)
            if key is not None:
                by_key.setdefault((key, _row_side(r)), []).append(r)
        out = {}
        for key, kind, side, group in self.constructor(X):
            family, pid = key
            tokens = pid.split('_')
            heads = [key] + [(family, '_'.join(tokens[:n]) + s) for n in range(len(tokens) - 1, 0, -1) for s in _HEADS]
            found = None
            for head in heads:
                for s in dict.fromkeys((side, 'C')):
                    rows = [r for r in by_key.get((head, s), ()) if self.measured_group(r) == group]
                    if rows:
                        found = min(rows, key=lambda r: (_size(r), r['id']))
                        break
                if found:
                    break
            if found is None and by_group.get(group):
                found = min(by_group[group], key=lambda r: (_size(r), r['id']))
            if found is None:
                raise ValueError(f'Ersatzmodus {X}: kein gemessenes Teil der Gruppe {group} als Wirt für {family}.{pid}')
            out[(key, side)] = found
        self._hosts[X] = out, by_group
        return out, by_group

    @staticmethod
    def kit_id(key, kind, side):
        return f'{_native(kind, side if _sided(kind) else "C")}_kit_{key[1]}'

    def part_map(self):
        """Gemessene ID → Ersatzteil-ID für alle Teile ersetzter Einzelteile (Anker, Gelenke, parent_part)."""
        out = {}
        for X in self.replace:
            hosts, _ = self.hosts(X)
            hosted, keyed, grouped, sided = {}, {}, {}, {}
            for key, kind, side, group in self.constructor(X):
                pid = self.kit_id(key, kind, side)
                hosted.setdefault(hosts[(key, side)]['id'], pid)
                keyed.setdefault((key, side), pid)
                grouped.setdefault(group, pid)
                sided.setdefault(side, pid)
            for r in self.measured(X):
                side = _row_side(r)
                key = profiles.binding(r)
                choice = (hosted.get(r['id']) or keyed.get((key, side)) or keyed.get((key, 'C'))
                          or grouped.get(self.measured_group(r)) or sided.get(side) or next(iter(sided.values()), None))
                if choice is None:
                    raise ValueError(f'Ersatzmodus {X}: kein Ersatzteil für {r["id"]}')
                out[r['id']] = choice
        return out


def part_map(params, rows):
    """Für roboterbasic_02.anchors/joints: gemessene ID → Ersatzteil-ID; leer ohne Ersatz."""
    return Plan(params, rows).part_map() if params.get('replace') else {}


def _frames(group, params, base_frames):
    """(O, R_cal, J, R_c) einer Gruppe in Quellwelt-mm (XYZ): gemessenes Gelenk mit Achsen, Gelenk des Konstruktors mit Achsen."""
    kind, side = group
    sx = 1 if side == 'R' else -1
    if kind == 'shoulder':
        R, o, _, _ = base_frames['torso']
        t = params['torso']
        return base_frames[f'arm_{side}_upper'][1], R, o + R @ np.array((sx * t['SX'], 0.0, t['SZ'])), R
    if kind == 'hip':
        R, o, _, _ = base_frames['pelvis']
        p = params['pelvis']
        return base_frames[f'thigh_{side}'][1], R, o + R @ np.array((sx * p['hip_x'], 0.0, p['hip_z'])), R
    R, o, _, _ = base_frames[_native(kind, side)]
    if _FINGER.fullmatch(kind):
        # RA02-Finger liegen an ihren gemessenen Knochen, nicht an den 01-Fingerrahmen des Quellrigs (19–44 mm, bis 42° daneben).
        two = _two()
        bone = _finger_bone(kind, side)
        head, tail = two._point(bone), two._point(bone, 'tail')
        z = (tail - head) / np.linalg.norm(tail - head)
        y = R[:, 1] - (R[:, 1] @ z) * z
        y /= np.linalg.norm(y)
        return head, np.column_stack([np.cross(y, z), y, z]), o, R
    return o, R, o, R


def _build(key, kind, side, row, base_frames):
    """Konstruktorteil wie RA01 (kit.part) im Quellrahmen von RA02; Koordinaten f/u/x der Quellwelt, links an X gespiegelt."""
    pid, label, _, form, role, options = row
    name = _native(kind, side if _sided(kind) else 'C')
    R, o, _, _ = base_frames[name]
    return kit.part(pid, label, name, form, role, options, (R, o), -1 if _sided(kind) and side == 'L' else 1, '', side)


def _hull(clouds):
    every = np.concatenate([c for c in clouds if len(c)])
    return every.min(axis=0), every.max(axis=0)


def _mirror(group):
    """Linke Seite in rechte Koordinaten: Konstruktor und Rig spiegeln links an der Segment-X-Achse (kit.part sx = −1)."""
    return np.array((-1.0, 1.0, 1.0)) if group[1] == 'L' else np.ones(3)


def _end(pairs, index, other=None):
    """Skala eines Hüllenendes über alle Seiten (kleinste Quadrate); Enden unter MIN_END mm oder mit Vorzeichenwechsel zählen nicht."""
    num = den = 0.0
    for c, m in pairs:
        if abs(c[index]) >= MIN_END and c[index] * m[index] > 0:
            num += c[index] * m[index]
            den += c[index] ** 2
    return num / den if den else other


def _scale(pairs):
    """Skala je Achse und Richtung um den Ursprung: (−, +) je Achse, Ursprung fest, stetig; die Hüllenenden treffen die Messung.

    pairs: [((lo_c, hi_c), (lo_m, hi_m))] je Seite in rechten Koordinaten. Fehlt ein Ende (Gruppe nur auf einer Seite des Gelenks),
    gilt die Skala des anderen; fehlen beide, das Verhältnis der Ausdehnungen."""
    out = np.ones((2, 3))
    for axis in range(3):
        lo = [((c[0][axis], c[1][axis]), (m[0][axis], m[1][axis])) for c, m in pairs]
        neg, pos = _end(lo, 0), _end(lo, 1)
        if neg is None and pos is None:
            ext_c = sum(c[1] - c[0] for c, _ in lo)
            neg = pos = sum(m[1] - m[0] for _, m in lo) / ext_c if ext_c > 1e-9 else 1.0
        out[:, axis] = (neg if neg is not None else pos, pos if pos is not None else neg)
    return np.clip(out, *SCALE_LIMITS)


def _fit(O, Rcal, J, Rc, s, mirror):
    def apply(v):
        n = (v - J) @ Rc * mirror
        n = np.where(n < 0, n * s[0], n * s[1])
        return O + (n * mirror) @ Rcal.T
    return apply


def fits(plan, defaults, base_frames):
    """{Einzelteil: {Gruppenart: Skala (−, +) × x/y/z}} aus der Grundform des Typs (defaults) gegen die gemessene Hülle."""
    base = Plan(dict(defaults, replace=plan.replace), plan.raw, plan.rows)
    out = {}
    for X in plan.replace:
        _, by_group = base.hosts(X)
        local_c = {}
        for key, kind, side, group in base.constructor(X):
            O, Rcal, J, Rc = _frames(group, defaults, base_frames)
            cloud = profiles._cloud(_build(key, kind, side, base.canonical[key], base_frames))
            local_c.setdefault(group, []).append((cloud - J) @ Rc * _mirror(group))
        pairs = {}
        for group, clouds in local_c.items():
            if by_group.get(group):
                O, Rcal, _, _ = _frames(group, defaults, base_frames)
                measured = [(profiles._cloud(r) - O) @ Rcal * _mirror(group) for r in by_group[group]]
                pairs.setdefault(group[0], []).append((_hull(clouds), _hull(measured)))
        out[X] = {kind: _scale(p) for kind, p in pairs.items()}
    return out


def _break_cycles(new, rows):
    """Jeder Zyklus enthält ein Ersatzteil (gemessen ist azyklisch, umgehängte Teile zeigen auf Ersatzteile): dessen parent_part fällt weg."""
    parents = {r['id']: r.get('parent_part') for r in rows}
    for r in new:
        seen, p = {r['id']}, r.get('parent_part')
        while p:
            if p == r['id'] or p in seen:
                if p == r['id']:
                    r.pop('parent_part', None)
                    parents[r['id']] = None
                break
            seen.add(p)
            p = parents.get(p)


def build(params, defaults, rows, base_frames):
    """(übrige gemessene Teile, Ersatzteile, Plan) für params['replace']; parent_part auf ersetzte Teile zeigt dann auf Ersatzteile."""
    plan = Plan(params, rows)
    mapping = plan.part_map()
    scales = fits(plan, defaults, base_frames) if FIT else {}
    kept = []
    for raw in rows:
        if plan.assembly[raw['id']] in plan.replace:
            continue
        if raw.get('parent_part') in mapping:
            raw = dict(raw, parent_part=mapping[raw['parent_part']])
        kept.append(raw)
    new = []
    for X in plan.replace:
        hosts, _ = plan.hosts(X)
        for key, kind, side, group in plan.constructor(X):
            host = hosts[(key, side)]
            part = _build(key, kind, side, plan.canonical[key], base_frames)
            s = scales.get(X, {}).get(group[0], np.ones((2, 3)))
            if FIT:
                part = profiles._map(part, _fit(*_frames(group, params, base_frames), s, _mirror(group)))
            pid = plan.kit_id(key, kind, side)
            row = {k: deepcopy(part[k]) for k in profiles._GEOMETRY if k in part}
            row.update(id=pid, source_object=f'Kit_{key[1]}_{side}', label=part['label'], role=part['role'],
                       bone=host['bone'], assembly=host['assembly'], bevel=part['bevel'],
                       provenance=dict(kind='Annahme', source=PROVENANCE.format(
                           key=f'{key[0]}.{key[1]}', group=f'{X}/{group[0]}',
                           scale=' '.join('{:.4f}/{:.4f}'.format(*s[:, i]) for i in range(3)) if FIT else 'keine (Gegenprobe)')))
            for field in ('frame', 'mount_frame', 'length_scale'):
                if field in host:
                    row[field] = deepcopy(host[field])
            parent = mapping.get(host.get('parent_part'), host.get('parent_part'))
            if parent and parent != pid:
                row['parent_part'] = parent
            new.append(row)
    _break_cycles(new, kept + new)
    return kept, new, plan
