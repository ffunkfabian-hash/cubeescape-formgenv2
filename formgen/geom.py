"""Kit meshes in metres, author axes (f,u,x) → world (x,-f,u).

Primitive dimensions/phase follow cubeescape-ballon/basic/kit.py (read-only
reference, 2026-10-26). No Blender and no v1 modelling language.
"""
from __future__ import annotations
import copy
import math
from collections import defaultdict, deque

import numpy as np
from scipy.spatial import ConvexHull, QhullError

from .model import normalize, ModelError
from .versions import GEOM as VERSION

try:
    import manifold3d as _manifold
except ImportError:
    _manifold = None


class GeometryError(ValueError):
    pass


def to_xyz(point):
    f, u, x = point
    return [x / 1000, -f / 1000, u / 1000]


def _area(points):
    a = np.asarray(points)
    return np.sum(a[:, 0] * np.roll(a[:, 1], -1) - a[:, 1] * np.roll(a[:, 0], -1)) / 2


def _triangulate(vertices, faces):
    """Ear clipping supports concave caps, retaining the input face winding."""
    v = np.asarray(vertices, dtype=float)
    triangles = []
    for face in faces:
        if len(face) == 3:
            triangles.append(list(face))
            continue
        xyz = v[face]
        normal = np.sum(np.cross(xyz, np.roll(xyz, -1, axis=0)), axis=0)
        if np.linalg.norm(normal) < 1e-14:
            raise GeometryError('Degenerierte Fläche')
        pts = np.delete(xyz, np.argmax(abs(normal)), axis=1)
        orientation = 1 if _area(pts) > 0 else -1
        remaining = list(range(len(face)))
        def cross(a, b, c):
            d, e = b - a, c - a
            return d[0] * e[1] - d[1] * e[0]
        while len(remaining) > 3:
            for at, i in enumerate(remaining):
                j, k = remaining[at - 1], remaining[(at + 1) % len(remaining)]
                if orientation * cross(pts[j], pts[i], pts[k]) <= 1e-16:
                    continue
                contained = False
                for t in remaining:
                    if t in (j, i, k):
                        continue
                    if all(orientation * cross(pts[a], pts[b], pts[t]) >= -1e-16 for a, b in ((j, i), (i, k), (k, j))):
                        contained = True
                        break
                if not contained:
                    triangles.append([face[j], face[i], face[k]])
                    remaining.pop(at)
                    break
            else:
                raise GeometryError('Profil ist degeneriert oder selbstüberschneidend')
        triangles.append([face[t] for t in remaining])
    return triangles


def _orient(vertices, faces, *, outward=True):
    """Consistent winding; orient each closed connected solid by signed volume."""
    faces = [list(f) for f in faces]
    edges = defaultdict(list)
    for i, face in enumerate(faces):
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))].append((i, a < b))
    if any(len(e) > 2 for e in edges.values()):
        raise GeometryError('Nichtmannigfaltige Kante mit mehr als zwei Flächen')
    adjacent = defaultdict(list)
    for uses in edges.values():
        if len(uses) == 2:
            (a, da), (b, db) = uses
            adjacent[a].append((b, da == db))
            adjacent[b].append((a, da == db))
    visited = {}
    verts = np.asarray(vertices)
    for seed in range(len(faces)):
        if seed in visited:
            continue
        visited[seed] = False
        q, component = deque([seed]), []
        while q:
            a = q.popleft()
            component.append(a)
            for b, flip in adjacent[a]:
                expected = visited[a] ^ flip
                if b in visited and visited[b] != expected:
                    raise GeometryError('Nicht orientierbare Oberfläche')
                if b not in visited:
                    visited[b] = expected
                    q.append(b)
        for i in component:
            if visited[i]:
                faces[i].reverse()
        if outward:
            tris = _triangulate(verts, [faces[i] for i in component])
            volume = sum(np.dot(verts[a], np.cross(verts[b], verts[c])) for a, b, c in tris)
            if volume < 0:
                for i in component:
                    faces[i].reverse()
    return verts.tolist(), faces


