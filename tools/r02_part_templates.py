"""R02 „Frost“: maßhaltige Einzelteil-Schablonen für Bildgenerator → Meshy → Blender.

Je Teil ein SVG (4000×4000 px) mit Front, Seite (von links, wie Profil B), Rücken und Draufsicht
(vorn = unten) in einem gemeinsamen Maßstab je Blatt, dazu PNG mit und ohne Unterlage und ein
manifest.json. Ebenen/Gruppen: underlay, frame, markers, swatches. Regeln: docs/zeichnungsvorgabe-teile.md.

Herkunft: Hüllrahmen und Konturen aus tools/r02_measure.py (mask revision 1, 5-mm-Zeilen), Front
verbindlich (Rücken-Rahmen = gespiegelter Front-Rahmen). Gelenkhöhen aus docs/herkunft-r02.md,
Gelenkmitten f/x aus den Socket-Ankern bzw. der gemessenen Laufmitte, Anschlussdurchmesser als
schmalste gemessene Breite im ausgewiesenen Zeilenfenster. Verdeckte Kanten sind Annahmen mit Quelle.
Paarige Teile sind die anatomisch linke Seite (x > 0); die rechte entsteht durch Spiegeln an x = 0.
Nur Werkzeug: kein Modul unter formgen/ liest diese Ausgaben (KI-Ergebnisse bleiben optional).

Aufruf: python tools/r02_part_templates.py [--out DIR] [--only kopf,arm] [--force]
"""
import argparse,base64,hashlib,io,json,math,subprocess,sys,tomllib
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from tools import r02_measure

REF=r02_measure.REF
OUT=REF/'part-templates'
SHEET=REF/'r02-sheet-9803.png'
CANVAS=4000
STEP=5
MARGIN=25  # mm Luft um den Hüllrahmen je Ansicht
ROLES=['frost_shell','frost_frame','frost_slate','frost_joint','frost_crystal','frost_core','frost_visor']
# Konstruktionsfarben: kommen in skins.toml nicht vor und dürfen nicht ins Konzeptbild.
BG,FRAME_C,MARK_C,TEXT_C='#808080','#FFD400','#FF00FF','#111111'
FONT='Helvetica, Arial, sans-serif'

A=lambda value,source:{'kind':'Annahme','value':value,'source':source}
P=lambda source:{'kind':'gemessen','value':None,'source':source}
SRC_ARM_FRONT='herkunft-r02.md › Annahmen: Arm-Vorderkanten am Profil-Farbbild (Polster ≈+87, Oberarm ≈+35, Unterarm +22..+49)'

# Gelenke: u aus herkunft-r02.md (verwendet); f/x Mitte; Durchmesser = schmalste Breite im Fenster.
JOINTS={
    'hals':dict(de='Hals',u=1760,f=(0,'Socket_Neck (Profilmitte)'),x=(0,'Mittelebene'),
                win=(1760,1790),sel=('clip',(-150,150)),dsrc='Front: Halsring über der Schaloberkante'),
    'taille':dict(de='Taille',u=1265,f=(10,'Socket_Waist (Gürteloberkante)'),x=(0,'Mittelebene'),
                  win=(1265,1310),sel=('clip',(-215,215)),dsrc='Front: Bauchansatz über dem Gürtel'),
    'schulter':dict(de='Schulter',u=1560,f=(-40,'Annahme: Achse unter dem Polster (Socket_Shoulder)'),
                    x=(260,'Annahme: Socket_Shoulder'),win=(1440,1475),sel=('center',(205,540)),
                    dsrc='Ersatzzeilen: Oberarm direkt unter dem Polster (Achse verdeckt)'),
    'ellbogen':dict(de='Ellbogen',u=1329,f=(-77,'gemessen: Profil-Ellbogenscheibe'),x='run',
                    win=(1314,1344),sel=('center',(205,540)),dsrc='Front: Ellbogenblock'),
    'handgelenk':dict(de='Handgelenk',u=1036,f=(15,'Annahme: Mitte Handprofil u1040 (−30..+60)'),x='run',
                      win=(1031,1046),sel=('center',(400,560)),dsrc='Front: schmalste Zeile Unterarm/Hand'),
    'huefte':dict(de='Hüfte',u=1060,f=(15,'Annahme: Socket_Hip'),x=(135,'Annahme: Socket_Hip'),
                  win=(940,970),sel=('center',(20,330)),dsrc='Ersatzzeilen: Oberschenkel unter dem Schritt (Gelenk verdeckt)'),
    'knie':dict(de='Knie',u=675,f=(0,'gemessen: Kniescheibenmitte (Registrierung f=0)'),x='run',
                win=(660,690),sel=('center',(20,330)),dsrc='Front: Knieblock'),
    'knoechel':dict(de='Knöchel',u=169,f=(-22,'gemessen: Profilscheibe A2'),x='run',
                    win=(164,184),sel=('center',(20,330)),dsrc='Front: Knöchelzeilen über dem Fuß'),
}

