"""R02-Silhouettenhülle: Maßhaltigkeit, Sollvolumen, Determinismus – synthetisch, ohne refs-r02.

Eine Kugel (r = 100 mm) wird in jedem Quadranten mit anderem Pixelmaß als Ellipse gezeichnet. Nach der anisotropen
Einpassung muss der Schnitt das Tricylinder-Volumen 8(2−√2)·r³ und der Loft das Kugelvolumen 4/3·π·r³ treffen.
"""
import json,math,struct,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

from tools import r02_part_check as pc
from tools import r02_part_hull as ph

R=100.0;F0=20.0;U0=1100.0
ELLIPSES={'front':(60,50,340,350),'side':(450,60,750,330),'top':(70,470,330,770),'back':(460,450,740,750)}  # px, bewusst ungleich


def synthetic():
    img=Image.new('RGB',(800,800),(128,128,128));d=ImageDraw.Draw(img)
    for box in ELLIPSES.values():d.ellipse(box,fill=(38,43,51))
    rows=lambda c:[[u,round(c-math.sqrt(max(R*R-(u-U0)**2,0)),2),round(c+math.sqrt(max(R*R-(u-U0)**2,0)),2)]
                   for u in range(int(U0-R),int(U0+R)+1,5)]
    part={'id':'kugel','u_mm':[U0-R,U0+R],
          'frame_mm':{'front':{'x':[-R,R],'u':[U0-R,U0+R]},'side':{'f':[F0-R,F0+R],'u':[U0-R,U0+R]}},
          'contour_mm':{'front':rows(0.0),'back':rows(0.0),'side':rows(F0)},
          'joints':[{'id':'hals','u':U0-R,'f':F0,'x':0,'diameter_mm':50.0,'diameter_row_u':U0-R+10}]}
    _,boxes=pc.quadrant_boxes(np.asarray(img));return img,boxes,part


class PartHullTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.img,cls.boxes,cls.part=synthetic();cls.rgb=np.asarray(cls.img)
        cls.record={'teil':'kugel','variante':'test','bild_sha256':'0'*64,'quadranten_px':cls.boxes,
                    'messung':{'iou_kontur':{v:{'rahmen_eingepasst':None} for v in ('front','back','side')}}}

        cls.cache={}

    def measure(self,modus):
        if modus not in self.cache:
            res=ph.build(self.rgb,self.boxes,self.part,modus=modus);self.cache[modus]=res,ph.measure(res,self.part,self.record)[0]
        return self.cache[modus]

    def test_frame_exact_and_silhouettes(self):
        for modus in ph.MODI:
            res,m=self.measure(modus)
            for axis,(lo,hi) in m['rahmen_abweichung_mm'].items():
                self.assertLess(max(abs(lo),abs(hi)),0.3,f'{modus} {axis}')
            for view,e in m['ansichten'].items():
                self.assertGreater(e['iou_huelle_gegen_quelle'],0.985,f'{modus} {view}')
                if view!='top':self.assertGreater(e['iou_kontur_huelle'],0.97,f'{modus} {view}')
            self.assertEqual(m['netz']['genus'],0);self.assertTrue(m['gelenke']['hals']['mitte_innen'])

    def test_volume_matches_closed_form(self):
        soll={'schnitt':8*(2-math.sqrt(2))*R**3/1e6,'loft':4/3*math.pi*R**3/1e6}
        for modus,v in soll.items():
            self.assertAlmostEqual(self.measure(modus)[1]['netz']['volumen_l']/v,1.0,delta=0.02,msg=modus)

    def test_deterministic_glb_and_cache(self):
        a,b=(ph.build(self.rgb,self.boxes,self.part) for _ in range(2))
        ga,gb=(ph.glb_bytes(r['vertices'],r['triangles'],'kugel','#E2EAEE') for r in (a,b))
        self.assertEqual(ga,gb)
        magic,ver,total=struct.unpack('<III',ga[:12]);n=struct.unpack('<I',ga[12:16])[0];doc=json.loads(ga[20:20+n])
        self.assertEqual((magic,ver,total),(0x46546C67,2,len(ga)))
        acc=doc['accessors'][0];self.assertEqual(acc['count'],len(a['vertices']))
        np.testing.assert_allclose(acc['min'],[-R/1000,(U0-R)/1000,(F0-R)/1000],atol=3e-4)  # (x,u,f) in Metern
        np.testing.assert_allclose(acc['max'],[R/1000,(U0+R)/1000,(F0+R)/1000],atol=3e-4)
        with tempfile.TemporaryDirectory() as tmp:
            t=Path(tmp);self.img.save(t/'source.png');(t/'record.json').write_text(json.dumps(self.record))
            (t/'manifest.json').write_text(json.dumps({'parts':{'kugel':self.part}}))
            first=ph.run(t,t/'manifest.json');files={n:(t/'hull'/n).read_bytes() for n in first['dateien']}
            self.assertEqual(ph.run(t,t/'manifest.json'),first)
            ph.run(t,t/'manifest.json',force=True)
            self.assertEqual({n:(t/'hull'/n).read_bytes() for n in files},files)
            self.assertEqual(ph.out_name(1.0,ph.BUILD_VIEWS,'loft'),'hull-loft-tol1')


if __name__=='__main__':unittest.main()
