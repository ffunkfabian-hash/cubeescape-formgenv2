"""R02 Frost – gemeinsame Bausteine der fünf Baugruppen (mm, Autorenraum f,u,x).

Maßstab: Höhe 2000 mm (Nutzervorgabe 27.10.2026) über die Front-Scheitel-/
Bodenzeilen des weiß/blauen Blatts, k=2000/3665 mm/px für alle Ansichten.
Konturzeilen stammen aus tools/r02_measure.py (mask revision 1, gemessen):
Front-x anatomisch links positiv, Profil-f vorn positiv, f=0 Kniescheibenmitte.
Front und Profile sind je Seite gemittelt (Spiegelbild), Front verbindlich.

Teile sind geschlossene, positiv orientierte Netze mit expliziten Dreiecken.
Spiegelung (rechts=−x) behält dieselben Diagonalen; kein zweiter Tessellierer.
"""
import math

K = 2000 / 3665
PROVENANCE = {
    'kind': 'gemessen',
    'source': 'refs-r02/r02-blauweiss.svg (SHA d997c46b…a4814), Raster rsvg-convert -w 9803, mask revision 1; tools/r02_measure.py',
    'scale': {'kind': 'Vorgabe', 'height_mm': 2000, 'mm_per_pixel': K,
              'source': 'Nutzerentscheidung 27.10.2026; Frontscheitel y174, Frontboden y3839 (Kante)'},
    'registration': {'kind': 'gemessen',
                     'source': 'Front/Rücken: Symmetrieachse (Spiegel-IoU 0,9947/0,9939); Profile: f=0 an der Kniescheibenmitte (Ringschwerpunkt), refs-r02/mask-provenance.json'},
}


def ring(u, xl, xr, fb, ff, cx=.22, cf=.22):
    """Octagonal horizontal ring with exact x/f extents (front/profile contour)."""
    dx, df = cx * (xr - xl), cf * (ff - fb)
    return [[ff, u, xl + dx], [ff, u, xr - dx], [ff - df, u, xr], [fb + df, u, xr],
            [fb, u, xr - dx], [fb, u, xl + dx], [fb + df, u, xl], [ff - df, u, xl]]


def _volume(vertices, faces):
    def det(a, b, c):
        return (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0])
                + a[2]*(b[0]*c[1]-b[1]*c[0]))
    return sum(det(vertices[a], vertices[b], vertices[c]) for a, b, c in faces)


def closed(vertices, faces):
    """Explicit triangles with positive world volume (author f,u,x is mirrored)."""
    tris = [[face[0], face[i], face[i+1]] for face in faces for i in range(1, len(face)-1)]
    # Author f,u,x -> world x,-f,u reverses orientation: positive world volume
    # means negative determinant sum in author coordinates.
    if _volume(vertices, tris) > 0:
        tris = [[a, c, b] for a, b, c in tris]
    return dict(shape='surface', vertices=[list(map(float, v)) for v in vertices], faces=tris)


def _ears(ring):
    """Ear-clipping of a simple horizontal ring in (f,x); triangles as (i,j,k), ring order kept."""
    pts = [(p[0], p[2]) for p in ring]
    area = sum(pts[i][0]*pts[i-1][1] - pts[i-1][0]*pts[i][1] for i in range(len(pts)))
    sign = 1 if area > 0 else -1

    def turn(a, b, c):
        return sign*((pts[b][0]-pts[a][0])*(pts[c][1]-pts[a][1]) - (pts[b][1]-pts[a][1])*(pts[c][0]-pts[a][0]))
    left, out = list(range(len(pts))), []
    while len(left) > 3:
        for k in range(len(left)):
            a, b, c = left[k-1], left[k], left[(k+1) % len(left)]
            if turn(c, b, a) <= 1e-12:
                continue
            if any(turn(c, b, p) >= 0 and turn(b, a, p) >= 0 and turn(a, c, p) >= 0
                   for p in left if p not in (a, b, c)):
                continue
            out.append((a, b, c))
            left.pop(k)
            break
        else:
            raise ValueError('Querschnitt nicht einfach')
    return out + [tuple(left)]


