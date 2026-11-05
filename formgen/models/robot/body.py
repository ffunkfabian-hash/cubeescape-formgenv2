# Einmalig übertragen aus BALLON Commit 14bd78d (basic/robot/studies/body.py); BALLON bleibt Lesereferenz, keine Laufzeitabhängigkeit.
"""Gemeinsamer Formbaukasten der Roboterstudien (Runde 5): Körper aus Parametern, rund, mit sichtbarer Technik und Glanzpunkten.

Die Studien (a_waechter, b_paladin, c_mechanik) setzen nur Proportionen, Formstil und Technikanteil. Rahmen wie in basic/robot:
Rumpf, Becken und Kopf +Y vorn, +X rechte Körperseite; Bein +Y vorn, +X innen (rechtes Bein ungespiegelt, das linke an X
gespiegelt), Fuß +Z nach vorn, +Y oben. Winkel der Platten (wrap) in Grad um die Segmentachse, 0 = +Y.

Nutzer 27.10.2026, Runde 5: „mehr sichtbare robotische sachen“, „runder“ – und während der Arbeit „Mehr Details, mehr Highlights ;)“.
Glanzpunkte deshalb: blanke Kanten (trim) an Plattenrändern und Gelenken, orange Doppelstreifen der Waffen (accent), kleine
Statuslichter (energy, klein gegen die Augenlinie).
"""
import math

from .rig import frame_axes as _frame
from .shapes import loft, wrap, ring, tab, arrow, two_bolts, medallion, sec


# ------------------------------------------------------------------ Bausteine

def cyl(pid, de, seg, role, axis, r, ln, c):
    return (pid, de, seg, 'cyl', role, dict(axis=axis, r=r, len=ln, c=c))


def tube(pid, de, seg, role, path, r, **kw):
    return (pid, de, seg, 'tube', role, dict(path=path, r=r, **kw))


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def piston(name, de, seg, a, b, r=9.0):
    """Hydraulik von a nach b (mm im Segmentrahmen): dunkler Zylinder, blanke Stange, Manschette am Übergang."""
    return [tube(f'{name}_cyl', de, seg, 'dark_metal', [a, _lerp(a, b, 0.58)], r),
            tube(f'{name}_rod', f'{de} (Stange)', seg, 'trim', [_lerp(a, b, 0.5), b], r * 0.5),
            tube(f'{name}_collar', f'{de} (Manschette)', seg, 'graphite', [_lerp(a, b, 0.53), _lerp(a, b, 0.6)], r * 1.2)]


def cable(name, de, seg, path, r=5.0):
    return [tube(name, de, seg, 'rubber', path, r)]


def joint(name, de, seg, c, r, ln, axis='x'):
    """Sichtbares Gelenk: brünierte Achse, an beiden Enden Medaillon (Scheibe, blanker Ring, Nabe)."""
    return [cyl(f'{name}_axle', de, seg, 'dark_metal', axis, r, ln, c)] + medallion(name, seg, c, r * 0.8, ln + 8, axis)


def light(name, seg, c, axis='y', r=5.0):
    """Statuslicht: kleine leuchtende Linse in blanker Fassung."""
    return [cyl(f'{name}_bezel', 'Lichtfassung', seg, 'trim', axis, r + 2.2, 3.0, c),
            cyl(f'{name}_lamp', 'Statuslicht', seg, 'energy', axis, r, 4.4, c)]


def vstripes(name, seg, secs, mid, w=1.6, gap=2.4, t=1.2):
    """Orange Doppelstreifen der Waffen längs der Querschnitte (Winkel in Grad um mid)."""
    return [wrap(f'{name}_stripe_{k}', 'Akzentstreifen', seg, 'accent', secs, mid + s * gap / 2, mid + s * (gap / 2 + w), t,
                 steps=2, sub=2) for k, s in (('a', -1), ('b', 1))]


def hstripes(name, seg, f, z, grow, a0, a1, h=6.0, gap=5.0, t=1.2):
    """Orange Doppelstreifen quer um die Kontur f (zwei Bänder der Höhe h)."""
    return [wrap(f'{name}_stripe_{k}', 'Akzentstreifen', seg, 'accent', [f(z0, grow), f(z0 + h, grow)], a0, a1, t, sub=1)
            for k, z0 in (('a', z), ('b', z + h + gap))]


def edge(name, seg, s, a0, a1, h=5.0, t=1.4):
    """Blanke Kante: schmales Band der Kontur s (sec) von z bis z + h."""
    return [wrap(f'{name}_edge', 'Zierkante', seg, 'trim', [s, dict(s, z=s['z'] + h)], a0, a1, t, sub=1)]


def surf_y(s, x):
    """Vorderkante (+Y) des Querschnitts s bei x (mm): Superellipse oder gefastes Rechteck (ch)."""
    dx = abs(x - s['x'])
    if s.get('ch'):
        c = min(s['ch'], s['a'] - 0.1, s['b'] - 0.1)
        return s['y'] + s['b'] - max(0.0, dx - (s['a'] - c))
    u = min(dx / s['a'], 0.999)
    return s['y'] + s['b'] * (1 - u ** s['n']) ** (1 / s['n'])


