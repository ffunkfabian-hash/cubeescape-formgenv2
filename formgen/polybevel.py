"""Direct conservative post-Cut polyhedral bevels in double precision.

No convex replacement hull, primitive/Cut reorder or null-face cleanup.
"""
import math
from collections import defaultdict, Counter

import numpy as np
from scipy.spatial import Delaunay, QhullError

from . import geom


def _solve(matrix, values):
    try:
        return np.linalg.solve(matrix, values)
    except np.linalg.LinAlgError as exc:
        raise geom.GeometryError('Polyhedral corner planes are singular') from exc


def _cross(a, b, c):
    u, v = (b - a, c - a)
    return float(u[0] * v[1] - u[1] * v[0])

def _cap_triangulate(contours):
    """Recover constrained Delaunay edges, then select the positive region.

    Manifold's general cap triangulator may emit zero-area triangles across
    collinear holes. Here no degenerate triangles are ever constructed or
    deleted. Boundary edges, signed area and positive triangles are mandatory.
    """
    pts = np.concatenate(contours)
    try:
        tri = Delaunay(pts).simplices.tolist()
    except QhullError as exc:
        raise geom.GeometryError('Polyhedral cap cannot be triangulated: '+str(exc)) from exc
    for t in tri:
        if _cross(*pts[t]) < 0:
            t.reverse()
    constraints = []
    base = 0
    for contour in contours:
        constraints += [tuple(sorted((base + j, base + (j + 1) % len(contour)))) for j in range(len(contour))]
        base += len(contour)
    fixed = set()

    def edges():
        out = defaultdict(list)
        for ti, t in enumerate(tri):
            for a, b in zip(t, t[1:] + t[:1]):
                out[tuple(sorted((a, b)))].append(ti)
        return out

    def crosses(a, b, c, d):
        if len({a, b, c, d}) < 4:
            return False
        p, q, r, s = pts[[a, b, c, d]]
        return _cross(p, q, r) * _cross(p, q, s) < -1e-30 and _cross(r, s, p) * _cross(r, s, q) < -1e-30
    for constraint in constraints:
        a, b = constraint
        for iteration in range(len(tri) * len(tri)):
            ee = edges()
            if constraint in ee:
                fixed.add(constraint)
                break
            changed = False
            for (c, d), uses in ee.items():
                if len(uses) != 2 or (c, d) in fixed or (not crosses(a, b, c, d)):
                    continue
                i, j = uses
                p = next((k for k in tri[i] if k not in (c, d)))
                q = next((k for k in tri[j] if k not in (c, d)))
                if not crosses(c, d, p, q):
                    continue
                if any((crosses(p, q, x, y) for x, y in fixed)):
                    continue
                new = [[p, q, c], [q, p, d]]
                for t in new:
                    if _cross(*pts[t]) < 0:
                        t.reverse()
                tri[i], tri[j] = new
                changed = True
                break
            if not changed:
                raise geom.GeometryError('cap constraint cannot be recovered')
        else:
            raise geom.GeometryError('cap constraint recovery iteration limit')

    def winding(p):
        value = 0
        for contour in contours:
            for a, b in zip(contour, np.roll(contour, -1, axis=0)):
                if a[1] <= p[1] < b[1] and _cross(a, b, p) > 0:
                    value += 1
                elif b[1] <= p[1] < a[1] and _cross(a, b, p) < 0:
                    value -= 1
        return value
    result = [t for t in tri if winding(pts[t].mean(axis=0)) > 0]
    area = sum((_cross(*pts[t]) / 2 for t in result))
    expected = sum((geom._area(p) for p in contours))
    if abs(area - expected) > max(1e-14, abs(expected) * 1e-10):
        raise geom.GeometryError('cap area mismatch')
    uses = defaultdict(int)
    for t in result:
        for a, b in zip(t, t[1:] + t[:1]):
            uses[tuple(sorted((a, b)))] += 1
    if {e for e, n in uses.items() if n == 1} != set(constraints):
        raise geom.GeometryError('cap topology mismatch')
    if not result or min((_cross(*pts[t]) for t in result)) < 1e-14:
        raise geom.GeometryError('cap has near-zero triangle')
    return result

