"""Cairn (BT04), statische Außenform. Schichtkonturen und Relief sind Formannahmen."""

from copy import deepcopy

from ... import ballon
from .sidearm_shell import Shell


def build(pilot=None):
    if pilot is None:
        snap = ballon.snapshot()
        pilot = ballon.load(snap, '04', ballon.resolve_base(snap, '04', 'pilot'))
    s = Shell('Cairn')
    # Der Modellursprung und die offenen Visierteile folgen dem BA04-Spielpiloten.
    s.plate('grip_cast', 'grip_controls', 'graphite', 'Schräger Griffkörper',
            [(-14,49),(20,48),(37,34),(26,18),(7,-37),(9,-48),(-1,-57),
             (-34,-53),(-41,-44),(-30,-17),(-17,19),(-25,36)], 31, 3)
    s.inlay('grip_panel', 'grip_controls', 'rubber', 'Eingelassene Griffwange',
            [(-11,30),(12,35),(16,25),(2,-15),(-4,-41),(-23,-44),
             (-30,-36),(-22,-13)], 15.1, 17.3, 1.2)
    s.plate('heel', 'grip_controls', 'dark_metal', 'Abgesetzte Griffsohle',
            [(-39,-39),(-28,-47),(-2,-47),(7,-42),(12,-50),(1,-59),
             (-33,-56),(-43,-49)], 35.8, 1.8)
    s.plate('bow', 'grip_controls', 'graphite', 'Offene Griffspange',
            [(20,4),(41,4),(54,12),(66,36),(75,40),(64,12),(49,-4),
             (39,-6),(17,-3)], 14, 1.4)
    s.plate('pendant', 'grip_controls', 'dark_metal', 'Dunkle Innenzunge',
            [(34,40),(43,39),(38,23),(43,17),(37,18),(32,25)], 9, .8)
    s.plate('core', 'receiver', 'graphite', 'Dunkle Mittelfuge',
            [(-34,65),(-25,83),(5,89),(80,87),(114,83),(193,83),(241,87),
             (263,77),(266,58),(253,38),(231,32),(142,32),(106,22),(71,24),
             (48,36),(24,34),(-6,40),(-26,49)], 35.8, 2.4)
    s.plate('rear_stone', 'receiver', 'shell', 'Hohe hintere Keramikschulter',
            [(-35,67),(-27,83),(-16,91),(20,92),(52,89),(68,79),
             (54,67),(22,66),(2,52),(-18,53)], 39, 2)
    s.plate('aft_seat', 'receiver', 'dark_metal', 'Dunkle Deckkante',
            [(-12,89),(-5,92.1),(20,92.1),(28,89),(17,87),(-8,87)], 26, .6)
    s.plate('fore_stone', 'barrel', 'shell', 'Lange obere Keramiklage',
            [(82,79),(102,89),(146,89),(162,85),(207,85),(228,91),
             (255,91),(264,82),(260,69),(235,62),(182,63),(158,68),
             (119,68),(99,62),(80,65)], 40.4, 1.9)
    s.plate('fore_seat', 'barrel', 'dark_metal', 'Abgesetzte vordere Deckkante',
            [(234,89),(240,92.1),(257,92.1),(260,89),(254,87),(238,87)], 22, .5)
    s.plate('keel', 'barrel', 'shell', 'Kurze untere Keramiklage',
            [(103,44),(128,54),(153,54),(169,49),(218,50),(246,55),
             (253,52),(242,39),(218,32),(169,32),(144,36),(117,30),(101,32)], 36.4, 1.6)
    s.facet('nose_tile', 'barrel', 'graphite', 'Geschlossene Stirnkachel',
            255, 268, 68, 31, 33, 7, 1.5)
    s.facet('nose_glaze', 'barrel', 'anodized', 'Stirneinlage',
            266, 269, 68, 24, 25, 6, .7)
    # Das Plakettenrelief bestimmt die Gesamtbreite: BA04 im GLB, gerundet 44,83 mm.
    half_width = 44.83 / 2
    for side, end in ((1, 'l'), (-1, 'r')):
        for key, role, radius, inner, outer in (
                ('medallion', 'dark_metal', 25, 16.8, 20.5),
                ('coin', 'anodized', 21, 20.1, half_width)):
            a, b = sorted((side * inner, side * outer))
            s.add(key+'_'+end, 'receiver', role, 'Facettiertes Seitenmedaillon',
                  'cyl', .75, axis='x', c=(72,62), a0=a, a1=b, r=radius, segs=12)
    s.inlay('slate_band', 'barrel', 'accent', 'Einzelne schräge Farbmarke',
            [(170,70),(177,70),(191,81),(185,81)], 19.9, 20.65)
    s.inlay('name_plate', 'barrel', 'graphite', 'Dunkles Schriftfeld',
            [(111,73),(120,82),(155,82),(160,77),(153,72),(118,72)], 19.9, 20.7)
    s.word('barrel', 'shell', 136, 74.8, 20.86, 4.7)
    s.inlay('heel_inset', 'grip_controls', 'anodized', 'Flacher Griffindex',
            [(-21,-34),(-6,-29),(-8,-33),(-22,-38)], 16.9, 17.65, .35)

    s.parts.extend(deepcopy(p) for p in pilot['PARTS'] if p['asm'] == 'sight')
    refs = {'Socket_Hand': ('grip_cast', [0,0,0]), 'Socket_SupportHand': ('grip_panel_l', [-4,-34,17]),
            'Socket_Muzzle': ('nose_glaze', [269,68,0])}
    points = {'grip.grip': refs['Socket_Hand'], 'grip.support': refs['Socket_SupportHand'],
              'grip.mag': ('medallion_l', [72,62,18]), 'grip.charge': ('rear_stone', [-15,71,18]),
              'eject': ('core', [39,59,-17])}
    parts, anchors, points = s.finish(refs, points)
    for key in ('Socket_Eye', 'Socket_Sight', 'Socket_Reticle'):
        anchors[key] = deepcopy(pilot['ANCHORS'][key])
        anchors[key]['at'] = list(anchors[key]['at'])
    return parts, anchors, points
