"""Swift (BT05), statisches Spielmodell. Außenkonturen und Fasen sind Formannahmen."""

from ... import ballon
from .sidearm_shell import Shell


def build(pilot=None):
    if pilot is None:
        snap = ballon.snapshot()
        pilot = ballon.load(snap, '05', ballon.resolve_base(snap, '05', 'pilot'))
    s = Shell('Swift')
    # Die beiden Griffwangen setzen die am BA05-GLB gemessene Gesamtbreite.
    # Die Aussparung wird durch Kern und beide Flächen gemeinsam geschnitten.
    window = [(-37,-42),(-26,-28),(-18,-25),(-19,-36),(-28,-44),(-36,-45)]
    cut = dict(shape='prof', pts=window, w=40)
    s.plate('grip_arch', 'grip_controls', 'graphite', 'Gefalteter Griffkern',
            [(-19,54),(13,51),(27,37),(19,12),(3,-19),(-6,-48),(-20,-61),
             (-44,-60),(-55,-51),(-47,-34),(-32,-9),(-18,24),(-25,36)], 27, 2.2, cuts=[cut])
    s.plate('grip_cheek', 'grip_controls', 'shell', 'Heller Saum um die offene Ferse',
            [(-17,39),(2,43),(9,34),(-2,8),(-17,-19),(-10,-26),(-13,-44),(-23,-54),
             (-43,-54),(-48,-48),(-40,-30),(-25,-7),(-15,15),(-21,29)], 30, 1.5, cuts=[cut])
    s.inlay('palm_wing', 'grip_controls', 'rubber', 'Dunkle federförmige Griffwange',
            [(-13,27),(2,32),(6,24),(-2,4),(-15,-18),(-28,-27),(-22,-10),(-12,11)],
            14.7, 16.75, .85)
    s.plate('heel_tip', 'ammo', 'anodized', 'Abgesetzte Fersenspitze',
            [(-54,-49),(-43,-55),(-21,-55),(-10,-46),(-12,-54),(-22,-62),
             (-44,-62),(-55,-56)], 29, 1)
    s.plate('bow', 'grip_controls', 'dark_metal', 'Schmaler Griffbogen',
            [(17,13),(37,11),(48,18),(55,40),(62,43),(57,20),(47,8),(36,5),(15,7)], 11, 1.1)
    s.plate('inner_mark', 'grip_controls', 'graphite', 'Innenmarke',
            [(30,44),(36,42),(34,29),(38,24),(33,24),(28,31)], 8, .8)

    s.plate('keel', 'receiver', 'graphite', 'Dunkler Rumpf mit ansteigender Unterkante',
            [(-39,66),(-30,83),(-4,87),(52,86),(82,79),(146,82),(185,88),(197,81),
             (197,67),(184,62),(138,59),(113,52),(65,47),(46,35),(21,34),
             (8,42),(-10,46),(-31,48)], 27.8, 1.9)
    # Die sechs BA05-Visierteile referenzieren die obere Schale als 'slide'.
    s.plate('slide', 'receiver', 'shell', 'Helle Schulter mit rückwärts gezogenem Zipfel',
            [(-40,69),(-33,85),(-19,92),(8,92),(27,88),(58,86),(86,79),(119,77),
             (101,72),(64,72),(39,77),(16,76),(-6,64),(-31,56),(-24,65)], 31.2, 1.6)
    s.plate('quill', 'barrel', 'shell', 'Lange helle Feder an der Front',
            [(58,61),(76,68),(111,71),(133,77),(157,85),(177,92),(192,92),
             (198,85),(189,81),(162,79),(140,70),(105,64),(78,63),(66,57)], 28.8, 1.3)
    s.plate('ventral', 'barrel', 'anodized', 'Schmale dunkle Gegenkante',
            [(62,51),(85,58),(111,60),(149,66),(183,66),(191,70),(190,63),
             (168,57),(133,55),(106,49),(75,46)], 22, 1.2)
    s.facet('tip_tile', 'barrel', 'dark_metal', 'Geschlossene Stirnkachel',
            188, 199, 77, 24, 23, 4, 1)
    s.facet('tip_inset', 'barrel', 'anodized', 'Kleine Stirnfacette',
            198, 200, 77, 17, 16, 3, .55)
    s.plate('aft_seat', 'receiver', 'dark_metal', 'Dunkle hintere Deckkante',
            [(-22,89),(-17,92.2),(7,92.2),(13,89),(4,88),(-19,88)], 24.5, .52)
    s.plate('fore_seat', 'barrel', 'graphite', 'Dunkle vordere Deckkante',
            [(172,89),(176,92.2),(192,92.2),(196,90),(191,88),(176,88)], 17, .45)
    s.inlay('name_tile', 'receiver', 'graphite', 'Schriftfeld an der Schulter',
            [(-19,78),(-8,86),(23,85),(30,81),(17,78),(-9,75)], 15.3, 16.1, .45)
    s.word('receiver', 'shell', 5, 79.3, 16.15, 4)
    s.inlay('swift_mark', 'receiver', 'accent', 'Doppelfeder am Heck',
            [(31,81),(37,85),(46,84),(39,80)], 15.3, 16.05, .25)
    s.inlay('quill_glint', 'barrel', 'energy', 'Kurzer Lichtstrich in der Feder',
            [(132,73),(150,80),(160,82),(154,79),(137,73)], 14.2, 14.85, .23)

    refs = {'Socket_Hand': ('grip_arch', [0,0,0]), 'Socket_SupportHand': ('palm_wing_l', [-13,-12,16.75]),
            'Socket_MagWell': ('heel_tip', [-31,-60,0]), 'Socket_Muzzle': ('tip_inset', [200, pilot['ANCHORS']['Socket_Muzzle']['at'][1], 0])}
    points = {'grip.grip': refs['Socket_Hand'], 'grip.support': refs['Socket_SupportHand'],
              'grip.mag': refs['Socket_MagWell'], 'grip.charge': ('slide', [-18,79,15]),
              'eject': ('keel', [48,64,-13])}
    return s.finish_with_open_sight(refs, points, pilot)
