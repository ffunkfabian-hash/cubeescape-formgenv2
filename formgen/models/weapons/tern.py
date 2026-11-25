"""Tern (BT06), statische Sci-Fi-Außenform. Konturen und Fasen sind Formannahmen."""

from ... import ballon
from .sidearm_shell import Shell


def build(pilot=None):
    if pilot is None:
        snap = ballon.snapshot()
        pilot = ballon.load(snap, '06', ballon.resolve_base(snap, '06', 'pilot'))
    s = Shell('Tern')
    # Zwei schmale Heckstreben treffen sich in einem geschlossenen Keramikabschluss.
    s.plate('tail', 'stock', 'graphite', 'Flacher Heckrahmen',
            [(-163,89),(-137,103),(-97,106),(-62,99),(-51,85),(-64,54),
             (-104,41),(-147,27),(-165,34)], 27, 2.1,
            cuts=[dict(shape='prof', w=34, pts=[(-146,80),(-130,89),(-96,90),
                       (-78,84),(-83,65),(-105,54),(-144,42)])])
    s.plate('tail_cap', 'stock', 'shell', 'Helle hintere Federkante',
            [(-168,83),(-154,101),(-126,110),(-94,110),(-75,104),(-103,100),
             (-134,99),(-155,88),(-159,54),(-167,44)], 31, 1.7)
    s.plate('grip', 'grip_controls', 'graphite', 'Geschwungener Griffkörper',
            [(-24,55),(14,57),(34,43),(26,20),(4,-40),(-8,-60),(-42,-61),
             (-54,-52),(-38,-20),(-20,20),(-30,37)], 33, 2.5)
    s.inlay('grip_leaf', 'grip_controls', 'rubber', 'Blattförmige Griffwange',
            [(-15,36),(8,41),(18,29),(8,5),(-13,-43),(-33,-48),(-39,-41),
             (-25,-12),(-9,20)], 16.2, 18.1, 1)
    s.plate('heel', 'ammo', 'anodized', 'Dunkle Fersenkappe',
            [(-52,-45),(-39,-52),(-10,-52),(2,-42),(-4,-58),(-16,-67),
             (-46,-66),(-57,-58)], 36, 1.4)
    s.plate('bow', 'grip_controls', 'dark_metal', 'Bogen vor dem Griff',
            [(16,14),(55,13),(67,23),(77,49),(86,49),(79,21),(62,6),
             (43,5),(14,8)], 15, 1.2)
    s.plate('inner_tab', 'grip_controls', 'graphite', 'Dunkle Innenzunge',
            [(33,47),(44,48),(42,31),(48,25),(41,24),(33,32)], 9, .85)
    s.plate('body', 'receiver', 'graphite', 'Durchgehender dunkler Kern',
            [(-77,91),(-52,109),(-12,115),(43,117),(76,109),(123,101),
             (207,100),(272,95),(296,83),(289,63),(257,55),(197,53),(139,58),
             (109,48),(68,42),(31,40),(5,54),(-42,57),(-69,68)], 39.8, 2.6)
    s.plate('mantle', 'receiver', 'shell', 'Lange hintere Deckschale',
            [(-89,84),(-71,105),(-40,118),(-5,120),(36,120),(58,115),
             (82,104),(128,99),(161,91),(136,88),(81,94),(48,104),(19,100),
             (-12,89),(-56,86),(-77,76)], 43.6, 1.9)
    s.plate('deck', 'receiver', 'dark_metal', 'Dunkles Visierpodest',
            [(-17,118),(-11,122),(37,122),(45,119),(39,117),(-11,117)], 28, .7)
    s.plate('chin', 'support', 'shell', 'Ansteigende untere Spange',
            [(91,56),(111,66),(158,68),(202,61),(250,62),(271,68),(282,66),
             (267,52),(242,45),(196,44),(158,50),(118,50),(101,44),(88,47)], 35, 1.8)
    s.plate('palm', 'support', 'graphite', 'Kurze dunkle Handauflage',
            [(173,52),(191,54),(219,48),(241,47),(251,50),(244,29),(230,20),
             (208,21),(191,31),(165,37)], 32, 2)
    s.plate('prow', 'barrel', 'shell', 'Vorgesetzte helle Bugschale',
            [(149,87),(174,98),(194,102),(294,102),(308,99),(318,94),
             (318,74),(309,68),(278,68),(262,73),(211,73),(191,80),
             (175,84),(159,83)], 40.8, 1.9)
    s.facet('front_tile', 'barrel', 'dark_metal', 'Geschlossene dunkle Stirn',
            309, 321, 82, 30, 27, 6, 1.2)
    s.facet('front_mark', 'barrel', 'anodized', 'Stirnfacette',
            319, 322, 82, 23, 20, 4, .7)
    # Die erhabenen Schulterfelder setzen das am BA06-GLB gemessene Außenmaß.
    s.inlay('shoulder', 'receiver', 'anodized', 'Facettierter Schultereinsatz',
            [(-65,95),(-50,109),(-16,114),(12,113),(2,106),(-34,100),(-54,93)],
            21.5, 23.5, .8)
    s.inlay('type_plate', 'receiver', 'graphite', 'Dunkles Typenschild',
            [(9,105),(22,114),(39,114),(50,110),(41,105),(18,102)], 21.5, 22.3, .45)
    s.word('receiver', 'shell', 30, 106.7, 22.4, 4.6)
    for i, forward in enumerate((209, 220)):
        s.inlay(f'wing_mark_{i}', 'barrel', 'accent', 'Schräger Flügelstrich',
                [(forward,94),(forward+5,94),(forward+12,101),(forward+7,101)],20,21.1,.35)
    s.inlay('edge_light', 'support', 'energy', 'Lichtfuge am Unterbogen',
            [(123,56),(135,59),(157,59),(150,56)], 17.2, 18.15, .35)

    refs = {'Socket_Hand': ('grip', [0,0,0]), 'Socket_SupportHand': ('palm', [230,24,0]),
            'Socket_Muzzle': ('front_mark', [322,82,0]), 'Socket_MagWell': ('heel', [-31,-64,0]),
            'Socket_Charge': ('shoulder_l', [-45,104,23.5])}
    points = {'grip.grip': refs['Socket_Hand'], 'grip.support': refs['Socket_SupportHand'],
              'grip.mag': refs['Socket_MagWell'], 'grip.charge': refs['Socket_Charge'],
              'eject': ('body', [43,82,-19])}
    return s.finish_with_pilot_sight(refs, points, pilot)
