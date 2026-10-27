"""R02-Konturmessung: belegte Läufe je Blattzeile in mm (gemessen, mask revision 1).

Front/Rücken: x in mm, anatomisch links positiv (Front: Bild rechts; Rücken: Bild links).
Profile: f in mm, vorn positiv (A blickt nach rechts, B nach links). u über Frontboden.
Keine Modellanpassung: liefert nur Stützpunkte für Herkunft und Module.
Aufruf: python tools/r02_measure.py [--step 10] [--out datei.json]
"""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
REF=Path.home()/'Library/Caches/CubeEscapeFormgen/refs-r02'

def load():
    prov=json.loads((REF/'mask-provenance.json').read_bytes());k=prov['mm_per_pixel'];floor=prov['front_floor_px']
    views={}
    for view,r in prov['views'].items():
        m=np.asarray(Image.open(REF/f'ortho-{view}-mask.png'))>127
        x0=r['registration']['x0_px']-r['window_x0_px']
        # Pixelmitte: Spalte c deckt [c,c+1); Kante links=c, rechts=c+1.
        sign={'front':1,'back':-1,'profile-a':1,'profile-b':-1}[view]
        views[view]=(m,x0,sign)
    return prov,k,floor,views

def runs(row,x0,sign,k):
    edges=np.flatnonzero(np.diff(np.r_[0,row.astype(np.int8),0]))
    out=[]
    for a,b in zip(edges[::2],edges[1::2]):
        lo,hi=sorted(((a-x0)*sign*k,(b-x0)*sign*k));out.append([round(lo,1),round(hi,1)])
    return sorted(out)

def measure(step=10):
    prov,k,floor,views=load();rows={}
    for u in range(0,2001,step):
        y=int(floor-u/k-.5)
        rows[u]={v:runs(m[y],x0,s,k) if 0<=y<m.shape[0] else [] for v,(m,x0,s) in views.items()}
    return {'mm_per_pixel':k,'front_floor_px':floor,'rows':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--step',type=int,default=10);p.add_argument('--out',type=Path);a=p.parse_args()
    d=measure(a.step)
    if a.out:a.out.write_text(json.dumps(d,indent=0)+'\n')
    else:
        for u,r in d['rows'].items():print(u,json.dumps(r))
