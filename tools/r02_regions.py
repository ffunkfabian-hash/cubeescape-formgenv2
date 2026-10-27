"""R02-Farbregionen: Plattenumrisse aus dem weiß/blauen Blatt (gemessen).

Jede Ansicht wird nach Farbklassen der Vorlage getrennt (Konturschwarz,
Weiß, Grau, Kristall, Schiefer, Unterbau). Die schwarzen Zeichenlinien
trennen die Platten; jede zusammenhängende Fläche einer Klasse wird ein
Polygon in mm (Front/Rücken: x anatomisch links +, Profil: f vorn +, u über
Boden). Ergebnis ist ein generiertes Python-Modul, das die Baugruppe
importiert (keine Laufzeitabhängigkeit von refs-r02).
Aufruf: python tools/r02_regions.py arms
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import manifold3d as mf

ROOT=Path(__file__).resolve().parents[1]
REF=Path.home()/'Library/Caches/CubeEscapeFormgen/refs-r02'
SHEET_SHA='97ccf96fe77e2daa9dd51a640624d0b1a3df43588294a65bdcd2b9e8b5077350'
# Häufigste Blattfarben je Klasse (gemessen im Armbereich, 6er-Quantisierung).
CLASSES={'shell':['#E7EDED','#E1EDED','#E1E7ED','#C3C9D5'],'gray':['#A5ABB7'],
         'crystal':['#B1E7FF','#A5DBF9','#7BB7ED','#7BB7E7'],'slate':['#515D6F'],
         'frame':['#272733','#333945','#212733','#1B2127']}
ROLES={'shell':'frost_shell','gray':'frost_gray','crystal':'frost_crystal','slate':'frost_slate'}
STEP=2            # Halbe Blattauflösung: 1 px = 1,09 mm
MIN_AREA_MM2=60   # kleinere Flächen sind Lichter, Schrauben, Facettenlinien
SIMPLIFY_MM=.8
# Bereiche je Baugruppe: Ansicht -> (u0, u1, a0, a1) in mm; linke Körperseite.
ZONES={'arms':{'front':(850,1765,203,545),'back':(850,1765,203,545),'profile-b':(850,1765,-200,200)}}


def _hex(c):return np.array([int(c[i:i+2],16) for i in (1,3,5)])


def classify(rgb):
    names=[];cols=[]
    for name,colors in CLASSES.items():
        for c in colors:names.append(name);cols.append(_hex(c))
    cols=np.array(cols,dtype=float)
    d=((rgb[...,None,:].astype(float)-cols[None,None])**2).sum(-1)
    best=d.argmin(-1);ok=d.min(-1)<30**2
    return {n:ok&np.isin(best,[i for i,m in enumerate(names) if m==n]) for n in CLASSES}


def polygons(mask,to_mm):
    """Union of pixel row runs as exact CrossSection, simplified, in mm."""
    rects=[]
    for r in range(mask.shape[0]):
        row=mask[r];edges=np.flatnonzero(np.diff(np.r_[0,row.astype(np.int8),0]))
        for a,b in zip(edges[::2],edges[1::2]):
            (xa,ya),(xb,yb)=to_mm(a,r),to_mm(b,r+1)
            xa,xb=sorted((xa,xb));ya,yb=sorted((ya,yb))
            # Gegen den Uhrzeigersinn, sonst gilt das Rechteck als Loch.
            rects.append(mf.CrossSection([[(xa,ya),(xb,ya),(xb,yb),(xa,yb)]]))
    if not rects:return []
    cs=mf.CrossSection.batch_boolean(rects,mf.OpType.Add).simplify(SIMPLIFY_MM)
    return [[[round(float(x),2),round(float(y),2)] for x,y in poly] for poly in cs.to_polygons()]


def extract(group):
    sheet=REF/'r02-sheet-9803.png'
    if hashlib.sha256(sheet.read_bytes()).hexdigest()!=SHEET_SHA:raise ValueError('Blattraster verändert')
    Image.MAX_IMAGE_PIXELS=None
    rgba=np.asarray(Image.open(sheet));prov=json.loads((REF/'mask-provenance.json').read_bytes())
    k=prov['mm_per_pixel'];floor=prov['front_floor_px'];result={}
    for view,(u0,u1,a0,a1) in ZONES[group].items():
        rec=prov['views'][view];x0=rec['registration']['x0_px'];sign={'front':1,'back':-1,'profile-a':1,'profile-b':-1}[view]
        c0,c1=sorted((x0+sign*a0/k,x0+sign*a1/k));c0=int(c0)//STEP*STEP;c1=int(c1+STEP)
        r0=int(floor-u1/k)//STEP*STEP;r1=int(floor-u0/k)+STEP
        win=rgba[r0:r1:STEP,c0:c1:STEP];rgb=win[...,:3];opaque=win[...,3]>127
        classes=classify(rgb);regions=[]
        to_mm=lambda c,r:((c0+c*STEP-x0)*sign*k,(floor-(r0+r*STEP))*k)
        for name,mask in classes.items():
            if name not in ROLES:continue
            # Dünne Facettenlinien anderer Farbe schließen, Konturschwarz trennt weiter.
            mask=ndimage.binary_closing(mask&opaque,iterations=1)&opaque
            lab,n=ndimage.label(mask);sizes=np.bincount(lab.ravel())*(STEP*k)**2
            for i in range(1,n+1):
                if sizes[i]<MIN_AREA_MM2:continue
                polys=polygons(lab==i,to_mm)
                if polys:regions.append({'class':name,'role':ROLES[name],'area_mm2':round(float(sizes[i]),1),'contours':polys})
        regions.sort(key=lambda r:(-r['area_mm2'],r['class']))
        result[view]=regions
    return result


def write(group,data):
    target=ROOT/f'formgen/models/figures/r02_parts/{group}_regions.py'
    body=json.dumps(data,separators=(',',':'))
    target.write_text(f'"""Generiert von tools/r02_regions.py {group} – nicht von Hand ändern.\n\n'
                      f'Gemessen: Farbregionen des weiß/blauen Blatts (Raster SHA {SHEET_SHA[:12]}…, Schritt {STEP} px,\n'
                      f'Mindestfläche {MIN_AREA_MM2} mm², Vereinfachung {SIMPLIFY_MM} mm). Konturen in mm: Front/Rücken (x,u), Profil (f,u).\n"""\n'
                      f'REGIONS = {body}\n')
    return target


if __name__=='__main__':
    group=sys.argv[1] if len(sys.argv)>1 else 'arms';data=extract(group);t=write(group,data)
    print(t.name,{v:len(r) for v,r in data.items()},round(t.stat().st_size/1024),'KB')
