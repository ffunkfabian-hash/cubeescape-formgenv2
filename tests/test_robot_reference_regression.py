"""R01 bleibt nach der R02-Verallgemeinerung bytegleich (Masken, Registrierung, Metriken).

Externe Referenzen/Belege fehlen in frischen Checkouts; dann wird übersprungen.
"""
import hashlib,io,json,unittest
import numpy as np
from PIL import Image

from tools import robot_evidence as ev
from tools import robot_reference_masks as masks

R01_GROUPS=['legs','lower_body','upper_body','head','arms']
# Stand 27.10.2026 10:56 (Fußabnahme, GEOM8/RASTER5), evidence/robot/…/metrics.json.
R01_FRAMES={'back':'ec291c7fb3e83a378fadafde433b8b18a8525c85b0683c4400a10d6efcc57fea',
            'front':'7fb705a5140e8f4e1f07b480cf6396d34d93b68d7bd5bd7751600f772b51b610',
            'side-left':'f04b55bf8445a77a88a44a126a640612b8da64e3cd7134c18440a0cbf23abd6e',
            'side-right':'e000c6749e4bfe05dd7534b7772342f0f104f26aa0e2badd25ad889a16d2a36f'}
R01_METRICS={'back': {'iou': 0.8859483142429271, 'ratios': [1.0970891339721571, 1.0743834685638913, 1.042046961541462, 1.0534158243290344, 0.9771450362272786, 1.0271161597654819, 1.008558605573531, 0.9997384595266117, 1.015148327372186, 1.039039039039039]},
             'front': {'iou': 0.9400816578075649, 'ratios': [0.994265115516959, 1.001751574553721, 1.001837477031537, 0.9967843007915566, 0.9686980190533797, 1.005808607504093, 0.9916363076607317, 0.9900925985883572, 1.000725915171627, 1.0127169963665723]},
             'side-left': {'iou': 0.9009895076353356, 'ratios': [1.424647081266692, 0.960189407225535, 1.0004552179355866, 0.990449148167269, 0.9837952090183186, 1.0186577302780546, 1.0077319587628866, 1.0107709750566896, 0.9781889600992351, 0.9923325262308313]},
             'side-right': {'iou': 0.9038097892075877, 'ratios': [1.4174364165506768, 0.9530026109660575, 0.9993179493008981, 0.9901935483870968, 0.9738463326746485, 1.013151968291145, 1.0023868458274399, 1.0084841628959278, 0.9759694719471947, 0.9926329599354122]}}


class R01RegressionTests(unittest.TestCase):
    def test_r01_constants_unchanged(self):
        cfg=ev.ROBOTS['R01']()
        self.assertEqual((cfg['scale'],cfg['floor_px'],cfg['height_mm'],cfg['registration']),(3653/1.924/4,3876,1924,4))
        self.assertEqual(cfg['views'],ev.VIEWS)
        self.assertEqual(ev.VIEWS['side-right'][1:],([0,-(2150/4-512)/ev.SCALE,ev.CENTER_Z],0,7))
        self.assertEqual(masks.BOUNDS,{'front':(223,3876),'back':(223,3873),'side-right':(216,3776),'side-left':(218,3776)})

    def test_r01_masks_reproduce_provenance_sha(self):
        provenance=masks.REF/'mask-provenance.json'
        if not provenance.exists():self.skipTest('R01-Referenzen fehlen')
        prov=json.loads(provenance.read_bytes())
        for view in masks.BOUNDS:
            buffer=io.BytesIO();Image.fromarray(np.uint8(masks.r01_mask(view))*255).save(buffer,'PNG')
            self.assertEqual(hashlib.sha256(buffer.getvalue()).hexdigest(),prov['views'][view]['mask_sha256'],view)

    def test_r01_metrics_recomputed_from_stored_frames(self):
        cfg=ev.ROBOTS['R01']();folder=cfg['out']/'-'.join(R01_GROUPS)
        for view,sha in R01_FRAMES.items():
            frame=folder/(view+'-frame.png')
            if not frame.exists() or hashlib.sha256(frame.read_bytes()).hexdigest()!=sha:
                self.skipTest('R01-Belegframe fehlt oder ist neuer als die Baseline')
            m=np.asarray(Image.open(frame).convert('RGBA').getchannel('A'))>127
            _,_,record=ev.view_metrics(ev.reference_mask(view),m,R01_GROUPS,view,cfg,0,1924)
            self.assertEqual(record['iou'],R01_METRICS[view]['iou'],view)
            self.assertEqual([b['ratio'] for b in record['bands']],R01_METRICS[view]['ratios'],view)


class R02ReferenceTests(unittest.TestCase):
    def test_r02_masks_match_frozen_revision(self):
        provenance=masks.REF2/'mask-provenance.json'
        if not provenance.exists():self.skipTest('R02-Referenzen fehlen')
        prov=json.loads(provenance.read_bytes())
        self.assertEqual((prov['revision'],prov['svg_sha256'],prov['height_mm']['value']),(1,masks.SVG2_SHA,2000))
        for view,record in prov['views'].items():
            self.assertEqual(hashlib.sha256((masks.REF2/f'ortho-{view}-mask.png').read_bytes()).hexdigest(),record['mask_sha256'])
        self.assertEqual({v:r['camera'] for v,r in prov['views'].items()},masks.CAMERAS2)

    def test_r02_registration_shares_rows_and_scale(self):
        if not (masks.REF2/'mask-provenance.json').exists():self.skipTest('R02-Referenzen fehlen')
        cfg=ev.ROBOTS['R02']()
        self.assertEqual({v[3] for v in cfg['views'].values()},{0})
        for view in cfg['views']:
            r=ev.reference_mask(view,'R02');ys,xs=np.nonzero(r)
            # Gemeinsamer Scheitel aller Ansichten; Boden der Front bei u=0.
            self.assertEqual(ys.min(),174//4,view)
        front=ev.reference_mask('front','R02');xs=np.nonzero(front)[1]
        self.assertLessEqual(abs((xs.min()+xs.max())/2-511.5),1.5)


if __name__=='__main__':unittest.main()
