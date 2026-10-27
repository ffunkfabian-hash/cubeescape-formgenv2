"""Reproduce reviewed robot reference masks; never independently scale views.

R01: original pixels stay untouched. Threshold248 and fixed head/sole crop are
segmentation assumptions (revision2), not changes made to improve model IoU.
White holes inside the connected figure are filled, closing radius2px.
R02 (mask revision 1): vector sheet rendered once at width 9803 px, alpha>127,
components >=0.2% of the largest (detached hands belong to the silhouette),
closing2, fill. Registration is stored separately; masks keep sheet pixels.
Aufruf: python tools/robot_reference_masks.py [R01|R02]
"""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image
CACHE=Path.home()/'Library/Caches/CubeEscapeFormgen'
REF=CACHE/'refs'
BOUNDS={'front':(223,3876),'back':(223,3873),'side-right':(216,3776),'side-left':(218,3776)}

def r01_mask(view):
    top,bottom=BOUNDS[view]
    a=np.asarray(Image.open(REF/f'robot-ortho-{view}.png').convert('RGB'))
    m=a.min(axis=2)<248
    labels,_=ndimage.label(m);sizes=np.bincount(labels.ravel());sizes[0]=0
    m=labels==sizes.argmax();m=ndimage.binary_closing(m,iterations=2);m=ndimage.binary_fill_holes(m)
    m[:top]=False;m[bottom:]=False
    return m

