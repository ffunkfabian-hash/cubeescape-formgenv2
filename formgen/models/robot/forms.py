# Einmalig übertragen aus BALLON Commit 14bd78d (basic/arms/forms.py); BALLON bleibt Lesereferenz, keine Laufzeitabhängigkeit.
"""Formen für Arm-Rigs ab 0.23 „Gauntlet“: gewölbte Schalen statt konvexer Hüllen (reines Python, ohne Blender, testbar).

Alle Maße in mm im Segmentrahmen (+Z entlang des Segments, +Y Panzer-/Rückseite, +X Daumenseite der rechten Hand). Ein Querschnitt
ist eine Superellipse: `sec(z, a, b, y=0, x=0, n=2.6)` mit Halbbreite a (X), Halbhöhe b (Y), Mitte (x, y) und Exponent n
(2 Ellipse, 4 abgerundetes Rechteck). Winkel in Grad um die Segmentachse: 0 = +Y (außen/oben), positiv zur +X-Seite.

  loft(secs)                 geschlossener Körper durch die Querschnitte (weich interpoliert, Deckel an beiden Enden)
  wrap(secs, a0, a1, t)      Panzerplatte: Band der Querschnittskontur von a0 bis a1, Dicke t nach außen; je Querschnitt dürfen
                             a0/a1 abweichen (Pfeilschnitt); a1 − a0 = 360 ergibt einen geschlossenen Ring
  tube(path, r)              Leitung oder Kolbenstange entlang einer Polylinie

Rückgabe jeweils (verts, faces) mit verts in mm und Flächen als Indextupel (nach außen orientiert).
"""
import math


def sec(z, a, b, y=0.0, x=0.0, n=2.6, ch=0.0, **kw):
    """Querschnitt bei z. ch > 0: gefastes Rechteck (Fase ch mm an allen vier Ecken, wie robot_arm.section) statt Superellipse."""
    return dict(z=z, a=a, b=b, y=y, x=x, n=n, ch=ch, **kw)


