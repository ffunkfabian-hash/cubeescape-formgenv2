"""BT04 Cairn, statisches Sci-Fi-Spielmodell. Proportionen, Fasen und Farbakzente sind Formannahmen."""

from .sidearm_shell import Shell


def build():
    s = Shell('Cairn')
    s.plate('grip_cast','grip_controls','graphite','Geschwungene Griffschale',
            [(-67,75),(-31,76),(-12,60),(-23,36),(-42,-7),(-42,-24),(-55,-33),
             (-81,-33),(-89,-24),(-80,-2),(-67,26),(-56,52),(-72,61)], 37, 3.3)
    s.inlay('grip_panel','grip_controls','rubber','Eingesetzte Griffwange',
            [(-58,40),(-41,47),(-35,35),(-49,3),(-56,-20),(-72,-22),(-77,-16),(-67,11)],18.15,20.1,1.4)
    s.plate('heel','ammo','dark_metal','Gestufter Griffabschluss',
            [(-85,-22),(-71,-25),(-48,-22),(-42,-26),(-48,-36),(-78,-38),(-90,-32)], 41, 1.8)
    s.plate('bow','grip_controls','dark_metal','Offener kantiger Griffbogen',
            [(-35,15),(-9,11),(10,16),(28,47),(23,53),(5,25),(-9,19),(-32,21)], 17, 1.4)
    s.plate('pendant','grip_controls','graphite','Kleine Innenzunge',
            [(-17,61),(-7,59),(-10,45),(-5,38),(-10,37),(-17,46)], 10, 1.1)
    s.plate('core','receiver','graphite','Dunkler Mittelblock',
            [(-82,72),(-70,91),(-33,104),(46,103),(107,97),(120,78),
             (114,51),(79,40),(25,40),(-4,52),(-44,58),(-70,59)], 42, 2.6)
    s.plate('aft_shield','receiver','shell','Hintere Keramikschulter',
            [(-86,78),(-70,101),(-42,111),(-12,109),(5,99),(-5,76),
             (-33,66),(-68,64),(-82,67)], 46, 2.4)
    s.plate('keystone','receiver','shell','Gestufte obere Bugschale',
            [(18,84),(28,103),(53,110),(123,109),(148,97),(147,81),(130,76),
             (85,78),(68,70),(40,70)], 49, 2.1)
    s.plate('chin_shell','barrel','dark_metal','Abgesetztes Unterkinn',
            [(64,69),(87,75),(147,78),(153,71),(148,52),(127,44),(80,44),(62,50)], 43, 2)
    s.facet('nose_rim','barrel','graphite','Breite Stirnfassung',139,157,77,46,48,9,1.4)
    s.facet('nose_ceramic','barrel','anodized','Geschlossene Keramikstirn',154,159,77,38,39,8)
    for i,u in enumerate((72,80)):
        s.facet(f'nose_inlay_{i}','barrel','energy','Eingelegte Lichtkerbe',158.8,159.6,u,16,2.4,.8,.35)
    # Die fixen Flankenmedaillons bilden ein flaches, konzentrisches Relief.
    for side, end in ((1,'l'),(-1,'r')):
        for key,role,r,inner,outer in [('round_base','graphite',25.5,19,23.9),
                                      ('ring','metal',23.7,23.6,24.7),('coin','anodized',22.3,24.4,26.2)]:
            a,b=sorted((side*inner,side*outer))
            s.add(key+'_'+end,'receiver',role,'Facettierte Keramikwange','cyl',.7,
                  axis='x',c=(9,76),a0=a,a1=b,r=r,segs=16)
    s.inlay('coin_dash','receiver','energy','Kurzer Lichtindex',
            [(0,73),(6,83),(12,83),(6,73)],26.0,26.5,.32)
    s.inlay('cap_band','receiver','accent','Versetzte Schalenmarkierung',
            [(67,108),(77,108),(65,92),(55,92)],24.1,24.9,.5)
    s.inlay('lower_panel','barrel','shell','Keramikfeld am Kinn',
            [(83,59),(97,68),(132,69),(136,63),(123,54),(89,53)],21.2,23,.7)
    s.word('barrel','graphite',109,58,23.05,5.6)
    s.plate('bridge_aft','sight','shell','Brückenanstieg',
            [(-77,96),(-55,117),(-44,120),(-38,114),(-57,100)],27,1.2)
    s.plate('bridge_front','sight','shell','Vorderes Brückenbein',
            [(6,117),(18,120),(45,109),(42,104),(30,106)],26,1.1)
    s.plate('brow','sight','graphite','Flaches Sensorband',
            [(-64,115),(-52,124),(8,124),(24,120),(27,116),(-45,117),(-60,112)],30,1.2)
    s.facet('glass_tile','sight','glass','Facettiertes Sichtfenster',-61,-57,118,26,10,2,.6)
    s.inlay('grip_index','grip_controls','dark_metal','Griffmarke',
            [(-67,-11),(-55,-8),(-54,-5),(-66,-8)],19.8,20.65,.25)
    refs={'Socket_Hand':('grip_cast',[-55,15,0]),'Socket_SupportHand':('grip_cast',[-54,17,0]),
          'Socket_Muzzle':('nose_ceramic',[158,77,0]),'Socket_Eye':('glass_tile',[-60,118,0])}
    points={'grip.grip':refs['Socket_Hand'],'grip.support':refs['Socket_SupportHand'],
            'grip.mag':('heel',[-66,-29,0]),'grip.charge':('aft_shield',[-50,88,22]),
            'eject':('core',[60,78,-20])}
    return s.finish(refs,points)
