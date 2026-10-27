"""Registrierte Roboter-Prüfbilder: gemeinsamer Frontmaßstab, kein Fit pro Modell.

R01: vier 4096²-Orthos, Werte unverändert seit registration 4.
R02: weiß/blaues Blatt, mask revision 1 und Registrierung aus
refs-r02/mask-provenance.json (tools/robot_reference_masks.py R02).
Aufruf: python tools/robot_evidence.py [--robot R02] gruppe [gruppe …]
"""
import argparse,hashlib,importlib,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from formgen import geom,model,raster,versions
from formgen.cache import Artifact,canonical,file_hash,run_artifacts
CACHE=Path.home()/'Library/Caches/CubeEscapeFormgen'
REF=CACHE/'refs'
OUT=CACHE/'evidence/robot'
SCALE=3653/1.924/4
CENTER_Z=(3876/4-512)/SCALE
VIEWS={'front':('front',[0,0,CENTER_Z],0,0),'back':('back',[0,0,CENTER_Z],0,0),
       'side-right':('side_left',[0,-(2150/4-512)/SCALE,CENTER_Z],0,7),
       'side-left':('side_right',[0,(1946/4-512)/SCALE,CENTER_Z],0,5)}

def _r02():
    """R02 constants from the frozen mask provenance (revision 1)."""
    ref=CACHE/'refs-r02';prov=json.loads((ref/'mask-provenance.json').read_bytes())
    floor=prov['front_floor_px'];scale=(floor-prov['front_top_px'])/2.0/4;cz=(floor/4-512)/scale
    views={v:(r['camera'],[0,0,cz],round(2048-r['registration']['x0_px']+r['window_x0_px']),0)
           for v,r in prov['views'].items()}
    return dict(id='R02',ref=ref,out=CACHE/'evidence/robot-r02',height_mm=2000,scale=scale,floor_px=floor,views=views,
                package='formgen.models.figures.r02_parts.',registration='r02-1',legs_half_width=None,
                mask=lambda view:ref/f'ortho-{view}-mask.png',canvas=4096,mask_sha={v:r['mask_sha256'] for v,r in prov['views'].items()},
                info={'id':'R02','kind':'figure','name_de':'Frost Roboter','provenance':{'kind':'Vorgabe','source':'Weiß/blaues Blatt; Höhe 2000mm Nutzervorgabe; Details siehe docs/herkunft-r02.md'}})

ROBOTS={'R01':lambda:dict(id='R01',ref=REF,out=OUT,height_mm=1924,scale=SCALE,floor_px=3876,views=VIEWS,
                          package='formgen.models.figures.r01_parts.',registration=4,legs_half_width=380,
                          mask=lambda view:REF/f'ortho-{view}-mask.png',canvas=None,mask_sha=None,
                          info={'id':'R01','kind':'figure','name_de':'BASIC Roboter','provenance':{'kind':'Vorgabe','source':'Neue vier Orthos; Höhe1924mm Entwurfsvorgabe; Details siehe docs/herkunft-roboter.md'}}),
        'R02':_r02}

def band_metrics(reference, rendered, heights, u_min, u_max):
    """Mean outer row span over the same fixed rows, including empty rows.

    Width includes the gap between limbs. Occupied area remains a separate
    diagnostic: it cannot detect limbs moving apart without changing size.
    """
    def spans(mask):
        present=mask.any(axis=1)
        left=mask.argmax(axis=1)
        right=mask.shape[1]-1-mask[:,::-1].argmax(axis=1)
        return np.where(present,right-left+1,0)
    rw,mw=spans(reference),spans(rendered)
    result=[]
    for i in range(10):
        lo=u_min+(u_max-u_min)*i/10;hi=u_min+(u_max-u_min)*(i+1)/10
        rows=(heights>=lo)&(heights<hi)
        wr=float(rw[rows].mean()) if rows.any() else 0.
        wm=float(mw[rows].mean()) if rows.any() else 0.
        ar=int(reference[rows].sum());am=int(rendered[rows].sum())
        result.append({'from_bottom':i,'reference_mean_width_px':wr,
                       'model_mean_width_px':wm,'ratio':wm/wr if wr else None,
                       'occupied_area_ratio':am/ar if ar else None})
    return result

def document(groups,robot='R01'):
    cfg=ROBOTS[robot]();parts=[];anchors={};sources={}
    for group in groups:
        name=cfg['package']+group;m=importlib.import_module(name)
        parts+=m.PARTS;anchors.update(m.ANCHORS);sources[group]=file_hash(Path(m.__file__))
    d={'INFO':cfg['info'],'PARTS':parts,'ASSEMBLIES':[{'id':g,'de':g} for g in groups],'ANCHORS':anchors}
    # Gruppenanker dürfen auf Teile verweisen, die erst Montage liefert.
    pids={p['id'] for p in parts};d['ANCHORS']={k:v for k,v in anchors.items() if v.get('part') in pids}
    return geom.evaluate(model.normalize(d),bevels=True),sources

