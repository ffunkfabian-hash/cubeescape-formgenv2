"""BT02 Vesper. Konturen, Fasen und Farbverteilung sind freie Formannahmen für ein statisches Spielasset."""

from ... import ballon
from . import legacy_shared


def build(snap=None):
    # Das Glas sitzt mittig auf der bisherigen BT02-Spielvisierlinie.
    family = legacy_shared.build(optic_base=146)
    # Griff und Sichtfenster sind sichtbare Gleichteile der Trestle-Linie.
    parts = [p for p in family if p['asm'] == 'grip_controls' or p['id'].startswith('optic_')]

    def add(key, group, material, name, shape, bevel, **geom):
        parts.append(dict(id=key, asm=group, mat=material, de=name, en=key.replace('_', ' '),
                          func=name, attach='Außenmodell Vesper', shape=shape, bevel=bevel,
                          segs_bevel=3, **geom))

    def plate(key, group, material, name, points, width, bevel=2, x=0, **geom):
        add(key, group, material, name, 'prof', bevel, pts=points, w=width, x=x, **geom)

    def cap(key, material, name, start, end, height, width, corner, bevel):
        a, b = width/2, height/2
        ring = [(-a+corner,-b), (a-corner,-b), (a,-b+corner), (a,b-corner),
                (a-corner,b), (-a+corner,b), (-a,b-corner), (-a,-b+corner)]
        add(key, 'barrel', material, name, 'xprof', bevel, f0=start, f1=end, cu=76, pts=ring)

    # BA02 ist die Maß- und Stilreferenz. Die drei hellen Segmente sind
    # einzelne Körper, ihre Fugen gehen über beide Flanken und den Rücken.
    # Alle weiteren Maße sind gestalterische Annahmen für das Spielmodell.
    plate('aft_pad', 'stock', 'graphite', 'Heckabschluss',
          [(-316,127),(-300,135),(-291,126),(-293,33),(-303,25),(-316,30)], 41, 3)
    plate('aft_shell', 'stock', 'graphite', 'Offener Winkelrahmen',
          [(-300,129),(-285,139),(-155,139),(-126,126),(-128,79),(-144,70),
           (-198,69),(-289,34),(-303,36)], 38, 3, cuts=[dict(shape='prof',w=48,
           pts=[(-279,115),(-263,124),(-174,124),(-160,114),(-160,91),
                (-198,87),(-279,57)])])
    plate('aft_spine', 'stock', 'dark_metal', 'Untere Rahmenkante',
          [(-297,45),(-278,50),(-196,80),(-145,80),(-136,73),(-194,69),
           (-284,36),(-297,35)], 34, 1.7)
    plate('aft_rest', 'stock', 'shell', 'Auflage auf dem Rahmen',
          [(-278,134),(-263,144),(-197,144),(-187,140),(-190,136),(-268,136)], 30, 1.2)
    plate('body_spine','receiver','graphite','Dunkler Gehäusesockel',
          [(-143,118),(-119,132),(95,131),(111,113),(104,58),(94,43),(37,40),
           (18,55),(-11,55),(-45,67),(-95,71),(-139,88)], 43, 3)
    plate('aft_cowl','receiver','shell','Gerade obere Gehäuseschale',
          [(-144,126),(-130,140),(82,140),(103,129),(98,91),(83,85),
           (-100,85),(-139,94)], 48, 2.2)
    plate('bridge_shadow','receiver','dark_metal','Flache Rückenfuge',
          [(-123,137),(-109,144),(68,144),(84,139),(68,136),(-120,136)], 35, 1.2)
    plate('bridge_fold','receiver','graphite','Oberes Deck',
          [(-97,142),(-82,145),(33,145),(47,144),(73,143),(77,141)], 34, 1)
    plate('bridge_seat','receiver','anodized','Hintere Deckstufe',
          [(-123,141),(-111,146),(-91,146),(-94,142),(-104,140)], 32, .6)
    for i, f in enumerate((-112,-101)):
        plate(f'bridge_mark_{i}','receiver','accent','Seitliche Impulsmarke',
              [(f,120),(f+4,120),(f+10,129),(f+6,129)], 48.6, .3)
    plate('crest','sight','graphite','Flache Visierauflage',
          [(-52,144),(-43,146),(16,146),(30,144),(17,143),(-44,143)], 31, 1)

    # Die dunkle durchgehende Mitte ist in den Fugen sichtbar. Drei getrennte
    # Deckschalen werfen jeweils ein eigenes Profil in Seite und Draufsicht.
    plate('well_floor','support','graphite','Durchgehender Kern der Impulsreihe',
          [(89,101),(103,116),(296,116),(318,105),(333,91),(328,72),
           (302,61),(128,56),(98,66)], 34, 2.2)
    for i, key in enumerate(('pulse_mantle','pulse_middle','pulse_front')):
        f = 100 + 74 * i
        crown = 139 - 3*i
        plate(key,'support','shell','Impulssegment '+str(i+1),
              [(f,119),(f+10,crown),(f+54,crown),(f+62,crown-8),(f+59,83),
               (f+49,74),(f+4,74),(f-3,82)], 48, 2,
              cuts=[dict(shape='prof',w=56,pts=[(f+9,96),(f+17,118),
                   (f+45,118),(f+49,112),(f+42,94),(f+14,94)])])
    plate('chin','support','graphite','Flache Unterkante der Impulsreihe',
          [(98,74),(132,68),(288,68),(315,75),(334,84),(329,66),(295,51),
           (201,45),(177,35),(159,34),(133,44),(102,46)], 35, 2)
    plate('cell','ammo','graphite','Abgesetzte kantige Kassette',
          [(53,55),(96,52),(105,39),(110,-21),(103,-34),(65,-34),
           (59,-19),(56,20)], 37, 2.4)
    plate('cell_heel','ammo','dark_metal','Kassettenunterkante',
          [(62,-26),(107,-26),(112,-21),(112,-34),(105,-39),(63,-38),(60,-34)], 41, 1.5)

    cap('front_gasket','dark_metal','Hals hinter der Stirn',295,343,41,40,7,1.4)
    cap('front_mask','graphite','Gestufter Vorbau',339,366,32,34,6,1.5)
    cap('front_glaze','anodized','Keramische Endkappe',362,381,27,27,5,1)
    for idx, level in enumerate((71,81)):
        add(f'front_trace_{idx}','barrel','energy','Lichtsignatur','xprof',.5,f0=380.6,f1=381.8,
            cu=level,pts=[(-13,-1.4),(7,-1.4),(12,1.4),(-8,1.4)])
    for side,suffix in ((1,'l'),(-1,'r')):
        def relief(key,group,role,name,pts,inside,outside,bevel):
            plate(key+'_'+suffix,group,role,name,pts,outside-inside,bevel,x=side*(inside+outside)/2)
        for i in range(3):
            f = 100 + 74 * i
            relief(f'porcelain_{i}','support','anodized','Keramikinlay',
                   [(f+14,98),(f+21,114),(f+41,114),(f+44,110),(f+38,97)],16.7,21,1)
            # Ein Leuchtstrich je Segment sitzt innerhalb der eigenen Öffnung.
            relief(f'pulse_line_{i}','support','energy','Lichtmarke',
                   [(f+20,100),(f+23,106),(f+38,106),(f+35,100)],20.7,21.6,.45)
        relief('cell_panel','ammo','shell','Kassettenwange',
               [(62,26),(99,26),(103,-18),(96,-25),(66,-24)],18.1,20,1)
        relief('aft_badge','receiver','anodized','Eloxiertes Schriftfeld',
               [(-126,103),(-114,118),(-69,121),(-54,115),(-63,103),(-110,101)],23.6,24.9,1)
        add('word_'+suffix,'receiver','graphite','Schriftzug','text',0,text='VESPER',f=-90,u=107,
            x=side*25.1,side=side,depth=.3,size=7.3,align='CENTER')
        relief('serial','support','dark_metal','Serienfeld',
               [(112,125),(116,132),(148,132),(145,125)],23.7,25.5,.5)
        for i in range(3):
            f=32+i*7
            relief(f'index_{i}','receiver','metal','Indexsegment',
                   [(f,64),(f+4,64),(f+7,70),(f+3,70)],21.2,22.2,.3)

    # Das Absehen ist das gezeichnete Spiel-HUD von BA02 im Vesper-Fenster.
    # Alle drei Anker folgen dem tatsächlichen Glas beziehungsweise Rahmen.
    glass = next(p for p in parts if p['id'] == 'optic_pane')
    frame = next(p for p in parts if p['id'] == 'optic_hood')
    glass_face, level = glass['f0'], glass['cu']
    # BA02 setzt den Zielanker etwas hinter die sichtbare HUD-Ebene im Glas.
    reticle_f = glass_face + 0.4
    with ballon.snapshot_imports(snap or ballon.snapshot()):
        from basic.common import drawn_reticle
        from basic.reticles import SIGHT
        relief_mm = SIGHT['types']['reflex']['eye_relief_mm']
        eye_f = reticle_f - relief_mm
        parts.append(drawn_reticle(glass_face, level, 'pulse_rifle', glass_face-eye_f, parent='optic_pane'))

    anchors = dict(Socket_Hand=('handle',[-20,23,0]), Socket_SupportHand=('chin',[165,35,0]),
                   Socket_Muzzle=('front_trace_1',[381.8,81,0]),
                   Socket_Sight=('optic_hood',[frame['f0'],level,0]),
                   Socket_Reticle=('optic_pane',[reticle_f,level,0]),
                   Socket_Eye=('optic_hood',[eye_f,level,0]))
    points = {'grip.grip':anchors['Socket_Hand'], 'grip.support':anchors['Socket_SupportHand'],
              'grip.mag':('cell',[86,17,0]),'grip.charge':('aft_cowl',[-30,101,24]),
              'eject':('body_spine',[39,65,-21])}
    sockets = {name:dict(part=part,at=list(at),source='Annahme: Bezugspunkt des Spielmodells')
               for name,(part,at) in anchors.items()}
    sockets['Socket_Eye'].update(std=True, sight_type='reflex', source='BALLON: Reflexvisier-Spielstandard')
    return parts, sockets, {name:dict(part=part,at=list(at)) for name,(part,at) in points.items()}
