"""EXTENDED-17 „Gorget“ – eigenständige Sci-Fi-Glefe der BASIC-Familie (Formgen v2 0.20 „Riftguard“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-17: aus `basic.common` kommen nur die genormten Familienschnittstellen Griffmodul BGM-1 (`grip_v21`) und Energiezelle BEC-1
(`energy_cell`) sowie Formhelfer (`part`, `prof`, `box`, `cyl`, `cut_box`, `screws`, `mirror`) und die Radienstufen.
Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal: Ringkragen im Takt. Der lange runde Graphitschaft (70 % der Länge) trägt vier Creme-Kragen – Endkragen, Abzugskragen,
  Zellenkragen, Kopfkragen –, alle mit derselben nach vorn unten vorgeneigten Stirn (Anlauf 14 mm auf 54 mm). Der Schaft dominiert,
  der Kopf ist kompakt (Klinge 370 mm, BASIC-17 390 mm, V).
- Querschnitt: Schaft rund, Kragen als gefaste Rechteckquerschnitte, Klinge als Keil (Querprofil `xprof`) mit 10 mm Rückenfläche
  unten und blanker Schneide oben; Spitze als Meißelschnitt (Tanto), kein Speerblatt.
- Negativraum: die Laterne – Emitter und Spulen liegen frei in einem Fenster, das quer durch Laternenrahmen und beide Schildflügel geht;
  dazu die Schusslinie unter dem Klingenrücken.
- Zweiton: Creme-Kragen über dem Graphitschaft; der Abzugskragen ist selbst geteilt (Creme oben, Graphit unten, Fuge 1 mm, ≈ 65:35).
- Blickfang (genau einer): Emitterlinse in der Laterne, blank gefasst, leuchtet beim Schuss. Zweite Leuchtfunktion: Ladefenster der
  Energiezelle (BEC-1).
- Grafik: ein Orange-Streifen auf dem Kopfkragen, parallel zur Stirn; eine Schrift rechts auf dem Graphitunterteil.
- Front mehrstufig: Schneide und Rückenfläche, Klingenhalter, Laternenrahmen mit Bohrung, Linse und Krone, Schildflügel, Kopfkragen.
- Ergonomie: Griff BGM-1 mit Abzug am Abzugskragen (Socket_Hand), Gummimanschette für die Stützhand zwischen Zellen- und Kopfkragen;
  Akzent-Bedienfunktionen: Schildschalter (Daumen) und Zellenhalter (2).
- Kein Visier (Schuss aus der Hüfte, Formgen v1 `wtypes.MELEE`), kein Magazin (Energiezelle BEC-1 wie BASIC-17), kein Hülsenauswurf,
  keine Ego-Griffe (wie BASIC-17).

Herkunft der Zahlen: V = Vorgabe (BASIC-17 bzw. Familie/Schnittstelle), A = Annahme (Entwurf 0.20), G = gemessen; Zahlen ohne Kennung
sind A (Entwurf 0.20, an den Renders r1–r3 gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, grip_v21, energy_cell, R_BODY, R_MID, R_SMALL, R_FINE)

META = dict(id='EXTENDED-17', num='E17', sheet_id='EA17', type='glaive', type_de='Glefe', type_en='Glaive', family='BASIC',
            name='Gorget', nick='Ringkragen', ammo='special', fire='melee_projectile_shield',
            reference_length_m=1.595, reference_length_source='A: Entwurf 0.20 (BASIC-17 1,40 m als Rahmen, V; Schaft länger)',
            inspired_by='BASIC-17 Familie; Kragenrhythmus als Haltung',
            summary='Glefe mit Ringkragen-Schaft, Keilklinge über der Schusslinie und Emitter-Laterne (EXTENDED-Reihe).')
ASSEMBLIES = [   # V: Baugruppen wie BASIC-17 (assemblies('shaft', 'receiver', 'ammo', 'grip_controls', 'support', 'blade', 'shield'))
    dict(id='shaft', de='Stange', en='Shaft'),
    dict(id='receiver', de='Hauptgehäuse', en='Receiver'),
    dict(id='ammo', de='Munitionsversorgung', en='Ammunition feed'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
    dict(id='support', de='Stützbereich', en='Support'),
    dict(id='blade', de='Klinge', en='Blade'),
    dict(id='shield', de='Schild', en='Shield'),
]

AX = 40                 # V: Schaftachse wie BASIC-17 (Griff BGM-1 darunter)
R_SHAFT = 13.0          # V: Schaft r 13 wie BASIC-17
LEAN = 14 / 54          # A: Anlauf der Kragenstirn (14 mm auf 54 mm Höhe), allen Kragen gemeinsam
F_BUTT, F_TIP = -425, 1170   # A: Stoßende, Klingenspitze → 1,595 m (Runde 2: Klinge 30 mm länger)
GRIP_TOP = 18           # A: Griff BGM-1 unter dem Abzugskragen (BASIC-17 grip_rifle top 20, V)


def collar(f0, f1, u0, u1, chamfer=4.0):
    """Kragenprofil (f, u): hinten senkrecht mit Fase, Stirn vorgeneigt (oben um LEAN × Höhe zurück)."""
    back = (u1 - u0) * LEAN
    return [(f0, u0 + chamfer), (f0 + chamfer, u0), (f1, u0), (f1 - back, u1), (f0 + chamfer, u1), (f0, u1 - chamfer)]


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


def stripe(f_bottom, u0, u1, width):
    """Streifen parallel zur Kragenstirn: unten ab f_bottom, oben um LEAN × Höhe zurück."""
    back = (u1 - u0) * LEAN
    return [(f_bottom, u0), (f_bottom + width, u0), (f_bottom + width - back, u1), (f_bottom - back, u1)]


# A (Runde 2, r1 zu klein für den Schaft, Takt unklar): Zellen- und Kopfkragen gleich groß (84 × 54), Endkragen größer
C0 = (-392, -344, 18, 62, 32)    # A: Endkragen (f0, f1, u0, u1, Breite)
C1 = (-84, 118, 16, 70, 40)      # A: Abzugskragen (Gehäuse), Teilung bei u 34
C2 = (330, 414, 14, 68, 38)      # A: Zellenkragen
C3 = (640, 724, 14, 68, 38)      # A: Kopfkragen
SEAM_U = 34.0                    # A: Teilung Creme/Graphit am Abzugskragen (36:18 → 67:33)
LANTERN = (724, 808, 12, 70, 30)  # A: Laternenrahmen (Runde 2: 30 breit für die größere Linse)
WINDOW = (736, 796, 20, 62)      # A: Fenster quer durch Rahmen und Schildflügel (Negativraum)
F_MUZZLE = 808
BLADE_F, BLADE_U = (800, F_TIP), 50.0   # A: Klinge ab Laternenfront, Rücken bei u 50 (10 mm über der Schusslinie r 6,5)
SPINE_W, RIDGE, EDGE_U, H_BLADE = 10.0, 20.0, 40.0, 52.0   # A: Rückenfläche 10 mm, Grat 20 mm, Schneidenband ab 40, Höhe 52
CLIP = (1088, 1170, 63.0)        # A: Meißelschnitt oben ab f 1088 zur Spitze (f 1170, u 63)
HEEL = (1118, 1170)              # A: Rücken steigt ab f 1118 zur Spitze

_c1 = collar(*C1[:4])
P = []
# ---------------------------------------------------------------- Schaft und Endkragen
P += [
    cyl('shaft', 'Stange', 'Shaft', 'shaft', 'graphite', 'Trägt alle Kragen; durchgehend', 'durchgehend, in den Kragen verklebt',
        'f', (AX, 0), C0[0] + 4, LANTERN[0] + 10, R_SHAFT, segs=20, bevel=R_SMALL),   # A (Runde 3): 20 Segmente (Dreiecksziel 20 k)
    prof('end_collar', 'Endkragen', 'End collar', 'shaft', 'shell', 'Fasst das Stoßende; erster Kragen im Takt',
         'auf die Stange geklemmt', collar(*C0[:4]), C0[4], bevel=R_MID),
    cyl('butt_cap', 'Stoßkappe', 'Butt cap', 'shaft', 'dark_metal', 'Gegengewicht und Stoßende', 'in den Endkragen geschraubt',
        'f', (AX, 0), F_BUTT + 6, C0[0] + 2, 15, r1=17, segs=24, bevel=R_MID),
    cyl('butt_crown', 'Stoßkrone', 'Butt crown', 'shaft', 'trim', 'Blanker Abschluss', 'auf die Stoßkappe gepresst',
        'f', (AX, 0), F_BUTT, F_BUTT + 7, 10, segs=24, bevel=0.6),
]
# ---------------------------------------------------------------- Abzugskragen (Gehäuse) mit Griff BGM-1
P += [
    prof('housing', 'Abzugskragen', 'Trigger collar', 'receiver', 'shell', 'Abzugsmechanik und Schildsteuerung; zweiter Kragen',
         'um die Stange geklemmt, auf das Unterteil geschraubt (Fuge)', clip_u(_c1, SEAM_U + 0.5, True), C1[4], bevel=R_BODY,
         cuts=[dict(shape='prof', pts=[(-64, 42), (62, 42), (57, 63), (-64, 63)], w=3.0, x=sx * (C1[4] / 2 + 0.6)) for sx in (1, -1)]
         + [cut_box(4, 22, 64, 74, 11)]),    # Schalterbahn oben (Daumen)
    prof('housing_base', 'Abzugsunterteil', 'Trigger base', 'receiver', 'graphite', 'Abzugsgruppe, Griffaufnahme',
         'unter dem Abzugskragen, Fuge 1 mm', clip_u(_c1, SEAM_U - 0.5, False), C1[4] - 2, bevel=R_MID),
    prof('panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über der Schildsteuerung',
         'in die Mulde geschraubt (4 Schrauben)', [(-62, 44), (60, 44), (55.5, 61), (-62, 61)], 1.2, bevel=R_FINE, x=C1[4] / 2 - 0.8),
    prof('panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über der Abzugsmechanik',
         'in die Mulde geschraubt (4 Schrauben)', [(-62, 44), (60, 44), (55.5, 61), (-62, 61)], 1.2, bevel=R_FINE, x=-C1[4] / 2 + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-57, 48), (-57, 57), (50, 48), (48, 57)], C1[4] / 2 - 0.2, r=1.5, h=0.7))),
    box('shield_switch', 'Schildschalter', 'Shield switch', 'grip_controls', 'accent', 'Klappt die Schildflügel auf (Daumen)',
        'in der Schalterbahn oben am Abzugskragen geführt', 6, 14, 68, 74.5, 9, bevel=R_FINE,
        move=dict(kind='translate', pivot=(10, 71, 0), vector_mm=(8, 0, 0), event='shield')),
    # A: rechts auf dem Graphitunterteil, linksbündig nach vorn: 0,62 × 5 × 12 ≈ 37 mm ab f −70 → bis −33 (Unterteil u 16–33)
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC EX-17“ (einzige Schrift)', 'aufgedruckt',
         bevel=0, text='BASIC  EX-17', size=5.0, f=-70, u=22, x=-(C1[4] - 2) / 2 - 0.05, side=-1, depth=0.12),
]
P += grip_v21(top=GRIP_TOP)
# ---------------------------------------------------------------- Zellenkragen mit Energiezelle BEC-1
P += [
    prof('cell_collar', 'Zellenkragen', 'Cell collar', 'ammo', 'shell', 'Zellenschacht; dritter Kragen', 'um die Stange geklemmt',
         collar(*C2[:4]), C2[4], bevel=R_BODY),
    part('cell_release', 'Zellenhalter', 'Cell release', 'ammo', 'cyl', 'accent', 'Gibt die Energiezelle frei', 'Druckknopf links',
         bevel=R_FINE, axis='x', c=(352, 41), a0=C2[4] / 2 - 0.5, a1=C2[4] / 2 + 3.5, r=4.5, segs=20,
         move=dict(kind='translate', pivot=(352, 41, C2[4] / 2), vector_mm=(0, 0, -2.5), event='reload')),
]
P += energy_cell('energy_cell', 346, 398, C2[3] - 1, C2[3] + 15, 24, (0, 60, 0))   # V: BEC-1, Entnahme nach oben
# ---------------------------------------------------------------- Stützgriff
P += [
    cyl('support_grip', 'Stützmanschette', 'Support sleeve', 'support', 'rubber', 'Griffbereich der Stützhand; Rillen',
        'auf die Stange geschoben', 'f', (AX, 0), 432, 624, 17.5, segs=20, bevel=R_SMALL,
        cuts=[dict(shape='cyl', axis='f', c=(AX, 0), a0=f, a1=f + 2.4, r=20, r_in=16.6, segs=20) for f in range(448, 616, 18)]),
]
# ---------------------------------------------------------------- Kopf: Kopfkragen, Laterne, Emitter, Klinge
P += [
    prof('head_collar', 'Kopfkragen', 'Head collar', 'blade', 'shell', 'Trägt Laterne, Klinge und Schildscharniere; vierter Kragen',
         'um die Stange geklemmt', collar(*C3[:4]), C3[4], bevel=R_BODY),
    part('collar_stripe', 'Kragenstreifen', 'Collar stripe', 'blade', 'multi', 'accent',
         'Lackierter Streifen parallel zur Stirn (einziges Grafikelement)', 'lackiert, beidseitig am Kopfkragen', bevel=0,
         items=[dict(shape='prof', pts=stripe(694, C3[2] + 5, C3[3] - 3, 8), w=0.6, x=sx * (C3[4] / 2 + 0.05)) for sx in (1, -1)]),
    box('lantern', 'Laterne', 'Emitter lantern', 'blade', 'anodized', 'Rahmen um Emitter und Spulen; Fenster quer durch (Negativraum)',
        'vorn in den Kopfkragen geschraubt', *LANTERN[:4], LANTERN[4], bevel=R_MID,
        cuts=[cut_box(*WINDOW, 60), dict(shape='cyl', axis='f', c=(AX, 0), a0=794, a1=F_MUZZLE + 4, r=10.5, segs=24)]),
    cyl('emitter_body', 'Emitterrohr', 'Emitter tube', 'blade', 'metal', 'Führt die Ladung zur Linse; im Fenster sichtbar',
        'in Kopfkragen und Laternenfront gelagert', 'f', (AX, 0), LANTERN[0] - 4, F_MUZZLE - 6, 6.5, segs=24),
    part('emitter_coils', 'Spulen', 'Coils', 'blade', 'multi', 'dark_metal', 'Bündeln die Ladung; frei im Fenster',
         'auf das Emitterrohr gepresst', bevel=0.4, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(AX, 0), a0=f, a1=f + 6, r=10.5, segs=16) for f in (744, 760, 776)]),
    cyl('emitter', 'Emitterlinse', 'Emitter lens', 'blade', 'energy', 'Gibt das Projektil ab; leuchtet beim Schuss (Blickfang)',
        'in der Bohrung der Laternenfront', 'f', (AX, 0), F_MUZZLE - 10, F_MUZZLE - 3, 8.5, segs=24, bevel=0,
        move=dict(kind='glow', pivot=None, event='fire', max=6.0)),
    cyl('emitter_crown', 'Linsenkrone', 'Lens crown', 'blade', 'trim', 'Blanke Fassung der Linse', 'in die Laternenfront gepresst',
        'f', (AX, 0), F_MUZZLE - 4, F_MUZZLE + 1.5, 13.0, r_in=9.0, segs=24, bevel=0.5),   # A (Runde 2): Linse r 8,5, Krone r 13
    prof('blade_mount', 'Klingenhalter', 'Blade mount', 'blade', 'dark_metal', 'Klemmt die Klingenwurzel über der Laterne',
         'auf die Laternenfront geschraubt', [(LANTERN[0] + 62, BLADE_U - 1), (852, BLADE_U - 1), (852 - 46 * LEAN, BLADE_U + 46),
                                              (LANTERN[0] + 62, BLADE_U + 46)], SPINE_W + 6, bevel=R_SMALL),
    part('mount_screws', 'Halterschrauben', 'Mount screws', 'blade', 'multi', 'trim', 'Halten Klingenhalter und Klinge',
         'quer durch den Halter', bevel=0.2, items=mirror(screws([(800, 62), (800, 84), (828, 62), (826, 84)], (SPINE_W + 6) / 2 - 0.2,
                                                                  r=1.8, h=0.7))),
]
_outline = [dict(shape='prof', pts=[(CLIP[0], BLADE_U + H_BLADE), (CLIP[1] + 5, CLIP[2] - 1.2), (CLIP[1] + 40, CLIP[2] - 1.2),
                                     (CLIP[1] + 40, BLADE_U + 90), (CLIP[0], BLADE_U + 90)], w=60),
            dict(shape='prof', pts=[(HEEL[0], BLADE_U), (HEEL[1] + 5, CLIP[2] + 1.2), (HEEL[1] + 40, CLIP[2] + 1.2),
                                    (HEEL[1] + 40, BLADE_U - 30), (HEEL[0], BLADE_U - 30)], w=60)]
P += [
    part('blade', 'Klinge', 'Blade', 'blade', 'xprof', 'metal', 'Keilklinge mit Rückenfläche; Meißelspitze (Tanto)',
         'im Klingenhalter geklemmt', bevel=R_FINE, f0=BLADE_F[0], f1=BLADE_F[1], cu=BLADE_U,
         pts=[(-SPINE_W / 2, 0), (SPINE_W / 2, 0), (SPINE_W / 2, RIDGE), (1.5, EDGE_U), (-1.5, EDGE_U), (-SPINE_W / 2, RIDGE)],
         cuts=list(_outline)),
    part('blade_edge', 'Schneide', 'Edge', 'blade', 'xprof', 'trim', 'Blanke Schneide oben', 'mit der Klinge verbunden', bevel=0.4,
         f0=BLADE_F[0] + 6, f1=BLADE_F[1], cu=BLADE_U, pts=[(-1.5, EDGE_U - 0.5), (1.5, EDGE_U - 0.5), (0.6, H_BLADE), (-0.6, H_BLADE)],
         cuts=list(_outline)),
]
# ---------------------------------------------------------------- Schildflügel (klappen um das vordere Scharnier nach außen)
# A (Runde 2, r1 lagen sie als Rahmen flach auf der Laterne): hohe Flügel mit 8 mm Luft zur Laterne, Hinterkante im Kragen-Anlauf,
# Scharnierarme vorn; das Fenster geht weiter quer durch Flügel und Laterne.
SHIELD_X = LANTERN[4] / 2 + 8 + 2          # A: Flügelmitte 10 mm außerhalb der Laterne (8 mm Luft, Flügel 4 mm)
_shield = [(734, -14), (F_MUZZLE - 2, -6), (F_MUZZLE - 2, 86), (734 - 108 * LEAN, 94)]
for sid, sx, de, en in (('shield_l', 1, 'Schildflügel links', 'Shield wing left'), ('shield_r', -1, 'Schildflügel rechts', 'Shield wing right')):
    x = sx * SHIELD_X
    P.append(prof(sid, de, en, 'shield', 'shell', 'Klappt zum Blocken nach vorn-außen auf; Fenster wie die Laterne',
                  'Scharnier vorn an der Laterne', _shield, 4, x=x, bevel=R_SMALL,
                  cuts=[cut_box(*WINDOW, 10, x=x)],
                  move=dict(kind='rotate', pivot=(F_MUZZLE - 2, AX, x), axis='u', range_deg=(0, -70 * sx), event='shield',
                            expect=((734, AX, x), (0, 0, sx)))))
P.append(part('shield_hinges', 'Schildscharniere', 'Shield hinges', 'shield', 'multi', 'dark_metal',
              'Tragen die Schildflügel; Drehachse senkrecht vorn', 'an die Laternenfront geschraubt', bevel=0.4,
              items=[dict(shape='box', f0=F_MUZZLE - 9, f1=F_MUZZLE - 1, u0=u0, u1=u0 + 14, w=SHIELD_X - LANTERN[4] / 2 + 1,
                          x=sx * (LANTERN[4] / 2 + SHIELD_X) / 2) for sx in (1, -1) for u0 in (2, 66)]
              + [dict(shape='cyl', axis='u', c=(F_MUZZLE - 2, sx * SHIELD_X), a0=-4, a1=84, r=3.0, segs=16) for sx in (1, -1)]))
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='hintere Hand mit Abzug (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(533, AX, 0), part='support_grip', note='Mitte der Stützmanschette'),
    'Socket_Muzzle': dict(at=(F_MUZZLE, AX, 0), part='emitter', note='Projektilaustritt in der Laternenfront'),
    'Socket_BladeCenter': dict(at=(970, BLADE_U + 26, 0), part='blade', note='Trefferzentrum'),
}
EGO_GRIPS = {}      # V: Nahkampf ohne Ego-Übertrag (wie BASIC-17)
POINTS = {}
ACTIONS = {
    'fire': dict(de='Projektil abgeben', frames=14, step=1, keys={
        'trigger': [(0, 0), (2, 1), (6, 0)], 'emitter': [(0, 0), (2, 1), (8, 0)]}, events=[(2, 'shot')]),
    'shield': dict(de='Schild aufklappen, halten, schließen', frames=40, step=2, keys={
        'shield_switch': [(0, 0), (4, 1), (30, 1), (34, 0)],
        'shield_l': [(0, 0), (8, 1), (30, 1), (38, 0)], 'shield_r': [(0, 0), (8, 1), (30, 1), (38, 0)]},
        events=[(8, 'shield_up'), (38, 'shield_down')], view=(0.5, -0.8, 0.45)),
    'reload': dict(de='Energiezelle wechseln', frames=70, keys={
        'cell_release': [(0, 0), (6, 1), (14, 0)], 'energy_cell': [(0, 0), (16, 1), (34, 1), (50, 0)]},
        events=[(16, 'cell_out'), (50, 'cell_in')]),
}
EXPLODE = {'shield_l': (0, 0, 70), 'shield_r': (0, 0, -70), 'blade': (130, 0, 0), 'ammo': (0, 80, 0), 'grip_controls': (0, -60, 0),
           'support': (0, 0, 0)}
HERO = (0.66, -0.42, 0.62)   # A: von links vorn oben – Laterne mit Linse (Blickfang) und Kragenfolge zur Kamera
