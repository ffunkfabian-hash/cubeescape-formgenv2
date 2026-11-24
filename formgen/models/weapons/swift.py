"""BT05 Swift, statisches Sci-Fi-Spielmodell. Alle Konturen und Abstände sind freie Formannahmen."""

from .sidearm_shell import Shell


def build():
    s=Shell('Swift')
    # Eine helle obere Wange und eine schmale, offene Ferse bilden den diagonalen Griff.
    grip_window=[(-68,-32),(-56,-17),(-49,-18),(-48,-25),(-58,-35)]
    s.plate('grip_arch','grip_controls','graphite','Gebogene Griffkontur',
            [(-56,62),(-24,58),(-12,43),(-22,15),(-37,-12),(-41,-31),(-54,-44),
             (-78,-41),(-81,-32),(-68,-25),(-57,-2),(-49,26),(-51,40),(-60,48)],29,2.2,
            cuts=[dict(shape='prof',pts=grip_window,w=43)])
    s.plate('grip_cheek','ammo','shell','Durchbrochene helle Ferse',
            [(-78,-25),(-60,16),(-50,43),(-38,47),(-32,38),(-35,20),(-51,-11),
             (-41,-15),(-41,-28),(-53,-43),(-77,-43),(-84,-37)],30.5,1.25,
            cuts=[dict(shape='prof',pts=grip_window,w=42)])
    s.plate('heel_tip','ammo','dark_metal','Schmaler Fersenabschluss',
            [(-83,-36),(-77,-40),(-54,-40),(-47,-37),(-52,-45),(-79,-46),(-85,-42)],31.5,1)
    s.plate('bow','grip_controls','dark_metal','Schlanker offener Bogen',
            [(-29,16),(-7,13),(7,18),(24,42),(19,47),(2,23),(-8,19),(-29,22)],12,1.1)
    s.plate('inner_mark','grip_controls','graphite','Geschwungene Innenzunge',
            [(-13,51),(-5,53),(-6,38),(-1,31),(-4,30),(-12,38)],8,.8)
    s.plate('keel','receiver','graphite','Durchgehender Gehäusekiel',
            [(-76,62),(-63,76),(-37,81),(65,77),(113,73),(133,64),(131,54),
             (113,48),(67,46),(20,40),(-12,46),(-33,52),(-65,51)],30,1.8)
    s.plate('rear_fold','receiver','shell','Nach hinten gezogene Hauptschale',
            [(-83,63),(-67,83),(-43,89),(4,87),(32,82),(24,66),
             (-3,60),(-32,60),(-48,53),(-70,55)],34,1.8)
    s.plate('fore_fold','barrel','shell','Spitz auslaufende Vorderwange',
            [(32,66),(39,82),(67,84),(113,78),(142,69),(151,63),(135,57),
             (99,59),(57,62),(41,58)],35,1.7)
    s.plate('chin','barrel','anodized','Lange schmale Unterkante',
            [(32,56),(57,61),(104,59),(142,58),(150,63),(147,54),
             (121,48),(76,49),(42,46),(29,49)],25,1.3)
    s.facet('tip_shadow','barrel','graphite','Eingefasste Spitze',139,153,63,26,16,4)
    s.facet('tip_tile','barrel','dark_metal','Geschlossene Facettenspitze',151,155,63,23,13,3,.8)
    s.facet('tip_slash','barrel','energy','Stirnindex',154.8,155.4,63,10,2,.6,.25)
    s.plate('rear_pier','sight','shell','Rückwärtiger Bügelanstieg',
            [(-65,80),(-49,96),(-32,103),(-26,99),(-42,90),(-55,82)],22,1.1)
    s.plate('front_pier','sight','anodized','Vorderer Bügelabschluss',
            [(12,100),(20,102),(42,87),(44,82),(35,82),(24,91)],18,.9)
    s.plate('ribbon','sight','graphite','Schwebende flache Visierkappe',
            [(-50,95),(-37,105),(-6,106),(16,104),(23,100),(16,98),(-33,100),(-46,94)],23,1)
    s.facet('eye_tile','sight','glass','Getönte Sichtfläche',-43,-40,100,18,7,1.7,.45)
    s.inlay('mark','receiver','accent','Keilmarkierung',
            [(-61,80),(-54,82),(-60,71),(-67,69)],16.8,17.5,.35)
    s.inlay('name_tile','receiver','anodized','Schmales Schriftfeld',
            [(-46,70),(-39,78),(-12,79),(-5,76),(-12,68),(-38,67)],16.7,17.8,.55)
    s.word('receiver','shell',-26,71,17.85,4.5)
    s.inlay('feather','barrel','anodized','Federförmiges Seitenfeld',
            [(48,68),(59,76),(104,74),(119,70),(97,70),(61,71)],17.2,18.5,.45)
    s.inlay('glint','barrel','energy','Kurzer Lichtindex',
            [(62,72.6),(68,74.5),(78,74.2),(74,72.5)],18.35,18.8,.18)
    refs={'Socket_Hand':('grip_arch',[-37,18,0]),'Socket_SupportHand':('grip_arch',[-38,19,0]),
          'Socket_Muzzle':('tip_tile',[155,63,0]),'Socket_Eye':('eye_tile',[-42,100,0])}
    points={'grip.grip':refs['Socket_Hand'],'grip.support':refs['Socket_SupportHand'],
            'grip.mag':('heel_tip',[-66,-43,0]),'grip.charge':('rear_fold',[-34,75,16]),
            'eject':('keel',[20,59,-14])}
    return s.finish(refs,points)
