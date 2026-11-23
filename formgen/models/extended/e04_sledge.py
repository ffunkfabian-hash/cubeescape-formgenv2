"""EXTENDED-04 „Sledge“ – eigenständige Sci-Fi-Handkanone der BASIC-Familie (Formgen v2 0.18 „Holster“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-04: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Kimme/Korn K1 „Klammer“, Baugruppen) und
Hilfen (`cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main`
(`tools/extended_render.py`). Auswahl, Skizzen und Nachbesserung: docs/extended.md › EXTENDED-04.

Formsprache (Stilhandbuch BALLON §3)
| Frage | EXTENDED-04 „Sledge“ |
|---|---|
| Leitmerkmal der Silhouette | Hammerkopf: ein schwerer Kopf (Prallkammer) vorn, schlanker Hals über offener Kehle, dahinter Rahmen mit freier Trommel; Oberlinie Sattel – Hals – Kopf |
| Schichten | Rahmen (Graphit) → Creme-Oberbrücke mit Sattel → Hals 4 mm schmaler als der Rahmenkopf → Kopf breiter als alles (Draufsicht ebenfalls Hammer) → eloxierte Stirnplatte 2 mm vor dem Kopf |
| Negativraum | offene Kehle zwischen Rahmen und Kopf unter dem Hals; Prallkammer quer durch den Kopf, drei Prallplatten im Fenster, zwei Gasschlitze oben |
| Blickfang | Zündauge links hinter der Trommel: runde Leuchtlinse mit blankem Ring (genau eine Leuchtfunktion außer dem Visier) |
| Zweiton-Blockung | Oberbrücke mit Sattel und Kopf Lack (`shell`) als zwei helle Massen, dazwischen der Hals eloxiert (`anodized`, Laufmantel); Rahmen Polymer (`graphite`), Trommel, Kran und Prallplatten `dark_metal`, Stirnplatte und Hahn `anodized` |
| Querschnitt | Doppel-T: Brücke, Hals und Kopf mit durchgehender Längsnut je Seite (6 mm hoch, 3 mm tief); die Halsnut läuft auf Laufhöhe in die Prallkammer |
| Grafik | ein Chevronpaar am Kieferblock des Kopfes, nach vorn zeigend; ein Schriftzug rechts am Hals |
| Front | Kopf mit Fasen oben und unten → eloxierte Stirnplatte → Mündungsmulde → blanke Krone; Prallkammer und Gasschlitze dahinter |
| Übergänge | Kiefer des Kopfes läuft mit schräger Rückseite zur Kehle; Sattel fällt mit einer Rampe auf den Hals |
| Ergonomie | Griff BGM-1 wie die Familie (Socket_Hand 0/0), Hahnsporn unter der Visierlinie, Trommelriegel unter dem Daumen links |
| Akzente kameranah (A3) | Zündauge, Trommelriegel und Hahn links hinten; Prallkammer mit drei breiten Platten statt vieler feiner |
| Teilungen (A8) | Creme oben ≈ 70 %, Graphit unten ≈ 30 % der Seitenfläche über dem Griff |
| Lesbarkeit (A1/A7) | Seitensilhouette eigenständig gegen BASIC-04 und EXTENDED-01/05 (tests/test_extended_faustwaffen.py) |

Schlichtheitsbudget: Leuchten 2 Funktionen (Zündauge; Visier: Klammern und Kornpunkt) · Grafik 1 Chevronpaar · Schrift 1 · Orange 1
außerhalb des Visiers (Trommelriegel; dazu der Klemmhebel des Visiers) · Schrauben nur an der Stirnplatte.

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-04 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.18),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.18, an den Renders r1–r3 gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import part, prof, box, cyl, cut_box, screws, mirror, assemblies, grip_v21, klammer, R_BODY, R_MID, R_SMALL, R_FINE
from basic.variant import collect

META = dict(id='EXTENDED-04', num='E04', sheet_id='EA04', type='hand_cannon', type_de='Handfeuerwaffe', type_en='Hand Cannon',
            family='BASIC', name='Sledge', nick='Hammerkopf', ammo='primary', fire='semi_auto_double_action',
            reference_length_m=0.300, reference_length_source='A: Entwurf 0.18 (BASIC-04 0,30 m als Rahmen, V)',
            inspired_by='BASIC-04 Familie; Formgen v1 Handkanone (schwere Stirn) als Haltung',
            summary='Handkanone mit Hammerkopf-Prallkammer, schlankem Hals über offener Kehle und freier Trommel (EXTENDED-Reihe).')
ASSEMBLIES = assemblies('receiver', 'barrel', 'ammo', 'sight', 'grip_controls', 'mechanism')   # V: wie BASIC-04

GRIP_TOP = 24                      # V: Griffoberkante = Rahmenunterkante wie BASIC-04
BORE = 71                          # V: Laufachse = oberste Kammer wie BASIC-04
CYL_U, CYL_R, CYL_F = 57, 24.0, (18, 80)   # A: Trommelachse (V wie BASIC-04), Radius 24 (BASIC 22,5: schwerer), Länge 62
CH = 14                            # V: Kammerkreis 14 mm (BORE − CYL_U)
STRAP = CYL_U + CYL_R + 1.5        # A: Unterkante Oberbrücke, 1,5 mm über der Trommel
WIN_U = CYL_U - CYL_R - 1.5        # A: Unterkante Trommelfenster; Steg zum Rahmenboden 7,5 mm (≥ 3 × R_MID, Stilhandbuch §9)
SADDLE = 98                        # A: Oberkante Sattel und Kopf = Träger des Visiers (Linie + 11 → 109, 38 über der Laufachse)
NECK = (59, 87)                    # A: Hals unten/oben, 28 mm hoch (r1: 20 mm wirkte wie ein Werkzeugstiel)
HEAD_F, HEAD_BOT = (190, 254), GRIP_TOP + 4   # A: Kopf hinten/vorn (r1: 200/262, Hals zu lang); Kiefer 4 mm über der Rahmenlinie
FRONT = 257                        # A: Stirnplatte vorn
FR_W, ST_W, NK_W, HD_W = 34, 32, 26, 38   # A: Rahmen (V wie BASIC-04), Oberbrücke, Hals, Kopf
PIVOT = (CYL_U - 27, 14)           # A: Kranachse (u, x) unten links im Rahmen


def groove(f0, f1, u0, u1, w, depth=3.0):
    """Längsnut beidseitig (Doppel-T-Querschnitt): Schneidkörper je Seite, `depth` tief in die Seitenfläche der Breite w."""
    return [cut_box(f0, f1, u0, u1, 2 * depth, x=s * w / 2) for s in (1, -1)]


P = []
# ---------------------------------------------------------------- Rahmen (Graphit) mit Trommelfenster, Hahn, Riegel, Zündauge
EYE = (2, 62)                      # A: Zündauge links hinter der Trommel (f, u), Ego-Seite
P += [
    prof('frame', 'Rahmen', 'Frame', 'receiver', 'graphite', 'Trägt Trommel, Hahn, Abzug, Griff und Hals; Trommelfenster',
         'Grundkörper', [(-13.5, GRIP_TOP), (96, GRIP_TOP), (100, GRIP_TOP + 3), (110, NECK[0] - 1), (CYL_F[1] + 2.5, NECK[0] - 1),
                         (CYL_F[1] + 2.5, WIN_U), (CYL_F[0] - 1.5, WIN_U), (CYL_F[0] - 1.5, STRAP), (-8, STRAP), (-8, 89),
                         (-19, 89), (-26, 85), (-30.5, 77), (-31, 63), (-26, 48)],
         FR_W, bevel=R_MID,
         cuts=[cut_box(-36, -8, 64, 95, 9),                                                  # Hahnschlitz
               dict(shape='cyl', axis='x', c=EYE, a0=FR_W / 2 - 2, a1=FR_W / 2 + 2, r=9.6, segs=32)]),   # Mulde Zündauge
    prof('hammer', 'Hahn', 'Hammer', 'mechanism', 'anodized', 'Wird gespannt und schlägt beim Schuss vor; breiter Sporn',
         'Drehpunkt hinten im Rahmen', [(-24, 62), (-12, 62), (-10, 84), (-15, 93), (-29, 98), (-36, 97), (-37, 92), (-26, 84)], 8, bevel=R_FINE,
         move=dict(kind='rotate', pivot=(-19, 66, 0), axis='x', range_deg=(0, 28), event='cock', expect=((-36, 96, 0), (-1, 0, 0)))),
    cyl('cylinder_latch', 'Trommelriegel', 'Cylinder latch', 'grip_controls', 'accent', 'Gibt den Kran frei (Daumen)',
        'links am Rahmen unter dem Zündauge, gleitet nach vorn', 'x', (6, 40), FR_W / 2 - 0.5, FR_W / 2 + 3, 4.2, segs=20,
        move=dict(kind='translate', pivot=(6, 40, FR_W / 2), vector_mm=(6, 0, 0), event='reload', expect=((6, 40, FR_W / 2), (1, 0, 0)))),
    cyl('eye_ring', 'Augenring', 'Eye ring', 'receiver', 'trim', 'Fasst das Zündauge; blanker Ring', 'in die Mulde gepresst',
        'x', EYE, FR_W / 2 - 2, FR_W / 2 + 1.2, 9.4, r_in=7.2, segs=32, bevel=0.5),
    cyl('eye_lens', 'Zündaugenglas', 'Eye lens', 'receiver', 'glass', 'Schützt das Zündauge', 'im Augenring',
        'x', EYE, FR_W / 2 - 1.2, FR_W / 2 - 0.4, 7.2, segs=32, bevel=0),
    cyl('eye_glow', 'Zündauge', 'Ignition eye', 'receiver', 'energy', 'Ladezustand der Kammer (Blickfang)', 'hinter dem Glas',
        'x', EYE, FR_W / 2 - 2, FR_W / 2 - 1.3, 6.0, segs=32, bevel=0),
]
# ---------------------------------------------------------------- Kran und Trommel (schwenkt nach links unten aus)
_chambers = [dict(shape='cyl', axis='f', c=(CYL_U + CH * math.cos(math.radians(a)), CH * math.sin(math.radians(a))),
                  a0=CYL_F[1] - 5, a1=CYL_F[1] + 1, r=4.6, segs=16) for a in range(0, 360, 60)]
_grooves = [dict(shape='cyl', axis='f', c=(CYL_U, 0), a0=f, a1=f + 3, r=CYL_R + 1, r_in=CYL_R - 1.6, segs=48) for f in (28, 63)]
P += [
    part('crane', 'Kran', 'Crane', 'mechanism', 'multi', 'dark_metal', 'Trägt die Trommel; schwenkt nach links unten aus',
         'Achse unten links im Rahmen', bevel=R_FINE,
         move=dict(kind='rotate', pivot=(50, PIVOT[0], PIVOT[1]), axis='f', range_deg=(0, -90), event='reload',
                   note='Trommel schwenkt vollständig links neben den Rahmen', expect=((50, CYL_U, 0), (0, 0, 1))),
         items=[dict(shape='cyl', axis='f', c=PIVOT, a0=CYL_F[0], a1=CYL_F[1] + 2.5, r=3.2, segs=12),
                dict(shape='xprof', f0=CYL_F[1], f1=CYL_F[1] + 2.5, cu=CYL_U,
                     pts=[(-4.5, 3), (4.5, 3), (PIVOT[1] + 4, PIVOT[0] - CYL_U + 2), (PIVOT[1] - 3, PIVOT[0] - CYL_U - 3)])]),
    cyl('cylinder', 'Trommel', 'Cylinder', 'ammo', 'dark_metal', 'Sechs Kammern, glatt mit zwei Rillenringen; dreht je Schuss um 60°',
        'auf dem Kran gelagert', 'f', (CYL_U, 0), CYL_F[0], CYL_F[1], CYL_R, bevel=R_SMALL, segs=48, parent_part='crane',
        cuts=_chambers + _grooves, move=dict(kind='rotate', pivot=(50, CYL_U, 0), axis='f', range_deg=(0, -60), event='fire',
                                              note='oben nach links (von hinten gesehen gegen den Uhrzeigersinn)',
                                              expect=((50, BORE, 0), (0, 0, 1)))),
]
# ---------------------------------------------------------------- Oberbrücke mit Sattel, Hals, Kopf (Creme)
P += [
    prof('strap', 'Oberbrücke', 'Top strap', 'receiver', 'shell',
         'Brücke über der Trommel; hinten der Sattel als Träger der Kimme, fällt mit einer Rampe auf den Hals',
         'auf den Rahmen gesetzt, je Seite 1 mm schmaler (Stufe)',
         [(-8, STRAP), (CYL_F[1] + 2.5, STRAP), (CYL_F[1] + 2.5, NECK[1]), (100, NECK[1]), (88, SADDLE), (-4, SADDLE), (-8, SADDLE - 4)],
         ST_W, bevel=R_MID, cuts=groove(-12, 80, 87, 93, ST_W)),
    prof('neck', 'Hals', 'Neck', 'receiver', 'anodized', 'Laufmantel zwischen Brücke und Kopf; schlank über der offenen Kehle (r3: eloxiert statt Creme)',
         'auf den Rahmenkopf gesetzt (Fuge 1 mm), unter der Brücke, vorn in den Kopf gesteckt',
         [(CYL_F[1] + 2.5, NECK[0]), (HEAD_F[0] + 2, NECK[0]), (HEAD_F[0] + 2, NECK[1]), (CYL_F[1] + 2.5, NECK[1])], NK_W, bevel=R_MID,
         cuts=groove(CYL_F[1], HEAD_F[0] + 4, 70, 76, NK_W)),
    prof('head', 'Kopf', 'Head', 'barrel', 'shell', 'Prallkammer: bremst den Rückstoß; Fenster quer durch, zwei Gasschlitze oben',
         'auf den Hals gesteckt, mit der Stirnplatte verschraubt',
         [(HEAD_F[0], NECK[0] - 2), (HEAD_F[0] + 14, HEAD_BOT), (HEAD_F[1] - 12, HEAD_BOT), (HEAD_F[1], HEAD_BOT + 12),
          (HEAD_F[1], SADDLE - 6), (HEAD_F[1] - 6, SADDLE), (HEAD_F[0] + 12, SADDLE), (HEAD_F[0], NECK[1] + 2)], HD_W, bevel=R_MID,
         cuts=groove(HEAD_F[0] - 2, HEAD_F[1] + 2, 70, 76, HD_W)
         + [cut_box(208, 240, 60, 83, 60),                                                    # Prallkammer quer durch
            cut_box(212, 217, 81, SADDLE + 2, 14), cut_box(221, 226, 81, SADDLE + 2, 14),    # Gasschlitze oben
            dict(shape='cyl', axis='f', c=(BORE, 0), a0=HEAD_F[1] - 8, a1=HEAD_F[1] + 2, r=9, segs=32)]),   # Mündungsbohrung
    prof('face_plate', 'Stirnplatte', 'Face plate', 'barrel', 'anodized', 'Schließt den Kopf vorn; Mündungsmulde',
         'vorn auf den Kopf geschraubt (4 Schrauben), 3 mm Stufe', [(HEAD_F[1] - 1, HEAD_BOT + 10), (FRONT, HEAD_BOT + 12),
                                                                    (FRONT, SADDLE - 8), (HEAD_F[1] - 1, SADDLE - 6)], 30, bevel=R_SMALL,
         cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=FRONT - 6, a1=FRONT + 2, r=11.5, segs=32),
               dict(shape='cyl', axis='f', c=(BORE, 0), a0=HEAD_F[1] - 2, a1=FRONT + 2, r=8.4, segs=32)]),
    part('face_screws', 'Stirnschrauben', 'Face screws', 'barrel', 'multi', 'trim', 'Halten die Stirnplatte', 'in der Stirnplatte',
         bevel=0.2, items=screws([(u, x) for u in (HEAD_BOT + 17, SADDLE - 14) for x in (10.5, -10.5)], FRONT - 0.2, r=1.5, h=0.8, axis='f')),
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; endet vor der Prallkammer', 'in den Rahmen geschraubt',
        'f', (BORE, 0), CYL_F[1] + 1, 209, 7.5, segs=24),
    cyl('muzzle_crown', 'Laufkrone', 'Barrel crown', 'barrel', 'trim', 'Blanke Laufmündung in der Prallkammer', 'Laufende',
        'f', (BORE, 0), 205, 209, 8.4, r_in=4.6, segs=24, bevel=0.5),
    part('baffles', 'Prallplatten', 'Baffles', 'barrel', 'multi', 'dark_metal', 'Lenken das Gas nach oben; im Fenster sichtbar',
         'im Kopf verstiftet', bevel=0.4, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f, a1=f + 3.5, r=14, r_in=5.2, segs=32) for f in (214, 222.5, 231)]),
    cyl('muzzle', 'Mündungsring', 'Muzzle ring', 'barrel', 'trim', 'Blanke Stufe in der Mündungsmulde', 'in die Stirnplatte gepresst',
        'f', (BORE, 0), FRONT - 6, FRONT - 3, 11.4, r_in=5.6, segs=32, bevel=0.5),
    part('chevron', 'Chevronpaar', 'Chevron pair', 'receiver', 'multi', 'accent', 'Lackiertes Chevronpaar (einziges Grafikelement)',
         'lackiert, beidseitig am Kieferblock', bevel=0,
         items=[dict(shape='prof', pts=[(f, 34), (f + 6, 34), (f + 13, 44.5), (f + 6, 55), (f, 55), (f + 7, 44.5)], w=0.3,
                     x=sx * (HD_W / 2 + 0.15)) for f in (216, 227) for sx in (1, -1)]),
    # A: Hals rechts zwischen Rahmenkopf (102) und Kopf (200); linksbündig, läuft nach vorn bis ≈ 147 (0,62 × 4,2 × 12 Zeichen)
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC EX-04“ (einzige Schrift)',
         'aufgedruckt (hell)', bevel=0, text='BASIC  EX-04', size=4.2, f=118, u=64.5, x=-NK_W / 2 - 0.05, side=-1, depth=0.12),
]
# ---------------------------------------------------------------- Griff, Abzug, Bügel (BGM-1 v2.1)
P += grip_v21(top=GRIP_TOP)
# ---------------------------------------------------------------- Visier K1 „Klammer“: Kimme auf dem Sattel, Korn auf dem Kopf
_sight, SIGHT_ANCHORS = klammer(-2, 238, SADDLE)
P += _sight
PARTS = P

ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(-4, -34, 17), part='grip', note='Stützhand umfasst die Griffhand von links (V wie BASIC-04)'),
    'Socket_Muzzle': dict(at=(FRONT, BORE, 0), part='face_plate', note='Stirn der Stirnplatte auf der Laufachse (Prallkammer davor)'),
    'Socket_MagWell': dict(at=(CYL_F[1], CYL_U, 0), part='cylinder', note='Ladestelle: Trommelstirn (ausgeschwenkt beim Nachladen)'),
}
ANCHORS.update(SIGHT_ANCHORS)
# Hülsen (V wie BASIC-04): Trommel – keine Hülse beim Schuss; beim Nachladen fallen die leeren Hülsen hinten aus den Kammern
EJECT = dict(at=(CYL_F[0] - 4, CYL_U, 4), dir=(0.35, 0.3, 1.0), case='revolver', on='reload', event='eject', part='cylinder',
             ring=dict(r_mm=CH, n=6), speed_k=0.35, life_k=2.0,
             src='V wie BASIC-04: beim Nachladen hinten aus den Kammern, langsam nach außen und etwas nach vorn')
# Ego-Griffe (V wie BASIC-04, Kontakte auf diesem Modell): Pistolengriff beidhändig, 'mag' die Trommel, 'charge' der Trommelriegel
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(-2, -34, 19), palm=(0.1, 0.0, -1.0), fingers=(0.75, -0.66, 0.0), fingers_pose='grip',
                    src='V wie BASIC-04: links an Griff und Griffhand'),
    'mag':     dict(part='cylinder', contact=(48, CYL_U, CYL_R + 1.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.25, 0.0),
                    fingers_pose='mag_hold', src='A: links an der Trommel, folgt dem Kran'),
    'charge':  dict(part='cylinder_latch', contact=(6, 40, FR_W / 2 + 3.5), palm=(0.0, 0.0, -1.0), fingers=(0.6, 0.8, 0.0),
                    fingers_pose='pinch', src='A: am Trommelriegel links (Daumen)'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(grip='grip', support='grip'))
ACTIONS = {
    'fire_da': dict(de='Schuss Double Action (Hahn, Trommel)', frames=14, step=1, keys={
        'trigger': [(0, 0), (6, 1), (10, 0)], 'hammer': [(0, 0), (6, 1), (7, 0)], 'cylinder': [(0, 0), (6, 1), (14, 1)]},
        events=[(7, 'shot')]),
    'reload': dict(de='Trommel ausschwenken, laden, einschwenken', frames=72, keys={
        'cylinder_latch': [(0, 0), (6, 1), (14, 0)], 'crane': [(0, 0), (8, 0), (18, 1), (52, 1), (62, 0)]},
        events=[(18, 'cylinder_open'), (24, 'eject'), (40, 'rounds_in'), (62, 'cylinder_closed')], view=(0.55, -0.65, 0.5)),
}
EXPLODE = {'sight': (0, 90, 0), 'ammo': (0, 0, 80), 'barrel': (110, 0, 0), 'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, 60),
           'receiver': (0, 0, 0)}
HERO = (0.78, -0.50, 0.40)   # A: Produktbild von links vorn oben – Zündauge (Blickfang), Trommel und Prallkammer zur Kamera
