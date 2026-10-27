"""R02-Teilbild → deterministische, maßhaltige Silhouettenhülle (ohne Meshy).

Eingabe ist eine Ablage von tools/r02_part_check.py (source.png, record.json mit quadranten_px) und das Schablonen-Manifest
(frame_mm, joints, contour_mm). Je Quadrant: Vordergrund gegen den Grund (gleiche Regel wie r02_part_check), Löcher füllen,
größte Komponente → Polygon (Zeilenläufe vereinigt, vereinfacht mit TOL_MM) → anisotrop auf den Rahmen der Ansicht skaliert.
Front (x,u) wird entlang f, Seite (f,u) entlang x und Draufsicht (x,f) entlang u extrudiert; die Hülle ist der Schnitt
(wie prism2 in docs/modellsprache.md, um die Draufsicht erweitert). Die Rückansicht baut nicht mit, sie ist die Gegenprobe.

Ablage: <ablage>/hull/ (andere Parameter: hull-<schlüssel8>/) mit hull.glb, hull.obj, hull.json, contact.png.
Achsen: intern Blender-mm (X=x anatomisch links, Y=−f, Z=u); GLB/OBJ in Metern Y-oben (x,u,f) wie der Blender-Import erwartet.
Ohne --force wird nur gebaut, wenn Eingaben, Parameter oder Werkzeugversion sich geändert haben. Zweiter Lauf bytegleich.

Aufruf: python tools/r02_part_hull.py ABLAGE [--tol-mm 0.5] [--views front,side,top] [--force]
        (ABLAGE z. B. refs-r02/part-generations/kopf/a-blatt/4fb623f7ab66)
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import manifold3d as mf
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
from tools import r02_part_check as pc
from tools import r02_part_templates as pt

VERSION=1
TOL_MM=0.5  # Annahme: Vereinfachungstoleranz; < ½ Bildpixel (≈0,22 mm bei 2,3 px/mm) ist Rauschen, > 1 mm glättet Fasen weg
PAD=2.0  # mm Überstand der Extrusionen über den Rahmen, damit der Schnitt keine koplanaren Deckflächen trifft
SS=4  # Überabtastung beim Rastern der Hüllprojektionen
BUILD_VIEWS=('front','side','top')
MODI=('schnitt','loft')  # schnitt: reine Silhouettenhülle; loft: zusätzlich Draufsicht je Höhe auf Front/Seite skaliert (rund statt Grat)
LOFT_STEP=2.0  # mm Schichtabstand des Lofts (Annahme)
# Bildachsen je Ansicht: (Achse, Richtung) für Bildspalte und Bildzeile; Achsen intern X=x, Y=−f, Z=u (Blender-mm)
VIEWS={'front':(('X',1),('Z',-1)),'side':(('Y',1),('Z',-1)),'top':(('X',1),('Y',-1)),'back':(('X',-1),('Z',-1))}
DEPTH={'front':'Y','side':'X','top':'Z','back':'Y'}  # Projektionsrichtung
AX='XYZ'


def sha(b):return hashlib.sha256(b).hexdigest()


def ranges(part):
    (x0,x1),(f0,f1),(u0,u1)=part['frame_mm']['front']['x'],part['frame_mm']['side']['f'],part['u_mm']
    return {'X':(x0,x1),'Y':(-f1,-f0),'Z':(u0,u1)}


def view_map(view,box,part):
    """Bildpixel (Spalte, Zeile) relativ zur Quadrantenhülle → (a,b) in mm der Ansichtsebene, anisotrop auf den Rahmen."""
    R=ranges(part);(ha,hd),(va,vd)=VIEWS[view];bw,bh=box[2]-box[0],box[3]-box[1]
    def axis(lo,hi,d,n):return (lo,(hi-lo)/n) if d>0 else (hi,-(hi-lo)/n)
    return (ha,va),axis(*R[ha],hd,bw),axis(*R[va],vd,bh)


def silhouette(rgb,box):
    """Vordergrundmaske im Quadranten: Abstand > 40 zur Eckfarbe (wie r02_part_check), Löcher gefüllt, größte Komponente."""
    a=rgb.astype(int);fg=np.abs(a-a[2,2]).max(2)>40
    sub=ndimage.binary_fill_holes(fg[box[1]:box[3],box[0]:box[2]]);lab,n=ndimage.label(sub)
    if n>1:sub=lab==(np.argmax(np.bincount(lab.ravel())[1:])+1)
    return sub


def mask_section(mask,mapping,tol,frame):
    """Zeilenläufe als Rechtecke in mm vereinigen, vereinfachen (Abweichung ≤ tol) und auf den Rahmen (a,b) einpassen.
    Das Einpassen gleicht aus, dass Vereinfachung, Lochfüllung oder Komponentenwahl ein Randpixel der Quadrantenhülle entfernen."""
    _,(h0,dh),(v0,dv)=mapping;rects=[]
    for i,row in enumerate(mask):
        d=np.diff(np.concatenate(([0],row.astype(np.int8),[0])));starts,ends=np.nonzero(d==1)[0],np.nonzero(d==-1)[0]
        for j0,j1 in zip(starts,ends):
            a0,a1=sorted((h0+j0*dh,h0+j1*dh));b0,b1=sorted((v0+i*dv,v0+(i+1)*dv))
            rects.append(np.array([[a0,b0],[a1,b0],[a1,b1],[a0,b1]]))
    cs=mf.CrossSection(rects).simplify(tol);b=np.array(cs.bounds()).reshape(2,2);lo,hi=np.array(frame).T
    return mf.CrossSection([lo+(np.asarray(p)-b[0])*(hi-lo)/(b[1]-b[0]) for p in cs.to_polygons()])


def extrude(cs,view,R):
    """Querschnitt (a,b) der Ansicht entlang der Projektionsrichtung über den Rahmen (+PAD) extrudieren."""
    (ha,_),(va,_)=VIEWS[view];da=DEPTH[view];lo,hi=R[da];solid=cs.extrude(hi-lo+2*PAD)
    m=np.zeros((3,4));m[AX.index(ha),0]=1;m[AX.index(va),1]=1;m[AX.index(da),2]=1;m[AX.index(da),3]=lo-PAD
    if np.linalg.det(m[:,:3])<0:m[AX.index(da),2],m[AX.index(da),3]=-1,hi+PAD  # Extrusion umkehren statt spiegeln (Windung bleibt außen)
    return solid.transform(m)


def canonical(solid):
    """Netz kanonisch ordnen (Ecken lexikografisch, Dreiecke ab kleinstem Index, Windung erhalten) → bytegleiche Ausgabe."""
    mesh=solid.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3].astype(np.float64);t=np.asarray(mesh.tri_verts).astype(np.int64)
    order=np.lexsort(v.T[::-1]);inv=np.empty_like(order);inv[order]=np.arange(len(order));v,t=v[order],inv[t]
    t=np.array([np.roll(tri,-int(np.argmin(tri))) for tri in t]);t=t[np.lexsort(t.T[::-1])]
    return v,t


def strip_ranges(cs,levels,width):
    """Ausdehnung (a0,a1) eines Querschnitts (a,b) auf den Höhen b=levels; leere Höhen von den Nachbarn interpoliert."""
    out=[]
    for b in levels:
        s=cs^mf.CrossSection.square((4*width,0.2)).translate((-2*width,b-0.1))
        out.append(np.array(s.bounds())[[0,2]] if not s.is_empty() else (np.nan,np.nan))
    out=np.array(out,float);ok=~np.isnan(out[:,0])
    return np.stack([np.interp(levels,levels[ok],out[ok,i]) for i in (0,1)],1)


def loft(sections,R):
    """Draufsicht je Höhe anisotrop auf die Front-Breite (x) und Seiten-Tiefe (f) dieser Höhe skalieren (warp einer Extrusion)."""
    (z0,z1),(x0,x1),(y0,y1)=R['Z'],R['X'],R['Y'];n=max(2,int(round((z1-z0)/LOFT_STEP)))
    levels=np.clip(np.linspace(z0,z1,n+1),z0+0.25,z1-0.25)
    xr=strip_ranges(sections['front'],levels,x1-x0);yr=strip_ranges(sections['side'],levels,y1-y0);zs=np.linspace(z0,z1,n+1)
    def warp(p):
        p=np.array(p,float);z=p[:,2]
        a0,a1=np.interp(z,zs,xr[:,0]),np.interp(z,zs,xr[:,1]);b0,b1=np.interp(z,zs,yr[:,0]),np.interp(z,zs,yr[:,1])
        p[:,0]=a0+(p[:,0]-x0)/(x1-x0)*(a1-a0);p[:,1]=b0+(p[:,1]-y0)/(y1-y0)*(b1-b0);return p
    return sections['top'].extrude(z1-z0,n-1).translate((0,0,z0)).warp_batch(warp)


def build(rgb,boxes,part,tol=TOL_MM,views=BUILD_VIEWS,modus='schnitt'):
    R=ranges(part);masks,maps,sections={},{},{}
    for view in VIEWS:
        maps[view]=view_map(view,boxes[view],part);masks[view]=silhouette(rgb,boxes[view])
        (ha,_),(va,_)=VIEWS[view];sections[view]=mask_section(masks[view],maps[view],tol,(R[ha],R[va]))
    solids=[extrude(sections[v],v,R) for v in views]
    if modus=='loft':solids.append(loft(sections,R))
    solid=mf.Manifold.batch_boolean(solids,mf.OpType.Intersect)
    if str(solid.status())!='Error.NoError' or solid.is_empty():raise ValueError(f'Hülle leer/ungültig: {solid.status()}')
    v,t=canonical(solid)
    return {'solid':solid,'vertices':v,'triangles':t,'masks':masks,'maps':maps,'sections':sections,'views':tuple(views),'modus':modus}


def project(v,t,view,mapping,shape):
    """Hülle orthografisch in das Pixelraster der Quellansicht rastern (SS-fach überabgetastet, Mehrheit je Pixel)."""
    (ha,va),(h0,dh),(v0,dv)=mapping;H,W=shape;img=Image.new('L',(W*SS,H*SS));d=ImageDraw.Draw(img)
    px=np.stack([(v[:,AX.index(ha)]-h0)/dh,(v[:,AX.index(va)]-v0)/dv],1)*SS
    for tri in px[t]:d.polygon([tuple(p) for p in tri],fill=255)
    a=np.asarray(img,dtype=np.float32).reshape(H,SS,W,SS).mean((1,3))
    return a>=127.5


def iou(a,b):return round(float((a&b).sum()/(a|b).sum()),4)


def boundary_deviation_mm(mask,section,mapping):
    """Größter Abstand zwischen Pixelkante und vereinfachtem Polygon (über die Pixel der Differenzfläche), in mm."""
    (ha,va),(h0,dh),(v0,dv)=mapping;H,W=mask.shape;img=Image.new('L',(W*SS,H*SS));d=ImageDraw.Draw(img)
    for poly in section.to_polygons():d.polygon([(((a-h0)/dh)*SS,((b-v0)/dv)*SS) for a,b in poly],fill=255)
    poly=np.asarray(img,dtype=np.float32).reshape(H,SS,W,SS).mean((1,3))>=127.5;diff=poly^mask
    if not diff.any():return 0.0,iou(poly,mask)
    pm=np.pad(mask,1)  # Rand zählt als außen, sonst misst die Distanztransformation an der Quadrantenkante ins Leere
    dist=np.where(pm,ndimage.distance_transform_edt(pm),ndimage.distance_transform_edt(~pm))[1:-1,1:-1]
    return round(max(0.0,float(dist[diff].max())-0.5)*max(abs(dh),abs(dv)),3),iou(poly,mask)  # Pixelmitte → Pixelkante


def joint_sections(solid,part):
    """Querschnitt der Hülle an jeder Gelenkhöhe (im Rahmen 1 mm nach innen) gegen den Anschluss-Ø aus dem Manifest."""
    (u0,u1)=part['u_mm'];out={}
    for j in part['joints']:
        u=j.get('diameter_row_u',j['u']);u=min(max(u,u0+1),u1-1);cs=solid.slice(u)
        if cs.is_empty():out[j['id']]={'u':u,'leer':True};continue
        b=cs.bounds();x0,y0,x1,y1=b
        out[j['id']]={'u':u,'breite_x_mm':round(x1-x0,1),'tiefe_f_mm':round(y1-y0,1),'flaeche_mm2':round(cs.area(),0),
                      'durchmesser_soll_mm':j['diameter_mm'],'mitte_innen':bool(x0<=j['x']<=x1 and y0<=-j['f']<=y1)}
    return out


def measure(res,part,record):
    v,t=res['vertices'],res['triangles'];R=ranges(part);out={'ansichten':{}}
    hull_masks={}
    for view in VIEWS:
        m=res['masks'][view];hm=project(v,t,view,res['maps'][view],m.shape);hull_masks[view]=hm
        dev,poly_iou=boundary_deviation_mm(m,res['sections'][view],res['maps'][view])
        entry={'iou_huelle_gegen_quelle':iou(hm,m),'polygon_iou_gegen_maske':poly_iou,'polygon_abweichung_max_mm':dev,
               'polygon_ecken':sum(len(p) for p in res['sections'][view].to_polygons()),
               'mm_je_px':[round(abs(res['maps'][view][1][1]),4),round(abs(res['maps'][view][2][1]),4)],
               'baut_mit':view in res['views']}
        if view!='top':
            entry['iou_kontur_huelle']=pc.contour_iou(hm,(0,0,m.shape[1],m.shape[0]),part,view)
            entry['iou_kontur_quelle']=record['messung']['iou_kontur'][view]['rahmen_eingepasst']
        out['ansichten'][view]=entry
    lo,hi=v.min(0),v.max(0);solid=res['solid']
    out['rahmen_abweichung_mm']={a:[round(float(lo[i]-R[a][0]),3),round(float(hi[i]-R[a][1]),3)] for i,a in enumerate(AX)}
    out['netz']={'ecken':len(v),'dreiecke':len(t),'volumen_l':round(solid.volume()/1e6,3),'oberflaeche_m2':round(solid.surface_area()/1e6,4),
                 'genus':solid.genus(),'quader_fuellgrad':round(solid.volume()/np.prod([R[a][1]-R[a][0] for a in AX]),3)}
    out['gelenke']=joint_sections(solid,part);return out,hull_masks


def srgb_lin(c):
    c=np.array([int(c[i:i+2],16)/255 for i in (1,3,5)]);return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)


def export_xyz(v):return np.stack([v[:,0],v[:,2],-v[:,1]],1)/1000  # Blender-mm → Meter Y-oben (x,u,f)


def glb_bytes(v,t,name,color):
    p=export_xyz(v).astype('<f4');i=t.astype('<u4');pb,ib=p.tobytes(),i.tobytes();bin_=pb+ib+b'\0'*(-len(pb+ib)%4)
    r,g,b=(round(float(x),6) for x in srgb_lin(color))
    doc={'asset':{'version':'2.0','generator':f'cubeescape-formgenv2 tools/r02_part_hull.py v{VERSION}'},'scene':0,
         'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':name}],
         'meshes':[{'name':name,'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],
         'materials':[{'name':'frost_shell','pbrMetallicRoughness':{'baseColorFactor':[r,g,b,1.0],'metallicFactor':0.0,'roughnessFactor':0.5}}],
         'buffers':[{'byteLength':len(bin_)}],
         'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(pb),'target':34962},
                        {'buffer':0,'byteOffset':len(pb),'byteLength':len(ib),'target':34963}],
         'accessors':[{'bufferView':0,'componentType':5126,'count':len(p),'type':'VEC3',
                       'min':[float(x) for x in p.min(0)],'max':[float(x) for x in p.max(0)]},
                      {'bufferView':1,'componentType':5125,'count':i.size,'type':'SCALAR'}]}
    js=json.dumps(doc,separators=(',',':'),sort_keys=True).encode();js+=b' '*(-len(js)%4)
    return struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(bin_))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(bin_),0x004E4942)+bin_


def obj_bytes(v,t,name):
    lines=[f'# cubeescape-formgenv2 tools/r02_part_hull.py v{VERSION}; Meter, Y oben (x,u,f)',f'o {name}']
    lines+=[f'v {a:.6f} {b:.6f} {c:.6f}' for a,b,c in export_xyz(v)];lines+=[f'f {a+1} {b+1} {c+1}' for a,b,c in t]
    return ('\n'.join(lines)+'\n').encode()


def shade(v,t,direction,up,size,color,mapping=None,margin=0.06,aa=2):
    """Flach schattierte Orthoansicht mit Z-Puffer (aa-fach überabgetastet). Mit mapping im Pixelraster der Quellansicht."""
    d=np.asarray(direction,float);d/=np.linalg.norm(d);upv=np.asarray(up,float);r=np.cross(d,upv);r/=np.linalg.norm(r);u=np.cross(r,d)
    tri=v[t];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    light=np.array([-0.4,-0.7,0.6]);light/=np.linalg.norm(light);base=np.array([int(color[i:i+2],16) for i in (1,3,5)],float)
    W,H=size[0]*aa,size[1]*aa
    if mapping is None:
        P=np.stack([v@r,v@u],1);lo,hi=P.min(0),P.max(0);s=min(W,H)*(1-2*margin)/max(hi-lo);P=(P-(lo+hi)/2)*[s,-s]+[W/2,H/2]
    else:
        (ha,va),(h0,dh),(v0,dv)=mapping[:3];P=np.stack([(v[:,AX.index(ha)]-h0)/dh,(v[:,AX.index(va)]-v0)/dv],1)*[W/mapping[3][0],H/mapping[3][1]]
    Z=v@d;zb=np.full((H,W),np.inf);cb=np.full((H,W,3),128.0)
    for k in np.nonzero((n@-d)>0)[0]:
        p,z=P[t[k]],Z[t[k]];x0,y0=np.maximum(np.floor(p.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(p.max(0)).astype(int),(W,H))
        (ax,ay),(bx,by),(cx,cy)=p;den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if x0>=x1 or y0>=y1 or abs(den)<1e-12:continue
        xs,ys=np.meshgrid(np.arange(x0,x1)+0.5,np.arange(y0,y1)+0.5)
        w0=((by-cy)*(xs-cx)+(cx-bx)*(ys-cy))/den;w1=((cy-ay)*(xs-cx)+(ax-cx)*(ys-cy))/den;w2=1-w0-w1
        zz=w0*z[0]+w1*z[1]+w2*z[2];sub=zb[y0:y1,x0:x1];upd=(w0>=-1e-9)&(w1>=-1e-9)&(w2>=-1e-9)&(zz<sub)
        sub[upd]=zz[upd];cb[y0:y1,x0:x1][upd]=np.clip(base*(0.3+0.4*float(n[k]@-d)+0.3*max(0.0,float(n[k]@light))),0,255)  # Kopflicht + Streiflicht
    return Image.fromarray(cb.round().astype(np.uint8)).resize(size,Image.LANCZOS)


def font(size):
    for f in (ROOT/'docs/fonts/DejaVuSans.ttf','/System/Library/Fonts/Supplemental/Arial.ttf'):
        try:return ImageFont.truetype(str(f),size)
        except OSError:pass
    return ImageFont.load_default(size)


VIEW_DIR={'front':((0,1,0),(0,0,1)),'side':((-1,0,0),(0,0,1)),'top':((0,0,-1),(0,1,0)),'back':((0,-1,0),(0,0,1))}
# Blickrichtung (Kamera schaut entlang) und oben: Front von vorn (−Y) nach +Y, Seite von links (+X) nach −X, Draufsicht nach −Z (vorn unten)


def contact(img,boxes,res,meas,part,title):
    """Kontaktbogen: oben Quellquadranten, unten Hüllen-Orthos im gleichen Raster mit Quellkontur (gelb), plus 3/4-Ansicht."""
    cell=360;pad=12;head=34;foot=40;cols=4;canvas=Image.new('RGB',(cols*cell+(cols+1)*pad,head+2*(cell+foot)+pad),(128,128,128))
    dr=ImageDraw.Draw(canvas);big,small=font(16),font(14)
    dr.text((pad,10),title,fill='#111111',font=big);v,t=res['vertices'],res['triangles']
    color=pt.tomllib.loads((ROOT/'skins.toml').read_text())['roles']['frost_shell']['color']
    def place(tile,col,row,label):
        tile=tile.copy();tile.thumbnail((cell,cell),Image.LANCZOS);x=pad+col*(cell+pad);y=head+row*(cell+foot)
        canvas.paste(tile,(x+(cell-tile.width)//2,y+(cell-tile.height)//2));dr.text((x,y+cell+4),label,fill='#111111',font=small)
    for c,view in enumerate(('front','side','top','back')):
        b=boxes[view];place(img.convert('RGB').crop(b),c,0,f'Quelle {view}'+('' if view in res['views'] else ' (Gegenprobe)'))
    for c,view in enumerate(('front','side','top')):
        m=res['masks'][view];mp=res['maps'][view];H,W=m.shape;k=max(1,round(720/max(W,H)))
        tile=shade(v,t,*VIEW_DIR[view],(W*k,H*k),color,mapping=(*mp,(W,H)))
        edge=m^ndimage.binary_erosion(m,iterations=1);edge=np.kron(edge,np.ones((k,k),bool));edge=ndimage.binary_dilation(edge,iterations=k)
        a=np.asarray(tile).copy();a[edge]=(255,212,0);tile=Image.fromarray(a);e=meas['ansichten'][view]
        place(tile,c,1,f'Hülle {view}: IoU Quelle {e["iou_huelle_gegen_quelle"]:.3f}'+
              (f' · Kontur {e["iou_kontur_huelle"]:.3f}' if e.get('iou_kontur_huelle') is not None else ''))
    place(shade(v,t,(-0.55,0.75,-0.38),(0,0,1),(720,720),color),3,1,
          f'3/4 · Rücken-Gegenprobe IoU {meas["ansichten"]["back"]["iou_huelle_gegen_quelle"]:.3f}')
    return canvas


def params_key(tol,views,modus):
    return sha(json.dumps({'tol_mm':tol,'views':list(views),'modus':modus,'pad':PAD,'ss':SS,'loft_step':LOFT_STEP,'version':VERSION},sort_keys=True).encode())


def out_name(tol,views,modus):
    """hull/ für Standardparameter, sonst sprechend: hull-loft, hull-tol1, hull-front+side …"""
    tags=([modus] if modus!='schnitt' else [])+([f'tol{tol:g}'] if tol!=TOL_MM else [])+(['+'.join(views)] if tuple(views)!=BUILD_VIEWS else [])
    return '-'.join(['hull',*tags])


def run(ablage,manifest,tol=TOL_MM,views=BUILD_VIEWS,modus='schnitt',force=False):
    ablage=Path(ablage);record=json.loads((ablage/'record.json').read_text());man=json.loads(Path(manifest).read_text())
    part=man['parts'][record['teil']];src=(ablage/'source.png').read_bytes()
    key=params_key(tol,views,modus);out=ablage/out_name(tol,views,modus)
    inputs={'bild_sha256':sha(src),'record_quadranten_px':record['quadranten_px'],
            'teil_sha256':sha(json.dumps(part,sort_keys=True).encode()),'parameter_sha256':key}
    old=out/'hull.json'
    if not force and old.exists():
        prev=json.loads(old.read_text())
        if prev.get('eingaben')==inputs and all((out/n).exists() and sha((out/n).read_bytes())==h for n,h in prev['dateien'].items()):
            print(f'aktuell → {out}');return prev
    img=Image.open(ablage/'source.png');rgb=np.asarray(img.convert('RGB'))
    boxes={k:tuple(b) for k,b in record['quadranten_px'].items()}
    res=build(rgb,boxes,part,tol,views,modus)
    meas,_=measure(res,part,record);name=f"r02-{record['teil']}-{record['variante']}-{record['bild_sha256'][:12]}-hull"
    color=pt.tomllib.loads((ROOT/'skins.toml').read_text())['roles']['frost_shell']['color']
    files={'hull.glb':glb_bytes(res['vertices'],res['triangles'],name,color),'hull.obj':obj_bytes(res['vertices'],res['triangles'],name)}
    title=(f"{record['teil']}/{record['variante']}/{record['bild_sha256'][:12]} · Silhouettenhülle v{VERSION} ({modus}) · "
           f"tol {tol} mm · {meas['netz']['dreiecke']} Dreiecke · {meas['netz']['volumen_l']} l")
    buf=__import__('io').BytesIO();contact(img,boxes,res,meas,part,title).save(buf,'PNG',compress_level=9);files['contact.png']=buf.getvalue()
    out.mkdir(parents=True,exist_ok=True)
    for n,b in files.items():(out/n).write_bytes(b)
    doc={'format':'cubeescape-formgenv2/r02-part-hull','version':VERSION,'teil':record['teil'],'variante':record['variante'],
         'quelle':f"{record['teil']}/{record['variante']}/{record['bild_sha256'][:12]}",'eingaben':inputs,
         'parameter':{'tol_mm':tol,'tol_herkunft':'Annahme (Vereinfachung; gemessene Abweichung je Ansicht unter messung)',
                      'modus':modus,'extrudiert':list(views),'gegenprobe':[v for v in VIEWS if v not in views],'pad_mm':PAD,'ueberabtastung':SS},
         'achsen':'GLB/OBJ in Metern, Y oben: (x anatomisch links, u, f vorn); Blender-Import ergibt X=x, Y=−f, Z=u',
         'massstab':'anisotrop je Ansicht auf frame_mm (Quadrantenhülle = Rahmen)','messung':meas,
         'profile_mm':{v:{'achsen':[VIEWS[v][0][0],VIEWS[v][1][0]],'konturen':[[[round(float(a),2),round(float(b),2)] for a,b in poly]
                                                                          for poly in res['sections'][v].to_polygons()]} for v in views},
         'dateien':{n:sha(b) for n,b in files.items()}}
    old.write_text(json.dumps(doc,ensure_ascii=False,indent=1)+'\n');print(f'gebaut → {out}');return doc


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('ablage',type=Path);ap.add_argument('--manifest',type=Path,default=pt.OUT/'manifest.json')
    ap.add_argument('--tol-mm',type=float,default=TOL_MM);ap.add_argument('--modus',choices=MODI,default='schnitt');ap.add_argument('--views',default=','.join(BUILD_VIEWS))
    ap.add_argument('--force',action='store_true');a=ap.parse_args(argv)
    views=tuple(a.views.split(','))
    if not set(views)<=set(VIEWS) or len(views)<2:ap.error(f'--views: mindestens zwei aus {sorted(VIEWS)}')
    doc=run(a.ablage,a.manifest,a.tol_mm,views,a.modus,a.force);print(json.dumps(doc['messung'],ensure_ascii=False,indent=1));return doc


if __name__=='__main__':main()
