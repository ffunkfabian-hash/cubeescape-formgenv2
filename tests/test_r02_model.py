"""R02 Frost: Geometrie-, Symmetrie-, Schnitt- und Exportprüfungen ohne Bildabnahme."""
import copy,json,re,tempfile,unittest
from collections import Counter
from pathlib import Path

import numpy as np

from formgen import geo,geom,model,spec
from formgen.models.figures import r02_basic_robot as r02
from formgen.models.figures.r02_parts import common

ROOT=Path(__file__).resolve().parents[1]
PANEL=re.compile(r'(crystal|strap|slot|plate|band|hex|blade|kneecap|disc|visor|core_light|core_ring|ear)')


class R02ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=geom.evaluate(model.load(ROOT/'formgen/models/figures/r02_basic_robot.py'),bevels=True)
        cls.parts={p['id']:p for p in cls.document['parts']}

    def test_five_assemblies_height_ground_and_provenance(self):
        self.assertEqual([a['id'] for a in self.document['assemblies']],['legs','lower_body','upper_body','head','arms'])
        low,high=self.document['bounds_m']
        self.assertAlmostEqual(low[2],0,places=9)
        self.assertTrue(1.99<=high[2]<=2.0,high[2])
        for p in self.document['parts']:
            self.assertTrue(p['id'].startswith(p['assembly']+'_'),p['id'])
            self.assertIn(p['provenance']['kind'],('gemessen','Annahme','Vorgabe'),p['id'])
            self.assertTrue(p['role'].startswith('frost_'),p['id'])
        self.assertFalse(self.document['warnings'])

    def test_closed_positive_manifold_meshes_without_degenerate_triangles(self):
        for p in self.document['parts']:
            mesh=p['mesh'];v=np.asarray(mesh['vertices'])
            directed=Counter((a,b) for face in mesh['faces'] for a,b in zip(face,face[1:]+face[:1]))
            self.assertTrue(all(n==1 and directed[(b,a)]==1 for (a,b),n in directed.items()),p['id'])
            self.assertGreater(geom._volume(mesh['vertices'],mesh['faces']),0,p['id'])
            areas=[np.linalg.norm(np.cross(v[b]-v[a],v[c]-v[a])) for a,b,c in mesh['faces']]
            self.assertGreater(min(areas),1e-10,p['id'])

    def test_left_right_parts_are_exact_mirrors_with_same_diagonals(self):
        pairs=[pid for pid in self.parts if pid.endswith('_l')]
        self.assertGreater(len(pairs),25)
        for pid in pairs:
            left,right=self.parts[pid]['mesh'],self.parts[pid[:-2]+'_r']['mesh']
            self.assertEqual([[-x,y,z] for x,y,z in left['vertices']],right['vertices'],pid)
            self.assertEqual([[a,c,b] for a,b,c in left['faces']],right['faces'],pid)
        for pid,p in self.parts.items():
            if not pid.endswith(('_l','_r')):
                v=np.asarray(p['mesh']['vertices'])
                self.assertAlmostEqual(v[:,0].min(),-v[:,0].max(),places=9,msg=pid)

    def test_only_visor_core_and_crystal_emit(self):
        emissive={p['role'] for p in self.document['parts'] if p['role'] in ('frost_visor','frost_core','frost_crystal')}
        self.assertEqual(emissive,{'frost_visor','frost_core','frost_crystal'})
        roles={p['role'] for p in self.document['parts']}
        self.assertNotIn('energy',roles)

    def test_panels_lie_on_host_faces_and_cores_do_not_overlap_unexpectedly(self):
        """Pairwise intersection volume: only declared embeddings.

        Panels sink ≤ their depth into their host; stacked segments overlap by
        the 3 mm embedding; everything else must stay separate.
        """
        solids={pid:geom._as_manifold(p['mesh']['vertices'],p['mesh']['faces']) for pid,p in self.parts.items()}
        volume={pid:s.volume() for pid,s in solids.items()}
        boxes={pid:np.asarray(p['bounds_m']) for pid,p in self.parts.items()}
        ids=sorted(self.parts)
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                if np.any(boxes[a][0]>boxes[b][1]) or np.any(boxes[b][0]>boxes[a][1]):continue
                shared=(solids[a]^solids[b]).volume()
                if shared<=1e-12:continue
                small=min(volume[a],volume[b]);smaller=a if volume[a]<=volume[b] else b
                if PANEL.search(smaller):
                    self.assertLess(shared/small,.9,f'{a}/{b}')
                else:
                    # Eingesetzte Stöße: höchstens 12 % des kleineren Teils.
                    self.assertLess(shared/small,.12,f'{a}/{b} {shared/small:.3f}')

    def test_no_coplanar_overlap_between_parts(self):
        parts=[dict(id=p['id'],channel='MT',material=p['role'],emissive=False,glass=False,mesh=p['mesh'])
               for p in self.document['parts']]
        self.assertEqual(geo._coplanar(parts),[])

    def test_face_panel_follows_loft_face_at_constant_offset(self):
        from formgen.models.figures.r02_parts import legs
        panel=common.face_panel(legs.SHIN,'front',[(335,.3),(345,.78),(470,.95),(555,.85),(555,.15),(470,.05)])
        for f,u,x in panel['vertices']:
            ff=common._row_at(legs.SHIN,u)[4]
            self.assertTrue(abs(f-(ff+1.2))<1e-9 or abs(f-(ff-1.8))<1e-9,(f,u))

    def test_spec_and_geo_roundtrip_keep_mirrors(self):
        document=copy.deepcopy(self.document)
        data=spec.build(document)
        json.dumps(data,allow_nan=False)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'R02.spec.json';path.write_bytes(json.dumps(data).encode())
            exported=geo.export(document,path)
            geo_path=Path(folder)/'R02.geo.json';geo_path.write_text(json.dumps(exported))
            loaded=geo.load(geo_path)
        parts={p['source_id'] if 'source_id' in p else p['id']:p for p in loaded['parts']}
        for pid in [p for p in self.parts if p.endswith('_l')]:
            left=next(p for k,p in parts.items() if k.endswith(pid) or k==pid)
            right=next(p for k,p in parts.items() if k.endswith(pid[:-2]+'_r') or k==pid[:-2]+'_r')
            self.assertEqual([[-x,y,z] for x,y,z in left['mesh']['vertices']],right['mesh']['vertices'],pid)
        self.assertEqual(loaded['counts']['triangles'],self.document['counts']['triangles'])


if __name__=='__main__':unittest.main()