# u: Hüllhöhe (Gelenkmarken begrenzen); mu: Zeilen der Front-/Rückenmessung; sel: Laufauswahl
# (clip = Läufe auf das Fenster schneiden, center = Läufe mit Mitte im Fenster); fb/ff: Tiefe hinten/vorn.
PARTS=[
    dict(id='kopf',de='Kopf',side='mitte',u=(1760,2000),mu=(1760,2000),sel=('clip',(-300,300)),
         fu=(1760,2000),fb=P('Profil A/B gemittelt'),ff=P('Profil A/B gemittelt'),side_contour=True,
         joints=['hals'],note='Helm mit Visier; Hals steckt im Schal (Teil Oberkörper).'),
    dict(id='oberkoerper',de='Oberkörper (Brust/Bauch)',side='mitte',u=(1265,1760),mu=(1265,1760),
         sel=('clip',(-201.4,201.4)),fu=(1265,1740),
         fb=A(-122,'herkunft-r02.md › Annahmen: Rumpfrücken Brust −122 (im Profil von Armen verdeckt)'),
         ff=P('Profil-Vorderkante (Brust bildet die Silhouette)'),side_contour=False,
         joints=['hals','taille',('schulter','beide')],
         note='Breite hinter den Polstern ±201 (gemessen u1500). Flanken unter den Armen vollständig zeichnen.'),
    dict(id='becken',de='Becken mit Gürtel',side='mitte',u=(975,1265),mu=(975,1265),
         sel=('clip',(-214,214)),fu=(1060,1265),
         fb=A(-118,'herkunft-r02.md › Annahmen: Becken −108..−112, Gürtel −116..−118'),
         ff=P('Profil-Vorderkante (Gürteltaschen)'),side_contour=False,
         joints=['taille',('huefte','beide')],
         note='Unterkante = Schritt u975 (gemessen). Unter u1060 verdecken die Oberschenkel die Seiten (Rahmen ±214 Annahme).'),
    dict(id='schulterpolster',de='Schulterpolster',side='links',u=(1470,1745),mu=(1470,1745),
         sel=('clip',(204,430)),fu=(1480,1700),fb=P('Profil-Rückenkante (Polster bildet die Silhouette)'),
         ff=A(87,SRC_ARM_FRONT),side_contour=False,joints=['schulter'],
         note='Innenkante x204 = Brustkante (Annahme). Polster sitzt über der Schulterachse.'),
    dict(id='arm',de='Arm (Oberarm bis Unterarm)',side='links',u=(1036,1560),mu=(1036,1475),
         sel=('center',(205,540)),fu=(1060,1460),fb=P('Profil-Rückenkante (Ellbogen/Unterarm)'),
         ff=A(49,SRC_ARM_FRONT),side_contour=False,joints=['schulter','ellbogen','handgelenk'],
         note='Über u1475 unter dem Polster verdeckt: Oberarm bis zur Schulterachse weiterführen (Annahme).'),
    dict(id='hand',de='Hand',side='links',u=(860,1036),mu=(860,1036),sel=('center',(400,560)),
         fu=(860,1036),fb=A(-44,'herkunft-r02.md: Hand f−44..+93 (Profil-Farbbild)'),
         ff=A(93,'herkunft-r02.md: Hand f−44..+93 (Profil-Farbbild)'),side_contour=False,
         joints=['handgelenk'],note='Handfläche zum Oberschenkel (innen), Fingerspitzen u≈860.'),
    dict(id='bein',de='Bein (Oberschenkel bis Unterschenkel)',side='links',u=(169,1060),mu=(169,975),
         sel=('center',(20,330)),fu=(169,975),fb=P('Profil A/B gemittelt'),ff=P('Profil A/B gemittelt'),
         side_contour=True,joints=['huefte','knie','knoechel'],
         note='Über u975 verdeckt (Becken): Oberschenkel bis zur Hüftachse weiterführen (Annahme).'),
    dict(id='fuss',de='Fuß',side='links',u=(0,169),mu=(0,169),sel=('center',(100,420)),
         fu=(0,169),fb=P('Profil A/B gemittelt'),ff=P('Profil A/B gemittelt'),side_contour=True,
         joints=['knoechel'],note='Front verbindlich (Zehen bis x361); Rücken zeigt schmalere Fersen (Konflikt 1).'),
]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def n(v):return f'{v:.2f}'.rstrip('0').rstrip('.') if isinstance(v,float) else str(v)