def _self_intersects(v, t):
    """Reject actual triangle crossings and coplanar overlaps.

    Shared topological vertices/edges are allowed. AABB overlap is only a broad
    phase: noncoplanar pairs get segment/triangle tests; coplanar pairs get an
    area intersection in their common plane. This gate is mandatory for every
    accepted segment count and does not depend on a part ID.
    """
    tri = v[t]
    low = tri.min(axis=1)
    high = tri.max(axis=1)
    norm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norm /= np.linalg.norm(norm, axis=1)[:, None]
    for i in range(len(t)):
        candidates = np.flatnonzero(np.all(high[i] + 1e-11 >= low[i + 1:], axis=1) & np.all(high[i + 1:] + 1e-11 >= low[i], axis=1)) + i + 1
        for j in candidates:
            shared = set(t[i]) & set(t[j])
            coplanar = abs(norm[i] @ norm[j]) > 1 - 1e-10 and max(abs((tri[j] - tri[i, 0]) @ norm[i])) < 1e-11
            if coplanar:
                drop = np.argmax(abs(norm[i]))
                aa = np.delete(tri[i], drop, axis=1) * 1000
                bb = np.delete(tri[j], drop, axis=1) * 1000
                if geom._area(aa) < 0:
                    aa = aa[::-1]
                if geom._area(bb) < 0:
                    bb = bb[::-1]
                overlap = (geom._manifold.CrossSection([aa]) ^ geom._manifold.CrossSection([bb])).area()
                if overlap > 1e-08:
                    return True
                continue
            if len(shared) >= 2:
                continue
            for k, l in [(i, j), (j, i)]:
                a, b, c = tri[l]
                e1, e2 = (b - a, c - a)
                for origin, end in zip(tri[k], np.roll(tri[k], -1, axis=0)):
                    direction = end - origin
                    h = np.cross(direction, e2)
                    det = e1 @ h
                    if abs(det) < 1e-18:
                        continue
                    inv = 1 / det
                    s = origin - a
                    u = s @ h * inv
                    q = np.cross(s, e1)
                    w = direction @ q * inv
                    d = e2 @ q * inv
                    if not (-1e-09 <= u <= 1 + 1e-09 and -1e-09 <= w and (u + w <= 1 + 1e-09) and (-1e-09 <= d <= 1 + 1e-09)):
                        continue
                    p = origin + d * direction
                    if shared and min((np.linalg.norm(p - v[a]) for a in shared)) < 1e-09:
                        continue
                    return True
    return False