def loft(rings, caps='fan'):
    """Closed loft over equal rings with canonical triangles.

    caps 'fan' (convex octagons) or 'ear' (measured, possibly concave sections).
    """
    n = len(rings[0])
    vertices = [p for r in rings for p in r]
    faces = []
    for j in range(len(rings) - 1):
        for i in range(n):
            a, b = j*n+i, j*n+(i+1) % n
            c, d = (j+1)*n+(i+1) % n, (j+1)*n+i
            faces += [[a, b, c], [a, c, d]]
    last = (len(rings)-1)*n
    if caps == 'ear':
        faces += [[a, c, b] for a, b, c in _ears(rings[0])]
        faces += [[last+a, last+b, last+c] for a, b, c in _ears(rings[-1])]
    else:
        faces += [[0, i+1, i] for i in range(1, n-1)]
        faces += [[last, last+i, last+i+1] for i in range(1, n-1)]
    return closed(vertices, faces)


def rows_loft(rows, cx=.22, cf=.22):
    """rows: (u, xl, xr, fb, ff) bottom to top."""
    return loft([ring(u, xl, xr, fb, ff, cx, cf) for u, xl, xr, fb, ff in rows])


# --- Querschnitte aus der KI-Referenz (0.2) ----------------------------------
# sections: [[u, [f0, x0, f1, x1, …]], …] aus tools/r02_sections.py, Form auf
# −1..1 normiert. Die Zeilenmaße (Blatt) skalieren sie affin: Umriss bleibt beim
# Blatt, Querschnitt kommt aus dem Netz.
def _shape_at(sections, u):
    """(shape, origin) at u, linear between measured section rows, clamped at the ends."""
    if u <= sections[0][0]:
        return sections[0][1], sections[0][2]
    for (ua, a, oa), (ub, b, ob) in zip(sections, sections[1:]):
        if ua <= u <= ub:
            t = (u - ua) / (ub - ua)
            return [p + (q - p) * t for p, q in zip(a, b)], [p + (q - p) * t for p, q in zip(oa, ob)]
    return sections[-1][1], sections[-1][2]


def section_ring(row, shape, inset=0):
    """Measured shape scaled onto the row extents; inset moves points radially
    towards the ray origin so the layer is about `inset` thick along the normal
    and the inner ring stays star-shaped inside the outer one (concave sections)."""
    import math as m
    (u, xl, xr, fb, ff), (pts, origin) = row, shape
    fc, xc, hf, hx = (fb + ff) / 2, (xl + xr) / 2, (ff - fb) / 2, (xr - xl) / 2
    ring = [(fc + pts[i] * hf, xc + pts[i + 1] * hx) for i in range(0, len(pts), 2)]
    if inset:
        of, ox = fc + origin[0] * hf, xc + origin[1] * hx
        n, area = len(ring), sum(ring[i-1][0]*ring[i][1] - ring[i][0]*ring[i-1][1] for i in range(len(ring)))
        out = []
        for i, (f, x) in enumerate(ring):
            (f0, x0), (f1, x1) = ring[i-1], ring[(i+1) % n]
            nf, nx = (x1 - x0), -(f1 - f0)          # outward for counter-clockwise (f,x)
            if area < 0:
                nf, nx = -nf, -nx
            rf, rx = f - of, x - ox
            rl, nl = m.hypot(rf, rx), m.hypot(nf, nx) or 1
            cos = max((rf * nf + rx * nx) / (rl * nl), .35) if rl else 1
            k = max(.15, 1 - inset / cos / rl) if rl else 1
            out.append((of + rf * k, ox + rx * k))
        ring = out
    return [[f, u, x] for f, x in ring]


