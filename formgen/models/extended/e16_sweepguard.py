"""EXTENDED-16 „Sweepguard“ – eigenständiges Sci-Fi-Schwert der BASIC-Familie (Formgen v2 0.20 „Riftguard“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-16: aus `basic.common` kommen nur Formhelfer (`part`, `prof`, `box`, `cyl`, `cut_box`, `screws`, `mirror`) und die Radienstufen.
Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal: Schwung. Einschneidige Säbelklinge, deren Rücken auf einem Bogen steigt (58 mm Stich auf 730 mm), mit Rückenabsatz
  (Clip) zur Spitze; der Creme-Korbbügel unter dem Griff nimmt denselben Schwung zurück zum Knauf auf. Einhandgriff, Klinge dominiert
  (79 % der Länge).
- Querschnitt: dreistufig geschichtet statt Fase – Creme-Rückenschiene 11 mm, Klingenkörper 7 mm, blanke Schneide 3 mm; je Seite 2 mm
  Stufe (Familienschichtung 2–3 mm). Kein Hohlschliff, kein Fuller.
- Negativraum: der Handraum zwischen Griff und Korbbügel (lichte Höhe ≈ 37 mm), aus jeder Seitenansicht offen.
- Zweiton: Creme (Parierblock, Bügel, Knaufkragen, Rückenschiene) umschließt als Rahmen die dunkle Hand (Gummigriff, Graphitfuß,
  eloxierter Klingenschuh); Klinge metallisch.
- Blickfang (genau einer): Ladebogen links – drei Leuchtsegmente auf einem Kreisbogen im eloxierten Paneel, konzentrisch zum Bügel.
- Grafik: ein schräges Orange-Band über der Rückenschiene, parallel zur Schuhkante; eine Schrift rechts auf dem Paneel.
- Front mehrstufig: Spitze, Schneidenstufe, Klingenschuh mit Schrägkante, Parierblock mit Daumenrampe, Bügel darunter, Knauf.
- Ergonomie: Socket_Hand mittig auf dem Griff (Einhand, 112 mm), Daumenrampe mit Ladeschalter (einzige Orange-Bedienfunktion),
  Knaufkragen als Anlage für die zweite Hand beim beidhändigen Hieb (Socket_SupportHand).
- Kein Visier, kein Magazin, kein Hülsenauswurf, keine Ego-Griffe (wie BASIC-16, Formgen v1 `wtypes.MELEE`).

Herkunft der Zahlen: V = Vorgabe (BASIC-16 bzw. Familie/Stilhandbuch), A = Annahme (Entwurf 0.20), G = gemessen; Zahlen ohne Kennung
sind A (Entwurf 0.20, an den Renders r1–r3 gesichtet).
Maße mm; f nach vorn (Klinge), u nach oben (Rücken), x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import part, prof, box, cyl, cut_box, screws, mirror, R_BODY, R_MID, R_SMALL, R_FINE

META = dict(id='EXTENDED-16', num='E16', sheet_id='EA16', type='sword', type_de='Schwert', type_en='Sword', family='BASIC',
            name='Sweepguard', nick='Bogenwacht', ammo='heavy', fire='melee',
            reference_length_m=1.04, reference_length_source='A: Entwurf 0.20 (BASIC-16 1,10 m als Rahmen, V; Einhand kürzer)',
            inspired_by='BASIC-16 Familie; Säbel mit Korbbügel als Haltung',
            summary='Einhand-Säbel mit geschwungener Schichtklinge, Creme-Korbbügel und Ladebogen (EXTENDED-Reihe).')
ASSEMBLIES = [   # V: Baugruppen wie BASIC-16 (assemblies('blade', 'guard', 'grip_controls'))
    dict(id='blade', de='Klinge', en='Blade'),
    dict(id='guard', de='Parierblock', en='Guard'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
]

F_GRIP = (-56, 56)      # A: Einhandgriff 112 mm (BASIC-16 Zweihand 194 mm, V)
F_GUARD = (56, 122)     # A: Parierblock
F_ROOT = 104            # A: Klingenwurzel im Parierblock
F0, FC, FT = 122, 852, 918   # A: Klinge frei ab Parierblock, Rückenabsatz (Clip), Spitze
RISE = 54               # A: Stich des Rückens bis FC
K = RISE / (FC - F0) ** 2
H0, H1 = 52.0, 40.0     # A (Runde 2, r1 44/34 zu schmal): Klingenhöhe an der Wurzel / am Clip (BASIC-16 50 mm, V)
TIP = (FT, 62.0)        # A: Spitze unter der Rückenlinie (Clip fällt 17 mm)
HALF_G = 19.0           # A: halbe Breite Parierblock (BASIC-16 46 mm, V)
W_RAIL, W_BODY, W_EDGE = 11.0, 7.0, 3.0   # A: Stufen 2 mm je Seite (V: Familienschichtung 2–3 mm)


def spine(f):
    """A: Rückenlinie, Bogen ab der Wurzel (Stich RISE bei FC); vor FC fällt der Clip gerade zur Spitze."""
    if f <= FC:
        return 25.0 + K * (max(f, F0) - F0) ** 2
    s = spine(FC)
    return s + (TIP[1] - s) * (f - FC) / (FT - FC)


def edge(f):
    """A: Schneidenlinie; bis FC um die Klingenhöhe unter dem Rücken, danach konvex zur Spitze (Tangente stetig)."""
    if f <= FC:
        return spine(f) - (H0 + (H1 - H0) * (max(f, F0) - F0) / (FC - F0))
    e = edge(FC)
    slope = 2 * K * (FC - F0) + (H0 - H1) / (FC - F0)
    c = (TIP[1] - e - slope * (FT - FC)) / (FT - FC) ** 2
    return e + slope * (f - FC) + c * (f - FC) ** 2


def fade(f):
    """1 bis FC, dann linear auf 0 an der Spitze (Stufenhöhen laufen in die Spitze)."""
    return 1.0 if f <= FC else (FT - f) / (FT - FC)


def stations(f0, f1, n):
    return [f0 + (f1 - f0) * i / n for i in range(n + 1)]


ALONG = stations(F_ROOT, FC, 28) + stations(FC, FT, 6)[1:]


def band(curve, thick):
    """Seitenprofil eines Bandes der Dicke thick (mm) um eine Mittellinie [(f, u) …] (Normalen je Punkt)."""
    left, right = [], []
    for i, (f, u) in enumerate(curve):
        a, b = curve[max(i - 1, 0)], curve[min(i + 1, len(curve) - 1)]
        df, du = b[0] - a[0], b[1] - a[1]
        n = (df * df + du * du) ** 0.5
        nf, nu = -du / n * thick / 2, df / n * thick / 2
        left.append((f + nf, u + nu))
        right.append((f - nf, u - nu))
    return left + right[::-1]


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


# Klingenkörper: oben der Rücken (bzw. Clip), unten über der Schneidenstufe (die Schneide trägt die unterste Stufe)
EDGE_H = 12.0           # A (Runde 2): Schneidenstufe 12 mm hoch (r1: 8 mm, im Render nicht lesbar)
BODY = [(f, spine(f)) for f in ALONG] + [(f, edge(f) + (EDGE_H - 1) * fade(f)) for f in ALONG[::-1] if f < FT]
EDGE = [(f, edge(f) + EDGE_H * fade(f)) for f in ALONG] + [(f, edge(f)) for f in ALONG[::-1] if f < FT]
F_RAIL = 792            # A: Rückenschiene endet vor dem Clip, Ende schräg wie die Schuhkante
RAIL_H = 10.0
RAIL_ALONG = [f for f in ALONG if f <= F_RAIL - 20] + [F_RAIL]
RAIL = [(f, spine(f)) for f in RAIL_ALONG] + [(F_RAIL - 20, spine(F_RAIL - 20) - RAIL_H)] + [
    (f, spine(f) - RAIL_H) for f in RAIL_ALONG[::-1] if f < F_RAIL - 20]
SHOE_F, SHOE_LEAN = (110, 190), 22   # A: Klingenschuh, Vorderkante schräg (oben 22 mm weiter vorn)
SHOE = [(SHOE_F[0], spine(SHOE_F[0]) + 2.5)] + [(f, spine(f) + 2.5) for f in stations(SHOE_F[0], SHOE_F[1], 6)[1:]] + [
    (SHOE_F[1] - SHOE_LEAN, edge(SHOE_F[1] - SHOE_LEAN) - 2.5), (SHOE_F[0], edge(SHOE_F[0]) - 2.5)]

# Parierblock (Runde 2): Seitenprofil als Schwung statt Würfel – hinten oben die Daumenrampe, Front nach unten vorgeneigt wie die
# Schuhkante, Unterkante läuft in den Bügelfuß. Zweiton: Creme oben, Graphitfuß unten (Fuge 1 mm bei u SEAM_U).
SEAM_U = -12.0          # A: Teilung Creme/Graphit am Parierblock ≈ 64:36
GUARD_OUT = [(58, -22), (58, 40), (72, 43), (90, 37), (118, 31), (127, -30), (122, -42), (104, -50), (80, -46), (62, -34)]


def clip_u(poly, u_cut, keep_above):
    """Polygon (f, u) an der Waagerechten u_cut beschneiden (Sutherland–Hodgman, eine Kante)."""
    out = []
    inside = (lambda q: q[1] >= u_cut) if keep_above else (lambda q: q[1] <= u_cut)
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            t = (u_cut - a[1]) / (b[1] - a[1])
            out.append((a[0] + t * (b[0] - a[0]), u_cut))
    return out


GUARD = clip_u(GUARD_OUT, SEAM_U + 0.5, True)
FOOT = clip_u(GUARD_OUT, SEAM_U - 0.5, False)

# Korbbügel: kubische Bézier vom Graphitfuß unter dem Griff zurück zum Knaufkragen, 13 mm stark (Seite), 16 mm breit
BOW_LINE = bezier((108, -40), (96, -74), (-72, -76), (-90, -16))
BOW = band(BOW_LINE, 13.0)

# Ladebogen: drei Segmente auf einem Kreisbogen, r 9–13, je 30° mit 6° Fuge, im Paneel des Creme-Oberteils
ARC_C, ARC_R = (92.0, 8.0), (10.5, 16.0)   # A (Runde 3, r2 r 9–13 zu klein)


def sector(a0, a1, n=6, r=ARC_R):
    """Kreisringsektor a0..a1 (Grad, 0 = nach vorn, 90 = nach oben) mit Radien r um ARC_C."""
    def at(rad, a):
        return (ARC_C[0] + rad * math.cos(math.radians(a)), ARC_C[1] + rad * math.sin(math.radians(a)))
    return [at(r[1], a0 + (a1 - a0) * i / n) for i in range(n + 1)] + [at(r[0], a1 - (a1 - a0) * i / n) for i in range(n + 1)]


ARCS = [sector(a, a + 30) for a in (57, 93, 129)]
PANEL = [(72, -6), (112, -6), (111, 24), (90, 28), (74, 30)]   # A (Runde 3): Paneel kleiner, 8–10 mm Creme-Rand bleibt sichtbar
MULDE = [(70, -8), (114, -8), (113, 26), (90, 30), (72, 32)]

P = []
# ---------------------------------------------------------------- Klinge
_BAND_F, _LEAN = 214, 1.2   # A: Zierband schräg (1,2 mm vor je mm Höhe), über Rückenschiene und Klingenkörper
P += [
    prof('blade', 'Klingenkörper', 'Blade body', 'blade', 'metal', 'Tragende Säbelklinge; mittlere Stufe (7 mm)',
         'Angel im Parierblock vernietet, Klingenschuh klemmt', BODY, W_BODY, bevel=R_FINE),
    prof('blade_edge', 'Schneide', 'Edge', 'blade', 'trim', 'Blanke Schneide; unterste Stufe (3 mm), läuft in die Spitze',
         'mit dem Klingenkörper verbunden', EDGE, W_EDGE, bevel=0.5),
    prof('spine_rail', 'Rückenschiene', 'Spine rail', 'blade', 'shell', 'Versteift den Rücken; oberste Stufe (11 mm), Creme',
         'auf den Klingenrücken geklebt und im Schuh gefasst', RAIL, W_RAIL, bevel=R_SMALL),
    prof('blade_shoe', 'Klingenschuh', 'Blade shoe', 'blade', 'anodized', 'Klemmt die Klinge im Parierblock; Schrägkante',
         'vorn auf den Parierblock geschraubt', SHOE, 13.0, bevel=R_SMALL),
    part('shoe_screws', 'Schuhschrauben', 'Shoe screws', 'blade', 'multi', 'trim', 'Halten den Klingenschuh', 'im Schuh',
         bevel=0.2, items=mirror(screws([(136, 14), (136, -14), (160, 16), (160, -12)], 6.6, r=1.5, h=0.6))),
    part('spine_band', 'Zierband', 'Accent band', 'blade', 'multi', 'accent',
         'Lackiertes Schrägband über Rückenschiene und Klingenkörper (einziges Grafikelement)', 'lackiert, beidseitig', bevel=0,
         items=[dict(shape='prof', pts=[(_BAND_F, s0 - RAIL_H - 0.5), (_BAND_F + 7, s0 - RAIL_H - 0.5),
                                         (_BAND_F + 7 + _LEAN * (RAIL_H + 1), s0 + 0.4), (_BAND_F + _LEAN * (RAIL_H + 1), s0 + 0.4)],
                     w=0.6, x=sx * (W_RAIL / 2 + 0.05)) for sx in (1, -1) for s0 in (spine(_BAND_F),)]
         + [dict(shape='prof', pts=[(_BAND_F - _LEAN * 14, s0 - RAIL_H - 14), (_BAND_F + 7 - _LEAN * 14, s0 - RAIL_H - 14),
                                    (_BAND_F + 7, s0 - RAIL_H + 0.5), (_BAND_F, s0 - RAIL_H + 0.5)],
                 w=0.6, x=sx * (W_BODY / 2 + 0.05)) for sx in (1, -1) for s0 in (spine(_BAND_F),)]),
]
# ---------------------------------------------------------------- Parierblock
P += [
    prof('guard', 'Parierblock', 'Guard block', 'guard', 'shell', 'Fasst die Klinge, schützt die Hand, trägt die Ladung',
         'auf die Angel geschoben, auf den Bügelfuß geschraubt (Fuge)', GUARD, 2 * HALF_G, bevel=R_BODY,
         cuts=[dict(shape='prof', pts=MULDE, w=3.0, x=sx * (HALF_G + 0.6)) for sx in (1, -1)]
         + [cut_box(64, 80, 38, 48, 11)]),    # Schalterbahn in der Daumenrampe
    prof('guard_foot', 'Bügelfuß', 'Bow foot', 'guard', 'graphite', 'Unterteil des Parierblocks; trägt den Korbbügel',
         'unter den Parierblock geschraubt, Fuge 1 mm', FOOT, 2 * HALF_G - 2, bevel=R_MID),
    prof('guard_panel_l', 'Paneel links', 'Side panel left', 'guard', 'anodized', 'Deckel über der Ladeelektronik; trägt den Ladebogen',
         'in die Mulde geschraubt (4 Schrauben)', PANEL, 1.2, bevel=R_FINE, x=HALF_G - 0.8),
    prof('guard_panel_r', 'Paneel rechts', 'Side panel right', 'guard', 'anodized', 'Deckel über der Ladeelektronik',
         'in die Mulde geschraubt (4 Schrauben)', PANEL, 1.2, bevel=R_FINE, x=-HALF_G + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'guard', 'multi', 'trim', 'Halten die Paneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(76, -2), (76, 26), (108, -2), (108, 22)], HALF_G - 0.2, r=1.4, h=0.7))),
    part('charge_arc', 'Ladebogen', 'Charge arc', 'guard', 'multi', 'energy',
         'Drei Leuchtsegmente zeigen die Ladungen für schwere Hiebe (Blickfang)', 'im linken Paneel', bevel=0,
         items=[dict(shape='prof', pts=a, w=0.8, x=HALF_G - 0.2 + 0.4) for a in ARCS],
         move=dict(kind='glow', pivot=None, event='charge', max=5.0)),
    part('arc_frame', 'Ladebogen-Fassung', 'Charge arc bezel', 'guard', 'multi', 'trim', 'Blanke Fassung des Ladebogens',
         'auf das linke Paneel geschraubt', bevel=0.2,
         items=[dict(shape='prof', pts=sector(52, 164, 14, r=(8.5, 18.0)), w=0.6, x=HALF_G - 0.2 + 0.1)]),
    box('charge_switch', 'Ladeschalter', 'Charge switch', 'grip_controls', 'accent', 'Löst den geladenen Hieb aus (Daumen)',
        'in der Schalterbahn der Daumenrampe geführt', 66, 74, 40, 45.5, 9, bevel=R_FINE,
        move=dict(kind='translate', pivot=(70, 42, 0), vector_mm=(6, 0, 0), event='charge')),
    # A: rechts auf dem Paneel, linksbündig nach vorn: 0,62 × 4 × 12 ≈ 30 mm ab f 76 → bis 106 (Paneel 68–114 bei u 0–4)
    part('text_r', 'Schriftzug', 'Lettering', 'guard', 'text', 'decal', 'Kennung „BASIC EX-16“ (einzige Schrift)', 'aufgedruckt',
         bevel=0, text='BASIC  EX-16', size=4.0, f=76, u=-1, x=-HALF_G + 0.8 - 0.65, side=-1, depth=0.12),
]
# ---------------------------------------------------------------- Griff, Bügel, Knauf
P += [
    # A (Runde 3, r2 als Vierkant gelesen): runder Kegelgriff, zum Parierblock 1,5 mm dicker, Wickelrillen im Takt 20 mm
    cyl('grip', 'Griff', 'Grip', 'grip_controls', 'rubber', 'Einhandgriff, zum Parierblock leicht kegelig; trägt Socket_Hand',
        'auf die Angel geschoben, zwischen Parierblock und Knaufkragen', 'f', (0, 0), F_GRIP[0] - 4, F_GUARD[0] + 4, 14.0, r1=15.5, segs=24,
        bevel=R_SMALL, cuts=[dict(shape='cyl', axis='f', c=(0, 0), a0=f, a1=f + 2.2, r=20, r_in=13.6, segs=24)
                             for f in (-40, -20, 0, 20, 40)]),
    prof('bow', 'Korbbügel', 'Knuckle bow', 'guard', 'shell', 'Schützt die Finger; nimmt den Schwung der Klinge auf',
         'im Bügelfuß und im Knaufkragen verschraubt', BOW, 16, bevel=R_MID),
    prof('pommel_collar', 'Knaufkragen', 'Pommel collar', 'grip_controls', 'shell', 'Fasst Griffende und Bügel; Anlage zweite Hand',
         'auf die Angel geschraubt',   # A (Runde 4, r3 klobig): flacher, Rückkante oben schräg wie die Schuhkante
         [(-100, -14), (-90, -25), (-66, -23), (-58, -15), (-58, 15), (-64, 18), (-88, 18)], 28, bevel=R_MID),
    cyl('pommel', 'Knauf', 'Pommel', 'grip_controls', 'dark_metal', 'Gegengewicht, sichert die Angel', 'auf die Angel geschraubt',
        'f', (0, 0), -116, -98, 15, r1=17, segs=24, bevel=R_MID),
    cyl('pommel_nut', 'Angelmutter', 'Tang nut', 'grip_controls', 'trim', 'Blanker Abschluss der Angel', 'Griffende',
        'f', (0, 0), -121, -115, 8.5, segs=24, bevel=0.6),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand mittig auf dem Einhandgriff'),
    'Socket_SupportHand': dict(at=(-80, 0, 0), part='pommel_collar', note='zweite Hand am Knaufkragen (beidhändiger Hieb)'),
    'Socket_Muzzle': dict(at=(TIP[0], TIP[1], 0), part='blade', note='Klingenspitze (Formgen-Konvention wie BASIC-16)'),
    'Socket_BladeCenter': dict(at=(540, (spine(540) + edge(540)) / 2, 0), part='blade', note='Trefferzentrum'),
}
EGO_GRIPS = {}      # V: Nahkampf ohne Ego-Übertrag (wie BASIC-16)
POINTS = {}
ACTIONS = {
    'guard_charge': dict(de='Blocken: Ladebogen zieht Energie', frames=30, step=2, keys={
        'charge_arc': [(0, 1), (6, 0.3), (24, 0.3), (30, 1)]}, events=[(6, 'block_start'), (24, 'block_end')],
        view=(0.75, -0.3, 0.6)),
    'heavy_release': dict(de='Geladenen Hieb auslösen', frames=20, step=1, keys={
        'charge_switch': [(0, 0), (3, 1), (10, 1), (14, 0)], 'charge_arc': [(0, 1), (4, 1), (12, 0.2), (20, 1)]},
        events=[(4, 'heavy_strike')]),
}
EXPLODE = {'blade': (170, 0, 0), 'guard': (60, 0, 0), 'grip_controls': (-60, 0, 0)}
HERO = (0.62, -0.42, 0.66)   # A: von links vorn oben – Ladebogen (Blickfang) und Bügel zur Kamera
