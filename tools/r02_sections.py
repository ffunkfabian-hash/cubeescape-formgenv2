"""R02-Querschnitte: Ringform je Segment und Zeile aus dem Meshy-9-Teile-Netz (gemessen an KI-Referenz).

Das Netz (`refs-r02/meshy/r02-meshy-split9.glb`, Nutzerlieferung 27.10.2026) liegt an der Blattposition.
Registrierung (Übergabe R02): Gesamthöhe → 2000 mm, u = y·s, x = x·s (anatomisch links +),
f = (z − z_mitte)·s + 34 mm (Mittel aus Profil A +32 und B +36). Je Segment und Zeile wird der ebene
Schnitt der zugeordneten Netzteile genommen, auf seine Hüllbox normiert und von der Boxmitte aus
in N Richtungen abgetastet (äußerster Treffer je Strahl). Gespeichert wird nur die normierte Form
(−1..1 in f und x); die Modulzeilen passen sie affin auf die gemessenen Blattmaße ein, damit der
Umriss beim Blatt bleibt. Ergebnis ist ein generiertes Modul je Baugruppe; der Bau liest das GLB nie.
Aufruf: python tools/r02_sections.py arms
"""
import hashlib,json,math,struct,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
GLB=Path.home()/'Library/Caches/CubeEscapeFormgen/refs-r02/meshy/r02-meshy-split9.glb'
GLB_SHA='29c8dd04a633ebba1cd82278f84f6ab4b2bbbda9f0f363f30df0e7146516e896'
HEIGHT=2000;F_OFFSET=34;STEP=5;RAYS=32
# Segmente der linken Körperseite: Netzteile, u-Bereich (mm), optional x-Bereich.
# Teile split9: 0/3 Bein r/l, 1 Becken, 2 Kopf, 4+7 Polster l, 5+6 Polster r, 8/9 Arm l/r, 10 Rumpf.
SEGMENTS={'arms':{'shoulder_pad':dict(parts=[4,7],u=(1465,1740)),
                  'upper_arm':dict(parts=[8],u=(1325,1500)),
                  'elbow':dict(parts=[8],u=(1250,1340)),
                  'forearm':dict(parts=[8],u=(1030,1265)),
                  'hand_palm':dict(parts=[8],u=(935,1045)),
                  'hand_fingers':dict(parts=[8],u=(855,948),x=(450,600)),
                  'hand_thumb':dict(parts=[8],u=(900,948),x=(380,450))}}


def read_glb(path):
    """Minimal glTF-2.0-Binärleser: POSITION (float32) und Indizes je Knoten."""
    data=path.read_bytes()
    if data[:4]!=b'glTF':raise ValueError('kein GLB')
    n=struct.unpack('<I',data[12:16])[0];js=json.loads(data[20:20+n]);off=20+n
    blob=data[off+8:off+8+struct.unpack('<I',data[off:off+4])[0]]
    def accessor(i):
        a=js['accessors'][i];view=js['bufferViews'][a['bufferView']]
        dtype={5126:np.float32,5125:np.uint32,5123:np.uint16}[a['componentType']]
        width={'SCALAR':1,'VEC3':3}[a['type']];start=view.get('byteOffset',0)+a.get('byteOffset',0)
        if view.get('byteStride',width*np.dtype(dtype).itemsize)!=width*np.dtype(dtype).itemsize:raise ValueError('verschränkte Puffer')
        return np.frombuffer(blob,dtype,count=a['count']*width,offset=start).reshape(a['count'],width)
    parts=[]
    for node in js['nodes']:
        prim=js['meshes'][node['mesh']]['primitives']
        if len(prim)!=1:raise ValueError('ein Primitiv je Teil erwartet')
        parts.append((accessor(prim[0]['attributes']['POSITION']).astype(float),accessor(prim[0]['indices']).reshape(-1,3).astype(np.int64)))
    return parts


def registered(parts):
    allv=np.vstack([v for v,_ in parts]);y0=allv[:,1].min();s=HEIGHT/(allv[:,1].max()-y0)
    zc=(allv[:,2].min()+allv[:,2].max())/2
    # (f,u,x) in mm
    return [(np.c_[(v[:,2]-zc)*s+F_OFFSET,(v[:,1]-y0)*s,v[:,0]*s],f) for v,f in parts],dict(scale=s,y0=float(y0),z_center=float(zc))


def section(points,faces,u):
    """Schnittstrecken (m,2,2) in (f,x) der Ebene u."""
    tri=points[faces];d=tri[:,:,1]-u;above=d>0
    tri,d=tri[above.any(1)&~above.all(1)],d[above.any(1)&~above.all(1)]
    out=[]
    for i,j in ((0,1),(1,2),(2,0)):
        cut=(d[:,i]>0)!=(d[:,j]>0);t=np.where(cut,d[:,i]/np.where(cut,d[:,i]-d[:,j],1),0)
        out.append((tri[:,i]+t[:,None]*(tri[:,j]-tri[:,i]),cut))
    pts=[];
    for k in range(len(tri)):
        p=[o[0][k][[0,2]] for o in out if o[1][k]]
        if len(p)==2:pts.append(p)
    return np.asarray(pts).reshape(-1,2,2)


