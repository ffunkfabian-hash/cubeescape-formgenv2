"""Validated kit vocabulary; no Blender imports and no implicit geometry transforms."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
from types import ModuleType

from .versions import MODEL as VERSION

SHAPES = {'prof', 'box', 'cyl', 'plan', 'frame', 'xbox', 'multi', 'tube', 'text', 'hull', 'loft', 'surface', 'prism2', 'xprof'}


class ModelError(ValueError):
    """Invalid source model, before geometry evaluation."""


def _alias(d, key, old):
    if old in d:
        if key in d and d[key] != d[old]:
            raise ModelError(f'Widersprüchliche Felder {key}/{old}')
        d[key] = d.pop(old)


def _point(value, n, name):
    if not isinstance(value, (list, tuple)) or len(value) != n or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in value):
        raise ModelError(f'{name}: {n} endliche Koordinaten erwartet')


def _provenance(value, name):
    if not isinstance(value, dict) or value.get('kind') not in ('Vorgabe', 'gemessen', 'Annahme') or not isinstance(value.get('source'), str) or not value['source'].strip():
        raise ModelError(f'{name}: Herkunft mit kind Vorgabe/gemessen/Annahme und source erforderlich')


def _shape(p):
    k = p.get('shape')
    if k not in SHAPES:
        raise ModelError(f'Unbekannte Form: {k!r}')
    required = {'box': 'f0 f1 u0 u1 w', 'prof': 'pts w', 'plan': 'pts u0 u1', 'cyl': 'axis c a0 a1 r', 'frame': 'f0 f1 cu ow oh iw ih r_out r_in', 'xbox': 'f0 f1 cu ww hh', 'multi': 'items', 'tube': 'path r', 'text': 'text size f u', 'hull': 'points', 'loft': 'rings', 'surface': 'vertices faces', 'prism2': 'side front', 'xprof': 'f0 f1 cu pts'}[k].split()
    for key in required:
        if key not in p:
            raise ModelError(f'{k}: Feld {key} fehlt')
    for key in ('f0','f1','u0','u1','w','x','a0','a1','r','r1','r_in','size','f','u','depth','cu','cx','ww','hh','ow','oh','iw','ih','r_out','thickness','bevel'):
        if key in p and (not isinstance(p[key], (int,float)) or isinstance(p[key], bool) or not math.isfinite(p[key])):
            raise ModelError(f'{k}: {key} muss eine endliche Zahl sein')
    for key in ('w', 'r', 'size', 'ww', 'hh', 'ow', 'oh', 'thickness'):
        if key in p and (not isinstance(p[key], (int, float)) or p[key] <= 0):
            raise ModelError(f'{k}: {key} muss positiv sein')
    for a, b in (('f0', 'f1'), ('u0', 'u1'), ('a0', 'a1')):
        if a in p and b in p and p[a] == p[b]:
            raise ModelError(f'{k}: {a}/{b} dürfen nicht gleich sein')
    for key, dims, minimum in (('pts', 2, 3), ('path', 3, 2), ('points', 3, 4), ('vertices', 3, 3), ('side', 2, 3), ('front', 2, 3)):
        if key in p and not (key == 'side' and k != 'prism2'):
            if len(p[key]) < minimum:
                raise ModelError(f'{k}: zu wenige Punkte in {key}')
            for point in p[key]:
                _point(point, dims, key)
    if k == 'cyl':
        if p['axis'] not in ('f', 'x', 'u'):
            raise ModelError('cyl: axis muss f/x/u sein')
        _point(p['c'], 2, 'cyl.c')
        if not isinstance(p.get('segs', 24), int) or p.get('segs', 24) < 3:
            raise ModelError('cyl: segs muss ganzzahlig >= 3 sein')
        if p.get('r1', p['r']) <= 0 or not 0 <= p.get('r_in', 0) < p['r']:
            raise ModelError('cyl: ungültige Radien')
    if k == 'multi':
        if not p['items']:
            raise ModelError('multi: items darf nicht leer sein')
        for q in p['items']:
            q.setdefault('shape', 'box')
            _shape(q)
    if k == 'loft':
        rings = p['rings']
        if len(rings) < 2 or len(rings[0]) < 3 or any(len(r) != len(rings[0]) for r in rings):
            raise ModelError('loft: mindestens zwei gleich lange Ringe mit >=3 Punkten')
        for ring in rings:
            for point in ring:
                _point(point, 3, 'loft.rings')
    if k == 'surface':
        for face in p['faces']:
            if len(face) < 3 or len(set(face)) != len(face) or any(not isinstance(i, int) or i < 0 or i >= len(p['vertices']) for i in face):
                raise ModelError('surface: ungültige Flächenindizes')
    for cut in p.get('cuts', []):
        _shape(cut)
    if 'bevel' in p and p['bevel'] < 0:
        raise ModelError('bevel darf nicht negativ sein')


def normalize(model):
    """Return an independent JSON-compatible canonical document; reject bad references."""
    if isinstance(model, ModuleType):
        model = {k: getattr(model, k) for k in ('INFO', 'META', 'PARTS', 'ASSEMBLIES', 'ANCHORS', 'POSES') if hasattr(model, k)}
    d = copy.deepcopy(model)
    for key in ('info', 'parts', 'assemblies', 'anchors', 'poses'):
        _alias(d, key, key.upper())
    _alias(d, 'info', 'META')
    if not isinstance(d.get('info'), dict) or not d['info'].get('id'):
        raise ModelError('INFO.id fehlt')
    info = d['info']
    if info.get('kind') not in ('weapon', 'sight', 'figure'):
        raise ModelError('INFO.kind muss weapon/sight/figure sein')
    if info.get('provenance') is not None:
        _provenance(info['provenance'], 'INFO')
    if not isinstance(d.get('assemblies'), list) or not d['assemblies']:
        raise ModelError('ASSEMBLIES muss eine nichtleere Liste sein')
    if not isinstance(d.get('parts'), list) or not d['parts']:
        raise ModelError('PARTS muss eine nichtleere Liste sein')
    assemblies = [a.get('id') for a in d['assemblies']]
    ids = [p.get('id') for p in d['parts']]
    for names, label in ((assemblies, 'Baugruppen'), (ids, 'Teile')):
        if any(not isinstance(n, str) or not n.strip() for n in names) or len(set(names)) != len(names):
            raise ModelError(f'{label}: IDs müssen eindeutige nichtleere Strings sein')
    for assembly in d['assemblies']:
        if 'explode' in assembly:
            _point(assembly['explode'], 3, 'assembly.explode')
    parents = {}
    for p in d['parts']:
        for key, old in (('assembly', 'asm'), ('role', 'mat'), ('label', 'de')):
            _alias(p, key, old)
        if p.get('assembly') not in assemblies:
            raise ModelError(f"{p['id']}: unbekannte Baugruppe")
        if not isinstance(p.get('role'), str) or not p['role']:
            raise ModelError(f"{p['id']}: Materialrolle fehlt")
        if any(key in p for key in ('color', 'colour', 'rgba', 'rgb')):
            raise ModelError('Farben gehören ausschließlich in skins.toml')
        _provenance(p.get('provenance', info.get('provenance')), p['id'])
        if p.get('parent_part'):
            if p['parent_part'] not in ids:
                raise ModelError(f"{p['id']}: unbekanntes parent_part")
            parents[p['id']] = p['parent_part']
        _shape(p)
    for pid in parents:
        seen = set()
        while pid in parents:
            if pid in seen:
                raise ModelError('Zyklische parent_part-Verknüpfung')
            seen.add(pid)
            pid = parents[pid]
    used = {p['assembly'] for p in d['parts']}
    if used != set(assemblies):
        raise ModelError(f'Leere Baugruppen: {sorted(set(assemblies) - used)}')
    d.setdefault('anchors', {})
    for name, a in d['anchors'].items():
        if not name.startswith('Socket_') or a.get('part') not in ids:
            raise ModelError(f'{name}: Socket-Name oder Teilreferenz ungültig')
        _point(a.get('at'), 3, name)
        if not a.get('source') and not a.get('provenance') and not info.get('provenance'):
            raise ModelError(f'{name}: Herkunft fehlt')
    d.setdefault('poses', {})
    d.setdefault('source', {})
    d.setdefault('warnings', [])
    try:
        return json.loads(json.dumps(d, allow_nan=False))
    except (TypeError, ValueError) as e:
        raise ModelError(f'Modell muss endlich und JSON-serialisierbar sein: {e}') from e


def load(path_or_module):
    """Load trusted Python model code by file, dotted module name, module or dictionary."""
    if isinstance(path_or_module, (dict, ModuleType)):
        return normalize(path_or_module)
    path = Path(path_or_module)
    if path.is_file():
        name = f'_formgen_model_{hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]}'
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        # Compile source directly: rapid edits must never reuse a timestamp-based pyc.
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    else:
        module = importlib.import_module(str(path_or_module))
        path = Path(module.__file__)
    d = normalize(module)
    root = Path(__file__).resolve().parents[1]
    resolved = path.resolve()
    source_name = str(resolved.relative_to(root)) if resolved.is_relative_to(root) else path.name
    d['source'] = {'path': source_name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return d