def _loft(rings, caps=True):
    rings = np.asarray(rings, dtype=float)
    n, count = rings.shape[1], rings.shape[0]
    faces = [[j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i] for j in range(count-1) for i in range(n)]
    if caps:
        faces += [list(range(n-1, -1, -1)), list(range((count-1)*n, count*n))]
    return _orient(rings.reshape((-1, 3)), faces, outward=caps)


def _solidify(vertices, faces, thickness):
    """Mitered inward plane offset with boundary walls, preserving outer dimensions."""
    vertices, faces = _orient(vertices, faces, outward=False)
    v = np.asarray(vertices)
    normals = [[] for _ in v]
    edges = defaultdict(list)
    for face in faces:
        xyz = v[face]
        normal = np.sum(np.cross(xyz, np.roll(xyz, -1, axis=0)), axis=0)
        normal /= np.linalg.norm(normal)
        for i in face:
            normals[i].append(normal)
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))].append((a, b))
    offsets = []
    for values in normals:
        if not values:
            raise GeometryError('surface enthält unbenutzte Vertices')
        a = np.asarray(values)
        delta = np.linalg.lstsq(a, np.full(len(a), -thickness), rcond=None)[0]
        if np.max(abs(a @ delta + thickness)) > max(thickness * .02, 1e-8):
            raise GeometryError('Innenversatz an diesem nichtplanaren Knoten nicht eindeutig; Oberfläche unterteilen')
        offsets.append(delta)
    inner = v + offsets
    for a, b in edges:
        edge = v[b] - v[a]
        if np.dot(inner[b] - inner[a], edge) <= 1e-14:
            raise GeometryError('Wandstärke kollabiert oder kehrt eine Innenkante um')
    n = len(v)
    result = faces + [[n+i for i in reversed(face)] for face in faces]
    for uses in edges.values():
        if len(uses) == 1:
            a, b = uses[0]
            result.append([b, a, n+a, n+b])
    verts = np.vstack([v, inner]).tolist()
    # Orient the entire shell without reversing an enclosed cavity separately.
    volume = _volume(verts, result)
    if volume <= 0:
        raise GeometryError('Wandstärke ist zu groß oder Oberfläche zeigt nach innen')
    return verts, result


def _volume(vertices, faces):
    v = np.asarray(vertices)
    return sum(np.dot(v[a], np.cross(v[b], v[c])) for a, b, c in _triangulate(v, faces)) / 6


def _concat(meshes):
    vertices, faces = [], []
    for v, f in meshes:
        offset = len(vertices)
        vertices.extend(v)
        faces.extend([[i+offset for i in face] for face in f])
    return vertices, faces


def _roundrect(cx, cu, w, h, r, rounded=True):
    if not rounded:
        return [(cx-w/2, cu-h/2), (cx+w/2, cu-h/2), (cx+w/2, cu+h/2), (cx-w/2, cu+h/2)]
    if r < 0 or r > min(w, h)/2:
        raise GeometryError('Rahmenradius außerhalb des Rechtecks')
    out = []
    for sx, su, start in ((1,-1,-90), (1,1,0), (-1,1,90), (-1,-1,180)):
        for j in range(5):
            a = math.radians(start+j*22.5)
            out.append((cx+sx*(w/2-r)+r*math.cos(a), cu+su*(h/2-r)+r*math.sin(a)))
    return out