def pick(runs,sel):
    mode,(lo,hi)=sel;out=[]
    for a,b in runs:
        if mode=='clip' and b>lo and a<hi:out.append((max(a,lo),min(b,hi)))
        if mode=='center' and lo<=(a+b)/2<=hi:out.append((a,b))
    return (min(a for a,_ in out),max(b for _,b in out)) if out else None


def side_ext(row):
    """Profil A und B gemittelt (beide f vorn positiv; Kopfversatz ±6 mm, herkunft-r02.md Konflikt 2)."""
    ea,eb=[(r[0][0],r[-1][1]) if r else None for r in (row['profile-a'],row['profile-b'])]
    return ((ea[0]+eb[0])/2,(ea[1]+eb[1])/2) if ea and eb else None


def us(lo,hi):return range(lo-lo%STEP+(STEP if lo%STEP else 0),hi+1,STEP)


def measure_part(part,rows):
    front=[(u,*e) for u in us(*part['mu']) if (e:=pick(rows[u]['front'],part['sel']))]
    back=[(u,*e) for u in us(*part['mu']) if (e:=pick(rows[u]['back'],part['sel']))]
    side=[(u,*e) for u in us(*part['fu']) if (e:=side_ext(rows[u]))]
    x=(min(r[1] for r in front),max(r[2] for r in front))
    fb=part['fb']['value'] if part['fb']['kind']=='Annahme' else min(r[1] for r in side)
    ff=part['ff']['value'] if part['ff']['kind']=='Annahme' else max(r[2] for r in side)
    return dict(x=[float(round(x[0],1)),float(round(x[1],1))],f=[float(round(fb,1)),float(round(ff,1))],
                contour={'front':[[u,round(a,1),round(b,1)] for u,a,b in front],
                         'back':[[u,round(a,1),round(b,1)] for u,a,b in back],
                         'side':[[u,round(a,1),round(b,1)] for u,a,b in side] if part['side_contour'] else []})


def measure_joint(jid,rows,sign=1):
    j=JOINTS[jid];ext=[(u,e) for u in us(*j['win']) if (e:=pick(rows[u]['front'],j['sel']))]
    u_min,(a,b)=min(ext,key=lambda t:(t[1][1]-t[1][0],t[0]))
    if j['x']=='run':
        near=min(ext,key=lambda t:(abs(t[0]-j['u']),t[0]))[1]
        x,xsrc=(near[0]+near[1])/2,f"gemessen: Mitte des Front-Laufs bei u{j['u']}"
    else:x,xsrc=j['x']
    return dict(id=jid,de=j['de'],u=j['u'],f=j['f'][0],x=round(sign*x,1),diameter_mm=round(b-a,1),
                diameter_row_u=u_min,diameter_window_u=list(j['win']),
                sources={'u':'docs/herkunft-r02.md › Gelenkhöhen (verwendet)','f':j['f'][1],'x':xsrc,
                         'diameter':f"gemessen: schmalste Front-Breite u{j['win'][0]}..{j['win'][1]} ({j['dsrc']})"})