def build_image(artifact):
    robot=artifact.inputs.get('robot','R01');cfg=ROBOTS[robot]()
    doc,_=document(artifact.inputs['groups'],robot);view=artifact.params['view']
    camera,center,_,_=cfg['views'][view]
    im=raster.render(doc,view=camera,width=1024,height=1024,scale=cfg['scale'],center=center,bg='transparent')
    im.putalpha(im.coverage_mask)
    buf=io.BytesIO();im.save(buf,'PNG');return buf.getvalue()

def reference_mask(view,robot='R01'):
    """Registered reference in the 1024² evaluation frame (nearest, no scaling per view)."""
    cfg=ROBOTS[robot]();_,_,dx,dy=cfg['views'][view]
    ref=Image.open(cfg['mask'](view))
    if cfg['mask_sha'] and hashlib.sha256(cfg['mask'](view).read_bytes()).hexdigest()!=cfg['mask_sha'][view]:
        raise ValueError('Referenzmaske weicht von mask-provenance ab: '+view)
    if cfg['canvas']:
        # R02: Fensterausschnitt in Blattzeilen; Registrierpunkt auf Spalte 2048.
        canvas=Image.new('L',(cfg['canvas'],cfg['canvas']));canvas.paste(ref,(dx,dy))
        return np.asarray(canvas.resize((1024,1024),Image.Resampling.NEAREST))>127
    ref=ref.resize((1024,1024),Image.Resampling.NEAREST)
    shifted=Image.new('L',(1024,1024));shifted.paste(ref,(round(dx/4),round(dy/4)));return np.asarray(shifted)>127

def view_metrics(r,m,groups,view,cfg,u_min,u_max):
    yy=np.arange(1024)[:,None];u=(cfg['floor_px']/4-yy)/cfg['scale']*1000;region=(u>=u_min)&(u<=u_max)
    r=r&region;m=m&region
    # Isolated lower groups: exclude dangling hands from target in shared heights.
    if groups==['legs'] and cfg['legs_half_width']:
        x=(np.arange(1024)[None,:]-512)/cfg['scale']*1000
        if view in ('front','back'):r &= abs(x)<cfg['legs_half_width']
    union=(r|m).sum();iou=float((r&m).sum()/union) if union else 0
    bands=band_metrics(r,m,u[:,0],u_min,u_max)
    return r,m,{'iou':iou,'bands':bands,'iou_pass':iou>=.9,'bands_pass':all(b['ratio'] is not None and .92<=b['ratio']<=1.08 for b in bands)}

def evaluate(groups, u_min=0,u_max=None,robot='R01'):
    cfg=ROBOTS[robot]();u_max=cfg['height_mm'] if u_max is None else u_max
    doc,sources=document(groups,robot);name='-'.join(groups);out=cfg['out']/name;out.mkdir(parents=True,exist_ok=True)
    result={'groups':groups,'counts':doc['counts'],'sources':sources,'height_mm':cfg['height_mm'],'scale_px_m':cfg['scale'],'u_range_mm':[u_min,u_max],'views':{},'warnings':doc['warnings'],'mask_source':'same render frame, final part buffer, coverage >=128/255','band_metric':'mean_outer_row_span_v1; fixed registered rows, empty rows included'}
    for view in cfg['views']:
        inputs={'groups':groups} if robot=='R01' else {'groups':groups,'robot':robot}
        a=Artifact(robot+'-'+name,'views',hashlib.sha256(canonical(sources)).hexdigest(),{'view':view,'registration':cfg['registration'],'bevels':True,'mask_source':'raster-final-part-buffer','skin_sha':file_hash(ROOT/'skins.toml')},{'GEOM':versions.GEOM,'RASTER':versions.RASTER},view+'-frame.png','tools.robot_evidence:build_image',inputs)
        run_artifacts([a],out,CACHE/'artifacts')
        frame=Image.open(out/(view+'-frame.png')).convert('RGBA')
        mask=frame.getchannel('A');mask.save(out/(view+'-mask.png'));m=np.asarray(mask)>127
        background=Image.new('RGBA',frame.size,raster.palette()['render']['background_mid'])
        Image.alpha_composite(background,frame).convert('RGB').save(out/(view+'.png'))
        r,m,record=view_metrics(reference_mask(view,robot),m,groups,view,cfg,u_min,u_max)
        overlay=np.full((1024,1024,3),238,np.uint8);overlay[r]=[220,70,80];overlay[m]=[60,130,230];overlay[r&m]=[95,80,150];Image.fromarray(overlay).save(out/(view+'-overlay.png'))
        result['views'][view]=record
    (out/'metrics.json').write_bytes(canonical(result)+b'\n')
    print(name,doc['counts'], {v:round(d['iou'],4) for v,d in result['views'].items()})
    return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('groups',nargs='+');p.add_argument('--robot',default='R01',choices=sorted(ROBOTS));p.add_argument('--u-min',type=float,default=0);p.add_argument('--u-max',type=float);a=p.parse_args();evaluate(a.groups,a.u_min,a.u_max,a.robot)
