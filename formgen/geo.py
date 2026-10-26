"""Geo-Eingang ohne v1-Modellmodule. Vertrag: v1 geometry-spec und ballon/geo v1.

Schema unverändert aus cubeescape-formgen/claude/docs/geometry-spec.schema.json.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import itertools
import re
import unicodedata
from pathlib import Path
import jsonschema
from .versions import GEO as VERSION

ROOT = Path(__file__).resolve().parents[1]
LEGACY = 'cubeescape-design/geometry-spec'
NATIVE = 'cubeescape-formgen/geometry-spec'
FIGURE = 'cubeescape-formgen/figure-geo'
FORMATS = {LEGACY, NATIVE, FIGURE, 'cubeescape-ballon/geo'}


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('Nichtendliche Zahl im Geo-Dokument')
    if isinstance(value, dict):
        for v in value.values(): _finite(v)
    elif isinstance(value, list):
        for v in value: _finite(v)


def validate(data):
    if data.get('format') not in FORMATS or data.get('format_version') != 1:
        raise ValueError('Unbekanntes Geo-Format oder Version (erwartet v1)')
    _finite(data)
    if data['format'] in (LEGACY, NATIVE, FIGURE):
        filename = {LEGACY:'v1-geo.schema.json', NATIVE:'native-geo.schema.json', FIGURE:'figure-geo.schema.json'}[data['format']]
        schema = json.loads((ROOT / 'docs/schemas' / filename).read_text())
        jsonschema.Draft202012Validator(schema).validate(data)
    else:
        # Ballons Export ist noch nicht vorhanden: expliziter Mindestvertrag,
        # keine Behauptung einer Produzentenabnahme.
        for field in ('parts', 'anchors', 'counts', 'source'):
            if field not in data: raise ValueError(f'Ballon Geo: {field} fehlt')
    parts = data['parts']
    if not parts: raise ValueError('Geo ohne Teile')
    ids = [p['id'] for p in parts]
    if len(ids) != len(set(ids)): raise ValueError('Doppelte Teil-IDs')
    counts = dict(parts=len(parts), vertices=0, faces=0, triangles=0)
    for p in parts:
        mesh = p['mesh']; vertices, faces = mesh['vertices'], mesh['faces']
        if not vertices or not faces: raise ValueError(f'{p["id"]}: leeres Netz')
        if any(len(v) != 3 or any(not isinstance(x, (int, float)) or isinstance(x, bool) for x in v) for v in vertices):
            raise ValueError(f'{p["id"]}: ungültige Vertices')
        for face in faces:
            if len(face) < 3 or len(set(face)) != len(face) or any(type(i) is not int or i < 0 or i >= len(vertices) for i in face):
                raise ValueError(f'{p["id"]}: ungültige Flächenindizes')
        if len(mesh.get('hard', [1]*len(faces))) != len(faces): raise ValueError('hard-Länge stimmt nicht')
        if any(type(h) is not int or h not in (0,1) for h in mesh.get('hard', [])):
            raise ValueError('hard muss 0/1 enthalten')
        if 'bounds_m' in p:
            bb = _bounds(vertices)
            if any(abs(p['bounds_m'][j][i]-bb[j][i]) > 1e-8 for j in range(2) for i in range(3)):
                raise ValueError(f'{p["id"]}: bounds_m weicht vom Netz ab')
        counts['vertices'] += len(vertices); counts['faces'] += len(faces)
        counts['triangles'] += sum(len(f)-2 for f in faces)
    for k,v in counts.items():
        if type(data['counts'].get(k)) is not int or data['counts'][k] != v: raise ValueError(f'counts.{k}: erwartet {v}')
    if 'decals' in data['counts'] and (type(data['counts']['decals']) is not int or data['counts']['decals'] != len(data.get('decals', []))):
        raise ValueError('counts.decals weicht ab')
    for key in ('dropped_faces', 'normal_fixes'):
        if key in data['counts'] and (type(data['counts'][key]) is not int or data['counts'][key] < 0):
            raise ValueError(f'counts.{key}: nichtnegative Ganzzahl erwartet')
    for name, a in data['anchors'].items():
        if not name.startswith('Socket_'): raise ValueError('Ungültiger Ankername')
        if a.get('part') is not None and a['part'] not in ids: raise ValueError(f'{name}: unbekanntes Teil')
        pos = a.get('position_m')
        if pos is not None and (len(pos) != 3 or any(not isinstance(x,(int,float)) or isinstance(x,bool) for x in pos)):
            raise ValueError(f'{name}: ungültige Position')
    for decal in data.get('decals', []):
        if decal['part'] not in ids: raise ValueError('Decal verweist auf unbekanntes Teil')
    for pid in data.get('sight', {}).get('parts', []):
        if pid not in ids: raise ValueError('Visier verweist auf unbekanntes Teil')
    for field in ('grip', 'support'):
        block = data.get(field)
        if block and block.get('part') is not None and block['part'] not in ids:
            raise ValueError(f'{field}: unbekanntes Teil')
    for part in parts:
        if part.get('parent_part') is not None and part['parent_part'] not in ids:
            raise ValueError(f'{part["id"]}: unbekanntes Elternteil')
    if 'assemblies' in data:
        assemblies = [a['id'] for a in data['assemblies']]
        if len(assemblies) != len(set(assemblies)):
            raise ValueError('Doppelte Baugruppen-IDs')
        if any(p.get('assembly') not in assemblies for p in parts):
            raise ValueError('Teil verweist auf unbekannte Baugruppe')
    for ref in _references(data):
        _local_name(ref['file'])
    return counts


def _bounds(vertices):
    return [[min(v[i] for v in vertices) for i in range(3)],
            [max(v[i] for v in vertices) for i in range(3)]]


def _local_name(value):
    if not isinstance(value, str) or not value or value in ('.', '..') or Path(value).name != value or '\\' in value:
        raise ValueError(f'Spec-Referenz muss ein lokaler Dateiname sein: {value!r}')
    return value


def _references(data):
    source = data.get('source', {})
    refs = [source.get(k) for k in ('weapon_spec', 'sight_spec', 'figure_spec')]
    refs.append(data.get('sight', {}).get('sight_spec'))
    return [r for r in refs if r is not None]


def _role(p):
    if p.get('role') or p.get('material_role'): return p.get('role', p.get('material_role'))
    if p.get('glass'): return 'glass'
    if p.get('emissive'): return 'energy'
    channel = p.get('channel', '')
    return {'MT_Primary':'shell', 'MT_Secondary':'graphite', 'MT_Accent':'accent', 'MT_Metal':'metal',
            'MT_Energy':'energy', 'MT_Emission':'energy', 'MT_Detail':'dark_metal'}.get(channel, 'shell')


def normalize(data, *, source=None):
    counts = validate(data)
    sheet = data.get('sheet', data.get('figure', data.get('info', data.get('model', {}))))
    if not isinstance(sheet,dict): sheet={'id':sheet}
    sid = sheet.get('id', data.get('id'))
    if not sid: raise ValueError('Modell-ID fehlt')
    parts = []
    for original in data['parts']:
        p=copy.deepcopy(original)
        p['assembly']=p.get('assembly', p.get('asm', 'sight' if p.get('sight') else 'body'))
        p['role']=_role(p);p['label']=p.get('label',p.get('name',p['id']))
        p['mesh'].setdefault('hard',[1]*len(p['mesh']['faces']))
        parts.append(p)
    vertices = [v for p in parts for v in p['mesh']['vertices']]
    bounds = [[min(v[i] for v in vertices) for i in range(3)], [max(v[i] for v in vertices) for i in range(3)]]
    info=dict(sheet);info.setdefault('name_de',sid);info.setdefault('kind','weapon')
    info['provenance']={'kind':'gemessen','source':'Netzkoordinaten aus geprüftem Geo-Export; keine Ableitung aus Bild'}
    doc={'info':info,'parts':parts,'assemblies':data.get('assemblies') or [{'id':a,'de':a} for a in dict.fromkeys(p['assembly'] for p in parts)],
         'anchors':copy.deepcopy(data['anchors']),'poses':copy.deepcopy(data.get('poses',{})),
         'source':source or data['source'],'warnings':[],'bounds_m':bounds,'counts':counts,
         'decals':copy.deepcopy(data.get('decals',[])),'source_geo':copy.deepcopy(data)}
    if data['format']=='cubeescape-ballon/geo':
        doc['warnings'].append('Ballon-Geo: Mindestvertrag geprüft; Produzentenfixture noch nicht verfügbar.')
    return doc


def load(path):
    path=Path(path);raw=path.read_bytes();data=json.loads(raw)
    doc=normalize(data,source={'kind':'geo','path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'producer':data.get('source')})
    # Alle Abhängigkeiten prüfen, auch das separate Visier einer Waffe.
    dependencies = {}
    for ref in _references(data):
        name = _local_name(ref['file'])
        sp = path.parent / name
        # Original v1 bundles colocate Geo and Spec; v2's documented output
        # layout separates out/geo from out/specs without embedding paths.
        if not sp.is_file() and path.parent.name == 'geo':
            sp = path.parent.parent / 'specs' / name
        if not sp.is_file(): raise ValueError(f'{name}: Geo-Spec-Abhängigkeit fehlt neben {path.name}')
        raw_spec = sp.read_bytes()
        if hashlib.sha256(raw_spec).hexdigest() != ref['sha256']:
            raise ValueError(f'{name}: Herkunfts-SHA stimmt nicht')
        dependencies[name] = json.loads(raw_spec)
    field = {'weapon':'weapon_spec', 'sight':'sight_spec', 'figure':'figure_spec'}[doc['info']['kind']]
    ref = data.get('source', {}).get(field)
    if ref: doc['source_spec'] = dependencies[ref['file']]
    doc['source_specs'] = dependencies
    return doc


def _spec_reference(path, expected=None):
    """Hash exactly the bytes delivered in out/specs, including their newline."""
    path = Path(path)
    _local_name(path.name)
    if not path.is_file(): raise ValueError(f'Geo-Spec-Abhängigkeit fehlt: {path}')
    raw = path.read_bytes()
    value = json.loads(raw)
    if expected is not None:
        from .cache import canonical
        if canonical(value) != canonical(expected):
            raise ValueError(f'{path.name}: Spec passt nicht zum ausgewerteten Dokument')
    return dict(file=path.name, format=value['format'], format_version=value['format_version'],
                sha256=hashlib.sha256(raw).hexdigest())


def _coplanar(parts):
    """Measured same-facing triangle overlap, <0.5 mm, >=1 mm², normals <=1°.

    Only native evaluated triangles enter here; imported polygon meshes retain
    their producer's checks verbatim. Sweep windows and normal bins avoid a
    quadratic scan over every face in the model.
    """
    import numpy as np
    limit, minimum, cosine = .0005, 1e-6, math.cos(math.radians(1))
    groups, looks = {}, {}
    radius = 0.
    for part in parts:
        vertices = np.asarray(part['mesh']['vertices'], dtype=float)
        looks[part['id']] = tuple(part[k] for k in ('channel', 'material', 'emissive', 'glass'))
        radius = max(radius, float(np.linalg.norm(vertices, axis=1).max()))
        for index, face in enumerate(part['mesh']['faces']):
            if len(face) != 3: raise ValueError('Native Koplanarprüfung benötigt Dreiecke')
            points = vertices[face]
            normal = np.cross(points[1]-points[0], points[2]-points[0])
            length = float(np.linalg.norm(normal))
            if length <= 1e-16: raise ValueError(f'{part["id"]}: degeneriertes Dreieck')
            normal /= length
            key = tuple(round(float(c)*100) for c in normal)
            groups.setdefault(key, []).append((part['id'], index, points, normal))
    neighbors = tuple(itertools.product((-2,-1,0,1,2), repeat=3))
    # <=1° can cross two bins at a rounding boundary (100 * sin(1°)).
    window = limit + 2*math.sin(math.radians(3))*radius
    found, seen = {}, set()

    def dot(a, b): return float(np.dot(a, b))
    def area(p):
        return sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2
    def clip(subject, boundary):
        output = list(subject)
        if area(boundary) < 0: boundary = boundary[::-1]
        for k, a in enumerate(boundary):
            b = boundary[(k+1)%len(boundary)]
            previous, output = output, []
            if not previous: break
            def side(p): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
            for j, p in enumerate(previous):
                q = previous[(j+1)%len(previous)]
                sp, sq = side(p), side(q)
                if sp >= 0: output.append(p)
                if (sp >= 0) != (sq >= 0):
                    t = sp/(sp-sq)
                    output.append((p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])))
        return abs(area(output)) if len(output) >= 3 else 0.

    for key in sorted(groups):
        normal = groups[key][0][3]
        own = {(p, f) for p, f, _, _ in groups[key]}
        rows = [row for dk in neighbors for row in groups.get(tuple(key[i]+dk[i] for i in range(3)), ())]
        rows = sorted([(dot(normal, row[2][0]), row) for row in rows], key=lambda row:row[0])
        for i, (distance, (pa, fa, a, na)) in enumerate(rows):
            for other_distance, (pb, fb, b, nb) in rows[i+1:]:
                if other_distance-distance >= window: break
                pair = tuple(sorted(((pa,fa),(pb,fb))))
                if pa == pb or pair in seen or ((pa,fa) not in own and (pb,fb) not in own): continue
                seen.add(pair)
                if dot(na,nb) < cosine: continue
                d = max(abs(dot(na,b[0]-a[0])), abs(dot(nb,b[0]-a[0])))
                if d >= limit: continue
                if np.any(a.max(axis=0)+limit < b.min(axis=0)) or np.any(b.max(axis=0)+limit < a.min(axis=0)): continue
                axis = np.array([1.,0.,0.] if abs(na[0]) < .9 else [0.,1.,0.])
                u = np.cross(na,axis);u /= np.linalg.norm(u);v = np.cross(na,u)
                a2, b2 = [(dot(p,u),dot(p,v)) for p in a], [(dot(p,u),dot(p,v)) for p in b]
                overlap = clip(a2,b2)
                if overlap < minimum: continue
                ids = tuple(sorted((pa,pb)))
                entry = found.setdefault(ids, dict(parts=list(ids),distance_m=d,overlap_m2=overlap,
                                                   normal=na.tolist(),faces=0,same_look=looks[pa]==looks[pb]))
                entry['faces'] += 1
                entry['overlap_m2'] = max(entry['overlap_m2'],overlap)
                if d < entry['distance_m']: entry.update(distance_m=d,normal=na.tolist())
    return [found[k] for k in sorted(found)]


def _native_weapon(document, specification, reference):
    import numpy as np
    info = document['info']
    origin = specification['axes']['origin_world_m']
    mapping = specification['part_id_map']
    if set(mapping) != {p['id'] for p in document['parts']} or len(set(mapping.values())) != len(mapping):
        raise ValueError('Spec part_id_map passt nicht zum Teilebestand')
    by_id = {p['source_id']:p for p in specification['parts']}
    parts = []
    dropped = 0
    for original in document['parts']:
        semantic = by_id[original['id']]
        pid = mapping[original['id']]
        vertices = [[v[i]-origin[i] for i in range(3)] for v in original['mesh']['vertices']]
        mesh = copy.deepcopy(original['mesh']);mesh['vertices'] = vertices
        kept_faces, kept_hard = [], []
        array = np.asarray(vertices,dtype=float)
        for face,hard in zip(mesh['faces'],mesh['hard']):
            if len(face) != 3: raise ValueError('Native Geo benötigt ausgewertete Dreiecke')
            a,b,c = array[face]
            if float(np.linalg.norm(np.cross(b-a,c-a))) <= 1e-16:
                dropped += 1
                continue
            kept_faces.append(face);kept_hard.append(hard)
        if not kept_faces: raise ValueError(f'{original["id"]}: ausschließlich degenerierte Flächen')
        mesh['faces'],mesh['hard'] = kept_faces,kept_hard
        label = semantic['label']
        ascii_label = re.sub('[^A-Za-z0-9]', '', unicodedata.normalize('NFKD', label).encode('ascii','ignore').decode()) or 'Part'
        move = original.get('move')
        moving = dict(kind=move.get('kind', 'author_move') if isinstance(move,dict) else str(move),
                      toolgen_node=None,author_move=copy.deepcopy(move)) if move else None
        parts.append(dict(id=pid,source_id=original['id'],name=f'SM_PG_{ascii_label}_{pid}',label=label,
                          assembly=original['assembly'],parent_part=mapping.get(original.get('parent_part')),
                          role=original['role'],channel=semantic['channel'],material=semantic['material'],
                          toolgen_material=semantic['toolgen_material'],texture=None,color=semantic['color'],
                          emissive=semantic['emissive'],glass=original['role'].startswith('glass'),sight=semantic['sight'],
                          moving=moving,bounds_m=_bounds(vertices),primitive=None,mesh=mesh))
    anchors = copy.deepcopy(specification['anchors'])
    for name in ('Socket_Reticle','Socket_Eye'):
        anchors.setdefault(name,dict(position_m=None,part=None,source='nicht definiert; keine optische Ableitung aus Netzen'))
    sight = specification['sight']
    result = dict(format=NATIVE,format_version=1,
                  generator=dict(repo='cubeescape-formgenv2',tool='formgen/geo.py',claude_version=None,version=VERSION),
                  sheet=dict(id=info['id'],kind='weapon',variant=info.get('variant'),number=str(info.get('num','')),
                             name_de=info['name_de'],toolgen_id=specification['weapon']['toolgen_id']),
                  source=dict(weapon_spec=reference,sight_spec=None,model=_model_source(document)),
                  units=dict(length='m',digits=12,model_unit_m=.001),axes=copy.deepcopy(specification['axes']),origin='Socket_Hand',
                  parts=parts,decals=[],grip=None,support=None,
                  sight=dict(present=sight['present'],kind=sight.get('kind'),type=None,sight_spec=None,
                             socket_reticle_m=anchors['Socket_Reticle']['position_m'],socket_eye_m=anchors['Socket_Eye']['position_m'],
                             eye_radius_m=None,parts=list(sight['parts']),
                             source=sight['source']),anchors=anchors,melee=None,string=None,
                  checks=dict(coplanar=_coplanar(parts),coplanar_rule='Gleichgerichtete Dreiecke ≤1°; Abstand <0.5 mm; projizierte Überdeckung ≥1 mm²'),
                  counts=_counts(parts),warnings=list(document.get('warnings', [])),
                  compatibility=dict(legacy_v1=False,reason='Native stabile Modell-ID; keine Toolgen-Produzentenabnahme'))
    result['counts']['dropped_faces'] = dropped
    if dropped:
        result['warnings'].append(f'Geo-Export: {dropped} degenerierte native Dreiecke entfernt (Fläche ≤5e−17 m²); Koordinaten unverändert.')
    result['checks']['degenerate_triangle_area_max_m2'] = 5e-17
    return result


def _counts(parts):
    return dict(parts=len(parts),vertices=sum(len(p['mesh']['vertices']) for p in parts),
                faces=sum(len(p['mesh']['faces']) for p in parts),
                triangles=sum(len(f)-2 for p in parts for f in p['mesh']['faces']),
                decals=0,dropped_faces=0,normal_fixes=0)


def _model_source(document):
    value = document.get('source', {}).get('path')
    if not value: return copy.deepcopy(document.get('source', {}))
    path = Path(value)
    if path.is_absolute():
        try: value = path.resolve().relative_to(ROOT).as_posix()
        except ValueError: raise ValueError('Modellquelle liegt außerhalb des Repos; relativen Herkunftsnachweis angeben')
    return dict(path=value,sha256=document['source'].get('sha256'))


def export(document, spec_path):
    """Export evaluated geometry; all referenced specs must already exist beside spec_path.

    Imports keep original meshes and semantics, and only rebind spec byte hashes.
    Native weapons use their own namespace; figures explicitly use figure-geo/1.
    """
    from . import spec
    from .cache import canonical
    spec_path = Path(spec_path)
    measured = _counts(document['parts'])
    for field in ('parts','vertices','faces','triangles'):
        if type(document.get('counts',{}).get(field)) is not int or document['counts'][field] != measured[field]:
            raise ValueError(f'Dokument counts.{field} weicht vom Netz ab')
    expected = document['source_spec'] if document.get('source_geo',{}).get('format') == FIGURE else spec.build(document)
    reference = _spec_reference(spec_path, expected)
    if 'source_geo' in document:
        result = copy.deepcopy(document['source_geo'])
        kind = document['info']['kind']
        main = {'weapon':'weapon_spec','sight':'sight_spec','figure':'figure_spec'}[kind]
        old = result['source'].get(main)
        if not old: raise ValueError(f'Geo-Import ohne {main}')
        old_main_name = old['file']
        for block in _references(result):
            name = _local_name(block['file'])
            if name == old_main_name:
                replacement = reference
            else:
                expected = document.get('source_specs', {}).get(name)
                if expected is None: raise ValueError(f'{name}: ungeprüfte zusätzliche Geo-Abhängigkeit')
                replacement = _spec_reference(spec_path.parent/name, expected)
            block.update(replacement)
    elif document['info']['kind'] == 'figure':
        parts = copy.deepcopy(document['parts'])
        result = dict(format=FIGURE,format_version=1,
                      generator=dict(repo='cubeescape-formgenv2',tool='formgen/geo.py',version=VERSION),
                      figure=copy.deepcopy(document['info']),source=dict(figure_spec=reference,model=_model_source(document)),
                      units=dict(length='m',model_unit_m=.001),axes=dict(forward='-Y',up='+Z',left='+X'),origin='author_origin',
                      parts=parts,assemblies=copy.deepcopy(document['assemblies']),anchors=copy.deepcopy(document['anchors']),
                      poses=copy.deepcopy(document.get('poses',{})),counts=_counts(parts),warnings=list(document.get('warnings',[])))
    elif document['info']['kind'] == 'weapon':
        result = _native_weapon(document, json.loads(spec_path.read_bytes()), reference)
    else:
        raise ValueError('Neue Visier-Geometrie benötigt einen expliziten Exportvertrag; Geo-Import verwenden')
    validate(result)
    canonical(result)
    return result
