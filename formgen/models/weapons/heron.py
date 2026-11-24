"""Heron (BT03): statische Scout-Außenform, Gesamtbreite nach dem BA03-Blatt."""

from copy import deepcopy

from ... import ballon
from . import legacy_shared


def build(pilot=None):
    if pilot is None:
        snap = ballon.snapshot()
        pilot = ballon.load(snap, '03', ballon.resolve_base(snap, '03', 'pilot'))
    parts = [p for p in legacy_shared.build() if p['asm'] == 'grip_controls']

    def add(key, group, material, label, shape, bevel, **geometry):
        parts.append(dict(id=key, asm=group, mat=material, de=label, en=key.replace('_', ' '),
                          func=label, attach='Außenmodell Heron', shape=shape,
                          bevel=bevel, segs_bevel=3, **geometry))

    def plate(key, group, material, label, outline, width, bevel=2, x=0, **geometry):
        add(key, group, material, label, 'prof', bevel, pts=outline, w=width, x=x, **geometry)

    # BA03 misst über alle sichtbaren Teile 47 mm. Alle übrigen Außenkonturen
    # sind gestalterische Annahmen. Der vorhandene T-Griff bleibt der Modellursprung.
    plate('tail_pad', 'stock', 'graphite', 'Geneigte Heckkante',
          [(-340,129),(-324,137),(-313,131),(-323,48),(-337,39),(-349,44)], 39, 3)
    plate('tail_cowl', 'stock', 'shell', 'Lange Heckschale mit offenem Fenster',
          [(-333,124),(-308,139),(-190,139),(-153,132),(-121,115),(-137,89),
           (-209,93),(-258,87),(-315,52),(-331,53)], 40, 2.5,
          cuts=[dict(shape='prof', w=48, pts=[(-310,111),(-291,125),(-210,125),
                     (-183,119),(-199,110),(-256,105),(-312,78)])])
    plate('tail_rest', 'stock', 'rubber', 'Abgesetzte obere Auflage',
          [(-309,135),(-291,145),(-211,145),(-194,140),(-190,136),(-302,134)], 33, 1.8)
    plate('tail_stay', 'stock', 'dark_metal', 'Dunkler Fensterabschluss',
          [(-328,54),(-310,58),(-259,89),(-194,96),(-143,94),(-131,86),
           (-196,85),(-255,79),(-309,45),(-327,43)], 31, 1.7)

    plate('spine', 'receiver', 'graphite', 'Durchgehender Unterkörper',
          [(-172,113),(-147,128),(-55,132),(39,121),(137,118),(161,99),
           (144,77),(91,66),(59,44),(28,39),(-7,49),(-62,66),(-148,80)], 41, 2.5)
    plate('main_shell', 'receiver', 'shell', 'Gestufte lange Seitenwange',
          [(-165,110),(-142,135),(-57,138),(-15,138),(7,128),(94,128),
           (134,119),(122,98),(64,91),(28,78),(-17,75),(-75,91),(-145,91)], 44, 2.2)
    # Beide Auflagen gehören zur Außenhaut. Das vollständige BA03-Visier sitzt
    # als eine zusammenhängende Baugruppe im ursprünglichen Bezugssystem des Piloten.
    plate('aft_pier', 'receiver', 'dark_metal', 'Hintere Deckstufe',
          [(-80,135),(-65,140.5),(-13,140.5),(-6,137),(-17,134)], 29, .7)
    plate('fore_seat', 'receiver', 'dark_metal', 'Vordere Deckstufe',
          [(30,126),(40,130.5),(77,130.5),(85,127),(76,125)], 27, .6)
    plate('cell_fairing', 'ammo', 'graphite', 'Hintere Keramikkassette',
          [(-123,85),(-73,82),(-65,70),(-72,27),(-85,18),(-119,22),(-129,33)], 34, 2)
    plate('cell_band', 'ammo', 'anodized', 'Schräger Kassettenabschluss',
          [(-127,39),(-116,30),(-79,26),(-73,31),(-76,19),(-88,14),(-124,21),(-131,29)], 37, 1.3)

    # Eine dunkle, zurückliegende Fläche verbindet die Wange mit der Gabel.
    # Die beiden Spitzen bilden einen langen offenen Schlitz im Seitenriss.
    plate('fore_knuckle', 'support', 'graphite', 'Schmale Halsfuge',
          [(103,105),(123,125),(183,123),(229,109),(222,83),(172,69),
           (115,70),(100,78)], 39, 1.9)
    plate('fore_root', 'support', 'shell', 'Abgesetzter Gabelansatz',
          [(115,91),(138,120),(161,128),(218,125),(266,111),(278,101),
           (254,94),(206,92),(168,72),(135,70),(118,78)], 44, 2.2)
    plate('upper_beak', 'barrel', 'dark_metal', 'Oberer Gabelarm',
          [(200,103),(222,117),(297,116),(426,105),(478,101),(497,94),
           (487,88),(418,92),(299,101),(236,101)], 25, 1.5)
    plate('beak_crown', 'barrel', 'shell', 'Helle Federkante',
          [(218,118),(237,124),(305,122),(417,111),(463,105),(448,103),
           (395,108),(299,115),(231,115)], 29, 1.2)
    plate('lower_beak', 'support', 'shell', 'Aufsteigende untere Feder',
          [(137,74),(174,84),(204,78),(234,69),(297,70),(386,78),(454,91),
           (474,91),(463,83),(394,67),(306,56),(224,52),(169,58),(138,64)], 29, 1.8)
    plate('palm_sweep', 'support', 'graphite', 'Dunkle Unterkante',
          [(135,67),(171,61),(225,56),(289,59),(310,64),(300,56),(229,48),
           (183,51),(150,55)], 32, 1.4)
    plate('beak_end', 'barrel', 'graphite', 'Gestufte Spitze',
          [(458,96),(475,104),(504,100),(514,94),(507,88),(479,86),(459,90)], 24, 1.2)
    plate('beak_tile', 'barrel', 'anodized', 'Facettierte Stirn',
          [(503,99),(513,98),(519,94),(514,90),(504,89)], 20, .8)
    plate('tip_glyph', 'barrel', 'energy', 'Stirnmarke',
          [(515,95),(519,95),(520,94),(518,93),(515,93)], 10, .25)

    for side, suffix in ((1, 'l'), (-1, 'r')):
        def inlay(key, group, role, label, outline, inner, outer, bevel=.6):
            plate(key+'_'+suffix, group, role, label, outline, outer-inner, bevel, x=side*(inner+outer)/2)
        # Die äußersten erhabenen Felder setzen symmetrisch das am BA03 gemessene Gesamtmaß.
        inlay('maker_plate','receiver','anodized','Typenschild',
              [(-142,106),(-129,122),(-76,124),(-65,118),(-80,104),(-130,102)],21.7,22.95)
        add('name_'+suffix,'receiver','shell','Modellschriftzug','text',0,text='HERON',f=-103,u=109,
            x=side*23.05,side=side,depth=.18,size=7,align='CENTER')
        inlay('fore_chevron','support','anodized','Keil am Gabelansatz',
              [(144,90),(166,114),(214,117),(226,111),(176,108),(154,87)],21.7,23.5)
        inlay('beak_inset','barrel','graphite','Facettenstreifen',
              [(279,106),(294,112),(373,106),(381,103),(306,108)],12.2,13.3,.35)
        for index,f in enumerate((-60,-50)):
            inlay(f'bridge_band_{index}','receiver','accent','Schultermarkierung',
                  [(f,116),(f+3,116),(f+10,128),(f+7,128)],21.75,22.45,.25)

    # Einmal aus dem gepinnten BA03 übernehmen. Die Ursprungskorrektur der
    # Pipeline gilt gemeinsam für Körper, Visierteile und Unity-Knoten.
    parts.extend(deepcopy(part) for part in pilot['PARTS'] if part['asm']=='sight')
    refs = {'Socket_Hand':('handle',[-20,23,0]), 'Socket_SupportHand':('palm_sweep',[178,56,0]),
            'Socket_Muzzle':('beak_tile',[518,94,0])}
    points = {'grip.grip':refs['Socket_Hand'], 'grip.support':refs['Socket_SupportHand'],
              'grip.mag':('cell_fairing',[-91,48,0]),'grip.charge':('main_shell',[-44,102,22]),
              'eject':('spine',[68,82,-20])}
    anchors = {k:dict(part=p,at=list(at),source='Annahme: Bezugspunkt des Spielmodells') for k,(p,at) in refs.items()}
    for name in ('Socket_Eye','Socket_Sight','Socket_Reticle','Socket_Objective'):
        anchor = pilot['ANCHORS'][name]
        anchors[name] = dict(anchor,at=list(anchor['at']),source='BALLON: Originalvisier BASIC-03')
    return parts, anchors, {k:dict(part=p,at=list(at)) for k,(p,at) in points.items()}