def main():
    records={}
    for view,(top,bottom) in BOUNDS.items():
        p=REF/f'robot-ortho-{view}.png';m=r01_mask(view)
        target=REF/f'ortho-{view}-mask.png';Image.fromarray(np.uint8(m)*255).save(target)
        records[view]={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                       'mask_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                       'head_y_px':top,'clip_bottom_y_px':bottom,'mm_per_pixel':1924/3653}
    (REF/'mask-provenance.json').write_text(json.dumps({'method':'threshold248/largest/closing2/fill/fixedclip','revision':2,'views':records},indent=2)+'\n')

# --- R02 -------------------------------------------------------------------
REF2=CACHE/'refs-r02'
SVG2=REF2/'r02-blauweiss.svg'
SVG2_SHA='d997c46b427cb13839cfe23a0241dce5745b143e23ead03796693802286a4814'
SHEET2=REF2/'r02-sheet-9803.png'
SHEET2_SHA='97ccf96fe77e2daa9dd51a640624d0b1a3df43588294a65bdcd2b9e8b5077350'
SVG_PX=9803/2723
# Gemessen (Referenzprobe 27.10.2026): Lücken zwischen den Figuren, SVG-Einheiten.
WINDOWS2={'front':(40,690),'back':(700,1400),'profile-a':(1450,1780),'profile-b':(1790,2110)}
ROW_LIMIT2=1100
# Profil A blickt nach rechts → Rasterkamera side_right; B nach links → side_left.
CAMERAS2={'front':'front','back':'back','profile-a':'side_right','profile-b':'side_left'}
# Sichtbare Knie-Scheibenmitte (Codex-Marker conf visible-disc-center), SVG-Einheiten.
KNEE_MARKERS2={'profile-a':(1599,723),'profile-b':(1965,723)}

def r02_sheet():
    if not SHEET2.exists():
        if hashlib.sha256(SVG2.read_bytes()).hexdigest()!=SVG2_SHA:raise ValueError('R02-Vorlage verändert')
        subprocess.run(['rsvg-convert','-w','9803',str(SVG2),'-o',str(SHEET2)],check=True)
    if hashlib.sha256(SHEET2.read_bytes()).hexdigest()!=SHEET2_SHA:
        raise ValueError('R02-Blattraster weicht von der Referenzprobe ab (rsvg-Version prüfen)')
    Image.MAX_IMAGE_PIXELS=None
    return np.asarray(Image.open(SHEET2))

def r02_mask(rgba,view):
    """Mask revision 1 (R02) in sheet pixels of the window; returns (mask, x0)."""
    x0,x1=(round(v*SVG_PX) for v in WINDOWS2[view])
    m=rgba[:round(ROW_LIMIT2*SVG_PX),x0:x1,3]>127
    lab,_=ndimage.label(m);sizes=np.bincount(lab.ravel());sizes[0]=0
    m=(sizes>=max(2000,sizes.max()*.002))[lab]
    m=ndimage.binary_closing(m,iterations=2)
    return ndimage.binary_fill_holes(m),x0

def _axis(mask):
    """Mirror axis (sheet px, half-pixel steps) with maximal self-IoU."""
    ys,xs=np.nonzero(mask);lo,hi=xs.min(),xs.max()
    best=None
    for twice in range(2*lo+(hi-lo)//2*2-80,2*lo+(hi-lo)//2*2+81):
        # Reflection x -> twice-x keeps pixel centres for integer 'twice'.
        cols=twice-np.arange(mask.shape[1]);ok=(cols>=0)&(cols<mask.shape[1])
        mirror=np.zeros_like(mask);mirror[:,ok]=mask[:,cols[ok]]
        iou=(mask&mirror).sum()/(mask|mirror).sum()
        if best is None or iou>best[0]:best=(float(iou),twice/2)
    return best

RING_RGB2=(69,79,97)

def _disc(rgba,x0,point):
    """Centre of the slate ring of the joint disc nearest the marker (sheet px).

    The ring is a closed annulus in the vector art; its centroid is the disc
    centre. The marker only selects the ring, it does not set the result.
    """
    px,py=round(point[0]*SVG_PX),round(point[1]*SVG_PX)
    r=200;win=rgba[py-r:py+r,px-r:px+r,:3].astype(int)
    ring=(abs(win-RING_RGB2).max(axis=2)<=6)
    lab,n=ndimage.label(ring);sizes=np.bincount(lab.ravel());sizes[0]=0
    best=None
    for i in np.flatnonzero(sizes>=500):
        cy,cx=ndimage.center_of_mass(lab==i);d=np.hypot(cx-r,cy-r)
        if best is None or d<best[0]:best=(d,cx,cy,int(sizes[i]))
    _,cx,cy,area=best
    return float(px-r+cx),float(py-r+cy),area

def main_r02():
    rgba=r02_sheet();records={};heights={}
    for view in WINDOWS2:
        m,x0=r02_mask(rgba,view)
        target=REF2/f'ortho-{view}-mask.png';Image.fromarray(np.uint8(m)*255).save(target)
        ys,xs=np.nonzero(m)
        records[view]={'camera':CAMERAS2[view],'window_x0_px':x0,'mask_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                       'top_px':int(ys.min()),'bottom_px':int(ys.max()),'x_range_px':[int(x0+xs.min()),int(x0+xs.max())]}
        heights[view]=int(ys.max()-ys.min()+1)
        if view in ('front','back'):
            iou,axis=_axis(m);records[view]['registration']={'kind':'gemessen','x0_px':x0+axis,'self_mirror_iou':round(iou,4),
                'source':'Symmetrieachse: maximale IoU der Maske mit ihrem Spiegelbild, Halbpixelschritte'}
        else:
            cx,cy,area=_disc(rgba,x0,KNEE_MARKERS2[view])
            records[view]['registration']={'kind':'gemessen','x0_px':cx,'knee_disc_y_px':cy,'ring_area_px':area,
                'source':'f=0 an der Kniescheibenmitte: Schwerpunkt des schiefergrauen Rings RGB(69,79,97)±6; Codex-Marker wählt nur den Ring'}
    floor=records['front']['bottom_px']+1;top=records['front']['top_px']
    prov={'robot':'R02','method':'vector-alpha>127/components>=0.2%/closing2/fill','revision':1,
          'svg_sha256':SVG2_SHA,'sheet_png_sha256':SHEET2_SHA,'render':'rsvg-convert 2.63.2 -w 9803 (Faktor 9803/2723)',
          'height_mm':{'kind':'Vorgabe','value':2000,'source':'Nutzerentscheidung 27.10.2026'},
          'front_floor_px':floor,'front_top_px':top,'mm_per_pixel':2000/(floor-top),
          'u_mm':'u=(front_floor_px-y_px)*mm_per_pixel für alle Ansichten (gleiche Blattzeilen, keine Einzelskalierung)',
          'views':records}
    (REF2/'mask-provenance.json').write_text(json.dumps(prov,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({v:{k:r[k] for k in ('top_px','bottom_px')}|{'x0':round(r['registration']['x0_px'],2)} for v,r in records.items()}),
          'mm/px',round(prov['mm_per_pixel'],5))

if __name__=='__main__':
    {'R01':main,'R02':main_r02}[sys.argv[1] if len(sys.argv)>1 else 'R01']()
