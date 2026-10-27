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
from .curves import auto_bezier_points
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
        warnings.append('tube: AUTO-Bezier-Mittellinie nach Blender5.0.1, Auflösung12; paralleler Ringtransport statt vollständiger Blender-Tessellation')
        points = auto_bezier_points([to_xyz(pt) for pt in p['path']])
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
        from .text import text_mesh
        return text_mesh(p)
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
    # Plane trimming works in double precision internally. A float32 boundary
    # rounds distinct bevel vertices onto each other, creating zero-area faces
    # even though the manifold itself is valid. Preserve precision both ways.
    mesh = _manifold.Mesh64(np.asarray(vertices,dtype=np.float64),np.asarray(_triangulate(vertices,faces),dtype=np.uint64))
    solid = _manifold.Manifold(mesh)
    if str(solid.status()) != 'Error.NoError':
        raise GeometryError(f'Boolean-Eingang nicht geschlossen/mannigfaltig: {solid.status()}')
    return solid


def _from_manifold(solid):
    if str(solid.status()) != 'Error.NoError' or solid.is_empty():
        raise GeometryError(f'Leeres/ungültiges Boolean-Ergebnis: {solid.status()}')
    mesh = solid.to_mesh64()
    return np.asarray(mesh.vert_properties)[:,:3].astype(float).tolist(), np.asarray(mesh.tri_verts).astype(int).tolist()


def _mesh_components(vertices, faces):
    """Split joined kit primitives without a convex hull across their gap."""
    by_vertex = defaultdict(list)
    for i, face in enumerate(faces):
        for vertex in face:
            by_vertex[vertex].append(i)
    visited = set()
    for seed in range(len(faces)):
        if seed in visited:
            continue
        visited.add(seed)
        queue, selected = [seed], []
        while queue:
            i = queue.pop()
            selected.append(faces[i])
            for vertex in faces[i]:
                for neighbor in by_vertex[vertex]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
        ids = sorted({i for face in selected for i in face})
        remap = {old: new for new, old in enumerate(ids)}
        yield [vertices[i] for i in ids], [[remap[i] for i in face] for face in selected]


def _convex_bevel(vertices, faces, radius, segments):
    """Convex edge offset with a sampled circular profile and local clamp.

    ``radius`` follows kit/Blender's offset width: distance along either face
    from the original edge. At one segment this is a planar chamfer. Multiple
    segments use supporting planes of the circular edge profile. Their vertex
    intersections are deterministic, but do not claim Blender's corner miters.
    """
    v = np.asarray(vertices)
    hull = ConvexHull(v)
    volume = abs(_volume(v,faces))
    if abs(hull.volume-volume)>max(hull.volume*1e-5,1e-12):
        raise GeometryError('Fasen für konkave Netzkomponenten noch nicht implementiert')
    triangles = _triangulate(v,faces)
    edges = defaultdict(list)
    for face in triangles:
        xyz = v[face]
        normal = np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
        normal /= np.linalg.norm(normal)
        for a,b in zip(face,face[1:]+face[:1]):
            edges[tuple(sorted((a,b)))].append(normal)
    features = []
    incident_lengths = defaultdict(list)
    for (a,b),normals in edges.items():
        if len(normals)!=2:
            raise GeometryError('Fase benötigt geschlossenes Netz')
        cosine = float(np.clip(np.dot(*normals),-1,1))
        if cosine >= math.cos(math.radians(30)) - 1e-8:
            continue
        length = float(np.linalg.norm(v[b]-v[a]))
        incident_lengths[a].append(length)
        incident_lengths[b].append(length)
        features.append((a, b, normals, math.acos(cosine)))
    solid = _as_manifold(vertices,faces)
    used = set()
    for a, b, normals, angle in features:
        # Conservative endpoint clamp prevents opposite bevel strips from
        # consuming thin faces. Only feature edges count, not cap diagonals.
        setback = min(radius, .49*min(incident_lengths[a]+incident_lengths[b]))
        bisector = (normals[0]+normals[1])/(2*math.cos(angle/2))
        center = v[a]-bisector*(setback/math.sin(angle/2))
        rolling_radius = setback/math.tan(angle/2)
        for i in range(segments):
            t = (i+.5)/segments
            normal = (math.sin((1-t)*angle)*normals[0]
                      +math.sin(t*angle)*normals[1])/math.sin(angle)
            offset = np.dot(normal,center)+rolling_radius*math.cos(angle/(2*segments))
            key = tuple(np.round(np.r_[normal,offset],12))
            if key not in used:
                solid = solid.trim_by_plane((-normal).tolist(),float(-offset))
                used.add(key)
    return _from_manifold(solid)


