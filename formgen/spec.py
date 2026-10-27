"""Measured specifications from the shared evaluated geometry; no rendering."""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import tomllib

import jsonschema
from .versions import SPEC as VERSION

ROOT = Path(__file__).resolve().parents[1]
MEASURE = 'gemessen: ausgewertete mesh.vertices/mesh.faces in Metern; AABB und Dreiecksflächen'
CHANNELS = ('MT_Primary', 'MT_Secondary', 'MT_Accent', 'MT_Metal', 'MT_Energy', 'MT_Emission', 'MT_Detail')
ROLE_CHANNEL = {'shell': 'MT_Primary', 'graphite': 'MT_Secondary', 'rubber': 'MT_Secondary',
                'string': 'MT_Secondary', 'accent': 'MT_Accent', 'metal': 'MT_Metal',
                'trim': 'MT_Metal', 'brass': 'MT_Metal', 'energy': 'MT_Energy'}


def bounds(parts, origin=(0, 0, 0)):
    vertices = [v for p in parts for v in p['mesh']['vertices']]
    if not vertices:
        raise ValueError('Spec benötigt ausgewertete, nichtleere Geometrie')
    if any(len(v) != 3 or not all(math.isfinite(x) for x in v) for v in vertices):
        raise ValueError('Spec: ungültige Netzkoordinaten')
    return [[min(v[i] for v in vertices)-origin[i] for i in range(3)],
            [max(v[i] for v in vertices)-origin[i] for i in range(3)]]


def dimensions(parts, origin=(0, 0, 0)):
    bb = bounds(parts, origin)
    width, length, height = [bb[1][i]-bb[0][i] for i in range(3)]
    return dict(length=length, height=height, width=width, bounds_m=bb, source=MEASURE)


