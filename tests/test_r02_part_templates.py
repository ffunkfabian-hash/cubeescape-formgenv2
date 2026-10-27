"""R02-Teilschablonen: deterministisch, Gelenke in der Hülle, benannte Ebenen.

Externe Referenzen (refs-r02) fehlen in frischen Checkouts; dann wird übersprungen.
"""
import json,shutil,tempfile,tomllib,unittest
from pathlib import Path
from PIL import Image,ImageDraw

from tools import r02_part_templates as pt

ROOT=Path(__file__).resolve().parent.parent
HAVE_REFS=pt.SHEET.exists() and (pt.REF/'mask-provenance.json').exists()


@unittest.skipUnless(HAVE_REFS,'refs-r02 fehlt')
class PartTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prov=json.loads((pt.REF/'mask-provenance.json').read_bytes())
        cls.skins=tomllib.loads((ROOT/'skins.toml').read_text())
        cls.rows=pt.r02_measure.measure(pt.STEP)['rows'];cls.sheet=Image.open(pt.SHEET).convert('RGBA')

    def build(self,pid):
        part=next(p for p in pt.PARTS if p['id']==pid)
        return pt.build_part(part,self.rows,self.sheet,self.prov,self.skins)

    def test_parts_and_joint_heights(self):
        self.assertEqual([p['id'] for p in pt.PARTS],['kopf','oberkoerper','becken','schulterpolster','arm','hand','bein','fuss'])
        self.assertEqual({k:j['u'] for k,j in pt.JOINTS.items()},
                         {'hals':1760,'taille':1265,'schulter':1560,'ellbogen':1329,'handgelenk':1036,'huefte':1060,'knie':675,'knoechel':169})
        for role in pt.ROLES:self.assertIn(role,self.skins['roles'])

    def test_deterministic_and_layers(self):
        for pid in ('kopf','arm'):
            a,b=self.build(pid)[0],self.build(pid)[0]
            self.assertEqual(a,b)
            for layer in ('underlay','frame','markers','swatches'):self.assertIn(f'<g id="{layer}" '.encode(),a)

    def test_joints_inside_envelope_and_frames_measured(self):
        for part in pt.PARTS:
            svg,m,joints,s,cells,_=self.build(part['id'])
            u0,u1=part['u'];self.assertLess(m['x'][0],m['x'][1]);self.assertLess(m['f'][0],m['f'][1])
            for j in joints:
                self.assertTrue(u0<=j['u']<=u1,(part['id'],j['id']))
                self.assertGreater(j['diameter_mm'],40)
            for view,c in cells.items():
                self.assertLessEqual(c['ox']+c['w_px'],pt.CANVAS);self.assertLessEqual(c['oy']+c['h_px'],pt.CANVAS-500)
        # Stichproben gegen herkunft-r02.md / Konturzeilen
        self.assertEqual({p['id']:self.build(p['id'])[3] for p in pt.PARTS},
                         {'kopf':4,'oberkoerper':2,'becken':2,'schulterpolster':4,'arm':2,'hand':4,'bein':2,'fuss':4})
        self.assertEqual(sorted(self.build('fuss')[5]),['back','front','side','top'])
        self.assertNotIn('top',self.build('bein')[5])
        self.assertIn(f'stroke="{pt.ASSUME_C}"'.encode(),self.build('arm')[0])
        arm=self.build('arm');self.assertAlmostEqual(arm[1]['x'][1],520.6,delta=1)
        knee=next(j for j in self.build('bein')[2] if j['id']=='knie');self.assertAlmostEqual(knee['x'],170,delta=3)

    @unittest.skipUnless(shutil.which('rsvg-convert'),'rsvg-convert fehlt')
    def test_second_run_bytewise_identical(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);args=['--out',str(out),'--only','hand','--force']
            pt.main(args);first={p.name:p.read_bytes() for p in out.iterdir()}
            pt.main(args);second={p.name:p.read_bytes() for p in out.iterdir()}
            self.assertEqual(first,second)
            with Image.open(out/'hand.png') as im:self.assertEqual(im.size,(4000,4000))
            man=json.loads((out/'manifest.json').read_text());self.assertEqual(list(man['parts']),['hand'])


class PartPromptTests(unittest.TestCase):
    """Prompts aus varianten.toml + Manifestmaßen; Prüfwerkzeug an einem synthetischen 2×2-Bild."""
    PART={'u_mm':[0,200],'side':'links','joints':[{'id':'knoechel','de':'Knöchel','u':200,'diameter_mm':120.0}],
          'frame_mm':{'front':{'x':[100.0,200.0]},'side':{'f':[-50.0,150.0]}},'assumed_edges':{'f_front':'Annahme'},
          'files':{'png':{'sha256':'0'*64}},'contour_mm':{'front':[[0,100.0,200.0],[200,100.0,200.0]],'back':[],'side':[]}}

    def test_prompts_deterministic_with_measures(self):
        skins=tomllib.loads((ROOT/'skins.toml').read_text())
        a=pt.build_prompts({'fuss':self.PART},skins,'x');b=pt.build_prompts({'fuss':self.PART},skins,'x')
        self.assertEqual(a,b)
        spec=tomllib.loads(pt.VARIANTS.read_text());self.assertEqual(list(a['prompts']['fuss']),[v['id'] for v in spec['variante']])
        text=a['prompts']['fuss']['a-blatt']['text']
        for s in ('100 mm wide','200 mm deep','200 mm tall','0.50 : 1.00 : 1','Ankle joint at the top edge','diameter 120 mm',
                  'the front face',"LEFT one",skins['roles']['frost_shell']['color']):self.assertIn(s,text)
        self.assertNotIn('{',text)

    def test_check_measures_synthetic_quadrants(self):
        from tools import r02_part_check as ck
        img=Image.new('RGB',(1000,1000),(128,128,128));d=ImageDraw.Draw(img);s=1.5  # px/mm, Bild halb so breit/tief
        for (qx,qy),(w,h) in {(0,0):(50,200),(500,0):(100,200),(0,500):(50,100),(500,500):(50,200)}.items():
            d.rectangle([qx+100,qy+50,qx+100+w*s-1,qy+50+h*s-1],fill=(226,234,238))
        res,boxes=ck.measure(img,self.PART,tomllib.loads((ROOT/'skins.toml').read_text()))
        self.assertEqual(res['blender_skalierung']['x'],2.0);self.assertEqual(res['blender_skalierung']['f'],2.0)
        self.assertEqual(res['blender_skalierung']['u'],1.0);self.assertEqual(res['konsistenz_spanne']['hoehe'],0.0)
        self.assertGreater(res['iou_kontur']['front']['rahmen_eingepasst'],0.98);self.assertEqual(res['urteil'],'tauglich')


if __name__=='__main__':unittest.main()