def planar_brep(vertices, faces):
    """Recover coplanar source faces and exact boundary loops.

    Only collinear subdivisions incident to the same two planes collapse.
    No source face, hole, dimension or noncollinear feature is removed.
    """
    v = np.asarray(vertices, float)
    t = np.asarray(geom._triangulate(v, faces), int)
    n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    lens = np.linalg.norm(n, axis=1)
    if np.any(lens < 1e-14):
        raise geom.GeometryError('degenerate source triangle')
    n /= lens[:, None]
    h = np.einsum('ij,ij->i', n, v[t[:, 0]])
    edges = defaultdict(list)
    for i, f in enumerate(t):
        for a, b in zip(f, np.roll(f, -1)):
            edges[tuple(sorted((a, b)))].append(i)
    if any((len(v) != 2 for v in edges.values())):
        raise geom.GeometryError('open input')
    root = list(range(len(t)))

    def find(a):
        while root[a] != a:
            root[a] = root[root[a]]
            a = root[a]
        return a
    for uses in edges.values():
        a, b = uses
        if np.linalg.norm(n[a] - n[b]) < 1e-10 and abs(h[a] - h[b]) < 1e-11:
            root[find(b)] = find(a)
    groups = defaultdict(list)
    for i in range(len(t)):
        groups[find(i)].append(i)
    bounds = []
    nv = []
    incident = defaultdict(set)
    for g, items in enumerate(groups.values()):
        uses = Counter(((a, b) for f in t[items] for a, b in zip(f, np.roll(f, -1))))
        boundary = [(a, b) for a, b in uses if (b, a) not in uses]
        nxt = {a: b for a, b in boundary}
        if len(nxt) != len(boundary):
            raise geom.GeometryError('branched face boundary')
        unseen = set(nxt)
        loops = []
        while unseen:
            a = next(iter(unseen))
            loop = []
            cur = a
            while cur in unseen:
                unseen.remove(cur)
                loop.append(cur)
                incident[cur].add(g)
                cur = nxt[cur]
            if cur != a:
                raise geom.GeometryError('open face boundary')
            loops.append(loop)
        bounds.append(loops)
        nv.append(n[items[0]])
    removed = set()
    for loops in bounds:
        for loop in loops:
            for j, a in enumerate(loop):
                if len(incident[a]) != 2:
                    continue
                pa, pb = (v[loop[j - 1]] - v[a], v[loop[(j + 1) % len(loop)]] - v[a])
                if np.dot(pa, pb) < 0 and np.linalg.norm(np.cross(pa, pb)) < 1e-12 * np.linalg.norm(pa) * np.linalg.norm(pb):
                    removed.add(a)
    bounds = [[[a for a in loop if a not in removed] for loop in loops] for loops in bounds]
    fedges = defaultdict(list)
    for g, loops in enumerate(bounds):
        for loop in loops:
            for a, b in zip(loop, loop[1:] + loop[:1]):
                fedges[tuple(sorted((a, b)))].append((g, a, b))
    if any((len(uses) != 2 for uses in fedges.values())):
        raise geom.GeometryError('unmatched simplified boundary')
    return (v, bounds, np.array(nv), fedges)

def distance_segments(p0, p1, q0, q1):
    u, v, w = (p1 - p0, q1 - q0, p0 - q0)
    a = u @ u
    b = u @ v
    c = v @ v
    d = u @ w
    e = v @ w
    D = a * c - b * b
    sN, sD = (D, D)
    tN, tD = (D, D)
    if D < 1e-24:
        sN, sD = (0.0, 1.0)
        tN, tD = (e, c)
    else:
        sN = b * e - c * d
        tN = a * e - b * d
        if sN < 0:
            sN = 0.0
            tN = e
            tD = c
        elif sN > sD:
            sN = sD
            tN = e + b
            tD = c
    if tN < 0:
        tN = 0.0
        if -d < 0:
            sN = 0.0
        elif -d > a:
            sN = sD
        else:
            sN = -d
            sD = a
    elif tN > tD:
        tN = tD
        if -d + b < 0:
            sN = 0.0
        elif -d + b > a:
            sN = sD
        else:
            sN = -d + b
            sD = a
    sc = 0.0 if abs(sN) < 1e-30 else sN / sD
    tc = 0.0 if abs(tN) < 1e-30 else tN / tD
    return float(np.linalg.norm(w + sc * u - tc * v))