def area(part):
    # Evaluated meshes are triangles. Import preservation never retriangulates v1.
    vertices = part['mesh']['vertices']
    total = 0.
    for face in part['mesh']['faces']:
        if len(face) != 3:
            raise ValueError('Neue Specs benötigen ausgewertete Dreiecksflächen')
        a, b, c = [vertices[i] for i in face]
        u, v = ([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        total += math.sqrt(sum(x*x for x in cross))/2
    return total


def validate(spec):
    kind = spec['format'].rsplit('/', 1)[-1]
    if kind not in ('weapon-spec', 'sight-spec', 'figure-spec'):
        raise ValueError('Unbekannter Spec-Vertrag')
    schema = json.loads((ROOT / 'docs/schemas' / f'{kind}.schema.json').read_text())
    jsonschema.Draft202012Validator(schema).validate(spec)
    json.dumps(spec, allow_nan=False)
    if kind == 'figure-spec':
        ids=[p['id'] for p in spec['parts']]
        assemblies=[a['id'] for a in spec['assemblies']]
        if len(set(ids)) != len(ids) or len(set(assemblies)) != len(assemblies):
            raise ValueError('Figure-Spec: doppelte Teil-/Baugruppen-ID')
        for part in spec['parts']:
            if part['assembly'] not in assemblies or (part.get('parent_part') is not None and part['parent_part'] not in ids):
                raise ValueError('Figure-Spec: unbekannte Baugruppe oder Elternteil')
        for anchor in spec['anchors'].values():
            if anchor.get('part') is not None and anchor['part'] not in ids:
                raise ValueError('Figure-Spec: Anker verweist auf unbekanntes Teil')
    return spec


def _source(document):
    return copy.deepcopy(document.get('source', {}))


def _figure(document):
    parts = []
    for part in document['parts']:
        parts.append(dict(id=part['id'], label=part.get('label', part['id']),
                          assembly=part['assembly'], role=part['role'],
                          parent_part=part.get('parent_part'),
                          dimensions_m=dimensions([part]), area_m2=area(part),
                          provenance=copy.deepcopy(part.get('provenance', document['info'].get('provenance')))))
    return dict(format='cubeescape-formgen/figure-spec', format_version=1,
                generator=dict(repo='cubeescape-formgenv2', tool='formgen/spec.py', version=VERSION),
                figure=copy.deepcopy(document['info']), units='m',
                axes=dict(forward='-Y', up='+Z', left='+X', origin='author_origin'),
                dimensions_m=dimensions(document['parts']), assemblies=copy.deepcopy(document['assemblies']),
                parts=parts, anchors=copy.deepcopy(document['anchors']), poses=copy.deepcopy(document.get('poses', {})),
                measurement_source=MEASURE, source=_source(document), warnings=list(document.get('warnings', [])))


def _channel(role):
    return ROLE_CHANNEL.get(role, 'MT_Emission' if role.startswith('reticle_') else 'MT_Detail')


def _material(role, material):
    if material.get('emit') or material.get('emit_only'):
        return 'lit', 'energy_glass'
    if role.startswith('glass'):
        return 'glass', None
    if role in ('rubber', 'string'):
        return 'rubber', 'rubber'
    if material.get('metal', 0) >= .5:
        return 'brushed', 'brushed'
    if role == 'graphite':
        return 'matte', 'painted_matte'
    return 'painted', 'painted'


def _weapon(document):
    info, original = document['info'], document['parts']
    hand = document['anchors'].get('Socket_Hand')
    if not hand or hand.get('position_m') is None:
        raise ValueError('Weapon-Spec benötigt einen belegten Socket_Hand')
    origin = hand['position_m']
    ids = {key: f'p{i:02d}' for i, key in enumerate(p['id'] for p in original)}
    if len(ids) != len(original) or len(ids) > 1000:
        raise ValueError('Teil-IDs sind doppelt oder überschreiten p999')
    raw = (ROOT / 'skins.toml').read_bytes()
    skins = tomllib.loads(raw.decode())
    colors, parts = {}, []
    for p in original:
        role = p['role']
        mat = skins['roles'][role]
        channel = _channel(role)
        material, toolgen_material = _material(role, mat)
        bb = bounds([p], origin)
        extent = [bb[1][i]-bb[0][i] for i in range(3)]
        color = mat['color'].upper()
        colors.setdefault(channel, color)
        parts.append(dict(id=ids[p['id']], source_id=p['id'], label=p.get('label', p['id']),
                          assembly=p['assembly'], parent_part=ids.get(p.get('parent_part')), author_move=copy.deepcopy(p.get('move')), channel=channel, channel_source='role', role=role,
                          material=material, toolgen_material=toolgen_material,
                          emissive=material == 'lit', sight=bool(p.get('sight') or p['assembly'] == 'sight'),
                          color=color, area_m2=area(p), bounds_m=bb,
                          long_axis='XYZ'[extent.index(max(extent))], measurement_source=MEASURE,
                          provenance=copy.deepcopy(p.get('provenance', info.get('provenance')))))
    anchors = {}
    for name in sorted(set(document['anchors']) | {'Socket_Hand', 'Socket_SupportHand', 'Socket_Muzzle', 'Socket_CenterOfMass', 'Socket_Sight'}):
        a = document['anchors'].get(name)
        if not a:
            anchors[name] = dict(position_m=None, model=None, part=None, source='nicht definiert; keine Massenannahme')
            continue
        position = a.get('position_m')
        provenance = a.get('provenance', info.get('provenance', {}))
        source = a.get('source') or provenance.get('source') or a.get('note')
        if not source:
            raise ValueError(f'{name}: Herkunft fehlt')
        anchors[name] = dict(position_m=[position[i]-origin[i] for i in range(3)] if position is not None else None,
                             model=copy.deepcopy(a.get('at')), part=ids.get(a.get('part')), source=source,
                             provenance=copy.deepcopy(provenance), note=a.get('note'))
    palette = []
    for pid, skin in [('base', None), ('standard', 'standard'), ('arktis', 'polar'), ('nacht', 'nacht')]:
        overrides = skins['skins'][skin].get('roles', {}) if skin else {}
        channels, other = {c: None for c in CHANNELS}, {}
        for p in parts:
            color = overrides.get(p['role'], skins['roles'][p['role']]['color']).upper()
            channel = p['channel']
            if channels[channel] is None:
                channels[channel] = color
            elif channels[channel] != color:
                other.setdefault(channel, {})[p['id']] = color
        swatches = [overrides.get(role, skins['roles'][role]['color']).upper() for role in ('shell', 'graphite', 'accent', 'metal')]
        palette.append(dict(id=pid, name=skins['skins'][skin]['de'] if skin else 'Basis',
                            swatches=swatches, channels=channels, other_colors=other, on_sheet=pid == 'standard',
                            sight_colors='wie Modell', source=f'skins.toml: {skin or "roles"}; arktis=polar, nacht=nacht, standard=standard'))
    sight_parts = [p for p in original if p.get('sight') or p['assembly'] == 'sight']
    weapon_parts = [p for p in original if p not in sight_parts]
    dims = dimensions(original, origin)
    # Type mapping is declared compatibility, never inferred from a silhouette.
    tid = {'auto_rifle': 'assault_rifle'}.get(info.get('type'))
    result = dict(format='cubeescape-design/weapon-spec', format_version=2,
                  generator=dict(repo='cubeescape-formgenv2', tool='formgen/spec.py', claude_version=None, version=VERSION),
                  sheet=dict(id=info['id'], file=f"{info['id']}.dc.html", variant=str(info.get('variant', '')),
                             number=str(info.get('num', '')), nick=info.get('nick', info['name_de']), fid=info.get('source_id', info['id'])),
                  weapon=dict(name_de=info.get('type_de', info['name_de']), toolgen_id=tid,
                              toolgen_status='tool' if tid else 'not_connected', type_source='INFO.type; auto_rifle → assault_rifle'),
                  element=None, element_source='im Autorenmodell nicht festgelegt',
                  units=dict(model_unit_m=.001, model_length_units=dims['length']*1000,
                             reference_length_m=info.get('reference_length_m', dims['length']),
                             rule='Autorenmillimeter; keine Skalierung an Referenzlänge',
                             reference=info.get('reference_length_source', MEASURE)),
                  axes=dict(model=dict(f='vorn', u='oben', x='links'),
                            target=dict(system='Toolgen/Blender', forward='-Y', up='+Z', left='+X', unit='m'),
                            matrix_model_to_target=[[0, 0, 1], [-1, 0, 0], [0, 1, 0]], origin='Socket_Hand',
                            formula='p_m = 0.001 * M * (p_fux_mm - Socket_Hand.model)',
                            origin_world_m=list(origin), origin_source=anchors['Socket_Hand']['source']),
                  dimensions_m=dict(weapon=dimensions(weapon_parts, origin), with_sight=dims),
                  anchors=anchors, palette=palette, channels_used=[c for c in CHANNELS if c in colors], parts=parts,
                  sight=dict(present=bool(sight_parts), kind=None, window=None, source='Baugruppe sight; Typ/Fenster nicht aus Netzen geraten',
                             modular=False, mount_side=None, labels=[p.get('label', p['id']) for p in sight_parts],
                             parts=[ids[p['id']] for p in sight_parts], bounds_m=bounds(sight_parts, origin) if sight_parts else None,
                             anchor='Socket_Sight' if sight_parts else None),
                  decals=[], textures=dict(source='Materialrollen skins.toml; keine Texturmuster spezifiziert',
                                           vocabulary='Weapon-Spec 2', **{k: None for k in ('painted', 'brushed', 'rubber', 'matte', 'lit')}),
                  summary=dict(parts=len(parts), parts_explicit_channel=0, decals=0,
                               channels_with_other_colors={p['id']: sorted(p['other_colors']) for p in palette if p['other_colors']}),
                  part_id_map=ids, source=_source(document),
                  material_source=dict(path='skins.toml', sha256=hashlib.sha256(raw).hexdigest()),
                  warnings=list(document.get('warnings', [])))
    return validate(result)


def build(document):
    """Preserve verified imported v1 specs; generate only from evaluated geometry."""
    if 'source_spec' in document:
        return validate(copy.deepcopy(document['source_spec']))
    if 'source_geo' in document:
        raise ValueError('Geo-Import ohne SHA-geprüfte Original-Spec; keine Vertragsrekonstruktion')
    kind = document['info']['kind']
    if kind == 'weapon':
        return _weapon(document)
    if kind == 'figure':
        return validate(_figure(document))
    raise ValueError(f'Neue {kind}-Spec nicht implementiert; geprüften Geo-Import verwenden')
