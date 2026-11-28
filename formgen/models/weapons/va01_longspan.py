"""VA01 Longspan. Kanonische Familienbausteine aus dem gepinnten BALLON-Kit.
Vorgabe: Griff, Magazin, Bedienzeichen und Optik sind Kit-Bausteine. Alle übrigen
Maße sind Entwurfsannahmen im Formgen-Koordinatensystem (siehe docs/modellsprache.md).
Leitlinien der Hülle: Griffdach 45, Laufachse 110, Gehäusedach 140.
"""
from functools import partial
from formgen import ballon, extended_lines

SHEET = "VA01"
TITLE = "Longspan"
ASSEMBLIES = [
    dict(id=key, de=name) for key, name in (
        ("receiver", "Gehäuse"), ("stock", "Schulterstück"), ("support", "Handauflage"),
        ("barrel", "Frontabschluss"), ("grip_controls", "Griff und Bedienung"),
        ("mechanism", "Bedienfeld"), ("ammo", "Magazin"), ("sight", "Visier"))
]


def silhouette(f0, f1, low, high, chamfer):
    return [(f0+chamfer,low), (f1-chamfer,low), (f1,low+chamfer), (f1,high-chamfer),
            (f1-chamfer,high), (f0+chamfer,high), (f0,high-chamfer), (f0,low+chamfer)]


class Shell:
    def __init__(self, snap):
        self.kit = partial(ballon.call, snap)
        self.parts = []

    def side(self, key, label, role, assembly, points, width, purpose, bevel=2, **kw):
        self.parts.append(self.kit("prof", key, label, label, assembly, role, purpose,
                                   "an der angrenzenden Gehäusefläche", points, width, bevel, **kw))

    def cross(self, key, label, role, assembly, start, end, centre, halfwidth, halfheight, corner, purpose):
        section = silhouette(-halfwidth, halfwidth, -halfheight, halfheight, corner)
        p = self.kit("xprof", key, label, role, start, end, section, centre,
                     func=purpose, attach="zwischen den benachbarten Schalen", bevel=1.5)
        p["asm"] = assembly
        self.parts.append(p)

    def disk(self, key, label, role, assembly, axis, centre, start, end, radius, purpose):
        self.parts.append(self.kit("cyl", key, label, label, assembly, role, purpose,
                                   "auf der sichtbaren Stirnfläche", axis, centre, start, end,
                                   radius, bevel=.6, segs=24))

    def fasteners(self, key, points, x):
        heads = self.kit("screws", points, x, r=3, h=1.5)
        self.parts.append(self.kit("part", key, "Deckelschrauben", "Cover fasteners",
                                   "receiver", "multi", "trim", "Markieren die abnehmbare Abdeckung",
                                   "auf beiden Deckelflächen", .25, items=self.kit("mirror", heads)))


def architecture(s):
    """Ein einziges langes Fenster trennt das helle Dach von der dunklen Handauflage."""
    s.side("shoulder", "Schultersteg", "shell", "stock",
           [(-330,60),(-285,60),(-255,90),(-80,90),(-80,130),(-90,140),(-330,140)],
           35, "Führt die obere Kontur bis zur Schulter")
    s.side("heel", "Schulterpolster", "rubber", "stock", silhouette(-345,-325,40,140,5),
           40, "Zeigt die Schulterauflage")
    s.side("comb", "Wangenpolster", "graphite", "stock", silhouette(-315,-170,135,150,5),
           38, "Markiert die Wangenauflage")
    s.cross("stock_joint","Schaftabschluss","anodized","stock",-100,-85,115,22,25,5,
            "Fasst das Schulterstück am Gehäuse")
    s.side("lower", "Griffträger", "graphite", "receiver",
           [(-80,65),(-60,45),(150,45),(180,75),(180,95),(-80,95)],
           44, "Verbindet Griff, Magazin und Vorderkörper")
    s.cross("cowl","Gehäusehaube","shell","receiver",-90,145,115,25,25,10,
            "Steigt im Querschnitt zum Visierdach an")
    s.side("bridge", "Brückendach", "shell", "receiver",
           [(125,120),(425,120),(435,130),(435,140),(125,140)], 40,
           "Zeichnet den langen oberen Rand des offenen Brückenfensters")
    s.cross("bridge_tip","Brückenstirn","shell","support",410,435,100,24,35,10,
            "Schließt das Fenster an der Front")
    s.side("cradle","Handsteg","graphite","support",
           [(150,65),(165,50),(345,50),(365,70),(425,70),(425,80),(150,80)],
           40, "Unterkante des offenen Fensters und Auflage der Stützhand")
    s.side("palm","Handpolster","rubber","support",silhouette(205,335,45,60,5),36,
           "Kennzeichnet die Handauflage unter dem Steg")
    s.fasteners("bridge_pins",[(420,95),(420,120)],24)
    return 100, 435, 545, 270


