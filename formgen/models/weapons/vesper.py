"""BT02 Vesper. Konturen, Fasen und Farbverteilung sind freie Formannahmen für ein statisches Spielasset."""

from . import trestle


def offset(points, d):
    """Polygon (f, u) parallel versetzt: d > 0 nach außen, d < 0 nach innen (Gehrung an jeder Ecke)."""
    n = len(points)
    turn = 1 if sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1] for i in range(n)) > 0 else -1
    def line(a, b):
        df, du = b[0]-a[0], b[1]-a[1]
        k = (df*df+du*du)**.5
        nf, nu = turn*du/k*d, -turn*df/k*d
        return (a[0]+nf, a[1]+nu), (df, du)
    out = []
    for i in range(n):
        (p, r), (q, s) = line(points[i-1], points[i]), line(points[i], points[(i+1)%n])
        t = ((q[0]-p[0])*s[1]-(q[1]-p[1])*s[0])/(r[0]*s[1]-r[1]*s[0])
        out.append((round(p[0]+t*r[0], 3), round(p[1]+t*r[1], 3)))
    return out


def build():
    family, _, _ = trestle.build()
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

    plate('aft_pad', 'stock', 'graphite', 'Abgesetzte Schulterkante',
          [(-255,115),(-246,121),(-233,117),(-235,46),(-247,30),(-258,33),(-262,45)], 47, 4)
    plate('aft_shell', 'stock', 'shell', 'Kurze Schaftwange',
          [(-246,113),(-231,128),(-181,133),(-147,128),(-128,116),(-141,98),
           (-188,100),(-218,90),(-237,62),(-245,63)], 43, 3)
    plate('aft_spine', 'stock', 'dark_metal', 'Schräge untere Strebe',
          [(-249,42),(-241,33),(-222,40),(-120,78),(-109,91),(-137,93),(-221,57)], 27, 2)
    plate('aft_rest', 'stock', 'graphite', 'Wangenauflage',
          [(-237,122),(-224,132),(-182,137),(-157,133),(-151,128),(-183,130),(-225,125)], 34, 2)
    plate('body_spine', 'receiver', 'graphite', 'Freiliegender Gehäusekiel',
          [(-151,109),(-134,120),(-112,116),(6,106),(71,94),(121,85),(129,51),
           (98,38),(55,35),(13,37),(-8,48),(-59,61),(-99,78),(-143,83)], 44, 3)
    # BASIC-02 setzt sein Seitenpaneel in eine Mulde (Stufe statt Schrauben). Vesper senkt das Typenschild
    # ebenso ein: Mulde 1,2 mm umlaufend, Boden bei x ±23,2 (Schalenfläche ±24,5). Maße: Annahme.
    badge = [(-118,102),(-104,115),(-70,119),(-51,114),(-58,100),(-103,98)]
    plate('aft_cowl', 'receiver', 'shell', 'Gefaltete hintere Schale',
          [(-136,99),(-120,119),(-83,130),(-54,130),(25,111),(52,99),(36,78),
           (1,73),(-52,79),(-73,88),(-121,88)], 49, 3,
          cuts=[dict(shape='prof', pts=offset(badge, 1.2), w=3, x=side*24.7) for side in (1, -1)])
    # Schalenabschluss wie die blanke Deckplatten-Kante von BASIC-02: schmaler Kragen über dem Hinterende,
    # 0,5 mm je Seite breiter als die Schale, folgt deren Kontur.
    plate('aft_cowl_cap', 'receiver', 'trim', 'Blanker Schalenabschluss',
          [(-121,88),(-136,99),(-120,119),(-116,120.2),(-131,99.4),(-117,88)], 50, .8)
    plate('bridge_shadow', 'receiver', 'dark_metal', 'Brückenunterkante',
          [(-105,118),(-67,145),(-53,149),(58,149),(109,123),(102,117),(55,138),(-48,138),(-84,120)], 32, 1.6)
    plate('bridge_fold', 'receiver', 'shell', 'Flache Rahmenbrücke',
          [(-116,119),(-68,151),(-54,154),(57,154),(72,150),(117,126),
           (110,121),(101,121),(55,143),(-51,143),(-86,121)], 40, 1.6)
    plate('bridge_seat', 'receiver', 'anodized', 'Abgesetzter Brückenschuh',
          [(94,119),(101,122),(110,122),(116,125),(121,122),(117,118),(98,118)], 42, .9)
    for i,(f,w) in enumerate([(-91,10),(-74,3)]):
        def top(y):
            return 119+(y+116)*32/48+.45
        def bottom(y):
            return 121+(y+86)*22/35+.35
        plate(f'bridge_mark_{i}', 'receiver', 'accent', 'Bügelmarkierung',
              [(f,top(f)),(f+w,top(f+w)),(f+w+9,bottom(f+w+9)),(f+9,bottom(f+9))], 40.8,.45)
    plate('crest', 'sight', 'graphite', 'Scheitelleiste',
          [(-54,152),(-45,156),(47,156),(56,152),(46,150),(-46,150)], 31, 1)

    # Das Seitenfenster ist ein echter Durchbruch. Der dunkle Grund und die
    # hellen Zwischenräume liegen tiefer als die keramischen Segmente.
    # Vorgabe Gesamtbreite 51–54 mm: Die beidseitigen Serienfelder schließen bei ±26,5 ab.
    window=[(108,74),(130,102),(205,102),(237,91),(231,74),(210,58),(137,57),(111,64)]
    plate('pulse_mantle', 'support', 'shell', 'Tiefe Impulsschale',
          [(71,77),(83,105),(97,118),(119,118),(135,124),(198,122),(230,115),
           (259,98),(257,61),(235,43),(204,37),(142,35),(109,44),(91,56),(74,57)],
          52, 3.1, cuts=[dict(shape='prof',pts=window,w=64)])
    plate('well_floor', 'support', 'graphite', 'Zurückgesetzter Fenstergrund',
          [(81,79),(102,109),(139,114),(208,111),(246,99),(245,65),(214,46),(136,45),(89,57)], 34, 2.5)
    plate('chin', 'support', 'graphite', 'Schwebende Bugkante',
          [(112,45),(144,40),(205,41),(247,54),(255,58),(247,42),(210,30),
           (143,27),(116,33),(106,38)], 38, 2.2)
    plate('cell', 'ammo', 'graphite', 'Flache Impulskassette',
          [(47,47),(90,50),(112,25),(118,13),(108,1),(79,-5),(64,1),(53,20)], 40, 3)
    plate('cell_heel', 'ammo', 'dark_metal', 'Keramiksockel',
          [(62,5),(80,-1),(109,5),(116,12),(120,7),(114,-1),(81,-10),(67,-6)], 44, 1.7)

    cap('front_gasket','dark_metal','Stirnschatten',237,264,55,45,8,1.4)
    cap('front_mask','graphite','Breite geschlossene Stirnmaske',259,278,57,48,10,1.8)
    # Abschlussstück der Stirn: blanke Kante am Hinterende der Maske, je Seite 0,4 mm über der Maske, Ecke so
    # gewählt, dass auch die Achtkant-Fase 0,4 mm Abstand hält (10 + 0,4·(2−√2)). Vorbild: die Deckplatten-Kante
    # von BASIC-02 (Trim, eine Stufe größer als die Platte, an deren Ende). Der schmalere Stirnschatten (45 mm)
    # bleibt als dunkle Fuge davor; die Draufsicht behält dadurch die schlanke Staffel 52 | 45 | 48,8 → 48 → 39 mm.
    cap('front_lip','trim','Blanke Maskenkante',258.4,260.6,57.8,48.8,10.234,.5)
    cap('front_glaze','anodized','Facettierte Keramikstirn',275,280,44,39,8,1.3)
    for idx, level in enumerate((71,81)):
        add(f'front_trace_{idx}','barrel','energy','Lichtsignatur','xprof',.5,f0=279.6,f1=280.8,
            cu=level,pts=[(-13,-1.4),(7,-1.4),(12,1.4),(-8,1.4)])
    for side,suffix in ((1,'l'),(-1,'r')):
        def relief(key,group,role,name,pts,inside,outside,bevel):
            plate(key+'_'+suffix,group,role,name,pts,outside-inside,bevel,x=side*(inside+outside)/2)
        for i in range(3):
            f=121+i*29
            relief(f'porcelain_{i}','support','anodized','Rauchgraues Keramiksegment',
                   [(f,67),(f+15,96),(f+35,96),(f+22,69),(f+15,63),(f+4,63)],16.7,22,1.5)
            # Metallene Stirnkante je Segment, übersetzt aus den Spulenringen von BASIC-02: trennt die drei
            # dunklen Segmente auch schräg vom Lichtstreifen davor, ohne selbst als Lichtstreifen zu wirken.
            relief(f'segment_edge_{i}','support','dark_metal','Segmentstirn',
                   [(f+31.3,95.2),(f+34,95.2),(f+21.4,69.8),(f+18.7,69.8)],21.6,22.4,.25)
            if i<2:
                relief(f'pulse_line_{i}','support','energy','Licht im Segmentzwischenraum',
                       [(f+23,66),(f+37,95),(f+41,95),(f+28,66)],16.8,18.8,.7)
        relief('cell_panel','ammo','shell','Kassettenwange',
               [(63,35),(80,42),(101,22),(104,14),(82,9),(74,12)],19.8,22.5,1)
        # Schriftfeld 0,2 mm unter der Schalenfläche, Schrift (x ±0,3) endet bei 24,45 knapp darunter.
        relief('aft_badge','receiver','anodized','Eingelassenes Schriftfeld',badge,23.0,24.3,.8)
        add('word_'+suffix,'receiver','shell','Schriftzug','text',0,text='VESPER',f=-85,u=104,
            x=side*24.15,side=side,depth=.3,size=7.3,align='CENTER')
        # Impulsfenster: abgestufte Innenkante der hellen Schale (Ledge 2,6 mm, x 22,3–24,3) über den
        # Keramiksegmenten (bis x 22); außen bleibt eine 1,7 mm tiefe Wand. Vorbild: BASIC-02-Kammerfenster.
        plate('window_step_'+suffix,'support','shell','Abgestufte Fensterkante',offset(window,.3),2,.6,
              x=side*23.3,cuts=[dict(shape='prof',pts=offset(window,-2.6),w=4,x=side*23.3)])
        relief('serial','support','dark_metal','Serienfeld',
               [(148,113),(155,118),(183,117),(178,112)],25.7,26.5,.5)
        for i in range(3):
            f=32+i*7
            relief(f'index_{i}','receiver','metal','Indexsegment',
                   [(f,64),(f+4,64),(f+7,70),(f+3,70)],21.8,22.8,.3)

    anchors = dict(Socket_Hand=('handle',[-20,23,0]), Socket_SupportHand=('chin',[165,35,0]),
                   Socket_Muzzle=('front_trace_1',[280,81,0]), Socket_Eye=('optic_pane',[-20,161,0]))
    points = {'grip.grip':anchors['Socket_Hand'], 'grip.support':anchors['Socket_SupportHand'],
              'grip.mag':('cell',[86,17,0]),'grip.charge':('aft_cowl',[-30,101,24]),
              'eject':('body_spine',[39,65,-21])}
    return (parts, {k:dict(part=p,at=list(at),source='Annahme: Bezugspunkt des Spielmodells') for k,(p,at) in anchors.items()},
            {k:dict(part=p,at=list(at)) for k,(p,at) in points.items()})
