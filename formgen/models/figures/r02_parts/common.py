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