def _hull(points):
    """Konvexe Hülle (monotone Kette) als geschlossener Streckenzug (m,2,2)."""
    pts=sorted(set(map(tuple,np.round(points,9))))
    def half(seq):
        out=[]
        for p in seq:
            while len(out)>1 and (out[-1][0]-out[-2][0])*(p[1]-out[-2][1])-(out[-1][1]-out[-2][1])*(p[0]-out[-2][0])<=0:out.pop()
            out.append(p)
        return out[:-1]
    h=np.asarray(half(pts)+half(pts[::-1]));return np.stack([h,np.roll(h,-1,0)],1)


def _cast(dirs,segments):
    p=segments[:,0];e=segments[:,1]-p
    # o + t·d = p + s·e  →  t·d − s·e = p
    det=dirs[:,None,0]*(-e[None,:,1])-dirs[:,None,1]*(-e[None,:,0])
    ok=np.abs(det)>1e-12;det=np.where(ok,det,1)
    t=(p[None,:,0]*(-e[None,:,1])-p[None,:,1]*(-e[None,:,0]))/det
    s=(dirs[:,None,0]*p[None,:,1]-dirs[:,None,1]*p[None,:,0])/det
    return np.where(ok&(t>0)&(s>=0)&(s<=1),t,0).max(1)


def ring(segments,rays=RAYS):
    """Äußerster Strahltreffer je Richtung in boxnormierten (f,x); Ergebnis auf −1..1 normiert.

    Richtungen ohne Treffer (offene Schalen, getrennte Fingerglieder) schließt die konvexe Hülle.
    """
    lo,hi=segments.reshape(-1,2).min(0),segments.reshape(-1,2).max(0);c=(lo+hi)/2;h=np.maximum((hi-lo)/2,1e-9)
    seg=(segments-c)/h
    theta=2*math.pi*np.arange(rays)/rays;dirs=np.c_[np.cos(theta),np.sin(theta)]   # (f,x): 0 = vorn, π/2 = außen (+x)
    r=_cast(dirs,seg);r=np.where(r>0,r,_cast(dirs,_hull(seg.reshape(-1,2))))
    if np.any(r<=0):raise ValueError('Strahl ohne Treffer')
    pts=dirs*r[:,None];lo,hi=pts.min(0),pts.max(0);c=(lo+hi)/2;h=(hi-lo)/2
    # Strahlursprung (Sternmittelpunkt) mitliefern: Kerne werden radial dazu eingerückt.
    return (pts-c)/h,-c/h


def measure(group):
    if hashlib.sha256(GLB.read_bytes()).hexdigest()!=GLB_SHA:raise ValueError('Meshy-Netz verändert')
    parts,reg=registered(read_glb(GLB));result={}
    for name,seg in SEGMENTS[group].items():
        rows=[];u0,u1=seg['u']
        for u in range(u0,u1+1,STEP):
            segs=np.concatenate([section(*parts[i],u+.5) for i in seg['parts']]).reshape(-1,2,2)
            if 'x' in seg:
                mid=segs.mean(1)[:,1];segs=segs[(mid>=seg['x'][0])&(mid<=seg['x'][1])]
            if len(segs)<8:continue
            shape,origin=ring(segs)
            rows.append([u,[round(float(v),3) for v in shape.ravel()],[round(float(v),3) for v in origin]])
        result[name]=rows
    return result,reg


def write(group,data,reg):
    target=ROOT/f'formgen/models/figures/r02_parts/{group}_sections.py'
    body=json.dumps(data,separators=(',',':'))
    target.write_text(f'"""Generiert von tools/r02_sections.py {group} – nicht von Hand ändern.\n\n'
                      f'Gemessen an KI-Referenz, eingepasst auf das Blatt: Meshy-Netz refs-r02/meshy/r02-meshy-split9.glb\n'
                      f'(SHA {GLB_SHA[:12]}…, Nutzerlieferung 27.10.2026), Höhe → {HEIGHT} mm, f-Versatz +{F_OFFSET} mm.\n'
                      f'Je Segment Zeilen [u, [f0, x0, f1, x1, …], [f, x] Strahlursprung]: {RAYS} Strahlen ab vorn (0) über außen (+x),\n'
                      f'Form auf −1..1 normiert; Maße liefern die Blattzeilen des Moduls. KI ist optional: der Bau liest das Netz nie.\n"""\n'
                      f'SOURCE = {json.dumps(dict(file="refs-r02/meshy/r02-meshy-split9.glb",sha256=GLB_SHA,height_mm=HEIGHT,f_offset_mm=F_OFFSET,step_mm=STEP,rays=RAYS,scale=round(reg["scale"],6)))}\n'
                      f'SECTIONS = {body}\n')
    return target


if __name__=='__main__':
    group=sys.argv[1] if len(sys.argv)>1 else 'arms';data,reg=measure(group);t=write(group,data,reg)
    print(t.name,{k:len(v) for k,v in data.items()},round(t.stat().st_size/1024),'KB')