def finish(s):
    # Die Dachkrone zeichnet die Breite: Messingmarke hinten, zwei blanke Stirnkanten vorn.
    s.cross("roof_crown", "Dachkrone", "shell", "receiver", 145, 405, 139, 16, 6, 4,
            "Zeigt in der Draufsicht die schmalere Krone über dem Brückensteg")
    s.cross("roof_end", "Dachabschluss", "trim", "receiver", 403, 408, 138, 17, 6, 4,
            "Schließt die Dachkrone zum vorderen Pfeiler ab")
    s.cross("roof_start", "Dachwurzel", "anodized", "receiver", 140, 151, 139, 18, 7, 4,
            "Zeigt den Übergang von der breiten Haube auf die Krone")
    for side, name in ((-1, "rechts"), (1, "links")):
        s.side("palm_inlay_" + name, "Griffeinlage " + name, "rubber", "support",
               silhouette(185, 325, 60, 75, 5), 3, "Markiert die Stützfläche seitlich",
               bevel=1, x=side * 20.5)
        s.disk("bridge_boss_" + name, "Pfeilerauge " + name, "metal", "support", "x",
               (420, 108), side*23.5, side*26, 6, "Markiert die Stirn des Brückenpfeilers")
        s.side("cheek_" + name, "Wangeneinlage " + name, "anodized", "stock",
               [(-305,100),(-295,90),(-265,90),(-255,100),(-150,100),(-150,120),(-305,120)],
               3, "Gliedert den Schaft unterhalb der Wangenauflage", bevel=1, x=side*18)
    s.cross("rear_spine", "Schaftrücken", "shell", "stock", -165, -105, 134, 15, 7, 4,
            "Verbindet Wangenstück und Gehäusedach in der Draufsicht")
    s.disk("heel_badge", "Schaftplakette", "brass", "stock", "x", (-235,110), 19, 21, 5,
           "Markiert die gelöste Kontur der Wangeneinlage")
    s.side("index_plate", "Indexplatte", "dark_metal", "receiver",
           silhouette(3,42,104,117,3), 2, "Dunkles Feld neben der Statusanzeige", bevel=.6, x=25.5)
    for i, f in enumerate((12,22,32)):
        s.side(f"index_{i+1}", "Indexstrich", "metal", "receiver",
               [(f,107),(f+3,107),(f+3,114),(f,114)], 1, "Kennzeichnung des Statusfeldes",
               bevel=.2, x=26.75)
    s.cross("nose_base", "Frontsockel", "dark_metal", "barrel", 435, 448, 110, 19, 19, 6,
            "Staffelt die Front von der breiten Schale auf die schmale Nase")
    s.disk("nose_cuff", "Frontmanschette", "anodized", "barrel", "f", (110,0), 445, 459, 15,
           "Fasst den Übergang zum runden Frontsteg")
    s.disk("nose_line", "Manschettenkante", "trim", "barrel", "f", (110,0), 457, 460, 15.5,
           "Zeichnet den Abschluss der Manschette")
    s.fasteners("cheek_rivets", [(-290,105),(-170,110)],19.5)


