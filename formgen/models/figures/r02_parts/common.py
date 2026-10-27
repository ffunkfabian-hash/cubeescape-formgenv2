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


def loft(rings):
    """Closed loft over equal rings with canonical triangles (caps fanned)."""
    n = len(rings[0])
    vertices = [p for r in rings for p in r]
    faces = []
    for j in range(len(rings) - 1):
        for i in range(n):
            a, b = j*n+i, j*n+(i+1) % n
            c, d = (j+1)*n+(i+1) % n, (j+1)*n+i
            faces += [[a, b, c], [a, c, d]]
    last = (len(rings)-1)*n
    faces += [[0, i+1, i] for i in range(1, n-1)]
    faces += [[last, last+i, last+i+1] for i in range(1, n-1)]
    return closed(vertices, faces)


def rows_loft(rows, cx=.22, cf=.22):
    """rows: (u, xl, xr, fb, ff) bottom to top."""
    return loft([ring(u, xl, xr, fb, ff, cx, cf) for u, xl, xr, fb, ff in rows])


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