def _shape(p, warnings):
    k = p['shape']
    if k == 'box':
        p = dict(p, pts=[(p['f0'],p['u0']), (p['f1'],p['u0']), (p['f1'],p['u1']), (p['f0'],p['u1'])])
        k = 'prof'
    if k == 'prof':
        return _loft([[to_xyz((f,u,p.get('x',0)+sign*p['w']/2)) for f,u in p['pts']] for sign in (-1,1)])
    if k == 'plan':
        return _loft([[to_xyz((f,u,x)) for f,x in p['pts']] for u in (p['u0'],p['u1'])])
    if k == 'cyl':
        n, r1 = p.get('segs',24), p.get('r1',p['r'])
        def ring(a,r):
            result = []
            for i in range(n):
                t = 2*math.pi*i/n+math.pi/n
                s,c = math.sin(t)*r, math.cos(t)*r
                cc = p['c']
                point = (a,cc[0]+c,cc[1]+s) if p['axis']=='f' else ((cc[0]+c,cc[1]+s,a) if p['axis']=='x' else (cc[0]+c,a,cc[1]+s))
                result.append(to_xyz(point))
            return result
        outer = [ring(p['a0'],p['r']),ring(p['a1'],r1)]
        if not p.get('r_in'):
            return _loft(outer)
        inner = [ring(p['a0'],p['r_in']),ring(p['a1'],p['r_in']*r1/p['r'])]
        return _ring_shell(outer,inner)
    if k in ('frame','xbox'):
        if k == 'xbox':
            p = dict(p, ow=p['ww'],oh=p['hh'],iw=0,ih=0,r_out=0,r_in=0)
        rounded = p['r_out'] > 0 or (p['iw'] > 0 and p['r_in'] > 0)
        if rounded and (p['r_out'] == 0 or (p['iw'] > 0 and p['r_in'] == 0)):
            # Subdivide straight edges compatibly with the rounded partner.
            raise GeometryError('Gemischt eckiger/runder Rahmen benötigt getrennte Profil-Cuts')
        def rings(w,h,r):
            pts = _roundrect(p.get('cx',0),p['cu'],w,h,r,rounded)
            return [[to_xyz((f,u,x)) for x,u in pts] for f in (p['f0'],p['f1'])]
        outer = rings(p['ow'],p['oh'],p['r_out'])
        if p['iw'] <= 0:
            return _loft(outer)
        if p['iw'] >= p['ow'] or p['ih'] >= p['oh']:
            raise GeometryError('Rahmenöffnung muss kleiner als Außenprofil sein')
        return _ring_shell(outer,rings(p['iw'],p['ih'],p['r_in']))
    if k == 'multi':
        return _concat([_shape(q,warnings) for q in p['items']])
    if k == 'hull':
        verts = np.asarray([to_xyz(pt) for pt in p['points']])
        try:
            hull = ConvexHull(verts)
        except QhullError as e:
            raise GeometryError('hull: Punkte spannen keinen Körper auf') from e
        return _orient(verts, hull.simplices.tolist())
    if k == 'loft':
        v,f = _loft([[to_xyz(pt) for pt in ring] for ring in p['rings']],p.get('caps',True))
        return _solidify(v,f,p['thickness']/1000) if p.get('thickness') else (v,f)
    if k == 'surface':
        v,f = _orient([to_xyz(pt) for pt in p['vertices']],p['faces'],outward=False)
        return _solidify(v,f,p['thickness']/1000) if p.get('thickness') else (v,f)
    if k == 'tube':
        warnings.append('tube: paralleler Ringtransport entlang der Polylinie; Blender-AUTO-Bezier wird nicht nachgebildet')
        points = np.asarray([to_xyz(pt) for pt in p['path']])
        tangents = np.empty_like(points)
        tangents[0],tangents[-1] = points[1]-points[0],points[-1]-points[-2]
        tangents[1:-1] = points[2:]-points[:-2]
        if np.any(np.linalg.norm(tangents,axis=1)<1e-12):
            raise GeometryError('tube: doppelte oder umkehrende Pfadpunkte')
        tangents /= np.linalg.norm(tangents,axis=1)[:,None]
        rings, previous = [], None
        for point,t in zip(points,tangents):
            ref = np.eye(3)[np.argmin(abs(t))] if previous is None else previous
            normal = ref-t*np.dot(t,ref)
            if np.linalg.norm(normal)<1e-9:
                normal = np.cross(t,np.eye(3)[np.argmin(abs(t))])
            normal /= np.linalg.norm(normal)
            second,previous = np.cross(t,normal),normal
            rings.append([point+p['r']/1000*(normal*math.cos(a)+second*math.sin(a)) for a in np.linspace(0,2*math.pi,p.get('segs',16),endpoint=False)])
        return _loft(rings)
    if k == 'text':
        warnings.append(f"text {p['text']!r}: sichtbare Texttafel als Ersatz, keine Blender-Schriftkontur")
        width,height = max(len(p['text']),1)*p['size']*.6,p['size']
        side,depth = p.get('side',1),p.get('depth',.15)
        origin = np.asarray(to_xyz((p['f'],p['u'],p.get('x',0))))
        align = {'LEFT':0,'CENTER':-.5,'RIGHT':-1}.get(p.get('align','LEFT'),0)*width
        a = np.array((0,side,0)) if side else np.array((0,-1,0))
        b = np.array((0,0,1)) if side else np.array((1,0,0))
        normal = np.cross(a,b)
        return _loft([[origin+(a*x+b*y+normal*z)/1000 for x,y in ((align,0),(align+width,0),(align+width,height),(align,height))] for z in (0,max(depth,.01))])
    if k == 'prism2':
        if _manifold is None:
            raise GeometryError('prism2 benötigt manifold3d für den exakten Profilschnitt')
        side,front = p['side'],p['front']
        x0,x1 = min(t[0] for t in front),max(t[0] for t in front)
        f0,f1 = min(t[0] for t in side),max(t[0] for t in side)
        a = _shape(dict(shape='prof',pts=side,w=x1-x0,x=(x0+x1)/2),warnings)
        b = _loft([[to_xyz((f,u,x)) for x,u in front] for f in (f0,f1)])
        return _from_manifold(_as_manifold(*a)^_as_manifold(*b))
    raise GeometryError(f'Unbekannte Form {k}')