def slot(c, d, rz=0.0, rx=0.0):
    """Fuge oder Schlitz: Quader (mm, Segmentrahmen), per Exact-Boolean aus der Form geschnitten (tools/ego_build.form_mesh)."""
    return dict(c=c, d=d, rz=rz, rx=rx)


def plate(pid, de, seg, role, secs, a0, a1, t, w=2.2, rim_t=1.4, **kw):
    """Platte (wrap) mit blanken Seitenkanten, die dem Umriss folgen – auch dem Pfeilschnitt (Prinzip Q-D1-TITAN: jede Platte
    hat eine helle Kante). w = Kantenbreite in Grad."""
    out = [wrap(pid, de, seg, role, secs, a0, a1, t, **kw)]
    for k, side in (('a', 0), ('b', 1)):
        rs = []
        for s in secs:
            s0, s1 = s.get('a0', a0), s.get('a1', a1)
            ww = min(w, (s1 - s0) / 2)
            rs.append(grow(dict(s, a0=s0, a1=s0 + ww) if side == 0 else dict(s, a0=s1 - ww, a1=s1), t))
        out.append(wrap(f'{pid}_rim_{k}', 'Zierkante', seg, 'trim', rs, a0, a1, rim_t, steps=2, sub=kw.get('sub', 6)))
    return out


def grow(s, g):
    """Querschnitt um g mm vergrößern; bei gefasten Querschnitten wandert die Fase parallel mit."""
    out = dict(s, a=s['a'] + g, b=s['b'] + g)
    if s.get('ch'):
        out['ch'] = s['ch'] + g * (2 - 2 ** 0.5)
    return out


def side_range(sx, span, center=90):
    """Winkelbereich einer Platte auf der Außenseite (rechts +center, links −center; 90° = genau seitlich)."""
    return sx * center - span, sx * center + span


# ------------------------------------------------------------------ Skelett

def frame_point(A, B, hint, local):
    x, y, z = _frame(A, B, hint)
    return tuple(round(A[i] + local[0] * x[i] + local[1] * y[i] + local[2] * z[i], 3) for i in range(3))


