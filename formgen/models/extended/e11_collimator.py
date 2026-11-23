"""EXTENDED-11 „Collimator“ – eigenständiges Sci-Fi-Linearfusionsgewehr der BASIC-Familie (Formgen v2 0.19 „Crucible“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-11: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Zielfernrohr Z2 „Gabel“ auf zwei Schienen
BRI-22, Schraubenköpfe) und Hilfen (`cut_box`, `mirror`, `screws`); die Rolle `charge_core` (Ladekern, reine Emission) kommt aus
`basic.pilot.energy_roles`. Geladen über `formgen.extended`, gerendert mit `tools/extended_render.py`.

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
| Frage | Lineares Fusionsgewehr EXTENDED-11 |
|---|---|
| Leitmerkmal der Silhouette | Kollimator: vor dem Gehäuse ein offener Käfig aus vier blanken Führungsstäben, gehalten von quadratischen Fokusplatten, deren Abstand nach vorn immer kürzer wird (128 → 40 mm) – der Strahl wird sichtbar gebündelt; vorn ein schlanker Fokuskegel |
| Schichten | Unteres Gehäuse, Unterzug, Schaftholm (Graphit) → Gehäuse, Fokusplatten, Schaftplatte (Creme) → Grundplatte, Optikbock, Seitenpaneele (eloxiert) → Schienen → Zielfernrohr Z2 |
| Negativraum | der ganze Käfig: zwischen den Stäben liegt der Linearkern frei, Hintergrund sichtbar; Durchbruch im Optikbock; offener Raum unter dem Schaftholm |
| Blickfang | Linearkern: leuchtende Linie im Käfig, durch die Platten rhythmisch gegliedert |
| Zweiton-Blockung | Creme oben (Gehäuse, Platten, Schaftplatte) über Graphit unten (Unteres Gehäuse, Unterzug, Schaftholm), etwa 60:40 |
| Grafik | die vorderste Platte seitlich lackiert (Kennplatte); ein Schriftzug rechts am Gehäuse |
| Front | vierstufig: Kennplatte → Fokuskragen → Fokuskegel mit zwei Rillen → blanke Krone |
| Querschnitt | quadratisch: Kastengehäuse mit Fasen oben, Platten 54 × 54 mit runder Blende, Stäbe auf den Ecken eines Quadrats |
| Übergänge | Gehäuse endet in der Grundplatte, die den Käfig trägt; der Unterzug läuft unter den hinteren Platten und trägt sie; Zellentrichter angeformt |
| Ergonomie | Griff BGM-1 wie die Familie, Zelle hinter dem Griff (BEC-1), Stützhand unter dem Unterzug mit Polster, hohe Wange für das Zielfernrohr |
| Akzente kameranah (A3) | Zellenhalter links, Höhenturm und Klemmhebel am Zielfernrohr; Front mit zwei breiten Rillen statt vieler feiner |
| Teilungen (A8) | Gehäuse 322 mm zu Käfig und Front 600 mm (≈ 35:65); Creme zu Graphit ≈ 60:40 |
| Lesbarkeit (A1/A7) | Seitensilhouette eigenständig (`tests/test_extended_fusion.py`); lang und offen (1,14 m) |

Schlichtheitsbudget: Leuchten 3 Funktionen (Ladung: Linearkern · Munition: Ladefenster der Zelle · Visier: Absehen) · Grafik 1 Platte ·
Schrift 1 · Orange 1 Bedienfunktion (Zellenhalter) plus Höhenturm und Klemmhebel im Visier · Schrauben nur an Grundplatte, Paneelen und Schaft.
Energiewaffe ohne Hülsenauswurf (`EJECT = None`).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-11 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.19),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.19, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
from basic.common import part, prof, box, cyl, cut_box, screws, mirror, rail, grip_v21, gabel, R_MID, R_SMALL, R_FINE
from basic.pilot.energy_roles import CHARGE_ROLES  # noqa: F401  (registriert die Rolle charge_core in Blender)
from basic.variant import collect

META = dict(id='EXTENDED-11', num='E11', sheet_id='EA11', type='linear_fusion_rifle', type_de='Lineares Fusionsgewehr',
            type_en='Linear Fusion Rifle', family='BASIC', name='Collimator', nick='Kollimator', ammo='heavy', fire='charge_single',
            reference_length_m=1.123, reference_length_source='A: Entwurf 0.19 (BASIC-11 1,10 m als Rahmen, V)',
            inspired_by='BASIC-11 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur je Waffe)',
            summary='Lineares Fusionsgewehr mit offenem Stabkäfig, Fokusplatten in enger werdendem Takt und Fokuskegel (EXTENDED-Reihe).')
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

GRIP_TOP = 40        # V: Griff BGM-1 wie BASIC-11
BORE = 92            # V: Kernachse wie BASIC-11
TOP = 122            # V: Oberkante Gehäuse; vordere Schiene darauf
HALF = 20.0          # V: halbe Gehäusebreite (BASIC-11 40)
F_REAR, F_FRONT = -122, 200     # V: Gehäuse wie BASIC-11
CELL = (-112, -58)   # V: Energiezelle hinter dem Griff (BASIC-11)
# Visiersitz Konzept A wie BASIC-11 (V): Visierlinie u 158 (66 über dem Kern), Ringstirn f 150, Augenpunkt f 60
_cu = BORE + 66
F_OBJ, SCOPE_L = 150, 190
SEAT = 146           # V: Schienenoberkante hinten unter der Okular-Unterkante
RISER = SEAT - 8     # A: Oberkante Optikbock (eigener eloxierter Bock statt angeformtem Buckel)
SEAT_F = (-20, 62)   # V: hintere Schiene (Sattel f −14 … 56)
FOOT_F = (116, 154)  # V: vordere Schiene unter dem Klemmfuß
# Käfig (Leitmerkmal): Platten mit nach vorn kürzer werdendem Abstand 128, 112, 96, 78, 60, 40 (A)
BASE = (196, 212)                          # Grundplatte (eloxiert, trägt den Käfig)
PLATES = (340, 452, 548, 626, 686)         # Fokusplatten (Creme), je 9 mm
FRONT_PLATE = (726, 740)                   # Kennplatte (Creme, seitlich lackiert)
ROD = 17.0           # A: Stäbe auf den Ecken eines Quadrats ±17 um den Kern (Seite: u 75 und 109, Kern frei dazwischen)
PLATE = 54.0         # A: Plattenkante (u 65–119)
APERTURE = 22.0      # A: runde Blende Ø 22 (quadratischer Rahmen mit Innenradius 11)
CONE = (752, 794)    # A: Fokuskegel r 13 → 6,5
TIP = 800            # A: Stirn der Krone (Socket_Muzzle)


def frame_geo(f0, f1, size=PLATE):
    """A: quadratische Platte quer zur Achse mit runder Blende (Rahmen, Innenradius = halbe Blende); nur die Maße."""
    return dict(f0=f0, f1=f1, cu=BORE, ow=size, oh=size, iw=APERTURE, ih=APERTURE, r_out=6, r_in=APERTURE / 2)


def plate(f0, f1, size=PLATE):
    return dict(shape='frame', **frame_geo(f0, f1, size))


_cage_x = [(ROD, ROD), (ROD, -ROD), (-ROD, ROD), (-ROD, -ROD)]   # (du, x)
_scope, SIGHT_ANCHORS = gabel(F_OBJ, TOP + 8, _cu, weapon_type='linear_fusion_rifle', seat_u=SEAT, length=SCOPE_L, saddle_f=(-14, 56))

P = []
# ---------------------------------------------------------------- Kastengehäuse, Optikbock, Unteres Gehäuse
P += [
    part('receiver', 'Gehäuse', 'Receiver', 'receiver', 'xprof', 'shell', 'Tragkörper: Steuerung, Optikbock und Grundplatte des Käfigs',
         'mit dem Unteren Gehäuse über zwei Querbolzen (fest); vorn in die Grundplatte gesteckt', bevel=R_MID,
         pts=[(HALF, 76), (HALF, TOP - 8), (HALF - 8, TOP), (-HALF + 8, TOP), (-HALF, TOP - 8), (-HALF, 76)], f0=F_REAR, f1=F_FRONT, cu=0,
         cuts=[dict(shape='prof', pts=[(F_REAR - 2, 100), (F_REAR + 12, TOP + 2), (F_REAR - 2, TOP + 2)], w=60),    # Rückenfase
               cut_box(-98, -28, 82, 112, 3.0, x=HALF + 0.6), cut_box(-98, -28, 82, 112, 3.0, x=-HALF - 0.6)]),     # Paneelmulden
    box('riser', 'Optikbock', 'Optic riser', 'receiver', 'anodized', 'Hebt die hintere Schiene unter das Okular; Durchbruch',
        'auf das Gehäuse geschraubt, Stufe 2 mm', -26, 68, TOP - 1, RISER, 30, bevel=R_SMALL,
        cuts=[dict(shape='prof', pts=[(-12, TOP + 3), (54, TOP + 3), (48, RISER - 4), (-6, RISER - 4)], w=40)]),
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Zellenschacht hinter dem Griff',
         'unter dem Gehäuse, Fuge 1 mm; Zellentrichter angeformt',
         [(F_REAR, 75), (F_REAR, 30), (CELL[0] - 4, 24), (CELL[1] + 4, 24), (CELL[1] + 16, 40), (120, 40), (134, 54), (F_FRONT, 54),
          (F_FRONT, 75)], 2 * HALF - 2, bevel=R_MID),
    prof('cell_lip', 'Schachtlippe', 'Cell well lip', 'receiver', 'trim', 'Blanke Einführkante des Zellenschachts',
         'unten am Trichter des Unteren Gehäuses', [(CELL[0] - 5, 21.5), (CELL[1] + 5, 21.5), (CELL[1] + 6, 25), (CELL[0] - 6, 25)], 39,
         bevel=0.6, iface='BEC-1'),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über der Steuerung',
        'in die Mulde geschraubt (4 Schrauben)', -96, -30, 84, 110, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über der Steuerung',
        'in die Mulde geschraubt (4 Schrauben)', -96, -30, 84, 110, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-91, 88), (-91, 106), (-35, 88), (-35, 106)], HALF - 0.2, r=1.5, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Gehäuse und Unteres Gehäuse',
         'quer durch das Untere Gehäuse (lösbar)', bevel=0.4, items=mirror(screws([(-106, 66), (186, 66)], HALF - 1, r=3.4, h=1.0))),
    part('cell_release', 'Zellenhalter', 'Cell release', 'grip_controls', 'cyl', 'accent', 'Löst die Energiezelle',
         'Druckknopf links', bevel=R_FINE, axis='x', c=(CELL[1] + 12, 54), a0=17, a1=21.5, r=5, segs=20,
         move=dict(kind='translate', pivot=(CELL[1] + 12, 54, 19), vector_mm=(0, 0, -2.5), event='reload',
                   expect=((CELL[1] + 12, 54, 21.5), (0, 0, -1)))),
    # A: rechts auf der freien Gehäusefläche vor den Paneelen; linksbündig, läuft nach vorn bis ≈ 37 mm
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC  EX-11“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-11', size=5.0, f=96, u=96, x=-HALF - 0.05, side=-1, depth=0.12),
]
P += [dict(p, mat='anodized', attach='auf dem Optikbock hinter dem Augenpunkt (fest)') for p in rail(*SEAT_F, RISER)] \
    + [dict(p, id='rail_front', de='Schiene vorn', en='Front rail', mat='anodized', attach='auf dem Gehäuse unter dem Objektiv (fest)')
       for p in rail(*FOOT_F, TOP)]
P += _scope
# ---------------------------------------------------------------- Käfig (Leitmerkmal): Grundplatte, Stäbe, Fokusplatten, Kern
P += [
    part('base_plate', 'Grundplatte', 'Base plate', 'barrel', 'frame', 'anodized', 'Trägt den Käfig am Gehäuse; erste Blende',
         'vorn auf Gehäuse und Unteres Gehäuse geschraubt', bevel=R_SMALL, **frame_geo(*BASE, size=PLATE + 6)),
    part('base_screws', 'Grundplattenschrauben', 'Base plate screws', 'barrel', 'multi', 'trim', 'Halten die Grundplatte am Gehäuse',
         'stirnseitig in der Grundplatte', bevel=0.2,
         items=[dict(shape='cyl', axis='f', c=(u, x), a0=BASE[1] - 1, a1=BASE[1] + 0.8, r=1.8, segs=12)
                for u in (BORE + 23, BORE - 23) for x in (23, -23)]),
    part('rods', 'Führungsstäbe', 'Guide rods', 'barrel', 'multi', 'metal', 'Vier blanke Stäbe führen das Feld; tragen die Platten',
         'in Grund- und Kennplatte eingespannt', bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE + du, x), a0=BASE[0] + 4, a1=FRONT_PLATE[1] - 2, r=3.2, segs=16)
                for du, x in _cage_x]),
    part('plates', 'Fokusplatten', 'Focus plates', 'cooling', 'multi', 'shell',
         'Bündeln das Feld; Abstand nach vorn kürzer (Takt der Bündelung); führen Wärme ab', 'auf die Stäbe geklemmt', bevel=R_MID,
         items=[plate(f, f + 9) for f in PLATES]),
    part('apertures', 'Blendenringe', 'Aperture rings', 'cooling', 'multi', 'trim', 'Blanke Ringe in den Blenden; fassen den Kern',
         'in die Blenden gepresst', bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f - 0.6, a1=f + 9.6, r=APERTURE / 2 + 0.4, r_in=7.5, segs=32)
                for f in PLATES + (FRONT_PLATE[0] + 2.5,)]),
    cyl('linear_core', 'Linearkern', 'Linear core', 'barrel', 'charge_core', 'Leuchtender Kern im Käfig; lädt sich sichtbar auf (Blickfang)',
        'zwischen Grundplatte und Fokuskegel gespannt', 'f', (BORE, 0), BASE[0] - 2, CONE[0] + 4, 2.8, bevel=0, segs=16,
        move=dict(kind='glow', pivot=None, event='charge', max=6.0)),
    part('front_plate', 'Kennplatte', 'Front plate', 'barrel', 'frame', 'shell', 'Schließt den Käfig vorn; trägt den Fokuskegel',
         'auf die Stäbe geschraubt', bevel=R_MID, **frame_geo(*FRONT_PLATE)),
    part('front_mark', 'Kennfarbe', 'Front mark', 'barrel', 'multi', 'accent', 'Lackierte Seitenflächen der Kennplatte (einziges Grafikelement)',
         'lackiert, beidseitig', bevel=0,
         items=[dict(shape='box', f0=FRONT_PLATE[0] + 2, f1=FRONT_PLATE[1] - 2, u0=BORE - PLATE / 2 + 7, u1=BORE + PLATE / 2 - 7, w=0.6,
                     x=sx * (PLATE / 2 + 0.05)) for sx in (1, -1)]),
    cyl('focus_collar', 'Fokuskragen', 'Focus collar', 'barrel', 'anodized', 'Fasst den Fokuskegel an der Kennplatte',
        'in die Kennplatte geschraubt', 'f', (BORE, 0), FRONT_PLATE[1] - 1, CONE[0] + 1, 16, segs=32, bevel=R_SMALL),
    cyl('muzzle', 'Fokuskegel', 'Focus cone', 'barrel', 'dark_metal', 'Bündelt den Strahl; zwei breite Rillen', 'auf den Fokuskragen geschraubt',
        'f', (BORE, 0), CONE[0], CONE[1], 13, r1=6.5, r_in=2.4, segs=32, bevel=R_FINE, iface='BMZ-15',
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=a0, a1=a0 + 3, r=16, r_in=11.6 - 0.15 * (a0 - CONE[0]), segs=32)
              for a0 in (762, 774)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn am Fokuskegel',
        'f', (BORE, 0), CONE[1] - 1, TIP, 7.2, r_in=3.0, segs=32, bevel=0.5),
]
# ---------------------------------------------------------------- Unterzug (Stützhand), trägt die hinteren Platten
_hg_top = BORE - PLATE / 2       # A: Oberkante = Plattenunterkante (u 65)
P += [
    prof('underbeam', 'Unterzug', 'Underbeam', 'support', 'graphite', 'Griffbereich der Stützhand; trägt die hinteren Fokusplatten',
         'an der Grundplatte verschraubt, Fuge 1 mm', [(BASE[0], 40), (430, 40), (470, 54), (470, _hg_top), (BASE[0], _hg_top)], 30,
         bevel=R_MID),
    prof('underbeam_grip', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand',
         'unten auf den Unterzug geklebt', [(262, 35), (410, 35), (410, 41), (262, 41)], 24, bevel=R_SMALL),
]
# ---------------------------------------------------------------- Griff, Zelle (Familienschnittstellen BGM-1, BEC-1)
P += grip_v21(top=GRIP_TOP)
_cc = ((CELL[0] + CELL[1]) / 2, 0)
P += [
    part('energy_cell', 'Energiezelle', 'Energy cell', 'ammo', 'prof', 'dark_metal', 'Speichert die Ladungen; austauschbar',
         'rastet im Zellenschacht hinter dem Griff ein (lösbar)', bevel=R_MID, iface='BEC-1', w=24,
         pts=[(CELL[0], 60), (CELL[1], 60), (CELL[1], -20), (CELL[1] - 4, -26), (CELL[0] + 4, -26), (CELL[0], -20)],
         move=dict(kind='translate', pivot=(_cc[0], _cc[1], 0), vector_mm=(0, -110, 0), event='reload', removable=True,
                   expect=((_cc[0], -26, 0), (0, -1, 0)))),
    box('cell_band', 'Zellenband', 'Cell band', 'ammo', 'trim', 'Blankes Band über dem Zellenboden; Greifkante',
        'um die Zelle', CELL[0] - 0.6, CELL[1] + 0.6, -18, -14, 25.2, bevel=0.4, parent_part='energy_cell'),
    box('cell_window', 'Ladefenster', 'Charge window', 'ammo', 'energy', 'Zeigt den Ladezustand der Zelle',
        'links in die Zelle eingelassen', CELL[1] - 12, CELL[1] - 7, -8, 12, 1.0, bevel=0.3, x=12.2, parent_part='energy_cell'),
]
# ---------------------------------------------------------------- T-Schaft: Holm in der Kernachse, Schaftplatte wie die Fokusplatten
S_F0 = -312          # A: Vorderkante der Schaftplatte
P += [
    box('stock_joint', 'Schaftverbindung', 'Stock joint', 'stock', 'dark_metal', 'Verbindet Holm und Gehäuse; Verriegelung',
        'Steckverbindung am Gehäuseende', -134, F_REAR + 1, 70, 112, 30, bevel=R_SMALL),
    box('stock_beam', 'Schaftholm', 'Stock beam', 'stock', 'graphite', 'Gerader Holm in der Kernachse; darunter offen (Negativraum)',
        'in der Schaftverbindung verschraubt', S_F0 + 2, -132, BORE - 12, BORE + 12, 24, bevel=R_MID),
    prof('stock', 'Schaftplatte', 'Stock plate', 'stock', 'shell', 'Schulterplatte; Creme wie die Fokusplatten',
         'auf das Holmende geschraubt', [(S_F0, 8), (S_F0 + 22, 14), (S_F0 + 22, 128), (S_F0, 132)], 40, bevel=R_MID),
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Hohe Anlage für die Wange (Zielfernrohr)',
         'auf den Holm geklebt', [(-292, BORE + 11), (-196, BORE + 11), (-204, BORE + 36), (-288, BORE + 38)], 22, bevel=R_SMALL),
    prof('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf die Schaftplatte gesteckt',
         [(S_F0 + 1, 10), (S_F0 + 1, 130), (S_F0 - 8, 128), (S_F0 - 11, 120), (S_F0 - 11, 18), (S_F0 - 8, 12)], 42, bevel=R_MID,
         cuts=[cut_box(S_F0 - 12, S_F0 - 8, 28 + 13 * i, 31 + 13 * i, 46) for i in range(7)]),
    part('stock_screws', 'Schaftschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten den Holm an der Schaftplatte',
         'seitlich an der Schaftplatte', bevel=0.2, items=mirror(screws([(S_F0 + 11, BORE - 6), (S_F0 + 11, BORE + 6)], 20.0, r=1.8, h=0.8))),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(336, 35, 0), part='underbeam', note='Griffpolster unter dem Unterzug'),
    'Socket_Muzzle': dict(at=(TIP, BORE, 0), part='muzzle_crown', note='Stirn der Krone auf der Kernachse'),
    'Socket_Cell': dict(at=(_cc[0], 24, 0), part='energy_cell', note='Einrastpunkt der Energiezelle (Schnittstelle BEC-1)'),
}
ANCHORS.update(SIGHT_ANCHORS)
ACTIONS = {
    'charge_fire': dict(de='Aufladen und Einzelstrahl', frames=36, step=1, keys={
        'trigger': [(0, 0), (2, 1), (18, 1), (21, 0)], 'linear_core': [(0, 0), (6, 0.25), (16, 0.8), (18, 1), (24, 0)]},
        events=[(2, 'charge_start'), (16, 'charged'), (18, 'beam'), (34, 'ready')], view=(0.8, -0.3, 0.45)),
    'reload': dict(de='Energiezelle wechseln', frames=80, keys={'cell_release': [(0, 0), (6, 1), (14, 1), (18, 0)],
                                                                'energy_cell': [(0, 0), (18, 1), (38, 1), (56, 0)]},
                   events=[(18, 'cell_out'), (56, 'cell_in'), (64, 'ready')], view=(0.8, -0.3, 0.45)),
}
EJECT = None    # Energiewaffe: keine Hülse
# Ego-Griffe (A): Richtungen und Fingerstellungen wie BASIC-11, Kontaktpunkte auf den Flächen dieses Modells
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(336, 33.5, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0), fingers_pose='underhand',
                    src='A: unter dem Unterzug auf dem Griffpolster (f 262–410, Unterkante u 35)'),
    'mag':     dict(part='energy_cell', contact=(-95, -5, 12.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0), fingers_pose='mag_hold',
                    src='V: links an der Energiezelle (Breite 24, f −112 … −58) wie BASIC-11'),
    'charge':  dict(part='cell_release', contact=(CELL[1] + 12, 54, 21.5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Zellenhalter links (kein Ladehebel)'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(grip='grip', support='underbeam_grip'))
EXPLODE = {'sight': (0, 130, 0), 'ammo': (0, -140, 0), 'stock': (-120, 0, 0), 'barrel': (160, 0, 0), 'cooling': (0, 90, 0),
           'support': (40, -70, 0), 'grip_controls': (-10, -80, 0), 'receiver': (0, 0, 0)}
HERO = (0.80, -0.48, 0.34)   # A: Produktbild von links vorn oben – Käfig mit Kern, Zellenhalter und Zielfernrohr zur Kamera
