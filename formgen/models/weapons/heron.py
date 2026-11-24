"""BT03 Heron. Alle Konturen und Maße sind gestalterische Annahmen für ein statisches Spielasset."""

from . import legacy_shared


def build():
    family = legacy_shared.build()
    parts = [p for p in family if p['asm'] == 'grip_controls']

    def add(key, group, material, label, shape, bevel, **geometry):
        parts.append(dict(id=key, asm=group, mat=material, de=label, en=key.replace('_', ' '),
                          func=label, attach='Außenmodell Heron', shape=shape,
                          bevel=bevel, segs_bevel=3, **geometry))

    def plate(key, group, material, label, outline, width, bevel=2, x=0, **geometry):
        add(key, group, material, label, 'prof', bevel, pts=outline, w=width, x=x, **geometry)

    def facet(key, group, material, label, start, end, level, width, height, cut, bevel=1):
        a, b = width / 2, height / 2
        rim = [(-a+cut,-b), (a-cut,-b), (a,-b+cut), (a,b-cut),
               (a-cut,b), (-a+cut,b), (-a,b-cut), (-a,-b+cut)]
        add(key, group, material, label, 'xprof', bevel, f0=start, f1=end, cu=level, pts=rim)

    # Hohes Heck mit flacher Decklinie und weit gespannter unterer Diagonale.
    plate('tail_pad', 'stock', 'graphite', 'Abgesetzter Schaftrücken',
          [(-306,121),(-293,133),(-282,130),(-279,61),(-291,42),(-306,44),(-311,54)], 42, 3.5)
    plate('tail_cowl', 'stock', 'shell', 'Obere Schaftschale',
          [(-296,123),(-278,136),(-213,140),(-169,134),(-134,119),(-145,106),
           (-221,111),(-253,104),(-281,78),(-295,65)], 41, 2.7)
    plate('tail_rest', 'stock', 'rubber', 'Wangenauflage',
          [(-286,131),(-272,141),(-210,145),(-184,141),(-175,135),(-215,138),(-275,134)], 35, 2)
    plate('tail_stay', 'stock', 'dark_metal', 'Rücklaufende Schaftstrebe',
          [(-297,52),(-288,43),(-263,47),(-153,78),(-117,92),(-124,98),(-159,93),(-266,63)], 24, 2)
    plate('spine', 'receiver', 'graphite', 'Durchlaufender Kiel',
          [(-156,113),(-145,125),(-113,122),(-65,117),(62,113),(129,105),(195,100),
           (209,88),(193,75),(113,70),(74,57),(51,43),(13,38),(-10,48),(-77,62),(-144,84)], 42, 2.8)
    plate('main_shell', 'receiver', 'shell', 'Geschweifte Hauptschale',
          [(-142,104),(-123,126),(-85,133),(-38,131),(15,122),(69,120),(100,109),
           (88,92),(36,90),(-8,77),(-58,78),(-91,90),(-135,93)], 49, 2.6)
    plate('cell_fairing', 'ammo', 'graphite', 'Hintere Formkassette',
          [(-114,86),(-71,82),(-63,63),(-72,35),(-81,24),(-112,28),(-121,36)], 36, 2.5)
    plate('cell_band', 'ammo', 'dark_metal', 'Sockelabschluss',
          [(-121,40),(-112,32),(-78,29),(-81,22),(-113,24),(-123,31)], 39, 1.4)

    # Die vordere Öffnung folgt zwei unterschiedlich langen, gegenläufigen Außenkonturen.
    plate('fore_knuckle', 'support', 'dark_metal', 'Schatten am Schalenanfang',
          [(89,98),(110,115),(148,115),(182,106),(182,77),(154,68),(108,73),(92,81)], 45, 2)
    plate('fore_root', 'support', 'shell', 'Abgesetzte Vorderwange',
          [(104,92),(120,114),(148,121),(186,117),(223,110),(232,101),(218,93),
           (179,91),(156,82),(139,68),(122,70),(108,78)], 52, 2.4)
    plate('upper_beak', 'barrel', 'dark_metal', 'Facettierter oberer Schnabel',
          [(165,105),(184,114),(261,110),(360,106),(429,99),(443,94),
           (435,87),(354,91),(258,95),(192,96)], 26, 1.7)
    plate('beak_crown', 'barrel', 'shell', 'Lange schmale Deckschale',
          [(201,109),(217,116),(277,115),(370,109),(420,103),(429,99),
           (390,100),(280,108),(215,110)], 31, 1.4)
    plate('lower_beak', 'support', 'shell', 'Ansteigende untere Spange',
          [(128,75),(155,85),(176,82),(208,72),(248,73),(324,81),(381,89),
           (402,96),(426,96),(433,91),(410,83),(343,73),(249,60),(199,56),(157,59),(135,64)], 32, 2.2)
    plate('palm_sweep', 'support', 'graphite', 'Unterkante der Spange',
          [(132,65),(159,61),(199,58),(247,62),(299,69),(292,64),
           (218,52),(176,50),(142,55)], 33, 1.5)
    facet('beak_end', 'barrel', 'graphite', 'Geschlossene Schnabelspitze', 421, 448, 94, 32, 23, 5, 1.5)
    facet('beak_tile', 'barrel', 'anodized', 'Keramische Stirn', 446, 451, 94, 25, 18, 4)
    facet('tip_glyph', 'barrel', 'energy', 'Heller Stirnindex', 450.7, 451.5, 94, 12, 2.8, 1, .3)

    # Der lange Sensorkörper bildet selbst den horizontalen Abschluss des Brückenfensters.
    plate('aft_pier', 'sight', 'shell', 'Hinterer Brückenanstieg',
          [(-125,124),(-93,151),(-75,158),(-55,158),(-57,148),(-78,145),(-102,127)], 34, 1.5)
    plate('fore_pier', 'sight', 'shell', 'Vorderes Brückenbein',
          [(9,152),(34,154),(68,127),(72,120),(59,119),(44,131)], 32, 1.5)
    plate('fore_seat', 'sight', 'graphite', 'Brückenschuh',
          [(54,120),(62,123),(73,123),(82,119),(79,116),(57,117)], 38, 1)
    plate('sensor_body', 'sight', 'anodized', 'Flacher Sensorkörper',
          [(-121,151),(-114,165),(-90,170),(39,167),(69,175),(90,173),(97,164),
           (90,151),(60,147),(36,150),(-89,153),(-108,147)], 34, 2)
    plate('sensor_crest', 'sight', 'shell', 'Gebrochene Sensorhaube',
          [(-104,166),(-90,173),(-48,175),(32,171),(54,172),(41,166),(-84,167)], 36, 1.4)
    facet('sensor_heel', 'sight', 'graphite', 'Hinterer Sensorabschluss', -123,-111,158, 38,22,5)
    facet('rear_glass', 'sight', 'glass', 'Rückseitiges Glasfeld', -124,-122.6,158, 29,15,3,.4)
    facet('sensor_nose', 'sight', 'graphite', 'Vordere Sensorfassung', 85,100,162, 40,29,6,1.3)
    facet('sensor_glass', 'sight', 'glass', 'Vorderes Facettenglas', 99.5,101,162, 33,22,5,.5)
    for side, suffix in ((1,'l'),(-1,'r')):
        def inlay(key, group, role, label, pts, inside, outside, bevel=.6):
            plate(key+'_'+suffix, group, role, label, pts, outside-inside, bevel, x=side*(inside+outside)/2)
        inlay('cell_side','ammo','shell','Kassettenwange',
              [(-113,65),(-83,64),(-76,57),(-83,36),(-107,38),(-113,44)],17.8,19,.9)
        inlay('name_field','receiver','graphite','Eloxiertes Schriftfeld',
              [(-112,106),(-101,118),(-59,121),(-48,116),(-59,104),(-99,102)],24.25,25.4)
        add('name_'+suffix,'receiver','shell','Modellschriftzug','text',0,text='HERON',f=-80,u=108,
            x=side*25.5,side=side,depth=.3,size=6.8,align='CENTER')
        inlay('fore_chevron','support','anodized','Vorderes Keilfeld',
              [(125,90),(137,106),(164,110),(182,107),(158,103),(145,91)],25.75,26.5)
        inlay('beak_inset','barrel','graphite','Seitliches Facettenfeld',
              [(244,103),(257,107),(339,103),(347,100),(268,102)],12.8,14.2,.4)
        inlay('sensor_index','sight','energy','Sensorindex',
              [(-13,157),(-10,161),(4,161),(1,157)],16.8,17.7,.35)
        for i,(f,w) in enumerate(((-104,9),(-90,3))):
            top = 124+(f+125)*27/32
            low = 127+(f+102)*18/24
            inlay(f'bridge_band_{i}','sight','accent','Brückenmarkierung',
                  [(f,top),(f+w,top+.84*w),(f+w+5,low+.75*(w+5)),(f+5,low+3.75)],16.8,17.6,.35)
    refs = {'Socket_Hand':('handle',[-20,23,0]), 'Socket_SupportHand':('palm_sweep',[178,56,0]),
            'Socket_Muzzle':('beak_tile',[451,94,0]), 'Socket_Eye':('rear_glass',[-123,158,0])}
    points = {'grip.grip':refs['Socket_Hand'], 'grip.support':refs['Socket_SupportHand'],
              'grip.mag':('cell_fairing',[-91,48,0]), 'grip.charge':('main_shell',[-44,102,24]),
              'eject':('spine',[68,82,-20])}
    return (parts, {k:dict(part=p,at=list(at),source='Annahme: Bezugspunkt des Spielmodells') for k,(p,at) in refs.items()},
            {k:dict(part=p,at=list(at)) for k,(p,at) in points.items()})
