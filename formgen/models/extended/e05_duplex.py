"""EXTENDED-05 „Duplex“ – eigenständige Sci-Fi-Seitenwaffe der BASIC-Familie (Formgen v2 0.18 „Holster“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-05: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Kimme/Korn K1 „Klammer“, Baugruppen) und
Hilfen (`cut_box`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main`
(`tools/extended_render.py`). Auswahl, Skizzen und Nachbesserung: docs/extended.md › EXTENDED-05.

Formsprache (Stilhandbuch BALLON §3)
| Frage | EXTENDED-05 „Duplex“ |
|---|---|
| Leitmerkmal der Silhouette | Doppeldeck: flacher Creme-Schlitten als Oberdeck über einem tief liegenden Laufrohr (Unterdeck); vorn trennt sie ein durchgehender Schlitz; flache, durchgehende Oberlinie, kurz |
| Schichten | Rahmen mit Laufrohr (Graphit) → Schlitten (Creme, 6 mm breiter als das Rohr, Fuge 1 mm; Oberdeck je Seite 2 mm eingezogen) → Kapselanzeige im Rahmen, 0,8 mm vorstehend |
| Negativraum | Schlitz zwischen Schlitten und Laufrohr vom Verschlussblock bis zur Stirn, quer ganz offen; Auswurffenster rechts mit Laufkopf |
| Blickfang | Kapselanzeige links am Verschlussblock: leuchtendes Stadionfenster (Munitionsstand) hinter Glas in blankem Rahmen, kameranah (eine Leuchtfunktion außer dem Visier) |
| Zweiton-Blockung | Schlitten Lack (`shell`), Rahmen und Laufrohr Polymer (`graphite`), Griff `rubber`, Magazinboden `anodized`; Teilung Seite ≈ 62:38 (G) |
| Querschnitt | Zweistock: Flachkasten (26 × 20 mm, große Kantenradien) über einem Rundrohr Ø 20, dazwischen 6,5 mm Luft |
| Grafik | ein Chevronpaar vorn am Schlitten, ein Schriftzug rechts am Schlitten |
| Front | zweistufig: Schlittenstirn oben, darunter das Laufrohr 6 mm weiter vorn mit Mündungsmulde und blanker Krone |
| Übergänge | Rahmen geht vor dem Abzugsbügel in das Laufrohr über; Verschlussblock fällt mit einem Radius in den Schlitz |
| Ergonomie | Griff BGM-1 wie die Familie (Socket_Hand 0/0), tiefe Laufachse (12 mm über der Griffoberkante), Schlittenfang und Magazinhalter links unter dem Daumen |
| Akzente kameranah (A3) | Kapselanzeige, Schlittenfang, Magazinhalter links; Rillen am Verschlussblock zum Durchladen |
| Teilungen (A8) | Creme ≈ 62 % der Seitenfläche über dem Griff (G, Seitensilhouette), Graphit ≈ 38 % |
| Lesbarkeit (A1/A7) | Seitensilhouette eigenständig gegen BASIC-05 und EXTENDED-01/04 (tests/test_extended_faustwaffen.py) |

Schlichtheitsbudget: Leuchten 2 Funktionen (Kapselanzeige; Visier: Klammern und Kornpunkt) · Grafik 1 Chevronpaar · Schrift 1 · Orange 2
außerhalb des Visiers (Schlittenfang, Magazinhalter; dazu der Klemmhebel des Visiers) · Schrauben keine.

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-05 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.18),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.18, an den Renders r1–r4 gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import part, prof, box, cyl, cut_box, assemblies, grip_v21, klammer, R_BODY, R_MID, R_SMALL, R_FINE
from basic.variant import collect

META = dict(id='EXTENDED-05', num='E05', sheet_id='EA05', type='sidearm', type_de='Pistole', type_en='Sidearm',
            family='BASIC', name='Duplex', nick='Doppeldeck', ammo='primary', fire='semi_auto',
            reference_length_m=0.197, reference_length_source='A: Entwurf 0.18 (BASIC-05 0,23 m als Rahmen, V; kürzer = kompakt)',
            inspired_by='BASIC-05 Familie; Formgen v1 Seitenwaffe (kompakter Block) als Haltung',
            summary='Kompakte Seitenwaffe mit flachem Schlitten über tief liegendem Laufrohr, Schlitz dazwischen und Kapselanzeige (EXTENDED-Reihe).')
ASSEMBLIES = assemblies('receiver', 'barrel', 'ammo', 'sight', 'grip_controls', 'mechanism')   # V: wie BASIC-05

T15 = math.tan(math.radians(15))   # V: Griffachse 15° (BGM-1)
GRIP_TOP = 30                      # A: Griffoberkante = Rahmenunterkante, 4 mm unter BASIC-05 (34): tiefe Achse
BORE = 42                          # A: Laufachse 12 mm über der Griffoberkante (BASIC-05: 40 mm) – flach, schnell
TUBE_R = 10                        # A: Laufrohr Ø 20 (Lauf Ø 12 mit Schließfeder darum)
RAIL = 40                          # A: Oberkante Rahmen hinten = Gleitbahn des Verschlussblocks
SL_F = (-26, 146)                  # A: Schlitten hinten / Stirn (r1: 166 – zu lang, nicht kompakt)
BLOCK_F = 60                       # A: Ende des Verschlussblocks = Beginn des Schlitzes
SL_U, DECK = 60, 78                # A: Unterkante Oberdeck (Schlitz 8 mm über dem Rohr; r1 6,5 las sich als Strich), Oberkante = Träger des Visiers
TUBE_F = (40, 154)                 # A: Laufrohr; Mündung 8 mm vor der Schlittenstirn
FR_W, SL_W = 24, 26                # A: Rahmenbreite, Schlittenbreite (BASIC-05 26/28)
BUSH_F = (62, 68)                  # A: blanke Laufbuchse am Schlitzanfang
PILL = dict(fc=18, uc=62, length=32, height=10)   # A: Kapselanzeige links am Verschlussblock (Blickfang), Fenster f 2–34, u 57–67
# A (r3): Heck des Schlittens als Viertelkreis R 22 oben hinten (r2: R 14 kaum sichtbar) – rundes, schnelles Heck gegen die harten Blöcke von EXTENDED-04
HECK = [(SL_F[0] + 22 - 22 * math.sin(math.radians(a)), DECK - 22 + 22 * math.cos(math.radians(a))) for a in range(0, 91, 10)]


def capsule(fc, uc, length, height, grow=0.0, n=8):
    """Stadionform (Kapsel) in (f, u): zwei Halbkreise, gerade Flanken; grow vergrößert gleichmäßig (Rahmen, Glas)."""
    r, half = height / 2 + grow, length / 2 - height / 2
    right = [(fc + half + r * math.cos(math.radians(a)), uc + r * math.sin(math.radians(a))) for a in range(-90, 91, 180 // n)]
    left = [(fc - half + r * math.cos(math.radians(a)), uc + r * math.sin(math.radians(a))) for a in range(90, 271, 180 // n)]
    return right + left


def _A(u, d):                       # V: Punkt auf der Griffachse (15° nach hinten geneigt) in Höhe u, um d nach vorn versetzt
    return (u * T15 + d, u)


P = []
# ---------------------------------------------------------------- Rahmen mit Laufrohr (Graphit), Bedienelemente
P += [
    prof('frame', 'Rahmen', 'Frame', 'receiver', 'graphite', 'Trägt Verschlussblock, Abzug, Griff und Magazinschacht; geht vorn ins Laufrohr über',
         'Grundkörper; vorn Wiege um die untere Hälfte des Laufrohrs',
         [(-12.5, GRIP_TOP), (84, GRIP_TOP), (92, 32), (102, 32), (114, BORE), (BLOCK_F + 1, BORE), (BLOCK_F + 1, RAIL), (-23, RAIL),
          (-30, 37.5), (-28, 33)], FR_W,
         bevel=R_SMALL),
    cyl('tube', 'Laufrohr', 'Barrel tube', 'receiver', 'graphite', 'Unterdeck: führt Lauf und Schließfeder; Mündungsmulde vorn',
        'aus dem Rahmen nach vorn (fest)', 'f', (BORE, 0), TUBE_F[0], TUBE_F[1], TUBE_R, segs=40, bevel=R_SMALL,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=TUBE_F[1] - 6, a1=TUBE_F[1] + 2, r=7.6, segs=32)]),
    box('slide_stop', 'Schlittenfang', 'Slide stop', 'grip_controls', 'accent', 'Hält den Schlitten nach dem letzten Schuss offen',
        'links am Rahmen (dreht)', 36, 58, 33, 38.5, 2.2, bevel=R_FINE, x=FR_W / 2 + 0.6,
        move=dict(kind='rotate', pivot=(56, 36, FR_W / 2 + 0.6), axis='x', range_deg=(0, 6), event='reload',
                  note='hebt hinten an, hält den Schlitten offen')),
    cyl('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'accent', 'Löst das Magazin im Griff',
        'Druckknopf links am Griff', 'x', (19, 23), 14.5, 17.5, 4.2, segs=20,
        move=dict(kind='translate', pivot=(19, 23, 16), vector_mm=(0, 0, -2.5), event='reload', expect=((19, 23, 17.5), (0, 0, -1)))),
]
# ---------------------------------------------------------------- Laufbuchse am Schlitzanfang (r2: statt Leuchtring – Glutring ist EXTENDED-10)
P += [
    cyl('bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf im Rohr; blanker Ring am Schlitzanfang',
        'auf das Laufrohr gepresst', 'f', (BORE, 0), BUSH_F[0], BUSH_F[1], TUBE_R + 2.0, segs=40, bevel=0.5),
]
# ---------------------------------------------------------------- Schlitten (Creme): Verschlussblock hinten, Oberdeck vorn
P += [
    prof('slide', 'Schlitten', 'Slide', 'mechanism', 'shell',
         'Verschluss und Oberdeck; läuft beim Schuss zurück, trägt Kimme und Korn; Schlitz über dem Laufrohr',
         'auf den Gleitbahnen des Rahmens (gleitet), Fuge 1 mm',
         [(SL_F[0], RAIL + 1), (BLOCK_F - 8, RAIL + 1), (BLOCK_F, RAIL + 9), (BLOCK_F, SL_U), (SL_F[1] - 5, SL_U), (SL_F[1], SL_U + 5),
          (SL_F[1], DECK - 2), (SL_F[1] - 2, DECK)] + HECK, SL_W, bevel=R_BODY,
         cuts=[cut_box(18, 50, 46, DECK - 5, 16, x=-SL_W / 2),                                 # Auswurffenster rechts
               dict(shape='cyl', axis='f', c=(BORE, 0), a0=TUBE_F[0] - 2, a1=BLOCK_F + 1, r=TUBE_R + 0.8, segs=40),  # Rohrdurchgang
               dict(shape='prof', pts=capsule(**PILL, grow=2.6), w=3, x=SL_W / 2)]                               # Mulde Kapselanzeige
         + [cut_box(BLOCK_F, SL_F[1] + 2, SL_U - 2, DECK + 2, 4, x=sx * SL_W / 2) for sx in (1, -1)]       # Oberdeck je Seite 2 mm eingezogen
         + [cut_box(f, f + 2.4, 47, DECK - 6, 3.0, x=sx * SL_W / 2) for f in (-19, -13, -7) for sx in (1, -1)],   # Rillen
         move=dict(kind='translate', pivot=(40, DECK, 0), vector_mm=(-26, 0, 0), event='fire', expect=((40, DECK, 0), (-1, 0, 0)))),
    prof('pill_frame', 'Anzeigenrahmen', 'Counter frame', 'mechanism', 'trim', 'Fasst die Kapselanzeige; blanker Rahmen',
         'in die Mulde des Verschlussblocks geschraubt', capsule(**PILL, grow=2.4), 2.2, bevel=0.5, x=SL_W / 2 - 0.4, parent_part='slide',
         cuts=[dict(shape='prof', pts=capsule(**PILL, grow=0.2), w=6, x=SL_W / 2)]),
    prof('pill_lens', 'Anzeigenglas', 'Counter lens', 'mechanism', 'glass', 'Schützt die Anzeige', 'im Rahmen',
         capsule(**PILL, grow=0.2), 0.6, bevel=0, x=SL_W / 2 - 1.0, parent_part='slide'),
    prof('pill_glow', 'Kapselanzeige', 'Capsule counter', 'mechanism', 'energy', 'Munitionsstand links, zum Auge (Blickfang)',
         'hinter dem Glas', capsule(**PILL, grow=-1.0), 1.0, bevel=0, x=SL_W / 2 - 1.9, parent_part='slide'),
    box('barrel_hood', 'Laufkopf', 'Barrel hood', 'barrel', 'metal', 'Verriegelt den Lauf im Verschlussblock; im Auswurffenster sichtbar',
        'am Lauf (fest)', 16, 56, RAIL + 2, 54, 14, bevel=R_SMALL),
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss', 'im Rahmen gelagert, im Laufrohr geführt',
        'f', (BORE, 0), 54, TUBE_F[1] - 3, 6.0, segs=24),
    cyl('muzzle', 'Mündungsring', 'Muzzle collar', 'barrel', 'anodized', 'Stufe vor der Schlittenstirn; zwei Gasschlitze oben (r3)',
        'auf das Laufrohr geschraubt (lösbar)', 'f', (BORE, 0), TUBE_F[1] - 10, TUBE_F[1], TUBE_R + 1.2, r_in=7.6, segs=40, bevel=R_SMALL,
        cuts=[cut_box(TUBE_F[1] - 8, TUBE_F[1] - 5, BORE + 4, BORE + 14, 5), cut_box(TUBE_F[1] - 4, TUBE_F[1] - 1, BORE + 4, BORE + 14, 5)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante in der Mündungsmulde', 'Laufende',
        'f', (BORE, 0), TUBE_F[1] - 6, TUBE_F[1] - 2, 7.5, r_in=3.6, segs=32, bevel=0.5),
    part('chevron', 'Chevronpaar', 'Chevron pair', 'mechanism', 'multi', 'accent', 'Lackiertes Chevronpaar (einziges Grafikelement)',
         'lackiert, beidseitig vorn am Schlitten', bevel=0, parent_part='slide',
         items=[dict(shape='prof', pts=[(f, 62.5), (f + 5, 62.5), (f + 11, 69), (f + 5, 75.5), (f, 75.5), (f + 6, 69)], w=0.3,
                     x=sx * (SL_W / 2 - 2 + 0.15)) for f in (118, 128) for sx in (1, -1)]),
    # A: Oberdeck rechts zwischen Verschlussblock (60) und Chevrons (118); linksbündig, läuft nach vorn bis ≈ 95 (0,62 × 3,6 × 12 Zeichen)
    part('text_r', 'Schriftzug', 'Lettering', 'mechanism', 'text', 'anodized', 'Kennung „BASIC EX-05“ (einzige Schrift)',
         'aufgedruckt (dunkel auf Creme wie BASIC-04; r3: hell auf Creme kaum lesbar)', bevel=0, text='BASIC  EX-05', size=3.6, f=68, u=65.5, x=-(SL_W / 2 - 2) - 0.05, side=-1, depth=0.12,
         parent_part='slide'),
]
# ---------------------------------------------------------------- Griff, Abzug, Bügel (BGM-1 v2.1), Magazin auf der Griffachse
P += grip_v21(top=GRIP_TOP)
_down = (round(-140 * math.sin(math.radians(15)), 1), round(-140 * math.cos(math.radians(15)), 1), 0)   # V: Entnahme wie BASIC-05
P += [
    prof('magazine', 'Magazin im Griff', 'Magazine', 'ammo', 'dark_metal', 'Hält die Patronen; steckt im Griff, entnehmbar',
         'rastet im Griff ein (lösbar, Magazinhalter)', [_A(40, -12), _A(40, 12), _A(-79, 12), _A(-79, -12)], 20, bevel=R_MID,
         move=dict(kind='translate', pivot=(*_A(-20, 0), 0), vector_mm=_down, event='reload',
                   note='Entnahme entlang der Griffachse nach unten', removable=True, expect=((*_A(-79, 0), 0), (-0.26, -0.97, 0)))),
    prof('magazine_base', 'Magazinboden', 'Magazine base plate', 'ammo', 'anodized', 'Greifkante mit Fingersporn vorn; schließt den Griff ab',
         'am Magazin (fest)', [_A(-79, -21), _A(-79, 23), _A(-82, 26), _A(-85, 23), _A(-85, -20)], 32,
         bevel=R_SMALL, parent_part='magazine'),
]
# ---------------------------------------------------------------- Visier K1 „Klammer“ (folgt dem Schlitten)
_sight, SIGHT_ANCHORS = klammer(-18, 136, DECK, parent='slide')
P += _sight
PARTS = P

ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(-4, -34, 17), part='grip', note='Stützhand umfasst die Griffhand von links (V wie BASIC-05)'),
    'Socket_Muzzle': dict(at=(TUBE_F[1] - 2, BORE, 0), part='muzzle_crown', note='Stirn der Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=(round(GRIP_TOP * T15, 1), GRIP_TOP, 0), part='grip', note='Magazinschacht im Griff'),
}
ANCHORS.update(SIGHT_ANCHORS)
# Hülsenauswurf (V wie BASIC-05): Mitte des Auswurffensters rechts im Verschlussblock, nach rechts, etwas hoch und vorn
EJECT = dict(at=(34, 60, -10), dir=(0.2, 0.5, -1.0), case='pistol',
             src='A: Auswurffenster rechts im Verschlussblock, Hülse nach rechts, etwas hoch und vorn (wie BASIC-05)')
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(-2, -34, 19), palm=(0.1, 0.0, -1.0), fingers=(0.75, -0.66, 0.0), fingers_pose='grip',
                    src='V wie BASIC-05: links an Griff und Griffhand'),
    'mag':     dict(part='magazine', contact=(round(-84 * T15, 1), -84, 17.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0),
                    fingers_pose='mag_hold', src='A: links am Magazinboden unter dem Griff (wie BASIC-05)'),
    'charge':  dict(part='slide', contact=(-13, 62, SL_W / 2 + 0.5), palm=(0.0, 0.0, -1.0), fingers=(0.2, 0.98, 0.0),
                    fingers_pose='pinch', src='A: hinten links an den Rillen des Verschlussblocks'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='slide', grip='grip', support='grip'))
ACTIONS = {
    'fire_semi': dict(de='Einzelschuss (Schlitten)', frames=10, step=1, keys={
        'trigger': [(0, 0), (2, 1), (6, 0)], 'slide': [(0, 0), (2, 0), (4, 1), (8, 0)]}, events=[(2, 'shot')]),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=60, keys={
        'mag_release': [(0, 0), (4, 1), (10, 0)], 'magazine': [(0, 0), (4, 0), (14, 1), (28, 1), (40, 0)],
        'slide': [(0, 1), (44, 1), (50, 0)]},
        events=[(14, 'mag_out'), (40, 'mag_seated'), (50, 'slide_release'), (54, 'ready')]),
}
EXPLODE = {'sight': (0, 90, 0), 'ammo': (0, -140, 0), 'barrel': (0, 0, -70), 'grip_controls': (-10, -80, 0), 'mechanism': (0, 60, 0),
           'receiver': (0, 0, 0)}
HERO = (0.78, -0.50, 0.40)   # A: Produktbild von links vorn oben – Kapselanzeige (Blickfang), Schlittenfang und Doppeldeck zur Kamera