def _constant_ring(part):
    if not part or part.get('cuts'):
        return False
    if part.get('shape') == 'cyl':
        return bool(part.get('r_in')) and math.isclose(part.get('r1', part['r']), part['r'], rel_tol=0, abs_tol=1e-12)
    return part.get('shape') == 'frame' and part.get('iw', 0) > 0 and part.get('ih', 0) > 0


def _convex_profile(points):
    """CCW convex profile's outward normals, supports and offset directions."""
    edge = np.roll(points, -1, axis=0)-points
    lengths = np.linalg.norm(edge, axis=1)
    if np.any(lengths < 1e-12):
        raise GeometryError('Endringfase: doppelte Profilpunkte')
    tangent = edge/lengths[:, None]
    previous = np.roll(tangent, 1, axis=0)
    turn = previous[:, 0]*tangent[:, 1]-previous[:, 1]*tangent[:, 0]
    cosine = np.clip(np.sum(previous*tangent, axis=1), -1, 1)
    if np.any(turn < -1e-10) or np.any(cosine < math.cos(math.radians(30))-1e-10):
        raise GeometryError('Endringfase: konkaves Profil oder Längskante über 30 Grad')
    normal = np.column_stack([tangent[:, 1], -tangent[:, 0]])
    prior = np.roll(normal, 1, axis=0)
    displacement = (prior+normal)/(1+cosine[:, None])
    support = np.sum(normal*points, axis=1)
    if np.any(points@normal.T > support[None, :]+1e-10):
        raise GeometryError('Endringfase: Profil nicht konvex')
    return normal, support, displacement


def _ring_bevel(vertices, faces, radius, segments=2):
    """Bevel only end rims of an untouched _ring_shell mesh.

    Source layout: outer start/end, inner start/end, equal point counts. A
    positive offset shrinks the outer profile and enlarges the inner profile.
    All allowed radii preserve convex offsets and strictly positive cap walls.
    """
    if not isinstance(segments, int) or isinstance(segments, bool) or segments < 1:
        raise GeometryError('segs_bevel muss eine positive ganze Zahl sein')
    if not np.isfinite(radius) or radius <= 0:
        raise GeometryError('Endringfase benötigt positive endliche Breite')
    v = np.asarray(vertices, dtype=float)
    if v.ndim != 2 or v.shape[1] != 3 or len(v) < 12 or len(v) % 4:
        raise GeometryError('Endringfase benötigt vier gleichlange Profilringe')
    n = len(v)//4
    outer0, outer1, inner0, inner1 = v.reshape((4, n, 3))
    delta = outer1[0]-outer0[0]
    length = float(np.linalg.norm(delta))
    if length < 1e-12:
        raise GeometryError('Endringfase benötigt positive Extrusionslänge')
    axis = delta/length
    if not np.allclose(outer1-outer0, delta, atol=1e-12, rtol=0) or not np.allclose(inner1-inner0, delta, atol=1e-12, rtol=0):
        raise GeometryError('Endringfase unterstützt keine Taperprofile')
    origin = outer0[0]
    if np.max(np.abs((np.vstack([outer0, inner0])-origin)@axis)) > 1e-12:
        raise GeometryError('Endringfase benötigt planare Endprofile')
    first = outer0[1]-outer0[0]
    first /= np.linalg.norm(first)
    basis = np.stack([first, np.cross(axis, first)])
    outer = (outer0-origin)@basis.T
    inner = (inner0-origin)@basis.T
    area = np.sum(outer[:, 0]*np.roll(outer[:, 1], -1)-outer[:, 1]*np.roll(outer[:, 0], -1))
    if area < 0:
        outer, inner = outer[::-1].copy(), inner[::-1].copy()
    normals, supports, outer_offset = _convex_profile(outer)
    _, _, inner_offset = _convex_profile(inner)
    # Every enlarged inner vertex must stay inside every shrunken outer edge.
    # These linear inequalities provide the actual wall-clamp limit; unlike
    # an edge-length clamp, harmless short rim segments do not reduce width.
    gaps = supports[None, :]-inner@normals.T
    slopes = 1+inner_offset@normals.T
    if np.any(gaps <= 1e-12):
        raise GeometryError('Endringfase benötigt strikt getrennte Innen-/Außenprofile')
    limits = gaps[slopes > 1e-12]/slopes[slopes > 1e-12]
    setback = min(float(radius), .49*length, .98*float(limits.min()))
    if setback < 1e-12:
        raise GeometryError('Endringfase: kein positiver Clampbereich')
    # Convex outer profile must retain its original edge topology at the cap.
    cap_outer = outer-setback*outer_offset
    edge = np.roll(cap_outer, -1, axis=0)-cap_outer
    original_edge = np.roll(outer, -1, axis=0)-outer
    if np.any(np.sum(edge*original_edge, axis=1) <= 1e-20):
        raise GeometryError('Endringfase: Außenoffset kollabiert vor Wandclamp')
    if np.any(cap_outer@normals.T > supports[None, :]-setback+1e-10):
        raise GeometryError('Endringfase: Außenoffset nicht konvex')
    theta = np.linspace(0, math.pi/2, segments+1)
    distances = setback*(1-np.cos(theta))
    offsets = setback*(1-np.sin(theta))
    # Keep endpoint coordinates exact and avoid tiny positive floating offsets.
    distances[0], distances[-1] = 0., setback
    offsets[0], offsets[-1] = setback, 0.
    stations = list(zip(distances, offsets))+list(zip(length-distances[::-1], offsets[::-1]))
    out_rings, in_rings = [], []
    for station, offset in stations:
        out_rings.append(origin+(outer-offset*outer_offset)@basis+station*axis)
        in_rings.append(origin+(inner+offset*inner_offset)@basis+station*axis)
    count = len(stations)
    points = np.concatenate(out_rings+in_rings)
    result = []
    def idx(inner_ring, ring, point):
        return (int(inner_ring)*count+ring)*n+point
    for ring in range(count-1):
        for j in range(n):
            k = (j+1) % n
            for inside in (False, True):
                result.append([idx(inside, ring, j), idx(inside, ring, k), idx(inside, ring+1, k), idx(inside, ring+1, j)])
    for ring in (0, count-1):
        for j in range(n):
            k = (j+1) % n
            result.append([idx(False, ring, j), idx(False, ring, k), idx(True, ring, k), idx(True, ring, j)])
    return _orient(points, result)



