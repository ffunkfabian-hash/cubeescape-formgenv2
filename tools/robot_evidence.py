"""Registrierte R01-Prüfbilder: gemeinsamer Frontmaßstab, kein Fit pro Modell."""
import argparse,hashlib,importlib,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from formgen import geom,model,raster,versions
from formgen.cache import Artifact,canonical,file_hash,run_artifacts
REF=Path.home()/'Library/Caches/CubeEscapeFormgen/refs'
OUT=Path.home()/'Library/Caches/CubeEscapeFormgen/evidence/robot'
SCALE=3653/1.924/4
CENTER_Z=(3876/4-512)/SCALE
VIEWS={'front':('front',[0,0,CENTER_Z],0,0),'back':('back',[0,0,CENTER_Z],0,0),
       'side-right':('side_left',[0,-(2150/4-512)/SCALE,CENTER_Z],0,7),
       'side-left':('side_right',[0,(1946/4-512)/SCALE,CENTER_Z],0,5)}

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

def document(groups):
    parts=[];anchors={};sources={}
    for group in groups:
        name='formgen.models.figures.r01_parts.'+group;m=importlib.import_module(name)
        parts+=m.PARTS;anchors.update(m.ANCHORS);sources[group]=file_hash(Path(m.__file__))
    d={'INFO':{'id':'R01','kind':'figure','name_de':'BASIC Roboter','provenance':{'kind':'Vorgabe','source':'Neue vier Orthos; Höhe1924mm Entwurfsvorgabe; Details siehe docs/herkunft-roboter.md'}},'PARTS':parts,'ASSEMBLIES':[{'id':g,'de':g} for g in groups],'ANCHORS':anchors}
    # Gruppenanker dürfen auf Teile verweisen, die erst Montage liefert.
    pids={p['id'] for p in parts};d['ANCHORS']={k:v for k,v in anchors.items() if v.get('part') in pids}
    return geom.evaluate(model.normalize(d),bevels=True),sources

def build_image(artifact):
    doc,_=document(artifact.inputs['groups']);view=artifact.params['view']
    camera,center,_,_=VIEWS[view]
    im=raster.render(doc,view=camera,width=1024,height=1024,scale=SCALE,center=center,bg='transparent')
    im.putalpha(im.coverage_mask)
    buf=io.BytesIO();im.save(buf,'PNG');return buf.getvalue()

def evaluate(groups, u_min=0,u_max=1924):
    doc,sources=document(groups);name='-'.join(groups);out=OUT/name;out.mkdir(parents=True,exist_ok=True)
    result={'groups':groups,'counts':doc['counts'],'sources':sources,'height_mm':1924,'scale_px_m':SCALE,'u_range_mm':[u_min,u_max],'views':{},'warnings':doc['warnings'],'mask_source':'same render frame, final part buffer, coverage >=128/255','band_metric':'mean_outer_row_span_v1; fixed registered rows, empty rows included'}
    for view in VIEWS:
        a=Artifact('R01-'+name,'views',hashlib.sha256(canonical(sources)).hexdigest(),{'view':view,'registration':4,'bevels':True,'mask_source':'raster-final-part-buffer','skin_sha':file_hash(ROOT/'skins.toml')},{'GEOM':versions.GEOM,'RASTER':versions.RASTER},view+'-frame.png','tools.robot_evidence:build_image',{'groups':groups})
        run_artifacts([a],out,Path.home()/'Library/Caches/CubeEscapeFormgen/artifacts')
        frame=Image.open(out/(view+'-frame.png')).convert('RGBA')
        mask=frame.getchannel('A');mask.save(out/(view+'-mask.png'));m=np.asarray(mask)>127
        background=Image.new('RGBA',frame.size,raster.palette()['render']['background_mid'])
        Image.alpha_composite(background,frame).convert('RGB').save(out/(view+'.png'))
        ref=Image.open(REF/f'ortho-{view}-mask.png')
        ref=ref.resize((1024,1024),Image.Resampling.NEAREST)
        _,_,dx,dy=VIEWS[view]
        shifted=Image.new('L',(1024,1024));shifted.paste(ref,(round(dx/4),round(dy/4)));r=np.asarray(shifted)>127
        yy=np.arange(1024)[:,None];u=(3876/4-yy)/SCALE*1000;region=(u>=u_min)&(u<=u_max)
        r=r&region;m=m&region
        # Isolated lower groups: exclude dangling hands from target in shared heights.
        if groups==['legs']:
            x=(np.arange(1024)[None,:]-512)/SCALE*1000
            if view in ('front','back'):r &= abs(x)<380
        union=(r|m).sum();iou=float((r&m).sum()/union) if union else 0
        bands=band_metrics(r,m,u[:,0],u_min,u_max)
        overlay=np.full((1024,1024,3),238,np.uint8);overlay[r]=[220,70,80];overlay[m]=[60,130,230];overlay[r&m]=[95,80,150];Image.fromarray(overlay).save(out/(view+'-overlay.png'))
        result['views'][view]={'iou':iou,'bands':bands,'iou_pass':iou>=.9,'bands_pass':all(b['ratio'] is not None and .92<=b['ratio']<=1.08 for b in bands)}
    (out/'metrics.json').write_bytes(canonical(result)+b'\n')
    print(name,doc['counts'], {v:round(d['iou'],4) for v,d in result['views'].items()})
    return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('groups',nargs='+');p.add_argument('--u-min',type=float,default=0);p.add_argument('--u-max',type=float,default=1924);a=p.parse_args();evaluate(a.groups,a.u_min,a.u_max)
