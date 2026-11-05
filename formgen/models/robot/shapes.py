# Einmalig übertragen aus BALLON Commit 14bd78d (basic/robot/shapes.py); BALLON bleibt Lesereferenz, keine Laufzeitabhängigkeit.
"""Formhilfen des BASIC-Roboters (mm): gerundete/gefaste Querschnitte, Kuppel, Motive Bolzen und Medaillon.

Aus basic/arms/robot_figure.py (v2) übernommen. Teile sind Tupel wie beim Arm: (id, de, segment, form, rolle, params);
Formen hull (konvexe Hülle aus pts), hulls (mehrere Hüllen in einem Teil, parts) und cyl (axis, r, len, c), gebaut von tools/ego_build.piece_mesh.
"""
import math


def rsection(w, y0, y1, r, z, n=4, bulge=0.0):
    """Gerundeter Rechteckquerschnitt bei z (Eckradius r, n Zwischenpunkte je Ecke; n=1 ist eine Fase).
    bulge > 0 wölbt die Seiten (±X) und Vorder-/Rückseite um so viele mm nach außen (je ein Mittelpunkt)."""
    r = min(r, w / 2 - 0.1, (y1 - y0) / 2 - 0.1)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, y1 - r, 0), (-(w / 2 - r), y1 - r, 90), (-(w / 2 - r), y0 + r, 180), (w / 2 - r, y0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    if bulge:
        ym = (y0 + y1) / 2
        pts += [(w / 2 + bulge, ym, z), (-w / 2 - bulge, ym, z), (0, y1 + bulge, z), (0, y0 - bulge, z)]
    return pts


def rsection_top(w, y0, y1, r, z, z_top=None, n=4, bulge=0.0):
    """Obere Hälfte (Schale) mit gerundeten Außenkanten; Punkte über y0 + r bekommen z_top (Pfeilschnitt)."""
    zt = z if z_top is None else z_top
    pts = [p for p in rsection(w, y0 - (y1 - y0), y1, r, z, n) if p[1] >= y0 - 1e-6]
    pts += [(w / 2, y0, z), (-w / 2, y0, z)]
    if bulge:
        pts.append((0, y1 + bulge, z))
    return [(x, y, zt if y > y0 + r else z) for x, y, z in pts]


def dome(sx, c, rings, n=4):
    """Kuppel entlang X (Schulter): rings = [(x, breite_y, höhe_z, radius)], c = (y, z) Mitte."""
    pts = []
    for x, wy, hz, r in rings:
        for yy, zz, _ in rsection(wy, -hz / 2, hz / 2, r, 0, n):
            pts.append((sx * x, c[0] + yy, c[1] + zz))
    return pts


def bolts(seg, y, z, dx=14, r=4.4, name=None):
    name = name or seg
    return [(f'{name}_bolt_{k}', 'Bolzen', seg, 'cyl', 'trim', dict(axis='y', r=r, len=4, c=(s * dx, y, z)))
            for k, s in (('a', -1), ('b', 1))]


def medallion(name, seg, c, r, length, axis='x'):
    """Scheibe, blanker Ring, Nabe – das Medaillon-Motiv vom Ellbogen."""
    return [(f'{name}_disc', 'Medaillon', seg, 'cyl', 'graphite', dict(axis=axis, r=r, len=length, c=c)),
            (f'{name}_ring', 'Medaillonring', seg, 'cyl', 'trim', dict(axis=axis, r=r * 0.76, len=length + 4, c=c)),
            (f'{name}_hub', 'Medaillonnabe', seg, 'cyl', 'graphite', dict(axis=axis, r=r * 0.52, len=length + 8, c=c))]


def piston(name, de, seg, a, b, r=7):
    """Kleine Hydraulik von a nach b (mm im Segmentrahmen): dunkler Zylinder, blanke Kolbenstange (je eine Hülle)."""
    m = [(a[i] + b[i]) / 2 for i in range(3)]
    return [(f'{name}_cyl', de, seg, 'hull', 'dark_metal', dict(pts=_tube(a, m, r))),
            (f'{name}_rod', de + ' (Stange)', seg, 'hull', 'trim', dict(pts=_tube(m, b, r * 0.55)))]


def cable(name, de, seg, path, r=6, role='rubber'):
    """Kabel entlang einer Polylinie (mm im Segmentrahmen): Kette aus Achtkantrohren, Form hulls (eine Hülle je Abschnitt)."""
    return [(name, de, seg, 'hulls', role, dict(parts=[_tube(a, b, r) for a, b in zip(path, path[1:])]))]


def _tube(a, b, r, n=8):
    """Achtkantrohr von a nach b als Punktwolke (Achse beliebig)."""
    d = [b[i] - a[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d)) or 1.0
    d = [v / L for v in d]
    h = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    u = _norm(_cross(d, h))
    v = _cross(d, u)
    pts = []
    for p in (a, b):
        for k in range(n):
            t = 2 * math.pi * k / n
            pts.append(tuple(p[i] + r * (math.cos(t) * u[i] + math.sin(t) * v[i]) for i in range(3)))
    return pts


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    L = math.sqrt(sum(v * v for v in a)) or 1.0
    return tuple(v / L for v in a)


# ------------------------------------------------------------------ 0.23 „Gauntlet“: Formsprache von Arm v3 und Stil v2.1
# Gewölbte Formen aus basic/arms/forms.py (Querschnitte sec, gebaut von tools/ego_build.form_mesh): Graphitkörper (loft), Cremeschale
# als umgreifende Platte (wrap) mit Pfeilschnitt, dunkle zweite Lage mit zwei Bolzen, Medaillon an den Gelenken.
from .forms import sec  # noqa: E402


def loft(pid, de, seg, role, secs, **kw):
    return (pid, de, seg, 'loft', role, dict(secs=secs, **kw))


def wrap(pid, de, seg, role, secs, a0, a1, t, **kw):
    return (pid, de, seg, 'wrap', role, dict(secs=secs, a0=a0, a1=a1, t=t, **kw))


def ring(pid, de, seg, role, z0, z1, a, b, t, n=2.4, **kw):
    """Geschlossener Ring (Wirbel-, Gürtel-, Halsring) um die Segmentachse."""
    return wrap(pid, de, seg, role, [sec(z0, a, b, n=n), sec(z1, a, b, n=n)], -180, 180, t, sub=1, **kw)


def tab(table, ch=0.0):
    """Querschnitt aus einer Tabelle [(z, a, b, y) …] linear abgreifen: f(z, grow=0, n=2.6, **extra) → sec. ch > 0: gefaster
    Querschnitt wie Arm v3 (robot_arm.section) – flache Seiten, Fasen an den Ecken; grow versetzt die Fasen parallel."""
    pairs = list(zip(table, table[1:]))

    def f(z, grow=0.0, n=2.6, **extra):
        (z0, a0, b0, y0), (z1, a1, b1, y1) = next((p for p in pairs if z <= p[1][0]), pairs[-1])
        u = max(0.0, min(1.0, (z - z0) / (z1 - z0)))
        return sec(z, a0 + (a1 - a0) * u + grow, b0 + (b1 - b0) * u + grow, y0 + (y1 - y0) * u, n=n,
                   ch=ch + grow * (2 - 2 ** 0.5) if ch else 0.0, **extra)
    return f


def arrow(f, z_full, z_tip, a0, a1, grow, n=2.6, tip=3.0):
    """Pfeilschnitt (Arm v3): Platte über f mit voller Breite a0..a1 bis z_full, läuft bis z_tip auf ±tip Grad zu."""
    return [f(z_full, grow, n=n, a0=a0, a1=a1), f(z_tip, grow, n=n, a0=-tip, a1=tip)]


def two_bolts(name, seg, f, z, grow, dx=14, r=4.2):
    """Zwei blanke Bolzen auf der Vorderseite (+Y) von f bei z, grow = Abstand über der Kontur – Motiv der Handgelenkplatte."""
    s = f(z, grow)
    return [(f'{name}_bolt_{k}', 'Bolzen', seg, 'cyl', 'trim', dict(axis='y', r=r, len=4, c=(sx * dx, s['y'] + s['b'] + 1.0, z)))
            for k, sx in (('a', -1), ('b', 1))]