def joints_of(part,rows):
    out=[]
    for spec in part['joints']:
        jid,both=(spec,False) if isinstance(spec,str) else (spec[0],True)
        out.append(measure_joint(jid,rows))
        if both:out.append({**measure_joint(jid,rows,-1),'id':jid+'_r','de':JOINTS[jid]['de']+' rechts'})
    return out


def layout(m):
    """Gemeinsamer Maßstab je Blatt (Viertel-px/mm). Draufsicht stets unter der Front (x fluchtet).
    Reihe: Front|Seite|Rücken über der Draufsicht; Raster: Front|Seite über Draufsicht|Rücken.
    Gewählt wird die Anordnung mit dem größeren Maßstab (bei Gleichstand Reihe)."""
    (x0,x1),(fb,ff)=m['x'],m['f'];u0,u1=m['u']
    wf,ws,h1,h2=x1-x0+2*MARGIN,ff-fb+2*MARGIN,u1-u0+2*MARGIN,ff-fb+2*MARGIN
    left,label,gap,top,bottom,title=140,420,110,330,620,70
    ah=CANVAS-top-bottom-2*title-gap
    q=lambda v:math.floor(v*4)/4
    s_row=q(min((CANVAS-2*left-label-2*gap)/(2*wf+ws),ah/(h1+h2)))
    s_grid=q(min((CANVAS-2*left-label-gap)/(wf+max(ws,wf)),ah/(h1+max(h1,h2))))
    grid=s_grid>s_row;s=s_grid if grid else s_row
    used=((wf+max(ws,wf))*s+gap if grid else (2*wf+ws)*s+2*gap)+label;ox=left+(CANVAS-2*left-used)/2+label
    yr1=top+title;yr2=yr1+h1*s+gap+title;c2=ox+wf*s+gap
    cells={'front':(ox,yr1,wf,h1),'side':(c2,yr1,ws,h1),'top':(ox,yr2,wf,h2),
           'back':(c2,yr2,wf,h1) if grid else (c2+ws*s+gap,yr1,wf,h1)}
    # Abbildung mm → px: px = ox + (h − h0)·s, py = oy + (v0 − v)·s; h/v je Ansicht siehe VIEW_AXES.
    hr={'front':(x0-MARGIN,x1+MARGIN),'back':(-x1-MARGIN,-x0+MARGIN),'side':(-ff-MARGIN,-fb+MARGIN),'top':(x0-MARGIN,x1+MARGIN)}
    vr={'front':u1+MARGIN,'back':u1+MARGIN,'side':u1+MARGIN,'top':-fb+MARGIN}
    return s,{k:dict(ox=round(c[0],2),oy=round(c[1],2),w_px=round(c[2]*s,2),h_px=round(c[3]*s,2),
                     h0_mm=round(hr[k][0],2),v0_mm=round(vr[k],2)) for k,c in cells.items()}


VIEW_AXES={'front':'h=x (anatomisch links → Bild rechts), v=u','side':'h=−f (vorn → Bild links, Blick von links wie Profil B), v=u',
           'back':'h=−x (anatomisch links → Bild links), v=u','top':'h=x, v=−f (vorn → Bild unten)'}


def to_px(view,cells,s,h,v):
    c=cells[view];return c['ox']+(h-c['h0_mm'])*s,c['oy']+(c['v0_mm']-v)*s


def hv(view,f,u,x):
    return {'front':(x,u),'back':(-x,u),'side':(-f,u),'top':(x,-f)}[view]