def make(snap):
    s = Shell(snap)
    mag, nose, tip, palm = architecture(s)
    finish(s)
    s.parts.extend(s.kit("grip_v21",top=45))
    s.parts.extend(s.kit("rifle_mag",mag,45,depth=55,length=120,tilt=0,curve=15,w=25,rounds=False))
    for sign, name in ((-1, "rechts"), (1, "links")):
        s.side("mag_grip_" + name, "Magazingriff " + name, "anodized", "ammo",
               [(mag+15,-55),(mag+20,-60),(mag+40,-60),(mag+40,10),(mag+35,15),(mag+15,15)],
               2, "Zeigt im Inventar die Grifffläche des Wechselmagazins",
               bevel=.8, x=sign*13, parent_part="magazine")
    s.parts.extend(s.kit("selector",0,65,x=23.5))
    s.parts.extend(s.kit("charging_handle",-70,113,x=29,travel=15))
    s.parts.extend(s.kit("rail",-75,-5,140))
    optic, anchors = s.kit("reflex_sight_v21",-65,148)
    s.parts.extend(optic)
    s.disk("front_stem","Frontsteg","dark_metal","barrel","f",(110,0),nose-3,tip-35,12,
           "Verbindet die abgestufte Stirn mit dem Vorderkörper")
    s.disk("shoulder_ring","Frontbund","trim","barrel","f",(110,0),nose+25,nose+29,13.5,
           "Zeigt den Übergang von der Schale zur schmalen Front")
    s.cross("end_cap","Stirnkappe","anodized","barrel",tip-40,tip,110,17,17,7,
            "Kennzeichnet die Front des Spielmodells")
    s.disk("front_rim","Stirnring","trim","barrel","f",(110,0),tip-1,tip+2,13,"Fasst das dunkle Endfeld")
    s.disk("front_mark","Endfeld","graphite","barrel","f",(110,0),tip+1,tip+3,9,"Dunkler Abschluss der Frontansicht")
    s.fasteners("body_screws",[(-80,120),(0,120),(90,120)],25)
    s.fasteners("lower_screws",[(-45,70),(40,70),(115,70)],22)
    s.disk("display_rim","Anzeigefassung","trim","receiver","x",(61,110),24.5,27,18,
           "Begrenzt das runde Statusfeld auf der linken Gehäuseseite")
    s.disk("display_face","Statusfeld","anodized","receiver","x",(61,110),26.5,29,16,
           "Trägt die Bereitschaftsanzeige")
    s.parts.append(s.kit("glow","status","Bereitschaft","Ready light","receiver",49,73,102,118,
                         x=29.5,w=2,func="Zeigt den Spielzustand im Statusfeld"))
    s.disk("heel_pin","Schultermarke","metal","stock","x",(-235,110),-18,18,6,
           "Markiert die Verbindung am Schulterstück")
    anchors.update(Socket_Hand=dict(at=(0,0,0),part="grip"),
                   Socket_SupportHand=dict(at=(palm,50,0),part="palm"),
                   Socket_Muzzle=dict(at=(tip+3,110,0),part="front_mark"))
    return dict(META=dict(id=SHEET,name=TITLE,type_de="Automatikgewehr",type_en="Auto Rifle"),
                PARTS=s.parts,ASSEMBLIES=ASSEMBLIES,ANCHORS=anchors)

def author(snap):
    raw = make(snap)
    doc, _ = extended_lines.author(raw, SHEET)
    for target, original in zip(doc["PARTS"], raw["PARTS"]):
        target["func"] = original["func"]
        target["attach"] = original["attach"]
        if original["id"].startswith("sight_") or original["id"] in {
            "rail", "grip", "grip_cap", "trigger", "trigger_guard", "selector",
            "charging_handle", "magazine", "magazine_base"}:
            target["provenance"] = dict(kind="Vorgabe", source="BASIC-Familienbaustein aus basic.common, BALLON-Pin in config.toml")
    doc["INFO"].update(type="auto_rifle", type_de="Automatikgewehr", num="01", nick=TITLE, variant="A",
                       summary="Offene Längsbrücke über einer abgesetzten Handauflage.",
                       provenance=dict(kind="Annahme", source="VA01 Longspan. Eigene Außenmaße auf dem Entwurfsraster; Familienbausteine nach dem BALLON-Pin in config.toml."))
    return doc