def _ring_shell(outer,inner):
    n = len(outer[0])
    vertices = outer[0]+outer[1]+inner[0]+inner[1]
    faces = []
    for i in range(n):
        j = (i+1)%n
        faces += [[i,j,n+j,n+i],[2*n+i,3*n+i,3*n+j,2*n+j],[i,2*n+i,2*n+j,j],[n+i,n+j,3*n+j,3*n+i]]
    return _orient(vertices,faces)


def _as_manifold(vertices, faces):
    if _manifold is None:
        raise GeometryError('manifold3d fehlt')
    mesh = _manifold.Mesh(np.asarray(vertices,dtype=np.float32),np.asarray(_triangulate(vertices,faces),dtype=np.uint32))
    solid = _manifold.Manifold(mesh)
    if str(solid.status()) != 'Error.NoError':
        raise GeometryError(f'Boolean-Eingang nicht geschlossen/mannigfaltig: {solid.status()}')
    return solid


def _from_manifold(solid):
    if str(solid.status()) != 'Error.NoError' or solid.is_empty():
        raise GeometryError(f'Leeres/ungültiges Boolean-Ergebnis: {solid.status()}')
    mesh = solid.to_mesh()
    return np.asarray(mesh.vert_properties)[:,:3].astype(float).tolist(), np.asarray(mesh.tri_verts).astype(int).tolist()


def _bevel(vertices,faces,radius):
    """Real planar convex-edge chamfers, clipped through manifold3d.

    Radius is the edge setback, not a smoothing strength. Concave solids are
    deliberately rejected; global clipping would erase unrelated geometry.
    """
    v = np.asarray(vertices)
    hull = ConvexHull(v)
    volume = abs(_volume(v,faces))
    if abs(hull.volume-volume)>max(hull.volume*1e-5,1e-12):
        raise GeometryError('Fasen für konkave/mehrteilige Netze noch nicht implementiert')
    triangles = _triangulate(v,faces)
    edges = defaultdict(list)
    for face in triangles:
        xyz = v[face]
        normal = np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
        normal /= np.linalg.norm(normal)
        for a,b in zip(face,face[1:]+face[:1]):
            edges[tuple(sorted((a,b)))].append(normal)
    solid = _as_manifold(vertices,faces)
    used = set()
    for (a,b),normals in edges.items():
        if len(normals)!=2:
            raise GeometryError('Fase benötigt geschlossenes Netz')
        cosine = float(np.clip(np.dot(*normals),-1,1))
        if cosine >= math.cos(math.radians(30)) - 1e-8:
            continue
        normal = normals[0]+normals[1]
        normal /= np.linalg.norm(normal)
        offset = np.dot(normal,v[a])-radius*math.sqrt((1-cosine)/2)
        key = tuple(np.round(np.r_[normal,offset],10))
        if key not in used:
            solid = solid.trim_by_plane((-normal).tolist(),float(-offset))
            used.add(key)
    return _from_manifold(solid)