def underlay_png(sheet,prov,view,c,s):
    """Ausschnitt des Masterblatts im selben mm-Raster: h=(px−x0)·k, u=(Boden−py)·k für alle drei Blattansichten."""
    k=prov['mm_per_pixel'];floor=prov['front_floor_px']
    key={'front':'front','back':'back','side':'profile-b'}[view];x0=prov['views'][key]['registration']['x0_px']
    h0,v0=c['h0_mm'],c['v0_mm'];h1,v1=h0+c['w_px']/s,v0-c['h_px']/s
    px0,px1=math.floor(x0+h0/k),math.ceil(x0+h1/k);py0,py1=math.floor(floor-v0/k),math.ceil(floor-v1/k)
    px0,py0=max(px0,0),max(py0,0);px1,py1=min(px1,sheet.width),min(py1,sheet.height)
    buf=io.BytesIO();sheet.crop((px0,py0,px1,py1)).save(buf,'PNG',compress_level=9)
    return dict(h=(px0-x0)*k,v=(floor-py0)*k,w=(px1-px0)*k,hgt=(py1-py0)*k,png=buf.getvalue(),
                crop_px=[px0,py0,px1,py1],source=f'r02-sheet-9803.png Ansicht {key}')


def text(x,y,t,size=34,anchor='start',weight='normal',fill=TEXT_C):
    return (f'<text x="{n(round(x,2))}" y="{n(round(y,2))}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{escape(t)}</text>')