def _concave_extrusion(part):
    """Only untouched prof/plan meshes have the two-ring topology below."""
    if not part or part.get('cuts') or part.get('shape') not in ('prof', 'plan'):
        return False
    p = np.asarray(part['pts'], dtype=float)
    edge = np.roll(p, -1, axis=0)-p
    following = np.roll(edge, -1, axis=0)
    turn = edge[:, 0]*following[:, 1]-edge[:, 1]*following[:, 0]
    return bool(np.any(turn*_area(p) < -1e-12))


def _simple_profile(points):
    """Reject crossed/overlapping non-neighbouring edges before making a mesh."""
    p = np.asarray(points)
    n = len(p)
    def cross(a, b):
        return float(a[0]*b[1]-a[1]*b[0])
    for i in range(n):
        a, b = p[i], p[(i+1) % n]
        for j in range(i+2, n):
            if i == 0 and j == n-1:
                continue
            c, d = p[j], p[(j+1) % n]
            if np.any(np.maximum(a, b) < np.minimum(c, d)-1e-13) or np.any(np.maximum(c, d) < np.minimum(a, b)-1e-13):
                continue
            r, s = b-a, d-c
            denominator = cross(r, s)
            if abs(denominator) <= 1e-20:
                if abs(cross(c-a, r)) < 1e-20:
                    return False
                continue
            t, u = cross(c-a, s)/denominator, cross(c-a, r)/denominator
            if -1e-10 <= t <= 1+1e-10 and -1e-10 <= u <= 1+1e-10:
                return False
    return n >= 3 and _area(p) > 1e-16