def section_rows(rows, sections, step=10):
    """Measured rows plus a step grid between them, each with its section shape."""
    levels = sorted({r[0] for r in rows} | set(range(int(rows[0][0]) // step * step + step, int(rows[-1][0]), step)))
    return [(tuple(_row_at(rows, u)), _shape_at(sections, u)) for u in levels]


def section_loft(dense, skin=0):
    return loft([section_ring(row, shape, skin) for row, shape in dense], caps='ear')


# Waagerechte Plattenkanten liegen auf geraden Blattpixelzeilen (tools/r02_regions.py,
# Schritt 2 px ab Frontboden y3839). Schnittebenen an Stößen liegen auf ungeraden
# Zeilen: ≥ 0,546 mm Abstand zu jeder Plattenkante, also nie koplanar (< 0,5 mm).
SHEET_FLOOR_PX = 3839


def lattice_mid(u, direction):
    """Nearest odd sheet row at/above (direction +1) or at/below (−1) u, in mm."""
    y = math.floor(SHEET_FLOOR_PX - u / K) if direction > 0 else math.ceil(SHEET_FLOOR_PX - u / K)
    if y % 2 == 0:
        y -= direction
    return (SHEET_FLOOR_PX - y) * K


def plate_span(lo, hi, below=None, above=None, gap=.55):
    """Plate range of one segment: starts ≥ gap above the segment below, ends ≥ gap under the one above."""
    lo = lattice_mid(below + gap, 1) if below is not None else lo
    hi = lattice_mid(above - gap, -1) if above is not None else hi
    return lo, hi


def mirror(shape):
    """Mirror x (left -> right) keeping identical triangle diagonals."""
    s = dict(shape)
    s['vertices'] = [[f, u, -x] for f, u, x in shape['vertices']]
    s['faces'] = [[a, c, b] for a, b, c in shape['faces']]
    return s


def box(f0, f1, u0, u1, x0, x1):
    v = [[f, u, x] for f in (f0, f1) for u in (u0, u1) for x in (x0, x1)]
    return closed(v, [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]])


def plate(outline, f_of, depth):
    """Thin panel: outline (u,x) polygon, front surface at f_of(u,x), depth mm backwards."""
    n = len(outline)
    front = [[f_of(u, x), u, x] for u, x in outline]
    back = [[f - depth, u, x] for f, u, x in front]
    faces = [list(range(n)), [n+i for i in reversed(range(n))]]
    faces += [[i, n+i, n+(i+1) % n, (i+1) % n] for i in range(n)]
    return closed(front+back, faces)


def disc(axis, center, a0, a1, r, segs=24):
    """Explicit cylinder (axis 'x' or 'f'), centre (f,u) or (u,x)."""
    pts = []
    for a in (a0, a1):
        for i in range(segs):
            t = 2*math.pi*i/segs
            if axis == 'x':
                pts.append([center[0]+r*math.cos(t), center[1]+r*math.sin(t), a])
            else:
                pts.append([a, center[0]+r*math.sin(t), center[1]+r*math.cos(t)])
    faces = [[i, (i+1) % segs, segs+(i+1) % segs, segs+i] for i in range(segs)]
    faces += [list(range(segs-1, -1, -1)), list(range(segs, 2*segs))]
    return closed(pts, faces)


def _row_at(rows, u):
    for a, b in zip(rows, rows[1:]):
        if a[0] <= u <= b[0]:
            t = (u - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0
            return [p + (q - p) * t for p, q in zip(a, b)]
    raise ValueError(f'Panel ausserhalb der Zeilen: u{u}')


def _face_point(rows, face, u, s, off, cx, cf):
    _, xl, xr, fb, ff = _row_at(rows, u)
    dx, df = cx * (xr - xl), cf * (ff - fb)
    if face in ('front', 'back'):
        x = xl + dx + (xr - xl - 2*dx) * s
        return [ff + off if face == 'front' else fb - off, u, x]
    f = fb + df + (ff - fb - 2*df) * s
    return [f, u, xr + off if face == 'outer' else xl - off]


def _clip(poly, lo, hi):
    """Convex (u,s) polygon clipped to lo<=u<=hi (Sutherland–Hodgman, stable)."""
    for bound, keep in ((lo, lambda p: p[0] >= lo), (hi, lambda p: p[0] <= hi)):
        out = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            if keep(a):
                out.append(a)
            if keep(a) != keep(b):
                # Same edge orientation on both neighbouring strips -> identical points.
                p, q = (a, b) if a < b else (b, a)
                t = (bound - p[0]) / (q[0] - p[0])
                out.append((bound, p[1] + (q[1] - p[1]) * t))
        poly = out
        if not poly:
            return []
    return poly


def _hull(points):
    """Counter-clockwise convex hull in (u,s) (monotone chain)."""
    pts = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) > 1 and ((out[-1][0]-out[-2][0])*(p[1]-out[-2][1])
                                    - (out[-1][1]-out[-2][1])*(p[0]-out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])


def face_panel(rows, face, poly, off=1.2, depth=3, cx=.22, cf=.22):
    """Thin panel lying on one planar loft face per ring interval.

    rows as for rows_loft; face front/back/outer/inner; poly (u, s) → convex hull
    with s 0..1 across the face (front/back: x low→high, sides: f back→front).
    Each ring interval is triangulated separately, so the panel stays parallel
    to the loft face at constant offset (no chord dipping into the body).
    """
    levels = [r[0] for r in rows]
    poly = _hull(poly)
    keys, verts, front = {}, [], []

    def vid(p, layer):
        key = (round(p[0], 6), round(p[1], 6), layer)
        if key not in keys:
            keys[key] = len(verts)
            verts.append(_face_point(rows, face, p[0], p[1], off if layer else off - depth, cx, cf))
        return keys[key]
    for lo, hi in zip(levels, levels[1:]):
        strip = _clip(list(poly), lo, hi)
        if len(strip) < 3:
            continue
        ids = [vid(p, 1) for p in strip]
        ids = [i for k, i in enumerate(ids) if i != ids[k-1]]
        front += [[ids[0], ids[i], ids[i+1]] for i in range(1, len(ids)-1)]
    uses = {}
    for a, b, c in front:
        for e in ((a, b), (b, c), (c, a)):
            uses.setdefault(tuple(sorted(e)), []).append(e)
    back = {i: vid(k[:2], 0) for k, i in list(keys.items()) if k[2] == 1}
    faces = [list(t) for t in front] + [[back[a], back[c], back[b]] for a, b, c in front]
    for pair in uses.values():
        if len(pair) == 1:
            a, b = pair[0]
            faces += [[b, a, back[a]], [b, back[a], back[b]]]
    return closed(verts, faces)


# --- Projizierte Platten (Pilot 0.2: Arme) ---------------------------------
# Eine Hülle (rows) wird in eine dunkle Kernschicht (um SKIN mm eingerückt)
# und eine Außenschicht geteilt. Farbregionen des Blatts werden entlang ihrer
# Blickrichtung extrudiert und mit der Außenschicht im Sektor dieser Ansicht
# geschnitten: Platten tragen den Zeichnungsumriss, die schwarzen Zeichen-
# linien bleiben als vertiefte Fugen im Kern sichtbar.
SKIN = 4
_SECTOR = {'front': ((1, -1), (1, 1)), 'back': ((-1, 1), (-1, -1)), 'outer': ((1, 1), (-1, 1))}


def _world(v):
    return [[x, -f, u] for f, u, x in v]


def _solid(shape):
    import manifold3d as mf
    import numpy as np
    return mf.Manifold(mf.Mesh64(np.asarray(_world(shape['vertices']), dtype=np.float64),
                                 np.asarray(shape['faces'], dtype=np.uint64)))


def _clean(points, tris, eps=1.2e-4, short=.05):
    """Repair boolean slivers without moving the surface.

    eps: |cross| in mm² below which a triangle counts as a sliver. A needle
    (vertex on its longest edge) is removed by flipping that edge with the
    neighbour; the flip is kept only if both new triangles are proper and face
    the neighbour's way. Remaining slivers collapse their shortest edge if it
    is below `short` mm and the link condition keeps the mesh 2-manifold.
    """
    import numpy as np
    P = np.asarray(points, dtype=float)
    tris = [tuple(t) for t in tris]

    def cross(t):
        a, b, c = P[list(t)]
        return np.cross(b - a, c - a)

    def length(a, b):
        return float(np.linalg.norm(P[a] - P[b]))
    # Coincident vertices joined by an edge: weld, then drop collapsed
    # triangles and the zero-volume fins (same triangle twice, opposite turn).
    parent = list(range(len(P)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for t in tris:
        for i in range(3):
            if length(t[i], t[(i+1) % 3]) < 1e-9:
                ra, rb = find(t[i]), find(t[(i+1) % 3])
                parent[max(ra, rb)] = min(ra, rb)
    tris = [tuple(find(i) for i in t) for t in tris]
    tris = [t for t in tris if len(set(t)) == 3]
    count = {}
    for t in tris:
        key = frozenset(t)
        count[key] = count.get(key, 0) + 1
    tris = [t for t in tris if count[frozenset(t)] == 1]
    for _ in range(200):
        bad = [k for k, t in enumerate(tris) if np.linalg.norm(cross(t)) < eps]
        if not bad:
            break
        edges = {(t[i], t[(i+1) % 3]): k for k, t in enumerate(tris) for i in range(3)}
        done = set()
        for k in bad:
            if k in done:
                continue
            t = tris[k]
            i = max(range(3), key=lambda i: length(t[i], t[(i+1) % 3]))
            a, b, c = t[i], t[(i+1) % 3], t[(i+2) % 3]
            j = edges.get((b, a))
            if j is None or j in done:
                continue
            d = next(x for x in tris[j] if x not in (a, b))
            if (c, d) in edges or (d, c) in edges:
                continue
            ref, new = cross(tris[j]), [(c, a, d), (c, d, b)]
            if all(np.linalg.norm(cross(n)) >= eps and cross(n) @ ref > 0 for n in new):
                tris[k], tris[j] = new
                done |= {k, j}
        if done:
            continue
        ring = {}
        for t in tris:
            for i in range(3):
                ring.setdefault(t[i], set()).update((t[(i+1) % 3], t[(i+2) % 3]))
        collapse = None
        for k in bad:
            t = tris[k]
            for i in sorted(range(3), key=lambda i: length(t[i], t[(i+1) % 3])):
                a, b = t[i], t[(i+1) % 3]
                if length(a, b) >= short or (b, a) not in edges:
                    continue
                opposite = {t[(i+2) % 3], next(x for x in tris[edges[(b, a)]] if x not in (a, b))}
                if ring[a] & ring[b] == opposite:
                    collapse = a, b, {k, edges[(b, a)]}
                    break
            if collapse:
                break
        if collapse:
            a, b, gone = collapse
            tris = [tuple(a if x == b else x for x in t) for n, t in enumerate(tris) if n not in gone]
        else:
            raise ValueError(f'Splitterdreieck nicht reparierbar ({len(bad)}): '+str([[P[i].round(4).tolist() for i in tris[k]] for k in bad[:3]]))
    used = sorted({i for t in tris for i in t})
    index = {old: new for new, old in enumerate(used)}
    return P[used].tolist(), [[index[i] for i in t] for t in tris]


def _shape_of(solid):
    import numpy as np
    mesh = solid.to_mesh64()
    v, tris = _clean(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts).tolist())
    return closed([[-y, z, x] for x, y, z in v], tris)


def _sector(rows, view, reach=4, margin=40):
    """Wedge from the row centre through the rectangle corners of one view.

    Blade quads always take the diagonal centre(j)–corner(j+1), so adjacent
    sectors share an identical, gap-free boundary surface.
    """
    (fa, xa), (fb_, xb) = _SECTOR[view]
    ext = [(rows[0][0]-margin,)+tuple(rows[0][1:])] + list(rows) + [(rows[-1][0]+margin,)+tuple(rows[-1][1:])]
    points = []
    for u, xl, xr, fb, ff in ext:
        fc, xc, hd, hw = (fb+ff)/2, (xl+xr)/2, reach*(ff-fb)/2, reach*(xr-xl)/2
        points += [[fc, u, xc], [fc+fa*hd, u, xc+xa*hw], [fc+fb_*hd, u, xc+xb*hw]]
    faces = []
    for j in range(len(ext)-1):
        c0, p0, q0, c1, p1, q1 = 3*j, 3*j+1, 3*j+2, 3*j+3, 3*j+4, 3*j+5
        faces += [[c0, p0, p1], [c0, p1, c1], [p0, q0, q1], [p0, q1, p1], [q0, c0, q1], [c0, c1, q1]]
    last = 3*(len(ext)-1)
    faces += [[0, 2, 1], [last, last+1, last+2]]
    return closed(points, faces)


def _extrusion(section, view):
    solid = section.extrude(2000)
    if view == 'outer':      # (f,u) → X=1000−z, Y=−f, Z=u
        m = [[0, 0, -1, 1000], [-1, 0, 0, 0], [0, 1, 0, 0]]
    else:                    # (x,u) → X=x, Y=1000−z, Z=u
        m = [[1, 0, 0, 0], [0, 0, -1, 1000], [0, 1, 0, 0]]
    return solid.transform(m)


def _disjoint(regions):
    """Drawing regions as disjoint cross-sections in list order (largest first)."""
    import manifold3d as mf
    out, taken = [], None
    for region in regions:
        section = mf.CrossSection([[tuple(p) for p in c] for c in region['contours']])
        if taken is not None:
            section = section - taken
        if section.area() > 1:
            out.append((region['role'], section))
            taken = section if taken is None else taken + section
    return out


def projected(rows, regions, views, skin=SKIN, cx=.22, cf=.22, sections=None, clip=None):
    """Core shape plus {role: shape} plates for one hull and drawing regions.

    regions: {view: [{'role', 'contours'}]} with view in front/back/outer.
    sections: optional measured cross-sections (section_rows) instead of octagons.
    clip: (u_lo, u_hi) limits the plates, e.g. above the 3-mm embedding into
    the segment below, so stacked segments never carry the same plate twice.
    Regions are made disjoint per view in 2D (largest first): the colour
    classes of the sheet touch along the ink lines and would otherwise
    overlap by a pixel with coplanar faces. Views meet only in sector planes.
    """
    import manifold3d as mf
    if sections:
        # Kern = Hülle um skin erodiert (Minkowski, 8er-Kugel: Normalabstand
        # 3,7–4 mm auch an flach liegenden Flächen, wo waagerechtes Einrücken
        # koplanar würde).
        # Kerndeckel auf Rastermitten (lattice_mid): nie koplanar zu Plattenkanten.
        hull = _solid(section_loft(section_rows(rows, sections)))
        lo, hi = lattice_mid(rows[0][0] + skin, 1), lattice_mid(rows[-1][0] - skin, -1)
        core = (hull.minkowski_difference(mf.Manifold.sphere(skin, 8))
                ^ mf.Manifold.cube([4000, 4000, hi - lo]).translate([-2000, -2000, lo]))
        inner_shape = _shape_of(core)
    else:
        inner = [(u, xl+skin, xr-skin, fb+skin, ff-skin) for u, xl, xr, fb, ff in rows]
        hull, inner_shape = _solid(rows_loft(rows, cx, cf)), rows_loft(inner, cx, cf)
        core = _solid(inner_shape)
    layer = hull - core
    if clip:
        layer = layer ^ mf.Manifold.cube([4000, 4000, clip[1]-clip[0]]).translate([-2000, -2000, clip[0]])
    plates = {}
    for view in views:
        zone = layer ^ _solid(_sector(rows, view))
        for role, section in _disjoint(regions.get(view, [])):
            piece = zone ^ _extrusion(section, view)
            if piece.volume() > 1:
                plates.setdefault(role, []).append(piece)
    shapes = {role: _shape_of(mf.Manifold.batch_boolean(pieces, mf.OpType.Add))
              for role, pieces in sorted(plates.items())}
    return inner_shape, shapes
