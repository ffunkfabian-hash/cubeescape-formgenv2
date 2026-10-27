"""R02-Teilbild prüfen und reproduzierbar ablegen (Bildgenerator → Meshy → Blender).

Erwartet das Layout aus docs/r02-teile/varianten.toml: quadratisch, 2×2 (Front | Seite von links / Draufsicht | Rücken).
Misst je Quadrant die Hülle, rechnet mit einem gemeinsamen Maßstab (aus der Fronthöhe) in mm um und vergleicht mit dem
Schablonen-Manifest: Ansichtskonsistenz, Proportionen, IoU gegen die gemessene Kontur (gleicher Maßstab und rahmen-
eingepasst), Palettenanteil. Ergebnis: Blender-Skalierung je Achse und Meshy-Einzelansichten (1024², Grund #808080).

Ablage: refs-r02/part-generations/<teil>/<variante>/<bild-sha12>/ mit source.png, front|side|back|top.png, prompt.txt,
record.json; index.json listet alle Ablagen. Ohne Zeitstempel: gleiche Eingaben ergeben bytegleiche Ablagen.
Ein Bild wird nie neu generiert, nur abgelegt – Reproduzierbarkeit über Bild-SHA plus Prompt-SHA.

Aufruf: python tools/r02_part_check.py BILD --part kopf --variant a-blatt --generator "codex gpt-6-luna"
        [--prompt-file DATEI] [--seed N] [--dry-run]
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from tools import r02_part_templates as pt

GEN=pt.REF/'part-generations'
QUADS={'front':(0,0),'side':(0,1),'top':(1,0),'back':(1,1)}
MESHY_PX=1024
LIMITS={'konsistenz':0.05,'iou_rahmen':0.85}  # Annahme: Schwellen für „tauglich“, am Kopf-Probelauf 27.10.2026 abgeleitet


def sha(b):return hashlib.sha256(b).hexdigest()


def quadrant_boxes(rgb):
    """Vordergrund je Quadrant (Abstand > 40 zur Eckfarbe) → Hülle (x0,y0,x1,y1) in Bildpixeln."""
    a=rgb.astype(int);fg=np.abs(a-a[2,2]).max(2)>40;H,W=fg.shape;out={}
    for k,(r,c) in QUADS.items():
        y0,x0=r*H//2,c*W//2;sub=fg[y0:y0+H//2,x0:x0+W//2];ys,xs=np.nonzero(sub)
        out[k]=None if len(xs)==0 else (x0+int(xs.min()),y0+int(ys.min()),x0+int(xs.max())+1,y0+int(ys.max())+1)
    return fg,out


def contour_iou(fg,box,part,view,s=None):
    """IoU im Konturbereich: Bild mit gemeinsamem Maßstab s px/mm (mittig) oder ohne s rahmen-eingepasst auf mm gelegt."""
    rows=part['contour_mm']['side' if view=='side' else view]
    if not rows:return None
    sg=-1 if view=='back' else 1
    if view=='side':pts=[(-b,u) for u,a,b in rows]+[(-a,u) for u,a,b in reversed(rows)]
    else:pts=[(sg*a,u) for u,a,b in rows]+[(sg*b,u) for u,a,b in reversed(rows)]
    (x0,x1),(fb,ff),(u0,u1)=part['frame_mm']['front']['x'],part['frame_mm']['side']['f'],part['u_mm']
    h0,h1={'front':(x0,x1),'back':(-x1,-x0),'side':(-ff,-fb)}[view]
    bw,bh=box[2]-box[0],box[3]-box[1]
    if s is None:sx,sy,ox=(h1-h0)/bw,(u1-u0)/bh,h0
    else:sx=sy=1/s;ox=(h0+h1)/2-bw*sx/2
    G=2;X0,X1=min(h0,ox)-20,max(h1,ox+bw*sx)+20;V0,V1=min(u0,u1-bh*sy)-20,u1+20
    ref=Image.new('L',(int((X1-X0)*G),int((V1-V0)*G)));ImageDraw.Draw(ref).polygon([((h-X0)*G,(V1-v)*G) for h,v in pts],fill=1)
    crop=Image.fromarray((fg[box[1]:box[3],box[0]:box[2]]*255).astype('uint8'))
    gen=Image.new('L',ref.size);gen.paste(crop.resize((max(1,int(bw*sx*G)),max(1,int(bh*sy*G))),Image.NEAREST),(int((ox-X0)*G),int((V1-u1)*G)))
    r,g=np.asarray(ref)>0,np.asarray(gen)>0
    lo,hi=int((V1-max(v for _,v in pts))*G),int((V1-min(v for _,v in pts))*G)+1  # nur gemessene Zeilen
    r,g=r[lo:hi],g[lo:hi];return round(float((r&g).sum()/(r|g).sum()),3)


def measure(img,part,skins):
    rgb=np.asarray(img.convert('RGB'));fg,boxes=quadrant_boxes(rgb)
    missing=[k for k,b in boxes.items() if b is None]
    if missing:return {'fehlende_ansichten':missing},boxes
    (x0,x1),(fb,ff),(u0,u1)=part['frame_mm']['front']['x'],part['frame_mm']['side']['f'],part['u_mm']
    W,D,H=x1-x0,ff-fb,u1-u0;bw={k:b[2]-b[0] for k,b in boxes.items()};bh={k:b[3]-b[1] for k,b in boxes.items()}
    s=bh['front']/H  # px/mm aus der Fronthöhe (gemeinsamer Maßstab laut Prompt)
    mm={'front':[bw['front']/s,bh['front']/s],'back':[bw['back']/s,bh['back']/s],'side':[bw['side']/s,bh['side']/s],
        'top':[bw['top']/s,bh['top']/s]}
    w_img=(mm['front'][0]+mm['back'][0]+mm['top'][0])/3;d_img=(mm['side'][0]+mm['top'][1])/2
    h_img=(mm['front'][1]+mm['side'][1]+mm['back'][1])/3
    spread=lambda vals:round((max(vals)-min(vals))/(sum(vals)/len(vals)),3)
    kons={'hoehe':spread([mm['front'][1],mm['side'][1],mm['back'][1]]),'breite':spread([mm['front'][0],mm['back'][0],mm['top'][0]]),
          'tiefe':spread([mm['side'][0],mm['top'][1]])}
    iou={v:{'gleicher_massstab':contour_iou(fg,boxes[v],part,v,s),'rahmen_eingepasst':contour_iou(fg,boxes[v],part,v)}
         for v in ('front','back','side')}
    pal=np.array([[int(c[i:i+2],16) for i in (1,3,5)] for c in (skins['roles'][r]['color'] for r in ('frost_shell','frost_frame','frost_crystal'))])
    px=rgb[fg].astype(int);near=np.sqrt(((px[:,None]-pal[None])**2).sum(-1)).min(1)<30
    fits=[x['rahmen_eingepasst'] for x in iou.values() if x['rahmen_eingepasst'] is not None]
    ok=max(kons.values())<=LIMITS['konsistenz'] and min(fits)>=LIMITS['iou_rahmen']
    return {'masse_mm':{'bild_bei_frontmassstab':{'breite':round(w_img,1),'tiefe':round(d_img,1),'hoehe':round(h_img,1)},
                        'soll':{'breite':round(W,1),'tiefe':round(D,1),'hoehe':round(H,1)}},
            'ansichten_mm':{k:[round(v[0],1),round(v[1],1)] for k,v in mm.items()},'konsistenz_spanne':kons,
            'proportion_quote':{'breite':round(w_img/W,3),'tiefe':round(d_img/D,3)},'iou_kontur':iou,
            'palette_anteil':round(float(near.mean()),3),
            'blender_skalierung':{'x':round(W/w_img,3),'f':round(D/d_img,3),'u':round(H/h_img,3),
                                  'hinweis':'Netz nach Meshy auf frame_mm bringen: Achsfaktoren relativ zum Bildmaßstab'},
            'urteil':'tauglich' if ok else 'prüfen','grenzen':LIMITS},boxes


def meshy_view(img,box,flip=False):
    crop=img.convert('RGB').crop(box);side=int(max(crop.size)*1.16)
    canvas=Image.new('RGB',(side,side),(128,128,128));canvas.paste(crop,((side-crop.width)//2,(side-crop.height)//2))
    return canvas.resize((MESHY_PX,MESHY_PX),Image.LANCZOS)


def write_index():
    recs=[json.loads(p.read_text()) for p in sorted(GEN.glob('*/*/*/record.json'))]
    idx=[{k:r[k] for k in ('teil','variante','bild_sha256','prompt_sha256','generator','seed')}|{'urteil':r['messung'].get('urteil'),
          'ordner':f"{r['teil']}/{r['variante']}/{r['bild_sha256'][:12]}"} for r in recs]
    (GEN/'index.json').write_text(json.dumps({'format':'cubeescape-formgenv2/r02-part-generations','version':1,'ablagen':idx},
                                             ensure_ascii=False,indent=1)+'\n')


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('image',type=Path);ap.add_argument('--part',required=True)
    ap.add_argument('--variant',required=True);ap.add_argument('--generator',required=True);ap.add_argument('--seed')
    ap.add_argument('--prompt-file',type=Path,help='tatsächlich verwendeter Prompt; Standard: docs/r02-teile/prompts.json')
    ap.add_argument('--manifest',type=Path,default=pt.OUT/'manifest.json');ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args(argv)
    man=json.loads(a.manifest.read_text());part=man['parts'][a.part]
    prompts=json.loads(pt.PROMPTS.read_text())
    if a.prompt_file:text=a.prompt_file.read_text()
    else:text=prompts['prompts'][a.part][a.variant]['text']
    data=a.image.read_bytes();img=Image.open(a.image);skins=pt.tomllib.loads((ROOT/'skins.toml').read_text())
    res,boxes=measure(img,part,skins)
    rec={'teil':a.part,'variante':a.variant,'generator':a.generator,'seed':a.seed,'bild_sha256':sha(data),
         'bild_px':list(img.size),'prompt_sha256':sha(text.encode()),
         'prompt_aktuell':sha(text.encode())==prompts['prompts'][a.part].get(a.variant,{}).get('sha256'),
         'schablone_png_sha256':part['files']['png']['sha256'],'quadranten_px':boxes,'messung':res}
    print(json.dumps(rec,ensure_ascii=False,indent=1))
    if a.dry_run or 'fehlende_ansichten' in res:return rec
    d=GEN/a.part/a.variant/rec['bild_sha256'][:12];d.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(a.image,d/'source.png');(d/'prompt.txt').write_text(text)
    for k,b in boxes.items():meshy_view(img,b).save(d/f'{k}.png',compress_level=9)
    (d/'record.json').write_text(json.dumps(rec,ensure_ascii=False,indent=1)+'\n');write_index()
    print(f'abgelegt → {d}');return rec


if __name__=='__main__':main()