def bevel(vertices, faces, width, segments=2):
    """Build inset faces, circular edge strips and triangulated corner patches.

    Width means setback along each incident source face. A common conservative
    clamp uses the minimum of 24% local source boundary lengths and nonincident
    coplanar boundary spacing over all selected edges; further local downward
    constraints keep shallow edges shared. This conservative margin
    avoids the known mouth/outer-rim overlap without modifying source geometry.

    At three-plane shallow junctions both fillet cylinders are intersected
    analytically, using their common face support as parameter. Other corner
    cycles are triangulated as nonplanar offset miters. These are our own
    corner patches, not Blender miter/clamp parity. A failed triangulation or
    any self-intersection raises GeometryError instead of returning a mesh.
    """
    if not isinstance(segments, int) or isinstance(segments, bool) or segments < 1:
        raise geom.GeometryError('Positive integral segment count required')
    if not math.isfinite(width) or width <= 1e-12:
        raise geom.GeometryError('Positive numerically stable bevel width required')
    if len(list(geom._mesh_components(vertices, faces))) != 1:
        raise geom.GeometryError('Polyhedral bevel needs one connected source boundary; enclosed voids unsupported')
    source = geom._as_manifold(vertices, faces)
    if source.volume() <= 0:
        raise geom.GeometryError('Polyhedral bevel source must have positive oriented volume')
    v, loops, n, edges = planar_brep(vertices, faces)
    widths = {}
    edgeinfo = {}
    byface = defaultdict(list)
    inc = defaultdict(list)
    for key, uses in edges.items():
        a, b = key
        (f, _, _), (g, _, _) = uses
        e = v[b] - v[a]
        L = np.linalg.norm(e)
        e /= L
        angle = math.acos(float(np.clip(n[f] @ n[g], -1, 1)))
        if angle >= math.pi - 1e-08:
            raise geom.GeometryError('folded antiparallel edge')
        _, u, w = uses[0]
        tangent = (v[w] - v[u]) / L
        inward = np.cross(n[f], tangent)
        sign = 1.0 if inward @ n[g] < 0 else -1.0
        widths[key] = width if angle > math.pi / 6 + 1e-08 else 0.0
        edgeinfo[key] = (f, g, e, L, angle, sign)
        for g in (f, g):
            byface[g].append(key)
        inc[a].append(key)
        inc[b].append(key)
    for key, (f, g, e, L, angle, sign) in edgeinfo.items():
        if not widths[key]:
            continue
        a, b = key
        limit = min((np.linalg.norm(v[y] - v[x]) for k in inc[a] + inc[b] for x, y in [k]))
        for face in [f, g]:
            for other in byface[face]:
                if set(key) & set(other):
                    continue
                x, y = other
                limit = min(limit, distance_segments(v[a], v[b], v[x], v[y]))
        widths[key] = min(width, 0.24 * limit)
        if widths[key] < 1e-12:
            raise geom.GeometryError('no numerically stable setback')

    # Overlap clamping changes the common width, rather than independently
    # widening distant edges that share the same bevel operation. The 24%
    # seed remains deliberately conservative; this is not Blender parity.
    global_setback = min((d for d in widths.values() if d), default=0.0)
    widths = {key: global_setback if d else 0.0 for key, d in widths.items()}

    def corner_offset(f, source):
        for loop in loops[f]:
            if source not in loop:
                continue
            j = loop.index(source)
            b, c = (loop[j - 1], loop[(j + 1) % len(loop)])
            keys = [tuple(sorted((source, b))), tuple(sorted((source, c)))]
            mm = [np.cross(n[f], (v[source] - v[b]) / np.linalg.norm(v[source] - v[b])), np.cross(n[f], (v[c] - v[source]) / np.linalg.norm(v[c] - v[source]))]
            A = np.stack([n[f], *mm])
            rhs = np.array([0.0, *[widths[k] for k in keys]])
            if abs(np.linalg.det(A)) < 1e-10:
                return (None, None)
            return (_solve(A, rhs), keys)
        raise geom.GeometryError('missing face corner')
    for iteration in range(200):
        changed = False
        for key, (f, g, e, L, angle, sign) in edgeinfo.items():
            if widths[key]:
                continue
            for source in key:
                aa, ka = corner_offset(f, source)
                bb, kb = corner_offset(g, source)
                if aa is None or bb is None:
                    continue
                ta, tb = (aa @ e, bb @ e)
                if abs(ta - tb) < 1e-12:
                    continue
                if ta * tb <= 0:
                    raise geom.GeometryError('incompatible low-angle corner offsets')
                target = min(abs(ta), abs(tb))
                for t, kk in [(ta, ka), (tb, kb)]:
                    factor = target / abs(t)
                    if factor < 1 - 1e-10:
                        for k in kk:
                            if widths[k]:
                                widths[k] *= factor
                                changed = True
        if not changed:
            break
    else:
        raise geom.GeometryError('low-angle width constraints did not converge')
    if any((0 < d < 1e-12 for d in widths.values())):
        raise geom.GeometryError('low-angle constraints collapse width')
    points = []
    result = []
    lookup = {}
    q = {}
    position = {}

    def vertex(p):
        key = tuple(np.round(p, 13))
        if key not in lookup:
            lookup[key] = len(points)
            points.append(np.array(p))
        return lookup[key]
    for f, face_loops in enumerate(loops):
        offset_loops = []
        ids = []
        for loop in face_loops:
            ring = []
            for j, a in enumerate(loop):
                b, c = (loop[j - 1], loop[(j + 1) % len(loop)])
                tangent0 = (v[a] - v[b]) / np.linalg.norm(v[a] - v[b])
                tangent1 = (v[c] - v[a]) / np.linalg.norm(v[c] - v[a])
                m0, m1 = (np.cross(n[f], tangent0), np.cross(n[f], tangent1))
                d0, d1 = (widths[tuple(sorted((a, b)))], widths[tuple(sorted((a, c)))])
                A = np.stack([n[f], m0, m1])
                rhs = np.array([0.0, d0, d1])
                if abs(np.linalg.det(A)) < 1e-10:
                    if np.linalg.norm(m0 - m1) > 1e-08 or abs(d0 - d1) > 1e-12:
                        raise geom.GeometryError('collinear unequal offset')
                    p = v[a] + m0 * d0
                else:
                    p = v[a] + _solve(A, rhs)
                idx = vertex(p)
                q[f, a] = idx
                position[f, a] = p
                ring.append(idx)
            offset_loops.append(np.array([points[i] for i in ring]))
            ids.extend(ring)
        drop = int(np.argmax(abs(n[f])))
        contours = [np.delete(p, drop, axis=1) for p in offset_loops]
        desired = n[f][drop] * (-1 if drop == 1 else 1)
        if desired < 0:
            contours = [p[::-1] for p in contours]
            ids = [q[f, a] for loop in face_loops for a in loop[::-1]]
        tris = _cap_triangulate(contours)
        if len(tris) == 0:
            raise geom.GeometryError('offset face has vanished')
        for tri in tris:
            face = [ids[i] for i in tri]
            if desired < 0:
                face.reverse()
            result.append(face)
    corner = defaultdict(list)
    diag = []
    for key, (f, g, e, L, angle, sign) in edgeinfo.items():
        a, b = key
        d = widths[key]
        rows = []
        for endpoint in [a, b]:
            start, end = (q[f, endpoint], q[g, endpoint])
            row = [start]
            if d:
                bis = (n[f] + n[g]) / (2 * math.cos(angle / 2))
                center = v[endpoint] - sign * bis * d / math.sin(angle / 2)
                radius = d / math.tan(angle / 2)
                for j in range(1, segments):
                    t = j / segments
                    normal = (math.sin((1 - t) * angle) * n[f] + math.sin(t * angle) * n[g]) / math.sin(angle)
                    smooth = [k for k in inc[endpoint] if not widths[k]]
                    planes = set((g for k in inc[endpoint] for g in edgeinfo[k][:2]))
                    if len(smooth) == 1 and len(planes) == 3:
                        sf, sg = edgeinfo[smooth[0]][:2]
                        anchor = next(iter(planes - {sf, sg}))
                        other = next((h for h in [f, g] if h != anchor))
                        neighbor = next((k for k in inc[endpoint] if k != key and widths[k]))
                        h = next((h for h in edgeinfo[neighbor][:2] if h != anchor))
                        end_support = -sign * d * math.sin(angle)
                        u = end_support * (1 - math.cos(math.pi * t / 2))

                        def second_support(k, u):
                            ff, gg, ee, ll, aa, ss = edgeinfo[k]
                            rr = widths[k] / math.tan(aa / 2)
                            x = u + ss * rr
                            radicand = rr * rr - x * x
                            if radicand < -1e-18:
                                raise geom.GeometryError('incompatible cylindrical miter')
                            return -ss * rr + math.cos(aa) * x + ss * math.sin(aa) * math.sqrt(max(0.0, radicand))
                        rhs = [u, second_support(key, u), second_support(neighbor, u)]
                        pp = v[endpoint] + _solve(np.stack([n[anchor], n[other], n[h]]), rhs)
                        if anchor != f:
                            u = end_support * (1 - math.cos(math.pi * (1 - t) / 2))
                            rhs = [u, second_support(key, u), second_support(neighbor, u)]
                            pp = v[endpoint] + _solve(np.stack([n[anchor], n[other], n[h]]), rhs)
                        row.append(vertex(pp))
                    else:
                        axial = (1 - t) * ((position[f, endpoint] - v[endpoint]) @ e) + t * ((position[g, endpoint] - v[endpoint]) @ e)
                        row.append(vertex(center + sign * radius * normal + e * axial))
            row.append(end)
            rows.append(row)
            corner[endpoint].append(row)
        for j in range(len(rows[0]) - 1):
            face = [rows[0][j], rows[1][j], rows[1][j + 1], rows[0][j + 1]]
            face = [a for i, a in enumerate(face) if a != face[i - 1]]
            if len(set(face)) >= 3:
                result.append(face)
        if d:
            diag.append(dict(edge=key, width=d, requested=width, angle=angle, convex=sign > 0))
    for source, arcs in corner.items():
        adj = defaultdict(list)
        boundary = Counter()
        for arc in arcs:
            for a, b in zip(arc, arc[1:]):
                if a != b:
                    boundary[tuple(sorted((a, b)))] += 1
        for (a, b), count in boundary.items():
            if count > 2:
                raise geom.GeometryError('overused analytic corner seam')
            if count == 1:
                adj[a].append(b)
                adj[b].append(a)
        if not adj:
            continue
        if any((len(k) != 2 for k in adj.values())):
            raise geom.GeometryError('corner boundary branches')
        start = next(iter(adj))
        ring = []
        prev = None
        cur = start
        while cur not in ring:
            ring.append(cur)
            nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
            prev, cur = (cur, nxt)
        if cur != start or len(ring) != len(adj):
            raise geom.GeometryError('corner patch has multiple rings')
        if len(ring) < 3:
            continue
        if len(ring) == 3:
            result.append(ring)
            continue
        result.extend(geom._triangulate(points, [ring]))
    for fi, face in enumerate(result):
        pp = np.array(points)[face]
        ar = np.linalg.norm(np.sum(np.cross(pp, np.roll(pp, -1, axis=0)), axis=0))
        if ar < 1e-14:
            raise geom.GeometryError('degenerate constructed polygon ' + str((fi, face, pp.tolist())))
    outv, outf = geom._orient(points, result)
    tr = geom._triangulate(outv, outf)
    p = np.array(outv)[tr]
    area = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
    if np.any(area < 1e-14):
        raise geom.GeometryError('constructed degenerate face')
    solid = geom._as_manifold(outv, tr)
    uses = Counter(((a, b) for face in tr for a, b in zip(face, face[1:] + face[:1])))
    if any((uses[a, b] != 1 or uses[b, a] != 1 for a, b in uses)):
        raise geom.GeometryError('Polyhedral bevel has an open/nonmanifold output boundary')
    if set((i for face in tr for i in face)) != set(range(len(outv))):
        raise geom.GeometryError('Polyhedral bevel has unused output vertices')
    if solid.volume() <= 0:
        raise geom.GeometryError('Polyhedral bevel has nonpositive volume')
    if _self_intersects(np.array(outv), np.array(tr)):
        raise geom.GeometryError('Polyhedral bevel corner/edge patches self-intersect')
    return (outv, tr, dict(edges=diag, global_conservative_setback_m=global_setback,
        shallow_reduced_edges=int(sum(edge["width"] < global_setback-1e-12 for edge in diag)),
        volume_m3=solid.volume(), min_double_area_m2=float(area.min())))
