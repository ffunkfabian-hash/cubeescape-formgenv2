"""ZERO-01 „Crosshair“ – eigenständiges Sci-Fi-Automatikgewehr der BASIC-Familie (Formgen v2 0.46 „Zero“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-01 oder EXTENDED-01: aus
`basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H0 auf Schiene BRI-22, Magazin BMW-R,
Feuerwahlhebel, Ladehebel-Form, Schraubenköpfe) und Hilfen (`rot`, `cut_box`, `mirror`). Geladen über `formgen.extended`
(Kurzname `z01`), gerendert mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py z01`).

Formsprache (Auswahl und Skizzen: docs/zero.md)
- Leitmerkmal Nullrahmen: Das Gehäuse ist ein geschlossener, liegender Achteckrahmen (312 × 104 mm, 62 breit), quer ganz offen. Durch seine Mitte
  läuft die Laufachse: hinten der Verschluss, vorn die leuchtende Kammer. Von unten steigt die Zuführsäule aus dem Magazinschacht, von oben
  hält ein Steg die Kammerschelle – Achse, Säule und Steg bilden im Rahmen ein Fadenkreuz („nullen“ = einschießen). Der Rahmen ist
  zugleich Auswurföffnung (rechts) und Sichtfenster auf die Mechanik.
- Silhouette Arm – Rahmen – Arm: die einzige Masse ist der hohe Rahmen; davor ein schlanker Handschutz mit 45°-Stufe, dahinter ein
  L-Schaft: Creme-Keilbalken über Graphit-Fersenkeil mit 45°-Innenfase. Der Rahmen steht in Draufsicht und Front 10–13 mm je Seite über die Arme,
  seine senkrechten Ecken sind 45° gefast.
- Querschnitte: Rahmenbügel, Haube (vor und hinter der Stufe), Schaft und Kappenfuß mit 45°-Einzügen (4–6 mm), Unterteile je Seite
  1 mm schmaler als die Oberteile.
- Zweiton: Creme oben (Rahmenbügel, Haube, Schaft, Magazin) über Graphit unten (Rahmenwanne, Handschutz-Unterteil); die Fuge liegt
  am Rahmen in den Pfosten (u 90), am Handschutz auf u 104.
- Blickfang (genau einer): die Kammer – ein Leuchtrohr unter Glas zwischen Kammerschelle und vorderer Kappe, von beiden Seiten durch
  den Rahmen sichtbar.
- Grafik: ein Chevronpaar (Akzent) an der Handschutzwurzel, nach vorn zeigend; eine Schrift rechts auf der Haubenflanke.
- Front mehrstufig: Haubennase mit Fase → blanke Laufbuchse → freier, kannelierter Lauf → achtkantiger Kompensator mit Seitenfenstern →
  blanke Krone; dahinter steht der Rahmen als zweite, größere Kontur.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0) unter der Rahmenwanne, Stützhand am Handschutz vor dem Handstopp, Ladehebel links am
  Rahmenbügel, Magazinhalter links an der Wanne; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-01 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.46),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.46, an Rasterskizzen und Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          reflex_sight_v21, rifle_mag, R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='ZERO-01', num='Z01', sheet_id='ZA01', type='auto_rifle', type_de='Automatikgewehr', type_en='Auto Rifle',
            family='BASIC', name='Crosshair', nick='Nullrahmen', ammo='primary', fire='full_auto',
            reference_length_m=0.886, reference_length_source='G: Hülle des Datensatzes 0.46 (BASIC-01 0,92 m, EXTENDED-01 0,90 m als Rahmen, V)',
            inspired_by='BASIC-01 und EXTENDED-01 (Familie); Formgen v1 Black Ice KJ02 (Schaft und Facetten als Haltung), '
                        'Werkstatt-Serie H (sichtbare Konstruktion), Nadel KF08 (Lauf frei im Rahmen)',
            summary='Automatikgewehr mit offenem Nullrahmen-Gehäuse: Verschluss, Leuchtkammer und Zuführsäule bilden ein Fadenkreuz '
                    '(ZERO-Reihe).')
ASSEMBLIES = [
    dict(id='receiver', de='Hauptgehäuse', en='Receiver'),
    dict(id='barrel', de='Lauf', en='Barrel'),
    dict(id='ammo', de='Munitionsversorgung', en='Ammunition feed'),
    dict(id='sight', de='Visier', en='Sight'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
    dict(id='support', de='Stützbereich', en='Support'),
    dict(id='stock', de='Schaft', en='Stock'),
    dict(id='mechanism', de='Bewegliche Mechanik', en='Moving mechanism'),
]

BORE = 106                    # V: Laufachse wie BASIC-01 (gleiche Griff-Lauf-Geometrie der Familie)
TOP = 146                     # A: Oberkante Rahmen = Unterkante Schiene; Visierlinie TOP + 8 + 26 = 180 → 74 über der Laufachse (Vertrag 60–80,
                              #    Familienband bis 74)
BASE = 42                     # V: Unterkante Gehäuse wie BASIC-01 (Griffoberkante BGM-1, Abzugsbügel)
F0, F1 = -60, 252             # A: Rahmen hinten / vorn (312 mm); Runde 4: 40 mm nach vorn, Fadenkreuz mittig in der Öffnung
HALF = 31.0                   # A: halbe Rahmenbreite (62; Arme 42/36 – Runde 4: der Rahmen steht in Draufsicht und Front deutlich heraus)
SPLIT = 90                    # A: Zweiton-Fuge in den Pfosten
C_OUT, C_IN = 22, 16          # A: 45°-Fasen außen / an der Öffnung
OPEN = (-26, 218, 64, 132)    # A: Öffnung f0, f1, u0, u1 – Pfosten 34 mm, Bügel 14 mm, Wanne 22 mm
H0, H1 = F1, 436              # A: Handschutz hinten (am Rahmen) / Nase
HG_TOP, HG_SPLIT, HG_LOW = 134, 104, 76   # A: Haube oben, Fuge, Unterkante Handschutz
HG_HALF = 21.0                # A: halbe Haubenbreite (Unterteil 20)
S0 = -290                     # A: Schaftende (Kappe hinten, vor dem Polster)
CROSS_F = (92, 112)           # A: Fadenkreuz am hinteren Kammerende (Zuführstelle über dem Magazin) – Steg, Säule und Schelle auf f 102,
                              #    Öffnungsmitte f 96


def octo(f0, f1, u0, u1, c, grow=0.0):
    """Achteck mit 45°-Fasen c (gegen den Uhrzeigersinn); grow vergrößert gleichmäßig (Rahmenkante, Schnitt)."""
    f0, f1, u0, u1 = f0 - grow, f1 + grow, u0 - grow, u1 + grow
    c = c + grow * 0.414
    return [(f0 + c, u0), (f1 - c, u0), (f1, u0 + c), (f1, u1 - c), (f1 - c, u1), (f0 + c, u1), (f0, u1 - c), (f0, u0 + c)]


def chamfer(f0, f1, u, half, d, up=True):
    """Fasen-Einzug an beiden Oberkanten (up) bzw. Unterkanten einer Fläche in Höhe u: xprof-Schneidkörper, 45°, Tiefe d."""
    s = 1 if up else -1
    return [dict(shape='xprof', f0=f0, f1=f1, cu=0, pts=[(sx * (half - d), u + s), (sx * (half + 2), u + s), (sx * (half + 2), u - s * (d + 2))])
            for sx in (1, -1)]


def corners(f0, f1, half, c, u0, u1):
    """45°-Fasen an den vier senkrechten Ecken (Draufsicht) als plan-Schneidkörper, Kantenlänge c."""
    out = []
    for f, sf in ((f0, -1), (f1, 1)):
        for sx in (1, -1):
            pts = [(f - sf * c, sx * (half + 2)), (f + sf * 2, sx * (half + 2)), (f + sf * 2, sx * (half - c))]
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
            out.append(dict(shape='plan', pts=pts if area < 0 else pts[::-1], u0=u0, u1=u1))   # im Uhrzeigersinn
    return out


def ring(inner, outer, w, x):
    """Achteckring als acht Viereck-Leisten (Seitenprofile) zwischen zwei gleichlaufenden Achtecken; ohne Bool, Fläche ehrlich messbar."""
    n = len(inner)
    return [dict(shape='prof', pts=[inner[i], inner[(i + 1) % n], outer[(i + 1) % n], outer[i]], w=w, x=x) for i in range(n)]


OPENING = octo(*OPEN, C_IN)
OPEN_CUT = dict(shape='prof', pts=OPENING, w=80)
P = []
# ---------------------------------------------------------------- Nullrahmen
P += [
    prof('frame_top', 'Rahmenbügel', 'Frame bow', 'receiver', 'shell',
         'Oberer Rahmen: trägt Schiene, Visier und Kammersteg; Pfosten führen Verschluss und Lauf',
         'mit der Rahmenwanne in beiden Pfosten verschraubt (Fuge u 90, zwei Querbolzen)',
         [(F0, SPLIT), (F1, SPLIT), (F1, TOP - C_OUT), (F1 - C_OUT, TOP), (F0 + 14, TOP), (F0, TOP - 14)], 2 * HALF,
         cuts=[OPEN_CUT] + chamfer(F0, F1, TOP, HALF, 8) + corners(F0, F1, HALF, 10, SPLIT - 2, TOP + 2)
         + [cut_box(150, 226, 134, 144, 10, x=HALF)]),                                 # Ladehebel-Nut links
    prof('frame_low', 'Rahmenwanne', 'Frame cradle', 'receiver', 'graphite',
         'Unterer Rahmen: Abzugsgruppe, Magazinschacht, Zuführsäule',
         'unter dem Rahmenbügel; Magazintrichter angeformt',
         [(F0, SPLIT), (F0, BASE + 22), (F0 + 22, BASE), (70, BASE), (78, 30), (82, 20), (142, 20), (148, 30), (176, BASE),
          (F1 - 14, BASE), (F1, BASE + 14), (F1, SPLIT)], 2 * HALF - 2,
         cuts=[OPEN_CUT] + chamfer(F0, F1, BASE, HALF - 1, 7, up=False) + corners(F0, F1, HALF - 1, 10, BASE - 2, SPLIT + 2)
         + [cut_box(-60, 40, 46, 60, 3.0, x=sx * (HALF - 0.4)) for sx in (1, -1)]),   # Paneelmulden der Wanne
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazintrichters',
         'unten am Trichter der Rahmenwanne', [(81, 17.5), (143, 17.5), (144, 21), (80, 21)], 2 * HALF - 1, bevel=0.6, iface='BMW-R'),
    part('frame_edge_l', 'Rahmenkante links', 'Frame edge left', 'receiver', 'multi', 'trim',
         'Blanke Kante der Öffnung aus acht Leisten; fasst das Fadenkreuz', 'um die Öffnung geschraubt', bevel=0.6,
         items=ring(OPENING, octo(*OPEN, C_IN, grow=4.0), 1.8, HALF + 0.5)),
    part('frame_edge_r', 'Rahmenkante rechts', 'Frame edge right', 'receiver', 'multi', 'trim',
         'Blanke Kante der Öffnung (Auswurfseite)', 'um die Öffnung geschraubt', bevel=0.6,
         items=ring(OPENING, octo(*OPEN, C_IN, grow=4.0), 1.8, -HALF - 0.5)),
    part('edge_screws', 'Kantenschrauben', 'Edge screws', 'receiver', 'multi', 'dark_metal', 'Halten die Rahmenkante', 'in der Rahmenkante',
         bevel=0.2, items=mirror(screws([(0, 61.5), (190, 61.5), (0, 134.2), (190, 134.2)], HALF + 1.4, r=1.1, h=0.5))),
    box('cradle_panel_l', 'Wannenpaneel links', 'Cradle panel left', 'receiver', 'anodized', 'Wartungsdeckel der Abzugsgruppe',
        'in die Wannenmulde geschraubt (4 Schrauben)', -58, 38, 47.5, 59, 1.2, bevel=R_FINE, x=HALF - 2.2),
    box('cradle_panel_r', 'Wannenpaneel rechts', 'Cradle panel right', 'receiver', 'anodized', 'Wartungsdeckel der Abzugsgruppe',
        'in die Wannenmulde geschraubt (4 Schrauben)', -58, 38, 47.5, 59, 1.2, bevel=R_FINE, x=-HALF + 2.2),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Wannenpaneele',
         'in den Paneelen', bevel=0.2,
         items=mirror(screws([(-53, 50.5), (-53, 56), (33, 50.5), (33, 56)], HALF - 1.6, r=1.3, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Rahmenbügel und Wanne in den Pfosten',
         'quer durch die Pfosten (lösbar)', bevel=0.4, items=mirror(screws([(F0 + 17, 78), (F1 - 17, 78)], HALF - 0.6, r=4.0, h=1.0))),
    prof('chamber_cover', 'Kammerdeckel', 'Chamber cover', 'receiver', 'shell', 'Deckt den Bügel über der Kammer; zweite Schicht',
         'auf den Rahmenbügel geschraubt, Stufe 2,5 mm', [(120, TOP - 1), (216, TOP - 1), (216, TOP + 0.5), (212, TOP + 2.5), (124, TOP + 2.5),
                                                          (120, TOP + 0.5)], 40, bevel=R_FINE),
    part('cover_screws', 'Deckelschrauben', 'Cover screws', 'receiver', 'multi', 'trim', 'Halten den Kammerdeckel', 'im Kammerdeckel',
         bevel=0.2, items=[dict(shape='cyl', axis='u', c=(f, x), a0=TOP + 2, a1=TOP + 3, r=1.5, segs=12) for f in (130, 206) for x in (13, -13)]),
    box('counter_bezel', 'Anzeigenrahmen', 'Counter bezel', 'stock', 'anodized', 'Fasst die Munitionsanzeige (unter dem Auge)',
        'auf den Schaftbalken vor die Wange geschraubt', -96, -72, 139.6, 141.6, 18, bevel=0.6),
    box('ammo_counter', 'Munitionsanzeige', 'Ammo counter', 'stock', 'energy', 'Füllstand, im Blick beim Zielen; klein, damit die Kammer Blickfang bleibt',
        'im Anzeigenrahmen', -93, -75, 141.2, 142.0, 10, bevel=0.2),
    part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
         'Druckknopf links an der Wanne', bevel=R_FINE, axis='x', c=(66, 52), a0=HALF - 2, a1=HALF + 2.5, r=5, segs=20,
         move=dict(kind='translate', pivot=(66, 52, HALF), vector_mm=(0, 0, -2.5), event='reload')),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC ZR-01“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  ZR-01', size=5.0, f=312, u=113, x=-HG_HALF - 0.05, side=-1, depth=0.12),
]
# ---------------------------------------------------------------- Fadenkreuz: Verschluss, Kammer, Säule, Steg
P += [
    cyl('bolt_carrier', 'Verschlussträger', 'Bolt carrier', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss in den Pfosten zurück',
        'im hinteren Pfosten geführt', 'f', (BORE, 0), F0 + 12, 82, 12.0, segs=24, bevel=R_SMALL,
        cuts=[cut_box(-10, 70, BORE - 2, BORE + 2, 6, x=sx * 12) for sx in (1, -1)],
        move=dict(kind='translate', pivot=(40, BORE, 0), vector_mm=(-42, 0, 0), event='fire')),
    box('bolt_lug', 'Spannnase', 'Bolt lug', 'mechanism', 'dark_metal', 'Nimmt den Ladehebel mit; zeigt den Verschlussweg',
        'oben auf dem Verschlussträger', 28, 54, BORE + 9, BORE + 17, 10, bevel=R_FINE, parent_part='bolt_carrier'),
    cyl('bolt_head', 'Verschlusskopf', 'Bolt head', 'mechanism', 'trim', 'Verriegelt an der Kammer; blanke Stirn',
        'vorn am Verschlussträger', 'f', (BORE, 0), 82, CROSS_F[0], 10.5, segs=24, bevel=0.5, parent_part='bolt_carrier'),
    cyl('chamber', 'Leuchtkammer', 'Glow chamber', 'receiver', 'energy', 'Beschleunigerkammer, leuchtet im Feuer (Blickfang)',
        'zwischen Kammerschelle und vorderer Kappe', 'f', (BORE, 0), CROSS_F[1] - 2, OPEN[1] - 8, 11.0, segs=24, bevel=0),
    cyl('chamber_glass', 'Kammerglas', 'Chamber glass', 'receiver', 'glass', 'Schützt die Kammer', 'zwischen Schelle und vorderer Kappe',
        'f', (BORE, 0), CROSS_F[1] - 2, OPEN[1] - 8, 12.5, r_in=11.5, segs=24, bevel=0),
    cyl('bolt_bushing', 'Führungsbuchse', 'Bolt bushing', 'mechanism', 'dark_metal', 'Führt den Verschluss im hinteren Pfosten',
        'in den hinteren Pfosten geschraubt', 'f', (BORE, 0), OPEN[0] - 6, OPEN[0] + 8, 16, segs=24, bevel=R_FINE,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=OPEN[0] + 3, a1=OPEN[0] + 5, r=17, r_in=14.6, segs=24)]),
    cyl('cap_front', 'Kammerkappe vorn', 'Chamber cap front', 'receiver', 'dark_metal', 'Fasst die Kammer am vorderen Pfosten',
        'in den vorderen Pfosten geschraubt', 'f', (BORE, 0), OPEN[1] - 10, OPEN[1] + 2, 16, segs=24, bevel=R_FINE),
    cyl('chamber_clamp', 'Kammerschelle', 'Chamber clamp', 'receiver', 'anodized', 'Mitte des Fadenkreuzes und Verschlusssitz; hält Kammer, Säule und Steg',
        'um die Kammer geklemmt', 'f', (BORE, 0), CROSS_F[0], CROSS_F[1], 15, segs=24, bevel=R_FINE,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=CROSS_F[0] + 9, a1=CROSS_F[0] + 11, r=17, r_in=14.2, segs=24)]),
    prof('feed_column', 'Zuführsäule', 'Feed column', 'ammo', 'metal',
         'Führt die Patrone vom Magazin in die Kammer (unterer Fadenkreuzarm, blank); Fenster zeigt sie',
         'steigt als Trichter aus dem Wannenboden über dem Magazinschacht, oben an der Kammerschelle',
         [(78, OPEN[2] - 1), (130, OPEN[2] - 1), (122, 84), (CROSS_F[1], 96), (CROSS_F[0], 96), (86, 84)], 30, bevel=R_SMALL,
         cuts=[cut_box(92, 116, 70, 84, 8, x=sx * 15) for sx in (1, -1)]),
    part('feed_round', 'Patrone in der Säule', 'Feeding round', 'ammo', 'multi', 'brass', 'Zeigt die nächste Patrone im Säulenfenster',
         'in der Zuführsäule', bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(77, sx * 9.5), a0=88, a1=120, r=4.4, segs=12) for sx in (1, -1)]),
    prof('floor_plate', 'Bodenblech', 'Floor plate', 'mechanism', 'dark_metal', 'Verschlussbahn und Auswurframpe auf dem Wannenboden',
         'in die Wanne geschraubt, vor der Säule', [(OPEN[0] + 4, OPEN[2] - 1), (CROSS_F[0] - 12, OPEN[2] - 1), (CROSS_F[0] - 12, OPEN[2] + 3),
                                                   (CROSS_F[0] - 30, OPEN[2] + 7), (OPEN[0] + 18, OPEN[2] + 7), (OPEN[0] + 4, OPEN[2] + 3)], 40,
         bevel=R_FINE, cuts=[cut_box(OPEN[0] + 24, CROSS_F[0] - 36, OPEN[2] + 4, OPEN[2] + 8, 4, x=sx * 9) for sx in (1, -1)]),
    box('cross_web', 'Kammersteg', 'Chamber web', 'receiver', 'metal', 'Hängt die Kammerschelle am Rahmenbügel (oberer Fadenkreuzarm, blank)',
        'zwischen Rahmenbügel und Kammerschelle', CROSS_F[0], CROSS_F[1], BORE + 12, OPEN[3] + 1, 20, bevel=R_FINE),
]
# ---------------------------------------------------------------- Schiene und Visier (Familienschnittstelle BRI-22 / H0)
P += [dict(p, mat='anodized') for p in rail(-48, 72, TOP)]
P[-1]['cuts'] = [cut_box(-42 + 12 * i, -36 + 12 * i, TOP + 4, TOP + 9, 30) for i in range(9)]
_sight, SIGHT_ANCHORS = reflex_sight_v21(-20, TOP + 8)
P += _sight
# ---------------------------------------------------------------- Handschutz (vorderer Arm)
HG_STEP = 360                 # A: 45°-Stufe der Haube (vorn 8 mm tiefer, wiederholt die Rahmenfasen)
_hg_top = [(H0, HG_SPLIT), (H1, HG_SPLIT), (H1, 112), (H1 - 14, HG_TOP - 8), (HG_STEP + 8, HG_TOP - 8), (HG_STEP, HG_TOP), (H0, HG_TOP)]
P += [
    prof('hg_top', 'Handschutzhaube', 'Handguard hood', 'support', 'shell', 'Haube über Lauf und Gasweg; trägt Chevrons und Schrift',
         'in den vorderen Rahmenpfosten gesteckt, zwei Schrauben', _hg_top, 2 * HG_HALF, bevel=R_SMALL,
         cuts=chamfer(H0, HG_STEP + 4, HG_TOP, HG_HALF, 6) + chamfer(HG_STEP, H1 + 2, HG_TOP - 8, HG_HALF, 6)),
    prof('hg_low', 'Handschutz', 'Handguard', 'support', 'graphite', 'Griffbereich der Stützhand; Handstopp vorn',
         'unter der Haube, am Rahmenpfosten verschraubt, Fuge',
         [(H0, HG_SPLIT), (H0, HG_LOW + 6), (H0 + 10, HG_LOW), (396, HG_LOW), (404, 66), (418, 66), (H1, 84), (H1, HG_SPLIT)],
         2 * HG_HALF - 2, bevel=R_MID, cuts=chamfer(H0, H1 + 2, HG_LOW, HG_HALF - 1, 4, up=False)
         + [cut_box(H0 + 12, 392, 84, 98, 3.0, x=sx * (HG_HALF - 0.4)) for sx in (1, -1)]),
    box('hg_vent_l', 'Kühlleiste links', 'Cooling strip left', 'support', 'dark_metal', 'Führt Laufwärme seitlich ab',
        'in die Handschutzmulde gesetzt', H0 + 14, 390, 86, 96, 1.2, bevel=R_FINE, x=HG_HALF - 2.2,
        cuts=[cut_box(H0 + 24, 380, 89, 93, 3, x=HG_HALF - 2.2)]),
    box('hg_vent_r', 'Kühlleiste rechts', 'Cooling strip right', 'support', 'dark_metal', 'Führt Laufwärme seitlich ab',
        'in die Handschutzmulde gesetzt', H0 + 14, 390, 86, 96, 1.2, bevel=R_FINE, x=-HG_HALF + 2.2,
        cuts=[cut_box(H0 + 24, 380, 89, 93, 3, x=-HG_HALF + 2.2)]),
    prof('hg_pad', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand', 'unten auf den Handschutz geklebt',
         [(H0 + 16, HG_LOW - 3), (392, HG_LOW - 3), (392, HG_LOW + 3), (H0 + 16, HG_LOW + 3)], 30, bevel=R_SMALL),
    part('hg_screws', 'Handschutzschrauben', 'Handguard screws', 'support', 'multi', 'trim', 'Halten Haube und Handschutz am Rahmen',
         'seitlich', bevel=0.2, items=mirror(screws([(H0 + 12, 92), (H0 + 12, 120)], HG_HALF - 1.0, r=1.8, h=0.8))),
    box('hg_step', 'Haubenstufe', 'Hood step', 'support', 'shell', 'Stufe über der Nase; Leitlinie nach vorn',
        'auf die Haube geschraubt, Stufe 2,5 mm', H0 + 24, HG_STEP - 8, HG_TOP - 1, HG_TOP + 2.5, 18, bevel=R_FINE),
    part('chevron', 'Chevronband', 'Chevron band', 'support', 'multi', 'accent', 'Lackiertes Chevronpaar (einziges Grafikelement)',
         'lackiert, beidseitig an der Haubenwurzel', bevel=0,
         items=[dict(shape='prof', pts=[(f, 106), (f + 8, 106), (f + 18, 116), (f + 8, 126), (f, 126), (f + 10, 116)],
                     w=0.6, x=sx * (HG_HALF + 0.05)) for f in (H0 + 20, H0 + 36) for sx in (1, -1)]),
]
# ---------------------------------------------------------------- Lauf und Mündung
P += [
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; kanneliert', 'im vorderen Rahmenpfosten verschraubt',
        'f', (BORE, 0), OPEN[1] - 2, 528, 10, segs=24,
        cuts=[cut_box(450, 512, BORE - 1.5, BORE + 1.5, 4, x=sx * 10) for sx in (1, -1)]
        + [cut_box(450, 512, BORE + 8.6, BORE + 12, 3), cut_box(450, 512, BORE - 12, BORE - 8.6, 3)]),
    cyl('nose_bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf in der Haubennase; blanke Stufe',
        'in die Nase gepresst', 'f', (BORE, 0), H1 - 4, H1 + 6, 13, r_in=10.2, segs=24, bevel=0.5),
    cyl('muzzle', 'Kompensator', 'Compensator', 'barrel', 'anodized', 'Achtkant-Mündungsteil mit Seitenfenstern; Socket_Muzzle',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), 520, 578, 16.5, r_in=5.5, segs=8, bevel=R_SMALL, iface='BMZ-15',
        cuts=[cut_box(538, 566, BORE - 6, BORE + 6, 44)]
        + [cut_box(540, 564, BORE + 7, BORE + 22, 8)]
        + [dict(shape='cyl', axis='f', c=(BORE, 0), a0=524 + 4 * i, a1=525.6 + 4 * i, r=18.5, r_in=15.6, segs=8) for i in range(2)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn am Kompensator',
        'f', (BORE, 0), 576, 584, 15, r_in=6, segs=8, bevel=0.6),
]
# ---------------------------------------------------------------- Griff und Bedienung (Familienschnittstelle BGM-1)
P += grip_v21(top=BASE)
P += selector(-46, 52, x=HALF + 0.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF - 0.5) for p in selector(-46, 52)]
P += charging_handle(194, 139, x=HALF + 0.5, travel=40)
# ---------------------------------------------------------------- Magazin: gerade, 10° nach vorn geneigt, Fenster, Bodenplatte mit Kante
_mc, _tilt = (108, 72), 10      # V: Neigung 10° wie EXTENDED-01 (Familie), Magazin vor dem Bügel
_m = rifle_mag(88, 72, depth=40, length=144, tilt=_tilt, w=24)
for p in _m:
    if p['id'] == 'magazine':
        p['pts'] = rot([(88, 72), (128, 72), (130, 10), (131, -62), (91, -62), (89, 10)], _mc, _tilt)
        p['de'], p['func'] = 'Magazin', 'Hält die Patronen; gerade, nach vorn geneigt; entnehmbar'
        p['cuts'] = ([dict(shape='prof', pts=rot([(98, uu), (124, uu), (124, uu + 2.2), (98, uu + 2.2)], _mc, _tilt), w=3, x=sx * 12)
                      for uu in (-36, -46) for sx in (1, -1)]
                     + [dict(shape='prof', pts=rot([(100, 36), (100, -14), (106, -20), (118, -20), (118, 36)], _mc, _tilt), w=8, x=10)])
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
        p['pts'] = rot([(86, -61.5), (134, -61.5), (134, -70), (128, -74), (86, -74)], _mc, _tilt)
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
_rounds = []
for i in range(7):
    uu0 = 30 - 6.4 * i
    ff, uu = rot([(109 + (3 if i % 2 else -3), uu0)], _mc, _tilt)[0]
    _rounds.append(dict(shape='cyl', axis='f', c=(uu, 4 if i % 2 else -2), a0=ff - 14, a1=ff + 14, r=4.4, segs=12))
P += [
    part('mag_rounds', 'Patronen im Fenster', 'Visible rounds', 'ammo', 'multi', 'brass', 'Zeigt den Füllstand', 'im Magazin',
         bevel=0.3, parent_part='magazine', items=_rounds, smooth=True),
    prof('mag_rib', 'Magazinrippe', 'Magazine rib', 'ammo', 'graphite', 'Griffkante vorn; trägt die Bodenplatte',
         'vorn am Magazin', rot([(127, 4), (133, 4), (134, -61), (128, -61)], _mc, _tilt), 20, bevel=R_FINE, parent_part='magazine'),
]
# ---------------------------------------------------------------- Schaft: L-Schaft aus Keilbalken und Fersenkeil (V1 Black Ice „Keilschaft“ als Haltung)
_stock = [(F0 + 4, 98), (F0 + 4, 140), (S0 + 8, 140), (S0, 132), (S0, 94), (S0 + 60, 94)]   # A: Keilbalken, unten 4 mm steigend
_heel = [(S0, 64), (S0 + 6, 58), (S0 + 18, 58), (S0 + 56, 96), (S0, 96)]                    # A: Fersenkeil, 45°-Innenfase
P += [
    prof('stock', 'Schaftbalken', 'Stock beam', 'stock', 'shell',
         'Keilbalken in Linie mit dem Gehäuse; Puffer liegt im Balken', 'in den hinteren Rahmenpfosten gesteckt, zwei Schrauben',
         _stock, 36, bevel=R_MID, cuts=chamfer(S0 - 2, F0 + 6, 140, 18, 6)),
    prof('stock_heel', 'Fersenkeil', 'Heel wedge', 'stock', 'graphite',
         'Trägt die Kappe unten; 45°-Innenfase öffnet den Winkel unter dem Balken (Zweiton wie das Gehäuse)',
         'unter den Balken geschraubt, Fuge', _heel, 34, bevel=R_MID, cuts=chamfer(S0 - 2, S0 + 32, 58, 17, 5, up=False)),
    prof('stock_plate', 'Schaftleiste', 'Stock plate', 'stock', 'shell', 'Deckel über dem Puffer (beidseitig), zweite Schicht',
         'auf den Balken geschraubt, Stufe 0,8 mm', [(-214, 106), (-118, 106), (-110, 114), (-110, 130), (-214, 130)], 37.6, bevel=R_FINE),
    part('stock_screws', 'Schaftschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten Leiste und Balken', 'seitlich',
         bevel=0.2, items=mirror(screws([(-206, 118), (-120, 122)], 18.8, r=1.5, h=0.8))),
    part('sling_socket', 'Riemenöse', 'Sling socket', 'stock', 'multi', 'trim', 'Steckaufnahme für den Riemen (beidseitig)',
         'in die Kappe gepresst', bevel=0.3,
         items=mirror([dict(shape='cyl', axis='x', c=(S0 + 14, 76), a0=17.4, a1=19.2, r=6.5, r_in=3.6, segs=20)])),
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Anlage für die Wange', 'auf den Balken geklebt',
         [(-252, 139), (-142, 139), (-150, 145), (-248, 145)], 24, bevel=R_MID),
    prof('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf die Kappe gesteckt',
         [(S0 + 1, 57), (S0 + 1, 141), (S0 - 7, 139), (S0 - 12, 132), (S0 - 12, 66), (S0 - 7, 59)], 40,
         bevel=R_MID, cuts=[cut_box(S0 - 13, S0 - 8, 70 + 12 * i, 73 + 12 * i, 44) for i in range(6)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(330, HG_LOW + 4, 0), part='hg_low', note='Mitte Handschutz hinter dem Handstopp, Stützhand umgreift'),
    'Socket_Muzzle': dict(at=(584, BORE, 0), part='muzzle_crown', note='Stirnfläche Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=(108, 70, 0), part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Charge': dict(at=(210, 139, HALF + 5), part='charging_handle', note='Griffpunkt Ladehebel links am Rahmenbügel'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(60, 116, -20), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: rechts durch die Rahmenöffnung über dem Verschlussweg, Hülse nach rechts, etwas hoch und vorn (wie BASIC-01)')
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((332, HG_LOW - 3, -2), 'A: unter dem Griffpolster, hinter dem Handstopp'),
            'mag': ((120, -18, 12.5), 'A: linke Magazinseite'),
            'charge': ((210, 139, HALF + 5), 'A: Ladehebel links am Rahmenbügel')}
EGO_GRIPS = {k: dict(g, contact=_CONTACT[k][0], src=_CONTACT[k][1]) for k, g in _EGO.items()}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='frame_top', grip='grip', support='hg_pad'))
ACTIONS = {
    'fire_auto': dict(de='Dauerfeuer (Verschluss im Rahmen sichtbar)', frames=30, step=1, keys={
        'trigger': [(0, 0), (3, 1), (27, 1), (30, 0)],
        'bolt_carrier': [(0, 0), (3, 0), (5, 1), (7, 0), (9, 1), (11, 0), (13, 1), (15, 0), (17, 1), (19, 0), (21, 1), (23, 0)]},
        events=[(3, 'shot'), (7, 'shot'), (11, 'shot'), (15, 'shot'), (19, 'shot')], view=(-0.85, -0.25, 0.45)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=84, keys={
        'mag_release': [(0, 0), (6, 1), (14, 0)],
        'magazine': [(0, 0), (6, 0), (18, 1), (34, 1), (50, 0)],
        'charging_handle': [(0, 0), (58, 0), (66, 1), (72, 0)]},
        events=[(18, 'mag_out'), (50, 'mag_seated'), (66, 'charge'), (72, 'ready')]),
}
EXPLODE = {'sight': (0, 110, 0), 'ammo': (30, -140, 0), 'stock': (-110, 0, 0), 'barrel': (150, 0, 0), 'support': (60, -40, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.78, -0.50, 0.40)   # A: Produktbild von links vorn oben – Kammer im Rahmen (Blickfang) und Ladehebel zur Kamera