def two_bone(A, C, l1, l2, pole):
    """Knie zwischen Hüfte A und Knöchel C (Welt, mm), Beugung zur Polrichtung."""
    d = [C[i] - A[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    if L > l1 + l2:
        raise ValueError(f'Bein zu kurz: {L:.0f} > {l1 + l2:.0f} mm')
    u = [v / L for v in d]
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    pd = sum(pole[i] * u[i] for i in range(3))
    pv = [pole[i] - pd * u[i] for i in range(3)]
    pl = math.sqrt(sum(v * v for v in pv))
    return tuple(round(A[i] + u[i] * x + pv[i] / pl * h, 3) for i in range(3))


def skeleton(S):
    """Skelett einer Studie aus wenigen Maßen: Becken gegen die Schultern geneigt (Kontrapost), Knie per Zwei-Knochen-Lösung.
    S: waist, neck, pelvis, head_h, head_off, torso_hint, head_hint, shoulder, hip_x, hip_z, thigh, shin, foot_h, ankles, toes."""
    W, N, P = S['waist'], S['neck'], S['pelvis']
    out = dict(WAIST=W, NECK=N, PELVIS=P, HEAD_H=S['head_h'], TORSO_HINT=S['torso_hint'], HEAD_HINT=S['head_hint'],
               HEAD_TOP=(N[0] + S['head_off'][0], N[1] + S['head_off'][1], N[2] + S['head_h']), SHOULDER_LOCAL=S['shoulder'],
               FOOT_H=S['foot_h'])
    J = {}
    for side, sx in (('R', 1), ('L', -1)):
        hip = frame_point(P, W, (0, -1, 0), (sx * S['hip_x'], 0, S['hip_z']))
        ank = S['ankles'][side] + (S['foot_h'],)
        knee = two_bone(hip, ank, S['thigh'], S['shin'], S['knee_pole'][side])
        J[side] = (hip, knee, ank, S['toes'][side] + (S['foot_h'],))
    out['JOINTS'] = J
    return out


# ------------------------------------------------------------------ Kopf

def head(P):
    """Hals mit Wirbelring und Kante; der Helm H 80 steht als Flächendaten in helmet_h80.json (BALLONs Helmstudien gehören nicht zu RoboterBasic-01)."""
    return [loft('neck', 'Hals', 'head', 'graphite', [sec(-40, P['neck'], P['neck'], n=2.2), sec(60, P['neck'] - 4, P['neck'] - 4, n=2.2)]),
            ring('neck_ring', 'Wirbelring', 'head', 'dark_metal', 2, 14, P['neck'] + 2, P['neck'] + 2, 6),
            ring('neck_trim', 'Halskante', 'head', 'trim', 16, 19, P['neck'] + 3, P['neck'] + 3, 2.5)]


# ------------------------------------------------------------------ Oberkörper

def torso(P):
    C = tab(P['core'], ch=P.get('core_ch', 0))       # ch > 0: gefaste Querschnitte (Nutzer: „generell alles … zu rund“)
    zc = [r[0] for r in P['core']]
    wa, wb = P['waist']
    SX, SZ = P['SX'], P['SZ']
    out = [loft('waist_core', 'Taillenkern', 'torso', 'graphite', [sec(-50, wa, wb, n=2.4), sec(zc[0] + 40, wa + 8, wb + 6, n=2.4)]),
           loft('torso_core', 'Rumpf', 'torso', 'graphite', [C(z) for z in zc]),
           loft('collar', 'Kragen', 'torso', 'graphite', [sec(*r, n=2.5) for r in P['collar']]),
           ring('collar_trim', 'Kragenkante', 'torso', 'trim', P['collar'][-1][0] - 4, P['collar'][-1][0] - 1,
                P['collar'][-1][1] + 1, P['collar'][-1][2] + 1, 2.0, n=2.5)]
    if P.get('gorget'):            # Halsring um den Kragen, vorn abgesenkt, mit erhöhtem Rand (Q-D1-TITAN)
        zg, ga, gb, tg = P['gorget']
        n1 = len(out)
        gs = [sec(zg, ga, gb, -8, n=2.6), sec(zg + 22, ga - 10, gb - 8, -8, n=2.6)]
        out += [wrap('gorget', 'Halsring', 'torso', 'shell', gs, -180, 180, 10, sub=2)]
        out += edge('gorget', 'torso', sec(zg + 18, ga - 8 + 10.2, gb - 6.5 + 10.2, -8, n=2.6), -180, 180, h=5, t=2.4)
        for q in out[n1:]:
            q[5]['rot'] = ('x', -tg, (0, 0, zg))
    if P.get('bridges'):           # zwei dicke Schulterstege schräg vom Brustansatz nach hinten, oben mit länglicher Vertiefung
        bx, bz, bl, bt = P['bridges']
        for k, sx in (('r', 1), ('l', -1)):
            c = (sx * bx, -6, bz)
            out += [(f'bridge_{k}', 'Schultersteg', 'torso', 'box', 'shell', dict(d=(50, bl, 34), c=c, bevel=5, rot=('x', -bt, c))),
                    (f'bridge_{k}_groove', 'Stegvertiefung', 'torso', 'box', 'graphite',
                     dict(d=(18, bl - 56, 6), c=(c[0], c[1], c[2] + 15.5), bevel=1.5, rot=('x', -bt, c)))]
    # Bauch
    ab = P['abdomen']
    if ab == 'plates':             # Bauchplatten in Lagen (Q-ARMOR-ORANGE), die obere greift über die untere
        out += [wrap('abs_a', 'Bauchplatte', 'torso', 'shell', [C(z, 3.0, a0=-58, a1=58) for z in (zc[0] + 4, zc[0] + 56)], -58, 58, 8),
                wrap('abs_b', 'Bauchplatte', 'torso', 'shell', [C(z, 10.0, a0=-64, a1=64) for z in (zc[0] + 48, zc[0] + 110)], -64, 64, 9)]
        out += edge('abs_a', 'torso', C(zc[0] + 4, 11.3), -58, 58, h=4)
    elif ab == 'vribs':            # schmaler Bauch aus dunklen, senkrecht gerippten Segmenten (Q-D1-TITAN)
        for i, ang in enumerate(range(-60, 61, 20)):
            out += [wrap(f'abs_rib_{i}', 'Bauchrippe', 'torso', 'dark_metal',
                         [sec(-34, wa + 1, wb + 1, n=2.4), sec(zc[0] + 30, wa + 9, wb + 7, n=2.4)], ang - 4, ang + 4, 7, steps=2)]
        out += [ring('waist_trim', 'Taillenkante', 'torso', 'trim', -40, -36, wa + 2, wb + 2, 2)]
    else:                          # offene Taille: Wirbelringe über dem Kern (dunkler Anzug sichtbar)
        for i, z in enumerate(P.get('rings', (-20, 6, 32))):
            out += [ring(f'waist_ring_{i}', 'Wirbelring', 'torso', 'dark_metal', z, z + 14, wa + 5, wb + 5, 5)]
        out += [ring('waist_trim', 'Taillenkante', 'torso', 'trim', P.get('rings', (-20,))[0] - 4, P.get('rings', (-20,))[0] - 1,
                     wa + 7, wb + 7, 2)]
    if ab == 'spine':              # Wirbelsäule vorn als Säule mit Scheiben (Zielbild)
        out += [cyl(f'spine_disc_{i}', 'Wirbelscheibe', 'torso', 'trim', 'z', 18, 4, (0, wb + 8, z)) for i, z in enumerate((-8, 18, 44))]
    if P.get('waist_pistons'):
        for k, sx in (('r', 1), ('l', -1)):
            out += piston(f'waist_piston_{k}', 'Taillenkolben', 'torso', (sx * (wa + 14), 20, -40), (sx * (wa + 34), 24, zc[0] + 80), 10)
    # Brust
    ch = P['chest']
    a0, a1 = ch['a']
    g = 2.0
    if ch.get('split'):            # zwei Brustplatten, dazwischen die Linse (Zielbild)
        for k, (b0, b1) in (('r', (3, a1)), ('l', (a0, -3))):
            out += plate(f'chest_{k}', 'Brustplatte', 'torso', 'shell',
                         [C(z, g, a0=b0, a1=b1) for z in (ch['full'], *ch['mid'])] + [C(ch['top'], g, a0=b0 + (8 if k == 'l' else 0),
                                                                                      a1=b1 - (8 if k == 'r' else 0))], b0, b1, ch['t'])
        zl = (ch['full'] + ch['top']) / 2
        s = C(zl)
        out += medallion('chest_lens', 'torso', (0, s['y'] + s['b'] + 2, zl), 30, 26, axis='y')
        out += light('chest_lens', 'torso', (0, s['y'] + s['b'] + 16, zl), 'y', 9)
    else:
        # Brust nach Q-D1-TITAN: obere Platte breit, flach gewölbt, trapezförmig (oben breit, unten schmaler), oben mittig ein Einschnitt,
        # senkrechte Mittelnaht; darunter eine dunkle, querliegende, facettierte Platte mit nach unten gewölbter Kontur, seitlich zwei
        # helle Rippenplatten wie schräge Klammern
        zb, zt_, t = ch['full'], ch['top'], ch['t']
        nf = 3.2
        cuts = [slot((sx * ch.get('vent_x', 112), surf_y(C(z, g + t), ch.get('vent_x', 112)), z), (46, 26, 3.6), rz=-sx * 12)
                for sx in (1, -1) for z in ch.get('vents', ())]
        cuts += [slot((0, surf_y(C(zt_, g + t, n=nf), 0), zt_), (36, 60, 40)),
                 slot((0, surf_y(C((zb + zt_) / 2, g + t, n=nf), 0), (zb + zt_) / 2), (3.4, 14, zt_ - zb - 40))]
        out += plate('chest', 'Brustplatte', 'torso', 'shell',
                     [C(zb, g, n=nf, a0=a0 + 28, a1=a1 - 28), C(zb + 50, g, n=nf, a0=a0 + 12, a1=a1 - 12)]
                     + [C(z, g, n=nf) for z in ch['mid'] if z > zb + 60] + [C(zt_, g, n=nf, a0=a0 + 4, a1=a1 - 4)], a0, a1, t, cuts=cuts, sharp=28)
        if ch.get('emblem'):       # Brustemblem mit Licht
            ze = zb + 0.42 * (zt_ - zb)
            s = C(ze, g + t, n=nf)
            out += medallion('emblem', 'torso', (0, s['y'] + s['b'] + 2, ze), 24, 12, axis='y')
            out += light('emblem', 'torso', (0, s['y'] + s['b'] + 9, ze), 'y', 8)
        gs = g + 4
        out += plate('solar', 'Sonnenplatte', 'torso', 'anodized',
                     [C(zb - 74, gs, n=4, a0=-24, a1=24), C(zb - 40, gs, n=4, a0=-44, a1=44), C(zb + 14, gs, n=4, a0=-54, a1=54)],
                     -54, 54, 9, sharp=25)
        out += two_bolts('solar', 'torso', C, zb - 30, gs + 9 + 2, dx=22)
        for k, sx in (('r', 1), ('l', -1)):
            def lo(u0, u1, sx=sx):
                return dict(a0=u0, a1=u1) if sx > 0 else dict(a0=-u1, a1=-u0)
            out += plate(f'rib_{k}', 'Rippenplatte', 'torso', 'shell',
                         [C(zb - 86, g + 2, **lo(46, 60)), C(zb - 30, g + 2, **lo(54, 74)), C(zb + 18, g + 2, **lo(62, 84))],
                         *lo(46, 60).values(), 8)
        if P.get('lights'):
            for k, sx in (('r', 1), ('l', -1)):
                s = C(zb + 40, g + t, n=nf)
                out += light(f'chest_light_{k}', 'torso', (sx * 62, surf_y(s, 62) + 1, zb + 40), 'y', 3.6)
    out += hstripes('chest', 'torso', C, ch['stripe'], g + ch['t'], ch['a'][0] + 22, ch['a'][0] + 44) if ch.get('stripe') else []
    # Rücken
    bk = P['back']
    out += plate('back', 'Rückenplatte', 'torso', 'shell', [C(z, g, a0=168, a1=192) for z in (bk['z'][0],)]
                 + [C(z, g) for z in bk['z'][1:]], 126, 234, 9) if bk['kind'] != 'spine' else []
    if bk['kind'] == 'pack':       # Rückenmodul mit zwei Düsen (Q-ARMOR-ORANGE)
        y0 = bk['y']
        out += [loft('backpack', 'Rückenmodul', 'torso', 'graphite', [sec(z, a, b, y=y0 + dy, n=2.8) for z, a, b, dy in bk['rows']]),
                wrap('backpack_shell', 'Rückenmodulschale', 'torso', 'shell',
                     [grow(sec(z, a, b, y=y0 + dy, n=2.8), 1.5) for z, a, b, dy in bk['rows'][1:-1]], 140, 220, 7)]
        for k, sx in (('r', 1), ('l', -1)):
            c = (sx * bk['nozzle_x'], y0 - 12, bk['rows'][0][0] - 26)
            out += [cyl(f'nozzle_{k}', 'Düse', 'torso', 'dark_metal', 'z', 26, 64, c),
                    cyl(f'nozzle_{k}_trim', 'Düsenkante', 'torso', 'trim', 'z', 28, 6, (c[0], c[1], c[2] - 30)),
                    cyl(f'nozzle_{k}_core', 'Düsenkern', 'torso', 'anodized', 'z', 17, 70, c)]
            out += cable(f'pack_cable_{k}', 'Leitung', 'torso',
                         [(sx * (bk['nozzle_x'] + 40), y0 + 20, bk['rows'][-1][0] - 20), (sx * (SX - 70), y0 + 40, SZ + 40),
                          (sx * (SX - 100), -20, SZ + 70)], 6)
        out += light('backpack', 'torso', (0, y0 - bk['rows'][2][2] - 9, bk['rows'][2][0]), 'y', 4.5)
    elif bk['kind'] == 'spine':    # offene Wirbelsäule mit zwei Schulterblattplatten (Zielbild)
        sb = C(200)
        yb = sb['y'] - sb['b']
        out += [tube('spine', 'Wirbelsäule', 'torso', 'dark_metal', [(0, yb - 4, -40), (0, yb - 10, 200), (0, yb - 4, zc[-1])], 14)]
        out += [ring(f'vertebra_{i}', 'Wirbel', 'torso', 'trim', z, z + 6, 20, 20, 3) for i, z in enumerate(range(10, 380, 46))]
        for k, (b0, b1) in (('r', (128, 172)), ('l', (188, 232))):
            out += [wrap(f'blade_{k}', 'Schulterblattplatte', 'torso', 'shell', [C(z, g) for z in (210, 290, 360)], b0, b1, 8)]
    # Schultern: Gelenk, runder Panzer (greift über Rumpf und Oberarm), Lagen, Medaillon, Glanzkante, Streifen
    pd = P['pauldron']
    for k, sx in (('r', 1), ('l', -1)):
        out += joint(f'shoulder_{k}', 'Schultergelenk', 'torso', (sx * (SX - 50), -4, SZ), P['joint_r'], 116)
        n0 = len(out)
        pch = pd.get('ch', 0)      # ch > 0: kantiger Panzer mit Fasen (Q-D1-TITAN)
        rows = [sec(z, a, b, y, x=sx * (SX + dx), n=pd.get('n', 2.6), ch=min(pch, 0.45 * a)) for z, a, b, y, dx in pd['rows']]
        lam = [slot((r['x'] + sx * r['a'], r['y'], z), (30, 2 * r['b'] + 60, 3.6))
                for z in pd.get('grooves', ()) for r in [[q for q in rows if q['z'] <= z][-1]]]
        out += [loft(f'pauldron_{k}', 'Schulterpanzer', 'torso', 'shell', rows, sharp=28 if pch else 60, cuts=lam)]
        out += edge(f'pauldron_{k}', 'torso', grow(rows[0], 0.4), -180, 180, h=5, t=1.6)
        if pd.get('stripes'):      # Doppelstreifen vorn außen auf dem Panzer
            m = 90 - pd.get('stripe_span', 34)
            for j, (u0, u1) in (('a', (m, m + 5)), ('b', (m + 9, m + 14))):
                b0, b1 = (u0, u1) if sx > 0 else (-u1, -u0)
                out += [wrap(f'pauldron_{k}_stripe_{j}', 'Akzentstreifen', 'torso', 'accent', [grow(r, 0.2) for r in rows[1:3]], b0, b1,
                             1.2, sub=2, steps=2)]
        if pd.get('panel'):        # aufgesetzte Platte vorn außen mit blanker Kante (Prinzip Q-D1-TITAN, Emblemplatte)
            z0, z1, span = pd['panel']
            q0, q1 = side_range(sx, span, pd.get('panel_center', 62))
            ps = [grow(dict(r, z=z), 0.5) for z in (z0, (z0 + z1) / 2, z1) for r in [[q for q in rows if q['z'] <= z][-1]]]
            ps = [dict(r, a=r['a'] - (2 if i == 2 else 0)) for i, r in enumerate(ps)]
            out += plate(f'pauldron_{k}_panel', 'Schulterplatte', 'torso', 'shell', ps, q0, q1, 5)
        for fk, span in (('flare', pd.get('flare_span', 120)), ('flare2', pd.get('flare_span', 120) - 26)):
            if not pd.get(fk):     # Lagen unter dem Rand, zum Oberarm hin schmaler (Q-D1-TITAN)
                continue
            fr = [sec(z, a, b, y, x=sx * (SX + dx), n=pd.get('n', 2.6), ch=min(pch, 0.45 * a)) for z, a, b, y, dx in pd[fk]]
            f0, f1 = side_range(sx, span)
            out += plate(f'pauldron_{k}_{fk}', 'Schulterlage', 'torso', 'shell', fr, f0, f1, 9)
            out += edge(f'pauldron_{k}_{fk}', 'torso', grow(fr[0], 9.2), f0, f1, h=4, t=1.4)
        if pd.get('band'):
            zb = pd['band']
            sb = [r for r in rows if r['z'] <= zb][-1]
            out += [wrap(f'pauldron_{k}_band', 'Panzerfuge', 'torso', 'graphite', [dict(grow(sb, -0.5), z=zb), dict(grow(sb, -0.5), z=zb + 6)],
                         -180, 180, 2.0, sub=1)]
        mz = pd['med'][0]
        mr = [r for r in rows if r['z'] <= mz][-1]
        out += medallion(f'shoulder_{k}_med', 'torso', (mr['x'] + sx * (mr['a'] - 4), mr['y'], mz), pd['med'][1], 22)
        for q in out[n0:]:         # Panzer schräg: außen tiefer, innen unter den Kragen (Prinzip Q-D1-TITAN), Drehpunkt Schulter
            q[5]['rot'] = ('y', sx * pd.get('tilt', 0), (sx * SX, 0, SZ))
        if P.get('shoulder_pistons'):
            out += piston(f'shoulder_piston_{k}', 'Schulterkolben', 'torso', (sx * 96, -96, 250), (sx * (SX - 36), -64, SZ + 12), 9)
    return out


# ------------------------------------------------------------------ Unterkörper

def pelvis(P):
    PL = tab(P['pel'], ch=P.get('pel_ch', 0))
    zs = [r[0] for r in P['pel']]
    bz0, bz1, ba, bb = P['belt']
    out = [loft('pelvis_core', 'Becken', 'pelvis', 'graphite', [PL(z) for z in zs]),
           ring('belt', 'Gürtelring', 'pelvis', 'dark_metal', bz0, bz1, ba, bb, 8, n=2.8),
           ring('belt_trim', 'Gürtelkante', 'pelvis', 'trim', bz1 - 3, bz1, ba + 8.5, bb + 8.5, 1.6, n=2.8)]
    # Schrittstück: dunkler Kern läuft zwischen den Beinen nach unten, die Oberschenkel setzen seitlich mit der Hüftkugel an
    p0 = PL(0)
    out += [loft('brief', 'Schrittstück', 'pelvis', 'graphite', [sec(-96, 34, 40, 8), sec(-52, 60, 60, 4),
                                                                 sec(0, p0['a'] * 0.72, p0['b'] * 0.92, p0['y'])])]
    zm = (bz0 + bz1) / 2               # flache, rechteckige Schließe
    out += [('buckle', 'Schließe', 'pelvis', 'box', 'trim', dict(d=(74, 12, 32), c=(0, bb + 12, zm), bevel=2)),
            ('buckle_inset', 'Schließenfeld', 'pelvis', 'box', 'graphite', dict(d=(56, 14, 18), c=(0, bb + 13, zm), bevel=1))]
    ft = P['front']
    zq = ft['tip'] + 0.24 * (ft['full'] - ft['tip'])  # Beckenschutz nach unten verjüngt, Ende abgerundet
    out += plate('tasset', 'Lendenplatte', 'pelvis', 'shell',
                 [PL(ft['tip'], 2.0, a0=-ft['a'] * 0.3, a1=ft['a'] * 0.3), PL(zq, 2.0, a0=-ft['a'] * 0.66, a1=ft['a'] * 0.66),
                  PL(ft['full'], 2.0, a0=-ft['a'], a1=ft['a']), PL(bz0 - 10, 2.0, a0=-ft['a'] - 4, a1=ft['a'] + 4)], -ft['a'], ft['a'], 9)
    out += vstripes('tasset', 'pelvis', [PL(z, 11.0) for z in (ft['full'] - 10, ft['full'] + 40, bz0 - 14)], 0, w=1.6, gap=3.0)
    sd = P['side']
    for k, sx in (('r', 1), ('l', -1)):
        rows = [sec(z, a, b, y, n=2.6) for z, a, b, y in sd['rows']]
        a0, a1 = side_range(sx, sd['span'], sd.get('center', 64))
        out += plate(f'tasset_side_{k}', 'Beintasche', 'pelvis', 'shell', rows, a0, a1, 9)
        out += edge(f'tasset_side_{k}', 'pelvis', grow(rows[0], 9.2), a0, a1, h=4)
        if sd.get('layer'):        # zweite, kürzere Lage über der ersten
            r2 = [grow(r, 11) for r in rows[1:]]
            b0, b1 = side_range(sx, sd['span'] - 6, sd.get('center', 64))
            out += [wrap(f'tasset_side_{k}_top', 'Beintasche oben', 'pelvis', 'shell', r2, b0, b1, 8)]
            out += edge(f'tasset_side_{k}_top', 'pelvis', grow(r2[0], 8.2), b0, b1, h=4)
        out += joint(f'hip_{k}', 'Hüftgelenk', 'pelvis', (sx * P['hip_x'], 0, P['hip_z']), P['hip_r'], P.get('hip_len', 92))
        if P.get('belt_boxes'):
            c = (sx * (ba - 20), -bb + 6, (bz0 + bz1) / 2 - 6)
            bx = [sec(z, 30, 20, c[1] - 12, c[0], n=3.0) for z in (c[2] - 34, c[2] + 26)]
            out += [loft(f'belt_box_{k}', 'Gürtelmodul', 'pelvis', 'graphite', bx),
                    wrap(f'belt_box_{k}_trim', 'Modulkante', 'pelvis', 'trim', [dict(bx[1], z=c[2] + 18), dict(bx[1], z=c[2] + 22)],
                         -180, 180, 1.2, sub=1)]
    if P.get('butt'):
        out += [wrap('butt', 'Gesäßplatte', 'pelvis', 'shell', [PL(z, 2.0) for z in (-30, 40, bz0 - 8)], 144, 216, 8)]
    return out


# ------------------------------------------------------------------ Beine

def legs(P):
    T, S, F = (tab(P['thigh'], ch=P.get('thigh_ch', 0)), tab(P['shin'], ch=P.get('shin_ch', 0)),
               tab(P['foot'], ch=P.get('foot_ch', 14)))   # gefast (Nutzer: „zu rund“; Zehenkappe Q-D1-TITAN)
    LT, LS, FH = P['LT'], P['LS'], P['foot_h']
    ta0, ta1 = P['thigh_shell']
    hr = P.get('hip_ball', T(0)['a'] * 0.9)          # Hüftkugel: der Oberschenkel setzt rund an, nicht flach abgeschnitten
    zt = P.get('thigh_top', 150)                       # Schale beginnt unter der Beintasche, Hüfte dunkel und offen
    out = [loft('hip_ball', 'Hüftkugel', 'thigh', 'dark_metal', [sec(z * hr, r * hr, r * hr, n=2.0) for z, r in
                                                                 ((-0.92, 0.39), (-0.6, 0.8), (0, 1), (0.6, 0.8), (0.92, 0.39))]),
           loft('thigh_core', 'Oberschenkel', 'thigh', 'graphite', [T(z) for z in (20, 100, 240, LT)]),
           wrap('thigh_cuff', 'Hüftmanschette', 'thigh', 'dark_metal', [T(36, 1.0), T(60, 1.0)], -180, 180, 6, sub=1),
           wrap('thigh_cuff_trim', 'Manschettenkante', 'thigh', 'trim', [T(60, 1.5), T(63, 1.5)], -180, 180, 2.0, sub=1),
           ]
    # Schale nach Q-D1-TITAN: hoch ansetzend mit gerundeter Oberkante, leicht eingezogenen Seiten und kantigem unteren Abschluss
    tm = (ta0 + ta1) / 2
    out += plate('thigh_shell', 'Oberschenkelschale', 'thigh', 'shell',
                 [T(zt - 16, 2.0, a0=tm - 14, a1=tm + 14), T(zt + 8, 2.0, a0=ta0 + 14, a1=ta1 - 14), T(zt + 60, 2.0),
                  T(220, 2.0, a0=ta0 + 7, a1=ta1 - 7), T(LT - 84, 2.0), T(LT - 46, 2.0, a0=ta0 + 24, a1=ta1 - 24)], ta0, ta1, 9)
    out += vstripes('thigh', 'thigh', [T(z, 11.0) for z in (zt + 30, 190, 250)], ta0 + 16, w=1.8, gap=3.0)
    for i, z in enumerate(P.get('thigh_seams', ())):      # Fugen quer über die Schale
        out += [wrap(f'thigh_seam_{i}', 'Fuge', 'thigh', 'graphite', [T(z, 10.6), T(z + 4, 10.6)], ta0 + 2, ta1 - 2, 1.4, sub=1)]
    if P.get('thigh_piston'):     # Kolben außen hinten vom Becken zum Knie
        out += piston('thigh_piston', 'Oberschenkelkolben', 'thigh', (-T(60)['a'] - 4, -T(60)['b'] * 0.55, 30),
                      (-T(LT - 60)['a'] - 2, -T(LT - 60)['b'] * 0.5, LT - 40), 10)
    if P.get('thigh_cable'):
        out += cable('thigh_cable', 'Leitung', 'thigh', [(T(40)['a'] * 0.5, -T(40)['b'] - 4, 20), (T(200)['a'] * 0.6, -T(200)['b'] - 8, 200),
                                                         (T(LT)['a'] * 0.4, -T(LT)['b'] - 6, LT - 20)], 5)
    # Knie
    kr = P['knee_r']
    out += joint('knee', 'Kniegelenk', 'shin', (0, 0, 0), kr, P.get('knee_len', 136))
    kc = P['kneecap']
    kb = max(b for _, _, b in kc[1:])  # Knieschale längs geteilt (Q-D1-TITAN)
    kch = P.get('knee_ch', 0)
    out += [wrap('knee_cap', 'Kniekappe', 'shin', 'shell',
                 [sec(kc[0][0], kc[0][1], kc[0][2], n=2.4, ch=min(kch, 0.4 * kc[0][1]), a0=-8, a1=8)]
                 + [sec(z, a, b, n=2.4, ch=kch) for z, a, b in kc[1:]], -62, 62, 11,
                 cuts=[slot((0, kb + 11, (kc[1][0] + kc[-1][0]) / 2), (3.4, 16, kc[-1][0] - kc[1][0] + 30))])]
    out += edge('knee_cap', 'shin', grow(sec(kc[-1][0] - 5, kc[-1][1], kc[-1][2], n=2.4, ch=kch), 11.2), -62, 62, h=4)
    if P.get('knee_pistons'):      # Kolben in der Kniekehle
        for k, dx in (('a', -26), ('b', 26)):
            out += piston(f'knee_piston_{k}', 'Kniekolben', 'shin', (dx, -T(LT - 120)['b'] - 4, -150), (dx * 0.8, -S(140)['b'] - 6, 140), 8)
    # Schienbein
    sa0, sa1 = P['shin_shell']
    out += [loft('shin_core', 'Schienbein', 'shin', 'graphite', [S(z) for z in (30, 140, 290, LS)]),
            ]
    # Schienbein nach Q-D1-TITAN: breiter oberer Abschluss, schmale Knöchelzone, erhöhte Seitenränder, kantiger Ausschnitt über dem Fuß
    out += plate('shin_shell', 'Schienbeinschale', 'shin', 'shell',
                 [S(64, 2.0, a0=sa0 + 6, a1=sa1 - 6), S(110, 2.0), S(230, 2.0, a0=sa0 + 8, a1=sa1 - 8), S(LS - 40, 2.0, a0=sa0 + 16, a1=sa1 - 16)],
                 sa0, sa1, 9, rim_t=3.2, cuts=[slot((0, surf_y(S(LS - 40, 11.0), 0), LS - 40), (40, 74, 74), rz=90, rx=45)])
    out += [
            wrap('shin_plate', 'Schienbeinlage', 'shin', 'anodized',
                 arrow(S, 196, 166, -18, 18, 11.0, tip=1.5)[::-1] + [S(z, 11.0) for z in (226, 256)], -18, 18, 2.5, steps=8)]
    out += two_bolts('shin', 'shin', S, 240, 14.5, dx=11, r=3.6)
    if P.get('lights'):
        s = S(150, 11.0)
        out += light('shin_light', 'shin', (0, s['y'] + s['b'] + 1.5, 150), 'y', 3.2)
    if P.get('calf'):
        out += [wrap('calf', 'Wadenplatte', 'shin', 'shell', [S(z, 2.0) for z in (90, 170, 250)], 140, 220, 8)]
    if P.get('calf_piston'):       # Kolben als Achillessehne
        out += piston('calf_piston', 'Wadenkolben', 'shin', (0, -S(60)['b'] - 8, 50), (0, -S(LS)['b'] - 10, LS + 20), 9)
    if P.get('ankle_pistons'):
        for k, sx in (('a', 1), ('b', -1)):
            out += piston(f'ankle_piston_{k}', 'Knöchelkolben', 'shin', (sx * (S(LS - 170)['a'] + 6), 0, LS - 180),
                          (sx * (S(LS - 30)['a'] + 4), 4, LS - 24), 7)
    out += [wrap('boot_cuff', 'Stiefelschaft', 'shin', 'shell', [S(z, 3.0) for z in (LS - 72, LS - 38, LS - 6)], 40, 320, 9)]
    out += edge('boot_cuff', 'shin', S(LS - 74, 12.2), 40, 320, h=4)
    # Fuß
    out += joint('ankle', 'Knöchel', 'foot', (0, 0, 0), P['ankle_r'], P.get('ankle_len', 122))
    fz = [r[0] for r in P['foot']]
    out += [loft('foot_core', 'Fuß', 'foot', 'graphite', [F(z) for z in fz]),
            wrap('toe_cap', 'Zehenkappe', 'foot', 'shell',
                 arrow(F, fz[2] + 6, fz[2] - 34, -82, 82, 2.0, tip=5)[::-1] + [F(z, 2.0) for z in (fz[3], fz[-1] + 2)], -82, 82, 8),
            wrap('heel_cap', 'Fersenkappe', 'foot', 'shell', [F(z, 2.0) for z in (fz[0] - 4, fz[0] + 30, fz[0] + 60)], 70, 290, 8),
            loft('sole', 'Sohle', 'foot', 'rubber', [sec(fz[0] - 6, F(fz[0])['a'] + 2, 6, -FH + 6, n=4),
                                                     sec(fz[-1] + 8, F(fz[-1])['a'], 6, -FH + 6, n=4)], sub=1)]
    out += edge('toe_cap', 'foot', dict(F(fz[-1] - 30, 10.2), a0=-82, a1=82), -82, 82, h=4)
    return out


# ------------------------------------------------------------------ Oberarm (Abwandlung am Roboter, Arm v3 bleibt für die Ego-Ansicht)

def upper_arm(P):
    """Runder Oberarm statt der gefasten v3-Hülle: Graphitkörper, Schale außen mit Pfeilschnitt zum Ellbogen, Fuge, Schulterkugel.
    Segment upper (Arm v3): Ursprung Schulter, +Z zum Ellbogen, +Y Außenseite."""
    out = [loft('shoulder_ball', 'Schulterkugel', 'upper', 'dark_metal', [sec(z, r, r, n=2.0) for z, r in
                                                                           ((-44, 8), (-30, 40), (0, P['ball']), (30, 40), (44, 8))])]
    if not P.get('rows'):          # Oberarm v3 bleibt, nur die Kugel kommt dazu
        return out
    U = tab(P['rows'], ch=P.get('ch', 0))
    out += [loft('upper_core', 'Oberarmkörper', 'upper', 'graphite', [U(z) for z in (10, 150, 290)])]
    if P.get('shell'):
        s0, s1 = P['shell']
        out += [wrap('upper_shell_r', 'Oberarmschale', 'upper', 'shell',
                     [U(60, 2.0, a0=s0 + 14, a1=s1 - 14), U(150, 2.0)] + arrow(U, 230, 280, s0, s1, 2.0, tip=5), s0, s1, 8)]
        out += vstripes('upper', 'upper', [U(z, 10.0) for z in (90, 150, 200)], 0, w=1.6, gap=3.0)
    out += [wrap('upper_seam', 'Oberarmfuge', 'upper', 'trim', [U(40, 0.5), U(44, 0.5)], -180, 180, 1.4, sub=1)]
    if P.get('piston'):
        out += piston('biceps_piston', 'Armkolben', 'upper', (U(40)['a'] + 6, 0, 30), (U(260)['a'] + 4, 0, 300), 8)
    return out