def build_svg(part,m,joints,skins,s,cells,unders):
    (x0,x1),(fb,ff)=m['x'],m['f'];u0,u1=m['u']
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{CANVAS}" height="{CANVAS}" '
       f'viewBox="0 0 {CANVAS} {CANVAS}">',f'<title>R02 Frost Schablone {part["id"]}</title>',
       f'<rect id="background" width="{CANVAS}" height="{CANVAS}" fill="{BG}"/>']
    o.append('<defs>'+''.join(f'<clipPath id="clip-{v}"><rect x="{n(c["ox"])}" y="{n(c["oy"])}" width="{n(c["w_px"])}" '
                               f'height="{n(c["h_px"])}"/></clipPath>' for v,c in cells.items())+'</defs>')
    layer=lambda name:f'<g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}">'
    # underlay
    o.append(layer('underlay')+'<g opacity="0.35">')
    for view,u in unders.items():
        c=cells[view];cid=f'clip-{view}'
        px,py=to_px(view,cells,s,u['h'],u['v'])
        o.append(f'<image clip-path="url(#{cid})" x="{n(round(px,2))}" y="{n(round(py,2))}" width="{n(round(u["w"]*s,2))}" '
                 f'height="{n(round(u["hgt"]*s,2))}" preserveAspectRatio="none" '
                 f'xlink:href="data:image/png;base64,{base64.b64encode(u["png"]).decode()}"/>')
    o.append('</g></g>')
    # frame
    o.append(layer('frame'))
    side_txt={'mitte':'Mittelteil','links':'linke Seite (rechts = gespiegelt an x=0)'}[part['side']]
    o.append(text(140,120,f'R02 „Frost“ · Teil-Schablone · {part["de"]}',72,weight='bold'))
    o.append(text(140,200,f'{side_txt} · u {u0}–{u1} mm · Figurhöhe 2000 mm · Maßstab 1 mm = {n(s)} px (4000-px-Blatt)',40))
    o.append(text(140,262,part['note'],34))
    titles={'front':'FRONT','side':'SEITE (von links)','back':'RÜCKEN','top':'DRAUFSICHT (vorn = unten)'}
    rects={'front':((x0,u1),(x1,u0)),'back':((-x1,u1),(-x0,u0)),'side':((-ff,u1),(-fb,u0)),'top':((x0,-fb),(x1,-ff))}
    for view,c in cells.items():
        o.append(text(c['ox'],c['oy']-22,titles[view],40,weight='bold'))
        (ha,va),(hb,vb)=rects[view];pa,pb=to_px(view,cells,s,ha,va),to_px(view,cells,s,hb,vb)
        o.append(f'<rect x="{n(round(pa[0],2))}" y="{n(round(pa[1],2))}" width="{n(round(pb[0]-pa[0],2))}" '
                 f'height="{n(round(pb[1]-pa[1],2))}" fill="none" stroke="{FRAME_C}" stroke-width="5"/>')
        wmm,hmm=abs(hb-ha),abs(vb-va)
        o.append(text((pa[0]+pb[0])/2,pb[1]+44,f'{n(round(wmm,1))} mm',30,'middle',fill=FRAME_C))
        o.append(text(pb[0]+12,(pa[1]+pb[1])/2,f'{n(round(hmm,1))}',30,fill=FRAME_C))
    for view,key in (('front','front'),('back','back'),('side','side')):
        rows=m['contour'][key]
        if not rows:continue
        sg=-1 if view=='back' else 1
        if view=='side':pts=[to_px(view,cells,s,-b,u) for u,a,b in rows]+[to_px(view,cells,s,-a,u) for u,a,b in reversed(rows)]
        else:pts=[to_px(view,cells,s,sg*a,u) for u,a,b in rows]+[to_px(view,cells,s,sg*b,u) for u,a,b in reversed(rows)]
        o.append(f'<polygon points="{" ".join(f"{n(round(x,1))},{n(round(y,1))}" for x,y in pts)}" fill="none" '
                 f'stroke="{FRAME_C}" stroke-width="2.5" stroke-dasharray="14 10"/>')
    # Maßleiste
    bar=100 if s*200>1400 else 200;bx,by=CANVAS-140-bar*s,CANVAS-130
    o.append(f'<rect x="{n(round(bx,2))}" y="{by}" width="{n(round(bar*s,2))}" height="18" fill="{TEXT_C}"/>')
    for t in range(0,bar+1,10):
        tx=round(bx+t*s,2);hh=40 if t%50==0 else 24
        o.append(f'<line x1="{n(tx)}" y1="{by}" x2="{n(tx)}" y2="{by-hh}" stroke="{TEXT_C}" stroke-width="3"/>')
    o.append(text(bx,by-52,'0',30,'middle'));o.append(text(bx+bar*s,by-52,f'{bar} mm',30,'middle'))
    o.append(text(bx+bar*s,by+62,'gelb = Hüllrahmen/Kontur (Masterblatt) · magenta = Gelenk, Kreis = Anschluss-Ø',28,'end'))
    o.append('</g>')
    # markers
    o.append(layer('markers'))
    rows={}
    for v in ('front','side','back'):rows.setdefault(cells[v]['oy'],[]).append(cells[v])
    marks={v:[] for v in cells}
    for j in joints:
        if not j['id'].endswith('_r'):
            for oy,cs in rows.items():
                xa,xb=min(c['ox'] for c in cs)-40,max(c['ox']+c['w_px'] for c in cs)
                _,py=to_px('front' if cs[0] is cells['front'] else 'back',cells,s,0,j['u'])
                o.append(f'<line x1="{n(round(xa,2))}" y1="{n(round(py,2))}" x2="{n(round(xb,2))}" y2="{n(round(py,2))}" '
                         f'stroke="{MARK_C}" stroke-width="3" stroke-dasharray="24 12"/>')
                if cells['front'] in cs:
                    o.append(text(xa-12,py-8,f'{j["de"]} u{j["u"]}',34,'end',weight='bold',fill=MARK_C))
                    o.append(text(xa-12,py+34,f'Ø {n(j["diameter_mm"])} mm',30,'end',fill=MARK_C))
                else:o.append(text(xa+8,py-10,f'{j["de"]} u{j["u"]}',30,weight='bold',fill=MARK_C))
        for view in cells:
            # Anschlussquerschnitt liegt waagrecht: Draufsicht Kreis, sonst Balken der Länge Ø mit Endstrichen.
            px,py=to_px(view,cells,s,*hv(view,j['f'],j['u'],j['x']));r=round(j['diameter_mm']/2*s,2)
            if view=='top':
                marks[view].append(f'<circle cx="{n(round(px,2))}" cy="{n(round(py,2))}" r="{n(r)}" fill="none" stroke="{MARK_C}" stroke-width="4"/>')
            else:
                marks[view].append(f'<path d="M{n(round(px-r,2))} {n(round(py,2))}h{n(round(2*r,2))}M{n(round(px-r,2))} {n(round(py-18,2))}v36'
                         f'M{n(round(px+r,2))} {n(round(py-18,2))}v36" stroke="{MARK_C}" stroke-width="7" fill="none"/>')
            marks[view].append(f'<path d="M{n(round(px-22,2))} {n(round(py,2))}h44M{n(round(px,2))} {n(round(py-22,2))}v44" stroke="{MARK_C}" stroke-width="5"/>')
    for view,items in marks.items():o.append(f'<g clip-path="url(#clip-{view})">'+''.join(items)+'</g>')
    o.append('</g>')
    # swatches
    o.append(layer('swatches'))
    sw,gap,y0=420,36,CANVAS-520
    for i,role in enumerate(ROLES):
        r=skins['roles'][role];x=140+i*(sw+gap)
        o.append(f'<rect id="swatch-{role}" x="{x}" y="{y0}" width="{sw}" height="150" fill="{r["color"]}" stroke="{TEXT_C}" stroke-width="3"/>')
        o.append(text(x,y0+196,role,32,weight='bold'));o.append(text(x,y0+236,r['color'],30))
    o.append('</g>')
    o.append('</svg>\n')
    return '\n'.join(o).encode()