def _sharp_ring_edges(vertices):
    v = np.asarray(vertices, dtype=float)
    outer = v[:len(v)//4]
    edge = np.roll(outer, -1, axis=0)-outer
    tangent = edge/np.linalg.norm(edge, axis=1)[:, None]
    return bool(np.any(np.sum(tangent*np.roll(tangent, 1, axis=0), axis=1)
                       < math.cos(math.radians(30))-1e-10))


def _extrusion_bevel(vertices, faces, radius, segments=2, *, inner=None):
    """Analytic concave-profile fillets and rounded cap rims.

    Longitudinal edges above kit's 30-degree angle limit use the requested
    offset width, on convex AND re-entrant corners. Cap rims follow inward
    offsets of that profile, sampled on a quarter circle. A shrinking convex
    arc collapses to a single topological vertex, rather than leaving duplicate
    vertices/zero-area triangles. This is a documented offset-surface corner
    construction, not a claim of Blender's corner-miter topology or clamp.
    """
    if not np.isfinite(radius) or radius <= 0:
        raise GeometryError('Profilfase benötigt positive endliche Breite')
    v = np.asarray(vertices, dtype=float)
    if len(v) % 2 or len(v) < 6:
        raise GeometryError('Profilfase benötigt zwei gleichlange Profilringe')
    n = len(v)//2
    delta = v[n]-v[0]
    length = float(np.linalg.norm(delta))
    if length <= 1e-12 or not np.allclose(v[n:]-v[:n], delta, atol=1e-12, rtol=0):
        raise GeometryError('Profilfase benötigt eine konstante Extrusion')
    axis = delta/length
    origin = v[0]
    if np.max(np.abs((v[:n]-origin)@axis)) > 1e-12:
        raise GeometryError('Profilfase benötigt planare Endprofile')
    first = v[1]-v[0]
    first /= np.linalg.norm(first)
    basis = np.stack([first, np.cross(axis, first)])
    profile = (v[:n]-origin)@basis.T
    if _area(profile) < 0:
        profile = profile[::-1].copy()
    profiles = [profile]
    if inner is not None:
        inner = np.asarray(inner, dtype=float)
        if inner.shape != v.shape or not np.allclose(inner[n:]-inner[:n], delta, atol=1e-12, rtol=0):
            raise GeometryError('Profilfase benötigt eine konstante innere Extrusion')
        if np.max(np.abs((inner[:n]-origin)@axis)) > 1e-12:
            raise GeometryError('Profilfase benötigt koplanare Innen-/Außenprofile')
        hole = (inner[:n]-origin)@basis.T
        if _area(hole) > 0:
            hole = hole[::-1].copy()
        profiles.append(hole)
    if any(not _simple_profile(p if i == 0 else p[::-1]) for i, p in enumerate(profiles)):
        raise GeometryError('Profilfase benötigt einfache Profilkonturen')
    profile = np.concatenate(profiles)
    edge = np.concatenate([np.roll(p, -1, axis=0)-p for p in profiles])
    lengths = np.linalg.norm(edge, axis=1)
    if np.any(lengths <= 1e-12):
        raise GeometryError('Profilfase: doppelte Profilpunkte')
    tangent = edge/lengths[:, None]
    normal = np.column_stack([tangent[:, 1], -tangent[:, 0]])
    prior = np.concatenate([np.roll(p, 1, axis=0) for p in np.split(normal, len(profiles))])
    cosine = np.clip(np.sum(prior*normal, axis=1), -1, 1)
    turn = prior[:, 0]*normal[:, 1]-prior[:, 1]*normal[:, 0]
    angles = np.arctan2(turn, cosine)
    if np.any(cosine <= -1+1e-10):
        raise GeometryError('Profilfase: umkehrendes Profil')
    miter = (prior+normal)/(1+cosine[:, None])
    selected = np.abs(angles) > math.radians(30)+1e-10
    setback = min(float(radius), .49*length, .49*float(lengths.min()))

    def ring(offset, signed_radii):
        points = []
        for i in range(len(profile)):
            sharp = profile[i]-offset*miter[i]
            effective = signed_radii[i]-offset
            if not selected[i] or (signed_radii[i] > 0 and effective <= 1e-13):
                points.extend([sharp]*(segments+1))
                continue
            center = profile[i]-signed_radii[i]*miter[i]
            start = math.atan2(prior[i, 1], prior[i, 0])
            for t in np.linspace(0, 1, segments+1):
                angle = start+t*angles[i]
                points.append(center+effective*np.array([math.cos(angle), math.sin(angle)]))
        return np.asarray(points)

    def unique(p):
        # Arc collapse is part of the construction. Consecutive sample slots
        # share one vertex when the exact offset radius reaches zero.
        out, ids = [], []
        for point in p:
            if out and np.linalg.norm(point-out[-1]) <= 1e-13:
                ids.append(len(out)-1)
            else:
                ids.append(len(out)); out.append(point)
        if len(out) > 1 and np.linalg.norm(out[0]-out[-1]) <= 1e-13:
            last = len(out)-1
            ids = [0 if i == last else i for i in ids]
            out.pop()
        return np.asarray(out), ids

    # Nonlocal narrow features can collide before any individual short edge.
    # A conservative common clamp retains every contour/corner; no polygon
    # union, hull, trimming, or discarded invalid faces conceal such collisions.
    for _ in range(24):
        signed_radii = np.zeros(len(profile))
        signed_radii[selected] = setback/np.tan(angles[selected]/2)
        theta = list(np.linspace(0, math.pi/2, segments+1))
        for r in signed_radii[selected]:
            if 1e-13 < r < setback-1e-13:
                theta.append(math.asin(1-r/setback))
        theta = sorted(set(theta))
        stations = [(setback*(1-math.cos(t)), setback*(1-math.sin(t))) for t in theta]
        stations[0] = (0., setback)
        stations[-1] = (setback, 0.)
        stations += [(length-z, d) for z, d in stations[::-1]]
        rings = [[unique(p) for p in np.split(ring(d, signed_radii), len(profiles))] for _, d in stations]
        if all(_simple_profile(p if i == 0 else p[::-1]) for r in rings for i, (p, _) in enumerate(r)):
            # Every inward offset must remain inside the middle section. The
            # CrossSection difference is validation only, never replacement.
            # CrossSection uses a fixed coordinate grid. Validate in micrometres
            # so that its area rounding cannot spuriously shrink a mm bevel.
            scale = 1e6
            sections = [_manifold.CrossSection([p*scale for p, _ in r]) for r in rings]
            middle = sections[len(theta)-1]
            if all(abs(s.area()/scale**2-sum(_area(p) for p, _ in r)) < 1e-14
                   and (s-middle).area()/scale**2 < 1e-14 for s, r in zip(sections, rings)):
                break
        setback *= .5
    else:
        raise GeometryError('Profilfase: kein kollisionsfreier Offsetbereich')
    points, maps, boundaries = [], [], []
    for (station, _), r in zip(stations, rings):
        section_maps, section_boundaries = [], []
        for p, ids in r:
            start = len(points)
            points.extend(origin+p@basis+station*axis)
            section_maps.append([start+i for i in ids])
            section_boundaries.extend(range(start, start+len(p)))
        maps.append(section_maps)
        boundaries.append(section_boundaries)
    result = []
    count = n*(segments+1)
    for before, after in zip(maps, maps[1:]):
        for left, right in zip(before, after):
            for j in range(count):
                k = (j+1) % count
                face = [left[j], left[k], right[k], right[j]]
                face = [a for i, a in enumerate(face) if a != face[i-1]]
                if len(face) >= 3:
                    result.append(face)
    for i in (0, -1):
        cap = _manifold.triangulate([p for p, _ in rings[i]])
        result.extend([[boundaries[i][j] for j in tri] for tri in cap])
    return _orient(points, result)


def _bevel(vertices, faces, radius, segments=2, *, part=None):
    if not isinstance(segments, int) or isinstance(segments, bool) or segments < 1:
        raise GeometryError('segs_bevel muss eine positive ganze Zahl sein')
    if _constant_ring(part):
        if _sharp_ring_edges(vertices):
            v = np.asarray(vertices)
            return _extrusion_bevel(v[:len(v)//2], faces, radius, segments, inner=v[len(v)//2:])
        return _ring_bevel(vertices, faces, radius, segments)
    if _concave_extrusion(part):
        return _extrusion_bevel(vertices, faces, radius, segments)
    return _concat([_convex_bevel(v, f, radius, segments)
                    for v, f in _mesh_components(vertices, faces)])


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
                        segments = part.get('segs_bevel', 2)
                        ring_profile = _constant_ring(part) and _sharp_ring_edges(vertices)
                        vertices,faces = _bevel(vertices,faces,radius/1000,segments,part=part)
                        part['bevel_status'] = 'segmented_bevel' if segments > 1 else 'planar_chamfer'
                        if ring_profile:
                            part['bevel_status'] = 'segmented_ring_profile_bevel' if segments > 1 else 'planar_ring_profile_chamfer'
                            local.append(f'Fase: {segments} Kreisprofilsegment(e), äußere/innere Profilkanten und Endränder; konservativer Profilclamp, Offset-Ecken statt bestätigter Blender-Eckmiterparität')
                        elif _constant_ring(part):
                            local.append(f'Fase: {segments} Kreisprofilsegment(e), nur Endringkanten; Wand-/Längenclamp, Längskanten unverändert, keine Blender-Eckmiterparität')
                        elif _concave_extrusion(part):
                            part['bevel_status'] = 'segmented_profile_bevel' if segments > 1 else 'planar_profile_chamfer'
                            local.append(f'Fase: {segments} Kreisprofilsegment(e), konvexe/konkave Profilkanten und Endränder; konservativer Profilclamp, Offset-Ecken statt bestätigter Blender-Eckmiterparität')
                        else:
                            local.append(f'Fase: {segments} Kreisprofilsegment(e), komponentenweise konvex; konservativer Kantenclamp, keine Blender-Eckmiterparität')
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