def _tangents(y):
    """Monotone Tangenten (Fritsch-Carlson) über gleichmäßige Schritte: keine Überschwinger zwischen den Querschnitten."""
    n = len(y)
    d = [y[i + 1] - y[i] for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        h = a * a + b * b
        if h > 9:
            k = 3 / math.sqrt(h)
            m[i], m[i + 1] = k * a * d[i], k * b * d[i]
    return m


def resample(secs, sub=6):
    """Querschnitte weich verdichten: sub Zwischenschritte je Abschnitt, alle Zahlenfelder monoton kubisch (Hermite)."""
    if len(secs) < 2 or sub <= 1:
        return [dict(s) for s in secs]
    keys = [k for k, v in secs[0].items() if isinstance(v, (int, float))]
    tan = {k: _tangents([s[k] for s in secs]) for k in keys}
    out = []
    for i in range(len(secs) - 1):
        for j in range(sub):
            t = j / sub
            h00, h10, h01, h11 = 2 * t ** 3 - 3 * t * t + 1, t ** 3 - 2 * t * t + t, -2 * t ** 3 + 3 * t * t, t ** 3 - t * t
            out.append({k: h00 * secs[i][k] + h10 * tan[k][i] + h01 * secs[i + 1][k] + h11 * tan[k][i + 1] for k in keys})
    out.append({k: secs[-1][k] for k in keys})
    return out


def _pt(s, ang, grow=0.0):
    """Punkt der Querschnittskontur bei Winkel ang (Grad, 0 = +Y), um grow nach außen vergrößert."""
    t = math.radians(ang)
    si, co = math.sin(t), math.cos(t)
    a, b = s['a'] + grow, s['b'] + grow
    if s.get('ch', 0) > 0:          # Strahl vom Mittelpunkt bis zum gefasten Rechteck (|x| ≤ a, |y| ≤ b, |x| + |y| ≤ a + b − Fase)
        c = min(s['ch'], a - 0.1, b - 0.1)
        lim = [a / abs(si) if abs(si) > 1e-9 else 1e9, b / abs(co) if abs(co) > 1e-9 else 1e9,
               (a + b - c - grow * (2 - math.sqrt(2))) / (abs(si) + abs(co))]   # Fasenlinie um grow parallel versetzt
        r = min(lim)
        return (s['x'] + r * si, s['y'] + r * co, s['z'])
    e = 2.0 / s['n']
    x = a * math.copysign(abs(si) ** e, si)
    y = b * math.copysign(abs(co) ** e, co)
    return (s['x'] + x, s['y'] + y, s['z'])


def loft(secs, ring=40, sub=6):
    S = resample(secs, sub)
    V, F = [], []
    for s in S:
        V += [_pt(s, 360.0 * k / ring) for k in range(ring)]
    for i in range(len(S) - 1):
        a, b = i * ring, (i + 1) * ring
        for k in range(ring):
            k2 = (k + 1) % ring
            F.append((a + k, b + k, b + k2, a + k2))
    for idx, s, flip in ((0, S[0], True), (len(S) - 1, S[-1], False)):
        c = len(V)
        V.append((s['x'], s['y'], s['z']))
        base = idx * ring
        for k in range(ring):
            k2 = (k + 1) % ring
            F.append((c, base + k, base + k2) if flip else (c, base + k2, base + k))
    return V, _orient(V, F, S)


def wrap(secs, a0, a1, t, steps=None, sub=6):
    """Platte über der Kontur der Querschnitte (innen = Kontur, außen = Kontur + t). a0/a1 je Querschnitt überschreibbar."""
    secs = [dict(s, a0=s.get('a0', a0), a1=s.get('a1', a1)) for s in secs]
    S = resample(secs, sub)
    closed = abs((a1 - a0) - 360.0) < 1e-6
    n = steps or max(8, int(abs(a1 - a0) / 6))
    cols = n if closed else n + 1
    V, F = [], []
    for s in S:
        for g in (0.0, t):
            V += [_pt(s, s['a0'] + (s['a1'] - s['a0']) * k / n, g) for k in range(cols)]
    row = 2 * cols

    def ix(i, layer, k):
        return i * row + layer * cols + (k % cols)
    for i in range(len(S) - 1):
        for k in range(n):
            F.append((ix(i, 1, k), ix(i + 1, 1, k), ix(i + 1, 1, k + 1), ix(i, 1, k + 1)))   # außen
            F.append((ix(i, 0, k + 1), ix(i + 1, 0, k + 1), ix(i + 1, 0, k), ix(i, 0, k)))   # innen
        if not closed:
            F.append((ix(i, 0, 0), ix(i + 1, 0, 0), ix(i + 1, 1, 0), ix(i, 1, 0)))
            F.append((ix(i, 1, n), ix(i + 1, 1, n), ix(i + 1, 0, n), ix(i, 0, n)))
    for i, flip in ((0, True), (len(S) - 1, False)):
        for k in range(n):
            q = (ix(i, 0, k), ix(i, 0, k + 1), ix(i, 1, k + 1), ix(i, 1, k))
            F.append(q[::-1] if flip else q)
    return V, _orient(V, F, S)


def tube(path, r, segs=14, sub=4):
    """Rohr mit Radius r entlang path [(x, y, z) …]; Ecken weich (Catmull-Rom), Rahmen parallel mitgeführt, Enden geschlossen."""
    P = resample([dict(x=p[0], y=p[1], z=p[2]) for p in path], sub) if len(path) > 2 else [dict(x=p[0], y=p[1], z=p[2]) for p in path]
    P = [(p['x'], p['y'], p['z']) for p in P]

    def sub_(a, b):
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    def norm(v):
        L = math.sqrt(sum(c * c for c in v)) or 1.0
        return (v[0] / L, v[1] / L, v[2] / L)

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    T = [norm(sub_(P[min(i + 1, len(P) - 1)], P[max(i - 1, 0)])) for i in range(len(P))]
    up = (0, 1, 0) if abs(T[0][1]) < 0.9 else (1, 0, 0)
    N = norm(cross(cross(T[0], up), T[0]))
    V, F = [], []
    for i, p in enumerate(P):
        if i:
            B = cross(T[i], N)
            N = norm(cross(B, T[i]))
        B = norm(cross(T[i], N))
        for k in range(segs):
            a = 2 * math.pi * k / segs
            V.append(tuple(p[j] + r * (math.cos(a) * N[j] + math.sin(a) * B[j]) for j in range(3)))
    for i in range(len(P) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            F.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    for i, flip in ((0, True), (len(P) - 1, False)):
        c = len(V)
        V.append(P[i])
        for k in range(segs):
            k2 = (k + 1) % segs
            F.append((c, i * segs + k2, i * segs + k) if flip else (c, i * segs + k, i * segs + k2))
    return V, _orient_tube(V, F)


def _volume(V, F):
    vol = 0.0
    for f in F:
        a = V[f[0]]
        for j in range(1, len(f) - 1):
            b, c = V[f[j]], V[f[j + 1]]
            vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return vol / 6.0


def _orient(V, F, S):
    """Flächen so drehen, dass das Volumen positiv ist (Normalen nach außen), unabhängig von der Laufrichtung in z."""
    return F if _volume(V, F) > 0 else [f[::-1] for f in F]


def _orient_tube(V, F):
    return F if _volume(V, F) > 0 else [f[::-1] for f in F]


def volume(V, F):
    return _volume(V, F)
