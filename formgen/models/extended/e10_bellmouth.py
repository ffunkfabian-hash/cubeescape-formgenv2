"""EXTENDED-10 „Bellmouth“ – eigenständiges Sci-Fi-Fusionsgewehr der BASIC-Familie (Formgen v2 0.19 „Crucible“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-10: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Visier F1 „Bögen“ auf Schiene BRI-22,
Schraubenköpfe) und Hilfen (`cut_box`, `mirror`, `screws`); die Rolle `charge_core` (Ladekern, reine Emission) kommt aus
`basic.pilot.energy_roles`. Geladen über `formgen.extended`, gerendert mit `tools/extended_render.py`.

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
| Frage | Fusionsgewehr EXTENDED-10 |
|---|---|
| Leitmerkmal der Silhouette | Glocke: kurzes Gehäuse, davor eine dicke runde Ladetrommel (Ø 92) und ein Trichter aus flachem Hals (Ø 60 → 68) und steilem Mund (Ø 68 → 104) – die Salve streut aus einem weiten Mund |
| Schichten | Unteres Gehäuse, Wiege, Ringschaft (Graphit) → Gehäuse mit Tonnendach, Trommel (Creme) → Flansche (3 mm über der Trommel), Trichter, Seitenpaneele (eloxiert) → Schiene → Visier F1 |
| Negativraum | offener Glockenmund mit Streuscheibe und Düse; Ringschaft als geschlossene Schlaufe mit großem Durchbruch |
| Blickfang | Glutring: leuchtender Ring zwischen Trommel und Glocke, rundum sichtbar (einzige Leuchtfunktion am Körper) |
| Zweiton-Blockung | Creme oben (Gehäuse, Trommel) über Graphit unten (Unteres Gehäuse, Wiege, Schaft), etwa 65:35; Trichter eloxiert wie ein Emitter |
| Grafik | ein lackierter Kennring um die Trommel; ein Schriftzug rechts am Unteren Gehäuse |
| Front | vierstufig: blanke Glockenlippe → Trichterinnenwand → Streuscheibe mit sechs Ports → Düse mit blanker Spitze |
| Querschnitt | rund: Trommel und Glocke drehsymmetrisch, das Gehäuse als Tonnendach (senkrechte Flanken, gewölbter Rücken) |
| Übergänge | Trommel sitzt mit Flanschring auf dem Gehäuse; die Wiege umgreift die Trommel unten; Zellentrichter im Unteren Gehäuse angeformt |
| Ergonomie | Griff BGM-1 wie die Familie, Energiezelle vor dem Griff (BEC-1), Stützhand unter der Wiege mit Polster, Wangenauflage auf der Schlaufe |
| Akzente kameranah (A3) | Zellenhalter und Glutring links/vorn, Visierklemme; Front mit sechs groben Ports statt feiner Schlitze |
| Teilungen (A8) | Schaft und Gehäuse 389 mm zu Trommel und Glocke 175 mm (≈ 69:31); Creme zu Graphit ≈ 65:35 |
| Lesbarkeit (A1/A7) | Seitensilhouette eigenständig (`tests/test_extended_fusion.py`); kompakt (0,56 m statt 0,70 m) |

Schlichtheitsbudget: Leuchten 3 Funktionen (Ladung: Glutring und Ladebalken im Visier · Munition: Ladefenster der Zelle) · Grafik 1 Ring ·
Schrift 1 · Orange 1 Bedienfunktion (Zellenhalter) plus Visierklemme · Schrauben nur an Paneelen, Flansch und Schaft.
Energiewaffe ohne Hülsenauswurf (`EJECT = None`).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-10 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.19),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.19, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import part, prof, box, cyl, cut_box, screws, mirror, rail, grip_v21, boegen, R_BODY, R_MID, R_SMALL, R_FINE
from basic.pilot.energy_roles import CHARGE_ROLES  # noqa: F401  (registriert die Rolle charge_core in Blender)
from basic.variant import collect

META = dict(id='EXTENDED-10', num='E10', sheet_id='EA10', type='fusion_rifle', type_de='Fusionsgewehr', type_en='Fusion Rifle',
            family='BASIC', name='Bellmouth', nick='Glocke', ammo='special', fire='charge_burst',
            reference_length_m=0.564, reference_length_source='A: Entwurf 0.19 (kompakt; BASIC-10 0,70 m als Rahmen, V)',
            inspired_by='BASIC-10 Familie; Formgen v1 Kompaktwaffen als Haltung (eine mutige Gesamtarchitektur)',
            summary='Kompaktes Fusionsgewehr mit runder Ladetrommel, Glutring und weitem Glockenmund (EXTENDED-Reihe).')
ASSEMBLIES = [
    dict(id='receiver', de='Hauptgehäuse', en='Receiver'),
    dict(id='barrel', de='Lauf', en='Barrel'),
    dict(id='ammo', de='Munitionsversorgung', en='Ammunition feed'),
    dict(id='sight', de='Visier', en='Sight'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
    dict(id='support', de='Stützbereich', en='Support'),
    dict(id='stock', de='Schaft', en='Stock'),
    dict(id='cooling', de='Kühlung', en='Cooling'),
]

GRIP_TOP = 40        # V: Griff BGM-1 wie BASIC-10 (Oberkante u 40)
BORE = 96            # V: Kernachse wie BASIC-10
TOP = 128            # V: Oberkante Gehäuse = Unterkante Schiene; Visierlinie TOP + 8 + 26 = 162 → 66 über der Kernachse (Vertrag 60–80)
HALF = 22.0          # V: halbe Gehäusebreite (BASIC-10 44)
F_REAR, F_FRONT = -96, 152      # A: Gehäuse (kürzer als BASIC-10 −110 … 150)
CELL = (86, 126)     # V: Energiezelle vor dem Griff (BASIC-10: 3 mm vor dem Abzugsbügel, Posenprüfung)
DRUM = (150, 232)    # A (Runde 3): Ladetrommel f, 82 mm lang
R_DRUM = 46.0        # A (Runde 3): Trommelradius Ø 92 – steht 14 mm über das Gehäuse und unter das Untere Gehäuse (r2 Ø 80 las sich noch als Rohr)
HUB = (232, 248)     # A: Nabe mit Glutring zwischen Trommel und Glocke
NECK = (246, 286)    # A (Runde 2): Glockenhals, außen r 30 → 34
R_NECK = (30.0, 34.0)
BELL = (284, 324)    # A (Runde 2): Trichter, außen r 34 → 52
R_BELL = (34.0, 52.0)
R_IN = (22.0, 27.0)  # A: Innenradius des Halses f 256 → 287 (Wand 7–8)
R_MOUTH = 48.0       # A: Innenradius an der Lippe (Wand 4)
DISC_F = 262         # A: Streuscheibe im Hals
TIP_F = 290          # A: Düsenspitze (Socket_Muzzle), 34 mm hinter der Lippe – der Mund bleibt offen


def vault(half, top, low, rad_u=16.0, flat=11.0, n=7):
    """A: Querprofil „Tonnendach“ (x, u): senkrechte Flanken bis top − rad_u, Viertelellipse bis zur flachen Schienenbahn ±flat."""
    a = half - flat
    right = [(flat + a * math.cos(math.pi / 2 * i / n), top - rad_u + rad_u * math.sin(math.pi / 2 * i / n)) for i in range(n + 1)]
    pts = [(half, low)] + right + [(-x, u) for x, u in right[::-1]] + [(-half, low)]
    return pts


def rounded(f0, f1, u0, u1, r_rear, steps=6):
    """A: Rechteck (f, u) mit gerundeten hinteren Ecken (Radius r_rear) – Umriss des Ringschafts."""
    pts = [(f1, u0), (f1, u1)]
    for i in range(steps + 1):                       # hinten oben
        a = math.pi / 2 + math.pi / 2 * i / steps
        pts.append((f0 + r_rear + r_rear * math.cos(a), u1 - r_rear + r_rear * math.sin(a)))
    for i in range(steps + 1):                       # hinten unten
        a = math.pi + math.pi / 2 * i / steps
        pts.append((f0 + r_rear + r_rear * math.cos(a), u0 + r_rear + r_rear * math.sin(a)))
    return pts


P = []
# ---------------------------------------------------------------- Gehäuse (Tonnendach) und Unteres Gehäuse
P += [
    part('upper', 'Gehäuse', 'Upper receiver', 'receiver', 'xprof', 'shell',
         'Tragkörper für Steuerung, Schiene und Trommel; Querschnitt Tonnendach', 'mit dem Unteren Gehäuse über zwei Querbolzen (fest)',
         bevel=R_MID, pts=vault(HALF, TOP, 82), f0=F_REAR, f1=F_FRONT, cu=0,
         cuts=[cut_box(-86, 38, 88, 112, 3.0, x=HALF + 0.6), cut_box(-86, 38, 88, 112, 3.0, x=-HALF - 0.6)]),        # Paneelmulden
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Zellenschacht',
         'unter dem Gehäuse, Fuge 1 mm; Zellentrichter angeformt, vorn in die Wiege übergehend',
         [(F_REAR, 81), (F_REAR, 60), (-62, 40), (CELL[0] - 14, 40), (CELL[0] - 8, 28), (CELL[0] - 4, 20), (CELL[1] + 4, 20),
          (CELL[1] + 10, 30), (146, 40), (F_FRONT + 10, 40), (F_FRONT + 10, 81)], 2 * HALF - 2, bevel=R_MID),
    prof('cell_lip', 'Schachtlippe', 'Cell well lip', 'receiver', 'trim', 'Blanke Einführkante des Zellenschachts',
         'unten am Trichter des Unteren Gehäuses', [(CELL[0] - 5, 17.5), (CELL[1] + 5, 17.5), (CELL[1] + 6, 21), (CELL[0] - 6, 21)], 43,
         bevel=0.6, iface='BEC-1'),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über der Ladesteuerung',
        'in die Mulde geschraubt (4 Schrauben)', -84, 36, 90, 110, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über der Ladesteuerung',
        'in die Mulde geschraubt (4 Schrauben)', -84, 36, 90, 110, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-79, 94), (-79, 106), (31, 94), (31, 106)], HALF - 0.2, r=1.6, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Gehäuse und Unteres Gehäuse',
         'quer durch das Untere Gehäuse (lösbar)', bevel=0.4, items=mirror(screws([(-84, 72), (140, 72)], HALF - 1, r=3.6, h=1.0))),
    part('cell_release', 'Zellenhalter', 'Cell release', 'grip_controls', 'cyl', 'accent', 'Löst die Energiezelle',
         'Druckknopf links', bevel=R_FINE, axis='x', c=(CELL[0] - 10, 54), a0=19, a1=23.5, r=5, segs=20,
         move=dict(kind='translate', pivot=(CELL[0] - 10, 54, 21), vector_mm=(0, 0, -2.5), event='reload',
                   expect=((CELL[0] - 10, 54, 23.5), (0, 0, -1)))),
    # A: rechts auf dem Unteren Gehäuse zwischen Griff und Zellentrichter; linksbündig, läuft nach vorn bis ≈ 37 mm
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC  EX-10“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-10', size=5.0, f=10, u=62, x=-HALF + 0.95, side=-1, depth=0.12),
]
P += [dict(p, mat='anodized') for p in rail(-60, 70, TOP)]
P[-1]['cuts'] = [cut_box(-52 + 14 * i, -45 + 14 * i, TOP + 4, TOP + 9, 30) for i in range(9)]
# Visier F1 „Bögen“ (Familienbaustein für Fusion, visier-konzept › 6a): Glas Ø 26, Ladebalken auf dem Visiersockel
_sight, SIGHT_ANCHORS = boegen(-12, TOP + 8, weapon_type='fusion_rifle')
P += _sight
# ---------------------------------------------------------------- Ladetrommel, Wiege, Glutring (Leitmerkmal Teil 1)
# Runde 2: Trommel dicker und kürzer (Ø 80 statt 68, 88 statt 112 mm lang), damit sie über und unter dem Gehäuse vorsteht und nicht als
# Verlängerung des Gehäuserohrs gelesen wird; Flansche 3 mm größer als die Trommel fassen sie ein.
P += [
    cyl('drum', 'Ladetrommel', 'Charge drum', 'barrel', 'shell', 'Kondensatortrommel: speichert die Ladung für die Salve; Creme-Schale',
        'zwischen den Flanschen verschraubt', 'f', (BORE, 0), DRUM[0] + 6, DRUM[1] - 6, R_DRUM, segs=56, bevel=R_MID,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=182, a1=183, r=R_DRUM + 2, r_in=R_DRUM - 0.8, segs=56)]),   # Fuge 1 mm
    part('drum_flanges', 'Trommelflansche', 'Drum flanges', 'cooling', 'multi', 'anodized',
         'Kühlflansche an beiden Trommelenden; tragen die Trommel', 'hinten am Gehäuse, vorn an der Nabe verschraubt', bevel=R_SMALL,
         smooth=True, items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=a0, a1=a0 + 6, r=R_DRUM + 3, segs=56)
                             for a0 in (DRUM[0], DRUM[1] - 6)]),
    part('flange_screws', 'Flanschschrauben', 'Flange screws', 'cooling', 'multi', 'trim', 'Halten die Trommel am vorderen Flansch',
         'stirnseitig im vorderen Flansch, um die Nabe', bevel=0.2,
         items=[dict(shape='cyl', axis='f', c=(BORE + 39 * math.sin(a), 39 * math.cos(a)), a0=DRUM[1] - 1, a1=DRUM[1] + 0.6, r=1.7,
                     segs=12) for a in (math.radians(d) for d in (30, 90, 150, 210, 270, 330))]),
    part('drum_ring', 'Kennring', 'Drum ring', 'barrel', 'cyl', 'accent', 'Lackierter Ring um die Trommel (einziges Grafikelement)',
         'lackiert', bevel=0, axis='f', c=(BORE, 0), a0=204, a1=212, r=R_DRUM + 0.15, r_in=R_DRUM - 1, segs=56),
    prof('cradle', 'Wiege', 'Cradle', 'support', 'graphite', 'Umgreift die Trommel unten; Griffbereich der Stützhand; Handstopp vorn',
         'am Unteren Gehäuse verschraubt, Fuge 1 mm; umschließt die Trommel',
         [(F_FRONT - 4, 40), (206, 34), (220, 28), (232, 28), (236, 36), (236, 80), (F_FRONT - 4, 80)], 40, bevel=R_MID,
         cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=DRUM[0] - 4, a1=DRUM[1] + 1, r=R_DRUM + 3.6, segs=56)]),
    prof('cradle_grip', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand',
         'unten auf die Wiege geklebt', [(166, 35), (200, 31), (202, 36), (166, 40)], 32, bevel=R_SMALL),
    part('cradle_screws', 'Wiegenschrauben', 'Cradle screws', 'support', 'multi', 'trim', 'Halten die Wiege am Unteren Gehäuse',
         'seitlich an der Wiege', bevel=0.2, items=mirror(screws([(162, 46), (224, 36)], 20.0, r=1.8, h=0.8))),
    cyl('hub', 'Nabe', 'Hub', 'barrel', 'dark_metal', 'Verbindet Trommel und Glocke; führt den Kern', 'zwischen Trommel und Glocke',
        'f', (BORE, 0), HUB[0], HUB[1], 28, segs=56, bevel=R_SMALL),
    part('hub_lips', 'Glutringkanten', 'Glow ring lips', 'barrel', 'multi', 'trim', 'Blanke Kanten beiderseits des Glutrings',
         'auf die Nabe gepresst', bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=a0, a1=a0 + 2, r=31.5, r_in=26, segs=56) for a0 in (HUB[0] + 2, HUB[0] + 12)]),
    cyl('glow_ring', 'Glutring', 'Glow ring', 'barrel', 'charge_core', 'Ladekern als Ring: leuchtet beim Aufladen auf (Blickfang)',
        'zwischen den Kanten auf der Nabe', 'f', (BORE, 0), HUB[0] + 4, HUB[0] + 12, 30.4, r_in=26, segs=56, bevel=0,
        move=dict(kind='glow', pivot=None, event='charge', max=6.0)),
]
# ---------------------------------------------------------------- Glocke (Leitmerkmal Teil 2): Hals, Trichter, Streuscheibe, Düse
# Runde 2: Trichter aus zwei Kegeln (Hals flach, Mund steil) statt eines geraden Kegels – liest sich als gekrümmter Schalltrichter, nicht
# als Megafon; eloxiert wie ein Emitter, Creme bleibt an Gehäuse und Trommel.
P += [
    cyl('bell_neck', 'Glockenhals', 'Bell neck', 'barrel', 'anodized', 'Hals des Streutrichters; nimmt die Streuscheibe auf',
        'auf die Nabe geschraubt', 'f', (BORE, 0), NECK[0], NECK[1], R_NECK[0], r1=R_NECK[1], segs=56, bevel=R_SMALL,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=DISC_F - 4, a1=NECK[1] + 1, r=R_IN[0], r1=R_IN[1], segs=56)]),
    cyl('bell', 'Glocke', 'Bell', 'barrel', 'anodized', 'Streutrichter: öffnet die Salve zum weiten Kegel',
        'auf den Glockenhals geschraubt', 'f', (BORE, 0), BELL[0], BELL[1], R_BELL[0], r1=R_BELL[1], segs=56, bevel=R_SMALL,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=BELL[0] - 1, a1=BELL[1] + 1, r=R_IN[1], r1=R_MOUTH, segs=56)]),
    cyl('bell_lip', 'Glockenlippe', 'Bell lip', 'barrel', 'trim', 'Blanke Stirnkante des Trichters', 'vorn auf die Glocke gepresst',
        'f', (BORE, 0), BELL[1] - 3, BELL[1] + 0.8, R_BELL[1] + 0.6, r_in=R_MOUTH - 1.4, segs=56, bevel=0.5),
    cyl('scatter_disc', 'Streuscheibe', 'Scatter disc', 'barrel', 'dark_metal', 'Teilt die Salve auf sechs durchgehende Ports',
        'im Glockenhals verschraubt', 'f', (BORE, 0), DISC_F - 4, DISC_F + 2, R_IN[0] + 1.2, segs=56, bevel=R_FINE,
        cuts=[dict(shape='cyl', axis='f', c=(BORE + 16 * math.sin(a), 16 * math.cos(a)), a0=DISC_F - 6, a1=DISC_F + 4, r=3.4, segs=16)
              for a in (math.radians(d) for d in range(0, 360, 60))]),
    cyl('nozzle', 'Düse', 'Nozzle', 'barrel', 'dark_metal', 'Zentrale Düse vor der Streuscheibe; Kernende', 'auf die Streuscheibe geschraubt',
        'f', (BORE, 0), DISC_F + 1, TIP_F - 3, 10, r1=6.5, segs=32, bevel=R_FINE, iface='BMZ-15'),
    cyl('nozzle_tip', 'Düsenspitze', 'Nozzle tip', 'barrel', 'trim', 'Blanke Spitze der Düse', 'vorn auf der Düse',
        'f', (BORE, 0), TIP_F - 4, TIP_F, 7, r_in=3.4, segs=32, bevel=0.5),
]
# ---------------------------------------------------------------- Griff, Zelle (Familienschnittstellen BGM-1, BEC-1)
P += grip_v21(top=GRIP_TOP)
_cc = ((CELL[0] + CELL[1]) / 2, 10)
P += [
    part('energy_cell', 'Energiezelle', 'Energy cell', 'ammo', 'prof', 'dark_metal', 'Speichert die Ladungen; austauschbar',
         'rastet im Zellenschacht ein (lösbar)', bevel=R_MID, iface='BEC-1', w=24,
         pts=[(CELL[0], 60), (CELL[1], 60), (CELL[1], -26), (CELL[1] - 4, -32), (CELL[0] + 4, -32), (CELL[0], -26)],
         move=dict(kind='translate', pivot=(_cc[0], _cc[1], 0), vector_mm=(0, -110, 0), event='reload', removable=True,
                   expect=((_cc[0], -32, 0), (0, -1, 0)))),
    box('cell_band', 'Zellenband', 'Cell band', 'ammo', 'trim', 'Blankes Band über dem Zellenboden; Greifkante',
        'um die Zelle', CELL[0] - 0.6, CELL[1] + 0.6, -24, -20, 25.2, bevel=0.4, parent_part='energy_cell'),
    box('cell_window', 'Ladefenster', 'Charge window', 'ammo', 'energy', 'Zeigt den Ladezustand der Zelle',
        'links in die Zelle eingelassen', CELL[1] - 12, CELL[1] - 7, -14, 8, 1.0, bevel=0.3, x=12.2, parent_part='energy_cell'),
]
# ---------------------------------------------------------------- Ringschaft: geschlossene Schlaufe mit großem Durchbruch
S_F0, S_U = -230, (40, 116)      # A (Runde 3): Schaftende und Höhe (Schlaufe 134 lang, 76 hoch; Schaftlänge wie eine Schulterwaffe)
P += [
    prof('stock', 'Ringschaft', 'Loop stock', 'stock', 'graphite',
         'Schlaufe: Rücken mit Wange, Schaftkappe, Unterzug zurück zum Gehäuse; großer Durchbruch (Negativraum)',
         'am Gehäuseende verschraubt', rounded(S_F0, F_REAR + 2, *S_U, 22), 34, bevel=R_MID,
         cuts=[dict(shape='prof', pts=rounded(S_F0 + 15, F_REAR - 18, S_U[0] + 13, S_U[1] - 14, 12), w=60)]),
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Anlage für die Wange', 'auf den Schaftrücken geklebt',
         [(-204, S_U[1] - 1), (-120, S_U[1] - 1), (-124, S_U[1] + 4), (-200, S_U[1] + 4)], 24, bevel=R_MID),
    prof('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf das Schaftende gesteckt',
         [(S_F0 + 1, S_U[0] + 18), (S_F0 + 1, S_U[1] - 18), (S_F0 - 7, S_U[1] - 20), (S_F0 - 9, S_U[1] - 26), (S_F0 - 9, S_U[0] + 24),
          (S_F0 - 7, S_U[0] + 20)], 38, bevel=R_MID, cuts=[cut_box(S_F0 - 10, S_F0 - 6, 64 + 10 * i, 67 + 10 * i, 44) for i in range(3)]),
    part('stock_bolts', 'Schaftbolzen', 'Stock bolts', 'stock', 'multi', 'trim', 'Halten den Schaft am Gehäuse',
         'quer durch den Schaftansatz', bevel=0.3, items=mirror(screws([(F_REAR - 9, 112), (F_REAR - 9, 40)], 17.4, r=2.6, h=1.0))),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(184, 34, 0), part='cradle', note='Griffpolster unter der Wiege'),
    'Socket_Muzzle': dict(at=(TIP_F, BORE, 0), part='nozzle_tip', note='Düsenspitze im Glockenmund auf der Kernachse'),
    'Socket_Cell': dict(at=(_cc[0], 20, 0), part='energy_cell', note='Einrastpunkt der Energiezelle (Schnittstelle BEC-1)'),
}
ANCHORS.update(SIGHT_ANCHORS)
_charge = [(0, 0), (4, 0.2), (14, 0.5), (24, 1.0), (27, 1.0), (36, 0)]
ACTIONS = {
    'charge_fire': dict(de='Aufladen und Salve', frames=40, step=1, keys={
        'trigger': [(0, 0), (2, 1), (30, 1), (33, 0)], 'glow_ring': _charge, 'sight_emitter': _charge},
        events=[(2, 'charge_start'), (24, 'charged'), (27, 'burst'), (40, 'ready')], view=(0.8, -0.3, 0.45)),
    'charge_cancel': dict(de='Aufladen abbrechen', frames=24, step=1, keys={
        'trigger': [(0, 0), (2, 1), (12, 1), (14, 0)], 'glow_ring': [(0, 0), (12, 0.45), (20, 0)],
        'sight_emitter': [(0, 0), (12, 0.45), (20, 0)]}, events=[(12, 'cancel')], view=(0.8, -0.3, 0.45)),
    'reload': dict(de='Energiezelle wechseln', frames=70, keys={'cell_release': [(0, 0), (6, 1), (14, 1), (18, 0)],
                                                                'energy_cell': [(0, 0), (16, 1), (34, 1), (50, 0)]},
                   events=[(16, 'cell_out'), (50, 'cell_in'), (58, 'ready')], view=(0.8, -0.3, 0.45)),
}
EJECT = None    # Energiewaffe: keine Hülse
# Ego-Griffe (A): Richtungen und Fingerstellungen wie BASIC-10, Kontaktpunkte auf den Flächen dieses Modells
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(184, 32.0, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0), fingers_pose='underhand',
                    src='A: unter der Wiege auf dem Griffpolster (f 166–202, Unterkante u 31–35)'),
    'mag':     dict(part='energy_cell', contact=(100, -10, 12.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0), fingers_pose='mag_hold',
                    src='V: links an der Energiezelle (Breite 24, f 86–126) wie BASIC-10'),
    'charge':  dict(part='cell_release', contact=(CELL[0] - 10, 54, 23.5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Zellenhalter links (kein Ladehebel)'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(grip='grip', support='cradle_grip'))
EXPLODE = {'sight': (0, 110, 0), 'ammo': (0, -140, 0), 'stock': (-110, 0, 0), 'barrel': (140, 0, 0), 'cooling': (0, 0, 80),
           'support': (40, -70, 0), 'grip_controls': (-10, -80, 0), 'receiver': (0, 0, 0)}
HERO = (0.74, -0.56, 0.38)   # A: Produktbild von links vorn oben – Glutring, Glockenmund und Zellenhalter zur Kamera
