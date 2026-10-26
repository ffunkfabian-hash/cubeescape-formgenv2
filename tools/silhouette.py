"""Deterministische Zielbild-Masken und IoU; Messung ohne erfundene Modellmaße.

Konzept-Crops manuell aus Nutzervorgabe, Hintergrundmodell linear je Zeile.
Messprotokoll hält Zuschnitt, Schwelle, Ausrichtung und Quellenhash fest.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage


def extract(path, box, threshold=18):
    rgb=np.asarray(Image.open(path).convert('RGB').crop(box),dtype=float)
    h,w,_=rgb.shape
    # Randstreifen außerhalb der einzelnen Figur; lineare Hintergrundschätzung.
    left=np.median(rgb[:,:8],axis=1);right=np.median(rgb[:,-8:],axis=1)
    t=np.linspace(0,1,w)[None,:,None]
    bg=left[:,None,:]*(1-t)+right[:,None,:]*t
    mask=np.max(abs(rgb-bg),axis=2)>threshold
    labels,n=ndimage.label(mask)
    sizes=np.bincount(labels.ravel());sizes[0]=0
    # Kleine Teile nur in Nähe großer Figur behalten, nie Schrift/Schlagschatten.
    keep=np.flatnonzero(sizes>=max(12,mask.size*.00015))
    mask=np.isin(labels,keep)
    mask=ndimage.binary_fill_holes(mask)
    return Image.fromarray((mask*255).astype('uint8'))


def normalized(mask, height=900, width=600):
    a=np.asarray(mask)>127
    ys,xs=np.nonzero(a)
    if not len(xs):raise ValueError('Leere Maske')
    crop=Image.fromarray((a[ys.min():ys.max()+1,xs.min():xs.max()+1]*255).astype('uint8'))
    scale=(height-20)/crop.height
    nw=round(crop.width*scale)
    if nw>width-20:raise ValueError('Maske passt nicht in normalisierte Breite')
    crop=crop.resize((nw,height-20),Image.Resampling.NEAREST)
    canvas=Image.new('L',(width,height));canvas.paste(crop,((width-nw)//2,10))
    return np.asarray(canvas)>127


def compare(a,b):
    a=normalized(a);b=normalized(b)
    union=(a|b).sum();iou=float((a&b).sum()/union)
    bands=[]
    for n in range(10):
        aa=a[10+n*88:10+(n+1)*88];bb=b[10+n*88:10+(n+1)*88]
        # occupied width summed per row, includes actual limb gaps
        wa=float(aa.sum(axis=1).mean());wb=float(bb.sum(axis=1).mean())
        bands.append({'band_top_to_bottom':n,'reference_mean_width_px':wa,'model_mean_width_px':wb,'ratio':wb/wa if wa else None})
    rgba=np.full((*a.shape,3),238,dtype=np.uint8)
    rgba[a]=[225,80,85];rgba[b]=[55,130,230];rgba[a&b]=[100,85,155]
    return {'iou':iou,'bands':bands,'pass':iou>=.9 and all(x['ratio'] is not None and .92<=x['ratio']<=1.08 for x in bands)},Image.fromarray(rgba)


def prepare():
    base=Path.home()/'Library/Caches/CubeEscapeFormgen/refs'
    defs={'body_b_front':('formstudie-b.png',[945,225,1385,1040],7),
          'concept_front':('roboterkonzeptblatt.png',[95,75,520,930],20),
          'concept_side':('roboterkonzeptblatt.png',[670,75,870,930],20)}
    records={}
    for name,(filename,box,threshold) in defs.items():
        path=base/filename;mask=extract(path,box,threshold)
        mask.save(base/(name+'-mask.png'));Image.open(path).crop(box).save(base/(name+'-crop.png'))
        records[name]={'source':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop_xyxy':box,'threshold_rgb':threshold,'method':'row-wise linear background from 8px border; connected components; hole fill','status':'requires visual mask review'}
    result,overlay=compare(Image.open(base/'body_b_front-mask.png'),Image.open(base/'concept_front-mask.png'))
    overlay.save(base/'target-front-difference.png');records['target_front_comparison']=result
    (base/'reference-masks.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Ziel-Fronten IoU',round(result['iou'],4),'Masken noch zu sichten')
if __name__=='__main__':prepare()