def rsvg(svg_bytes,out,hide_underlay=False):
    data=svg_bytes.replace(b'<g opacity="0.35">',b'<g opacity="0.35" display="none">',1) if hide_underlay else svg_bytes
    subprocess.run(['rsvg-convert','-w',str(CANVAS),'-h',str(CANVAS),'-f','png','-o',str(out)],input=data,check=True)


def contact(out,ids):
    tile,pad,lab=900,30,60;cols=4;rows=math.ceil(len(ids)/cols)
    sheet=Image.new('RGB',(cols*(tile+pad)+pad,rows*(tile+pad+lab)+pad),(128,128,128));d=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype(str(ROOT/'docs/fonts/DejaVuSans.ttf'),36)
    except OSError:font=ImageFont.load_default()
    for i,pid in enumerate(ids):
        x,y=pad+(i%cols)*(tile+pad),pad+(i//cols)*(tile+pad+lab)
        with Image.open(out/f'{pid}.png') as im:sheet.paste(im.convert('RGB').resize((tile,tile),Image.LANCZOS),(x,y+lab))
        d.text((x,y+8),pid,fill=(17,17,17),font=font)
    sheet.save(out/'contact.png',compress_level=9)


def build_part(part,rows,sheet,prov,skins):
    m=measure_part(part,rows);m['u']=list(part['u']);joints=joints_of(part,rows)
    s,cells=layout(m);unders={v:underlay_png(sheet,prov,v,cells[v],s) for v in ('front','side','back')}
    return build_svg(part,m,joints,skins,s,cells,unders),m,joints,s,cells,unders


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=OUT);ap.add_argument('--only')
    ap.add_argument('--force',action='store_true');a=ap.parse_args(argv)
    prov_path=REF/'mask-provenance.json';prov=json.loads(prov_path.read_bytes())
    if sha(SHEET)!=prov['sheet_png_sha256']:raise SystemExit('r02-sheet-9803.png weicht von mask-provenance.json ab')
    skins=tomllib.loads((ROOT/'skins.toml').read_text())
    rows=r02_measure.measure(STEP)['rows'];sheet=Image.open(SHEET).convert('RGBA')
    rsvg_ver=subprocess.run(['rsvg-convert','--version'],capture_output=True,text=True,check=True).stdout.split('\n')[0]
    a.out.mkdir(parents=True,exist_ok=True);manifest_path=a.out/'manifest.json'
    old=json.loads(manifest_path.read_text())['parts'] if manifest_path.exists() else {}
    only=set(a.only.split(',')) if a.only else None;parts={}
    for part in PARTS:
        pid=part['id']
        if only and pid not in only:
            if pid in old:parts[pid]=old[pid]
            continue
        svg,m,joints,s,cells,unders=build_part(part,rows,sheet,prov,skins);files={'svg':f'{pid}.svg','png':f'{pid}.png','png_clean':f'{pid}-ohne-unterlage.png'}
        svg_path=a.out/files['svg'];changed=not svg_path.exists() or svg_path.read_bytes()!=svg
        if changed:svg_path.write_bytes(svg)
        for key,hide in (('png',False),('png_clean',True)):
            if a.force or changed or not (a.out/files[key]).exists():rsvg(svg,a.out/files[key],hide)
        parts[pid]=dict(id=pid,de=part['de'],side=part['side'],mirror_right=part['side']=='links',note=part['note'],
                        u_mm=m['u'],frame_mm={'front':{'x':m['x'],'u':m['u']},'side':{'f':m['f'],'u':m['u']},
                                              'back':{'x':m['x'],'u':m['u'],'note':'gespiegelter Front-Rahmen (Front verbindlich)'},
                                              'top':{'x':m['x'],'f':m['f']}},
                        frame_sources={'x':f"gemessen: Front-Läufe u{part['mu'][0]}..{part['mu'][1]} ({part['sel'][0]} {list(part['sel'][1])})",
                                       'u':'Gelenkmarken/Teilgrenzen (herkunft-r02.md)','f_back':part['fb'],'f_front':part['ff'],
                                       'f_rows_u':list(part['fu'])},
                        joints=joints,scale_px_per_mm=s,views={k:{**c,'axes':VIEW_AXES[k]} for k,c in cells.items()},
                        underlay={v:{'crop_px':u['crop_px'],'source':u['source'],'opacity':0.35} for v,u in unders.items()},
                        contour_mm=m['contour'],files={k:{'name':f,'sha256':sha(a.out/f)} for k,f in files.items()})
        print(f"{pid:16s} 1 mm = {n(s)} px  x {m['x']}  f {m['f']}  u {m['u']}  {'neu' if changed else 'unverändert'}")
    contact(a.out,[p['id'] for p in PARTS if (a.out/f"{p['id']}.png").exists()])
    tool=Path(__file__).resolve()
    manifest={'robot':'R02','format':'cubeescape-formgenv2/r02-part-templates','version':1,'canvas_px':CANVAS,
              'units':'mm; u über Boden, f vorn positiv (f=0 Kniescheibenmitte), x anatomisch links positiv',
              'height_mm':prov['height_mm'],'mm_per_sheet_pixel':prov['mm_per_pixel'],
              'pixel_mapping':'px = ox + (h − h0_mm)·s, py = oy + (v0_mm − v)·s je Ansicht (views.*)',
              'rules':'docs/zeichnungsvorgabe-teile.md','renderer':rsvg_ver,
              'sources':{'r02-sheet-9803.png':prov['sheet_png_sha256'],'r02-blauweiss.svg':prov['svg_sha256'],
                         'mask-provenance.json':sha(prov_path),'mask_revision':prov['revision'],
                         'masks':{v:r['mask_sha256'] for v,r in prov['views'].items()},
                         'skins.toml':sha(ROOT/'skins.toml'),'tools/r02_measure.py':sha(ROOT/'tools/r02_measure.py'),
                         'docs/herkunft-r02.md':sha(ROOT/'docs/herkunft-r02.md'),'tools/r02_part_templates.py':sha(tool)},
              'swatches':{r:skins['roles'][r]['color'] for r in ROLES},
              'parts':{p['id']:parts[p['id']] for p in PARTS if p['id'] in parts},
              'contact':{'name':'contact.png','sha256':sha(a.out/'contact.png')}}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n')
    print(f'{len(parts)} Schablonen → {a.out}')


if __name__=='__main__':main()