def _fallback_cut(vertices, cut_vertices):
    """A thin dark projected marker on the nearest model bounding plane."""
    v,c = np.asarray(vertices),np.asarray(cut_vertices)
    lo,hi = v.min(axis=0),v.max(axis=0)
    clo,chi = np.maximum(c.min(axis=0),lo),np.minimum(c.max(axis=0),hi)
    if np.any(chi < clo):
        return None
    # Choose the smallest cutter extent: a through-cut chooses the model side
    # by the axis in which the cutter exceeds both bounds.
    through = np.where((c.min(axis=0)<=lo)&(c.max(axis=0)>=hi))[0]
    axis = int(through[0]) if len(through) else int(np.argmin(chi-clo))
    others = [i for i in range(3) if i != axis]
    points = []
    for a,b in ((0,0),(1,0),(1,1),(0,1)):
        point = (clo+chi)/2
        point[axis] = hi[axis]+1e-5
        point[others[0]] = (clo,chi)[a][others[0]]
        point[others[1]] = (clo,chi)[b][others[1]]
        points.append(point.tolist())
    return {'vertices':points,'faces':[[0,1,2],[0,2,3]],'hard':[1,1],'role':'graphite','kind':'cut_fallback'}


def evaluate(model, *, booleans=True, bevels=True):
    """Return one JSON-serializable document consumed by geo/raster/spec/sheets."""
    result = normalize(model)
    warnings = result['warnings']
    all_vertices = []
    counts = {'parts':len(result['parts']),'vertices':0,'faces':0,'triangles':0}
    for part in result['parts']:
        local = []
        try:
            vertices,faces = _shape(part,local)
            for cut in part.get('cuts',[]):
                cv,cf = _shape(cut,local)
                if booleans and _manifold is not None:
                    vertices,faces = _from_manifold(_as_manifold(vertices,faces)-_as_manifold(cv,cf))
                else:
                    marker = _fallback_cut(vertices,cv)
                    if marker:
                        part.setdefault('decal_meshes',[]).append(marker)
                    local.append('Cuts nur als dunkle Decal-Flächen: Boolean-Auswertung deaktiviert oder manifold3d fehlt')
            radius = part.get('bevel',1.0)
            if radius > 0:
                if bevels and _manifold is not None:
                    try:
                        vertices,faces = _bevel(vertices,faces,radius/1000)
                        part['bevel_status'] = 'planar_chamfer'
                        local.append('Fase: echte planare Kantenfase; ballons Zweisegment-Rundung wird nicht nachgebildet')
                    except (GeometryError,QhullError) as e:
                        part['bevel_status'] = 'unsupported'
                        local.append(f'Fase nicht ausgewertet: {e}')
                else:
                    part['bevel_status'] = 'disabled'
                    local.append('Fase nicht ausgewertet: deaktiviert oder manifold3d fehlt')
            triangles = _triangulate(vertices,faces)
        except (ValueError,KeyError,IndexError,TypeError) as e:
            raise GeometryError(f"{part['id']}: {e}") from e
        # Uniform triangles prevent renderers from fan-triangulating concave faces.
        part['mesh'] = {'vertices':vertices,'faces':triangles,'hard':[0 if part['shape'] in ('cyl','tube') or part.get('smooth') else 1]*len(triangles)}
        array = np.asarray(vertices)
        part['bounds_m'] = [array.min(axis=0).tolist(),array.max(axis=0).tolist()]
        part['counts'] = {'vertices':len(vertices),'faces':len(triangles),'triangles':len(triangles)}
        counts['vertices'] += len(vertices)
        counts['faces'] += len(triangles)
        counts['triangles'] += len(triangles)
        all_vertices.extend(vertices)
        warnings.extend(f"{part['id']}: {message}" for message in dict.fromkeys(local))
    array = np.asarray(all_vertices)
    result['bounds_m'] = [array.min(axis=0).tolist(),array.max(axis=0).tolist()]
    result['counts'] = counts
    for anchor in result['anchors'].values():
        anchor['position_m'] = to_xyz(anchor['at'])
    result['geometry_version'] = VERSION
    return result
