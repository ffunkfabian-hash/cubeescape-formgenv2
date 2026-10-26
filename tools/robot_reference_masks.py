"""Reproduce reviewed R01 masks; never independently scale reference images.

Original pixels stay untouched. Threshold248 and fixed head/sole crop are
segmentation assumptions (revision2), not changes made to improve model IoU.
White holes inside the connected figure are filled, closing radius2px.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image
REF=Path.home()/'Library/Caches/CubeEscapeFormgen/refs'
BOUNDS={'front':(223,3876),'back':(223,3873),'side-right':(216,3776),'side-left':(218,3776)}
def main():
    records={}
    for view,(top,bottom) in BOUNDS.items():
        p=REF/f'robot-ortho-{view}.png';a=np.asarray(Image.open(p).convert('RGB'))
        m=a.min(axis=2)<248
        labels,_=ndimage.label(m);sizes=np.bincount(labels.ravel());sizes[0]=0
        m=labels==sizes.argmax();m=ndimage.binary_closing(m,iterations=2);m=ndimage.binary_fill_holes(m)
        m[:top]=False;m[bottom:]=False
        target=REF/f'ortho-{view}-mask.png';Image.fromarray(np.uint8(m)*255).save(target)
        records[view]={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                       'mask_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                       'head_y_px':top,'clip_bottom_y_px':bottom,'mm_per_pixel':1924/3653}
    (REF/'mask-provenance.json').write_text(json.dumps({'method':'threshold248/largest/closing2/fill/fixedclip','revision':2,'views':records},indent=2)+'\n')
if __name__=='__main__':main()
